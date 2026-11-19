#!/usr/bin/env python3
"""Calibrate the laser-edge delay by drawing horizontal calibration lines.

    ssh -t david@rp4 'cd laser_node && python3 scripts/calibrate-delay.py --scale 0.7'

The script paints horizontal lines from left to right at several field speeds. The laser is off while the
mirrors move to the next line. Scroll the mouse wheel to change the running node's laser delay live; the
new value is printed, together with what a delay error means in field units at the current line speed.

At 300 field units/s, a 100 µs delay error moves the burn start/end by:

    300 * 100 / 1_000_000 = 0.030 field units

Look for:

* a dark gap at the left end of a line: the delay is too large;
* burn before the intended left end, or the line ending early: the delay is too small;
* high-speed lines show the error more visibly than slow lines.
"""

import argparse
import math
import os
import select
import signal
import socket
import sys
import threading
import time

REL_WHEEL = 0x08
REL_HWHEEL = 0x06
REL_WHEEL_HI_RES = 0x0B
REL_HWHEEL_HI_RES = 0x0C
EV_REL = 0x02

MAX_DELAY_US = 1_000_000.0
DEFAULT_SPEEDS = "30,60,100,150,200,300"


class Stop(Exception):
    pass


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


def parse_speeds(raw):
    vals = []
    for word in raw.replace(",", " ").split():
        try:
            v = float(word)
        except ValueError:
            return []
        if v > 0:
            vals.append(v)
    return vals


def load_evdev():
    try:
        import evdev
    except ImportError:
        return None
    return evdev


def load_devices(device_paths):
    out = []
    if device_paths:
        out.extend(device_paths)
    else:
        try:
            names = os.listdir("/dev/input")
        except OSError:
            return out
        out.extend(f"/dev/input/{n}" for n in names if n.startswith("event"))
    return out


def open_wheel_devices(evdev, device_paths):
    picked = []
    for path in load_devices(device_paths):
        if not path.startswith("/dev/input/event"):
            continue
        try:
            dev = evdev.InputDevice(path)
        except OSError as e:
            if device_paths:
                print(f"cannot use {path}: {e}")
            continue
        rel = set(dev.capabilities().get(EV_REL, ()))
        hi_res = REL_WHEEL_HI_RES in rel or REL_HWHEEL_HI_RES in rel
        if rel & {REL_WHEEL, REL_HWHEEL, REL_WHEEL_HI_RES, REL_HWHEEL_HI_RES}:
            picked.append({"dev": dev, "path": path, "name": dev.name or "input", "hi_res": hi_res})
    return picked


def drain(dev):
    """The events a device has queued, handling both evdev read() shapes."""
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


class DelayControl:
    """One socket used only for querying and changing the node's laser-edge delay."""

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

    def query(self):
        self._send("DELAY")
        return parse_delay(self._reply())

    def set(self, us):
        self._send(f"DELAY {float(us):.1f}")
        return parse_delay(self._reply())

    def close(self):
        try:
            self.f.close()
        except OSError:
            pass
        try:
            self.s.close()
        except OSError:
            pass


class Drawer:
    """One socket used only for SET lines; it does not read replies."""

    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(path)
        self.s.settimeout(2.0)

    def set(self, x, y, laser):
        self.s.sendall(f"SET {x:.6f} {y:.6f} {laser:.6f}\n".encode())

    def park(self):
        try:
            self.set(0.0, 0.0, 0.0)
        except OSError:
            pass

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


class State:
    """Shared delay/speed values, because the wheel thread and the drawing loop talk to the user."""

    def __init__(self, delay_us, delay_step):
        self.lock = threading.Lock()
        self.delay_us = delay_us
        self.delay_step = delay_step
        self.speed = None
        self.y = None

    def current_delay(self):
        with self.lock:
            return self.delay_us

    def current_speed(self):
        with self.lock:
            return self.speed

    def set_context(self, speed, y):
        with self.lock:
            self.speed = speed
            self.y = y

    def add_notches(self, notches):
        if not notches:
            return self.current_delay()
        with self.lock:
            self.delay_us = clamp(self.delay_us + notches * self.delay_step, 0.0, MAX_DELAY_US)
            return self.delay_us

    def set_delay(self, us):
        with self.lock:
            self.delay_us = clamp(float(us), 0.0, MAX_DELAY_US)
            return self.delay_us


def fmt_speed_speed(delay_us, speed):
    if speed is None:
        return f"delay {delay_us:.1f} us"
    field_per_100us = speed * 100.0 / 1_000_000.0
    return (f"delay {delay_us:.1f} us  speed {speed:.0f} u/s  "
            f"100 us delay error = {field_per_100us:.3f} field u")


def safe_print(print_lock, text):
    with print_lock:
        print(text, flush=True)


def wheel_loop(devices, state, delay_ctl, print_lock):
    print_lock_local = print_lock
    while True:
        try:
            ready = select.select([d["dev"] for d in devices], [], [], 0.25)[0]
        except OSError:
            return

        for dev in ready:
            d = next(x for x in devices if x["dev"] is dev)
            while True:
                try:
                    events = drain(dev)
                except BlockingIOError:
                    break
                except OSError:
                    return
                if not events:
                    break
                for ev in events:
                    if ev.type != EV_REL:
                        continue

                    if ev.code in (REL_WHEEL, REL_HWHEEL):
                        if d["hi_res"]:
                            continue
                        notches = ev.value
                    elif ev.code in (REL_WHEEL_HI_RES, REL_HWHEEL_HI_RES):
                        notches = ev.value / 120.0
                    else:
                        continue

                    target = state.add_notches(notches)
                    got = delay_ctl.set(target)
                    if got is None:
                        state.set_delay(target)
                        safe_print(print_lock_local, f"node did not answer DELAY {target:.1f}; showing {target:.1f} us")
                    else:
                        state.set_delay(got)
                        safe_print(print_lock_local, fmt_speed_speed(state.current_delay(), state.current_speed()))


def draw_line(drawer, x0, x1, y, speed, updates, passes, settle, gap, extra_settle):
    dt = 1.0 / updates
    step = speed * dt
    length = x1 - x0
    n = max(1, int(math.ceil(length / step)))

    for _ in range(passes):
        drawer.set(x0, y, 0.0)
        time.sleep(settle + extra_settle)

        t = time.monotonic()
        drawer.set(x0, y, 1.0)

        for k in range(1, n + 1):
            t += dt
            x = min(x1, x0 + speed * k * dt)
            drawer.set(x, y, 1.0)
            while time.monotonic() < t:
                pass

        drawer.set(x1, y, 0.0)
        time.sleep(gap)


def evenly_spaced_values(n, limit):
    if n <= 1:
        return [0.0]
    return [-limit + 2.0 * limit * i / (n - 1) for i in range(n)]


def parse_args():
    p = argparse.ArgumentParser(
        description="draw horizontal laser lines at different speeds and change the laser-edge delay with the mouse wheel",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--socket", default="/tmp/laser.sock", help="the node's Unix socket")
    p.add_argument("--scale", type=float, default=0.7,
                   help="line extent: draw x from -scale to +scale, and distribute lines over y in [-scale, +scale]")
    p.add_argument("--speeds", default=DEFAULT_SPEEDS,
                   help="comma-separated line speeds in field units/s")
    p.add_argument("--updates", type=float, default=6000.0,
                   help="the node's setpoint rate; 384000 Hz / period 64 gives 6000")
    p.add_argument("--passes", type=int, default=3, help="left-to-right passes per calibration line")
    p.add_argument("--cycles", type=int, default=2,
                   help="how many full sets of lines to draw (0 keeps drawing until Ctrl+C)")
    p.add_argument("--line-pause", type=float, default=0.30,
                   help="pause after each line so the delay can be changed and the line inspected")
    p.add_argument("--settle", type=float, default=0.12, help="settle time before each laser-on pass")
    p.add_argument("--gap", type=float, default=0.03, help="gap after each laser-off pass")
    p.add_argument("--delay-step", type=float, default=25.0, help="µs of delay change per wheel notch")
    p.add_argument("--start-delay", type=float, default=None,
                   help="set this delay first; by default the script reads the node's current delay")
    p.add_argument("--device", action="append", metavar="PATH", default=None,
                   help="use only these wheel devices instead of auto-detecting /dev/input/event*")
    return p.parse_args()


def main():
    args = parse_args()

    speeds = parse_speeds(args.speeds)
    if not speeds:
        print("no usable speeds; examples: --speeds 30,60,100,150,200,300")
        return 2
    if args.scale <= 0 or args.scale > 1:
        print("--scale has to be in (0, 1]")
        return 2
    if args.updates <= 0 or args.delay_step <= 0:
        print("--updates and --delay-step have to be above 0")
        return 2
    if args.passes < 1 or args.cycles < 0:
        print("--passes has to be at least 1, --cycles 0 or more")
        return 2

    def stop(signum, _frame):
        raise Stop(signal.Signals(signum).name)

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)

    drawer = None
    delay_ctl = None
    state = State(0.0, args.delay_step)

    try:
        delay_ctl = DelayControl(args.socket)
        drawer = Drawer(args.socket)
    except OSError as e:
        print(f"cannot connect to {args.socket}: {e}")
        print("start the node first:  systemctl --user start laser-node   (or ./scripts/deploy.sh run)")
        return 1

    try:
        evdev = load_evdev()
        if evdev is None:
            print("no evdev, so the mouse wheel cannot be read. On Raspberry Pi OS:\n"
                  "    sudo apt install python3-evdev")
            return 1

        devices = open_wheel_devices(evdev, args.device)
        if not devices:
            print("no /dev/input/event* wheel device found.")
            print("check the mouse with  cat /proc/bus/input/devices  or name it with --device /dev/input/eventN")
            return 1

        current = delay_ctl.query()
        if current is None:
            current = 0.0
            print("node did not answer DELAY; starting from 0 us")
        if args.start_delay is not None:
            got = delay_ctl.set(args.start_delay)
            if got is None:
                print(f"node did not set DELAY {args.start_delay:.1f}; using its answer-less value")
            else:
                current = got

        state = State(current, args.delay_step)
        print_lock = threading.Lock()

        x0 = -args.scale
        x1 = args.scale
        ys = evenly_spaced_values(len(speeds), args.scale)

        print(f"socket {args.socket}  scale {args.scale:.2f}  speeds {', '.join(f'{s:.0f}' for s in speeds)} u/s")
        print(f"lines: {len(speeds)}  passes/line: {args.passes}  cycles: {'infinite until Ctrl+C' if args.cycles == 0 else args.cycles}")
        print("wheel up/down: change delay  " +
              fmt_speed_speed(state.current_delay(), speeds[-1]))
        print("Ctrl+C parks the mirrors and stops the test\n")

        wheel_thread = threading.Thread(target=wheel_loop, args=(devices, state, delay_ctl, print_lock), daemon=True)
        wheel_thread.start()

        cycle = 0
        while True:
            if args.cycles and cycle >= args.cycles:
                break
            cycle += 1

            for i, (speed, y) in enumerate(zip(speeds, ys), start=1):
                delay_us = state.current_delay()
                state.set_context(speed, y)
                extra_settle = max(0.0, delay_us / 1_000_000.0)
                safe_print(print_lock, f"cycle {cycle}  line {i}/{len(speeds)}  y {y:+.2f}  "
                                       f"{fmt_speed_speed(delay_us, speed)}  x {x0:+.2f} -> {x1:+.2f}")
                draw_line(drawer, x0, x1, y, speed, args.updates, args.passes, args.settle, args.gap, extra_settle)
                time.sleep(args.line_pause)

        state.set_context(None, None)
        safe_print(print_lock, f"done: node delay now {fmt_speed_speed(state.current_delay(), None)}")
        return 0

    except Stop as e:
        state.set_context(None, None)
        print(f"stopped ({e}); node delay now {fmt_speed_speed(state.current_delay(), None)}")
        return 130
    except KeyboardInterrupt:
        state.set_context(None, None)
        print(f"stopped; node delay now {fmt_speed_speed(state.current_delay(), None)}")
        return 130
    finally:
        if drawer is not None:
            drawer.park()
            drawer.close()
        if delay_ctl is not None:
            delay_ctl.close()


if __name__ == "__main__":
    sys.exit(main())
