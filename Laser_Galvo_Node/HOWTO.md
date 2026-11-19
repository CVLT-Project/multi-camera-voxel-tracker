# How to use laser_node

Practical guide: bring the node up, drive the galvos, change the timing, read what the ALSA log is
telling you. `README.md` holds the measurements and the reasoning; this file is the operating manual.

Everything here was run on the bench: Pi 4 (`david@rp4`), PCM5102A on I2S, galvo X/Y on the DAC's left
and right channel, laser driver stage on GPIO 12.

---

## 1. What the software is

One binary on the Pi, `laser-node`, with three threads:

* **ALSA thread** - keeps a continuous stereo stream flowing to the DAC. Left = X, right = Y. Each ALSA
  period is a ramp from the last sample it emitted to the current setpoint, so the DAC never sees a
  step. Runs at `SCHED_FIFO` when the account is allowed to.
* **laser clock** - the only writer of the laser pin. Every edge a client asked for is dated, queued and
  applied at its deadline, so the light arrives together with the position in the same `SET` (section 6).
* **socket loop** - accepts any number of clients on `/tmp/laser.sock`, one thread each, and stores the
  setpoint in one `AtomicU64` (x, y and laser can never be read half-updated).

The laser line is a digital output on GPIO 12 (rppal): high while the value in a `SET` is > 0, low at 0.
There is no modulation frequency, no brightness and no duty floor any more - the hardware-PWM path that
had them was measured on the bench and removed (README, "Laser power: a TTL line").

Ctrl+C, SIGTERM, a panic or a `?` that escapes the code all end with the laser parked: the pin low, and
every edge that had not been applied yet dropped.

There is no watchdog and no fail-safe path, by design (the laser is eye-safe at the output). What the
stream does when nothing is sent: it holds the last setpoint.

---

## 2. First time on a Pi

```bash
PI=david@rp4 ./scripts/deploy.sh          # rsync the sources, build on the Pi (default host: admin@pi3)
PI=david@rp4 ./scripts/autostart.sh       # install + enable the systemd user service, enable linger
```

`deploy.sh` builds in `~/laser_node` with the toolchain in your own account (`~/.cargo/bin`); nothing
system-wide is touched and no root is needed.

One root step on each Pi gets realtime priority for the two timing threads (the ALSA writer and the laser
clock), which is what makes the short ring safe (0.33 ms instead of 2.7 ms) and the edge deadlines land.
Without it the node still works - it just widens its own ring and lets the laser edges move with the rest
of the system:

```bash
sudo mkdir -p /etc/systemd/user.conf.d
sudo printf 'DefaultLimitRTPRIO=90\n' | sudo tee /etc/systemd/user.conf.d/10-rt.conf
sudo printf 'david - rtprio 90\ndavid - nice -10\n' | sudo tee /etc/security/limits.d/60-laser-node.conf
sudo reboot
```

Check it afterwards with `ulimit -r` (should print 90) in a fresh login.

Access groups, if ALSA or the GPIO complains:

```bash
sudo usermod -aG audio david     # /dev/snd
sudo usermod -aG gpio  david     # /dev/gpio* (on Ubuntu a udev rule is needed as well)
```

GPIO 12 has to be a plain output. If a `dtoverlay=pwm` (or `pwm-2chan`) line for it is still in
`/boot/firmware/config.txt` from the old proportional setup, the kernel owns the pin and the node cannot
drive it - `laser_node` then fails with `GPIO: pin not available`. That is one root edit and a reboot:

```bash
sudo nano /boot/firmware/config.txt      # drop every dtoverlay=pwm* line; keep hifiberry-dac and dtparam=audio=off
sudo reboot
```

Afterwards `pinctrl get 12` should read an output rather than `12: a0 ... = PWM0_0`, and
`ls /sys/class/pwm` should be empty. Nothing else in the software touches `/sys/class/pwm`.

---

## 3. Running it

```bash
PI=david@rp4 ./scripts/deploy.sh start              # start the service
PI=david@rp4 ./scripts/deploy.sh stop               # stop it
PI=david@rp4 ./scripts/deploy.sh run                # run in this terminal instead (Ctrl+C stops it)
ssh david@rp4 'systemctl --user --no-pager status laser-node'
ssh david@rp4 'journalctl --user -u laser-node -n 30 --no-pager'
```

The service starts at boot on its own, without a login (`Linger=yes`), and retries if the sound card
appears a moment later. A reboot does not need any manual step.

The startup log tells you what it actually got:

```
laser_node: card 1 = "snd_rpi_hifiberry_dac"
laser_node: using card 1 for the DAC
laser_node: alsa=hw:1 socket=/tmp/laser.sock rate=384000 period=64 buffer=2x block=1x ramp=true rt=50
laser_node: laser = TTL gpio 12
ALSA: SCHED_FIFO priority 50
laser: SCHED_FIFO priority 50
ALSA: 384000 Hz stereo, buffer = 128 frames (0.3 ms), period = 64 frames, write = 64 frames, ~6000 updates/s
laser: edges are held 0.333 ms so they land with the position they were sent with (DELAY answers the same number)
```

Card index, sample rate and period are what the *driver* agreed to, not what was asked for - read
these lines rather than assume them. The edge spacing is the same story: it is what the ring the driver
gave the node turns out to be, unless `--laser-delay` pins it to a number (section 6).

---

## 4. Driving it

### From the command line

```bash
PI=david@rp4 ./scripts/deploy.sh send 0.5 -0.25 1     # x=+0.5, y=-0.25, laser on
PI=david@rp4 ./scripts/deploy.sh send 0 0 0           # park: mirrors centered, laser off
PI=david@rp4 ./scripts/deploy.sh get                  # what the node currently holds
PI=david@rp4 ./scripts/deploy.sh delay                # how far the node holds a laser edge back
```

Or on the Pi itself: `./target/release/laser-node --send 1 -1 1`, `--get`, `--get-delay`.

### Coordinates

| value | meaning |
|---|---|
| `x`, `y` in `[-1, 1]` | position across the field: `0` = center (mid-voltage), `-1`/`+1` = the rails |
| `laser` in `[0, 1]` | the digital line: 0 = low, anything > 0 = high. Nothing in between; the edge is applied `--laser-delay` after the command arrives (section 6) |

Values outside the range are clamped, non-numeric or short lines are dropped without disturbing the
output. `-1` maps to `-32767` and `+1` to `+32767` (a symmetric range, so `0` really is mid-scale).
`GET` answers with the stored values, the laser as 0 or 1.

What the two axes mean physically was measured with the mouse on the mount: **field `+x` is the spot
moving right, field `+y` the spot moving down**. So `x` is the non-inverted rail and `y` the mirrored one
on this bench. The node knows nothing about that - it clamps and scales, nothing else - and the mapping
from a picture to the field lives in one file, `scripts/laser_field.py`, which `svg.py`, `demo.py` and
`mouse_laser.py` share (see the mouse part of section 7).

### From your own program

The protocol is one text command per line on a Unix socket - any language works:

```
SET <x> <y> <laser>\n
GET\n                 ->  "SET <x> <y> <laser>"
DELAY [us]\n            ->  "DELAY <us>"  (with a number: set the edge spacing live, then answer it)
```

Stdlib Python, one connection you keep open (that is the shape a real control program should use):

```python
import socket

class Laser:
    def __init__(self, path="/tmp/laser.sock"):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(path)
        self.io = self.s.makefile("rw")

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def set(self, x, y, laser=0):
        self.io.write(f"SET {x:.6f} {y:.6f} {laser}\n"); self.io.flush()

    def get(self):
        self.io.write("GET\n"); self.io.flush()
        return self.io.readline().strip()

    def park(self):                      # mirrors centered, laser off
        self.set(0, 0, 0)

    def close(self):
        self.park(); self.s.close()

with Laser() as l:
    l.set(0.3, -0.3, 1)
    print(l.get())                       # SET 0.300000 -0.300000 1
```

The `close()` (and so the park) happens even if an exception escapes the block.

Several clients can be connected at once; a client that holds its connection open (the demo, a control
program) does not lock the others out.

---

## 5. Timing: what you get and how to change it

Delay from "socket command" to "voltage on the DAC pins" is `buffer / rate`, nothing else:

| setting | delay | new setpoint picked up | measured on this Pi |
|---|---|---|---|
| 384 kHz, period 64, ring 2 (**default**, realtime granted) | 0.33 ms | 6000/s | 0 underruns in 300 s under load |
| 192 kHz, period 64, ring 2 (realtime granted) | 0.67 ms | 3000/s | 0 underruns in 300 s |
| 192 kHz, period 128, ring 4 (realtime granted) | 2.7 ms | 1500/s | 0 underruns in 300 s |
| any rate, **no** realtime | widened automatically to a 0.67 ms write deadline (2.7 ms at 384 kHz) | 1500/s | 0 underruns in 300 s |
| 384 kHz, period 64, ring 2, **no** realtime | 0.33 ms | 6000/s | 8 underruns in 300 s - do not do this |

Knobs (all on the server side):

```bash
--rate 192000          # 384000 is the default; the node tries high first and falls back with a message
--period 128           # frames per ALSA period: fewer frames = more updates/s AND a steeper ramp
--periods 4            # ring depth in periods: this is the delay knob
--block 2              # periods per write; 1 is the default and the measured-clean pacing
--no-ramp              # steps instead of ramps (for comparing on a scope)
--rt 20                # ask for a different SCHED_FIFO priority
--no-rt                # do not ask for realtime at all
```

Two things to keep in mind when you shrink the period:

* the **write deadline** is one period: at 0.17 ms you need realtime, at 0.67 ms you do not;
* each ramp spans one period, so a shorter period means a **steeper** ramp. If the mirrors ring along
  the drawn lines, `--period 128` (0.33 ms ramps at 384 kHz) is the knob - the delay stays 0.33 ms
  because the ring is still 128 frames.

Latency also shows up where you may not expect it: one `SET` asks for a position and a laser edge, but a
raw GPIO line and a DAC stream do not arrive at the same time - the mirrors land `buffer / rate` after the
command. That is why the laser edge is held back by exactly that interval by default (section 6), and why
`--laser-delay` is the knob if the burn-in at the start of a line still sits a little early or a little
late.

---

## 6. Laser power: a TTL line, and when the edge lands

The laser module on the bench (Laserfuchs LFD650-1-12(9x20), 650 nm, 1 mW, class 2) has **two wires** and
its driver electronics inside the housing: 3..12 V, 25 mA typical, 30 mA max. There is no TTL input to
modulate it through, so the driver stage on GPIO 12 can only switch its supply: the line is high or low,
and a `SET` with a value > 0 means high. The hardware-PWM path that used to chop that supply was measured
on the bench and removed - README, "Laser power: a TTL line", has the numbers (a minimum on time of the
order of 12 µs, and only a narrow frequency/duty window where the chopping looked like brightness at all).

What replaced it is a timing correction instead of a brightness control: the node holds every laser edge
from a `SET` back by a fixed delay, so the light arrives at the point the mirrors have just reached, not at
the point they left.

### The knob

| flag / command | default | what it does |
|---|---|---|
| `--laser-delay <µs>` | `buffer / rate` (0.333 ms with the defaults) | how long a laser edge is held back after its `SET` before it is applied to GPIO 12. `GET` still answers with the value as sent |
| `--laser-delay 0` | - | fire the edge the moment the command arrives - the old behaviour. The mirrors are then `buffer / rate` behind the light: fine for aiming and for slow burns, wrong for the start of a fast vector |
| `DELAY [us]` on the socket, `--get-delay`, `PI=david@rp4 ./scripts/deploy.sh delay` | - | read the spacing the running node is applying; `DELAY <us>` sets it live (clamped to 0..1000000 µs) |
| `--rt <n>` / `--no-rt` | 50 | the laser clock asks for the same realtime priority as the ALSA thread; without it the deadlines land late by whatever else the kernel was running |

An edge is queued with its deadline and one thread (the laser clock) is the only writer of the pin. An
edge whose deadline has already passed is applied at once; edges that fall inside the same wakeup window
collapse to the last one of them, and a queue longer than 4096 edges drops its oldest - a client that
bursts faster than the clock loses detail, and the line keeps the state it was last asked for. Park
(`SET 0 0 0`, Ctrl+C, a panic) drops everything queued and pulls the pin low.

A startup line says what was built, auto or pinned:

```
laser: edges are held 0.333 ms so they land with the position they were sent with (DELAY answers the same number)
```

### Finding your number

`buffer / rate` is the ring's own delay, so the default is a good first guess and no measurement is needed
to start. The simplest beam calibration is `scripts/calibrate-delay.py`: it draws horizontal left-to-right
lines at several speeds, repeats the pattern, and lets the mouse wheel change the running node's delay live.

```bash
PI=david@rp4 ./scripts/deploy.sh delay                                                # what the node holds now
ssh -t david@rp4 'cd laser_node && python3 scripts/calibrate-delay.py --scale 0.7 --speeds 30,60,100,150,200,300'
```

Each wheel notch changes the delay by `--delay-step` (25 µs default) and prints the accepted value. At a
given line speed, a 100 µs delay error moves the burn start/end by `speed * 100 / 1_000_000` field units, so
the fast lines are the ones to read. A dark gap at the left end means the delay is too large; burn before
the intended left end or an early off means it is too small.

For fixed comparison runs instead of the calibration script:

```bash
ssh david@rp4 'cd laser_node && ./target/release/laser-node --laser-delay 0'   # a second run for comparison
python3 scripts/demo.py --speed 300 --pattern lines --lines 1 --duration 5    # one fast vector, watch its start
```

With the delay too small the burn-in sits *behind* the start of the vector, with too large the line starts
short and the spot sits dark at the start point for a moment. At 300 field units/s, 333 µs is 0.1 field unit
of timing error. `--laser-delay 0` is the reference run: it shows the raw skew between the socket line and
the mirrors.

On `rp4` with the defaults the number is 333 µs, which is also what `DELAY` answers; that is the ring, not
a measured optical offset, and it has not been re-tuned against the beam since the PWM path was removed.

### Rehearse the timing without the Pi

```bash
cargo test                                     # includes the laser clock and EdgeQueue tests
python3 scripts/tests/test-mouse.py            # the socket lines mouse_laser.py sends, incl. its DELAY read
```

`cargo test` runs 17 tests: the `AtomicU64` pack/unpack, the clamping of `SET` (including a broken line,
which changes nothing), that a `SET` dates its own edge and that 0 is a park rather than an extra edge, the
queue ordering and its deadline arithmetic, that no edge reaches the pin before its deadline, that a stalled
clock keeps only the newest of the expired ones, the ring delay as the default spacing, the running delay
being replaceable and clamped, and the ramp generator. If you ever want proportional power back, the whole measured PWM module and its scripts
are one commit away: `git show 9d68b4d:src/laser_pwm.rs`, `git show 9d68b4d:scripts/pwm-knee.sh`.

---

## 7. The scripts in `scripts/`

| script | what it is for |
|---|---|
| `deploy.sh` | rsync + build; `run` / `stop` / `start` / `send` / `get` / `delay` subcommands |
| `autostart.sh` | install or refresh the systemd user service, enable it, enable linger |
| `demo.py` | draws circle / square / raster patterns at a spot speed you choose; it computes the point density that needs (stdlib only) |
| `svg.py` | traces a drawing out of an `.svg` file: the file, `--scale`, `--speed`, `--duration` (stdlib only) |
| `calibrate-delay.py` | horizontal left-to-right laser lines at several speeds; the mouse wheel changes the running node's laser-edge delay live and prints the accepted value |
| `tests/run.sh` | the whole no-hardware gate on this machine: `cargo fmt --check`, `cargo clippy --all-targets -- -D warnings`, `cargo test`, and the three Python suites below |
| `tests/test-svg.py` | geometry checks for the SVG reader: beziers, arcs, transforms, what gets skipped (no socket, no hardware) |
| `mouse_laser.py` | point the spot with a real mouse on a headless Pi (`evdev`, no X11/Wayland): virtual cursor, left click as a laser switch, right click to switch the wheel between drawing scale and live laser delay, calibration flags |
| `laser_field.py` | the one place the picture-to-field mapping lives (`--invert-x` off, `--invert-y` on, `--swap-xy` off, `--raw-field` off, `LASER_INVERT_*`): `svg.py`, `demo.py` and `mouse_laser.py` all call it, so they draw the same way |
| `orient-check.py` | twenty seconds at the beam that settles which way a mount draws: walks an asymmetric figure with a pause at every marked point and prints where each one landed |
| `tests/test-orient.py` | the mapping under test: all four corners of a picture through every combination of the settings, plus what each script sends (no socket, no hardware) |
| `tests/test-mouse.py` | `mouse_laser.py` under test: synthetic `/dev/input` events in, the socket lines it sends out, both `evdev.read()` shapes, buttons, wheel, deadband, idle-off, park (no mouse, no node) |
| `soak.sh` | 3000 random setpoints (add `HARSH=1` for one client process per setpoint), reports underrun evidence, kernel stream state, CPU, the GPIO level and the edge spacing the node answers |
| `bench-underrun.sh` | idle or loaded robustness per timing setting, `rate:period:periods:block[:rt]` (`:0` means `--no-rt`) |
| `probe-alsa.sh` | what the card accepts, what the live stream is doing right now, kernel status |
| `test-loopback.sh` | read the i16 samples back through `snd-aloop` - see the caveat inside the file before trusting it on this driver pairing |

```bash
PI=david@rp4 ./scripts/soak.sh                                     # defaults, one open connection
PI=david@rp4 HARSH=1 ./scripts/soak.sh                             # a process per setpoint
PI=david@rp4 ./scripts/soak.sh --period 128                        # same test, gentler ramps
PI=david@rp4 LOAD=1 RUN_SECONDS=300 ./scripts/bench-underrun.sh 384000:64:2:1:50 192000:64:2:1:50
PI=david@rp4 ./scripts/probe-alsa.sh
PI=david@rp4 ./scripts/deploy.sh delay                            # the edge spacing the node is applying
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --speed 100 --pattern lines --duration 10'
ssh david@rp4 'cd laser_node && python3 scripts/orient-check.py --dry'          # which way this mount draws
ssh david@rp4 'cd laser_node && python3 scripts/tests/test-orient.py'                 # the mapping, no hardware
ssh david@rp4 'cd laser_node && python3 scripts/tests/test-mouse.py'                  # the mouse script, no mouse
ssh david@rp4 'cd laser_node && python3 scripts/svg.py hsd.svg --plan-only'
ssh david@rp4 'cd laser_node && python3 scripts/svg.py hsd.svg --speed 60 --scale 0.6 --duration 10'
./scripts/tests/test-svg.py
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --speed 300 --pattern lines --lines 5 --retrace 3'
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --plan-only --pattern all'   # the maths, no laser
```

`demo.py` is meant to be watched, not run as a service; Ctrl+C parks the mirrors at 0,0 with the laser
off. It plans around `--updates 6000`, which is the node's own setpoint rate - read it from the startup
line (`384000 Hz stereo ... period = 64 frames ... ~6000 updates/s`) and pass `--updates` when you run
the node with other settings (period 256 without realtime is 1500/s, `--period 32` would be 12000/s).
If the outline smears or the corners look rounded, the mirrors are outrunning their own slew rate: lower
`--speed`, or lower `--max-step` / `--accuracy` to force more points along the same path. To look at
settling and ringing up close, shrink the drawing instead: `--size 0.3` (a 0.3 u patch) or `--scale 0.1`
(a tenth-size version of whatever you were drawing).

### Pointing it with a mouse

`mouse_laser.py` puts the spot on a physical mouse and needs no desktop: it reads the mouse from
`/dev/input/event*` (the kernel input layer, through `evdev`), so it works in a plain console or over
SSH on a Pi with a USB or Bluetooth mouse plugged into it. Two things to set up first, on the Pi:

```bash
sudo apt install python3-evdev          # the only external package this needs
sudo usermod -aG input david            # /dev/input/event* belongs to the group "input"; log out and in
```

```bash
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --list-devices'   # what is plugged in
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --dry-run'        # calibration, nothing sent
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py'                  # left click = laser switch
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --always-on'      # beam on for aiming
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --sensitivity 0.15'                # what this bench needs on top of the defaults
ssh david@rp4 'cd laser_node && LASER_MOUSE_SENSITIVITY=0.15 python3 scripts/mouse_laser.py'      # the same, from the environment
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --no-invert-y --scale 0.4 --device /dev/input/event5'
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --wheel-step 0.1' # coarser scale wheel: 0.1 field per notch
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --wheel-target delay --delay-step 25' # live delay calibration: 25 us per notch
```

A mouse reports relative motion, so the script owns a virtual cursor in its own -1..+1 space, adds the
counts to it and clamps it at the rails: `--sensitivity` is field units per 100 counts (0.5 crosses the
whole field in 400 counts, about half an inch on an 800 dpi mouse). A tablet or touchscreen reports
absolute position and is used directly - its min..max becomes -1..+1, its corners are the rails.
`--scale` limits the working area, `--deadband` swallows jitter and `--max-hz` caps the send rate.

**Which way it points** is one setting for every script (`mouse_laser.py`, `demo.py`, `svg.py`), in
`scripts/laser_field.py`: `--invert-x` (off), `--invert-y` (**on**), `--swap-xy` (off), `--raw-field`
(off), environment `LASER_INVERT_X` / `LASER_INVERT_Y` / `LASER_SWAP_XY` / `LASER_RAW_FIELD`, and a
script's own flag beats the environment. The cursor you move is a viewer's cursor - pushing the mouse up
lifts the cursor - and the mapping to the field is the one this mount was measured with: `x` unchanged,
`y` negated. `--raw-field` skips the mapping and steers the raw field, which is how the axes get
identified in the first place; `--no-invert-y` is what `--invert-y` used to mean here, and the old
`LASER_MOUSE_*` spellings of the variables are still read.

**The buttons.** Left click is a switch: press once, the beam is on; press again, it is off
(`--hold-laser` is the old held-while-on semantics, `--always-on` forgets the switch for aiming). Right
click cycles the wheel target (`scale -> delay -> scale`), and middle click centres the cursor.
`--idle-off 5` flips the switch off if nothing moved for five seconds.

**The wheel.** In `scale` mode it changes `--scale`, one notch per `--wheel-step` (0.05 default, clamped to
0.01..1.0). In `delay` mode it sends `DELAY <us>` to the running node, stepping the laser-edge spacing by
`--delay-step` (25 µs default) and printing the accepted value on the console/status line. The `laser`
field of `SET` is still only 1 or 0 - the wheel changes the timing, not the beam brightness. Everything in
force stays on the status line:

```
 cursor +0.120 -0.430  ->  x +0.1200 y +0.4300  scale 1.00  wheel delay  laser held 333 us  LASER on  412 sets
```

The first `->` is the orientation: the viewer's cursor, then the numbers that go into the socket. "laser
held" is what the node answered with `DELAY`, so the edge spacing you are drawing against is visible
without a second terminal (section 6). A `--quiet` run, or output that is not a terminal, prints nothing
live.

`--keys` steers the same cursor from the terminal when there is no mouse or no `evdev`: arrows / wasd /
hjkl move, space is the switch, `+` / `-` are the wheel, `t` switches the wheel target, `c` centres,
`q` quits.

Checked on this bench (`rp4`, Logitech MX Vertical; the calibration was made while the node drove the TTL
line and is unchanged by the edge-delay work): moving the mouse right moves the spot right,
moving it up moves the spot **down** - field `+y` is down on this mount, which is why mirroring `y` is the
default and `--sensitivity` is the only calibration left to type. Auto-detect reads every usable device: the
Logitech receiver registers a keyboard interface and a mouse interface with identical capabilities - they
have been `event4`/`event5` and `event0`/`event1` on this same bench - and only the mouse one reports
motion, which is why the script reads them all rather than guessing a number. At the default `--sensitivity 0.5` that mouse is on the rails after a few centimetres;
`0.15` is what the bench runs with. To stop typing it:

```bash
export LASER_MOUSE_SENSITIVITY=0.15                          # field units per 100 counts
export LASER_INVERT_Y=0                                      # only if the mount stops mirroring y
export LASER_MOUSE_SCALE=0.4                                 # working area to start from
```

`python3 scripts/orient-check.py` is the twenty-second version of the same question, and it has been run
here (2026-11-17): tick at the **right** end of the horizontal arrow, tick at the **top** of the vertical
one, the diagonal climbing to the right, the square in the upper left corner - which is what the mapping
above says it should be. `--dry` prints the same figure as numbers before anything moves. The four-corner
`--get` poll `orient-check.py` runs and `scripts/tests/test-orient.py` are the same argument in measurement
and in code; if
the mount is ever rebuilt or an amplifier is swapped, that `orient-check.py` run is what to repeat.

It sends one `SET` per input packet and only when something changed - a still mouse sends nothing and the
script sits blocked in `select()`, so it is not a poller. Ctrl+C, SIGTERM, a crash or unplugging the
mouse all end with `SET 0 0 0`; `--dry-run` prints the mapping without touching the node.

---

## 8. Reading the log

| line | what happened | what to do |
|---|---|---|
| `ALSA: SCHED_FIFO priority 50` | realtime granted, the short ring is safe | nothing |
| `SCHED_FIFO 50: Operation not permitted - staying SCHED_OTHER` | account not allowed | do the root step in section 2, or accept the automatically widened 2.7 ms ring |
| `no realtime priority, taking the wider ring instead` | fallback active, delay is larger | fine; it is the safe configuration |
| `ALSA: 384000 Hz rejected: ...` | driver could not clock that rate | the node fell back to a lower rate; that is expected behaviour |
| `asked for a 32 frame period, the driver's floor is 64 frames` | driver minimum period | ask for 64 |
| `ALSA: short write (n of m frames)` | the writer woke late; ALSA dropped the tail of a block | the output stays continuous (the ramp resumes from the last frame that went out) - it is a timing hiccup, not a jump. Occasional: harmless. Frequent: your ring/deadline is too tight |
| `ALSA: ... 'Broken pipe (32)'` | real underrun, the DMA ran dry | for up to one ring's time the analog output replays recent valid samples, then the stream is re-primed and continues from the last commanded position. No drift, no jump. Frequent: widen the ring or get realtime |
| `Device or resource busy` at startup | another process holds the DAC | `pkill -x laser-node`, or stop a `deploy.sh run` session before starting the service |
| `no usable DAC card; name one with --device hw:N` | the I2S overlay is missing or the card is not there | check `dtoverlay=hifiberry-dac` in `/boot/firmware/config.txt`; the node retries via systemd rather than driving a silent card |
| `laser_node: laser = TTL gpio 12` | the line is a digital output, as intended | nothing |
| `GPIO: cannot open /dev/gpiomem (is this a Pi, and is the user in group gpio?)` | the node may not reach the GPIOs | the `usermod -aG gpio` step in section 2 (plus the udev rule on Ubuntu) |
| `GPIO: pin not available` | something else owns GPIO 12 - usually a leftover `dtoverlay=pwm` line | section 2: drop the overlay and reboot; `pinctrl get 12` should read an output |
| `laser: SCHED_FIFO priority 50` | the laser clock is realtime, so the edge deadlines land on time | nothing |
| `laser: SCHED_FIFO 50: Operation not permitted - edges will move with the rest of the system` | no realtime for the laser thread | the ring delay is still applied, but with the jitter of an ordinary thread; do the root step in section 2 |
| `laser: edges are held 0.333 ms ...` | the spacing in force (auto or `--laser-delay`) | `DELAY` on the socket answers the same number if a client needs it |

A quiet stream at the last setpoint is normal behaviour: nothing has to be "kept alive" from the
control side, and a lost command never moves the mirrors by itself.

---

## 9. Bench checklists

**After a reboot** - nothing to do, but confirm it:

```bash
ssh david@rp4 'systemctl --user --no-pager status laser-node | head -3; journalctl --user -u laser-node -n 6 --no-pager'
ssh david@rp4 'ps -eLo pid,tid,cls,comm | grep laser-node'      # two FF (realtime) threads, ALSA and the laser clock
```

**Try a different latency setting, then verify it under load:**

```bash
PI=david@rp4 ./scripts/deploy.sh stop
ssh david@rp4 'cd laser_node && ./target/release/laser-node --rate 192000 --period 64 --periods 2 &
               sleep 3; python3 scripts/demo.py --speed 100 --pattern lines --duration 20'
ssh david@rp4 'pkill -x laser-node; systemctl --user start laser-node'
```

**Before trusting a new Pi:** `deploy.sh`, `autostart.sh`, `probe-alsa.sh`, `soak.sh`, then the
multimeter pass - see "Analog checkout" in `README.md` (full-scale output is ~2.1 V RMS on a
PCM5102A, so a scope probe on X/Y while `--send 1 1 0` is the direct check of the whole chain).

**The laser side:**

```bash
ssh david@rp4 'journalctl --user -u laser-node -n 20 --no-pager | grep laser'   # "TTL gpio 12", the edge spacing, SCHED_FIFO for the clock?
PI=david@rp4 ./scripts/deploy.sh delay                       # what the running node holds an edge back by
pinctrl get 12                                               # on the Pi: an output, not PWM0 / SDA5
PI=david@rp4 ./scripts/deploy.sh send 0 0 1                  # the beam lights where the mirrors are parked
PI=david@rp4 ./scripts/deploy.sh send 0 0 0                  # and goes out again
```

**End a session safely:** `deploy.sh send 0 0 0`.

---

## 10. Things worth knowing

* `/tmp/laser.sock` is open to every local user on the Pi. Fine on a bench, not a control interface for
  a networked machine.
* GPIO 12 is only driven once the node has started, and `into_output_low` is what claiming it does: the
  pin is an input until then, so what the laser driver sees in the seconds between power-on and the
  service starting depends on that driver's own input bias - a pull-down question, not a software one. A
  stopped, restarting or crashed node leaves the pin low, and its handler gives the laser clock the moment
  it needs to write that low.
* GPIO 18/19/21 belong to I2S on this overlay, so GPIO 12 is the free one. It has to stay a plain output:
  a `dtoverlay=pwm` line for it (the old proportional experiment) hands the pin to the kernel and the node
  refuses to start with `GPIO: pin not available`.
* The laser value is a level, not a current and not a duty ratio. The module wants 25 mA at 3..12 V; the
  GPIO drives the driver stage, and all the software can choose is on or off - which is why section 6 is
  about *when* the edge lands rather than how bright the spot is.
* A bigger `--block` sounds attractive (half the wakeups) and measured worse, because ALSA wakes at a
  period boundary either way. Leave it at 1 unless you have a measurement saying otherwise.
