#!/usr/bin/env python3
"""Pattern demo for laser_node: circle, square and raster scans.

You give it a **speed** - how fast the spot should travel across the field - and the script works out
how many points each shape needs, how far apart they are and how long each one is held. There is no
fixed "points per circle" any more: the density comes from the shape's path length, the speed you
asked for, the geometric accuracy you want, and how often the node can pick up a new setpoint.

    python3 scripts/demo.py --speed 10                     # all three patterns, 10 field units/s
    python3 scripts/demo.py --speed 25 --pattern circle --endless
    python3 scripts/demo.py --speed 40 --accuracy 0.001    # tighter shape -> more points
    python3 scripts/demo.py --speed 12 --spacing 0.05      # raster with 0.05 field between lines
    python3 scripts/demo.py --speed 12 --retrace 4         # blank return sweeps four times as fast
    python3 scripts/demo.py --speed 2 --size 0.3           # a small patch: settling and ringing up close
    python3 scripts/demo.py --speed 10 --scale 0.1         # the same patterns a tenth the size
    python3 scripts/demo.py --speed 300 --plan-only        # just show the computed density

Units: x, y and speed are field units, where the field is -1..+1 - one unit is the distance from the
middle to one rail. --size is the width and height of the drawing, so --size 2 fills the field and
--radius (half of it) is the older spelling. A full left-to-right sweep over a radius-0.8 pattern is
1.6 units: 1.6 s at --speed 1, 0.16 s at --speed 10.

How the density comes out. The node ramps each new setpoint within one ALSA period, so a commanded
step travels in one update slot:

    dt_min = 1 / --updates                       one update slot of the node (rate / period)
    step   = speed * dt_min                      the step that *is* the speed you asked for
    limit  = sqrt(8 * radius * --accuracy)       on a curve: a chord may cut the corner no more than that
             = --max-step                        on a straight segment: biggest single commanded move
    points = path / min(step, limit)             rounded up, carried over the whole shape so the
                                                 rounding does not add up segment by segment

If your speed would need bigger steps than the limit allows, the shape can only be drawn as fast as
the limit permits, and the script says so instead of quietly lying about the speed.

The laser is on while a shape is drawn and off during the moves between raster lines; those blank
moves are walked too, at --retrace times the speed (--retrace 0 makes them one jump, the old
behaviour). Ctrl+C or the end always parks the mirrors at 0,0 with the laser off.

Points are paced against one absolute clock, so the pacing does not drift, and the numbers printed at
the end of a run are what actually happened rather than what was planned. On the Pi this script keeps
up with 6000 points/s; if a measured rate falls short of its plan, check that --updates matches the
node's rate/period first, then look at what else is running on the board.
"""

import argparse
import math
import os
import socket
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import laser_field


def parse_args():
    p = argparse.ArgumentParser(description="laser_node galvo pattern demo, speed driven")
    p.add_argument("--socket", default=os.environ.get("LASER_SOCKET", "/tmp/laser.sock"))
    p.add_argument("--pattern", choices=["circle", "square", "lines", "all"], default="all")
    p.add_argument("--speed", type=float, default=10.0,
                   help="spot speed in field units per second (1.0 = middle to one rail per second)")
    p.add_argument("--updates", type=int, default=6000,
                   help="how often per second the node takes a new setpoint: its rate / period "
                        "(384 kHz at period 64 = 6000; with --no-rt it is 384000/256 = 1500)")
    p.add_argument("--accuracy", type=float, default=0.005,
                   help="how far a drawn curve may cut the corner of the true shape, field units")
    p.add_argument("--max-step", type=float, default=0.05,
                   help="biggest single commanded move along a straight drawn segment, field units")
    p.add_argument("--retrace", type=float, default=1.0,
                   help="speed multiplier for the blank moves between raster lines (0 = one jump)")
    p.add_argument("--radius", type=float, default=0.8, help="pattern half size, 0..1 (the older spelling of --size)")
    p.add_argument("--size", type=float, help="width and height of the drawing in field units: 2.0 fills the whole "
                                              "field, 0.2 is a small patch; overrides --radius")
    p.add_argument("--scale", type=float, default=1.0, help="multiplier on that size: --scale 0.1 draws a tenth size "
                                              "pattern in the middle of the field (default 1)")
    p.add_argument("--spacing", type=float, default=0.1, help="distance between raster lines, field units (absolute, "
                                              "so --scale changes how many lines fit rather than how dense they are)")
    p.add_argument("--lines", type=int, help="raster lines per direction (default: from --spacing)")
    p.add_argument("--points", type=int, help="override the computed density: points per circle or per square edge")
    p.add_argument("--samples", type=int, help="override the computed density: points per raster line")
    p.add_argument("--duration", type=float, default=5.0, help="seconds per pattern (ignored by --endless)")
    p.add_argument("--hold", type=float, default=0.3, help="pause between patterns")
    p.add_argument("--endless", action="store_true", help="keep drawing until Ctrl+C")
    p.add_argument("--plan-only", action="store_true", help="print the computed density and stop")
    laser_field.add_flags(p)
    return p.parse_args()


class Node:
    """Just a line protocol on a Unix socket; the node does the clamping."""

    def __init__(self, path):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.connect(path)
        self.f = s.makefile("rw")

    def set(self, x, y, laser):
        self.f.write(f"SET {x:.4f} {y:.4f} {laser:.4f}\n")
        self.f.flush()

    def get(self):
        self.f.write("GET\n")
        self.f.flush()
        return self.f.readline().strip()


# A pattern is a polyline plus whether it is a curve: curves get the --accuracy limit, straight
# segments the --max-step limit. Where the samples go is decided by plan() below.

def polyline_circle(r, accuracy):
    """Vertices far enough apart that the chords stay inside --accuracy."""
    sag = max(1e-9, min(0.5 * r, accuracy))
    vertices = max(8, math.ceil(math.pi / math.acos(max(-1.0, min(1.0, 1.0 - sag / r)))))
    return [(r * math.cos(2.0 * math.pi * i / vertices),
             r * math.sin(2.0 * math.pi * i / vertices), 1.0) for i in range(vertices + 1)], True


def polyline_square(r):
    corners = [(-r, -r), (r, -r), (r, r), (-r, r), (-r, -r)]
    return [(x, y, 1.0) for x, y in corners], False  # exact corners, so the sides are straight


def polyline_raster(r, lines):
    """Horizontal lines swept left->right, worked top to bottom, then the same pattern rotated. The
    move from the end of one line to the start of the next is part of the cycle and is walked with the
    laser off, and so is the way back to the start of the pattern."""
    poly = []
    for j in range(lines):
        y = r - 2.0 * r * j / (lines - 1) if lines > 1 else 0.0
        poly.append((-r, y, 0.0))   # arriving at the start of the next line: blank
        poly.append((r, y, 1.0))    # the drawn line
    for j in range(lines):
        x = -r + 2.0 * r * j / (lines - 1) if lines > 1 else 0.0
        poly.append((x, r, 0.0))    # arriving at the start of the next line: blank
        poly.append((x, -r, 1.0))   # the drawn line
    poly.append(poly[0])            # close the cycle: walked back, not jumped
    return poly, False


def orient(poly, o):
    """The shapes are built with +y as the top of the pattern; laser_field turns that into this bench's
    field. Mirroring and swapping are rigid, so every length the plan works with is unchanged."""
    return [laser_field.map_point(o, x, y) + (laser,) for x, y, laser in poly]


def plan(poly, curve, speed, dt_min, s_curve, s_line, retrace, override):
    """Split every segment of the shape into points and describe the resulting cycle.

    The points are spread over the whole shape at one even density - instead of rounding each segment
    up on its own, which for a 29-chord circle would quietly turn 300 u/s into 259 - while every
    vertex of the polyline is still landed on exactly (otherwise a square gets its corners cut).
    """
    items = []
    for (x0, y0, _prev), (x1, y1, laser) in zip(poly, poly[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        blanked = laser == 0.0
        items.append({"x0": x0, "y0": y0, "x1": x1, "y1": y1, "laser": laser, "blank": blanked,
                      "len": length, "v": speed * (retrace if blanked else 1.0),
                      "limit": s_line if blanked else (s_curve if curve else s_line)})

    for it in items:
        if override:
            it["n"] = max(1, override)
            it["dt"] = max(dt_min, (it["len"] / it["n"]) / it["v"]) if it["v"] > 0 else 0.0
        elif it["v"] <= 0.0:  # --retrace 0: one jump, the node ramps it across in a single period
            it["n"], it["dt"] = 1, 0.0

    for blanked in (False, True):
        group = [it for it in items if it["blank"] == blanked and "n" not in it]
        if not group:
            continue
        v = group[0]["v"]
        limit = group[0]["limit"]
        total = sum(it["len"] for it in group)
        step = min(v * dt_min, limit)
        step = total / max(len(group), math.ceil(total / step)) if total > 0 else step
        reached = 0.0
        for it in group:
            before, after = reached, reached + it["len"]
            it["n"] = max(1, int(after / step) - int(before / step))
            it["dt"] = dt_min if it["n"] * step > 0 else 0.0
            reached = after

    segs = [(it["x0"], it["y0"], it["x1"], it["y1"], it["laser"], it["n"], it["dt"]) for it in items]
    drawn = sum(it["len"] for it in items if not it["blank"])
    blank = sum(it["len"] for it in items if it["blank"])
    drawn_time = sum(it["n"] * it["dt"] for it in items if not it["blank"])
    blank_time = sum(it["n"] * it["dt"] for it in items if it["blank"])
    cycle_time = drawn_time + blank_time
    return {
        "segs": segs,
        "points": sum(it["n"] for it in items),
        "drawn": drawn,
        "blank": blank,
        "path": drawn + blank,
        "cycle_time": cycle_time,
        "drawn_speed": drawn / drawn_time if drawn_time else 0.0,
        "step": min((it["len"] / it["n"] for it in items if it["n"]), default=0.0),
    }


def walk(segs):
    """Every commanded point of one cycle, each with the time it should be held."""
    for x0, y0, x1, y1, laser, n, dt in segs:
        for k in range(n):
            t = k / n
            yield x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, laser, dt
    x0, y0, x1, y1, laser, _n, dt = segs[-1]
    yield x1, y1, laser, dt


def describe(name, p, curve, speed, updates, dt_min, s_curve, s_line):
    print(f"--- {name}: path {p['path']:.2f} u (drawn {p['drawn']:.2f}, blank {p['blank']:.2f})")
    if p["cycle_time"] > 0:
        print(f"      {p['points']} points/cycle  {p['cycle_time']:.3f} s/cycle  "
              f"{1.0 / p['cycle_time']:.2f} cycles/s  {p['points'] / p['cycle_time']:.0f} points/s  "
              f"drawn at {p['drawn_speed']:.1f} u/s")
    groups = {}
    for x0, y0, x1, y1, laser, n, dt in p["segs"]:
        key = (round(math.hypot(x1 - x0, y1 - y0), 3), laser)
        g = groups.setdefault(key, {"points": 0, "times": 0, "dt": dt, "len": 0.0})
        g["points"] += n
        g["times"] += 1
        g["len"] += math.hypot(x1 - x0, y1 - y0)
    for (length, laser), g in sorted(groups.items(), key=lambda kv: -kv[1]["times"]):
        n_avg, dt, total = g["points"] / g["times"], g["dt"], g["len"]
        print(f"      {'blank' if laser == 0 else 'drawn '} {length:6.3f} u  {n_avg:6.1f} points  "
              f"step {total / g['points']:.4f} u  hold {dt * 1000:6.2f} ms  "
              f"{total / (g['points'] * dt) if g['points'] * dt else 0:6.1f} u/s  x{g['times']}")
    if p["drawn_speed"] < 0.9 * speed:
        limit = s_curve if curve else s_line
        print(f"      note: {speed} u/s needs steps bigger than {limit:.4f} u allows at {updates} "
              f"updates/s ({limit * updates:.0f} u/s is that limit); this shape tops out at "
              f"{p['drawn_speed']:.0f} u/s - raise --max-step / --accuracy or lower --speed")


def main():
    a = parse_args()
    half = a.size / 2.0 if a.size is not None else a.radius
    r = half * a.scale
    if not 0.05 <= r <= 1.0:
        print(f"a {2.0 * r:.2f} u drawing does not fit the field (0.10 .. 2.00), drawing at "
              f"{2.0 * min(1.0, max(0.05, r)):.2f} u instead")
    r = max(0.05, min(1.0, r))
    if a.speed <= 0:
        print("--speed has to be above 0")
        return 2
    dt_min = 1.0 / max(1, a.updates)
    s_curve = math.sqrt(8.0 * r * max(1e-9, a.accuracy))
    s_line = max(1e-9, a.max_step)
    lines = a.lines or max(2, round(2.0 * r / max(1e-9, a.spacing)) + 1)

    patterns = {"circle": polyline_circle(r, a.accuracy),
                "square": polyline_square(r),
                "lines": polyline_raster(r, lines)}
    o = laser_field.orientation(a)
    patterns = {name: (orient(poly, o), curve) for name, (poly, curve) in patterns.items()}
    order = ["circle", "square", "lines"] if a.pattern == "all" else [a.pattern]

    print(f"socket {a.socket}  drawing {2.0 * r:.2f} x {2.0 * r:.2f} u (radius {r:.2f})  "
          f"speed {a.speed} field u/s  node pickup {a.updates}/s "
          f"(dt_min {dt_min * 1000:.3f} ms, one step is {a.speed * dt_min:.4f} u)  "
          f"curve limit {s_curve:.4f} u  straight limit {s_line} u")
    print(laser_field.describe(o))
    print("the node's own startup line says its real rate and period; --updates has to match it")

    plans = []
    for name in order:
        poly, curve = patterns[name]
        override = a.points if name in ("circle", "square") else (a.samples if name == "lines" else None)
        p = plan(poly, curve, a.speed, dt_min, s_curve, s_line, a.retrace, override)
        describe(name, p, curve, a.speed, a.updates, dt_min, s_curve, s_line)
        plans.append((name, p))

    if a.plan_only:
        return 0

    try:
        node = Node(a.socket)
    except OSError as e:
        print(f"cannot connect to {a.socket}: {e}")
        print("start the node first:  systemctl --user start laser-node   (or ./scripts/deploy.sh run)")
        return 1

    print("drawing: " + ("endless (Ctrl+C to stop)" if a.endless else f"{a.duration}s per pattern"))
    try:
        for name, p in plans:
            started = time.monotonic()
            deadline = None if a.endless else started + a.duration
            cycles = sent = 0
            next_report = started + 1.0
            while deadline is None or time.monotonic() < deadline:
                t = time.monotonic()          # absolute schedule: sleeps do not drift across a cycle
                for x, y, laser, dt in walk(p["segs"]):
                    node.set(x, y, laser)
                    sent += 1
                    if dt:
                        t += dt
                        now = time.monotonic()
                        if t > now:
                            time.sleep(t - now)
                        else:
                            t = now           # we fell behind; do not try to burst back up to schedule
                cycles += 1
                if a.endless and time.monotonic() >= next_report:
                    el = time.monotonic() - started
                    print(f"      {name}: {cycles} cycles, {cycles / el:5.2f} cycles/s, "
                          f"{sent / el:6.0f} points/s, {cycles * p['path'] / el:6.1f} u/s over the cycle")
                    next_report = time.monotonic() + 1.0
            el = time.monotonic() - started
            print(f"      {name}: {cycles} cycles in {el:5.2f}s = {cycles / el:5.2f} cycles/s, "
                  f"{sent / el:6.0f} points/s, {cycles * p['path'] / el:6.1f} u/s over the cycle")
            node.set(0.0, 0.0, 0.0)
            time.sleep(a.hold)
    except KeyboardInterrupt:
        print("stopped")
    finally:
        node.set(0.0, 0.0, 0.0)  # always end parked in the middle with the laser off
        node.f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
