"""Geometric stroke engine: letters are centre-lines (straight runs joined by
round corners) given an even weight, then turned into font outlines."""
import math

from shapely import affinity
from shapely.geometry import LinearRing, LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

# ---- vertical metrics (1000 units per em) -------------------------------
UPM = 1000
CAP = 700      # top of capitals
XH = 520       # top of lowercase
ASC = 740      # top of ascenders (b d h k l)
DESC = -210    # bottom of descenders (g j p q y)

# ---- the stroke ----------------------------------------------------------
PEN = {
    "v": 150,    # thickness of vertical strokes
    "h": 124,    # thickness of horizontal strokes
}
LOOK = {
    "bulge": 0.60,   # how full the shoulders of the onion arch are
}


def half():
    return PEN["v"] / 2, PEN["h"] / 2


def rpath(pts, closed=False):
    """Points (x, y) or (x, y, r): a polyline whose corners are rounded with
    radius r. Returns the sampled centre-line."""
    P = [(p[0], p[1], p[2] if len(p) > 2 else 0) for p in pts]
    n = len(P)
    out = []
    for i, (x, y, r) in enumerate(P):
        if r <= 0 or (not closed and i in (0, n - 1)):
            out.append((x, y))
            continue
        ax, ay, _ = P[i - 1]
        cx, cy, _ = P[(i + 1) % n]
        ux, uy = ax - x, ay - y
        vx, vy = cx - x, cy - y
        lu, lv = math.hypot(ux, uy), math.hypot(vx, vy)
        ux, uy, vx, vy = ux / lu, uy / lu, vx / lv, vy / lv
        phi = math.acos(max(-1, min(1, ux * vx + uy * vy)))
        d = min(r / math.tan(phi / 2), lu, lv)
        r = d * math.tan(phi / 2)
        bx, by = ux + vx, uy + vy
        lb = math.hypot(bx, by)
        ox, oy = x + bx / lb * r / math.sin(phi / 2), y + by / lb * r / math.sin(phi / 2)
        a1 = math.atan2(y + uy * d - oy, x + ux * d - ox)
        a2 = math.atan2(y + vy * d - oy, x + vx * d - ox)
        da = (a2 - a1 + math.pi) % (2 * math.pi) - math.pi
        steps = max(6, int(abs(da) / math.radians(1.25)))
        for k in range(steps + 1):
            a = a1 + da * k / steps
            out.append((ox + r * math.cos(a), oy + r * math.sin(a)))
    if closed:
        out.append(out[0])
    return out


def arc(cx, cy, rx, ry, a0, a1):
    """Part of an ellipse, angles in degrees (0 = east, counter-clockwise)."""
    steps = max(8, int(abs(a1 - a0) / 1.25))
    return [(cx + rx * math.cos(math.radians(a0 + (a1 - a0) * k / steps)),
             cy + ry * math.sin(math.radians(a0 + (a1 - a0) * k / steps)))
            for k in range(steps + 1)]


def stroke(pts, closed=False, cap="flat", scale=1.0):
    """Give a centre-line its weight: PEN['v'] wide where it runs vertically,
    PEN['h'] thick where it runs horizontally."""
    hx, hy = half()
    hx, hy = hx * scale, hy * scale
    k = hx / hy
    pts = [(x, y * k) for x, y in pts]
    line = LinearRing(pts) if closed else LineString(pts)
    geo = line.buffer(hx, cap_style=cap, join_style="mitre", mitre_limit=4, quad_segs=48)
    return affinity.scale(geo, 1, 1 / k, origin=(0, 0))


def _bez(p0, p1, p2, p3, n=56):
    out = []
    for k in range(n + 1):
        u = k / n
        v = 1 - u
        out.append((v**3 * p0[0] + 3 * v * v * u * p1[0] + 3 * v * u * u * p2[0] + u**3 * p3[0],
                    v**3 * p0[1] + 3 * v * v * u * p1[1] + 3 * v * u * u * p2[1] + u**3 * p3[1]))
    return out


def _ogee_side(cx, hw, ys, ya, swell=0.0):
    h = ya - ys
    b = LOOK["bulge"]
    return _bez((cx - hw, ys), (cx - hw - swell * hw, ys + b * h), (cx - hw * 0.13, ya - 0.45 * h), (cx, ya))


def window(cx, w, y0, ys, ya, base="open", flip=None, swell=0.0):
    """An onion-arch (ogee) shape: sides rise straight from y0 to the spring
    line ys, swell, then reverse into a point at ya.
    base: 'open' = square foot at y0, 'round' = rounded foot.
    flip = y to mirror the whole shape about (for u- and v-like letters).
    swell > 0 lets the shoulders bulge wider than the sides, like a dome."""
    hw = w / 2
    left = _ogee_side(cx, hw, ys, ya, swell)
    right = [(2 * cx - x, y) for x, y in reversed(left)]
    pts = left + right[1:]
    if base == "round":
        pts += arc(cx, y0 + hw, hw, hw, 0, -180)
    else:
        pts += [(cx + hw, y0), (cx - hw, y0)]
    if flip is not None:
        pts = [(x, 2 * flip - y) for x, y in pts]
    return Polygon(pts).buffer(0)


def cusped(cx, w, y0, ys, ya):
    """A cusped (multifoil) Mughal arch: an onion arch with scalloped sides."""
    d = w * 0.11
    hw = w / 2 - d
    side = _ogee_side(cx, hw, ys, ya)
    parts = [window(cx, 2 * hw, ys - 1, ys, ya), box(cx - w / 2, y0, cx + w / 2, ys)]
    for t in (0.07, 0.36):
        x, y = side[int(t * (len(side) - 1))]
        for px in (x, 2 * cx - x):
            parts.append(Point(px, y).buffer(w * 0.17, 24))
    return unary_union(parts)


def rrect(x0, y0, x1, y1, tl=0, tr=0, br=0, bl=0):
    """A box with its own radius on each corner."""
    return Polygon(rpath([(x0, y0, bl), (x0, y1, tl), (x1, y1, tr), (x1, y0, br)], closed=True))


class G:
    """One glyph: strokes plus extra shapes, minus cuts."""

    def __init__(self, adv):
        self.adv = adv
        self.shapes = []
        self.cuts = []

    def s(self, pts, closed=False, cap="flat", scale=1.0, clip=None):
        geo = stroke(rpath(pts, closed) if not closed else rpath(pts, True)[:-1], closed, cap, scale)
        if clip:
            geo = geo.intersection(box(*clip))
        self.shapes.append(geo)
        return self

    def raw(self, pts, closed=False, cap="flat", scale=1.0, clip=None):
        """A stroke along points that are already sampled (arcs, ellipses)."""
        geo = stroke(pts, closed, cap, scale)
        if clip:
            geo = geo.intersection(box(*clip))
        self.shapes.append(geo)
        return self

    def add(self, shape):
        self.shapes.append(shape)
        return self

    def dot(self, x, y, r):
        self.shapes.append(Point(x, y).buffer(r, 32))
        return self

    def poly(self, pts):
        self.shapes.append(Polygon(pts))
        return self

    def cut(self, shape):
        self.cuts.append(shape)
        return self

    def geometry(self):
        geo = unary_union(self.shapes)
        for c in self.cuts:
            geo = geo.difference(c)
        return geo.simplify(0.04)        # keep curves smooth at poster sizes

    def contours(self):
        geo = self.geometry()
        polys = [geo] if geo.geom_type == "Polygon" else list(getattr(geo, "geoms", []))
        out = []
        for p in polys:
            if p.geom_type != "Polygon" or p.area < 30:
                continue
            p = orient(p, sign=-1.0)          # outer clockwise, holes counter-clockwise
            out.append(list(p.exterior.coords)[:-1])
            for hole in p.interiors:
                if Polygon(hole).area >= 30:
                    out.append(list(hole.coords)[:-1])
        return out
