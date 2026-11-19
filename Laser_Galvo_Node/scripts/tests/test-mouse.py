#!/usr/bin/env python3
"""Checks for scripts/mouse_laser.py: synthetic input events in, the socket lines it sends out.

No mouse, no node, no hardware - a fake /dev/input device with the two evdev read() shapes, a fake node
that records what arrived, and a fake clock. `python3 scripts/tests/test-mouse.py` (and
scripts/tests/test-orient.py for the mapping these numbers go through).
"""
import importlib.util
import os
import sys
import threading
import time

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
spec = importlib.util.spec_from_file_location("ml", os.path.join(HERE, "mouse_laser.py"))
if spec is None or spec.loader is None:
    raise RuntimeError("cannot import scripts/mouse_laser.py")
ml = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ml)


class Ev:
    __slots__ = ("type", "code", "value", "seconds", "nanoseconds")

    def __init__(self, t, c, v):
        self.type, self.code, self.value = t, c, v
        self.seconds = self.nanoseconds = 0


class FakeDev:
    """Enough of evdev.InputDevice for the loop: fileno(), read(), capabilities(), name."""

    def __init__(self, name, caps, gen_mode=True):
        self.name, self.caps, self.gen_mode = name, caps, gen_mode
        self.queue = []
        self.r, self.w = os.pipe()
        os.set_blocking(self.r, False)
        self.fd = self.r

    def feed(self, *events):
        for e in events:
            self.queue.append(e)
        os.write(self.w, b"\1" * len(events))

    def fileno(self):
        return self.r

    def capabilities(self, verbose=False):
        return self.caps

    def _drain_markers(self):
        while True:                 # drain the wake-up bytes; the last read raises BlockingIOError
            os.read(self.r, 1)

    def read(self):
        if not self.queue:
            if not self.gen_mode:
                self._drain_markers()      # raises BlockingIOError, like evdev on a drained fd

            def empty():
                yield from ()
                self._drain_markers()

            return empty()
        if not self.gen_mode:              # an evdev that hands back one event per call
            return self.queue.pop(0)

        def gen():                         # evdev 1.9 / 2.0: read() is a generator
            while self.queue:
                yield self.queue.pop(0)
            self._drain_markers()

        return gen()

    def grab(self):
        pass

    def ungrab(self):
        pass

    def close(self):
        os.close(self.r)
        os.close(self.w)


class Info:
    def __init__(self, lo, hi):
        self.min, self.max = lo, hi
        self.fuzz, self.flat, self.resolution = 0, 0, 0


class FakeNode:
    """Records every line the script sends; answers GET and DELAY the way the node does."""

    def __init__(self, get_reply="SET 0 0 0", delay_reply="DELAY 333.3"):
        self.lines = []
        self.get_reply = get_reply
        self.delay_reply = delay_reply

    def set(self, x, y, laser):
        self.lines.append(f"SET {x:.4f} {y:.4f} {laser:.4f}")

    def get(self):
        return self.get_reply

    def delay(self):
        return ml.parse_delay(self.delay_reply)

    def set_delay(self, us):
        self.lines.append(f"DELAY {us:.1f}")
        self.delay_reply = f"DELAY {us:.1f}"
        return float(us)

    def park(self):
        self.set(0, 0, 0)

    def close(self):
        pass


def args(**kw):
    base = dict(socket="x", device=None, list_devices=False, sensitivity=0.5, scale=1.0, invert_x=False,
                invert_y=False, swap_xy=False, always_on=False, hold_laser=False,
                wheel_step=0.05, wheel_target="scale", delay_step=25.0,
                deadband=0.001, max_hz=0.0, idle_off=0.0, grab=False, keys=False,
                key_step=0.02, quiet=True, dry_run=False)
    base.update(kw)
    return type("A", (), base)()


REL_CAPS = {ml.EV_REL: {ml.REL_X, ml.REL_Y, ml.REL_WHEEL},
            ml.EV_KEY: {ml.BTN_LEFT, ml.BTN_RIGHT, ml.BTN_MIDDLE}}
ABS_CAPS = {ml.EV_ABS: [(ml.ABS_X, Info(0, 4095)), (ml.ABS_Y, Info(0, 4095))], ml.EV_KEY: {ml.BTN_LEFT}}

fails = []
ran = 0


def check(label, node, expect):
    global ran
    ran += 1
    got = node.lines if hasattr(node, "lines") else node
    ok = got == expect
    print(f"{'ok  ' if ok else 'FAIL'} {label}\n     got    {got}\n     expect {expect}")
    if not ok:
        fails.append(label)


def state(label, ok, detail):
    """A check that is about the session's state rather than the lines it sent."""
    global ran
    ran += 1
    print(f"{'ok  ' if ok else 'FAIL'} {label}: {detail}")
    if not ok:
        fails.append(label)


def run(dev, kind, a, events, seconds=0.6, node=None):
    node = node or FakeNode()
    session = ml.Session(a, node)
    ml.sync_from_node(session)          # main() does this before the loop: start from the node's values
    picked = [(dev, kind, "fake", "/dev/input/fake0")]
    t = threading.Thread(target=ml.run_mouse, args=(None, picked, session), daemon=True)
    t.start()
    for batch in events:
        time.sleep(0.05)
        dev.feed(*batch)
    time.sleep(seconds)
    return node, session, t


def press(code, value):
    return [Ev(ml.EV_KEY, code, value), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)]


# 1. relative mouse: 100 counts at --sensitivity 0.5 is half the field, one SET per packet, and the
#    release of the left button sends nothing (a switch has nothing to do when the button comes up)
dev = FakeDev("Logitech USB Receiver Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(), [
    [Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_REL, ml.REL_Y, -100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    press(ml.BTN_LEFT, 1),
    press(ml.BTN_LEFT, 0),
    [Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],                       # a still mouse sends nothing
])
check("relative move + left click on, release does nothing", node,
      ["SET 0.5000 0.5000 0.0000", "SET 0.5000 0.5000 1.0000"])

# 2. rails: 1000 counts cannot leave the field
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(sensitivity=0.5), [
    [Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_REL, ml.REL_Y, -100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    [Ev(ml.EV_REL, ml.REL_X, 1000), Ev(ml.EV_REL, ml.REL_Y, -1000), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
])
check("1000 counts land on the rail, a second kick sends nothing new", node,
      ["SET 0.5000 0.5000 0.0000", "SET 1.0000 1.0000 0.0000"])

# 3. calibration: invert then swap then scale
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(invert_x=True, swap_xy=True, scale=0.4), [
    [Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_REL, ml.REL_Y, -100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
])
check("--invert-x --swap-xy --scale 0.4", node, ["SET 0.2000 -0.2000 0.0000"])

# 4. left click is a switch: on, off, on - and a press with the cursor parked still changes the beam
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(), [
    press(ml.BTN_LEFT, 1),
    press(ml.BTN_LEFT, 1),
    press(ml.BTN_LEFT, 1),
])
check("three left clicks: on, off, on", node,
      ["SET 0.0000 0.0000 1.0000", "SET 0.0000 0.0000 0.0000", "SET 0.0000 0.0000 1.0000"])

# 5. --hold-laser is the old semantics: held = on, released = off
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(hold_laser=True), [
    press(ml.BTN_LEFT, 1),
    press(ml.BTN_LEFT, 0),
])
check("--hold-laser keeps the held/released behaviour", node,
      ["SET 0.0000 0.0000 1.0000", "SET 0.0000 0.0000 0.0000"])

# 6. the wheel is the working area: two notches of 0.1 grow the scale, and the next SET carries it
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(scale=0.5, wheel_step=0.1), [
    [Ev(ml.EV_REL, ml.REL_X, 200), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],           # cursor at its rail, 0.5 out
    [Ev(ml.EV_REL, ml.REL_WHEEL, 1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],         # scale 0.6
    [Ev(ml.EV_REL, ml.REL_WHEEL, 1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],         # scale 0.7
    [Ev(ml.EV_REL, ml.REL_WHEEL, -1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],        # scale 0.6
])
check("wheel notches move the scale, and a held cursor moves with it", node,
      ["SET 0.5000 0.0000 0.0000", "SET 0.6000 0.0000 0.0000", "SET 0.7000 0.0000 0.0000",
       "SET 0.6000 0.0000 0.0000"])

# 7. the scale cannot be scrolled out of its own range
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(scale=0.95, wheel_step=0.1), [
    [Ev(ml.EV_REL, ml.REL_WHEEL, 1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    [Ev(ml.EV_REL, ml.REL_WHEEL, 1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    press(ml.BTN_MIDDLE, 1),
])
state("scale stops at 1.00 and the extra notch sends nothing new", session.scale == 1.0
      and node.lines == ["SET 0.0000 0.0000 0.0000"], f"scale {session.scale}, lines {node.lines}")
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(scale=0.05, wheel_step=0.1), [
    [Ev(ml.EV_REL, ml.REL_WHEEL, -1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    [Ev(ml.EV_REL, ml.REL_WHEEL, -1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
])
state("and at the bottom too: 0.01 is as small a workspace as the script goes", session.scale == 0.01,
      f"scale {session.scale}")

# 8. right click cycles what the wheel changes; the button itself is not a setpoint
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(), [
    press(ml.BTN_RIGHT, 1),
    press(ml.BTN_RIGHT, 1),
])
state("right click cycles scale -> delay -> scale and adds no extra SET",
      session.wheel_target == "scale" and node.lines == ["SET 0.0000 0.0000 0.0000"],
      f"target {session.wheel_target}, lines {node.lines}")

# 8b. in delay mode, a wheel notch changes the running node's laser-edge spacing instead of the scale
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(delay_step=25.0), [
    [Ev(ml.EV_KEY, ml.BTN_RIGHT, 1)],
    [Ev(ml.EV_REL, ml.REL_WHEEL, 1)],
])
state("delay-mode wheel sends DELAY and leaves scale/SET lines alone",
      node.delay_reply == "DELAY 358.3" and session.delay_us == 358.3 and session.scale == 1.0
      and node.lines == ["DELAY 358.3"],
      f"node says {node.delay_reply}, delay {session.delay_us}, scale {session.scale}, lines {node.lines}")

# 9. middle click centres the cursor
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(), [
    [Ev(ml.EV_REL, ml.REL_X, 200), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],           # cursor at the rail
    press(ml.BTN_MIDDLE, 1),
])
check("middle click centres: the cursor goes back to 0 and the SET says so", node,
      ["SET 1.0000 0.0000 0.0000", "SET 0.0000 0.0000 0.0000"])

# 10. the wheel works with the cursor parked, which is what a working-area knob is for
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(wheel_step=0.2, scale=0.8), [
    [Ev(ml.EV_REL, ml.REL_X, 200), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    [Ev(ml.EV_REL, ml.REL_WHEEL, -1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
])
check("wheel at the rail maps 0.8 -> 0.6 of the field", node,
      ["SET 0.8000 0.0000 0.0000", "SET 0.6000 0.0000 0.0000"])

# 11. absolute device: its own corners are the rails, its down is -y
dev = FakeDev("Wacom ISD v4 Pen", ABS_CAPS)
node, session, _ = run(dev, "absolute", args(), [
    [Ev(ml.EV_ABS, ml.ABS_X, 4095), Ev(ml.EV_ABS, ml.ABS_Y, 0), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    [Ev(ml.EV_ABS, ml.ABS_Y, 4095), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
])
check("absolute device maps 0..4095 onto -1..+1", node,
      ["SET 1.0000 1.0000 0.0000", "SET 1.0000 -1.0000 0.0000"])

# 12. deadband swallows jitter, a switch flip through the deadband still goes out
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(deadband=0.05, sensitivity=0.01), [
    [Ev(ml.EV_REL, ml.REL_X, 10), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],      # 0.001 u: below deadband
    press(ml.BTN_LEFT, 1),                                                # laser change goes through
])
check("deadband 0.05 keeps later jitter out but sends the switch", node,
      ["SET 0.0010 0.0000 0.0000", "SET 0.0010 0.0000 1.0000"])

# 13. --idle-off flips the switch off; a click brings it back
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(idle_off=0.3), [
    press(ml.BTN_LEFT, 1),
])
time.sleep(0.9)
dev.feed(Ev(ml.EV_REL, ml.REL_X, 40), Ev(ml.EV_SYN, ml.SYN_REPORT, 0))
time.sleep(0.2)
dev.feed(*press(ml.BTN_LEFT, 1))
time.sleep(0.3)
check("--idle-off flips the switch off; motion alone stays dark, the click flips it back on", node.lines[:4],
      ["SET 0.0000 0.0000 1.0000", "SET 0.0000 0.0000 0.0000", "SET 0.2000 0.0000 0.0000",
       "SET 0.2000 0.0000 1.0000"])

# 14. --idle-off on an --always-on run blanks the beam and the next motion brings it back
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(always_on=True, idle_off=0.3), [
    press(ml.BTN_LEFT, 1),
])
time.sleep(0.9)
dev.feed(Ev(ml.EV_REL, ml.REL_X, 40), Ev(ml.EV_SYN, ml.SYN_REPORT, 0))
time.sleep(0.3)
check("--idle-off with --always-on", node.lines[:3],
      ["SET 0.0000 0.0000 1.0000", "SET 0.0000 0.0000 0.0000", "SET 0.2000 0.0000 1.0000"])

# 15. park writes 0,0,0
node = FakeNode()
s = ml.Session(args(), node)
s.cx = s.cy = 0.7
s.commit(force=True)
s.park()
check("park() sends SET 0 0 0", node, ["SET 0.7000 0.7000 0.0000", "SET 0.0000 0.0000 0.0000"])

# 16. sync_from_node starts the switch where the beam is, and reads the node's edge spacing
node = FakeNode(get_reply="SET 0.2500 -0.1000 1", delay_reply="DELAY 412.0")
s = ml.Session(args(), node)
ml.sync_from_node(s)
state("sync_from_node adopts a lit beam and the node's DELAY", s.on and s.delay_us == 412.0,
      f"on={s.on}, delay={s.delay_us}")
node = FakeNode(get_reply="SET 0.2500 -0.1000 0", delay_reply="DELAY 0.0")
s = ml.Session(args(), node)
ml.sync_from_node(s)
state("a parked node starts the switch off", not s.on and s.delay_us == 0.0,
      f"on={s.on}, delay={s.delay_us}")
node = FakeNode(get_reply="SET 0.2500 -0.1000 0", delay_reply="")
s = ml.Session(args(), node)
ml.sync_from_node(s)
state("a node too old for DELAY is read as no compensation", s.delay_us is None, f"delay={s.delay_us}")

# 17. the wheel is not a laser control: a notch never lights the line and never darkens it
dev = FakeDev("Mouse", REL_CAPS)
node, session, _ = run(dev, "relative", args(scale=0.5), [
    [Ev(ml.EV_REL, ml.REL_WHEEL, 1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    [Ev(ml.EV_REL, ml.REL_WHEEL, -1), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
])
check("wheel notches never appear on the laser field of a SET", node,
      ["SET 0.0000 0.0000 0.0000"])

# 18. laser() is the switch, nothing else
s = ml.Session(args(), None)
off = s.laser()
s.on = True
on = s.laser()
s.blanked = True                          # what --idle-off does to an --always-on run
blanked = s.laser()
state("the switch alone decides the laser field", (off, on, blanked) == (0.0, 1.0, 0.0),
      f"switch off {off}, on {on}, blanked {blanked}")

# 19. --max-hz holds the rate down but the newest position still goes out
dev = FakeDev("Mouse", REL_CAPS)
packs = [[e for _ in range(8) for e in (Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0))]]
node, session, _ = run(dev, "relative", args(max_hz=20, sensitivity=0.05), packs, seconds=0.9)
last = node.lines[-1] if node.lines else ""
ok = len(node.lines) <= 6 and last == "SET 0.4000 0.0000 0.0000"
print(f"{'ok  ' if ok else 'FAIL'} --max-hz 20 over 8 rapid kicks: {len(node.lines)} sends, last {last}")
if not ok:
    fails.append("max-hz")

# 20. an evdev that returns one event per read() (older spelling) is drained the same way
dev = FakeDev("Intelaag mouse", REL_CAPS, gen_mode=False)
node, session, _ = run(dev, "relative", args(), [
    [Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_REL, ml.REL_Y, -100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    press(ml.BTN_LEFT, 1),
])
check("read() returning one event at a time works too", node,
      ["SET 0.5000 0.5000 0.0000", "SET 0.5000 0.5000 1.0000"])

# 21. the helper that reads the node's edge spacing off the wire
ok = (ml.parse_delay("DELAY 333.3") == 333.3 and ml.parse_delay("DELAY 0.0") == 0.0
      and ml.parse_delay("FREQ 3000.0") is None and ml.parse_delay("DELAY") is None
      and ml.parse_delay("DELAY a") is None and ml.parse_delay(None) is None)
state("parse_delay reads \"DELAY 333.3\" and refuses anything that is not a delay", ok, ok)

# 22. the mapping the bench runs with, seen from the socket: hand and wall agree
move_up_right = [[Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_REL, ml.REL_Y, -100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
                 press(ml.BTN_LEFT, 1)]                    # 100 counts right, 100 counts up, then the switch

dev = FakeDev("Logitech MX Vertical", REL_CAPS)
node, _s, _n = run(dev, "relative", args(invert_y=True), move_up_right)
check("mouse right and up sends x to the right and y to the top of the wall (field +y is down)", node,
      ["SET 0.5000 -0.5000 0.0000", "SET 0.5000 -0.5000 1.0000"])

dev = FakeDev("Logitech MX Vertical", REL_CAPS)
node, _s, _n = run(dev, "relative", args(raw_field=True, invert_y=True), move_up_right)
check("--raw-field sends the cursor as the script computed it, mirror flags or no mirror flags", node,
      ["SET 0.5000 0.5000 0.0000", "SET 0.5000 0.5000 1.0000"])

dev = FakeDev("Logitech MX Vertical", REL_CAPS)
node, _s, _n = run(dev, "relative", args(invert_y=True, swap_xy=True), move_up_right)
check("--swap-xy hands x to the Y rail after the mirroring, not before", node,
      ["SET -0.5000 0.5000 0.0000", "SET -0.5000 0.5000 1.0000"])

# 23. what the wire carries: the switch, at full, and nothing else
dev = FakeDev("Logitech MX Vertical", REL_CAPS)
node, _s, _n = run(dev, "relative", args(), [
    [Ev(ml.EV_REL, ml.REL_X, 100), Ev(ml.EV_SYN, ml.SYN_REPORT, 0)],
    press(ml.BTN_LEFT, 1),
    press(ml.BTN_LEFT, 1),
])
check("on is 1.0000 and off is 0.0000 - the line has nothing in between", node,
      ["SET 0.5000 0.0000 0.0000", "SET 0.5000 0.0000 1.0000", "SET 0.5000 0.0000 0.0000"])

print(f"\n{ran - len(fails)}/{ran} {'passed' if not fails else 'passed, failures: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
