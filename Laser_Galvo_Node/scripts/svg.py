#!/usr/bin/env python3
"""Trace an SVG drawing with the galvos.

    python3 scripts/svg.py art.svg                          # fit it to the field, trace it for 5 s
    python3 scripts/svg.py art.svg --scale 0.25             # a quarter of the field
    python3 scripts/svg.py art.svg --speed 40               # 40 field units per second
    python3 scripts/svg.py art.svg --speed 60 --duration 30
    python3 scripts/svg.py art.svg --plan-only              # geometry and density, no laser

Arguments: the file, --scale, --speed, --duration, plus the same socket / updates / retrace / max-step
/ accuracy knobs as demo.py - it imports the density and pacing code from demo.py rather than
repeating it, so the two scripts behave the same way.

What is read (standard library only, no SVG library): <path> with M L H V C S Q T A Z in absolute and
relative form, <line>, <polyline>, <polygon>, <rect>, <circle>, <ellipse>, <g> and nested <svg> with
translate / scale / rotate / skew / matrix transforms, and <use> references into <defs>. Curves are
flattened into straight chords, arcs are sampled from their exact centre parameterisation, and every
corner the polyline really has stays a sample point.

Not traced, and reported as skipped: <text>, <image>, <symbol>, <defs>, clip/mask/pattern/marker
definitions. Rounded corners on <rect> (rx/ry) are ignored: they are smaller than the laser spot.
Styling is only read from the fill / stroke / display / visibility attributes and the style= attribute
(including inherited ones on groups); a <style> block with classes is not interpreted, which is why
--only-stroke can keep a colour logo and can also keep a shape you meant to drop.

--accuracy is the budget for how far the traced path may sit from the shape in the file, and it is spent
twice: flattening a curve into chords may use half of it, and dropping a point that a straight line
between its neighbours already covers may use the other half. That is what makes the speed reachable: a
file converted from a drawing carries a path command every few microns, and honouring every one of them
at 6000 updates per second would cap the spot far below what it can follow. --no-simplify keeps every
point the file and the flattening produce, which is what you want when comparing against the file.

Size: the drawing's own bounding box is centred on 0,0 and scaled so its widest dimension spans the
field (-1..+1) at --scale 1.0; --scale 0.5 is half that, --scale 2 asks for twice the field and is
clamped to it with a message instead of being silently cut off. SVG's y axis points down, so the picture
- what a viewer shows you - is (x - middle, middle - y); from the picture, the orientation is the shared
one in scripts/laser_field.py (x as the picture has it, y mirrored on this bench, measured with a mouse on
the mount). `--invert-x` / `--invert-y` / `--swap-xy` and `LASER_INVERT_X` / `LASER_INVERT_Y` /
`LASER_SWAP_XY` are the same flags and variables svg.py, demo.py and mouse_laser.py all read, so one
setting moves all of them together, and `python3 scripts/orient-check.py` is the twenty second way to
find out what a bench needs.

Drawing: subpaths are traced in document order with the laser on. The move from the end of one subpath
to the start of the next is walked with the laser off at --retrace times the speed, and so is the walk
back to the start at the end of the cycle, which is what makes the repeat continuous. Ctrl+C or the end
of --duration parks the mirrors at 0,0 with the laser off.
"""

import argparse
import collections
import math
import os
import re
import sys
import time
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from demo import Node, plan, walk  # noqa: E402  the shared density and pacing rules
import laser_field  # noqa: E402  the one orientation every script here uses

NUM = r"[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?"
COUNTS = {"M": 2, "L": 2, "H": 1, "V": 1, "C": 6, "S": 4, "Q": 4, "T": 2, "A": 7, "Z": 0}
FOLLOW = {"M": "L", "L": "L", "H": "H", "V": "V", "C": "C", "S": "S", "Q": "Q", "T": "T", "A": "A",
          "Z": "L"}
IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)
SKIP_TAGS = {"defs", "clipPath", "mask", "pattern", "marker", "filter", "style", "script", "title",
             "desc", "metadata", "text", "tspan", "textPath", "image", "foreignObject", "symbol"}
STYLE_KEYS = ("fill", "stroke", "display", "visibility")


def parse_args():
    p = argparse.ArgumentParser(description="trace an SVG file with laser_node")
    p.add_argument("file", help="path to the .svg file")
    p.add_argument("--scale", type=float, default=1.0,
                   help="size as a fraction of the field: 1.0 fills it, 0.25 is a quarter of it")
    p.add_argument("--speed", type=float, default=10.0,
                   help="spot speed in field units per second (1.0 = middle to one rail per second)")
    p.add_argument("--duration", type=float, default=5.0, help="seconds to keep tracing the drawing")
    p.add_argument("--socket", default=os.environ.get("LASER_SOCKET", "/tmp/laser.sock"))
    p.add_argument("--updates", type=int, default=6000,
                   help="how often per second the node takes a new setpoint: its rate / period "
                        "(384 kHz at period 64 = 6000; with --no-rt it is 384000/256 = 1500)")
    p.add_argument("--accuracy", type=float, default=0.005,
                   help="how far the traced polyline may deviate from the curves in the file, field units; "
                        "it sets the chord length curves are flattened to and how much of the file's own "
                        "point density can be skipped")
    p.add_argument("--no-simplify", action="store_true",
                   help="keep every point the file and the flattening produce, instead of dropping the ones "
                        "that lie within --accuracy of a straight line")
    p.add_argument("--max-step", type=float, default=0.05,
                   help="biggest single commanded move, field units; it caps the speed at max-step*updates")
    p.add_argument("--retrace", type=float, default=1.0,
                   help="speed multiplier for the blank moves between subpaths (0 = one jump)")
    p.add_argument("--only-stroke", action="store_true",
                   help="trace only the shapes that say they are stroked, which is what a colour figure "
                        "from Inkscape usually needs")
    p.add_argument("--no-flip-x", action="store_true",
                   help="older spelling of --no-invert-x: keep the picture's own x direction")
    p.add_argument("--no-flip-y", action="store_true",
                   help="older spelling of --no-invert-y: keep the picture's own y direction")
    p.add_argument("--endless", action="store_true", help="keep tracing until Ctrl+C")
    p.add_argument("--plan-only", action="store_true", help="print the geometry and the plan, do not draw")
    laser_field.add_flags(p)
    return p.parse_args()


# ---------------------------------------------------------------- transforms

def mul(m1, m2):
    """Compose two affine matrices in SVG order: the point is transformed by m2 first, then m1."""
    a1, b1, c1, d1, e1, f1 = m1
    a2, b2, c2, d2, e2, f2 = m2
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def apply(m, x, y):
    a, b, c, d, e, f = m
    return a * x + c * y + e, b * x + d * y + f


def stretch_of(m):
    """How much this transform can lengthen a distance - used to shrink a local tolerance."""
    return max(math.hypot(m[0], m[1]), math.hypot(m[2], m[3])) or 1.0


def transform_of(attr):
    """transform="translate(10,20) rotate(45) scale(2)" -> one matrix."""
    m = IDENTITY
    for name, inner in re.findall(r"(\w+)\s*\(([^)]*)\)", attr or ""):
        v = [float(t) for t in re.findall(NUM, inner)]
        if name == "matrix" and len(v) == 6:
            op = tuple(v)
        elif name == "translate":
            op = (1.0, 0.0, 0.0, 1.0, v[0], v[1] if len(v) > 1 else 0.0)
        elif name == "scale":
            sx = v[0]
            op = (sx, 0.0, 0.0, v[1] if len(v) > 1 else sx, 0.0, 0.0)
        elif name == "rotate":
            ang = math.radians(v[0])
            cos, sin = math.cos(ang), math.sin(ang)
            op = (cos, sin, -sin, cos, 0.0, 0.0)
            if len(v) > 2:  # rotate(deg cx cy) is translate(cx,cy) rotate(deg) translate(-cx,-cy)
                cx, cy = v[1], v[2]
                op = mul(mul((1, 0, 0, 1, cx, cy), op), (1, 0, 0, 1, -cx, -cy))
        elif name == "skewX":
            op = (1.0, 0.0, math.tan(math.radians(v[0])), 1.0, 0.0, 0.0)
        elif name == "skewY":
            op = (1.0, math.tan(math.radians(v[0])), 0.0, 1.0, 0.0, 0.0)
        else:
            continue
        m = mul(m, op)
    return m


# ---------------------------------------------------------------- curves

def deviating(x0, y0, c1x, c1y, c2x, c2y, x1, y1):
    """How far the two control points sit from the chord, which bounds how far the curve does."""
    dx, dy = x1 - x0, y1 - y0
    ln = math.hypot(dx, dy)
    if ln < 1e-12:
        return max(math.hypot(c1x - x0, c1y - y0), math.hypot(c2x - x0, c2y - y0))
    return max(abs((c1x - x0) * dy - (c1y - y0) * dx), abs((c2x - x0) * dy - (c2y - y0) * dx)) / ln


def cubic_points(x0, y0, c1x, c1y, c2x, c2y, x1, y1, tol, out, depth=0):
    """Chords of a cubic bezier: split until both control points sit within tol of the chord."""
    if depth >= 14 or deviating(x0, y0, c1x, c1y, c2x, c2y, x1, y1) <= tol:
        out.append((x1, y1))
        return
    ax, ay = (x0 + c1x) / 2.0, (y0 + c1y) / 2.0
    bx, by = (c1x + c2x) / 2.0, (c1y + c2y) / 2.0
    cx, cy = (c2x + x1) / 2.0, (c2y + y1) / 2.0
    dx1, dy1 = (ax + bx) / 2.0, (ay + by) / 2.0
    ex, ey = (bx + cx) / 2.0, (by + cy) / 2.0
    mx, my = (dx1 + ex) / 2.0, (dy1 + ey) / 2.0
    cubic_points(x0, y0, ax, ay, dx1, dy1, mx, my, tol, out, depth + 1)
    cubic_points(mx, my, ex, ey, cx, cy, x1, y1, tol, out, depth + 1)


def quad_points(x0, y0, qx, qy, x1, y1, tol, out, depth=0):
    """A quadratic is a cubic with its controls two thirds of the way to the shared control point."""
    cubic_points(x0, y0, x0 + 2.0 * (qx - x0) / 3.0, y0 + 2.0 * (qy - y0) / 3.0,
                 x1 + 2.0 * (qx - x1) / 3.0, y1 + 2.0 * (qy - y1) / 3.0, x1, y1, tol, out, depth)


def arc_centre(x0, y0, rx, ry, phi_deg, large, sweep, x1, y1):
    """Endpoint parameters -> centre parameters (the F.6 conversion in the SVG specification)."""
    if (x0, y0) == (x1, y1) or rx == 0.0 or ry == 0.0:
        return None  # the specification: a degenerate arc is a straight line
    rx, ry = abs(rx), abs(ry)
    phi = math.radians(phi_deg)
    cos, sin = math.cos(phi), math.sin(phi)
    dx, dy = (x0 - x1) / 2.0, (y0 - y1) / 2.0
    x1p, y1p = cos * dx + sin * dy, -sin * dx + cos * dy
    lam = (x1p / rx) ** 2 + (y1p / ry) ** 2
    if lam > 1.0:  # the radii were too small to reach, so scale them up as the specification says
        rx, ry = rx * math.sqrt(lam), ry * math.sqrt(lam)
    num = rx * rx * ry * ry - rx * rx * y1p * y1p - ry * ry * x1p * x1p
    den = rx * rx * y1p * y1p + ry * ry * x1p * x1p
    co = (-1.0 if bool(large) == bool(sweep) else 1.0) * math.sqrt(max(0.0, num / den)) if den else 0.0
    cxp, cyp = co * rx * y1p / ry, -co * ry * x1p / rx
    ux, uy = (x1p - cxp) / rx, (y1p - cyp) / ry
    vx, vy = (-x1p - cxp) / rx, (-y1p - cyp) / ry

    def angle(ux_, uy_, vx_, vy_):
        nu, nv = math.hypot(ux_, uy_), math.hypot(vx_, vy_)
        if nu == 0.0 or nv == 0.0:
            return 0.0
        a = math.acos(max(-1.0, min(1.0, (ux_ * vx_ + uy_ * vy_) / (nu * nv))))
        return -a if ux_ * vy_ - uy_ * vx_ < 0.0 else a

    th1 = angle(1.0, 0.0, ux, uy)
    dth = angle(ux, uy, vx, vy) % (2.0 * math.pi)
    if not sweep:
        dth -= 2.0 * math.pi
    return (cxp * cos - cyp * sin + (x0 + x1) / 2.0, cxp * sin + cyp * cos + (y0 + y1) / 2.0,
            th1, dth, rx, ry, phi)


def arc_points(x0, y0, rx, ry, phi_deg, large, sweep, x1, y1, tol, out):
    c = arc_centre(x0, y0, rx, ry, phi_deg, large, sweep, x1, y1)
    if c is None:
        out.append((x1, y1))
        return
    cx, cy, th1, dth, rx, ry, phi = c
    r = max(rx, ry)
    step = 2.0 * math.acos(max(-1.0, min(1.0, 1.0 - max(1e-12, tol) / r))) if tol < r else math.pi
    chords = max(1, min(8192, int(math.ceil(abs(dth) / max(1e-9, step)))))
    cos, sin = math.cos(phi), math.sin(phi)
    for k in range(1, chords + 1):
        t = th1 + dth * k / chords
        out.append((cx + cos * rx * math.cos(t) - sin * ry * math.sin(t),
                    cy + sin * rx * math.cos(t) + cos * ry * math.sin(t)))
    out[-1] = (x1, y1)  # land exactly on the point the file asked for


def arc_box(x0, y0, rx, ry, phi_deg, large, sweep, x1, y1):
    """The endpoints of the arc plus the x/y extremes it actually reaches."""
    c = arc_centre(x0, y0, rx, ry, phi_deg, large, sweep, x1, y1)
    if c is None:
        return [(x0, y0), (x1, y1)]
    cx, cy, th1, dth, rx, ry, phi = c
    cos, sin = math.cos(phi), math.sin(phi)
    tau = 2.0 * math.pi
    eps = 1e-12

    def point(t):
        ct, st = math.cos(t), math.sin(t)
        return (cx + cos * rx * ct - sin * ry * st, cy + sin * rx * ct + cos * ry * st)

    ax = math.atan2(-ry * sin, rx * cos)
    ay = math.atan2(ry * cos, rx * sin)
    pts = [(x0, y0), (x1, y1)]
    if abs(dth) >= tau - eps:
        for a in (ax, ay):
            pts.extend([point(a), point(a + math.pi)])
        return pts

    def in_arc(t):
        if dth >= 0.0:
            return ((t - th1) % tau) <= dth + eps
        return ((th1 - t) % tau) <= -dth + eps

    for t in (ax, ax + math.pi, ay, ay + math.pi):
        if in_arc(t):
            pts.append(point(t))
    return pts


def dist_pt_seg(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    ln2 = dx * dx + dy * dy
    if ln2 == 0.0:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / ln2))
    return math.hypot(p[0] - (a[0] + t * dx), p[1] - (a[1] + t * dy))


def _simplify_range(pts, xs, ys, tol, i0, i1):
    n = i1 - i0 + 1
    if n < 3:
        return list(pts[i0:i1 + 1])
    if math.hypot(xs[i0] - xs[i1], ys[i0] - ys[i1]) <= 1e-9:
        return _simplify_range(pts, xs, ys, tol, i0, i1 - 1) + [pts[i0]]

    tol2 = tol * tol
    keep = [False] * n
    keep[0] = keep[n - 1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        k0 = i0 + i
        k1 = i0 + j
        x0, y0 = xs[k0], ys[k0]
        x1, y1 = xs[k1], ys[k1]
        dx, dy = x1 - x0, y1 - y0
        ln2 = dx * dx + dy * dy
        best, worst2 = -1, tol2
        if ln2 == 0.0:
            for k in range(i + 1, j):
                px = xs[i0 + k] - x0
                py = ys[i0 + k] - y0
                d2 = px * px + py * py
                if d2 > worst2:
                    best, worst2 = k, d2
        else:
            for k in range(i + 1, j):
                px, py = xs[i0 + k], ys[i0 + k]
                t = ((px - x0) * dx + (py - y0) * dy) / ln2
                if t < 0.0:
                    dxp, dyp = px - x0, py - y0
                elif t > 1.0:
                    dxp, dyp = px - x1, py - y1
                else:
                    dxp, dyp = px - (x0 + t * dx), py - (y0 + t * dy)
                d2 = dxp * dxp + dyp * dyp
                if d2 > worst2:
                    best, worst2 = k, d2
        if best >= 0:
            keep[best] = True
            stack.append((i, best))
            stack.append((best, j))
    return [pts[i0 + k] for k, kept in enumerate(keep) if kept]


def simplify(pts, tol):
    """Douglas-Peucker: drop the points that lie within tol of the line between the points kept.

    Flattening a curve and reading every command anchor of the file both leave far more points behind
    than the laser can be told about, and most of them are not corners: skipping one that is only
    barely off the straight line between its neighbours costs less than the accuracy asked for.
    """
    if len(pts) < 3:
        return list(pts)
    return _simplify_range(pts, [p[0] for p in pts], [p[1] for p in pts], tol, 0, len(pts) - 1)


# ---------------------------------------------------------------- the file

def parse_path(d):
    """A d attribute -> subpaths of items, in the file's own coordinates, command letter as written."""
    toks = re.findall(r"[A-Za-z]|" + NUM, d or "")
    subs, cur, i = [], [], 0
    cmd = "Z"
    while i < len(toks):
        if toks[i].isalpha():
            cmd = toks[i]
            i += 1
        else:
            nxt = FOLLOW[cmd.upper()]
            cmd = nxt.lower() if cmd.islower() else nxt  # coordinate sets with no command letter repeat it
        want = COUNTS[cmd.upper()]
        args = []
        for _ in range(want):
            if i < len(toks) and not toks[i].isalpha():
                args.append(float(toks[i]))
                i += 1
        args += [0.0] * (want - len(args))  # a truncated command is padded rather than crashing
        key = cmd.upper()
        if key == "M":
            cur = [(cmd, args[0], args[1])]
            subs.append(cur)
            cmd = "l" if cmd == "m" else "L"  # further pairs after a moveto are linetos, same direction
            continue
        if key == "Z":
            if cur:
                cur.append((cmd,))
            cmd = "L"
            continue
        if not cur:
            cur = [("M", 0.0, 0.0)]
            subs.append(cur)
        cur.append((cmd, *args))
        nxt = FOLLOW[key]
        cmd = nxt.lower() if cmd.islower() else nxt  # a repeated command keeps its relative or absolute form
    return [s for s in subs if len(s) > 1]


def flatten(sub, tol):
    """One subpath of items -> the polyline the laser will actually follow."""
    pts, x, y = [], 0.0, 0.0
    start = None
    ctrl = None
    for it in sub:
        key = it[0]
        rel = False  # items carry the command letter as written; relative ones are resolved here
        if key.islower():
            rel = True
        if key.upper() == "M":
            x, y = (x + it[1], y + it[2]) if rel else (it[1], it[2])
            pts.append((x, y))
            start, ctrl = (x, y), None
        elif key.upper() == "L":
            x, y = (x + it[1], y + it[2]) if rel else (it[1], it[2])
            pts.append((x, y))
            ctrl = None
        elif key.upper() == "H":
            x = x + it[1] if rel else it[1]
            pts.append((x, y))
            ctrl = None
        elif key.upper() == "V":
            y = y + it[1] if rel else it[1]
            pts.append((x, y))
            ctrl = None
        elif key.upper() == "C":
            n = [(x + it[k], y + it[k + 1]) if rel else (it[k], it[k + 1]) for k in (1, 3, 5)]
            cubic_points(x, y, n[0][0], n[0][1], n[1][0], n[1][1], n[2][0], n[2][1], tol, pts)
            x, y = n[2]
            ctrl = n[1]
        elif key.upper() == "S":
            c1 = (2 * x - ctrl[0], 2 * y - ctrl[1]) if ctrl else (x, y)
            n = [(x + it[k], y + it[k + 1]) if rel else (it[k], it[k + 1]) for k in (1, 3)]
            cubic_points(x, y, c1[0], c1[1], n[0][0], n[0][1], n[1][0], n[1][1], tol, pts)
            x, y = n[1]
            ctrl = n[0]
        elif key.upper() == "Q":
            n = [(x + it[k], y + it[k + 1]) if rel else (it[k], it[k + 1]) for k in (1, 3)]
            quad_points(x, y, n[0][0], n[0][1], n[1][0], n[1][1], tol, pts)
            x, y = n[1]
            ctrl = n[0]
        elif key.upper() == "T":
            c1 = (2 * x - ctrl[0], 2 * y - ctrl[1]) if ctrl else (x, y)
            n = (x + it[1], y + it[2]) if rel else (it[1], it[2])
            quad_points(x, y, c1[0], c1[1], n[0], n[1], tol, pts)
            x, y = n
            ctrl = c1
        elif key.upper() == "A":
            rx, ry, rot, large, sweep = it[1], it[2], it[3], it[4], it[5]
            n = (x + it[6], y + it[7]) if rel else (it[6], it[7])
            arc_points(x, y, rx, ry, rot, large, sweep, n[0], n[1], tol, pts)
            x, y = n
            ctrl = None
        elif key.upper() == "Z" and start and (x, y) != start:
            pts.append(start)
            x, y = start
            ctrl = None
    return pts


def item_bounds(sub):
    """A conservative box for a subpath without flattening it: curve hulls and exact arc boxes."""
    out, x, y = [], 0.0, 0.0
    for it in sub:
        key = it[0].upper()
        rel = it[0].islower()
        if key in ("M", "L"):
            x, y = (x + it[1], y + it[2]) if rel else (it[1], it[2])
            out.append((x, y))
        elif key == "H":
            x = x + it[1] if rel else it[1]
            out.append((x, y))
        elif key == "V":
            y = y + it[1] if rel else it[1]
            out.append((x, y))
        elif key == "C":
            n = [(x + it[k], y + it[k + 1]) if rel else (it[k], it[k + 1]) for k in (1, 3, 5)]
            out.extend(n)
            x, y = n[2]
        elif key == "S":
            n = [(x + it[k], y + it[k + 1]) if rel else (it[k], it[k + 1]) for k in (1, 3)]
            out.extend(n)
            x, y = n[1]
        elif key == "Q":
            n = [(x + it[k], y + it[k + 1]) if rel else (it[k], it[k + 1]) for k in (1, 3)]
            out.extend(n)
            x, y = n[1]
        elif key == "T":
            x, y = (x + it[1], y + it[2]) if rel else (it[1], it[2])
            out.append((x, y))
        elif key == "A":
            sx, sy = x, y
            x, y = (x + it[6], y + it[7]) if rel else (it[6], it[7])
            out.extend(arc_box(sx, sy, it[1], it[2], it[3], it[4], it[5], x, y))
    return out


def apply_all(ctm, pts):
    """One element's transform, applied to a whole polyline."""
    return [apply(ctm, x, y) for x, y in pts]


def num_at(at, key, default=0.0):
    """A numeric attribute, tolerant of the unit suffixes SVG allows (10mm, 100%, -3.5px)."""
    found = re.search(NUM, at.get(key) or "")
    return float(found.group(0)) if found else default


def shape_items(tag, at):
    """The geometry of one element as subpaths of items, in its own coordinates."""
    f = lambda k, d=0.0: num_at(at, k, d)  # noqa: E731  a numeric attribute
    if tag == "path":
        return parse_path(at.get("d", ""))
    if tag == "line":
        return [[("M", f("x1"), f("y1")), ("L", f("x2"), f("y2"))]]
    if tag in ("polyline", "polygon"):
        v = [float(t) for t in re.findall(NUM, at.get("points", ""))]
        pts = list(zip(v[0::2], v[1::2]))
        if len(pts) < 2:
            return []
        sub = [("M", pts[0][0], pts[0][1])] + [("L", x, y) for x, y in pts[1:]]
        if tag == "polygon":
            sub.append(("Z",))
        return [sub]
    if tag == "rect":
        x0, y0, w, h = f("x"), f("y"), f("width"), f("height")
        if w <= 0.0 or h <= 0.0:
            return []
        return [[("M", x0, y0), ("L", x0 + w, y0), ("L", x0 + w, y0 + h), ("L", x0, y0 + h), ("Z",)]]
    if tag in ("circle", "ellipse"):
        cx, cy = f("cx"), f("cy")
        rx = f("r") if tag == "circle" else f("rx")
        ry = rx if tag == "circle" else f("ry")
        if rx <= 0.0 or ry <= 0.0:
            return []
        return [[("M", cx + rx, cy), ("A", rx, ry, 0.0, 0, 1, cx - rx, cy),
                 ("A", rx, ry, 0.0, 0, 1, cx + rx, cy), ("Z",)]]
    return []


def tag_of(elem):
    return elem.tag.split("}")[-1]


def style_of(elem, inherited):
    st = dict(inherited)
    for key in STYLE_KEYS:
        if key in elem.attrib:
            st[key] = elem.attrib[key]
    for part in (elem.attrib.get("style") or "").split(";"):
        if ":" in part:
            key, value = part.split(":", 1)
            if key.strip() in STYLE_KEYS:
                st[key.strip()] = value.strip()
    return st


def collect(root, limit=8):
    """Walk the tree and return (ctm, items) for every drawable shape, plus what was skipped."""
    shapes, skipped = [], collections.Counter()
    defs = {e.get("id"): e for e in root.iter() if e.get("id")}

    def go(elem, ctm, style, depth):
        tag = tag_of(elem)
        if tag in SKIP_TAGS:
            skipped[tag] += 1
            return
        local = mul(ctm, transform_of(elem.get("transform")))
        st = style_of(elem, style)
        if st.get("display") == "none" or st.get("visibility") == "hidden":
            return
        if tag == "use":
            href = (elem.get("{http://www.w3.org/1999/xlink}href") or elem.get("href") or "").lstrip("#")
            target = defs.get(href)
            if target is None or depth >= limit:
                skipped["use"] += 1
                return
            off = mul(local, (1.0, 0.0, 0.0, 1.0, num_at(elem.attrib, "x"), num_at(elem.attrib, "y")))
            go(target, off, st, depth + 1)
            return
        if tag in ("g", "svg", "a"):
            for child in elem:
                go(child, local, st, depth)
            return
        items = shape_items(tag, elem.attrib)
        if not items:
            skipped[tag] += 1
            return
        shapes.append((local, items, st))

    go(root, IDENTITY, {}, 0)
    return shapes, skipped


def stroked(elem_style):
    s = (elem_style.get("stroke") or "").strip().lower()
    return s not in ("", "none")


def orientation_of(a):
    """The shared orientation, with this script's older --no-flip-x / --no-flip-y spellings taken back
    into it: both of them mean "do not mirror that axis"."""
    o = laser_field.orientation(a)
    if a.no_flip_x:
        o["invert_x"] = False
    if a.no_flip_y:
        o["invert_y"] = False
    return o


def field_mapper(orient, mid_x, mid_y, k):
    """SVG user coordinates -> field units.

    First the picture: SVG's y axis points down, a viewer's does not, so a user point (px, py) is the
    viewer's (px - mid_x, mid_y - py). Then the shared orientation of laser_field.py, then the scale - and
    the scale is a positive number, so it commutes with all of it.
    """
    def to_field(px, py):
        return tuple(v * k for v in laser_field.map_point(orient, px - mid_x, mid_y - py))
    return to_field


# ---------------------------------------------------------------- main

def main():
    a = parse_args()
    if a.speed <= 0.0 or a.scale <= 0.0:
        print("--speed and --scale have to be above 0")
        return 2
    try:
        root = ET.parse(a.file).getroot()
    except (OSError, ET.ParseError) as e:
        print(f"cannot read {a.file}: {e}")
        return 2

    shapes, skipped = collect(root)
    keep = [s for s in shapes if not a.only_stroke or stroked(s[2])]
    if not keep:
        print(f"{a.file}: nothing to trace" + (" - no shape there says it is stroked" if a.only_stroke else ""))
        return 2

    # A conservative box first (curve hulls, exact arc boxes), because the accuracy is stated in
    # field units and the tolerance a curve is flattened with has to be derived from it.
    lo_x = lo_y = float("inf")
    hi_x = hi_y = float("-inf")
    for ctm, subs, _st in keep:
        for sub in subs:
            for x, y in item_bounds(sub):
                x, y = apply(ctm, x, y)
                lo_x, hi_x = min(lo_x, x), max(hi_x, x)
                lo_y, hi_y = min(lo_y, y), max(hi_y, y)
    if not (hi_x > lo_x and hi_y > lo_y):
        print(f"{a.file}: every shape there is a point")
        return 2

    mid_x, mid_y = (lo_x + hi_x) / 2.0, (lo_y + hi_y) / 2.0
    span = max(hi_x - lo_x, hi_y - lo_y)
    k = 2.0 / span * a.scale
    wide, high = (hi_x - lo_x) * k, (hi_y - lo_y) * k
    if max(abs(wide), abs(high)) > 2.0:
        clamp = 2.0 / max(abs(wide), abs(high))
        print(f"a {wide:.2f} x {high:.2f} u drawing does not fit the field (2.00 x 2.00), drawing at "
              f"{wide * clamp:.2f} x {high * clamp:.2f} u instead")
        k *= clamp
    # The picture is (x - middle, middle - y): SVG's own y axis points down, a viewer's does not. From there
    # the shared orientation of scripts/laser_field.py decides what leaves as field units - on this bench
    # that is x as the picture has it and y mirrored, which is what the mouse showed the mount to need.
    # --no-invert-x / --no-invert-y (and the older --no-flip-x / --no-flip-y) undo one axis each;
    # --raw-field sends the viewer coordinates with nothing applied at all.
    orient_to = orientation_of(a)
    to_field = field_mapper(orient_to, mid_x, mid_y, k)

    # The accuracy budget is spent in two places: flattening a curve into chords may use half of it, and
    # dropping points a straight line already covers may use the other half.
    tol = max(1e-9, a.accuracy) / 2.0 / k
    subs_out, flattened, kept_pts, too_small = [], 0, 0, 0
    for ctm, subs, _st in keep:
        local_tol = tol / stretch_of(ctm)
        for sub in subs:
            pts = [to_field(*p) for p in apply_all(ctm, flatten(sub, local_tol))]
            flattened += len(pts)
            if not a.no_simplify:
                pts = simplify(pts, max(1e-9, a.accuracy) / 2.0)
            kept_pts += len(pts)
            if len(pts) > 1 and any(math.hypot(b[0] - c[0], b[1] - c[1]) > 1e-12 for b, c in zip(pts, pts[1:])):
                subs_out.append(pts)
            else:
                too_small += 1
    if not subs_out:
        print(f"{a.file}: nothing left after dropping zero length subpaths")
        return 2

    # The laser state belongs to the move arriving at a point: the first point of a subpath is reached
    # with the laser off, everything after it is drawn, and the walk back to the start closes the cycle.
    cycle = []
    for pts in subs_out:
        for j, (x, y) in enumerate(pts):
            cycle.append((x, y, 0.0 if j == 0 else 1.0))
    cycle.append((cycle[0][0], cycle[0][1], 0.0))

    dt_min = 1.0 / max(1, a.updates)
    p = plan(cycle, False, a.speed, dt_min, a.accuracy, max(1e-9, a.max_step), a.retrace, None)
    ext_x = max(abs(pt[0]) for pt in cycle)
    ext_y = max(abs(pt[1]) for pt in cycle)
    note = ", ".join(f"{t} {n}" for t, n in sorted(skipped.items())) or "nothing"
    print(f"file {a.file}  shapes {len(keep)}  subpaths {len(subs_out)}  traced {flattened} points, "
          f"{kept_pts} kept as corners and curves" + (" (no simplification)" if a.no_simplify else "") +
          (f"  {too_small} subpath(s) smaller than --accuracy dropped" if too_small else ""))
    print(f"skipped elements: {note}")
    flips_note = laser_field.describe(orient_to)
    print(f"drawing {hi_x - lo_x:.3f} x {hi_y - lo_y:.3f} user units -> {2.0 * ext_x:.2f} x "
          f"{2.0 * ext_y:.2f} field u (--scale {a.scale:g})")
    print(flips_note)
    print(f"socket {a.socket}  speed {a.speed} field u/s  node pickup {a.updates}/s "
          f"(dt_min {dt_min * 1000:.3f} ms, one step is {a.speed * dt_min:.4f} u, "
          f"straight limit {a.max_step} u)")
    print(f"cycle {p['path']:.2f} u drawn+blank ({p['drawn']:.2f} drawn, {p['blank']:.2f} blank walked at "
          f"{a.retrace:g}x)  {p['points']} points  {p['cycle_time']:.3f} s  "
          f"{1.0 / p['cycle_time']:.2f} cycles/s  {p['drawn_speed']:.1f} u/s over the drawn part")
    if p["drawn_speed"] < 0.9 * a.speed:
        drawn_pts = sum(n for _x0, _y0, _x1, _y1, laser, n, _dt in p["segs"] if laser)
        detail = p["drawn"] / max(1, drawn_pts)
        print(f"      note: this drawing tops out at {p['drawn_speed']:.0f} u/s, not {a.speed} u/s. "
              f"{a.speed} u/s would need {a.speed * dt_min:.4f} u per update, --max-step allows "
              f"{a.max_step:.4f} u, and the {drawn_pts} points this drawing needs on {p['drawn']:.2f} u "
              f"are {detail:.4f} u apart ({detail * a.updates:.0f} u/s). Raise --max-step, loosen "
              f"--accuracy, add --updates, or lower --speed.")

    if a.plan_only:
        return 0

    try:
        node = Node(a.socket)
    except OSError as e:
        print(f"cannot connect to {a.socket}: {e}")
        print("start the node first:  systemctl --user start laser-node   (or ./scripts/deploy.sh run)")
        return 1

    print("tracing: " + ("endless (Ctrl+C to stop)" if a.endless else f"{a.duration}s"))
    try:
        started = time.monotonic()
        deadline = None if a.endless else started + a.duration
        cycles = sent = 0
        next_report = started + 1.0
        while deadline is None or time.monotonic() < deadline:
            t = time.monotonic()  # one absolute schedule per cycle: sleeps do not drift across it
            try:
                for x, y, laser, dt in walk(p["segs"]):
                    node.set(x, y, laser)
                    sent += 1
                    if dt:
                        t += dt
                        now = time.monotonic()
                        if t > now:
                            time.sleep(t - now)
                        else:
                            t = now  # we fell behind; do not burst back up to the schedule
            except OSError as e:
                print(f"the node closed the socket: {e}")
                break
            cycles += 1
            if a.endless and time.monotonic() >= next_report:
                el = time.monotonic() - started
                print(f"      {cycles} cycles, {cycles / el:5.2f} cycles/s, {sent / el:6.0f} points/s, "
                      f"{cycles * p['path'] / el:6.1f} u/s over the cycle")
                next_report = time.monotonic() + 1.0
        el = time.monotonic() - started
        print(f"      {cycles} cycles in {el:5.2f}s = {cycles / el:5.2f} cycles/s, {sent / el:6.0f} "
              f"points/s, {cycles * p['path'] / el:6.1f} u/s over the cycle")
    except KeyboardInterrupt:
        print("stopped")
    finally:
        try:
            node.set(0.0, 0.0, 0.0)  # always end parked in the middle with the laser off
        except OSError:
            pass
        node.f.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
