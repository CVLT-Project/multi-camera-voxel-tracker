#!/usr/bin/env python3
"""Twenty seconds at the beam that settles, once, which way this bench draws.

    python3 scripts/orient-check.py                    # walk the figure, print every field number
    python3 scripts/orient-check.py --dry              # the numbers only, nothing on the wall
    python3 scripts/orient-check.py --speed 0.4 --hold 2
    python3 scripts/orient-check.py --raw-field        # the same figure with no calibration at all

It sends one asymmetric figure - four parts, each announced before it is drawn, with a pause at every
marked point:

    1  a horizontal arrow, drawn left to right, with a tick at its right end
    2  a vertical arrow, drawn bottom to top, with a tick at its top end
    3  a diagonal from the picture's bottom left to its top right
    4  a small square at the picture's top left corner

If what you see matches what the printed line says - arrow 1 with the tick on the **right**, arrow 2 with
the tick on **top**, the diagonal climbing to the right, the square in the upper left corner - then the
shared orientation in scripts/laser_field.py is right for this mount, and svg.py, demo.py and
mouse_laser.py all draw the same picture. Anything else names the axis that is wrong: a tick on the left
says x is mirrored, a tick at the bottom says y is mirrored, both at once means the figure came out
turned by 180 degrees. Afterwards a map prints where every marked point landed, so the answer can be read
off the paper instead of remembered.

Ctrl+C, and every normal end, parks the mirrors at 0,0 with the laser off.
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
    p = argparse.ArgumentParser(description="check which way this bench draws, with an asymmetric figure",
                               formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--socket", default=os.environ.get("LASER_SOCKET", "/tmp/laser.sock"))
    p.add_argument("--speed", type=float, default=0.6, help="spot speed, field units per second")
    p.add_argument("--hold", type=float, default=1.5, help="pause at each marked point, so the beam visibly settles")
    p.add_argument("--size", type=float, default=0.8, help="how far out the figure reaches: 0.8 is 80 percent of the field")
    laser_field.add_flags(p)
    p.add_argument("--dry-run", "--dry", action="store_true", help="print the numbers, do not touch the node")
    return p.parse_args()


class Laser:
    def __init__(self, path):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(path)
        self.f = self.s.makefile("w")

    def set(self, x, y, laser):
        self.f.write(f"SET {x:.4f} {y:.4f} {laser:.4f}\n")
        self.f.flush()

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


def figure(size):
    """The parts, in picture coordinates: x right, y up, the way a viewer reads them.

    Each point is (x, y, label); a label is a place worth naming on the map.
    """
    s = size
    t = 0.35 * s
    return [
        ("horizontal arrow, drawn left to right, tick at its RIGHT end",
         [(-s, 0.0, "start"), (s, 0.0, "tip"), (s, t, None), (s, -t, "tick"), (s, 0.0, None)]),
        ("vertical arrow, drawn bottom to top, tick at its TOP end",
         [(0.0, -s, "start"), (0.0, s, "tip"), (t, s, None), (-t, s, "tick"), (0.0, s, None)]),
        ("diagonal, from the picture's BOTTOM LEFT to its TOP RIGHT",
         [(-0.85 * s, -0.85 * s, "start"), (0.85 * s, 0.85 * s, "end")]),
        ("small square at the picture's TOP LEFT corner",
         [(-s, 0.7 * s, "start"), (-0.7 * s, 0.7 * s, "corner"), (-0.7 * s, s, "corner"),
          (-s, s, "corner"), (-s, 0.7 * s, "corner")]),
    ]


def walk(laser, pts, speed, dt_min):
    """Draw one part: arrive at its start with the laser off, then trace it."""
    laser.set(pts[0][0], pts[0][1], 0.0)
    for (x0, y0, _), (x1, y1, _) in zip(pts, pts[1:]):
        length = math.hypot(x1 - x0, y1 - y0)
        steps = max(1, int(math.ceil(length / max(speed * dt_min, 1e-9))))
        dwell = length / steps / speed            # >= dt_min, by how the steps were counted
        for k in range(1, steps + 1):
            t = k / steps
            laser.set(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 1.0)
            time.sleep(dwell)


def print_map(points):
    """Where every labelled point landed: field y down the page, field x across."""
    cols = sorted({round(x, 2) for x, y, _ in points})
    rows = sorted({round(y, 2) for x, y, _ in points}, reverse=True)
    grid = {(round(x, 2), round(y, 2)): label for x, y, label in points}
    print(f"   {'field y':>10} " + "".join(f"{c:>9.2f}" for c in cols))
    for r in rows:
        cells = "".join(f"{grid.get((c, r), ''):>9}" for c in cols)
        print(f"   {r:>10.2f} {cells}")
    print("\n   Rows are field y from +1 at the top of this listing down to -1; field +y is the spot")
    print("   moving down, so the first row here is the lowest place on the wall and the last row the")
    print("   highest. \"start\" is where the beam begins a part, \"tip\" its far end, \"tick\" the cross")
    print("   on that end, \"corner\" a corner of the square.")


def main():
    args = parse_args()
    if args.speed <= 0:
        print("--speed has to be above 0")
        return 2
    if not 0.05 <= args.size <= 1.0:
        print("--size has to be between 0.05 and 1")
        return 2
    o = laser_field.orientation(args)

    print("field -1..+1; on this bench +x is the spot moving right and +y is the spot moving down")
    print(laser_field.describe(o))
    print("the corners of the picture, as the field values that go out:")
    for name, x, y in laser_field.corners(o):
        print(f"  {name:13} x {x:+.2f}  y {y:+.2f}")

    parts = [(title, [(*laser_field.map_point(o, x, y), label) for x, y, label in pts])
             for title, pts in figure(args.size)]
    labelled = [(x, y, label) for _, pts in parts for x, y, label in pts if label]

    for title, pts in parts:
        print(f"\n{title}")
        print(f"  start {pts[0][0]:+.2f} {pts[0][1]:+.2f}   end {pts[-1][0]:+.2f} {pts[-1][1]:+.2f}")

    print("\nwhere each marked point lands, with this mapping:")
    print_map(labelled)

    if args.dry_run:
        print("\ndry run: nothing was sent")
        return 0

    try:
        laser = Laser(args.socket)
    except OSError as e:
        print(f"\ncannot connect to {args.socket}: {e}")
        print("start the node first:  systemctl --user start laser-node   (or ./scripts/deploy.sh run)")
        return 1

    print("\nwatch the beam: each part is announced, and the spot pauses at every marked point.")
    print("Ctrl+C parks the mirrors and turns the laser off.\n")
    dt_min = 1.0 / 6000.0                      # the node picks a new setpoint up at ~6 kHz
    try:
        for title, pts in parts:
            print(f"  -> {title}")
            walk(laser, pts, args.speed, dt_min)
            time.sleep(args.hold)
    except KeyboardInterrupt:
        print("\nstopped")
    except OSError as e:
        print(f"\nsocket error: {e}")
        return 1
    finally:
        try:
            laser.park()
        except OSError:
            pass
        laser.close()

    print("\nwhat you should have seen: the tick at the RIGHT end of the horizontal arrow, the tick at the")
    print("TOP of the vertical one, the diagonal climbing to the right, the square in the upper left")
    print("corner. Anything else names the axis to fix - in scripts/laser_field.py for good, or with")
    print("LASER_INVERT_X / LASER_INVERT_Y / LASER_SWAP_XY for this run.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
