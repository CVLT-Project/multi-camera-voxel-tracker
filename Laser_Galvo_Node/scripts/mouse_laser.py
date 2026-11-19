#!/usr/bin/env python3
"""Point the galvos with a real mouse, on a Pi with no desktop.

    python3 scripts/mouse_laser.py                          # auto-detect the mouse; left click = laser
    python3 scripts/mouse_laser.py --always-on              # laser on the whole run, for aiming
    python3 scripts/mouse_laser.py --sensitivity 0.2        # slow, fine pointing
    python3 scripts/mouse_laser.py --scale 0.4              # work only in the middle 0.8 u of the field
    python3 scripts/mouse_laser.py --invert-y               # spot moves opposite to the mouse on Y
    python3 scripts/mouse_laser.py --swap-xy                # the rails are swapped
    python3 scripts/mouse_laser.py --device /dev/input/event3
    python3 scripts/mouse_laser.py --list-devices           # what is plugged in, and what it can do
    python3 scripts/mouse_laser.py --wheel-step 0.1         # bigger wheel steps in the working area
    python3 scripts/mouse_laser.py --wheel-target delay     # wheel changes the node's --laser-delay live
    python3 scripts/mouse_laser.py --delay-step 25          # us per wheel notch in delay mode
    python3 scripts/mouse_laser.py --keys                   # no mouse / no evdev: arrow keys instead
    python3 scripts/mouse_laser.py --dry-run                # calibration check, nothing reaches the node

**Left click is a switch**: press it and the beam is on, press it again and it is off. **Right click
switches what the wheel changes** (`scale -> delay -> scale`), and middle click centres the cursor. In
`scale` mode the wheel limits the working area (`--scale`, one notch per `--wheel-step`). In `delay` mode
the wheel asks the running node to apply a new laser-edge spacing (`--laser-delay` equivalent, one notch
per `--delay-step` µs), so a cross or a long line can be redrawn while watching where its start lands.
Everything currently in force is on the status line:

    cursor +0.120 -0.430  ->  x +0.1200 y +0.4300  scale 1.00  wheel delay 333 us  LASER on  412 sets

`--hold-laser` is the old semantics (left button held = on, released = off) for anyone who prefers it.
Ctrl+C, SIGTERM, a crash or a lost socket always park the mirrors at 0,0 with the laser off.

Why evdev
---------
The mouse is read from /dev/input/event*, i.e. from the kernel input layer, so no X11, no Wayland, no
framebuffer and no DISPLAY are needed: a USB or Bluetooth mouse plugged into a headless Pi (or a plain
SSH session on it) works. evdev is the only external piece:

    sudo apt install python3-evdev          # Raspberry Pi OS bookworm / trixie
    python3 -m pip install evdev            # if you would rather have it in a venv

Devices live in the group "input", and a normal account is usually not a member of it:

    sudo usermod -aG input "$USER"          # then log out and back in (or reboot)
    sudo python3 scripts/mouse_laser.py     # ...or the one-off way, only until the group took effect

Without evdev the script says so and points at --keys, which steers the same virtual cursor from the
terminal (arrows / WASD / hjkl, space latches the laser, c centres, + / - scale, q quits).

Which device
------------
Auto-detect reads every /dev/input/event* that has REL_X/REL_Y or ABS_X/ABS_Y and feeds all of them into
the same virtual cursor. That is deliberate: a Logitech combo receiver registers the keyboard interface
and the mouse interface as two devices with identical capabilities - "which eventN is the mouse" is not a
question its capabilities can answer - while only the mouse one ever reports motion, so reading both is
what makes pointing work without knowing the number. --list-devices prints what is there, --device PATH
narrows it to one (repeat the flag to combine a mouse and a tablet, for instance).

Relative and absolute mice
--------------------------
An ordinary mouse reports *relative* motion (REL_X / REL_Y, "I moved 7 counts"), so this script keeps a
virtual cursor in its own [-1, +1] space, adds the counts to it, clamps it at the rails and maps it to
the node. --sensitivity is how far that cursor goes per 100 mouse counts: 0.5 (the default) crosses the
whole field in 400 counts, which is about half an inch on an 800 dpi mouse; 0.15 is fine work, 1.5 is
sloppy-fast. A tablet or touchscreen reports *absolute* position (ABS_X / ABS_Y), and that is used
directly: its own min..max is stretched onto -1..+1, so the tablet's corners are the rails and there is
nothing to accumulate. A device with both is treated as absolute.

Calibration
-----------
The cursor lives in the space a viewer reads a picture in: mouse right is +x, mouse up is +y. How that maps
onto the rails is the question every script here has to answer the same way, and the answer lives in one
place - `scripts/laser_field.py` - with the same flags (`--invert-x`, `--invert-y`, `--swap-xy`,
`--raw-field`, each with its `--no-` spelling) and the same environment variables (`LASER_INVERT_X`,
`LASER_INVERT_Y`, `LASER_SWAP_XY`; `LASER_MOUSE_*` still work as the older spelling) in `svg.py`, `demo.py`
and this script. Mirrors are applied first, the swap second, `--scale` last, so what leaves the script is
always inside [-scale, +scale].

The bench default is the measured one: x as the picture has it, **y mirrored**. On this mount that is what
makes the spot follow the hand - without it, moving the mouse up moves the spot down - and it is the same
mapping `svg.py` now applies to a drawing, which is the point of the shared module: what the mouse draws
and what the SVG file draws are the same picture on the same wall. `python3 scripts/orient-check.py` walks
an asymmetric figure and prints the field numbers of every part, which is how you find out what another
mount needs; `--raw-field` is there when you want to see a script's own numbers with nothing applied.

--scale is a workspace limit, not a magnification: --scale 0.5 keeps the whole cursor travel inside the
middle 1.0 x 1.0 u patch, which is what you want when the field's edges are clipped by the optics.
The wheel changes it live, one notch per --wheel-step.

The calibration can live in the environment instead of the command line - the variables are the defaults,
so a flag still overrides them. That is the way to stop typing the same settings on the Pi:

    export LASER_INVERT_Y=1 LASER_MOUSE_SENSITIVITY=0.15      # in the shell, or in the service file

LASER_INVERT_X / LASER_INVERT_Y / LASER_SWAP_XY are the shared three that svg.py, demo.py and this script
all read; LASER_MOUSE_INVERT_X / LASER_MOUSE_INVERT_Y / LASER_MOUSE_SWAP_XY keep working as the older
spelling of them. LASER_MOUSE_SENSITIVITY, LASER_MOUSE_SCALE and LASER_MOUSE_DEVICE (comma separated paths)
belong to this script alone.

Measured on the rp4 bench (Logitech MX Vertical on event5): x follows the mouse with no mirror, and y needs
the mirror - which is exactly the bench default in laser_field.py now, so nothing has to be typed; at the
default --sensitivity 0.5 that mouse reaches the rails inside a small wrist movement, 0.15 is the working
value (LASER_MOUSE_SENSITIVITY).

The laser line
--------------
The `laser` field of `SET` decides one digital line: above 0 is on, 0 is off. There is no brightness and no
modulation frequency to edit here, which is the point of the TTL wiring - an edge lands the moment the node
is ready for it instead of at the next PWM period, and there is no minimum on time that would turn a short
"off" into a dim spot.

What the node does with the edge is a setting of its own: it holds it back by its own ring delay so the
light arrives where the beam has actually got to (`--laser-delay` on the node, `DELAY` on the socket). That
number is printed at startup and it is the number to change on the **node**, not here, while watching where
the start and end of a drawn line land.

Traffic
-------
One SET per input packet, and only when something actually changed - a still mouse sends nothing, so the
script sits blocked in select() on the device and costs nothing between moves. --deadband swallows
the last sliver of jitter, --max-hz caps the SET rate if a mouse reports absurdly often. The socket is
opened once, like the Laser class in HOWTO.md, and kept open for the whole session.

Cleanup
-------
The node keeps whatever it was last told and has no watchdog of its own (HOWTO.md section 1), so this
script's own park is the safety path: Ctrl+C, SIGTERM, an unplugged mouse, a closed socket, an
exception - every one of them goes through "SET 0 0 0" before the socket is closed. --idle-off is the
one active safety on the beam itself: the laser goes off after that many seconds without input, and the
next movement or click brings it back.
"""

import argparse
import os
import select
import signal
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import laser_field

# Kernel input event numbers (evdev.ecodes has the same values; these are used for the plain comparisons
# and for the friendly messages, so the script can explain itself before evdev is even imported).
EV_SYN, EV_KEY, EV_REL, EV_ABS = 0x00, 0x01, 0x02, 0x03
SYN_REPORT = 0x00
REL_X, REL_Y, REL_HWHEEL, REL_WHEEL = 0x00, 0x01, 0x06, 0x08
REL_WHEEL_HI_RES, REL_HWHEEL_HI_RES = 0x0b, 0x0c   # the same wheel, in 1/120th notches
ABS_X, ABS_Y = 0x00, 0x01
BTN_LEFT, BTN_RIGHT, BTN_MIDDLE = 0x110, 0x111, 0x112
MAX_DELAY_US = 1_000_000.0

MOUSE_WORDS = ("mouse", "pointer", "trackball", "wheel mouse", "touchpad", "trackpoint")
TABLET_WORDS = ("tablet", "touch", "screen", "pen", "stylus", "wacom", "goodix", "abs")


class Stop(Exception):
    """Raised by the signal handlers so the finally block can park the mirrors."""


def env_num(name, fallback):
    """A numeric calibration default from the environment, or `fallback` when it is unset."""
    try:
        return float(os.environ.get(name, "").strip())
    except ValueError:
        return fallback


def env_paths(name):
    """A comma separated LASER_MOUSE_DEVICE into a list, or None when it is empty."""
    paths = [d.strip() for d in os.environ.get(name, "").split(",") if d.strip()]
    return paths or None


def parse_args():
    p = argparse.ArgumentParser(
        description="drive the galvos from a physical mouse on a headless Pi (evdev, no X11 needed)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--socket", default=os.environ.get("LASER_SOCKET", "/tmp/laser.sock"),
                   help="the node's Unix socket")
    p.add_argument("--device", action="append", metavar="PATH", default=env_paths("LASER_MOUSE_DEVICE"),
                   help="read this /dev/input/eventN instead of looking for one; may be given more than "
                        "once, then all of them drive the same cursor (auto-detect reads all usable ones; "
                        "LASER_MOUSE_DEVICE=/dev/input/event5 is the same, commas allowed)")
    p.add_argument("--list-devices", action="store_true", help="print the input devices and what they can do")
    p.add_argument("--sensitivity", type=float, default=env_num("LASER_MOUSE_SENSITIVITY", 0.5),
                   help="field units the virtual cursor moves per 100 mouse counts (relative mice only; "
                        "LASER_MOUSE_SENSITIVITY)")
    p.add_argument("--scale", type=float, default=env_num("LASER_MOUSE_SCALE", 1.0),
                   help="limit the output to [-scale, +scale]: 0.5 works in the middle half of the field "
                        "(LASER_MOUSE_SCALE)")
    laser_field.add_flags(p)
    p.add_argument("--always-on", action="store_true",
                   help="keep the laser on for the whole run instead of only while the switch says on")
    p.add_argument("--hold-laser", action="store_true",
                   help="old semantics: laser on only while the left button is held, instead of left click "
                        "toggling it")
    p.add_argument("--wheel-step", type=float, default=0.05, help="scale change per wheel notch")
    p.add_argument("--wheel-target", choices=("scale", "delay"), default="scale",
                   help="what the wheel changes; right click cycles the same thing live")
    p.add_argument("--delay-step", type=float, default=25.0,
                   help="microseconds of laser-delay change per wheel notch in delay mode")
    p.add_argument("--deadband", type=float, default=0.001,
                   help="ignore changes smaller than this (field units); the laser always goes through")
    p.add_argument("--max-hz", type=float, default=0.0,
                   help="cap the SET rate (0 = one per input packet; the node itself takes ~6000/s)")
    p.add_argument("--idle-off", type=float, default=0.0,
                   help="switch the laser off after this many seconds without mouse input (0 = never); "
                        "the next movement or click brings it back")
    p.add_argument("--grab", action="store_true",
                   help="grab the device so nothing else (a desktop, another script) sees the same mouse")
    p.add_argument("--keys", action="store_true", help="steer from the terminal instead of a mouse device")
    p.add_argument("--key-step", type=float, default=0.02, help="field units per key press in --keys mode")
    p.add_argument("--quiet", action="store_true", help="do not print the live cursor / laser line")
    p.add_argument("--dry-run", action="store_true", help="map and print, but never touch the node")
    return p.parse_args()


class Node:
    """The line protocol of HOWTO.md on one socket that stays open for the whole session.

    GET and DELAY always answer ("SET ..." and "DELAY <us>"), SET never does - so a read is only issued
    where one is owed, with a timeout instead of a hope: the mouse loop must not hang on a node that got
    restarted under it.
    """

    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(path)
        self.s.settimeout(2.0)
        self.f = self.s.makefile("rw")

    def _send(self, line):
        self.f.write(f"{line}\n")
        self.f.flush()

    def _reply(self):
        try:
            line = self.f.readline()
        except OSError:
            return None
        return line.strip() if line else None

    def set(self, x, y, laser):
        self._send(f"SET {x:.4f} {y:.4f} {laser:.4f}")

    def get(self):
        self._send("GET")
        return self._reply()

    def delay(self):
        """DELAY: how far the node holds a laser edge back, in microseconds. See parse_delay."""
        self._send("DELAY")
        return parse_delay(self._reply())

    def set_delay(self, us):
        """DELAY <us>: ask the running node to use a new laser-edge spacing, and read what it accepted."""
        self._send(f"DELAY {us:.1f}")
        return parse_delay(self._reply())

    def park(self):
        self.set(0.0, 0.0, 0.0)

    def close(self):
        try:
            self.f.close()
        except OSError:
            pass
        try:
            self.s.close()
        except OSError:
            pass


class Session:
    """Virtual cursor, switch, working area - and the SET they turn into."""

    def __init__(self, args, node):
        self.args = args
        self.node = node
        self.o = laser_field.orientation(args)   # the shared picture -> field mapping of laser_field.py
        self.scale = clamp(args.scale, 0.01, 1.0)
        if self.scale != args.scale:
            print(f"scale {args.scale} does not fit 0.01..1.0; using {self.scale:.2f}")
        self.cx = 0.0                      # cursor position, field units, +y is the direction a viewer
        self.cy = 0.0                      #   would call up (see the docstring)
        self.dx = self.dy = 0.0            # relative counts waiting for the end of the packet
        self.abs = None                    # absolute devices state the position instead of a delta
        self.abs_pending = False
        self.left = False                  # the physical left button (--hold-laser)
        self.on = False                    # the switch left click flips
        self.blanked = False               # set by --idle-off, cleared by the next input
        self.wheel_target = getattr(args, "wheel_target", "scale")
        self.delay_us = None               # what the node answered with DELAY, for the status line
        self.delay_target_us = None        # the delay the wheel is aiming for in delay mode
        self.sent = None                   # last (x, y, laser) that actually left
        self.last_move = time.monotonic()
        self.last_send = 0.0
        self.deferred = False                # a send --max-hz held back; the loop retries it
        self.sets = 0

    # ---------------------------------------------------------------- input side

    def move_relative(self, dx, dy):
        k = self.args.sensitivity / 100.0
        self.dx += dx * k
        self.dy -= dy * k                  # a mouse's +y is downwards, the field's +y is up
        self.touched()

    def move_absolute(self, x, y):
        self.abs = (x, y)                  # already in field convention: the device's down is -y
        self.abs_pending = True
        self.touched()

    def wheel(self, notches):
        """One notch of the wheel: either the working area, or the node's live laser delay."""
        if not notches:
            return
        if self.wheel_target == "delay":
            step = getattr(self.args, "delay_step", 25.0)
            if step > 0:
                start = self.delay_target_us if self.delay_target_us is not None else (self.delay_us or 0.0)
                target = clamp(start + notches * step, 0.0, MAX_DELAY_US)
                self.delay_target_us = target
                if self.node is not None and hasattr(self.node, "set_delay"):
                    got = self.node.set_delay(target)
                    self.delay_us = got if got is not None else target
                else:
                    self.delay_us = target
                say(self, f"delay {self.delay_us:.1f} us")
        else:
            self.scale = clamp(self.scale + notches * self.args.wheel_step, 0.01, 1.0)
        self.touched()

    def button(self, code, pressed):
        if code == BTN_LEFT:
            self.left = bool(pressed)
            if not self.args.hold_laser:
                if pressed:                            # a switch: press on, press again off
                    self.on = not self.on
                    say(self, f"laser {'on' if self.on else 'off'}")
            else:
                self.on = self.left
        elif code == BTN_RIGHT and pressed:
            self.wheel_target = "delay" if self.wheel_target == "scale" else "scale"
            if self.wheel_target == "delay" and self.delay_target_us is None:
                self.delay_target_us = self.delay_us or 0.0
            say(self, f"wheel target: {self.wheel_target}")
        elif code == BTN_MIDDLE and pressed:
            self.center()
        else:
            return
        self.touched()

    def touched(self):
        self.last_move = time.monotonic()
        if self.blanked:                   # an --idle-off shutoff is undone by the next input
            self.blanked = False

    def step(self, dx, dy):
        """Keys mode: one deliberate move of the virtual cursor."""
        self.cx = clamp(self.cx + dx, -1.0, 1.0)
        self.cy = clamp(self.cy + dy, -1.0, 1.0)
        self.touched()

    def center(self):
        self.cx = self.cy = 0.0
        self.touched()

    # ---------------------------------------------------------------- output side

    def laser(self):
        """What goes into the `laser` field of a SET: 1 when the switch says on, 0 when it says off."""
        if self.blanked:
            return 0.0
        if self.args.always_on or self.on:
            return 1.0
        return 0.0

    def project(self):
        x, y = laser_field.map_point(self.o, self.cx, self.cy)
        return x * self.scale, y * self.scale

    def commit(self, force=False):
        """Fold this packet's motion into the cursor and send it if anything changed.

        Returns the seconds this session still wants to wait before it may send again (--max-hz),
        0.0 when there is nothing pending."""
        if self.abs_pending and self.abs is not None:
            self.cx, self.cy = clamp(self.abs[0], -1.0, 1.0), clamp(self.abs[1], -1.0, 1.0)
            self.abs_pending, self.dx, self.dy = False, 0.0, 0.0
        elif self.dx or self.dy:
            self.cx = clamp(self.cx + self.dx, -1.0, 1.0)
            self.cy = clamp(self.cy + self.dy, -1.0, 1.0)
            self.dx = self.dy = 0.0
        return self.push(force)

    def pending(self):
        return bool(self.dx or self.dy or self.abs_pending)

    def push(self, force=False):
        x, y = self.project()
        laser = self.laser()
        if self.sent is not None and not force:
            px, py, pl = self.sent
            if abs(pl - laser) <= 1e-9 and max(abs(x - px), abs(y - py)) < self.args.deadband:
                return 0.0                 # nothing worth a SET; a still mouse sends nothing
        if self.node is None:                # --dry-run: the mapping is the point, not the node
            self.sent = (x, y, laser)
            self.last_send = time.monotonic()
            self.sets += 1
            self.deferred = False
            return 0.0
        if self.args.max_hz > 0:
            gap = time.monotonic() - self.last_send
            if gap < 1.0 / self.args.max_hz:
                self.deferred = True
                return 1.0 / self.args.max_hz - gap
        self.node.set(x, y, laser)
        self.sent = (x, y, laser)
        self.last_send = time.monotonic()
        self.sets += 1
        self.deferred = False
        return 0.0

    def idle_off(self):
        """--idle-off: flip the switch off (or blank an --always-on run); input brings it back."""
        if self.blanked or self.laser() == 0.0:
            return 0.0
        if self.args.always_on:
            self.blanked = True
        else:
            self.on = False
            say(self, "laser off (idle)")
        return self.push(force=True)

    def idle_left(self):
        if self.args.idle_off <= 0:
            return None
        return max(0.0, self.args.idle_off - (time.monotonic() - self.last_move))

    def send_left(self):
        """How long --max-hz still has to hold before the deferred SET may go out."""
        if not self.deferred or self.args.max_hz <= 0:
            return None
        return max(0.0, 1.0 / self.args.max_hz - (time.monotonic() - self.last_send))

    def park(self):
        self.cx = self.cy = self.dx = self.dy = 0.0
        self.abs, self.abs_pending = None, False
        self.left, self.on, self.blanked = False, False, False
        if self.node is not None:
            self.node.park()
            self.sent = (0.0, 0.0, 0.0)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def parse_delay(reply):
    """The node's "DELAY 333.3" -> 333.3 microseconds. Anything else is not a delay."""
    if not reply:
        return None
    parts = reply.split()
    if len(parts) != 2 or parts[0] != "DELAY":
        return None
    try:
        return float(parts[1])
    except ValueError:
        return None


def say(session, text):
    """A change worth its own line: the live cursor line is cleared first so nothing is left over."""
    if session.args.quiet:
        return
    if sys.stdout.isatty():
        sys.stdout.write("\r" + " " * 96 + "\r")
    print(f"  {text}")
    sys.stdout.flush()


# ------------------------------------------------------------------ the input devices


def load_evdev():
    try:
        import evdev
    except ImportError:
        print("no evdev, so /dev/input/event* cannot be read from Python. On Raspberry Pi OS:\n"
              "    sudo apt install python3-evdev         # or:  python3 -m pip install evdev\n"
              "Until that is done, steer with the terminal instead:  ... mouse_laser.py --keys")
        return None
    return evdev


def abs_bounds(info):
    """AbsInfo spelling differs between evdev versions; take whichever one this install has."""
    lo = getattr(info, "min", None)
    if lo is None:
        lo = getattr(info, "minimum", 0)
    hi = getattr(info, "max", None)
    if hi is None:
        hi = getattr(info, "maximum", 0)
    return lo, hi


def device_kind(evdev, dev):
    """(kind, score, note): kind is 'absolute' / 'relative' / None, score ranks the candidates."""
    caps = dev.capabilities()
    rel = set(caps.get(EV_REL, ()))
    keys = set(caps.get(EV_KEY, ()))
    absinfo = caps.get(EV_ABS, ())
    abs_codes = {}
    for entry in absinfo:
        code = entry[0] if isinstance(entry, tuple) else entry
        info = entry[1] if isinstance(entry, tuple) and len(entry) > 1 else None
        abs_codes[code] = info
    name = (dev.name or "").lower()
    if ABS_X in abs_codes and ABS_Y in abs_codes:
        kind = "absolute"
    elif REL_X in rel and REL_Y in rel:
        kind = "relative"
    else:
        return None, 0, ""
    score = 0
    if BTN_LEFT in keys:
        score += 4
    if any(w in name for w in MOUSE_WORDS):
        score += 3
    if any(w in name for w in TABLET_WORDS):
        score += 1
    score += 1 if kind == "relative" else 0
    note = f"{kind}{' +BTN_LEFT' if BTN_LEFT in keys else ''}"
    if kind == "absolute":
        lo_x, hi_x = abs_bounds(abs_codes[ABS_X] or ())
        lo_y, hi_y = abs_bounds(abs_codes[ABS_Y] or ())
        note += f" ABS_X {lo_x}..{hi_x} ABS_Y {lo_y}..{hi_y}"
    return kind, score, note


def abs_infos(dev):
    """{code: AbsInfo} for this device's EV_ABS axes, read once rather than per event."""
    out = {}
    for entry in dev.capabilities().get(EV_ABS, ()):
        if isinstance(entry, tuple):
            values = list(entry)
            if values:
                out[values[0]] = values[1] if len(values) > 1 else None
        else:
            out[entry] = None
    return out


def drain(dev):
    """The events a device has queued, as a list.

    evdev's read() is a generator (1.9 on the Pi, 2.0 elsewhere): it raises BlockingIOError when nothing
    is queued - before it yields anything on the versions I have met, and once the queue is drained on
    any other, so whatever it did yield is kept here. A version or a stand-in that hands back one event
    at a time is taken as well.
    """
    first = dev.read()
    if hasattr(first, "type"):
        return [first]
    out = []
    try:
        for ev in first:
            out.append(ev)
    except BlockingIOError:
        pass
    return out


def open_device(evdev, path):
    """Open one event device and say what it is: (dev, kind, score, note, path), or (None, ...) with the
    reason it cannot be used (permission, not a device, no X/Y motion)."""
    try:
        dev = evdev.InputDevice(path)
    except OSError as e:
        return None, None, 0, e, path
    kind, score, note = device_kind(evdev, dev)
    if kind is None:
        return None, None, 0, OSError(f"{path}: no REL_X/REL_Y or ABS_X/ABS_Y to drive the galvos"), path
    return dev, kind, score, note, path


def pick_devices(evdev, paths, limit=None):
    """The devices to read, best match first. Returns (picked, problems).

    With paths=None every usable /dev/input/event* is kept and all of them drive the same virtual cursor
    - a Logitech combo receiver registers the keyboard interface and the mouse interface as two devices
    with identical capabilities, and only one of them ever sees the motion, so reading both is what makes
    auto-detect work. --device PATH is how you narrow it to one.
    With paths given, every one of them is used as named."""
    scan = paths is None
    if scan:
        try:
            entries = sorted(os.listdir("/dev/input"))
        except OSError:
            entries = []
        paths = [f"/dev/input/{e}" for e in entries if e.startswith("event")]
    found, problems = [], []
    for path in paths:
        dev, kind, score, note, path = open_device(evdev, path)
        if dev is None:
            problems.append((path, note))          # scan: tripped over something unusable; --device: named
            continue
        found.append((score, kind, note, dev, path))
    found.sort(key=lambda d: (-d[0], d[4]))
    if scan and limit:
        found = found[:limit]
    return [(d[3], d[1], d[2], d[4]) for d in found], problems


def list_devices(evdev):
    """Everything under /dev/input/event*, usable or not - the diagnostic view."""
    try:
        entries = sorted(os.listdir("/dev/input"))
    except OSError:
        print("no /dev/input to look at on this system")
        return 1
    rows, denied = [], []
    for e in entries:
        if not e.startswith("event"):
            continue
        path = f"/dev/input/{e}"
        dev, _kind, _score, note, _ = open_device(evdev, path)
        if dev is None:
            if isinstance(note, PermissionError):
                denied.append(path)
            else:
                rows.append((path, "-", str(note)))
            continue
        rows.append((path, dev.name or "", note))
    for path, name, note in rows:
        print(f"  {path:22} {name:30} {note}")
    permission_help([(p, PermissionError()) for p in denied])
    usable = [r for r in rows if "relative" in r[2] or "absolute" in r[2]]
    print(f"{len(usable)} of {len(rows)} event devices can drive the galvos"
          f"{' - all of them are read, all drive the same cursor; --device PATH narrows it down'
            if len(usable) > 1 else ''}")
    return 0 if usable else 1


def permission_help(problems):
    denied = [p for p, e in problems if isinstance(e, PermissionError)]
    if not denied:
        return
    print(f"no permission for {', '.join(denied)} - input devices belong to the group \"input\":")
    print("    sudo usermod -aG input \"$USER\"     # then log out and back in, or reboot")
    print("    sudo python3 scripts/mouse_laser.py  # ...or this once, before the group takes effect")


def show(session, when):
    """One status line, redrawn at most ~12/s, only when something is on a terminal."""
    if session.args.quiet or not sys.stdout.isatty():
        return when
    now = time.monotonic()
    if now - when < 0.08:
        return when
    x, y = session.project()
    delay = "" if session.delay_us is None else f"laser held {session.delay_us:.0f} us  "
    target = f"wheel {session.wheel_target}  "
    sys.stdout.write(f"\r cursor {session.cx:+.3f} {session.cy:+.3f}  ->  x {x:+.4f} y {y:+.4f}  "
                     f"scale {session.scale:.2f}  {target}{delay}"
                     f"{'LASER on' if session.laser() else 'laser off'}  {session.sets} sets  ")
    sys.stdout.flush()
    return now


def run_mouse(evdev, picked, session):
    """Blocking read on the device(s); one SET per input packet, nothing at all when the mouse is still."""
    grabbed, devices = [], []
    for dev, kind, note, path in picked:
        if session.args.grab:
            try:
                dev.grab()
                grabbed.append(dev)
            except OSError as e:
                print(f"  cannot grab {path}: {e} (something else has it; carrying on anyway)")
        devices.append({"dev": dev, "kind": kind, "absinfo": abs_infos(dev), "raw": [0.0, 0.0],
                        "wheel_hi_res": REL_WHEEL_HI_RES in dev.capabilities().get(EV_REL, ())})
    by_fd = {d["dev"].fileno(): d for d in devices}
    status_at = 0.0

    try:
        while True:
            timeout = session.idle_left()
            wait = session.send_left()
            if wait is not None:
                timeout = wait if timeout is None else min(timeout, wait)
            try:
                ready = select.select([d["dev"] for d in devices], [], [], timeout)[0]
            except InterruptedError:
                continue
            except OSError as e:                  # an fd we were polling is gone (device unplugged)
                raise Stop(f"the input device is gone: {e}")
            if not ready:
                session.idle_off()                # --idle-off, and a --max-hz held-back SET
                if session.pending() or session.deferred:
                    session.commit(force=True)
                continue
            for dev in ready:
                d = by_fd[dev.fileno()]
                while True:
                    try:
                        events = drain(dev)
                    except BlockingIOError:
                        break                     # nothing queued any more; the fd is non-blocking
                    except OSError as e:
                        raise Stop(f"{dev.name}: {e}")
                    if not events:
                        break
                    for ev in events:
                        if ev.type == EV_SYN and ev.code == SYN_REPORT:
                            session.commit()      # one SET for the whole packet
                        elif ev.type == EV_KEY:
                            session.button(ev.code, ev.value != 0)
                        elif ev.type == EV_REL:
                            if ev.code == REL_X:
                                session.move_relative(ev.value, 0)
                            elif ev.code == REL_Y:
                                session.move_relative(0, ev.value)
                            elif ev.code in (REL_WHEEL, REL_HWHEEL):
                                # a wheel that also reports REL_*_HI_RES sends both: count it once
                                if not d["wheel_hi_res"]:
                                    session.wheel(ev.value)
                            elif ev.code in (REL_WHEEL_HI_RES, REL_HWHEEL_HI_RES):
                                session.wheel(ev.value / 120.0)   # hi-res wheels: 120 counts per notch
                        elif ev.type == EV_ABS and d["kind"] == "absolute":
                            lo, hi = abs_bounds(d["absinfo"].get(ev.code) or ())
                            if hi <= lo:
                                continue
                            raw = 2.0 * (clamp(ev.value, lo, hi) - lo) / (hi - lo) - 1.0
                            if ev.code == ABS_X:
                                d["raw"][0] = raw
                            elif ev.code == ABS_Y:
                                d["raw"][1] = raw
                            else:
                                continue
                            # the device's own +y points the way a screen's does: downwards
                            session.move_absolute(d["raw"][0], -d["raw"][1])
                status_at = show(session, status_at)
    finally:
        for dev in grabbed:
            try:
                dev.ungrab()
            except OSError:
                pass


def run_keys(session):
    """Fallback for a Pi with no mouse and no evdev: the same cursor, driven from the terminal."""
    import termios
    import tty

    steps = {"w": (0, 1), "up": (0, 1), "s": (0, -1), "down": (0, -1),
             "a": (-1, 0), "left": (-1, 0), "d": (1, 0), "right": (1, 0),
             "h": (-1, 0), "j": (0, -1), "k": (0, 1), "l": (1, 0)}
    print("arrows / wasd / hjkl move, space toggles the laser, + / - are the wheel, t switches the wheel")
    print("target, c centres, q quits")
    fd = sys.stdin.fileno()
    saved = termios.tcgetattr(fd)
    status_at = 0.0
    try:
        tty.setraw(fd)
        buf = b""
        while True:
            wait = session.idle_left()                       # --idle-off works here too
            if wait is not None and not select.select([fd], [], [], wait)[0]:
                session.idle_off()
                continue
            data = os.read(fd, 64)
            if not data:
                break
            buf += data
            while buf:
                if buf.startswith(b"\x1b["):
                    if len(buf) < 3:
                        break                             # arrow half-received; wait for the rest
                    name = {b"A": "up", b"B": "down", b"C": "right", b"D": "left"}.get(buf[2:3])
                    if name is None:
                        buf = buf[1:]
                        continue
                    key, used = name, 3
                else:
                    key, used = buf[0:1].decode(errors="replace").lower(), 1
                buf = buf[used:]
                if key in ("q", "\x03", "\x04"):
                    return
                elif key == " ":
                    session.button(BTN_LEFT, True)          # the switch, with no button to press
                    session.commit(force=True)
                elif key == "c":
                    session.center()
                    session.commit(force=True)
                elif key == "t":
                    session.button(BTN_RIGHT, True)
                elif key in ("+", "="):
                    session.wheel(1)
                    session.commit(force=True)
                elif key in ("-", "_"):
                    session.wheel(-1)
                    session.commit(force=True)
                elif key in steps:
                    dx, dy = steps[key]
                    session.step(dx * session.args.key_step, dy * session.args.key_step)
                    session.commit(force=True)
                status_at = show(session, status_at)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, saved)
        sys.stdout.write("\n")


def sync_from_node(session):
    """Ask the node what it is already doing, so the switch continues from that instead of from a guess.

    GET gives the position and the laser it is holding, DELAY gives how far the node holds a laser edge
    back - the number that decides where a drawn line actually starts and ends. A node too old to know
    DELAY answers nothing to that one, which is read as "no compensation on the node".
    """
    if session.node is None:
        return "-"
    got = session.node.get()
    parts = (got or "").split()
    if len(parts) == 4 and parts[0] == "SET":
        try:
            laser = float(parts[3])
        except ValueError:
            laser = 0.0
        if laser > 0:
            session.on = True                    # the node is lit; the switch starts where the beam is
    session.delay_us = session.node.delay()
    if session.wheel_target == "delay":
        session.delay_target_us = session.delay_us if session.delay_us is not None else 0.0
    return got or "-"


# ------------------------------------------------------------------ main


def main():
    args = parse_args()
    if args.sensitivity <= 0:
        print("--sensitivity has to be above 0")
        return 2
    if args.max_hz < 0 or args.deadband < 0 or args.wheel_step <= 0 or args.delay_step <= 0:
        print("--max-hz and --deadband have to be 0 or more, --wheel-step and --delay-step above 0")
        return 2

    def stop(signum, frame):
        raise Stop(signal.Signals(signum).name)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    if args.list_devices:
        evdev = load_evdev()
        return 1 if evdev is None else list_devices(evdev)

    if args.keys and not sys.stdin.isatty():
        print("--keys needs a terminal to read keys from (stdin is not one)")
        return 2

    evdev = None
    picked = []
    if not args.keys:
        evdev = load_evdev()
        if evdev is None:
            return 1
        picked, problems = pick_devices(evdev, args.device)
        if args.device is not None and problems:
            for path, e in problems:                 # a device that was named and cannot be used
                print(f"cannot use {path}: {e}")
            permission_help(problems)
            return 1
        if not picked:
            permission_help(problems)
            if not problems:
                print("no mouse under /dev/input/event* (REL_X/REL_Y + BTN_LEFT, or ABS_X/ABS_Y).")
                print("check the mouse with  cat /proc/bus/input/devices   and name it with --device PATH,")
                print("or drive this from the terminal with --keys.")
            return 1

    node = None
    if not args.dry_run:
        try:
            node = Node(args.socket)
        except OSError as e:
            print(f"cannot connect to {args.socket}: {e}")
            print("start the node first:  systemctl --user start laser-node   (or ./scripts/deploy.sh run)")
            return 1

    session = Session(args, node)
    node_says = sync_from_node(session)
    print(f"socket {args.socket}{' (dry run: nothing sent)' if args.dry_run else ''}  node says: {node_says}")
    print(f"field -1..+1  scale {session.scale:.2f}  {laser_field.describe(session.o)}  "
          f"{'laser on for the whole run' if args.always_on else ('left click held = laser' if args.hold_laser else 'left click = laser switch')}")
    held = "-" if session.delay_us is None else f"{session.delay_us:.0f} us"
    if args.wheel_target == "delay":
        print(f"wheel target: delay  [{args.delay_step:.1f} us per notch, right click switches to scale]   "
              f"the node holds a laser edge by {held}")
    else:
        print(f"wheel target: scale  [{args.wheel_step:.2f} of the field per notch, right click switches to delay]   "
              f"the node holds a laser edge by {held}")
    if args.keys:
        print("input: the keyboard (arrows / wasd / hjkl)")
    else:
        print("input: " + "  ".join(f'{path} "{dev.name}" [{note}]' for dev, _kind, note, path in picked))
    if args.grab and not args.keys:
        print("      grabbed: nothing else sees this device while the script runs")
    if args.idle_off > 0:
        print(f"idle safety: the laser goes off {args.idle_off:.1f}s after the last input")
    print("Ctrl+C parks the mirrors at 0,0 with the laser off\n")

    try:
        if args.keys:
            run_keys(session)
        else:
            run_mouse(evdev, picked, session)
    except Stop as e:
        print(f"\nstopped ({e})")
    except KeyboardInterrupt:
        print("\nstopped")
    except OSError as e:
        print(f"\ninput error: {e}")
        return 1
    finally:
        try:
            if node is not None:
                session.park()
        except OSError as e:
            print(f"could not park over {args.socket}: {e}")
            print("the mirrors are holding their last position - end it with:  "
                  "PI=user@pi ./scripts/deploy.sh send 0 0 0")
        if node is not None:
            node.close()
        sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
