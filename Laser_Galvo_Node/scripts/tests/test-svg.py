#!/usr/bin/env python3
"""Checks for scripts/svg.py: the path reader, the curve flattening, the transforms, the simplifying.

    python3 scripts/tests/test-svg.py

Each check compares what the reader produced against something known independently: how far a chord
sits from the bezier it approximates, the radius and sweep angle an arc's flags ask for, where a
transform puts a point, which elements are skipped. The last group parses a .svg file from the project
root when one is there, and only asks that it parses.
"""

import glob
import importlib.util
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
spec = importlib.util.spec_from_file_location("svgtr", os.path.join(ROOT, "svg.py"))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

TOL = 1e-4


def flat(d, tol=TOL):
    return [s.flatten(sub, tol) for sub in s.parse_path(d)]


def dist_pt_seg(p, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    ln2 = dx * dx + dy * dy
    if ln2 == 0:
        return math.hypot(p[0] - ax, p[1] - ay)
    t = max(0.0, min(1.0, ((p[0] - ax) * dx + (p[1] - ay) * dy) / ln2))
    return math.hypot(p[0] - (ax + t * dx), p[1] - (ay + t * dy))


def dev_from_polyline(curve_pts, poly):
    return max(min(dist_pt_seg(p, poly[i], poly[i + 1]) for i in range(len(poly) - 1)) for p in curve_pts)


def bez(a, c1, c2, b, t):
    u = 1 - t
    return (u ** 3 * a[0] + 3 * u * u * t * c1[0] + 3 * u * t * t * c2[0] + t ** 3 * b[0],
            u ** 3 * a[1] + 3 * u * u * t * c1[1] + 3 * u * t * t * c2[1] + t ** 3 * b[1])


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return (min(xs), min(ys), max(xs), max(ys))


def box_contains(a, b, eps=1e-6):
    ax0, ay0, ax1, ay1 = bbox(a)
    bx0, by0, bx1, by1 = bbox(b)
    return ax0 <= bx0 + eps and ay0 <= by0 + eps and ax1 >= bx1 - eps and ay1 >= by1 - eps


def near_bbox(a, b, eps=1e-6):
    return all(abs(x - y) <= eps for x, y in zip(a, b))


fails = []


def num_at_check():
    at = {"x": "10mm", "y": "-3.5px", "width": "100%", "height": "", "cx": "1e2"}
    got = [s.num_at(at, k) for k in ("x", "y", "width", "height", "cx")]
    ok = got == [10.0, -3.5, 100.0, 0.0, 100.0]
    rect = s.flatten(s.shape_items("rect", {"x": "0mm", "y": "0mm", "width": "10mm", "height": "5mm"})[0], 0.01)
    check("10mm x 5mm rect", ok and rect == [(0, 0), (10, 0), (10, 5), (0, 5), (0, 0)], f"{got} {rect}")
    return True


def check(name, ok, detail=""):
    print(f"{'ok  ' if ok else 'FAIL'} {name} {detail}")
    if not ok:
        fails.append(name)


def quad_as_cubic(p0, q, p1):
    return (p0[0] + 2.0 * (q[0] - p0[0]) / 3.0, p0[1] + 2.0 * (q[1] - p0[1]) / 3.0), \
           (p1[0] + 2.0 * (q[0] - p1[0]) / 3.0, p1[1] + 2.0 * (q[1] - p1[1]) / 3.0)


# --- 1. beziers
poly = flat("M0,0 C10,0 10,10 0,10")[0]
true = [bez((0, 0), (10, 0), (10, 10), (0, 10), i / 400) for i in range(401)]
check("cubic fidelity", dev_from_polyline(true, poly) <= TOL * 1.5, f"max dev {dev_from_polyline(true, poly):.6f}")
check("relative cubic == absolute", flat("M0,0 c10,0 10,10 0,10")[0] == poly)
check("S continues the control", flat("M0,0 C0,0 10,0 10,10 S20,20 20,10")[0] ==
      flat("M0,0 C0,0 10,0 10,10 C10,20 20,20 20,10")[0])
qp = flat("M0,0 Q10,0 10,10")[0]
c1, c2 = quad_as_cubic((0, 0), (10, 0), (10, 10))
qtrue = [bez((0, 0), c1, c2, (10, 10), i / 400) for i in range(401)]
check("quadratic fidelity", dev_from_polyline(qtrue, qp) <= TOL * 1.5, f"max dev {dev_from_polyline(qtrue, qp):.6f}")
check("T mirrors the control", flat("M0,0 Q10,0 10,10 T20,20") == flat("M0,0 Q10,0 10,10 Q10,20 20,20"))
check("tighter accuracy gives more chords",
      len(flat("M0,0 C10,0 10,10 0,10", 1e-2)[0]) < len(poly) < len(flat("M0,0 C10,0 10,10 0,10", 1e-6)[0]),
      f"{len(flat('M0,0 C10,0 10,10 0,10', 1e-2)[0])} / {len(poly)}")

# --- 2. arcs: every point on the ellipse the arc belongs to, endpoints exact, flags honoured
def on_ellipse(d, tol=TOL):
    p = flat(d)[0]
    it = s.parse_path(d)[0][1]
    cx, cy, th1, dth, rx, ry, phi = s.arc_centre(0, 0, it[1], it[2], it[3], it[4], it[5], it[6], it[7]) \
        if False else s.arc_centre(p[0][0], p[0][1], it[1], it[2], it[3], it[4], it[5], it[6], it[7])
    cos, sin = math.cos(phi), math.sin(phi)
    worst = 0.0
    for x, y in p:
        u = ((x - cx) * cos + (y - cy) * sin) / rx
        v = (-(x - cx) * sin + (y - cy) * cos) / ry
        worst = max(worst, abs(math.hypot(u, v) - 1.0))
    swept = abs(dth)
    return p, worst, swept


for d, want_sweep in (("M10,0 A10,10 0 0 0 0,10", math.pi / 2), ("M10,0 A10,10 0 0 1 0,10", math.pi / 2),
                      ("M10,0 A10,10 0 1 0 0,10", 3 * math.pi / 2), ("M10,0 A10,10 0 1 1 0,10", 3 * math.pi / 2),
                      ("M20,0 A20,10 30 0 1 -20,0", math.pi), ("M20,0 A20,10 30 1 1 -20,0", math.pi)):
    p, err, swept = on_ellipse(d)
    check(f"arc {d.split('A')[1]}", err <= TOL * 1.5 and abs(swept - want_sweep) < 1e-9 and p[-1] == flat(d)[0][-1],
          f"on-ellipse err {err:.2e}, sweep {math.degrees(swept):.1f} deg, {len(p)} chords")
p, err, swept = on_ellipse("M0,20 A20,20 0 0 1 0,-20")
check("half circle the short way", abs(swept - math.pi) < 1e-9 and err <= TOL * 1.5,
      f"{math.degrees(swept):.1f} deg, {len(p)} chords")
check("sweep 0 and 1 are the two different arcs",
      flat("M10,0 A10,10 0 0 1 0,10")[0] != flat("M10,0 A10,10 0 0 0 0,10")[0])
check("radii too small are scaled up to reach", on_ellipse("M5,0 A1,1 0 0 1 0,5")[0][-1] == (0.0, 5.0),
      f"{on_ellipse('M5,0 A1,1 0 0 1 0,5')[0][-1]}")
check("degenerate arc is a straight line", flat("M0,0 A0,0 0 0 0 5,5")[0] == [(0, 0), (5, 5)])
check("zero length arc stays put", flat("M5,5 A10,10 0 0 1 5,5")[0] == [(5, 5), (5, 5)])

# --- 2b. arc bounds: the box covers the arc's own extremes, not the whole ellipse's corners
ARC_BOX_CHECKS = (
    "M10,0 A10,10 0 0 0 0,10",
    "M10,0 A10,10 0 0 1 0,10",
    "M10,0 A10,10 0 1 0 0,10",
    "M10,0 A10,10 0 1 1 0,10",
    "M20,0 A20,10 30 0 1 -20,0",
    "M20,0 A20,10 30 1 1 -20,0",
    "M0,20 A20,20 0 0 1 0,-20",
    "M5,0 A1,1 0 0 1 0,5",
)
for d in ARC_BOX_CHECKS:
    sub = s.parse_path(d)[0]
    it = sub[1]
    got = s.arc_box(sub[0][1], sub[0][2], it[1], it[2], it[3], it[4], it[5], it[6], it[7])
    poly = s.flatten(sub, TOL)
    b, f = bbox(got), bbox(poly)
    tight = (b[2] - b[0] - (f[2] - f[0]) <= 1e-3 and b[3] - b[1] - (f[3] - f[1]) <= 1e-3)
    check(f"arc box {d.split('A')[1]}", box_contains(got, poly, 1e-3) and tight, f"box {b} flat {f}")
quarter = s.item_bounds(s.parse_path("M10,0 A10,10 0 0 1 0,10")[0])
check("item_bounds uses the arc, not the whole ellipse", near_bbox(bbox(quarter), (0.0, 0.0, 10.0, 10.0), 1e-9),
      f"{bbox(quarter)}")

# --- 3. straight-line grammar
check("h/v/z square", flat("M0,0 h10 v10 h-10 z") == [[(0, 0), (10, 0), (10, 10), (0, 10), (0, 0)]])
check("implicit lineto after M", flat("M0,0 5,5 10,0") == [[(0, 0), (5, 5), (10, 0)]])
check("implicit repeat of c and l", flat("M0,0 l5,0 l5,0") == flat("M0,0 l5,0 5,0") == [[(0, 0), (5, 0), (10, 0)]])
check("subpaths split at M", flat("M0,0 L10,0 M20,20 L30,20") == [[(0, 0), (10, 0)], [(20, 20), (30, 20)]])
check("truncated command padded not crashing", flat("M0,0 L5 5") == [[(0, 0), (5.0, 5.0)]])
check("numbers glued to a sign", flat("M0,0L10-5") == [[(0, 0), (10.0, -5.0)]])
check("exponential numbers", flat("M0,0L1e2,2E-1") == [[(0, 0), (100.0, 0.2)]])
check("empty d ignored", s.parse_path("") == [])

# --- 4. shapes, transforms, use, skipping
root = s.ET.fromstring(
    """<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink">
      <defs><path id="dot" d="M0,0 L2,0"/></defs>
      <rect x="1" y="2" width="3" height="4"/>
      <line x1="0" y1="0" x2="1" y2="1"/>
      <polyline points="0,0 1,0 1,1"/>
      <polygon points="0,0 1,0 1,1"/>
      <circle cx="0" cy="0" r="1"/>
      <ellipse cx="0" cy="0" rx="2" ry="1"/>
      <g transform="translate(10,20) scale(2)"><use xlink:href="#dot" x="1"/></g>
      <path transform="rotate(90)" d="M1,0 L1,1"/>
      <path transform="matrix(2,0,0,3,1,1)" d="M0,0 L1,1"/>
      <text>hello</text>
    </svg>""")
shapes, skipped = s.collect(root)
got = [[s.apply(ctm, x, y) for x, y in s.flatten(subs[0], 1e-3)] for ctm, subs, st in shapes]
check("rect traced closed", got[0] == [(1, 2), (4, 2), (4, 6), (1, 6), (1, 2)], f"{got[0]}")
check("line traced", got[1] == [(0, 0), (1, 1)])
check("polyline open, polygon closed", got[2] == [(0, 0), (1, 0), (1, 1)] and got[3] == [(0, 0), (1, 0), (1, 1), (0, 0)])
check("circle sampled on its radius", max(abs(math.hypot(x, y) - 1) for x, y in got[4]) < 1e-2)
check("ellipse sampled on its radius", max(abs(math.hypot(x / 2, y) - 1) for x, y in got[5]) < 1e-2)
check("use gets the group transform plus its own x", got[6] == [(12, 20), (16, 20)], f"{got[6]}")
def same(got_pts, want_pts, eps=1e-9):
    return len(got_pts) == len(want_pts) and all(abs(a[0] - b[0]) < eps and abs(a[1] - b[1]) < eps
                                                for a, b in zip(got_pts, want_pts))


check("rotate(90)", same(got[7], [(0.0, 1.0), (-1.0, 1.0)]), f"{got[7]}")
check("matrix(2,0,0,3,1,1)", same(got[8], [(1.0, 1.0), (3.0, 4.0)]), f"{got[8]}")
check("text and defs skipped", skipped.get("text") == 1 and skipped.get("defs") == 1, f"{dict(skipped)}")

# --- 5. style filtering
root2 = s.ET.fromstring(
    """<svg xmlns="http://www.w3.org/2000/svg"><g style="fill:none;stroke:#000">
        <path d="M0,0 L1,1"/><path style="stroke:none" d="M0,0 L2,2"/></g>
      <path d="M0,0 L3,3"/><path style="display:none" d="M0,0 L9,9"/><g display="none"><path d="M0,0"/></g></svg>""")
sh, sk = s.collect(root2)
kept = [x for x in sh if s.stroked(x[2])]
check("stroke inherited from the group", len(sh) == 3 and len(kept) == 1, f"{len(sh)} visible, {len(kept)} stroked")
check("display:none drops the subtree", len(sh) == 3, f"{dict(sk)}")

def check_project_file():
    files = glob.glob(os.path.join(HERE, "..", "..", "*.svg"))
    if not files:
        print("skip  no .svg file in the project root to parse")
        return
    d = files[0]
    root3 = s.ET.parse(d).getroot()
    sh3, sk3 = s.collect(root3)
    flat3 = [[s.apply(ctm, *p) for p in s.flatten(sub, 0.01)] for ctm, subs, st in sh3 for sub in subs]
    npts = sum(len(p) for p in flat3)
    xs = [x for p in flat3 for x, y in p]
    ys = [y for p in flat3 for x, y in p]
    print(f"  {os.path.basename(d)}: shapes {len(sh3)} subpaths {len(flat3)} flattened points {npts} "
          f"user box {max(xs) - min(xs):.2f} x {max(ys) - min(ys):.2f}")
    check(f"{os.path.basename(d)} parsed", len(sh3) >= 1 and len(flat3) >= 1)


# --- 8. attributes that carry a unit suffix
check("unit suffixes on lengths", num_at_check(), "")


check_project_file()

# --- 7. simplification: what a straight line can cover is dropped, what is a corner is not
check("barely off a line is dropped", s.simplify([(0, 0), (5, 0.001), (10, 0)], 0.005) == [(0, 0), (10, 0)])
check("a real corner survives", s.simplify([(0, 0), (5, 1), (10, 0)], 0.005) == [(0, 0), (5, 1), (10, 0)])
check("endpoints always survive", s.simplify([(0, 0), (1, 1), (2, 0)], 10.0) == [(0, 0), (2, 0)])
circle = s.flatten(s.shape_items("circle", {"cx": "0", "cy": "0", "r": "1"})[0], 0.0025)
kept = s.simplify(circle, 0.005)
rad = max(abs(math.hypot(x, y) - 1.0) for x, y in kept)
check("circle simplified to its own accuracy", 20 <= len(kept) <= 80 and rad <= 0.006,
      f"{len(circle)} -> {len(kept)} points, off the radius by {rad:.4f}")
check("no simplification keeps everything", len(s.simplify(circle, 0.0)) == len(circle))
ring = s.flatten(s.shape_items("circle", {"cx": "0", "cy": "0", "r": "1"})[0], 0.0025)
ring_kept = s.simplify(ring, 0.005)
ring_dev = max(min(s.dist_pt_seg(p, ring_kept[i], ring_kept[i + 1]) for i in range(len(ring_kept) - 1))
               for p in ring)
check("closed ring stays closed and inside tol", ring_kept[0] == ring_kept[-1] and ring_dev <= 0.005,
      f"{len(ring)} -> {len(ring_kept)} points, {ring_dev:.4f} off the traced ring")
dense_square = [(x, 0.0) for x in [i / 20 for i in range(21)]] + [(1.0, y) for y in [i / 20 for i in range(1, 21)]] \
    + [(x, 1.0) for x in [1 - i / 20 for i in range(1, 21)]] + [(0.0, y) for y in [1 - i / 20 for i in range(1, 20)]] \
    + [(0.0, 0.0)]
thin = s.simplify(dense_square, 0.001)
check("a densely sampled straight run is thinned", 5 <= len(thin) <= 8 and thin[0] == thin[-1],
      f"{len(dense_square)} -> {len(thin)}")
check("a closed square keeps its corners", s.simplify(s.flatten(
      s.shape_items("rect", {"x": "0", "y": "0", "width": "1", "height": "1"})[0], 0.01), 0.005) ==
      [(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
speck = s.flatten(s.shape_items("rect", {"x": "0", "y": "0", "width": "0.001", "height": "0.001"})[0], 1e-6)
check("a speck collapses", len(s.simplify(speck, 0.005)) <= 3, f"{len(speck)} -> {len(s.simplify(speck, 0.005))}")

print("failures:", fails or "none")
sys.exit(1 if fails else 0)
