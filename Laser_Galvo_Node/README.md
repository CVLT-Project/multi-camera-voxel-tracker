# laser_node

Galvo (X/Y) + laser controller for a Raspberry Pi, per `Task.md`.

**To use it: [`HOWTO.md`](HOWTO.md)** - deploy, drive the socket, pick the timing, read the log. This
file is the measurements and the reasoning behind the defaults.

Two machines are involved:

| host | hardware | role | ALSA card | GPIO access |
|---|---|---|---|---|
| `admin@pi3` | Pi 3, Raspberry Pi OS 13 | first target, no DAC wired | `hw:1` `snd_rpi_hifiberry_dac` | group `gpio` (preinstalled) |
| `david@rp4` | Pi 4 Model B, Ubuntu 26.04 | the bench with the PCM5102A wired | `hw:1` `snd_rpi_hifiberry_dac` (index moves: a `snd-aloop` module loaded at boot takes 0; the node picks the card by name) | group `gpio` via udev rule; also needs group `audio` for `/dev/snd` |

* X and Y: continuous stereo stream to a PCM5102A I2S DAC through ALSA (left = X, right = Y)
* Laser: GPIO 12 as a plain digital output - above 0 in a `SET` is on, 0 is off
* Control: line protocol on a Unix domain socket

Single binary (`laser-node`), three threads (ALSA, the laser clock, the socket loop), two dependencies
(`alsa`, `rppal`), one source file `src/main.rs` including its `#[cfg(test)]` module: the ramp arithmetic,
which is the one part that can be wrong without showing up on a multimeter, and the laser edge schedule,
which is the one part that can be wrong without showing up on a scope either.

## Status

Verified software-side on both hosts (rustup toolchain in the user account, `rustc 1.99.1`,
release build 17-33 s on the Pi):

* **Measured on the `rp4` bench with the current build** (`kernel 7.0.0-1023-raspi`, Ubuntu 26.04,
  card 1 `snd_rpi_hifiberry_dac`): the node runs **384 kHz stereo S16_LE, period 64 frames, buffer
  128 frames = 0.33 ms** setpoint-to-output delay, **6000 setpoint updates/s**, on a
  `SCHED_FIFO priority 50` ALSA thread, and every ALSA period is a **ramp** from the sample it last
  emitted to the new setpoint instead of a step. Confirmed from the kernel side: `rate: 384000 /
  period_size: 64 / buffer_size: 128 / state RUNNING`, and `ps -eLo cls` shows the ALSA thread as `FF`.
* Cleanliness at those settings, `underruns` = `Broken pipe` + `short write` log lines:

  | run | length | underruns | CPU |
  |---|---|---|---|
  | `bench-underrun.sh 384000:64:2:1:50`, demo traffic | 300 s | **0** | 16.7 % |
  | `soak.sh`, 3000 setpoints on one open connection | 60 s | **0** | 15.5 % |
  | `soak.sh HARSH=1`, a client process per setpoint | 105 s | **0** | 15.3 % |
  | same ring without realtime (fallback shape, 256 x 4) | 300 s | 0 | 7.1 % |
  | same tight ring **without** realtime | 300 s | 8 + 6 short writes | 18.3 % |

* What the same machine does at tighter or looser settings, all measured: 192 kHz at period 64 / ring 4
  (1.33 ms, 0.33 ms deadline) without realtime took ~1 hiccup per minute; 384 kHz at that ring without
  realtime took 8 underruns in 300 s; `avail_min` set to the write block instead of a period was worse
  still (14 and 29 underruns per 60 s) - the writer then wakes with no slack left. With realtime, all
  of 0.33 ms / 0.67 ms / 2.7 ms measured 0 underruns in 300 s. See `scripts/bench-underrun.sh`.
* Realtime scheduling **is** available on `rp4` since the root step described under "Realtime
  priority": `ulimit -r` is 90 in a fresh login, `/proc/<service pid>/limits` reports
  `Max realtime priority 90`, and the ALSA thread runs `SCHED_FIFO`. On a host where that step was
  never done the node falls back to a 0.67 ms deadline by itself.
* What the card actually offers (`aplay -D hw:0 --dump-hw-params`, see `scripts/probe-alsa.sh`):
  `RATE [8000 384000]`, `FORMAT S16_LE S24_LE S32_LE`, `PERIOD_SIZE [32 65536]`, `PERIODS [2 4096]`,
  `BUFFER_SIZE [64 131072]`. Asking for a 32 or 16 frame period in practice yields 64, so 64 is the
  usable floor even though the capability list says 32.
* Measured on the bench with the previous 48 kHz build, for comparison: stereo S16_LE, period 64
  frames, buffer 256 frames = **5.3 ms** delay, **~750 setpoint updates/s**, 2.9 % CPU idle and 4.3 %
  while demoing
* Why a small ring matters: the driver default is 131072 frames (2.7 s of latency), and the period has
  to be requested **before** the buffer - asking for the buffer first let the driver floor everything
  at 256 frames (~188 updates/s). 64 frames is this driver's floor.
* 60 s soak on `pi3` with ~3000 random setpoints: **no underruns, no ALSA errors**, 1.5 % CPU, 2.9 MB RSS
* laser pin verified again on `rp4` after the PWM overlay was removed (`pinctrl get 12`): `12: op -- pd | hi` while a soak holds power = 1, `12: op -- pd | lo` after parking; `DELAY` answers `333.3` with the default 384 kHz / period 64 / ring 2 timing
* **the laser line is TTL again.** The hardware-PWM path (`src/laser_pwm.rs`, `--laser pwm`, `--freq`,
  `--min-duty`, `--min-on`, `--raw-duty`, `--u8`, `--pwm`, `--sweep`) was built, measured on the bench and
  removed: at the modulation frequencies the module needed it was never better than on/off for drawing,
  and its two properties - a duty floor (`12 µs / period`, i.e. 48 % of a 40 kHz period) and an edge that
  can only move to the next period boundary - are exactly what made the start and end of a traced line
  land in the wrong place. What the bench measured while it existed is written down under
  "Laser power: a TTL line", so the numbers are not lost.
* 17 Rust tests (`cargo test`) and 3 Python test scripts (`scripts/tests/`, `./scripts/tests/run.sh`)
  cover the ramp, the setpoint packing, the fallback ring, the edge schedule (deadline, coalescing,
  ordering, queue cap) and the clamp rules.
* **Orientation verified at the beam** (`rp4`, 2026-11-17): field `+x` is the spot moving right, field `+y`
  the spot moving **down** - measured with the mouse, then confirmed by `scripts/orient-check.py` (tick at
  the right end of the horizontal arrow, tick at the top of the vertical one, square in the upper left
  corner). The mapping lives once in `scripts/laser_field.py` and `svg.py`, `demo.py` and `mouse_laser.py`
  all use it, so one drawing is no longer right side up while the next one is mirrored. **`svg.py`'s
  default changed with it**: x is no longer mirrored, `--invert-x` puts the old output back.
  `scripts/tests/test-orient.py` (34 checks) and `scripts/tests/test-mouse.py` (28) are the tests that
  keep it.
* clamping, garbage lines and wrong argument counts verified through the socket
* autostart on **both** hosts: user service `laser-node.service`, `enabled`, linger on
  (`Linger=yes`), `StartLimitIntervalSec=0` + `RestartSec=3` so a card that appears slightly late
  at boot is retried instead of leaving the unit failed
* verified by rebooting the rp4: boot 11:06:13, service started within ~5 s, before any login or
  ssh connection; `NRestarts=0`

Verified on `rp4`: `sudo usermod -aG audio david` fixed ALSA access; card 0 is picked by name; a
60 s soak with ~3000 setpoints ran clean (no underruns) and `pinctrl get 12` shows BCM 12 going
`hi`/`lo` with laser power. The older 48 kHz build (period 64, buffer 256, 5.3 ms, ~750 updates/s,
2.9 % CPU idle / 4.3 % while demoing) is still reachable with `--rate 48000 --period 64`.
`pi3` has not been re-tested since the change - it is a second host and needs the same deploy.
What is left: the analog measurement with a multimeter (see "Analog checkout"), and calibrating
`--laser-delay` at the beam - where the start and end of a traced line land is what that number decides
(see "Laser power: a TTL line"). The sample-level
loopback read-back is available (`snd-aloop` is loaded at boot on `rp4`) but does not work as a health
test on this driver pairing - see the note in `scripts/test-loopback.sh`.

Note: `/tmp/laser.sock` is open to any local user on the Pi, which is fine for a bench setup.

## Build and run

```bash
PI=david@rp4 ./scripts/deploy.sh                # sync + build (default host is admin@pi3)
PI=david@rp4 ./scripts/deploy.sh run            # ...and run in this terminal (stops the service first)
PI=david@rp4 ./scripts/deploy.sh send 0.5 -0.25 1
PI=david@rp4 ./scripts/deploy.sh get
PI=david@rp4 ./scripts/deploy.sh delay                  # how far the running node holds a laser edge back
PI=david@rp4 ./scripts/soak.sh                  # 3000 setpoints on one connection, underrun evidence
./scripts/autostart.sh                          # install/refresh the systemd user service (both hosts)
PI=david@rp4 ./scripts/probe-alsa.sh            # what the card accepts + live hw_params + stream state
PI=david@rp4 ./scripts/bench-underrun.sh 192000:128:4:1 192000:64:4:1:50   # rate:period:periods:block[:rt]
./scripts/test-loopback.sh                      # optional: read the i16 samples back with snd-aloop (see the caveat in that file)
./scripts/tests/run.sh                          # every check that needs no Pi: cargo test + the three Python ones
./scripts/tests/test-svg.py                     # geometry checks for the SVG reader in scripts/svg.py
./scripts/tests/test-orient.py                  # the picture-to-field mapping svg.py / demo.py / mouse_laser.py share
./scripts/tests/test-mouse.py                   # mouse_laser.py under test: synthetic events in, socket lines out
ssh david@rp4 'cd laser_node && python3 scripts/orient-check.py --dry'   # which way this mount draws
ssh -t david@rp4 'cd laser_node && python3 scripts/calibrate-delay.py --scale 0.7'   # horizontal-line delay calibration
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py'   # point the spot with a mouse on the Pi (python3-evdev)
```

The service starts at boot without a login; no manual start is needed. To stop it:
`ssh david@rp4 'systemctl --user stop laser-node'` (disable it entirely with `disable --now`).

Four knobs decide the timing, and all of them are the same trade-off - slack for latency:

| knob | default | what it does |
|---|---|---|
| `--rate <hz>` | 384000 | samples per second; tried high-first, falls back to 192000 / 96000 / 88200 / 48000 / 44100 / 32000 with a message |
| `--period <frames>` | 64 | how often a new setpoint is picked up (`rate / period` updates/s) **and** how much time one write is allowed to take; 64 is the driver's usable floor, asking for less silently gives 64 and says so |
| `--periods <n>` | 2 | ring depth in periods; `period * periods / rate` is the setpoint-to-analog delay |
| `--block <n>` | 1 | periods per write. 1 is the natural pacing; bigger blocks wake half as often but eat the slack, because ALSA wakes at a period boundary either way |
| `--rt <prio>` | 50 | run the ALSA thread **and** the laser clock thread SCHED_FIFO at priority `prio` (1-99). Needs `CAP_SYS_NICE` or a raised `RLIMIT_RTPRIO`; if that is refused the node says so in the log and widens the ring to keep a 0.67 ms deadline |
| `--no-rt` | - | do not ask for realtime at all (then the wider ring is what you get, unless you also name a period and a ring depth) |
| `--laser-delay <µs>` | - | how far a laser edge is held back behind the `SET` that asked for it. Without the flag the node uses its own ring delay (`buffer / rate`), which is how long the position in the same `SET` takes to reach the DAC; `0` switches the moment a `SET` arrives |

`--no-ramp` puts the old step behaviour back, which is the switch to flip when comparing the
staircase against the ramp on a scope or with `test-loopback.sh`.

`--laser-delay` is the compensation for the one thing the two output paths cannot share: the position
travels through an ALSA ring, the laser is one GPIO write. Spacing the edge by the same delay is what
makes "off during a blank move" land where the beam actually is, and it is the number to calibrate at
the beam (see "Laser power: a TTL line"). `DELAY` on the socket answers what a running node applies, and
`DELAY <us>` changes that spacing while the node is running.

What the bench says about these knobs (`rp4`, `scripts/bench-underrun.sh` and `scripts/soak.sh`,
25-300 s each, underruns counted as `Broken pipe` + `short write`):

| configuration | delay | write deadline | result |
|---|---|---|---|
| 384 kHz, period 64, ring 2, block 1, SCHED_FIFO 50 (**default**) | 0.33 ms | 0.17 ms | **0 underruns, 0 short writes** in 300 s with demo traffic, in `soak.sh` and in `soak.sh HARSH=1`; CPU 16 % |
| 384 kHz, period 256, ring 4, block 1, **no** realtime (what the node falls back to) | 2.7 ms | 0.67 ms | 0 / 0 in 300 s with demo traffic; CPU 7 % |
| 384 kHz, period 64, ring 2, block 1, **no** realtime | 0.33 ms | 0.17 ms | 8 underruns + 6 short writes in 300 s - this is exactly what the fallback is there to prevent |
| 192 kHz, period 64, ring 2, block 1, SCHED_FIFO 50 | 0.67 ms | 0.33 ms | 0 / 0 in 300 s |
| 192 kHz, period 128, ring 4, block 1, SCHED_FIFO 50 | 2.7 ms | 0.67 ms | 0 / 0 in 300 s; CPU 6.7 % |
| 192 kHz, period 64, ring 4, block 1, no realtime | 1.33 ms | 0.33 ms | 1 underrun + 1 short write per 180 s with demo traffic |
| any, `avail_min` = write block instead of a period | - | - | 14 and 29 underruns per 60 s: the writer wakes with no slack left |
| 384 kHz, period 64, ring 2, block 1, SCHED_FIFO 50 | 0.33 ms | 0.17 ms | 0 / 0 in 240 s with the **speed-driven demo** asking for a point per update slot (~6000 setpoints/s from one client); CPU 24 % including the demo |
| 384 kHz, period 256, ring 4, block 1, **no** realtime | 2.7 ms | 0.67 ms | 0 / 0 in the same 240 s at ~6000 setpoints/s; CPU 15 % |

"demo traffic" in the earlier rows is the older `demo.py`, which sent one point every 2 ms (~500
setpoints/s); the last two rows are against the current speed-driven demo, which fills every update
slot. The default setting is clean under both.

The honest budget: **a write has to be served within one period**. As an ordinary thread this Pi
meets a 0.67 ms deadline and misses a 0.33 ms one about once a minute; as a `SCHED_FIFO` thread it met
a 0.17 ms deadline in every 300 s run measured so far. The hiccups are stochastic rather than a
threshold you can sit safely below - the 2.7 ms setting measured 0 in six bench runs and 1 short write
+ 1 underrun in a 180 s run as a service with no client traffic at all.

So the node takes its ring depth from the answer to the realtime question: 64 x 2 frames where
realtime was granted (0.33 ms), and the wider ring that keeps a 0.67 ms deadline where it was not.
`--period 64 --periods 2 --no-rt` is how you ask for the tight one anyway.

### Realtime priority (`--rt`, default 50)

The misses were never CPU shortage - the node idles at 3-17 % - they are the ALSA thread being held
off its write deadline by everything else that wants the CPU (kernel threads, snapd, tailscaled, the
ssh session; there is no desktop running on this Pi). `SCHED_FIFO` removes that, and that is what
makes a 0.33 ms delay a setting that can be trusted instead of a coin toss.

`--rt <prio>` applies it to the ALSA thread and to the laser clock thread; the socket threads stay
ordinary. Verified on the bench after the root step below: the log says `ALSA: SCHED_FIFO priority 50` and
`laser: SCHED_FIFO priority 50`, `/proc/<pid>/limits` of the service reports
`Max realtime priority 90`.

Asking for realtime needs `CAP_SYS_NICE` or a raised `RLIMIT_RTPRIO`, which on a fresh Pi is one root
step. Both files are persistent and the user manager reads the first one when it starts, so this
survives reboots (checked after a reboot):

```bash
sudo mkdir -p /etc/systemd/user.conf.d
sudo printf 'DefaultLimitRTPRIO=90\n' | sudo tee /etc/systemd/user.conf.d/10-rt.conf
sudo printf 'david - rtprio 90\ndavid - nice -10\n' | sudo tee /etc/security/limits.d/60-laser-node.conf
sudo reboot            # or: logout/login, so the user manager and the session pick the limit up
```

Then `ulimit -r` prints 90 in a fresh login and the node gets its priority without any extra flag.
If the account is *not* allowed to do this, nothing breaks either: the node logs
`SCHED_FIFO 50: Operation not permitted - staying SCHED_OTHER`, widens the ring so the deadline is
0.67 ms again, and says so in the same log line. `--no-rt` skips the attempt.

To bench both sides of it (`0` means `--no-rt`, because the node asks for realtime on its own now):

```bash
PI=david@rp4 LOAD=1 RUN_SECONDS=300 ./scripts/bench-underrun.sh 384000:64:2:1:50 384000:64:2:1:0
```

The alternative, if you would rather not touch the login limits, is a *system* unit that runs as the
user and hands the process the one capability it needs (`User=david`, `Groups=audio`,
`AmbientCapabilities=CAP_SYS_NICE`, `LimitRTPRIO=90`); that also means the node no longer runs as a
user service, so it is not what this setup uses today.

Safety note for the realtime case: with `SCHED_FIFO` a runaway loop would starve the whole Pi, so
the ALSA error path sleeps 50 ms when recovery itself fails instead of spinning, and the laser clock
sleeps until 60 µs before an edge's deadline and spins only across those 60 µs (`SPIN_NS`). The ALSA path
never spins - it blocks in `writei` and lets the kernel pace it - and the laser clock blocks in
`recv()` whenever nothing is scheduled.

Until realtime is set up on a host, the node runs as an ordinary thread and the delay is 2.7 ms
instead of 0.33 ms - measured, not guessed.

### What survives a reboot (checked on `rp4`)

| thing | why it survives | checked |
|---|---|---|
| the service itself | user unit `laser-node.service`, `enabled`, `Linger=yes` so it starts without a login; `StartLimitIntervalSec=0` + `Restart=on-failure` so a card that appears slightly late at boot is retried instead of leaving the unit failed | yes: started by itself after the reboot |
| realtime priority | `/etc/systemd/user.conf.d/10-rt.conf` sets the user manager's default `RLIMIT_RTPRIO`, `/etc/security/limits.d/60-laser-node.conf` sets it for the login; both are plain files owned by root | yes: `ulimit -r` 90, service process `Max realtime priority 90`, ALSA thread `FF` |
| which ALSA card is the DAC | the node matches card **names** (`hifiberry`, `simple-audio`, `i2s`), never an index | yes: `snd-aloop` loaded at boot took index 0 and pushed the DAC to `hw:1`; the node logged `using card 1` |
| the control socket | a leftover `/tmp/laser.sock` from an earlier run is removed before binding | yes |
| the I2S overlay | `dtoverlay=hifiberry-dac` in `/boot/firmware/config.txt` | yes |
| the laser pin | GPIO 12 stays a plain output: no `dtoverlay=pwm*` line for it anywhere in `/boot/firmware/config.txt` | yes, 2026-11-18 after the overlay was removed: `pinctrl get 12` reads `12: op -- pd | lo // GPIO12 = output`, and `/sys/class/pwm` is empty |

Two things to know about. If the DAC overlay ever disappears, the node refuses to start ("no usable
DAC card") and systemd keeps retrying - it deliberately does **not** fall back to the loopback card,
because driving a silent DAC while the laser still switches is a failure you would not hear. And GPIO
12 is only driven once the node has started: before that the pin is an input, so what the laser driver
sees during the ~5 s between power-on and the service starting depends on that driver's own input
bias. If your driver needs a defined "off" there, that is a pull-down resistor question, not a
software one.

For reference, the old 48 kHz build measured: 64 frames = 5.3 ms and ~750 updates/s at 2.9 % CPU idle
/ 4.3 % while demoing; 128 frames = 10.7 ms, 375 updates/s, 1.3 %; 256 frames = 21.3 ms, 188 updates/s,
0.6 %. Still reachable with `--rate 48000 --period 64`.

On the Pi directly:

```bash
cd ~/laser_node && ~/.cargo/bin/cargo build --release
./target/release/laser-node --help
./target/release/laser-node                      # server: 384 kHz, period 64, ring 2, realtime
./target/release/laser-node --rate 192000        # server, if 384 kHz is refused by the driver
./target/release/laser-node --period 128         # gentler ramps (0.33 ms each), same 0.33 ms delay
./target/release/laser-node --no-rt              # ordinary thread: the ring widens to 256 x 4 on its own
./target/release/laser-node --no-ramp            # steps instead of ramps
./target/release/laser-node --laser-delay 400    # hold every laser edge 400 us behind its SET
./target/release/laser-node --send 1 -1 1        # client
./target/release/laser-node --get
./target/release/laser-node --get-delay
```

## Protocol

`/tmp/laser.sock`, one command per line:

```
SET <x> <y> <laser>     x, y in [-1, 1]  -> i16 -32768..32767, left/right channel
                        laser in [0, 1]  -> GPIO 12 high if > 0, low at 0. The edge is not applied when
                        the line arrives: it is dated by the node's laser delay, so it lands together
                        with the position in the same command
GET                     -> answers "SET <x> <y> <laser>" with the stored values, the laser as 0 or 1
DELAY [us]              -> answers "DELAY <us>", the edge spacing in use; with a number it sets it live
```

Values are clamped to the valid range; NaN, non-numeric or wrong-arity lines are dropped without
affecting the current output. The stream keeps running at the last setpoint, so a command loss
never moves the galvos on its own. Each connection gets its own thread, so a client that holds the
socket open (the demo, a control program) does not lock out the others.

## Demo

`scripts/demo.py` (stdlib Python, run manually - it is not a service). You tell it how fast the spot
should travel; it works out how many points that needs out of the node's 6000 updates per second:

```bash
PI=david@rp4 ./scripts/deploy.sh                                        # brings scripts/demo.py along
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --speed 10'                  # 5 s per pattern
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --plan-only --pattern all'   # maths, no laser
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --speed 2 --size 0.3'        # small patch, settling up close
ssh david@rp4 'cd laser_node && python3 scripts/demo.py --speed 300 --pattern lines --duration 10'
```

| argument | default | meaning |
|---|---|---|
| `--speed` | 10 | spot speed in field units per second (1.0 = centre to one rail) |
| `--size` | 1.6 | width and height of the drawing: `--size 2` fills the whole field, `--size 0.2` is a small patch |
| `--scale` | 1 | multiplier on that size: `--scale 0.1` draws a tenth-size pattern in the middle of the field |
| `--radius` | 0.8 | half size, the older spelling; `--size` wins when both are given, and `--scale` is applied to either |
| `--updates` | 6000 | the node's setpoint rate, which must match its `--rate`/`--period`: 384000/64 = 6000, `--no-rt` fallback 384000/256 = 1500 |
| `--pattern` | `all` | `circle`, `square`, `lines` (raster) or `all` |
| `--spacing` | 0.1 | distance between raster lines, in absolute field units - `--scale` therefore changes how many lines fit, not how dense they are |
| `--lines` | from `--spacing` | lines per direction (17 at the default size and spacing) |
| `--max-step` | 0.05 | biggest step allowed along a straight edge, so the staircase stays invisible |
| `--accuracy` | 0.005 | how far a chord is allowed to cut inside a curve |
| `--samples` / `--points` | computed | force a fixed number of points per raster line / per circle or square edge (old staircase mode) |
| `--duration` | 5 | seconds per pattern |
| `--hold` | 0.3 | pause between patterns |
| `--retrace` | 1 | speed multiplier for the blanked moves between lines (`0` is one jump, the old behaviour) |
| `--endless` | off | draw until Ctrl+C |
| `--plan-only` | off | print the density and timing without touching the galvos |
| `--socket` | `/tmp/laser.sock` | |

A drawing that does not fit the field is clamped to it with a message rather than silently clipped:
`--size 3` prints "a 3.00 u drawing does not fit the field (0.10 .. 2.00), drawing at 2.00 u instead".
`--size 0.3` was checked by polling `--get` while it drew: the commanded setpoints stayed inside
±0.1500 exactly.

How it sizes things: `--speed / 6000` is the step per update slot, then `--max-step` caps a straight
edge and `sqrt(8 R · --accuracy)` caps the chords of a curve - the step is the smallest of those, so
a slow shape holds one point per slot with fine steps, and a fast one holds one point per slot with
coarse steps until the step limit caps the speed and the plan says so. A circle at `--radius 0.8` with
the default accuracy is 37 chords, and the density is spread over the whole outline rather than rounded
up inside each chord, so the drawn speed is what you asked for (298 u/s at `--speed 300`, not 259).

Patterns: circle, square, then raster scans - horizontal lines swept left to right, worked from top to
bottom, then vertical lines swept top to bottom, worked from left to right. Laser on while a line is
drawn, off during the moves between them; Ctrl+C or the end always parks the mirrors at 0,0 with the
laser off. Every pattern is redrawn continuously for its duration, which is what fuses the shape into
a steady outline.

Measured on the rp4 with the galvo connected, node at 384 kHz / period 64 / realtime:

| run | points per cycle | plan | measured |
|---|---|---|---|
| `--speed 10 --pattern circle` | 3011 | 1.99 /s, 6000 pts/s, 10.0 u/s | 1.99 /s, 5999 pts/s, 10.0 u/s |
| `--speed 100 --pattern square` | 384 | 15.6 /s, 6000 pts/s, 100.0 u/s | 15.6 /s, 5993 pts/s, 99.6 u/s |
| `--speed 300 --pattern lines --lines 5 --retrace 3` | 674 | 8.90 /s, 6000 pts/s, 300.9 u/s | 8.88 /s, 5996 pts/s, 299.5 u/s |

The node logged no underruns or short writes during those runs. The ceilings are the shape limits,
not the node: `--max-step 0.05` at 6000 updates/s caps a straight edge at 300 u/s, and the chords of
a circle at `--radius 0.8` with `--accuracy 0.005` cap it at about 1070 u/s. Both ceilings rise with
`--rate`/`--period`: at 384 kHz / period 32 the node takes 12000 setpoints per second and `--updates`
is where you tell the demo about it.

If corners look rounded or the outline smears, the mirrors are outrunning their own slew rate and
settling time - raise `--delay` or lower `--radius`.

## Tracing an SVG file

`scripts/svg.py` traces a drawing out of a file. Its arguments are the file, `--scale`, `--speed` and
`--duration`; it imports the density and pacing code from `demo.py` rather than repeating it, so a
setpoint still lands once per update slot and the ramping stays the node's job.

```bash
PI=david@rp4 ./scripts/deploy.sh                                                    # .svg files travel along
ssh david@rp4 'cd laser_node && python3 scripts/svg.py hsd.svg --plan-only'        # geometry and density, no laser
ssh david@rp4 'cd laser_node && python3 scripts/svg.py hsd.svg --speed 60 --scale 0.6 --duration 10'
ssh david@rp4 'cd laser_node && python3 scripts/svg.py logo.svg --only-stroke --speed 120'
./scripts/tests/test-svg.py                                                              # 57 checks on the reader
```

| argument | default | meaning |
|---|---|---|
| `file` | - | the `.svg` to trace |
| `--scale` | 1.0 | size as a fraction of the field: 1.0 spans it edge to edge, 0.25 is a quarter of it |
| `--speed` | 10 | spot speed in field units per second |
| `--duration` | 5 | seconds to keep tracing the drawing |
| `--accuracy` | 0.005 | how far the traced path may sit from the shape in the file; it sets how finely curves are flattened **and** how much of the file's own point density a straight line may cover |
| `--max-step`, `--retrace`, `--updates`, `--socket` | as in `demo.py` | biggest commanded move, speed of the blank moves between subpaths, the node's setpoint rate, socket path |
| `--only-stroke` | off | trace only the shapes that say they are stroked (inherited from a group counts) |
| `--invert-x`, `--invert-y`, `--swap-xy`, `--raw-field` | x kept, y mirrored (the bench default) | the shared orientation of `scripts/laser_field.py`, the same flags in `demo.py` and `mouse_laser.py`; SVG's y axis points down, so the picture is `x - middle, middle - y` and the mapping from the picture to the field is one setting for every script. `--no-invert-x` / `--no-invert-y` turn one axis back, `--raw-field` sends the viewer coordinates with nothing applied |
| `--no-flip-x`, `--no-flip-y` | off | the older spelling of `--no-invert-x` / `--no-invert-y`, still accepted |
| `--no-simplify` | off | keep every point the file and the flattening produce |
| `--plan-only`, `--endless` | off | print the plan, or trace until Ctrl+C |

What it reads, with the standard library only: `<path>` with `M L H V C S Q T A Z` in absolute and
relative form, `<line>`, `<polyline>`, `<polygon>`, `<rect>`, `<circle>`, `<ellipse>`, `<g>` and nested
`<svg>` with `translate` / `scale` / `rotate` / `skewX` / `skewY` / `matrix`, and `<use>` references
into `<defs>`. What it skips and says so: `<text>`, `<image>`, `<symbol>`, clip/mask/pattern/marker
definitions, and the rounded corners of a `<rect>` (they are smaller than the laser spot). A `<style>`
block with CSS classes is not interpreted - styling is read from the `fill` / `stroke` / `display` /
`visibility` attributes and the inline `style=`, including inherited ones.

Subpaths are traced in document order with the laser on; the move from the end of one to the start of
the next, and the walk back to the start at the end of the cycle, are walked with the laser off at
`--retrace` times the speed.

Measured with `hsd.svg` in the project root (12 closed outlines, 211.5 x 139.5 user units, node at
384 kHz / period 64 / realtime):

| run | plan | measured |
|---|---|---|
| `--speed 60 --scale 0.6` | 4.17 cycles/s, 6000 pts/s, 59.7 u/s drawn | 4.16 /s, 5998 pts/s, 59.7 u/s |
| `--speed 190 --scale 0.5 --retrace 3` | 15.42 /s, 164.3 u/s drawn, 11.95 u per cycle | 15.36 /s, 5991 pts/s, 183.5 u/s over the cycle |
| the same traced while polling `--get` | widest extent 0.500 x 0.330 u | 0.497 x 0.327 u |
| `--speed 200 --scale 1` | 7.98 /s, 188 u/s drawn, 752 points per cycle | - |

The note on the 190 u/s line is the file talking back: `hsd.svg` flattens to 1237 points and
`--accuracy 0.005` allows 244 of them to be covered by a straight line, and the remaining corners are
0.027 u apart, which at 6000 updates/s is 164 u/s. Honouring every path command the file carries would
cap it near 60 u/s (`--no-simplify` measures exactly that), and `--accuracy 0.001` raises the ceiling
to 138 u/s at 600 points. `--max-step`, `--accuracy`, `--updates` and `--speed` are the four knobs that
trade shape fidelity for speed. Over roughly ten minutes of that tracing the node logged one hiccup - a
32 of 64 frame short write followed by one underrun, the same stochastic pair the timing section
already describes - and 0 in three further 50 s runs back to back.

Which way the drawing comes out was checked with a four-line file - one line in each corner of the
picture - traced slowly while `--get` was polled, so the sign of the commanded setpoint says where each
line landed (the laser flag in the reply separates drawn from blank moves). Field `+x` is the spot moving
right and field `+y` the spot moving **down** - measured with a mouse on the mount - so the row that puts
the picture's top left at `-x-y` is the row that comes out the way the file looks on the screen. That row
is what `svg.py`, `demo.py` and `mouse_laser.py` do by default now, from one place, and it has been
confirmed at the beam with `scripts/orient-check.py`:

| spelling | picture top-left → top-right → bottom-left → bottom-right ends up as | on the wall |
|---|---|---|
| **default** (`--no-invert-x`, y mirrored) | `-x-y` `+x-y` `-x+y` `+x+y` | **the way the file looks** |
| nothing applied (`--raw-field`) | `-x+y` `+x+y` `-x-y` `+x-y` | flipped top to bottom |
| x mirrored, y not | `+x+y` `-x+y` `+x-y` `-x-y` | turned by 180 degrees (computed, not polled) |
| x and y mirrored (the old default here, `--invert-x` today) | `+x-y` `-x-y` `+x+y` `-x+y` | mirrored left to right |

The first entry of each measured row is missing from the poll (it started 1.5 s in, and those lines are
1.25 s long at `--speed 0.4`); the rest of each sequence matches. **The default of `svg.py` changed on
2026-11-17**: x is no longer mirrored, because the mouse on this mount showed the x rail to be the
non-inverted one. `--invert-x` puts the old spelling back, and `python3 scripts/orient-check.py` is the
short way to find out what a mount actually does - it walks an asymmetric figure and prints the field
number of every part. `scripts/tests/test-orient.py` keeps the mapping itself from drifting again.

## Pointing it with a mouse

`scripts/mouse_laser.py` puts the spot under a physical mouse. It reads `/dev/input/event*` through
`evdev`, i.e. the kernel input layer, so it runs on a headless Pi over SSH with a USB or Bluetooth mouse
plugged into the board: no X11, no Wayland, no `DISPLAY`. An ordinary mouse reports relative motion, so
the script keeps a virtual cursor in its own -1..+1 space and clamps it at the rails; a tablet or
touchscreen (`ABS_X`/`ABS_Y`) is used directly, its own corners becoming the rails.

```bash
sudo apt install python3-evdev                    # on the Pi
sudo usermod -aG input "$USER"                     # then log out and back in
PI=david@rp4 ./scripts/deploy.sh                   # scripts/mouse_laser.py travels with the rest
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --dry-run'   # calibration, nothing sent
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --list-devices'
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --sensitivity 0.15'   # what this bench needs
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --scale 0.4'          # the middle 0.8 u only
ssh david@rp4 'cd laser_node && python3 scripts/mouse_laser.py --wheel-target delay --delay-step 25'  # draw a cross, right click switches between scale and delay
```

**Left click is a switch** - press for the beam, press again for off; `--hold-laser` is the old
held-while-on semantics and `--always-on` forgets the switch for aiming. **Right click switches what the
wheel changes**: `scale` adjusts `--scale` (`--wheel-step` of the field per notch), `delay` asks the running
node to change its live laser-edge spacing (`--delay-step` µs per notch). Middle click centres the cursor.
The script starts from what the node is already holding (`GET` for the position and whether the line is lit,
`DELAY` for the edge spacing the node applies) and prints both, so the status line says what the beam is
doing and where the laser edge will land.
`--sensitivity` (field units per 100 mouse counts), `--scale`, `--wheel-step` and the orientation flags of
the next section are the calibration knobs, `--deadband` and `--max-hz` the traffic knobs, `--idle-off` a
laser timeout, `--keys` a terminal fallback when there is no evdev or no mouse.
Ctrl+C, SIGTERM, a crash or the mouse being unplugged all end with `SET 0 0 0`.

## Which way the field points

`SET 0.5 0.5 1` is not self-describing: it is half right of centre on one channel and half up-scale on the
other, and what the spot does on the wall depends on how the two amplifier outputs are wired. On this mount
- measured with the mouse, and independently by the four-corner SVG test above - the field signs are:

| field value | the spot |
|---|---|
| `+x` | moves right |
| `+y` | moves **down** |

so a viewer's picture - x right, y up - reaches this field as `x -> x`, `y -> -y`. That mapping is one
setting for every script, in `scripts/laser_field.py`, and `svg.py`, `demo.py` and `mouse_laser.py` all
take the same four flags and the same environment variables:

| flag | environment | here |
|---|---|---|
| `--invert-x` | `LASER_INVERT_X` | off: the x rail is not inverted |
| `--invert-y` | `LASER_INVERT_Y` | **on**: the y rail is |
| `--swap-xy` | `LASER_SWAP_XY` | off: channels are not exchanged |
| `--raw-field` | `LASER_RAW_FIELD` | off: send what the script computed, with nothing applied |

A script's own flag wins over the environment; `--no-invert-x` / `--no-invert-y` turn one axis back, and
the old `LASER_MOUSE_*` spellings of these variables are still read. The order is swap first, then invert,
and it applies to both channels - `--swap-xy --invert-y` is not `--invert-y --swap-xy` in effect, it is one
setting. **`svg.py`'s default changed on 2026-11-17**: it used to mirror both axes, which on this mount put
the picture backwards; it now draws the way the file looks, and `--invert-x` puts the old output back.

Each script reports what it sends rather than what it computed: the mouse status line shows both
(`cursor +0.120 -0.430 -> x +0.1200 y +0.4300`, the cursor being the viewer's), and the mapping it is
using is printed in its banner at startup. To identify a mount that is not yet known:

```bash
python3 scripts/orient-check.py --dry          # print the plan, nothing sent
python3 scripts/orient-check.py                # the spot walks the figure, pausing at every marked point
```

It draws an asymmetric figure - an arrow to the right with a tick on its end, an arrow up with a tick on
its end, a diagonal from lower left to upper right, a square in the top left corner - and prints where
every marked point lands:

```
 orientation: x as the picture has it, y mirrored  [LASER_INVERT_Y]
 the corners of the picture, as the field values that go out:
   top right     x +1.00  y -1.00
   top left      x -1.00  y -1.00
   bottom right  x +1.00  y +1.00
   bottom left   x +1.00  y +1.00

 where each marked point lands, with this mapping:
      field y     -0.80    -0.68    -0.56    -0.28     0.00     0.68     0.80
         0.80                                         start
         0.68              start
         0.28                                                            tick
         0.00     start                                                   tip
        -0.56    corner            corner
        -0.68                                                    end
        -0.80    corner            corner     tick      tip
```

Rows are field y from +1 at the top of the listing down to -1, and field `+y` is the spot moving down, so
the **first** row of that map is the lowest place on the wall and the last row the highest. Read that way
the figure came out the way the picture is drawn: the upward arrow's tip in the top row, the square in the
upper left, the diagonal running from lower left to upper right. At the beam the same thing is seen by
eye - the tick has to sit at the **right** end of the horizontal arrow and at the **top** of the vertical
one, the square in the upper left corner - and a tick on the other side names the axis to fix, in
`scripts/laser_field.py` for good or with `LASER_INVERT_X` / `LASER_INVERT_Y` / `LASER_SWAP_XY` for one
run.

**Run on the rp4 bench on 2026-11-17, at the beam:** tick at the right end of the horizontal arrow, tick at
the top of the vertical one, the diagonal climbing to the right, the square in the upper left corner -
exactly the figure the mapping says. So `laser_field.py` describes this mount, and `svg.py`, `demo.py` and
`mouse_laser.py` draw the same picture on it without being told anything.

## Why a ramp, and why 384 kHz

Two separate problems were in the first version.

**The staircase.** A new setpoint used to appear at a period boundary, so the DAC output was a
staircase whose step height was the whole command delta. Step edges are broadband: they land on the
mirror's resonance and come back as ringing along the drawn lines. Each ALSA period now ramps from
the sample it last emitted to the new setpoint. Integer Bresenham arithmetic: one division per axis
per period, an add and a compare per frame - no division in the hot loop. `period * step + rem ==
delta`, so the ramp lands exactly on the setpoint on its last frame, never overshoots and never
drifts from period to period. `cargo test` proves that part (6 tests, pure arithmetic, no hardware).

**The delay.** Setpoint-to-analog delay is `buffer / rate`, full stop. The old 256-frame ring at
48 kHz was 5.3 ms. 128 frames at 384 kHz is 0.33 ms - but that also means every write has to land
within 0.17 ms, which an ordinary thread on this Pi does not manage (8 underruns in 300 s). A
`SCHED_FIFO` thread does manage it, in every run measured so far, so the default is 384 kHz with a
64 x 2 ring and the node asks for realtime by itself. Where realtime is refused, it widens the ring
until the deadline is 0.67 ms again instead of losing samples. The higher rate also shrinks the DAC's
own filter delay (FLT jumper, below).

**Why S16_LE and not S32_LE.** The card does offer `S24_LE` and `S32_LE`, and the node will accept
them if asked, but there is nothing to win: the Pi's I2S clock tops out at 12.288 MHz, and at
384 kHz stereo that is exactly what 16-bit slots already need (384000 · 2 · 16 = 12.288 MHz). 32-bit
slots would need 24.576 MHz, so at the default sample rate 32-bit is not even available; at 192 kHz,
32-bit slots sit at the same 12.288 MHz ceiling. On top of that the PCM5102A is a 112 dB-SNR part
(~17-18 effective bits), while one 16-bit LSB at its 2.1 V RMS full scale is 91 µV - below the galvo
amplifier's own offset. Sample rate and the ramp are the levers here, word length is not.

## What a short write and an underrun actually do

Both show up as log lines, and they mean different things:

**`short write (n of m frames)`** - ALSA took the first `n` frames of the block and dropped the rest,
because the writer woke late. The output does **not** step: the loop re-reads the last frame that
actually went out and continues the ramp from there, so the scan is a few tenths of a millisecond
later in time but continuous in level.

**`Broken pipe` (EPIPE, a real underrun)** - the DMA ran dry. For up to one ring's worth of time the
analog output replays whatever the ring still held, which is only ever valid data this node wrote
(recent ramps and setpoints), so the spot follows recent commanded positions rather than jumping to
noise. Then `try_recover` re-primes the stream and the loop resumes from `cur`, which is deliberately
not reset - the mirrors pick up at the last commanded position. Net effect: a hold or flicker of at
most `buffer / rate` = 2.7 ms, no drift, no permanent position error. At the demo's ~465 points/s a
2.7 ms hold is a few percent of the field on one line segment, and only if it lands while the laser is
on. With the current defaults it measured zero occurrences over idle 120 s, demo 90 s, soak 60 s and
harsh soak 60 s; at 1.33 ms it was about one a minute.

## Laser power: a TTL line, and when an edge lands

GPIO 12 driven by `rppal`, one writer (`laser_clock` in `src/main.rs`), and the `--laser-delay` spacing.

**What the laser module is, because that decides everything else.** The bench part is a Laserfuchs
LFD650-1-12(9x20): 650 nm dot laser, 1 mW, laser class 2, **two wires** (+3..12 V DC, GND), 25 mA
typical / 30 mA max, with its driver electronics inside the housing. There is no TTL input and no analog
dim input to modulate it with. So the only thing the GPIO can do for it is switch its supply through a
driver stage: the laser is lit, or it is not.

**Why on/off, and why the edge is dated.** A digital line has no period an edge has to wait for, no
minimum on time a short "off" can fall through, and no floor a brightness has to be remapped onto - which
is what a galvo drawing needs: a blank move has to be dark from the first sample to the last. What it does
have is the skew between the two output paths: a setpoint is written into an ALSA ring and comes out of
the DAC `buffer / rate` later (0.33 ms at the default 384 kHz / 64 frames / 2 periods), while a laser edge
would otherwise be applied the moment its `SET` is read. Light switching over a position the mirrors have
not reached yet is the smeared start and end of every traced line, and it is a whole ring delay wide - far
more than the GPIO write itself.

So `apply()` does not drive the pin: it dates the edge (`Instant::now() + delay`) and hands it to the
`laser_clock` thread, which is the only writer of the pin. The default delay is the ring delay the ALSA
thread ended up with, published by `alsa_loop` once the driver has said what it clocks; `--laser-delay
<µs>` pins it to a measured number, `--laser-delay 0` is the old immediate behaviour. `DELAY` on the
socket answers what a running node applies, `DELAY <us>` changes it live, and `scripts/deploy.sh delay`
prints it.

**The clock thread.** Edges sit in an order-preserving queue (`EdgeQueue`) keyed by deadline. The thread
sleeps until 60 µs before the next deadline and waits that last stretch out in a loop, because
`thread::sleep` is a millisecond instrument and 400 µs late is a visible blob on the beam; with `--rt` it
is a `SCHED_FIFO` thread like the ALSA one. Edges whose deadline passed in one wakeup are coalesced to the
newest state - an on and an off inside one wakeup is a flash shorter than the line can be told about. A
queue deeper than 4096 means the thread is not running, and it drops the stale intents rather than
lighting the beam late for all of them. Ctrl+C, SIGTERM, `Drop`: the line goes low (`laser: parked ->
TTL gpio 12`).

**Calibrating the delay.** The compensation is only right if the number is the delay the beam actually
travels, and there is a second unknown on top of it: how long the driver stage and the module take to
actually go dark. Start with what the log prints (`laser: edges are held 0.33 ms ...`), then draw a
pattern with long blank moves - `scripts/demo.py --retrace 4`, or `scripts/svg.py` on a file with several
subpaths - and read where the burn starts and stops relative to where the line was meant to start:

* the burn begins **inside** the drawn line → the laser is early, raise `--laser-delay`
* the burn begins **after** the line has started → the laser is late, lower it (the module's own turn-on
  time is part of this)
* a tail at the end of every drawn line → too much delay, or the module's turn-off time

`soak.sh` prints the spacing a running node applies, and `--send 1 1 1` / `--send 0 0 0` with a scope on
the driver stage is the direct way to see the edge against the analog ramps.

**What the PWM path measured before it was removed (2026-11-17, rp4, `--pwm` / `--sweep`, mapping off).**
Worth keeping, because it is the reason the module is driven on/off now:

* at `--pwm 0.3` the spot started to dim somewhere between 2500 and 3000 Hz and kept dimming as the
  frequency rose; at `--pwm 0.7` it did **not** get dimmer anywhere up to 50 kHz
* at 40 kHz, walking the duty down: **0.5 is dark and 1.0 is full power** - 12.5 µs of on time is not
  enough for this module
* 200 Hz was the sweet spot for dimming: full brightness, and clean dimming over the whole duty range,
  because 12 µs there is 0.24 % of the period
* `period` written from 1 s down to 10 µs reads back exactly, so none of the above is the SoC's limit
* two readings of the same data: the module integrates its own supply (its current regulator and
  capacitance average fast chopping, so at a high duty it simply stays lit), or the driver stage on
  GPIO 12 has a bandwidth of its own. The dark-at-50 %-of-25-µs datum is the one that says a *time* is
  involved; the dim-at-30 %-at-3 kHz datum is the one that says a single fixed time is not the whole story.

Both readings say the same thing about drawing: below a few kilohertz the duty is a brightness knob the
module follows, and at the chopping rates that would be flicker-free the module either stays lit or goes
dark without a usable middle. Which is the argument for a digital line and a well-placed edge.

**Tests.** 17 `cargo test` cases cover the laser side of the arithmetic that can be wrong quietly: an edge
is not applied before its deadline, only the newest expired edge reaches the line, edges are earliest-first
whatever order the client threads deliver them in, a stalled clock thread drops the oldest intents, `SET`
dates its own edge instead of driving the pin, `--laser-delay 0` means now, the automatic spacing is
the ring delay, and a live `DELAY <us>` setting replaces/clamps the spacing. None of that measures the beam;
the calibration above does.

## Hardware

Pi side (`/boot/firmware/config.txt`, already applied):

```
dtparam=audio=off
dtoverlay=hifiberry-dac        # codec-less simple card; kernel binds the pcm5102a driver
```

Breakout -> Pi (BCM numbering):

| PCM5102A | Pi GPIO (BCM) | Physical pin |
|---|---|---|
| BCK | 18 | 12 |
| LRCK | 19 | 35 |
| DIN | 21 | 40 |
| SCK | tied to GND | - |
| VIN | 5 V | 4 |
| GND | GND | 6 |

SCK on GND is correct: the PCM5102A runs in PLL mode, i.e. a **3-wire I2S** link where the Pi supplies
only BCK and LRCK and the DAC generates its own master clock (datasheet §9.3.5, "3-wire I2S connection").

**Numbering trap:** the DAC uses *physical* pin 12, which is **BCM GPIO 18**. The laser uses
**BCM GPIO 12**, which is **physical pin 32**. They are different pins; do not put the laser on
physical pin 12. rppal always takes BCM numbers, hence `--gpio 12`.

Jumpers on the breakout: **FMT low** (I2S, not left-justified), **DEMP low** (44.1 k de-emphasis off —
it would distort a DC value), **XSMT high** (not muted), **SC/LR in stereo** so left is X and right is Y.

**FLT is worth checking: low today, high is better for a galvo.** FLT picks the interpolation filter:
20 tS group delay for normal latency, 3.5 tS for low latency (datasheet, Typical Performance). At
48 kHz that is 417 µs vs 73 µs, at 192 kHz 104 µs vs 18 µs. The low-latency filter is not linear
phase, but for a DC-coupled position signal only the group delay matters, so high is the right side.

Laser: **BCM GPIO 12** (physical pin 32). GPIO 18/19/21 are taken by I2S, so the spec's suggestion
of GPIO 18 cannot be used, and the SoC's analog audio output sits on the PWM channels - which is why
`dtparam=audio=off` is in `config.txt` above. The pin drives the *driver stage* of the laser module, not
the module: the LFD650's own electronics need 3..12 V at ~25 mA, and a GPIO gives 3.3 V at a few mA, so
switching the pin switches the module's supply. GPIO 12 stays a plain output - no `dtoverlay=pwm*` line
for it (the PWM path that used it was measured and removed, see "Laser power: a TTL line").

## Analog checkout (needs a multimeter)

1. Wire the six lines above, check the jumpers.
2. `PI=david@rp4 ./scripts/probe-alsa.sh` - what the card accepts, what the node ended up with, and
   the live XRUN counters. Do this before trusting any latency number.
3. `PI=david@rp4 ./scripts/deploy.sh run`
4. Send extremes and measure DC at the DAC's L and R outputs:
   * `send 1 1 0` -> maximum positive on both
   * `send -1 -1 0` -> maximum negative
   * `send 0 0 0` -> 0 V
   * `send 0.5 -0.25 0` -> +half on L, -half on R
   Expect **2.1 V RMS = 2.97 V peak** full scale on a bare PCM5102A (datasheet, "full-scale
   single-ended output 2.1 V RMS"); the earlier note here said "about +2 V peak". If the bench shows
   ~2 V, the breakout's output resistors or the galvo amp's input impedance are attenuating it -
   measure it once and use that number for calibration instead of the datasheet one.
5. `PI=david@rp4 ./scripts/soak.sh` with the DAC loaded: it prints the live stream state (including
   the kernel's `delay` in frames) and counts underrun evidence before and after ~3000 random
   setpoints. `HARSH=1` does the same with a client process per setpoint.
6. Optional, no scope needed, needs `sudo modprobe snd-aloop` once on the Pi:
   `PI=david@rp4 ./scripts/test-loopback.sh` reads the exact i16 samples back through the loopback
   driver and fails if a ramp overshoots, is not monotone, does not land on the setpoint, or if a
   frame moves more than one period's slope (i.e. if it is still a step).
