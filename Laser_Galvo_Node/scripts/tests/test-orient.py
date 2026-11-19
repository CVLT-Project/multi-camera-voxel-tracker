#!/usr/bin/env python3
"""Tests for scripts/laser_field.py - the one orientation svg.py, demo.py and mouse_laser.py share.

    ./scripts/tests/test-orient.py

No socket, no hardware: this checks the mapping and the flags only, which is exactly the part that used to
live three times in three scripts and drift.
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import laser_field

fails = []
ran = 0


def check(label, got, want):
    global ran
    ran += 1
    ok = got == want
    print(f"{'ok  ' if ok else 'FAIL'} {label}\n     got    {got}\n     want   {want}")
    if not ok:
        fails.append(label)


def state(label, ok, detail):
    global ran
    ran += 1
    print(f"{'ok  ' if ok else 'FAIL'} {label}: {detail}")
    if not ok:
        fails.append(label)


O = lambda ix, iy, sw: {"invert_x": ix, "invert_y": iy, "swap_xy": sw}      # noqa: E731

# ------------------------------------------------------------------ the mapping itself

# The bench default: the picture as a viewer reads it, y mirrored (measured with a mouse on the mount).
check("bench default maps the picture's corners", laser_field.corners(O(False, True, False)),
      [("top right", 1.0, -1.0), ("top left", -1.0, -1.0),
       ("bottom right", 1.0, 1.0), ("bottom left", -1.0, 1.0)])

check("nothing applied sends the picture as written",
      [laser_field.map_point(O(False, False, False), x, y) for x, y in ((1, 1), (-1, 1), (1, -1), (-1, -1))],
      [(1, 1), (-1, 1), (1, -1), (-1, -1)])

check("mirroring both axes is the same picture turned by 180 degrees",
      [laser_field.map_point(O(True, True, False), x, y) for x, y in ((1, 1), (-1, 1))], [(-1, -1), (1, -1)])

check("swapping hands x to the Y rail", laser_field.map_point(O(False, False, True), 0.6, -0.2), (-0.2, 0.6))

check("mirrors come before the swap", laser_field.map_point(O(True, False, True), 0.6, -0.2), (-0.2, -0.6))

check("a mirrored zero is 0.00 and not -0.00",
      [f"{v:+.2f}" for v in laser_field.map_point(O(True, True, False), 0.0, 0.0)], ["+0.00", "+0.00"])

# Lengths survive: the plan each script builds (steps, chords, path length) is the same either way.
a = laser_field.map_point(O(True, False, True), 0.3, 0.4)
b = laser_field.map_point(O(True, False, True), 0.9, -0.4)
state("mirroring and swapping keep distances", abs((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 - (0.6 ** 2 + 0.8 ** 2))
      < 1e-12, f"{(a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2:.4f} == 1.0000")

# ------------------------------------------------------------------ environment and flags

CLEAN = ("LASER_INVERT_X", "LASER_INVERT_Y", "LASER_SWAP_XY",
         "LASER_MOUSE_INVERT_X", "LASER_MOUSE_INVERT_Y", "LASER_MOUSE_SWAP_XY")


from contextlib import contextmanager          # noqa: E402  (a test needs its environment put back)


@contextmanager
def under_env(**values):
    """Run a block as if the shell had these variables and nothing else orientation related."""
    saved = {k: os.environ.get(k) for k in CLEAN}
    for k in CLEAN:
        os.environ.pop(k, None)
    os.environ.update(values)
    try:
        yield
    finally:
        for k, v in saved.items():
            os.environ.pop(k, None)
            if v is not None:
                os.environ[k] = v


def with_env(**values):
    with under_env(**values):
        return laser_field.env_orientation()


check("no environment says the bench default", with_env(), O(False, True, False))
check("LASER_INVERT_X=1 turns the x mirror on", with_env(LASER_INVERT_X="1"), O(True, True, False))
check("LASER_INVERT_Y=0 turns the y mirror off", with_env(LASER_INVERT_Y="0"), O(False, False, False))
check("off/false/no are off, not just absent", with_env(LASER_INVERT_X="no", LASER_INVERT_Y="off"),
      O(False, False, False))
check("the older LASER_MOUSE_* spelling reaches the same setting",
      with_env(LASER_MOUSE_SWAP_XY="yes"), O(False, True, True))
check("a flag in the environment beats the bench default, and nothing else moves",
      with_env(LASER_SWAP_XY="1"), O(False, True, True))

with under_env():                       # the flag checks below mean "the shell says nothing".
    p = argparse.ArgumentParser()
    laser_field.add_flags(p)
    args = p.parse_args([])
    check("flags start at the environment's saying", laser_field.orientation(args), O(False, True, False))
    check("--no-invert-y is how a default gets turned off",
          laser_field.orientation(p.parse_args(["--no-invert-y"])), O(False, False, False))
    check("--invert-x is how a default gets turned on",
          laser_field.orientation(p.parse_args(["--invert-x"])), O(True, True, False))
    check("--raw-field sends what the script computed, flags or no flags",
          laser_field.orientation(p.parse_args(["--invert-x", "--swap-xy", "--raw-field"])),
          O(False, False, False))

# A different mount, spelled the old "both channels invert" way: one environment, every script follows it.
env = O(True, False, False)
with under_env(LASER_INVERT_X="1", LASER_INVERT_Y="0"):
    pp = argparse.ArgumentParser()
    laser_field.add_flags(pp)
    got = laser_field.orientation(pp.parse_args([]))
state("one environment, one answer for every script", got == env, laser_field.describe(env))

# ------------------------------------------------------------------ how the scripts use it

# demo.py: shapes built with +y as the top of the pattern, then oriented.
import demo                                                      # noqa: E402
poly = [(0.0, 0.8, 0.0), (0.8, 0.8, 1.0), (0.8, -0.8, 1.0)]     # a line along the top of the pattern, drawn right
check("demo.orient moves the top of a pattern to the top of the wall (field y is the mirrored one)",
      demo.orient(poly, O(False, True, False)),
      [(0.0, -0.8, 0.0), (0.8, -0.8, 1.0), (0.8, 0.8, 1.0)])
check("demo.orient keeps the laser flag with its point",
      [p[2] for p in demo.orient(poly, O(True, True, True))], [0.0, 1.0, 1.0])

# svg.py: user coordinates (SVG's y axis points down) -> the picture -> the shared mapping -> the scale.
import svg                                                      # noqa: E402

# A 10 x 10 drawing whose middle is (5, 5); in SVG's own numbers the picture's top left is (0, 0).
corner = {"top left": (0.0, 0.0), "top right": (10.0, 0.0), "bottom left": (0.0, 10.0),
          "bottom right": (10.0, 10.0)}
draw = svg.field_mapper(O(False, True, False), 5.0, 5.0, 0.1)
check("svg.py sends the picture's top left to the top left of the wall",
      [round(v, 6) for v in draw(*corner["top left"])], [-0.5, -0.5])
check("svg.py sends the picture's bottom right to the bottom right of the wall",
      [round(v, 6) for v in draw(*corner["bottom right"])], [0.5, 0.5])
check("svg.py with nothing applied keeps SVG's own y direction",
      [round(v, 6) for v in svg.field_mapper(O(False, False, False), 5.0, 5.0, 0.1)(*corner["top left"])],
      [-0.5, 0.5])
check("svg.py with both axes mirrored is the picture mirrored left to right",
      [round(v, 6) for v in svg.field_mapper(O(True, True, False), 5.0, 5.0, 0.1)(*corner["top left"])],
      [0.5, -0.5])
check("svg.py mirroring x alone turns the picture by 180 degrees",
      [round(v, 6) for v in svg.field_mapper(O(True, False, False), 5.0, 5.0, 0.1)(*corner["top left"])],
      [0.5, 0.5])
check("svg.py scales before the mapping matters: the same corner at --scale 1",
      [round(v, 6) for v in svg.field_mapper(O(False, True, False), 5.0, 5.0, 0.2)(*corner["top left"])],
      [-1.0, -1.0])


def svg_args(**over):
    a = dict(invert_x=False, invert_y=True, swap_xy=False, raw_field=False, no_flip_x=False, no_flip_y=False)
    a.update(over)
    return argparse.Namespace(**a)


check("the old --no-flip-x spelling means --no-invert-x", svg.orientation_of(svg_args(no_flip_x=True)),
      O(False, True, False))
check("the old --no-flip-y spelling means --no-invert-y", svg.orientation_of(svg_args(no_flip_y=True)),
      O(False, False, False))
check("--raw-field wins over the older spellings as well",
      svg.orientation_of(svg_args(raw_field=True, no_flip_x=True)), O(False, False, False))

# mouse_laser.py: the cursor is a viewer-space position, and project() is map_point plus the working scale.
import mouse_laser                                              # noqa: E402


class FakeNode:
    def set(self, x, y, laser):
        pass


def session_with(invert_x, invert_y, swap_xy, scale):
    a = argparse.Namespace(socket="x", scale=scale, raw_field=False, invert_x=invert_x, invert_y=invert_y,
                           swap_xy=swap_xy, wheel_step=0.05, quiet=True)
    s = mouse_laser.Session(a, FakeNode())
    s.cx, s.cy = 0.6, 0.2                                        # cursor right of centre, above centre
    return s


for ix, iy, sw in ((False, True, False), (False, False, False), (True, True, True), (True, False, True)):
    s = session_with(ix, iy, sw, 0.5)
    want = [v * 0.5 for v in laser_field.map_point(O(ix, iy, sw), 0.6, 0.2)]
    check(f"mouse_laser.project matches map_point for x={'on' if ix else 'off'}/"
          f"y={'on' if iy else 'off'}/swap={'on' if sw else 'off'}", [round(v, 6) for v in s.project()],
          [round(v, 6) for v in want])

s = session_with(False, True, False, 1.0)
s.args.raw_field = True
s.o = laser_field.orientation(s.args)
check("mouse_laser --raw-field sends the cursor as it is", [round(v, 6) for v in s.project()], [0.6, 0.2])

print(f"\n{ran - len(fails)}/{ran} {'passed' if not fails else 'passed, failures: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
