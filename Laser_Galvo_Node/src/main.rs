// laser_node - galvo (X/Y) + laser controller for the Raspberry Pi.
//
// X and Y go to a PCM5102A I2S DAC through ALSA (stereo: left = X, right = Y). The laser is a plain
// digital output on a GPIO: on or off. That is the fastest and most predictable thing this bench can do
// with a laser - no modulation period an edge has to wait for, no minimum on time, no duty floor the
// brightness would have to be remapped onto.
//
// Server (default):
//   laser_node [--device hw:2] [--gpio 12] [--socket /tmp/laser.sock]
//              [--rate 384000] [--period 64] [--periods 2] [--block 1] [--no-ramp] [--rt 50] [--no-rt]
//              [--laser-delay 333]
// Client (for bench testing, talks to the running server):
//   laser_node --send 0.5 -0.25 1      # send one setpoint, then print what the server holds
//   laser_node --get
//   laser_node --get-delay             # how far the running server holds its laser edges back
//
// Protocol on the socket (one command per line):
//   SET <x> <y> <laser>     x,y in [-1,1], laser in [0,1]; anything above 0 lights the line
//   GET                     answers with "SET <x> <y> <laser>", the laser as 0 or 1
//   DELAY [us]              answers with "DELAY <us>", the edge spacing in use; with a number it sets it
// Anything else is ignored.
//
// A laser edge is deliberately not applied when its SET arrives. The position in the same SET goes into
// an ALSA ring that is one ring delay away from the DAC (buffer/rate, 0.33 ms at the default 384 kHz), so
// light that switched the instant it was commanded switches over a position the mirrors have not reached
// yet - which is the smeared start and end of every traced line. laser_clock dates every edge and applies
// it that much later, so "off during a blank move" lands where the beam actually is.

// clippy wants `as_chunks::<N>()` where a chunk size is a constant, but that method is Rust 1.88+ and this
// tree also has to build with the pinned 1.87 toolchain. `chunks_exact(2)` is the same loop on both.
#![allow(clippy::chunks_exact_to_as_chunks)]

use std::collections::VecDeque;
use std::io::{BufRead, BufReader, Write};
use std::os::unix::net::UnixListener;
use std::process::exit;
use std::sync::atomic::AtomicBool;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::mpsc::{Receiver, Sender, TryRecvError};
use std::sync::Arc;
use std::thread;
use std::time::{Duration, Instant};

use alsa::card::Iter as CardIter;
use alsa::pcm::{Access, Format, HwParams, PCM};
use alsa::{Direction, ValueOr};
use rppal::gpio::{Gpio, OutputPin};

const RATE: u32 = 384_000; // wanted sample rate; falls back to what the driver can clock
const PERIOD: u32 = 64; // frames per ALSA period: the driver's floor, and with realtime it holds
const PERIODS: u32 = 2; // buffer = 2 periods => the setpoint reaches the DAC in ~0.33 ms at 384 kHz
const BLOCK: u32 = 1; // periods per write; > 1 wakes half as often but eats the ring's slack
const RT_PRIO: i32 = 50; // asked for by default: this is what makes the short ring survivable
                         // Ring used when realtime was refused and the caller did not ask for a specific one.
const FALLBACK_PERIODS: u32 = 4;

// The period that keeps a 0.67 ms write deadline at this sample rate: the deadline an ordinary
// (non realtime) thread on this Pi was measured to meet without losing samples. Snapped to a
// multiple of 64 frames, which is the driver's floor: 128 at 192 kHz, 256 at 384 kHz.
fn deadline_safe_period(rate: u32) -> u32 {
    const DEADLINE_US: u64 = 667;
    let frames = (rate as u64 * DEADLINE_US / 1_000_000).max(64);
    ((frames + 32) / 64 * 64) as u32
}
const SOCKET_PATH: &str = "/tmp/laser.sock";
const LASER_GPIO: u8 = 12; // free GPIO for the laser line; 18/19/21 belong to I2S

// The last stretch before an edge's deadline is waited out in a tight loop: thread::sleep is a
// millisecond-accurate instrument, and a laser edge that is 400 us late is a visible blob on the beam.
const SPIN_NS: u64 = 60_000;
// Edges the clock thread has not gotten to yet. A queue this deep means the thread is not running, and
// the recent intent is worth more than the oldest one.
const QUEUE_MAX: usize = 4096;
const MAX_LASER_DELAY_US: f64 = 1_000_000.0;

/// The laser line: one digital output. The `laser_clock` thread owns it, so a switching moment has one
/// author and the pin has one writer.
struct LaserLine {
    pin: OutputPin,
}

impl LaserLine {
    fn open(pin: u8) -> Self {
        LaserLine {
            pin: Gpio::new()
                .expect(
                    "GPIO: cannot open /dev/gpiomem (is this a Pi, and is the user in group gpio?)",
                )
                .get(pin)
                .expect("GPIO: pin not available")
                .into_output_low(),
        }
    }

    /// What the line is, for a log line.
    fn describe(&self) -> String {
        format!("TTL gpio {}", self.pin.pin())
    }
}

/// What the control side asks the laser line to do.
#[derive(Debug)]
enum LaserMsg {
    /// Be at `on` from `at` on.
    Edge { at: Instant, on: bool },
    /// Line low, forget every edge that has not happened yet, end the thread.
    Park,
}

/// The edges waiting for their deadline, earliest first.
#[derive(Default)]
struct EdgeQueue {
    q: VecDeque<(Instant, bool)>,
}

impl EdgeQueue {
    /// Insert in deadline order. Two clients whose SETs arrive a microsecond apart do not have to agree
    /// about which one was first for the line to run them in the order they were meant to run.
    fn push(&mut self, at: Instant, on: bool) {
        let idx = self.q.iter().take_while(|(t, _)| *t <= at).count();
        self.q.insert(idx, (at, on));
        if self.q.len() > QUEUE_MAX {
            self.q.pop_front();
        }
    }

    /// When the next edge is due, if one is waiting.
    fn next_deadline(&self) -> Option<Instant> {
        self.q.front().map(|(t, _)| *t)
    }

    /// The state the line should be in at `now`: the newest edge whose deadline has passed. Older expired
    /// edges are dropped without ever reaching the pin - an on and an off inside one wakeup window is a
    /// flash shorter than the line can be told about anyway.
    fn take_due(&mut self, now: Instant) -> Option<bool> {
        let mut state = None;
        while self.q.front().is_some_and(|(t, _)| *t <= now) {
            state = Some(self.q.pop_front().expect("checked above").1);
        }
        state
    }

    #[cfg(test)]
    fn len(&self) -> usize {
        self.q.len()
    }
}

/// How far a laser edge is held back behind the SET that asked for it. `auto` means "whatever ring delay
/// the ALSA thread ended up with", which is the spacing that makes light and position arrive together.
struct LaserDelay {
    auto: bool,
    ns: AtomicU64,
}

impl LaserDelay {
    /// `requested` is what `--laser-delay` gave, in microseconds. `estimate` is the ring delay of the
    /// timing the caller asked for, which is what an automatic spacing starts out at before the driver
    /// has said what it actually clocks.
    fn new(requested: Option<f64>, estimate: u64) -> Self {
        match requested {
            Some(us) if us.is_finite() => LaserDelay {
                auto: false,
                ns: AtomicU64::new((us * 1000.0).round().max(0.0) as u64),
            },
            _ => LaserDelay {
                auto: true,
                ns: AtomicU64::new(estimate),
            },
        }
    }

    fn ns(&self) -> u64 {
        self.ns.load(Ordering::Relaxed)
    }

    fn us(&self) -> f64 {
        self.ns() as f64 / 1000.0
    }

    /// Replace the spacing a running node applies, from `DELAY <us>` on the socket.
    fn set_us(&self, us: f64) -> f64 {
        let ns = (us * 1000.0)
            .clamp(0.0, MAX_LASER_DELAY_US * 1000.0)
            .round() as u64;
        self.ns.store(ns, Ordering::Relaxed);
        ns as f64 / 1000.0
    }
}

// Ctrl+C and SIGTERM: park the laser. The handler itself only raises a flag, which is about the only
// thing that is safe to do in a signal handler; whoever is running the loop sees the flag and does the
// writes with a normal stack. Without this, a Ctrl+C on `deploy.sh run` leaves the line at whatever
// level it had at the moment the process died.
static SHUTDOWN: AtomicBool = AtomicBool::new(false);

extern "C" fn on_signal(_: libc::c_int) {
    SHUTDOWN.store(true, Ordering::SeqCst);
}

fn catch_exit_signals() {
    // SAFETY: installing a handler that only stores to a static atomic. Nothing else is touched, and
    // the previous disposition is deliberately left alone (a SIG_IGN inherited from a parent is not our
    // business).
    unsafe {
        let handler: extern "C" fn(libc::c_int) = on_signal;
        libc::signal(libc::SIGINT, handler as libc::sighandler_t);
        libc::signal(libc::SIGTERM, handler as libc::sighandler_t);
    }
}

/// For the server: the main thread is blocked in accept(), so a second thread has to be the one that
/// notices Ctrl+C. It asks the clock thread to park and gives it the moment to write the low.
fn park_on_exit(tx: Sender<LaserMsg>) {
    thread::spawn(move || loop {
        if SHUTDOWN.load(Ordering::SeqCst) {
            let _ = tx.send(LaserMsg::Park);
            thread::sleep(Duration::from_millis(50));
            exit(0);
        }
        thread::sleep(Duration::from_millis(20));
    });
}

// -1.0..1.0 -> -32768..32767
fn to_i16(v: f64) -> i16 {
    (v.clamp(-1.0, 1.0) * 32767.0).round() as i16
}

// 0.0..1.0 -> 0..65535. Only its sign decides the laser line, but carrying the value keeps GET honest
// about what a caller sent.
fn to_u16(v: f64) -> u16 {
    (v.clamp(0.0, 1.0) * 65535.0).round() as u16
}

// One AtomicU64 holds the whole setpoint so the ALSA thread can never read a half
// updated (x from one command, y from the next) position.
//   bits 47..32 = x as i16, bits 31..16 = y as i16, bits 15..0 = laser as u16
fn pack(x: i16, y: i16, laser: u16) -> u64 {
    ((x as u16 as u64) << 32) | ((y as u16 as u64) << 16) | u64::from(laser)
}

fn unpack(v: u64) -> (i16, i16, u16) {
    ((v >> 32) as u16 as i16, (v >> 16) as u16 as i16, v as u16)
}

fn main() {
    let argv: Vec<String> = std::env::args().skip(1).collect();
    let mut device = String::new();
    let mut socket = SOCKET_PATH.to_string();
    let mut gpio_pin: u8 = LASER_GPIO;
    let mut send: Option<(f64, f64, f64)> = None;
    let mut get = false;
    let mut get_delay = false;
    let mut period: u32 = PERIOD;
    let mut rate: u32 = RATE;
    let mut buffer_periods: u32 = PERIODS;
    let mut block_periods: u32 = BLOCK;
    let mut ramp = true;
    let mut rt: Option<i32> = Some(RT_PRIO);
    let mut ring_is_asked_for = false;
    let mut laser_delay_us: Option<f64> = None;
    let mut i = 0;

    while i < argv.len() {
        match argv[i].as_str() {
            "--device" => {
                device = argv.get(i + 1).cloned().unwrap_or_default();
                i += 2
            }
            "--socket" => {
                socket = argv.get(i + 1).cloned().unwrap_or_default();
                i += 2
            }
            "--gpio" => {
                gpio_pin = argv
                    .get(i + 1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(LASER_GPIO);
                i += 2
            }
            "--period" => {
                // Setpoints can only reach the DAC at period boundaries, so this is also
                // the update rate the control side sees: rate / period updates per second.
                period = argv
                    .get(i + 1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(PERIOD)
                    .max(8);
                ring_is_asked_for = true;
                i += 2
            }
            "--rate" => {
                rate = argv.get(i + 1).and_then(|s| s.parse().ok()).unwrap_or(RATE);
                i += 2
            }
            "--periods" => {
                // Ring depth in periods. This is the latency knob: the setpoint is played out of
                // a ring that is block * period frames deep, and block can never exceed it.
                buffer_periods = argv
                    .get(i + 1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(PERIODS)
                    .clamp(2, 16);
                ring_is_asked_for = true;
                i += 2
            }
            "--block" => {
                // Periods per write. 1 is the natural pacing and the only value that measured
                // clean on the Pi; bigger blocks wake half as often but give the DMA more slack to
                // run out, because ALSA wakes us at a period boundary either way.
                block_periods = argv
                    .get(i + 1)
                    .and_then(|s| s.parse().ok())
                    .unwrap_or(BLOCK)
                    .clamp(1, 16);
                i += 2
            }
            "--no-ramp" => {
                // Old behaviour: hold each setpoint as a flat step until the next one arrives.
                ramp = false;
                i += 1
            }
            "--rt" => {
                // Run the timing threads SCHED_FIFO so the desktop stack cannot delay them past their
                // deadlines. Needs CAP_SYS_NICE or a raised RLIMIT_RTPRIO (ulimit -r); without either
                // the call is refused, the threads stay ordinary ones and the ALSA thread widens the
                // ring instead of losing samples.
                rt = Some(
                    argv.get(i + 1)
                        .and_then(|s| s.parse::<i32>().ok())
                        .unwrap_or(RT_PRIO)
                        .clamp(1, 99),
                );
                i += 2
            }
            "--no-rt" => {
                rt = None;
                i += 1
            }
            "--laser-delay" => {
                // Microseconds. A number here is a measured compensation; without it the node uses the
                // ring delay it ended up with, which is the same delay the position travels.
                laser_delay_us = argv
                    .get(i + 1)
                    .and_then(|s| s.parse::<f64>().ok())
                    .filter(|us| us.is_finite() && *us >= 0.0);
                if laser_delay_us.is_none() {
                    eprintln!("usage: --laser-delay <us>");
                    exit(2);
                }
                i += 2
            }
            "--send" => {
                let nums: Vec<f64> = argv[i + 1..]
                    .iter()
                    .filter_map(|s| s.parse().ok())
                    .collect();
                if nums.len() < 3 {
                    eprintln!("usage: --send <x> <y> <laser>");
                    exit(2);
                }
                send = Some((nums[0], nums[1], nums[2]));
                i += 4;
            }
            "--get" => {
                get = true;
                i += 1
            }
            "--get-delay" => {
                get_delay = true;
                i += 1
            }
            "-h" | "--help" => {
                eprintln!("server: laser_node [--device hw:N] [--gpio 12] [--socket path] [--rate hz] [--period frames] [--periods n] [--block n] [--no-ramp] [--rt prio] [--no-rt]");
                eprintln!("        laser: [--laser-delay us]   (default: the ring delay, buffer/rate; 0 switches the moment a SET arrives)");
                eprintln!("client: laser_node --send <x> <y> <laser> | --get | --get-delay");
                eprintln!("socket: SET <x> <y> <laser> | GET | DELAY [us]");
                exit(0);
            }
            other => {
                eprintln!("ignoring unknown argument: {other}");
                i += 1
            }
        }
    }

    // The ring delay of the timing that was asked for, as a starting point: alsa_loop replaces it with
    // the buffer and rate the driver actually gave, which is the number the edges have to match.
    let estimate = (f64::from(period) * f64::from(buffer_periods) * 1e9 / f64::from(rate)) as u64;
    let delay = Arc::new(LaserDelay::new(laser_delay_us, estimate));

    if send.is_some() || get || get_delay {
        client(&socket, send, get, get_delay);
        return;
    }

    if device.is_empty() {
        match find_dac() {
            Some(d) => device = d,
            None => {
                eprintln!("laser_node: no usable DAC card; name one with --device hw:N");
                exit(1);
            }
        }
    }
    eprintln!("laser_node: alsa={device} socket={socket} rate={rate} period={period} buffer={buffer_periods}x block={block_periods}x ramp={ramp} rt={}",
        rt.map(|p| p.to_string()).unwrap_or_else(|| "off".into()));

    let setpoint = Arc::new(AtomicU64::new(pack(0, 0, 0)));

    // Thread 1: keep the ALSA buffer fed so it never underruns.
    {
        let sp = Arc::clone(&setpoint);
        let dev = device.clone();
        let delay = Arc::clone(&delay);
        thread::spawn(move || {
            alsa_loop(
                &dev,
                Timing {
                    rate,
                    period,
                    periods: buffer_periods,
                    block: block_periods,
                    ramp,
                    rt,
                    explicit_ring: ring_is_asked_for,
                },
                sp,
                &delay,
            )
        });
    }

    // Thread 2: the laser line, and the only thing that ever writes the pin. Opened here so a missing
    // GPIO or a pin the kernel owns shows up as a startup message instead of a dead thread.
    let line = LaserLine::open(gpio_pin);
    eprintln!("laser_node: laser = {}", line.describe());
    let (tx, rx) = std::sync::mpsc::channel::<LaserMsg>();
    thread::spawn(move || laser_clock(line, rx, rt));
    catch_exit_signals();
    park_on_exit(tx.clone());

    // A leftover socket file from an earlier run is not a live server.
    if std::path::Path::new(&socket).exists() {
        std::fs::remove_file(&socket)
            .unwrap_or_else(|e| eprintln!("warning: cannot remove {socket}: {e}"));
    }
    let listener = UnixListener::bind(&socket).expect("cannot bind the control socket");
    eprintln!("laser_node: listening on {socket}");

    // One thread per client: a control program that keeps its connection open must not
    // lock everybody else out (a demo drawing for 30 s used to block every other client).
    for conn in listener.incoming() {
        let conn = match conn {
            Ok(c) => c,
            Err(e) => {
                eprintln!("socket: {e}");
                continue;
            }
        };
        let setpoint = Arc::clone(&setpoint);
        let tx = tx.clone();
        let delay = Arc::clone(&delay);
        thread::spawn(move || serve_client(conn, &setpoint, &tx, &delay));
    }
}

/// Thread 2: apply the laser edges at their deadlines. Nothing else writes the pin, which is what makes
/// a switching moment a fact of this thread's clock instead of a race between client threads.
fn laser_clock(mut line: LaserLine, rx: Receiver<LaserMsg>, rt: Option<i32>) {
    if let Some(prio) = rt {
        match set_realtime(prio) {
            Ok(()) => eprintln!("laser: SCHED_FIFO priority {prio}"),
            Err(e) => eprintln!("laser: {e} - edges will move with the rest of the system"),
        }
    }
    let mut queue = EdgeQueue::default();
    loop {
        // Take everything the control side has sent since the last look, then decide how long the line
        // has before the next edge is due.
        let mut park = false;
        loop {
            match rx.try_recv() {
                Ok(LaserMsg::Edge { at, on }) => queue.push(at, on),
                Ok(LaserMsg::Park) => park = true,
                Err(TryRecvError::Disconnected) => park = true,
                Err(TryRecvError::Empty) => break,
            }
        }
        if park {
            park_and_stop(&mut line);
            return;
        }

        let Some(deadline) = queue.next_deadline() else {
            // Nothing outstanding: wait for a command instead of spinning.
            match rx.recv() {
                Ok(LaserMsg::Edge { at, on }) => {
                    queue.push(at, on);
                    continue;
                }
                Ok(LaserMsg::Park) | Err(_) => {
                    park_and_stop(&mut line);
                    return;
                }
            }
        };

        let now = Instant::now();
        // Sleep up to the last 60 us, and wait those out: sleep wakes a thread at millisecond granularity
        // at best, and that is two orders of magnitude more than a galvo can see.
        let spin_from = deadline
            .checked_sub(Duration::from_nanos(SPIN_NS))
            .unwrap_or(now);
        if spin_from > now {
            thread::sleep(spin_from - now);
        }
        while Instant::now() < deadline {}

        if let Some(on) = queue.take_due(Instant::now()) {
            if on {
                line.pin.set_high();
            } else {
                line.pin.set_low();
            }
        }
    }
}

fn park_and_stop(line: &mut LaserLine) {
    line.pin.set_low();
    eprintln!("laser: parked -> {}", line.describe());
}

/// GET answers with what the line is doing. A digital line has one rate: the rate somebody toggles it at.
fn report_power(p: u16) -> f64 {
    f64::from(p > 0)
}

fn serve_client(
    conn: std::os::unix::net::UnixStream,
    setpoint: &AtomicU64,
    tx: &Sender<LaserMsg>,
    delay: &LaserDelay,
) {
    let mut out = match conn.try_clone() {
        Ok(c) => c,
        Err(e) => {
            eprintln!("socket: {e}");
            return;
        }
    };
    let mut line = String::new();
    let mut reader = BufReader::new(&conn);
    while reader.read_line(&mut line).unwrap_or(0) > 0 {
        let cmd = line.split_whitespace().next().unwrap_or("").to_string();
        match cmd.as_str() {
            "SET" => apply(&line, setpoint, tx, delay),
            "GET" => {
                let (x, y, p) = unpack(setpoint.load(Ordering::Relaxed));
                let _ = writeln!(
                    out,
                    "SET {} {} {}",
                    x as f64 / 32767.0,
                    y as f64 / 32767.0,
                    report_power(p)
                );
            }
            "DELAY" => {
                let words: Vec<&str> = line.split_whitespace().collect();
                match words.as_slice() {
                    ["DELAY"] => {
                        let _ = writeln!(out, "DELAY {:.1}", delay.us());
                    }
                    ["DELAY", value] => match value.parse::<f64>() {
                        Ok(us) if us.is_finite() => {
                            let _ = writeln!(out, "DELAY {:.1}", delay.set_us(us));
                        }
                        _ => {
                            let _ = writeln!(
                                out,
                                "ERR DELAY needs a finite 0..={MAX_LASER_DELAY_US} us"
                            );
                        }
                    },
                    _ => {
                        let _ = writeln!(out, "ERR DELAY [us]");
                    }
                }
            }
            _ => {} // unknown command: ignore
        }
        line.clear();
    }
}

// Turn "SET <x> <y> <laser>" into a clamped setpoint and a dated laser edge.
// Anything malformed is dropped without disturbing the current output.
fn apply(line: &str, setpoint: &AtomicU64, tx: &Sender<LaserMsg>, delay: &LaserDelay) {
    let mut words = line.split_whitespace();
    words.next(); // "SET"
    let x = words
        .next()
        .and_then(|s| s.parse::<f64>().ok())
        .filter(|v| v.is_finite());
    let y = words
        .next()
        .and_then(|s| s.parse::<f64>().ok())
        .filter(|v| v.is_finite());
    let p = words
        .next()
        .and_then(|s| s.parse::<f64>().ok())
        .filter(|v| v.is_finite());
    // three finite numbers, nothing trailing
    let (x, y, p) = match (x, y, p) {
        (Some(x), Some(y), Some(p)) if words.next().is_none() => (x, y, p),
        _ => return,
    };
    let (xi, yi, pi) = (to_i16(x), to_i16(y), to_u16(p));
    setpoint.store(pack(xi, yi, pi), Ordering::Relaxed);
    // The position is in the ring now and reaches the DAC one ring delay later. Dating the edge by the
    // same amount is the whole compensation: light and beam arrive at the same place at the same time.
    let at = Instant::now() + Duration::from_nanos(delay.ns());
    let _ = tx.send(LaserMsg::Edge { at, on: pi > 0 });
}

// Pick the DAC card by name: card indexes move around (HDMI is normally 0).
// Says out loud what ALSA reports, because guessing silently produced pages of
// unrelated "Unknown PCM default" errors when the user simply lacked /dev/snd access.
fn find_dac() -> Option<String> {
    // By name, not by index: a loopback module loaded at boot takes index 0 and pushes the real
    // DAC to 1. The loopback card is deliberately not on this list - driving a silent DAC while the
    // laser still switches would be a quiet failure, so the node refuses to start instead and
    // systemd keeps trying. Bench scripts name the card explicitly (--device hw:3).
    let preferred = ["hifiberry", "simple-audio", "i2s"];
    let cards: Vec<(i32, Result<String, alsa::Error>)> = CardIter::new()
        .filter_map(|c| c.ok())
        .map(|c| (c.get_index(), c.get_name()))
        .collect();
    if cards.is_empty() {
        eprintln!("laser_node: ALSA reports no sound cards (no access to /dev/snd? add the user to group audio)");
        return None;
    }
    for (index, name) in &cards {
        match name {
            Ok(n) => eprintln!("laser_node: card {index} = \"{n}\""),
            Err(e) => eprintln!("laser_node: card {index}: {e} (no access to /dev/snd? add the user to group audio)"),
        }
    }
    for want in preferred {
        for (index, name) in &cards {
            if let Ok(n) = name {
                if n.to_lowercase().contains(want) {
                    eprintln!("laser_node: using card {index} for the DAC");
                    return Some(format!("hw:{index}"));
                }
            }
        }
    }
    None
}

// Run a timing thread at a realtime priority, so the desktop stack cannot hold it off its deadline.
// Needs CAP_SYS_NICE or a raised RLIMIT_RTPRIO; anything else is EPERM and the caller
// keeps running as an ordinary SCHED_OTHER thread.
fn set_realtime(prio: i32) -> Result<(), String> {
    // SAFETY: the caller wants to change the scheduling of the calling thread, pid 0 means
    // "this thread", and sched_param is the plain struct sched_setscheduler expects.
    unsafe {
        let param = libc::sched_param {
            sched_priority: prio,
        };
        if libc::sched_setscheduler(0, libc::SCHED_FIFO, &param) == 0 {
            Ok(())
        } else {
            Err(format!(
                "SCHED_FIFO {prio}: {}",
                std::io::Error::last_os_error()
            ))
        }
    }
}

// Rates the codec/driver combination can actually be asked for, biggest first, nothing above
// what the caller wanted. Advertised is not the same as clockable: the Pi's I2S master clock
// tops out at 12.288 MHz, so a rate can pass hw_params' rate test and still be refused when
// the bit clock is worked out. So the candidates are tried one by one, and whatever stuck is
// printed.
fn rate_candidates(pcm: &PCM, want: u32) -> Vec<u32> {
    const POOL: [u32; 7] = [384_000, 192_000, 96_000, 88_200, 48_000, 44_100, 32_000];
    let Ok(hwp) = HwParams::any(pcm) else {
        return vec![want];
    };
    let mut ok: Vec<u32> = POOL
        .iter()
        .copied()
        .filter(|r| hwp.test_rate(*r).is_ok())
        .collect();
    if hwp.test_rate(want).is_ok() && !ok.contains(&want) {
        ok.push(want);
    }
    ok.retain(|r| *r <= want);
    ok.sort_unstable_by(|a, b| b.cmp(a));
    if ok.is_empty() {
        ok.push(want); // let the driver be the one to say no
    }
    ok
}

// Thread 1: turn the stream of setpoints into one continuous analog signal. Blocking writes
// pace the loop at the sample rate, so no sleeps and no underruns.
//
// Two things happen here that a plain "write the value again" loop does not:
//   * the ring is kept as short as the driver allows - rate and buffer depth are what set the
//     setpoint-to-analog delay, not the write pattern;
//   * every period ramps from the sample we last emitted to the new setpoint, so the DAC never
//     sees a step. A step edge is broadband and lands straight on the mirror's resonance; a
//     ramp buries the same edge (sinc^2 instead of 1/f rolloff).
// The timing knobs as asked for on the command line. The card gets the last say in alsa_loop.
#[derive(Clone, Copy)]
struct Timing {
    rate: u32,
    period: u32,
    periods: u32,
    block: u32,
    ramp: bool,
    rt: Option<i32>,
    explicit_ring: bool,
}

fn alsa_loop(device: &str, cfg: Timing, setpoint: Arc<AtomicU64>, delay: &LaserDelay) {
    let Timing {
        rate: want_rate,
        period: mut period_frames,
        periods: mut buffer_periods,
        block: block_periods,
        ramp,
        rt,
        explicit_ring,
    } = cfg;

    // Realtime first, because it decides how short the ring may be: as an ordinary thread this Pi
    // misses a 0.33 ms write deadline about once a minute, as a SCHED_FIFO thread it does not. The
    // same defaults therefore mean 0.67 ms where realtime is allowed and 2.7 ms where it is not.
    let realtime = match rt {
        Some(prio) => {
            match set_realtime(prio) {
                Ok(()) => {
                    eprintln!("ALSA: SCHED_FIFO priority {prio}");
                    true
                }
                Err(e) => {
                    eprintln!("ALSA: {e} - staying SCHED_OTHER (needs CAP_SYS_NICE or a raised 'ulimit -r')");
                    false
                }
            }
        }
        None => false,
    };
    let safe = deadline_safe_period(want_rate);
    if !realtime && !explicit_ring && (period_frames, buffer_periods) != (safe, FALLBACK_PERIODS) {
        eprintln!("ALSA: no realtime priority, taking the wider ring instead: period {period_frames} -> {safe} frames, periods {buffer_periods} -> {}",
            buffer_periods.max(FALLBACK_PERIODS));
        period_frames = period_frames.max(safe);
        buffer_periods = buffer_periods.max(FALLBACK_PERIODS);
    }
    let pcm = match PCM::new(device, Direction::Playback, false) {
        Ok(p) => p,
        Err(e) => {
            eprintln!(
                "ALSA: cannot open {device}: {e} (check 'ls -l /dev/snd' and the user's groups)"
            );
            exit(1);
        }
    };

    let mut applied = None;
    // Being refused anywhere in here means "try the next candidate", not panic: a rate can pass
    // the rate test and still be rejected once the driver works out the bit clock it would need.
    for rate in rate_candidates(&pcm, want_rate) {
        let attempt = || -> Result<(), alsa::Error> {
            let hwp = HwParams::any(&pcm)?;
            hwp.set_channels(2)?;
            hwp.set_rate(rate, ValueOr::Nearest)?;
            hwp.set_format(Format::s16())?;
            hwp.set_access(Access::RWInterleaved)?;
            // Ask for a small ring: the driver happily defaults to >100 k frames, which would
            // delay every setpoint by seconds. Period first, then the buffer that holds it: asking
            // for the buffer first lets the driver floor everything at its default 256-frame
            // period. Asked in this order the SoC drivers give their real floor, 64 frames.
            hwp.set_period_size_near(period_frames as i64, ValueOr::Nearest)?;
            hwp.set_buffer_size_near((period_frames * buffer_periods) as i64)?;
            pcm.hw_params(&hwp)
        };
        match attempt() {
            Ok(()) => {
                applied = Some(rate);
                break;
            }
            Err(e) => {
                eprintln!("ALSA: {rate} Hz rejected: {e}");
                let _ = pcm.hw_free();
            }
        }
    }
    if applied.is_none() {
        eprintln!("ALSA: no usable sample rate on {device} (asked for {want_rate} Hz)");
        exit(1);
    }

    let hwp = pcm
        .hw_params_current()
        .expect("ALSA: current hardware parameters");
    let period = hwp.get_period_size().expect("ALSA: period size") as usize;
    let buffer = hwp.get_buffer_size().expect("ALSA: buffer size") as usize;
    let rate = hwp.get_rate().expect("ALSA: sample rate") as usize;

    // Start the stream only once the whole ring is filled: that avoids an underrun at startup.
    let swp = pcm.sw_params_current().expect("ALSA: software parameters");
    swp.set_start_threshold(buffer as i64)
        .expect("ALSA: start threshold");
    // Wake us at a period boundary. Waking only when a whole block fits (avail_min = block) is
    // measurably worse: the writer then wakes at the last possible instant with no slack left,
    // and the DMA runs dry - 14 underruns in 60 s at 192 kHz versus none with a period here.
    swp.set_avail_min(period as i64).expect("ALSA: avail min");
    pcm.sw_params(&swp)
        .expect("ALSA: apply software parameters");

    let io = pcm.io_i16().expect("ALSA: 16 bit I/O");
    // One write carries this many periods; never more than the ring holds.
    let block_frames = period * (block_periods as usize).clamp(1, buffer / period).max(1);
    eprintln!("ALSA: {} Hz stereo, buffer = {} frames ({:.1} ms), period = {} frames, write = {} frames, ~{:.0} updates/s",
        rate, buffer, buffer as f64 * 1000.0 / rate as f64, period, block_frames,
        rate as f64 / period as f64);
    if period_frames as usize != period {
        eprintln!(
            "ALSA: asked for a {period_frames} frame period, the driver's floor is {} frames",
            hwp.get_period_size_min().unwrap_or(period as i64)
        );
    }
    if rate != want_rate as usize {
        eprintln!(
            "ALSA: asked for {want_rate} Hz, the driver gave {rate} Hz (its range is {}-{} Hz)",
            hwp.get_rate_min().unwrap_or(0),
            hwp.get_rate_max().unwrap_or(0)
        );
    }
    if !ramp {
        eprintln!("ALSA: ramp off - setpoints are written as steps");
    }

    // The number the laser edges are spaced by, now that the driver has said what it clocks: a setpoint
    // written here is analog on the DAC about this much later, so this is what an edge has to wait.
    if delay.auto {
        delay.ns.store(
            (buffer as f64 * 1e9 / rate as f64).round() as u64,
            Ordering::Relaxed,
        );
    }
    eprintln!("laser: edges are held {:.1} ms so they land with the position they were sent with (DELAY answers the same number)",
        delay.us() / 1000.0);

    let mut buf = vec![0i16; block_frames * 2];
    let ramps = block_frames / period; // periods per write
    let mut cur = [0i32, 0i32]; // the sample we last emitted, per channel: X and Y
    loop {
        // One ramp per period inside the block, each loading the setpoint fresh. With --block 2
        // two periods go out per write, which halves the number of wakeups; --block 1 (the
        // default) paces the loop at one period and measured clean on the Pi.
        for r in 0..ramps {
            let (x, y, _) = unpack(setpoint.load(Ordering::Relaxed));
            let target = [i32::from(x), i32::from(y)];
            let chunk = &mut buf[r * period * 2..(r + 1) * period * 2];
            if ramp {
                ramp_period(&mut cur, target, chunk, period);
            } else {
                cur = target;
                for frame in chunk.chunks_exact_mut(2) {
                    frame[0] = target[0] as i16; // left  = X
                    frame[1] = target[1] as i16; // right = Y
                }
            }
        }
        // writei answers with frames, not samples: 2 samples per frame here.
        match io.writei(&buf) {
            Ok(n) if n == block_frames => {}
            Ok(n) if n > 0 => {
                // ALSA took the first n frames of the block and dropped the rest. Continue the
                // trajectory from the last frame that actually went out - otherwise the discarded
                // tail becomes a step in the analog output, because cur already moved past it.
                cur = [i32::from(buf[n * 2 - 2]), i32::from(buf[n * 2 - 1])];
                eprintln!("ALSA: short write ({n} of {block_frames} frames), continuing from the last frame that went out");
            }
            Ok(n) => eprintln!("ALSA: nothing written ({n} of {block_frames} frames)"),
            Err(e) => {
                // Underrun: the DAC played stale ring content for a moment. cur is deliberately
                // left alone, so the stream resumes from the last value we commanded - the mirrors
                // hold position instead of jumping somewhere.
                eprintln!("ALSA: {e}");
                if let Err(re) = pcm.try_recover(e, true) {
                    // Recovery failed as well: the device is gone or held by somebody else. Back
                    // off instead of spinning - with --rt this thread is SCHED_FIFO, and a hot
                    // loop at realtime priority would starve the rest of the Pi.
                    eprintln!("ALSA: recovery failed: {re}; trying again in 50 ms");
                    thread::sleep(std::time::Duration::from_millis(50));
                }
            }
        }
    }
}

// Fill one period of interleaved stereo frames with a straight ramp from `cur` to `target`,
// leaving `cur` exactly on `target`. Bresenham-style: one division per axis per period, then an
// add and a compare per frame - no division in the hot loop, no drift from period to period,
// and the output stays monotone between the two setpoints.
fn ramp_period(cur: &mut [i32; 2], target: [i32; 2], buf: &mut [i16], period: usize) {
    let period = period as i64;
    let mut step = [0i32; 2];
    let mut rem = [0i32; 2];
    for ch in 0..2 {
        let delta = i64::from(target[ch]) - i64::from(cur[ch]);
        step[ch] = delta.div_euclid(period) as i32;
        rem[ch] = delta.rem_euclid(period) as i32; // 0 <= rem < period, negative delta included
    }
    let period_i32 = period as i32;
    let mut err = [0i32; 2];
    for frame in buf.chunks_exact_mut(2) {
        for ch in 0..2 {
            err[ch] += rem[ch];
            let mut v = cur[ch] + step[ch];
            if err[ch] >= period_i32 {
                err[ch] -= period_i32;
                v += 1;
            }
            cur[ch] = v;
            frame[ch] = v as i16; // stays between start and target, so this cannot wrap
        }
    }
    debug_assert_eq!(*cur, target, "the ramp must land on the setpoint");
}

// Bench client: talk to the running server over the same socket.
fn client(socket: &str, send: Option<(f64, f64, f64)>, get: bool, get_delay: bool) {
    let conn = match std::os::unix::net::UnixStream::connect(socket) {
        Ok(c) => c,
        Err(e) => {
            eprintln!("cannot connect to {socket}: {e}");
            exit(1)
        }
    };
    let mut reader = BufReader::new(&conn);
    let mut reply = String::new();
    if get_delay {
        let _ = writeln!(&conn, "DELAY");
        reply.clear();
        let _ = reader.read_line(&mut reply);
        print!("{reply}");
    }
    if let Some((x, y, p)) = send {
        let _ = writeln!(&conn, "SET {x} {y} {p}");
    }
    if get {
        let _ = writeln!(&conn, "GET");
        reply.clear();
        let _ = reader.read_line(&mut reply);
        print!("{reply}");
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    // The ramp arithmetic is the one part of this node that can be wrong without anything
    // looking wrong on a multimeter: a 1 LSB error per period drifts the mirrors off position.
    #[test]
    fn ramp_lands_monotone_and_inside_the_range() {
        // -32768 is tested on its own further down: both channels share these values negated,
        // and negating i16::MIN is not an i16.
        let ends = [0i32, 1, -1, 32767, -32767, 12345, -23456, 32766, -2];
        for period in [8usize, 63, 64, 1024] {
            for start in ends {
                for target0 in ends {
                    let cur_start = [start, -start];
                    let mut cur = cur_start;
                    let target = [target0, -target0];
                    let mut buf = vec![0i16; period * 2];
                    ramp_period(&mut cur, target, &mut buf, period);
                    assert_eq!(cur, target, "period {period}: {start} -> {target0}");
                    let mut prev = cur_start;
                    for frame in buf.chunks_exact(2) {
                        for ch in 0..2 {
                            let (from, to) = (cur_start[ch], target[ch]);
                            let (lo, hi) = (from.min(to), from.max(to));
                            let v = i32::from(frame[ch]);
                            assert!((lo..=hi).contains(&v), "ramp left its range");
                            let max_slope = ((to - from).abs() + period as i32 - 1) / period as i32;
                            assert!(
                                (v - prev[ch]).abs() <= max_slope,
                                "moved more than one period's slope"
                            );
                            if to > from {
                                assert!(v >= prev[ch], "ramp went backwards");
                            } else if to < from {
                                assert!(v <= prev[ch], "ramp went backwards");
                            }
                            prev[ch] = v;
                        }
                    }
                }
            }
        }
    }

    // Worst case a galvo can be asked for: one rail to the other inside a single period.
    #[test]
    fn full_rail_to_rail_swing() {
        for period in [8usize, 64, 1024] {
            let start = [i16::MIN as i32, i16::MAX as i32];
            let target = [i16::MAX as i32, i16::MIN as i32];
            let mut cur = start;
            let mut buf = vec![0i16; period * 2];
            ramp_period(&mut cur, target, &mut buf, period);
            assert_eq!(cur, target);
            let worst = (65535 + period as i32 - 1) / period as i32; // ceil(delta / period)
            let mut prev = start;
            for frame in buf.chunks_exact(2) {
                for ch in 0..2 {
                    let v = i32::from(frame[ch]);
                    assert!(
                        (v - prev[ch]).abs() <= worst,
                        "one frame moved too far at period {period}"
                    );
                    prev[ch] = v;
                }
            }
        }
    }

    // A held setpoint must produce a perfectly flat signal, not a dithering ramp.
    #[test]
    fn ramp_on_a_held_setpoint_is_flat() {
        let mut cur = [12345, -6789];
        let mut buf = vec![0i16; 128 * 2];
        for _ in 0..4 {
            let held = cur;
            ramp_period(&mut cur, held, &mut buf, 128);
            assert!(buf
                .chunks_exact(2)
                .all(|f| [i32::from(f[0]), i32::from(f[1])] == cur));
        }
    }

    // Consecutive periods must chain: the second ramp starts where the first ended.
    #[test]
    fn ramps_chain_across_periods() {
        let mut cur = [0i32, 0];
        let mut buf = vec![0i16; 64 * 2];
        for target in [[32767i32, -32768], [-32768, 32767], [7, -7], [32767, 32767]] {
            ramp_period(&mut cur, target, &mut buf, 64);
        }
        assert_eq!(cur, [32767, 32767]);
    }

    // The ring the node falls back to when realtime was refused has to keep the deadline it is
    // supposed to be safe at, at every rate the node is willing to try.
    #[test]
    fn the_no_realtime_fallback_keeps_its_deadline() {
        assert_eq!(deadline_safe_period(384_000), 256);
        assert_eq!(deadline_safe_period(192_000), 128);
        assert_eq!(deadline_safe_period(96_000), 64);
        for rate in [32_000u32, 44_100, 48_000, 88_200, 96_000, 192_000, 384_000] {
            let frames = deadline_safe_period(rate);
            let deadline_ms = frames as f64 * 1000.0 / rate as f64;
            assert!(
                frames >= 64,
                "{rate}: {frames} frames is below the driver's floor"
            );
            assert!(
                frames.is_multiple_of(64),
                "{rate}: {frames} is not a multiple of the floor"
            );
            assert!(
                deadline_ms >= 0.6,
                "{rate}: {frames} frames is {deadline_ms:.3} ms"
            );
        }
    }

    #[test]
    fn pack_unpack_and_clamp_roundtrip() {
        for (x, y, p) in [(0i16, 0i16, 0u16), (i16::MAX, i16::MIN, 65535), (-1, 1, 1)] {
            assert_eq!(unpack(pack(x, y, p)), (x, y, p));
        }
        assert_eq!(to_i16(2.0), 32767);
        assert_eq!(to_i16(-2.0), -32767); // -1.0 maps to -32767, the range is symmetric
        assert_eq!(to_u16(1.5), 65535);
        assert_eq!(to_u16(-0.5), 0);
    }

    #[test]
    fn a_digital_line_reports_on_or_off() {
        assert_eq!(report_power(0), 0.0);
        assert_eq!(report_power(1), 1.0);
        assert_eq!(report_power(1234), 1.0);
        assert_eq!(report_power(65535), 1.0);
    }

    // The compensation is a date, not a sleep: an edge is not applied before its deadline and is
    // applied once it has passed.
    #[test]
    fn an_edge_is_not_applied_before_its_deadline() {
        let now = Instant::now();
        let mut q = EdgeQueue::default();
        q.push(now + Duration::from_millis(50), true);
        assert_eq!(q.take_due(now), None, "the line moved early");
        assert_eq!(q.take_due(now + Duration::from_millis(50)), Some(true));
        assert_eq!(
            q.take_due(now + Duration::from_secs(1)),
            None,
            "one edge, one state change"
        );
        assert_eq!(q.len(), 0);
    }

    // Two SETs that land in one wakeup window are one state change: what the line was meant to be at
    // the end of the window is what it becomes, and the flash in between never gets written.
    #[test]
    fn only_the_newest_expired_edge_reaches_the_line() {
        let now = Instant::now();
        let mut q = EdgeQueue::default();
        q.push(now + Duration::from_millis(1), true);
        q.push(now + Duration::from_millis(2), false);
        assert_eq!(q.take_due(now + Duration::from_millis(10)), Some(false));
        assert_eq!(q.len(), 0);
    }

    // Client threads race; the line runs the edges in the order they were meant to happen.
    #[test]
    fn edges_are_earliest_first_whatever_order_they_arrive_in() {
        let now = Instant::now();
        let mut q = EdgeQueue::default();
        q.push(now + Duration::from_millis(30), true);
        q.push(now + Duration::from_millis(10), false);
        q.push(now + Duration::from_millis(20), true);
        assert_eq!(q.next_deadline(), Some(now + Duration::from_millis(10)));
        assert_eq!(q.take_due(now + Duration::from_millis(15)), Some(false));
        assert_eq!(q.next_deadline(), Some(now + Duration::from_millis(20)));
    }

    // A clock thread that is not running must not turn into a laser that lights up late, many
    // millisecond intents deep: the queue keeps the recent ones and drops the stale ones.
    #[test]
    fn a_stalled_clock_drops_the_oldest_intents() {
        let now = Instant::now();
        let mut q = EdgeQueue::default();
        for n in 0..(QUEUE_MAX + 100) {
            q.push(now + Duration::from_millis(n as u64), n % 2 == 0);
        }
        assert_eq!(q.len(), QUEUE_MAX);
        assert_eq!(
            q.next_deadline(),
            Some(now + Duration::from_millis(100)),
            "the 100 oldest edges are gone, not the newest"
        );
    }

    // SET does not drive the pin, it dates the edge. This is the whole compensation, and it is the
    // part a client can get wrong.
    #[test]
    fn a_set_dates_the_edge_itself() {
        let (tx, rx) = std::sync::mpsc::channel::<LaserMsg>();
        let delay = LaserDelay::new(Some(250.0), 333_333);
        let setpoint = AtomicU64::new(pack(0, 0, 0));
        let before = Instant::now();
        apply("SET 0.5 -0.25 1\n", &setpoint, &tx, &delay);
        let after = Instant::now();

        let (x, y, p) = unpack(setpoint.load(Ordering::Relaxed));
        assert_eq!((x, y), (16384, -8192)); // 0.5 and -0.25 of the 32767 range
        assert_eq!(p, 65535);

        match rx.try_recv() {
            Ok(LaserMsg::Edge { at, on }) => {
                assert!(on);
                let held = at.checked_duration_since(before).expect("dated ahead");
                assert!(
                    held >= Duration::from_micros(250) - Duration::from_micros(5)
                        && held <= Duration::from_micros(250) + (after - before),
                    "edge was held {held:?}, expected about 250 us"
                );
            }
            other => panic!("expected an edge, got {other:?}"),
        }
    }

    // Off is off: the third number decides the line by its sign, nothing else.
    #[test]
    fn a_zero_brightness_is_a_park_and_not_an_edge_too() {
        let (tx, rx) = std::sync::mpsc::channel::<LaserMsg>();
        let delay = LaserDelay::new(Some(0.0), 333_333);
        let setpoint = AtomicU64::new(pack(0, 0, 1));
        apply("SET 0 0 0\n", &setpoint, &tx, &delay);
        assert_eq!(unpack(setpoint.load(Ordering::Relaxed)).2, 0);
        match rx.try_recv() {
            Ok(LaserMsg::Edge { at, on }) => {
                assert!(!on);
                assert!(at <= Instant::now(), "--laser-delay 0 means switch now");
            }
            other => panic!("expected an edge, got {other:?}"),
        }
    }

    // Automatic spacing is the ring the node ended up with; a typed number wins over it and says so.
    #[test]
    fn the_ring_delay_is_the_default_spacing() {
        let d = LaserDelay::new(None, 333_333);
        assert!(d.auto);
        assert_eq!(d.ns(), 333_333);
        assert!((d.us() - 333.333).abs() < 0.01);

        let d = LaserDelay::new(Some(120.0), 333_333);
        assert!(!d.auto);
        assert_eq!(d.ns(), 120_000);

        // 0 is a setting, not "no setting": it means the old immediate behaviour.
        let d = LaserDelay::new(Some(0.0), 333_333);
        assert!(!d.auto);
        assert_eq!(d.ns(), 0);

        // Anything that is not a number falls back to the ring delay instead of inventing one.
        let d = LaserDelay::new(Some(f64::NAN), 333_333);
        assert!(d.auto);
        assert_eq!(d.ns(), 333_333);
    }

    // The socket can change the spacing while the node runs, which is what live calibration needs.
    #[test]
    fn the_running_delay_can_be_replaced_and_clamped() {
        let d = LaserDelay::new(None, 333_333);
        assert_eq!(d.set_us(450.0), 450.0);
        assert_eq!(d.ns(), 450_000);
        assert_eq!(d.set_us(-1.0), 0.0);
        assert_eq!(d.set_us(MAX_LASER_DELAY_US + 1.0), MAX_LASER_DELAY_US);
        assert_eq!(d.us(), MAX_LASER_DELAY_US);
    }

    // Malformed commands are dropped without disturbing what is running, and they do not
    // schedule a laser edge either.
    #[test]
    fn a_broken_set_changes_neither_the_position_nor_the_line() {
        let (tx, _rx) = std::sync::mpsc::channel::<LaserMsg>();
        let delay = LaserDelay::new(Some(0.0), 0);
        let setpoint = AtomicU64::new(pack(1000, -2000, 1));
        for bad in [
            "SET 0 0\n",
            "SET 0 0 0 0\n",
            "SET a b c\n",
            "SET nan 0 1\n",
            "SET 0 0 inf\n",
            "SET\n",
        ] {
            apply(bad, &setpoint, &tx, &delay);
        }
        assert_eq!(unpack(setpoint.load(Ordering::Relaxed)), (1000, -2000, 1));
    }

    // Out of range is clamped, which is the node's one rule for every input.
    #[test]
    fn a_set_is_clamped_and_never_rejected() {
        let (tx, _rx) = std::sync::mpsc::channel::<LaserMsg>();
        let delay = LaserDelay::new(Some(0.0), 0);
        let setpoint = AtomicU64::new(pack(0, 0, 0));
        apply("SET 4 -9 3\n", &setpoint, &tx, &delay);
        let (x, y, p) = unpack(setpoint.load(Ordering::Relaxed));
        assert_eq!((x, y, p), (32767, -32767, 65535));
        apply("SET -4 9 -3\n", &setpoint, &tx, &delay);
        let (x, y, p) = unpack(setpoint.load(Ordering::Relaxed));
        assert_eq!((x, y, p), (-32767, 32767, 0));
    }
}
