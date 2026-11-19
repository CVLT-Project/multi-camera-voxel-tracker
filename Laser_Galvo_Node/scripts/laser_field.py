#!/usr/bin/env python3
"""One orientation for everything that draws on this bench: svg.py, demo.py, mouse_laser.py, orient-check.py.

Why this file exists. Every script here ends up sending `SET <x> <y> <laser>` in field units (-1..+1), and
each one started from its own idea of which way is up:

* `svg.py`  - the picture as Inkscape shows it, mirrored in x and in y ("both channels invert")
* `demo.py` - shapes built with +y as the top of the pattern, sent as computed
* `mouse_laser.py` - a cursor with +y = up (the way a viewer sees a picture), no mirror by default, and the
  bench needed `--invert-y` to make the spot follow the hand

Three starting points is how you get one drawing right side up and the next one mirrored. So the mapping
lives here once, and every script uses `map_point()` with the same flags and the same environment variables.

What the field actually is on this bench (rp4, measured with a mouse on 2026-11-17, laser on PWM0):

    +x  ->  the spot moves to the right      (as somebody looking at the wall sees it)
    +y  ->  the spot moves DOWN              (the vertical rail is the mirrored one)

which means a picture drawn the way a viewer reads it - x right, y up - has to leave as

    field_x = picture_x          no mirror on x on this bench
    field_y = -picture_y         the mirror the mount needs

Those two are the defaults below. They are a statement about *this* mount (amplifier polarity and how the
galvos are bolted down), not about the protocol - on another machine `LASER_INVERT_X=1 LASER_INVERT_Y=0`
is the old "both channels invert" spelling, and `orient-check.py` is the twenty second way to find out
which one a bench is.

Environment, same names in every script:

    LASER_INVERT_X=0|1     LASER_INVERT_Y=0|1     LASER_SWAP_XY=0|1

(`LASER_MOUSE_INVERT_X` / `LASER_MOUSE_INVERT_Y` / `LASER_MOUSE_SWAP_XY` keep working as the older
spelling of the same three, for scripts/mouse_laser.py.) A command line flag always wins over the
environment, and `--raw-field` turns the whole calibration off: what the script computed goes out exactly
as it is, which is what you want when comparing two scripts against each other.
"""

import os
import argparse

TRUE = ("1", "true", "yes", "on")
FALSE = ("0", "false", "no", "off")

# Measured on the rp4 bench, 2026-11-17: x as the picture has it, y mirrored.
INVERT_X = False
INVERT_Y = True
SWAP_XY = False


def flag(names, default):
    """One environment setting, possibly spelled in more than one way."""
    for name in names:
        value = os.environ.get(name, "").strip().lower()
        if value in TRUE:
            return True
        if value in FALSE:
            return False
    return default


def env_orientation():
    """The calibration as the environment states it, or the bench defaults when it says nothing."""
    return {
        "invert_x": flag(("LASER_INVERT_X", "LASER_MOUSE_INVERT_X"), INVERT_X),
        "invert_y": flag(("LASER_INVERT_Y", "LASER_MOUSE_INVERT_Y"), INVERT_Y),
        "swap_xy": flag(("LASER_SWAP_XY", "LASER_MOUSE_SWAP_XY"), SWAP_XY),
    }


def add_flags(parser, **over):
    """The three orientation flags, with the defaults this script wants - each one with its `--no-` spelling
    so a default that belongs to this bench can be turned off without editing anything.

    `--raw-field` is the shared escape hatch: no mirror, no swap, nothing - the numbers the script worked
    out go to the node exactly as they are.
    """
    base = env_orientation()
    base.update(over)
    parser.add_argument("--invert-x", action=argparse.BooleanOptionalAction, default=base["invert_x"],
                        help="mirror the x axis (--no-invert-x keeps it; LASER_INVERT_X)")
    parser.add_argument("--invert-y", action=argparse.BooleanOptionalAction, default=base["invert_y"],
                        help="mirror the y axis (--no-invert-y keeps it; LASER_INVERT_Y)")
    parser.add_argument("--swap-xy", action=argparse.BooleanOptionalAction, default=base["swap_xy"],
                        help="send x to the Y rail and back (LASER_SWAP_XY)")
    parser.add_argument("--raw-field", action="store_true",
                        help="no orientation calibration at all: send what this script computed as it is")


def orientation(args):
    """The flags as they ended up, after --raw-field had its say."""
    if getattr(args, "raw_field", False):
        return {"invert_x": False, "invert_y": False, "swap_xy": False}
    return {"invert_x": bool(args.invert_x), "invert_y": bool(args.invert_y),
            "swap_xy": bool(args.swap_xy)}


def map_point(o, x, y):
    """Viewer coordinates (x right, y up) -> field units. Mirrors first, then the swap, then nothing else:
    a scale is a positive number and commutes with all of it. The + 0.0 keeps a mirrored zero printing as
    0.00 instead of -0.00, which matters the moment a number is shown to a person."""
    if o["invert_x"]:
        x = -x
    if o["invert_y"]:
        y = -y
    if o["swap_xy"]:
        x, y = y, x
    return x + 0.0, y + 0.0


def describe(o):
    """One line, in the same words in every script, saying what the mapping did."""
    what_x = "mirrored" if o["invert_x"] else "as the picture has it"
    what_y = "mirrored" if o["invert_y"] else "as the picture has it"
    line = f"orientation: x {what_x}, y {what_y}"
    if o["swap_xy"]:
        line += ", rails swapped"
    env = [name for name, on in (("LASER_INVERT_X", o["invert_x"]), ("LASER_INVERT_Y", o["invert_y"]),
                                ("LASER_SWAP_XY", o["swap_xy"])) if on]
    return line + (f"  [{', '.join(env)}]" if env else "  [nothing applied]")


def corners(o):
    """The four corners of the picture as field values - the table a human can check against the wall."""
    names = (("top right", 1.0, 1.0), ("top left", -1.0, 1.0), ("bottom right", 1.0, -1.0),
             ("bottom left", -1.0, -1.0))
    return [(name,) + map_point(o, x, y) for name, x, y in names]


if __name__ == "__main__":
    o = env_orientation()
    print(describe(o))
    print("the corners of a picture, as field units:")
    for name, x, y in corners(o):
        print(f"  {name:12}  x {x:+.2f}  y {y:+.2f}")
    print("\nfield +x is the spot moving right, field +y is the spot moving down (measured on the rp4 bench)")
    print("compare with:  python3 scripts/orient-check.py --dry-run")
