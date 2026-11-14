"""The letters: heavy blocks with Mughal architecture cut into them.

  door     n m h r stand on a pointed onion-arch doorway; u is one upside down
  bud      o a b d e g p q ... have a counter shaped like a lotus bud / dome window
  minaret  the tall stems of b d h k l end in an onion dome; the dot of i and j,
           and the full stop, are small domes
  cusps    the doorways of capital A, H and M are cusped (scalloped) arches

Call set_weight(k) before building to switch weights (1.00 = Black, 0.79 = Bold, 0.60 = Regular).
"""
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import engine
from engine import ASC, CAP, DESC, G, XH, arc, box, cusped, rrect, window

OV = 8           # how far round shapes pass the baseline and the top line
R = 4            # tiny softening of square corners
SPRING = 225     # height where a lowercase doorway starts to curve

# Weight-dependent metrics, populated by set_weight().
K = 1.0
WS = 1.0
SB = SR = V = VC = HB = WL = WC = TA = CTA = FL = CFL = DOOR = PW = 0
HX = HY = T = CT = BO = DB = 0.0


def set_weight(k=1.0):
    """Set masonry and window proportions for weight factor k in (0.55 .. 1.0]."""
    global K, WS, SB, SR, V, VC, HB, WL, WC, TA, CTA, FL, CFL, DOOR, PW, HX, HY, T, CT, BO, DB
    K = k
    WS = 0.90 + 0.10 * k                       # outer widths narrow only slightly in lighter weights
    SB = round(46 + 15 * (1 - k))              # 46 Black, 49 Bold, 52 Regular
    SR = round(34 + 12 * (1 - k))              # 34 Black, 37 Bold, 39 Regular
    V = round(150 * k)                         # 150 Black, 118 Bold, 90 Regular
    VC = round(160 * k)                        # 160 Black, 126 Bold, 96 Regular
    HB = round(124 * k)                        # 124 Black, 98 Bold, 74 Regular
    WL = round(136 * k)                        # round lowercase wall
    WC = round(150 * k)                        # round capital wall
    TA = round(80 * k - 10 * (1 - k))          # masonry above lowercase arch point
    CTA = round(92 * k)                        # masonry above capital arch point
    FL = round(94 * k)                         # floor thickness of lowercase bud bowl
    CFL = round(112 * k)                       # floor thickness of capital bud bowl
    DOOR = round(492 * (0.89 + 0.11 * k)) - 2 * V   # 192 Black, 245 Bold, 290 Regular
    engine.PEN["v"] = V
    engine.PEN["h"] = HB
    HX, HY = engine.half()
    T = XH - HY                                # centre-line of a stroke along the top of lowercase
    CT = CAP - HY                              # ... along the top of capitals
    BO = HY - OV                               # centre-line of a round bottom
    DB = DESC + HY                             # centre-line of a descender's hook
    PW = V + 2 * SB                            # advance of a dot


set_weight(1.0)

GLYPHS = {}


def glyph(*chars):
    def reg(fn):
        for ch in chars:
            GLYPHS[ch] = fn
        return fn
    return reg


# ------------------------------------------------------------------ parts
def stem(g, x0, y0, y1, w=None):
    w = V if w is None else w
    g.add(rrect(x0, y0, x0 + w, y1, R, R, R, R))


def minaret(g, x0, w=None):
    """A tall stem ending in an onion dome."""
    w = V if w is None else w
    ya = ASC + 54
    ys = ya - round(144 * (0.76 + 0.24 * K))
    stem(g, x0, 0, ys - 4, w)
    g.add(window(x0 + w / 2, w + round(12 * K), ys - 35, ys, ya, swell=0.16))


def dome(cx, y0, w=None):
    """A free-standing onion dome: the dot of i, the full stop."""
    w = V if w is None else w
    return window(cx, w, y0, y0 + w * 0.56, y0 + w * 1.42, base="round", swell=0.12)


def diag(xa, ya, xb, yb, wd):
    """A slanted bar from (xa, ya) to (xb, yb), cut level at both ends."""
    h = wd / 2
    return Polygon([(xa - h, ya), (xa + h, ya), (xb + h, yb), (xb - h, yb)])


def corbel(x, y, sx, sy, size):
    """A bracket filling the corner where a bar meets a stem, with the
    S-curved profile of the stone brackets under a jharokha balcony.
    (x, y) is the corner; sx = which way the bar runs, sy = the stem."""
    size = size * K
    curve = engine._bez((x, y + sy * size), (x + sx * 0.05 * size, y + sy * 0.30 * size),
                        (x + sx * 0.70 * size, y + sy * 0.55 * size), (x + sx * 1.1 * size, y))
    return Polygon([(x - sx * 2, y - sy * 2), (x - sx * 2, y + sy * size)] + curve + [(x + sx * 1.1 * size, y - sy * 2)])


def cross(cx, w, wall, top, clip=None):
    """Two onion arches meeting point to point: X, x and the arms of K, k."""
    v = vee(cx, w, w - 2 * wall, top, round(190 * K))
    upper = affinity.scale(v, yfact=0.61, origin=(cx, top + OV))
    lower = affinity.scale(upper, yfact=-1, origin=(cx, top / 2))
    lower = lower.intersection(box(cx - w, 0, cx + w, top))
    upper = upper.intersection(box(cx - w, 0, cx + w, top))
    shape = unary_union([upper, lower])
    return shape.intersection(box(*clip)) if clip else shape


def sway(xa, ya, xb, yb, wd):
    """A diagonal that leaves both ends upright and swings across in an
    S-curve, the profile of an onion arch: Z, z, 7."""
    h = yb - ya
    mid = engine._bez((xa, ya), (xa, ya + 0.5 * h), (xb, yb - 0.5 * h), (xb, yb))
    return Polygon([(x - wd / 2, y) for x, y in mid] + [(x + wd / 2, y) for x, y in reversed(mid)])


def gate(g, x0, door_w=None, stems=2, top=XH, spring=None):
    """A block standing on onion-arch doorways. Returns its right edge."""
    door_w = DOOR if door_w is None else door_w
    spring = round(SPRING + 55 * (1 - K)) if spring is None else spring
    tuck = round(22 * K) if stems > 2 else 0
    step = door_w + V - tuck
    x1 = x0 + V + step * (stems - 1) + tuck
    g.add(rrect(x0, 0, x1, top, tl=R, tr=round(150 * (0.80 + 0.20 * K)), br=R, bl=R))
    x = x0 + V
    for _ in range(stems - 1):
        g.cut(window(x + door_w / 2, door_w, -20, spring, top - TA))
        x += step
    return x1


def bowl(g, x0, w=None, side=None):
    """A rounded block with a bud-shaped counter; `side` ('left'/'right') is
    kept square where it meets a stem. Returns its right edge."""
    w = DOOR if w is None else w
    wl = V if side == "left" else WL
    wr = V if side == "right" else WL
    x1 = x0 + wl + w + wr
    rad = round(205 * (0.88 + 0.12 * K))
    rl = R if side == "left" else rad
    rr = R if side == "right" else rad
    ov = 0 if side else OV
    shape = rrect(x0, -ov, x1, XH + ov, tl=rl, tr=rr, br=rr, bl=rl)
    shape = shape.difference(window(x0 + wl + w / 2, w, FL, 250, XH - TA + 4, base="round"))
    g.add(shape)
    return x1


def hook(g, xs, top=150, reach=290):
    """A descender that turns left along the bottom line."""
    g.s([(xs, top), (xs, DB, 160), (xs - round(reach * WS), DB)])


@glyph(" ", "\u00a0")
def space():
    return G(round(230 * (0.94 + 0.06 * K)))


# ---------------------------------------------------------------- capitals
@glyph("A")
def cap_A():
    x0 = round(30 + 8 * (1 - K))
    w = round(548 * WS)
    cx = x0 + w / 2
    g = G(w + 2 * x0)
    g.add(window(cx, w, 0, 270, CAP + 54))
    g.cut(cusped(cx, w - 2 * round(165 * K), -20, 108, round(258 + 56 * (1 - K))))
    g.cut(window(cx, round(150 + 116 * (1 - K)), round(354 - 16 * (1 - K)),
                 round(440 + 24 * (1 - K)), round(572 + 72 * (1 - K)), base="round"))
    return g


@glyph("B")
def cap_B():
    x0 = SB + 6
    ow = round(492 * WS)
    rw = round(134 * K + 14 * (1 - K))
    x1 = x0 + ow
    upper = rrect(x0, round(356 - 26 * K), x1 - 24, CAP,
                  tl=R, tr=round(165 * K + 20 * (1 - K)), br=round(120 * K + 16 * (1 - K)), bl=R)
    lower = rrect(x0, 0, x1, round(356 + 28 * K),
                  tl=R, tr=round(135 * K + 16 * (1 - K)), br=round(180 * K + 18 * (1 - K)), bl=R)
    g = G(x1 + SR)
    g.add(unary_union([upper, lower]))
    uw = (x1 - 24) - (x0 + VC) - rw
    lw = x1 - (x0 + VC) - rw
    g.cut(window(x0 + VC + uw / 2, uw, round(356 + 70 * K), 500, CAP - round(86 * K)))
    g.cut(window(x0 + VC + lw / 2, lw, round(100 * K + 14 * (1 - K)), 190, round(356 - 58 * K)))
    return g


def c_body(x0, mouth):
    ow = round(530 * WS)
    x1 = x0 + ow
    cx = (x0 + x1) / 2
    iw = ow - 2 * WC
    shape = rrect(x0, -OV, x1, CAP + OV, 250, 250, 250, 250)
    shape = shape.difference(window(cx, iw, CFL, 360, CAP - CTA, base="round"))
    shape = shape.difference(box(cx + round(56 * K), mouth[0], x1 + 20, mouth[1]))
    return shape, x1, cx


@glyph("C")
def cap_C():
    pad = round(34 * (1 - K))
    shape, x1, _ = c_body(SR, (236 - pad, 376 + pad))
    g = G(x1 + SR - 8)
    g.add(shape)
    return g


@glyph("D")
def cap_D():
    x0 = SB + 6
    ow = round(546 * WS)
    x1 = x0 + ow
    iw = ow - VC - WC
    g = G(x1 + SR)
    g.add(rrect(x0, 0, x1, CAP, tl=R, tr=250, br=250, bl=R))
    g.cut(window(x0 + VC + iw / 2, iw, CFL, 370, CAP - CTA, base="round"))
    return g


@glyph("E")
def cap_E():
    x0 = SB + 6
    x1 = x0 + VC + round(240 * WS)
    m0, m1 = round(362 - HB / 2), round(362 + HB / 2)
    g = G(x1 + SR)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(box(x0 + VC, m1, x1 + 20, CAP - HB))
    g.cut(box(x0 + VC, HB, x1 + 20, m0))
    g.cut(box(x1 - 44, m0 - 10, x1 + 20, m1 + 10))
    g.add(corbel(x0 + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x0 + VC, HB, 1, 1, 66))
    return g


@glyph("F")
def cap_F():
    x0 = SB + 6
    x1 = x0 + VC + round(230 * WS)
    m0, m1 = round(362 - HB / 2), round(362 + HB / 2)
    g = G(x1 + 20)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(box(x0 + VC, m1, x1 + 20, CAP - HB))
    g.cut(box(x0 + VC, -20, x1 + 20, m0))
    g.cut(box(x1 - 44, m0 - 10, x1 + 20, m1 + 10))
    g.add(corbel(x0 + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x0 + VC, m0, 1, -1, 84))
    return g


@glyph("G")
def cap_G():
    shape, x1, cx = c_body(SR, (352, round(462 + 24 * (1 - K))))
    shape = unary_union([shape, rrect(cx - 12, 352 - HB, x1 - round(60 * K), 352, R, R, R, R)])
    g = G(x1 + SR)
    g.add(shape)
    return g


@glyph("H")
def cap_H():
    x0 = SB + 6
    ow = round(524 * WS)
    x1 = x0 + ow
    cx = (x0 + x1) / 2
    cw = ow - 2 * VC
    b0, b1 = round(358 - HB / 2), round(358 + HB / 2)
    g = G(x1 + SB + 6)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(cusped(cx, cw, -20, 125, b0))
    g.cut(box(cx - cw / 2, b1, cx + cw / 2, CAP + 20))
    return g


@glyph("I")
def cap_I():
    x0 = SB + 6
    g = G(x0 * 2 + VC)
    stem(g, x0, 0, CAP, VC)
    return g


@glyph("J")
def cap_J():
    xs = round(300 * WS)
    g = G(xs + VC / 2 + SB + 6)
    g.s([(xs, CAP), (xs, HY, 190), (24, HY)])
    return g


@glyph("K")
def cap_K():
    x0 = SB + 6
    s = x0 + VC
    arm_w = round(338 * WS)
    g = G(s + arm_w)
    stem(g, x0, 0, CAP, VC)
    g.add(cross(s - 4, round(644 * WS), round(186 * K), CAP, clip=(s - 5, 0, s + 400, CAP)))
    return g


@glyph("L")
def cap_L():
    x0 = SB + 6
    arm = round(226 * WS)
    g = G(x0 + VC + arm + 24)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 0, x0 + VC + arm, HB, R, R, R, R))
    g.add(corbel(x0 + VC, HB, 1, 1, 112))
    return g


@glyph("M")
def cap_M():
    x0 = SB + 6
    ow = round(814 * (0.92 + 0.08 * K))
    x1 = x0 + ow
    cx = (x0 + x1) / 2
    cw = (ow - 2 * VC - V) / 2 - round(8 * (1 - K))
    ys_c = round(170 + 60 * (1 - K))
    ya_c = round(420 + 110 * (1 - K))
    g = G(x1 + SB + 6)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(cusped(x0 + VC + cw / 2, cw, -20, ys_c, ya_c))
    g.cut(cusped(x1 - VC - cw / 2, cw, -20, ys_c, ya_c))
    g.cut(window(cx, round(196 + 88 * (1 - K)), -20, round(70 + 30 * (1 - K)),
                 round(392 + 64 * (1 - K)), flip=CAP / 2))
    return g


@glyph("N")
def cap_N():
    x0 = SB + 6
    ow = round(556 * WS)
    x1 = x0 + ow
    dw = round(196 * K)
    g = G(x1 + SB + 6)
    stem(g, x0, 0, CAP, VC)
    stem(g, x1 - VC, 0, CAP, VC)
    g.poly([(x0, CAP), (x0 + dw, CAP), (x1, 0), (x1 - dw, 0)])
    return g


def o_body(x0):
    ow = round(540 * WS)
    x1 = x0 + ow
    cx = (x0 + x1) / 2
    iw = ow - 2 * WC
    shape = rrect(x0, -OV, x1, CAP + OV, 250, 250, 250, 250)
    return shape.difference(window(cx, iw, CFL, 370, CAP - CTA, base="round")), x1, cx


@glyph("O")
def cap_O():
    shape, x1, _ = o_body(SR)
    g = G(x1 + SR)
    g.add(shape)
    return g


@glyph("P")
def cap_P():
    x0 = SB + 6
    ow = round(486 * WS)
    rw = round(134 * K)
    x1 = x0 + ow
    iw = ow - VC - rw
    by = round(286 + 16 * (1 - K))
    g = G(x1 + 24)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, by, x1, CAP, tl=R, tr=180, br=180, bl=R))
    g.cut(window(x0 + VC + iw / 2, iw, by + round(106 * K), 480, CAP - round(86 * K)))
    return g


@glyph("Q")
def cap_Q():
    shape, x1, cx = o_body(SR)
    g = G(x1 + SR)
    g.add(shape)
    g.add(diag(cx + 70, round(150 * K + 20 * (1 - K)), x1 - 10, -118, round(136 * K)))
    return g


@glyph("R")
def cap_R():
    x0 = SB + 6
    ow = round(486 * WS)
    rw = round(134 * K)
    x1 = x0 + ow
    iw = ow - VC - rw
    s = x0 + VC
    by = round(292 + 16 * (1 - K))
    g = G(x1 + 34)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, by, x1, CAP, tl=R, tr=180, br=180, bl=R))
    g.cut(window(s + iw / 2, iw, by + round(104 * K), 482, CAP - round(86 * K)))
    g.add(cross(s - 10, round(668 * WS), round(190 * K), 720, clip=(s - 10, 0, s + 420, by + 63)))
    return g


def s_path(cx, rx, top, bot):
    mid = (top + bot) / 2 + 9
    return (arc(cx, (top + mid) / 2, rx * 0.95, (top - mid) / 2, 24, 270)
            + arc(cx, (mid + bot) / 2, rx, (mid - bot) / 2, 90, -156)[1:])


@glyph("S")
def cap_S():
    cx = round(266 * WS)
    rx = round(162 + 18 * (1 - K))
    g = G(cx * 2 - 6)
    g.raw(s_path(cx, rx, CT + OV, BO))
    return g


@glyph("T")
def cap_T():
    x0 = round(18 + 6 * (1 - K))
    w = round(500 * WS)
    g = G(w + 2 * x0)
    g.add(rrect(x0, CAP - HB, x0 + w, CAP, R, R, R, R))
    stem(g, x0 + w / 2 - VC / 2, 0, CAP, VC)
    g.add(corbel(x0 + w / 2 - VC / 2, CAP - HB, -1, -1, 92))
    g.add(corbel(x0 + w / 2 + VC / 2, CAP - HB, 1, -1, 92))
    return g


@glyph("U")
def cap_U():
    x0 = SB + 6
    ow = round(524 * WS)
    x1 = x0 + ow
    iw = ow - 2 * VC
    rad = round(225 * (0.76 + 0.24 * K))
    g = G(x1 + SB + 6)
    g.add(rrect(x0, -OV, x1, CAP, tl=R, tr=R, br=rad, bl=rad))
    g.cut(window((x0 + x1) / 2, iw, -20, round(250 + 215 * (1 - K)),
                 CAP - round(104 * K - 22 * (1 - K)), flip=CAP / 2))
    return g


def vee(cx, w, inner, top, depth):
    """An upside-down onion arch: V, v and the halves of W, w."""
    out = window(cx, w, 0, 80, top + OV, flip=top / 2)
    return out.difference(window(cx, inner, -30, 80, top - depth, flip=top / 2))


@glyph("V")
def cap_V():
    w = round(566 * WS)
    wall = round(185 * K)
    g = G(w + 36)
    g.add(vee(18 + w / 2, w, w - 2 * wall, CAP, round(190 * K)))
    return g


@glyph("W")
def cap_W():
    w = round(470 * WS)
    step = round(312 * WS)
    wall = round(160 * K)
    g = G(w + step + 36)
    g.add(vee(18 + w / 2, w, w - 2 * wall, CAP, round(200 * K)))
    g.add(vee(18 + w / 2 + step, w, w - 2 * wall, CAP, round(200 * K)))
    return g


@glyph("X")
def cap_X():
    x0 = round(20 + 6 * (1 - K))
    w = round(548 * WS)
    g = G(w + 2 * x0)
    g.add(cross(x0 + w / 2, w, round(182 * K), CAP))
    return g


@glyph("Y")
def cap_Y():
    x0 = round(14 + 6 * (1 - K))
    w = round(560 * WS)
    cx = x0 + w / 2
    wall = round(184 * K)
    g = G(w + 2 * x0)
    v = vee(cx, w, w - 2 * wall, CAP, round(190 * K))
    g.add(affinity.scale(v, yfact=0.62, origin=(cx, CAP + OV)).intersection(box(0, 0, w + 2 * x0, CAP)))
    stem(g, cx - VC / 2, 0, 330, VC)
    return g


@glyph("Z")
def cap_Z():
    x0 = round(34 + 6 * (1 - K))
    x1 = x0 + round(470 * WS)
    inset = round(100 * K)
    g = G(x1 + x0)
    g.add(box(x0, CAP - HB, x1, CAP))
    g.add(box(x0, 0, x1, HB))
    g.add(sway(x0 + inset, HB - 2, x1 - inset, CAP - HB + 2, round(200 * K)))
    return g


# --------------------------------------------------------------- lowercase
@glyph("a")
def a():
    g = G(0)
    x1 = bowl(g, SR, side="right")
    g.adv = x1 + SB
    return g


@glyph("b")
def b():
    g = G(0)
    x1 = bowl(g, SB, side="left")
    minaret(g, SB)
    g.adv = x1 + SR
    return g


@glyph("c")
def c():
    g = G(0)
    x1 = bowl(g, SR)
    g.cut(box((SR + x1) / 2 + round(44 * K), round(150 * K + 18 * (1 - K)), x1 + 20, round(262 + 52 * (1 - K))))
    g.adv = x1 + SR - 8
    return g


@glyph("d")
def d():
    g = G(0)
    x1 = bowl(g, SR, side="right")
    minaret(g, x1 - V)
    g.adv = x1 + SB
    return g


@glyph("e")
def e():
    x0, w = SR, DOOR
    x1 = x0 + WL + w + WL
    cx = (x0 + x1) / 2
    rad = round(205 * (0.88 + 0.12 * K))
    y_eye = round(292 - 48 * (1 - K))
    m_bot = round(FL + 52 * K * K)
    m_top = y_eye - round(92 * K)
    mr = min(27, max(8, (m_top - m_bot) // 2))
    m_bl = min(m_top - m_bot - mr, round(mr + 150 * (1 - K)))
    g = G(x1 + SR)
    g.add(rrect(x0, -OV, x1, XH + OV, rad, rad, rad, rad))
    g.cut(window(cx, w, y_eye, y_eye + 46, XH - TA + 4))
    g.cut(rrect(x0 + WL + round(34 * K), m_bot, x1 + 20, m_top, tl=mr, bl=m_bl))
    return g


@glyph("f")
def f():
    xs = 40 + round(62 * WS) + V / 2
    g = G(xs + round(204 * WS))
    g.s([(xs, 0), (xs, ASC - HY, 150), (xs + round(194 * WS), ASC - HY)])
    g.s([(20, T), (xs + round(190 * WS), T)])
    return g


@glyph("g")
def g_():
    g = G(0)
    x1 = bowl(g, SR, side="right")
    hook(g, x1 - V / 2)
    g.adv = x1 + SB
    return g


@glyph("h")
def h():
    g = G(0)
    x1 = gate(g, SB)
    minaret(g, SB)
    g.adv = x1 + SB
    return g


@glyph("i")
def i():
    g = G(SB * 2 + V)
    stem(g, SB, 0, XH)
    g.add(dome(SB + V / 2, XH + 58))
    return g


@glyph("j")
def j():
    x0 = round(112 * WS)
    xs = x0 + V / 2
    g = G(x0 + V + SB)
    g.s([(xs, XH), (xs, DB, 150), (xs - round(196 * WS), DB)])
    g.add(dome(xs, XH + 58))
    return g


@glyph("k")
def k():
    s = SB + V
    g = G(s + round(294 * WS))
    minaret(g, SB)
    g.add(cross(s - 4, round(560 * WS), round(166 * K), XH, clip=(s - 5, 0, s + 400, XH)))
    return g


@glyph("l")
def l_():
    g = G(SB * 2 + V)
    minaret(g, SB)
    return g


@glyph("m")
def m():
    g = G(0)
    ow = round(760 * WS)
    tuck = round(22 * K)
    dw = round((ow - 3 * V + tuck) / 2)
    x1 = gate(g, SB, door_w=dw, stems=3)
    g.adv = x1 + SB
    return g


@glyph("n")
def n():
    g = G(0)
    x1 = gate(g, SB)
    g.adv = x1 + SB
    return g


@glyph("o")
def o():
    g = G(0)
    x1 = bowl(g, SR)
    g.adv = x1 + SR
    return g


@glyph("p")
def p():
    g = G(0)
    x1 = bowl(g, SB, side="left")
    stem(g, SB, DESC, 10)
    g.adv = x1 + SR
    return g


@glyph("q")
def q():
    g = G(0)
    x1 = bowl(g, SR, side="right")
    stem(g, x1 - V, DESC, 10)
    g.adv = x1 + SB
    return g


@glyph("r")
def r():
    g = G(0)
    ow = round(450 * WS)
    dw = ow - 2 * V
    x1 = gate(g, SB, door_w=dw)
    g.cut(box(SB + V + round(dw / 2 + 11 * K), -20, x1 + 10, round(318 + 52 * (1 - K))))
    g.adv = x1 + round(14 + 8 * (1 - K))
    return g


@glyph("s")
def s():
    cx = round(238 * WS)
    rx = round(132 + 16 * (1 - K))
    g = G(cx * 2 - 6)
    g.raw(s_path(cx, rx, T + OV, BO))
    return g


@glyph("t")
def t():
    xs = 40 + round(60 * WS) + V / 2
    g = G(xs + round(252 * WS))
    g.s([(xs, 560), (xs, HY, 150), (xs + round(206 * WS), HY)])
    g.s([(22, T), (xs + round(216 * WS), T)])
    g.add(window(xs, V, 540, 592, 716))
    return g


def u_body(g, x0):
    x1 = x0 + V + DOOR + V
    g.add(rrect(x0, 0, x1, XH, tl=R, tr=R, br=R, bl=round(150 * (0.76 + 0.24 * K))))
    g.cut(window((x0 + x1) / 2, DOOR, -20, round(SPRING + 70 * (1 - K)), XH - TA, flip=XH / 2))
    return x1


@glyph("u")
def u():
    g = G(0)
    x1 = u_body(g, SB)
    g.adv = x1 + SB
    return g


@glyph("v")
def v():
    w = round(462 * WS)
    wall = round(153 * K)
    g = G(w + 32)
    g.add(vee(16 + w / 2, w, w - 2 * wall, XH, round(150 * K)))
    return g


@glyph("w")
def w_():
    w = round(400 * WS)
    step = round(262 * WS)
    wall = round(138 * K)
    g = G(w + step + 32)
    g.add(vee(16 + w / 2, w, w - 2 * wall, XH, round(158 * K)))
    g.add(vee(16 + w / 2 + step, w, w - 2 * wall, XH, round(158 * K)))
    return g


@glyph("x")
def x():
    x0 = round(18 + 6 * (1 - K))
    w = round(468 * WS)
    g = G(w + 2 * x0)
    g.add(cross(x0 + w / 2, w, round(164 * K), XH))
    return g


@glyph("y")
def y():
    g = G(0)
    x1 = u_body(g, SB)
    hook(g, x1 - V / 2)
    g.adv = x1 + SB
    return g


@glyph("z")
def z():
    x0 = round(30 + 6 * (1 - K))
    x1 = x0 + round(404 * WS)
    inset = round(92 * K)
    g = G(x1 + x0)
    g.add(box(x0, XH - HB, x1, XH))
    g.add(box(x0, 0, x1, HB))
    g.add(sway(x0 + inset, HB - 2, x1 - inset, XH - HB + 2, round(184 * K)))
    return g


# ------------------------------------------------------------------ digits
@glyph("0")
def d0():
    x0 = SR
    ow = round(470 * WS)
    x1 = x0 + ow
    wall = round(137 * K)
    g = G(x1 + SR)
    g.add(rrect(x0, -OV, x1, CAP + OV, 215, 215, 215, 215))
    g.cut(window((x0 + x1) / 2, ow - 2 * wall, CFL, 365, CAP - CTA, base="round"))
    return g


@glyph("1")
def d1():
    x0 = round(150 * WS)
    g = G(x0 + VC + round(62 + 12 * (1 - K)))
    stem(g, x0, 0, CAP, VC)
    y0 = round(436 + 10 * (1 - K))
    flag = window(x0 + VC, 2 * (VC + round(88 * WS + 22 * (1 - K))), y0, round(470 + 16 * (1 - K)), CAP + 4)
    g.add(flag.intersection(box(0, y0, x0 + VC, CAP)))
    return g


@glyph("2")
def d2():
    cx = round(250 * WS)
    g = G(cx * 2)
    g.raw(arc(cx, 470, round(142 + 16 * (1 - K)), CT + OV - 470, 172, -42) + [(round(46 + 74 * K), round(96 * K))])
    g.add(box(46, 0, round(462 * WS), HB))
    return g


@glyph("3")
def d3():
    cx, top, mid = round(240 * WS), CT + OV, 368
    g = G(round(494 * WS))
    g.raw(arc(cx, (top + mid) / 2, round(142 + 16 * (1 - K)), (top - mid) / 2, 158, -90)
          + arc(cx, (mid + BO) / 2, round(152 + 16 * (1 - K)), (mid - BO) / 2, 90, -156)[1:])
    g.cut(box(-200, 290, 168, 450))
    return g


@glyph("4")
def d4():
    ow = round(552 * WS)
    xs = round(306 * WS)
    g = G(ow)
    stem(g, xs, 0, CAP, VC)
    g.add(box(28, 168, ow - 26, 168 + HB))
    g.add(diag(round(120 * WS), round(168 + HB - 12), xs + round(72 * K), CAP, round(176 * K)))
    return g


@glyph("5")
def d5():
    cx, cy = round(246 * WS), 240
    g = G(round(516 * WS))
    g.add(box(72, CAP - HB, round(448 * WS), CAP))
    g.add(box(72, round(372 - 20 * (1 - K)), 72 + V, CAP))
    g.add(corbel(72 + V, CAP - HB, 1, -1, 70))
    g.raw(arc(cx, cy, round(160 + 16 * (1 - K)), cy - BO, 146, -152))
    return g


@glyph("6")
def d6():
    x0 = SR
    x1 = x0 + WL + DOOR + WL
    rad = round(205 * (0.88 + 0.12 * K))
    g = G(x1 + SR)
    shape = rrect(x0, -OV, x1, 436, rad, rad, rad, rad)
    g.add(shape.difference(window((x0 + x1) / 2, DOOR, FL, 240, round(352 + 28 * (1 - K)), base="round")))
    g.s([(x0 + HX, round(372 - 330 * (1 - K))), (x0 + HX, CT, 210), (x1 - 66, CT)])
    return g


@glyph("7")
def d7():
    g = G(round(492 * WS))
    g.add(box(30, CAP - HB, round(468 * WS), CAP))
    g.add(sway(round(196 * WS), 0, round(376 * WS), CAP - HB + 2, round(184 * K)))
    return g


@glyph("8")
def d8():
    x0 = SR
    ow = round(452 * WS)
    x1 = x0 + ow
    cx = (x0 + x1) / 2
    lw = ow - 2 * round(126 * K)
    uw = (ow - 48) - 2 * round(116 * K)
    g = G(x1 + SR)
    g.add(rrect(x0, -OV, x1, round(362 + 26 * K), 190, 190, 190, 190))
    g.add(rrect(x0 + 24, round(362 - 26 * K), x1 - 24, CAP + OV, 176, 176, 176, 176))
    g.cut(window(cx, lw, round(92 * K), 200, round(362 - 56 * K), base="round"))
    g.cut(window(cx, uw, round(362 + 54 * K), 515, CAP - round(86 * K), base="round"))
    return g


@glyph("9")
def d9():
    x0 = SR
    x1 = x0 + WL + DOOR + WL
    rad = round(205 * (0.88 + 0.12 * K))
    g = G(x1 + SR)
    shape = rrect(x0, 264, x1, CAP + OV, rad, rad, rad, rad)
    g.add(shape.difference(window((x0 + x1) / 2, DOOR, round(360 - 28 * (1 - K)), 505, CAP - round(90 * K), base="round")))
    g.s([(x1 - HX, round(345 + 300 * (1 - K))), (x1 - HX, HY, 210), (x0 + 66, HY)])
    return g


# ------------------------------------------------------------- punctuation
def comma_shape(x0, y=0):
    w = V
    s = w / 150
    return Polygon([(x0, y + w), (x0 + w, y + w), (x0 + w, y + 10 * s),
                    (x0 + 52 * s, y - 150 * (0.75 + 0.25 * s)),
                    (x0 - 12 * s, y - 150 * (0.75 + 0.25 * s)),
                    (x0 + 62 * s, y), (x0, y)])


@glyph(".")
def period():
    return G(PW).add(dome(PW / 2, -OV))


@glyph(",")
def comma():
    return G(PW).add(comma_shape(SB))


@glyph(":")
def colon():
    return G(PW).add(dome(PW / 2, -OV)).add(dome(PW / 2, 300))


@glyph(";")
def semicolon():
    return G(PW).add(comma_shape(SB)).add(dome(PW / 2, 300))


@glyph("!")
def exclam():
    g = G(PW + 10)
    cx = g.adv / 2
    hw1, hw0 = round(82 * K), round(52 * K)
    g.poly([(cx - hw1, CAP), (cx + hw1, CAP), (cx + hw0, round(262 - 30 * (1 - K))), (cx - hw0, round(262 - 30 * (1 - K)))])
    g.add(dome(cx, -OV))
    return g


@glyph("?")
def question():
    cx = round(226 * WS)
    g = G(cx * 2)
    g.raw(arc(cx, 500, round(138 + 14 * (1 - K)), CT + OV - 500, 168, -52) + [(cx, 318), (cx, round(262 - 30 * (1 - K)))])
    g.add(dome(cx, -OV))
    return g


def tick(x0):
    w = round(140 * K)
    t = round(36 * K)
    return Polygon([(x0, CAP), (x0 + w, CAP), (x0 + w - t, CAP - 236), (x0 + t, CAP - 236)])


def curly_close(x0):
    w = round(V * 0.92)
    s = affinity.scale(comma_shape(0, 0), xfact=0.92, yfact=0.92, origin=(0, V))
    return affinity.translate(s, x0, CAP - V), w


def curly_open(x0):
    c, w = curly_close(0)
    s = affinity.rotate(c, 180, origin=(w / 2, CAP - w))
    return affinity.translate(s, x0, 0), w


@glyph("'")
def quote():
    w = round(140 * K)
    return G(w + 2 * 40).add(tick(40))


@glyph('"')
def dquote():
    w = round(140 * K)
    gap = round(44 + 12 * (1 - K))
    return G(w * 2 + gap + 2 * 40).add(tick(40)).add(tick(40 + w + gap))


@glyph("\u2018")
def quote_l():
    s, w = curly_open(36)
    return G(w + 72).add(s)


@glyph("\u2019")
def quote_r():
    s, w = curly_close(36)
    return G(w + 72).add(s)


@glyph("\u201c")
def dquote_l():
    s1, w = curly_open(36)
    gap = round(34 + 12 * (1 - K))
    s2, _ = curly_open(36 + w + gap)
    return G(w * 2 + gap + 72).add(s1).add(s2)


@glyph("\u201d")
def dquote_r():
    s1, w = curly_close(36)
    gap = round(34 + 12 * (1 - K))
    s2, _ = curly_close(36 + w + gap)
    return G(w * 2 + gap + 72).add(s1).add(s2)


@glyph("\u2026")
def ellipsis():
    w = round(126 * K)
    step = round(186 * (0.86 + 0.14 * K))
    g = G(SB * 2 + w + step * 2)
    for idx in range(3):
        g.add(dome(SB + w / 2 + idx * step, -OV, w))
    return g


@glyph("\u2022")
def bullet():
    w = round(156 * K)
    adv = PW + 24
    return G(adv).add(dome(adv / 2, 210, w))


@glyph("\u00b0")
def degree():
    r_out = round(122 * (0.88 + 0.12 * K))
    r_in = round(r_out - 74 * K)
    cx, cy = 32 + r_out, CAP + OV - r_out
    return G(cx * 2).add(Point(cx, cy).buffer(r_out, 32).difference(Point(cx, cy).buffer(r_in, 32)))


@glyph("-")
def hyphen():
    return G(260 + 2 * SB).add(box(SB, round(298 - HB / 2), SB + 260, round(298 + HB / 2)))


@glyph("\u2013")
def endash():
    return G(430 + 2 * SB).add(box(SB, round(298 - HB / 2), SB + 430, round(298 + HB / 2)))


@glyph("\u2014")
def emdash():
    return G(760 + 2 * 30).add(box(30, round(298 - HB / 2), 790, round(298 + HB / 2)))


@glyph("_")
def underscore():
    th = round(100 * K)
    return G(520).add(box(0, -60 - th, 520, -60))


@glyph("(")
def paren_l():
    g = G(340)
    g.raw(arc(SB + HX + 250, 270, 250, 560, 116, 244))
    return g


@glyph(")")
def paren_r():
    g = G(340)
    g.raw(arc(340 - (SB + HX + 250), 270, 250, 560, 64, -64))
    return g


@glyph("[")
def bracket_l():
    th = round(110 * K)
    g = G(SB + 290)
    g.add(box(SB, -200, SB + V, 780)).add(box(SB, 780 - th, SB + 264, 780)).add(box(SB, -200, SB + 264, -200 + th))
    return g


@glyph("]")
def bracket_r():
    th = round(110 * K)
    g = G(SB + 290)
    x1 = 290
    g.add(box(x1 - V, -200, x1, 780)).add(box(x1 - 264, 780 - th, x1, 780)).add(box(x1 - 264, -200, x1, -200 + th))
    return g


@glyph("/")
def slash():
    return G(430).add(diag(92, -110, 338, 780, V))


@glyph("\\")
def backslash():
    return G(430).add(diag(338, -110, 92, 780, V))


@glyph("|")
def pipe():
    w = round(130 * K)
    return G(2 * 70 + w).add(box(70, -200, 70 + w, 780))


@glyph("+")
def plus():
    hw = round(66 * K)
    return G(480).add(box(40, round(298 - HB / 2), 440, round(298 + HB / 2))).add(box(240 - hw, 98, 240 + hw, 498))


@glyph("=")
def equal():
    th = round(110 * K)
    return G(480).add(box(40, 391 - th // 2, 440, 391 + (th - th // 2))).add(box(40, 205 - th // 2, 440, 205 + (th - th // 2)))


@glyph("*")
def asterisk():
    g = G(420)
    hw = round(40 * K)
    bar = box(210 - hw, 540 - 150, 210 + hw, 540 + 150)
    for ang in (0, 60, 120):
        g.add(affinity.rotate(bar, ang, origin=(210, 540)))
    return g


@glyph("#")
def hash_():
    th = round(110 * K)
    dw = round(122 * K)
    g = G(610)
    g.add(diag(170, 0, 250, CAP, dw)).add(diag(370, 0, 450, CAP, dw))
    g.add(box(50, 491 - th // 2, 580, 491 + (th - th // 2))).add(box(30, 215 - th // 2, 560, 215 + (th - th // 2)))
    return g


@glyph("%")
def percent():
    g = G(770)
    iw = 270 - 2 * round(98 * K)

    def ring(x0, y0):
        r = rrect(x0, y0, x0 + 270, y0 + 316, 132, 132, 132, 132)
        return r.difference(window(x0 + 135, iw, y0 + round(84 * K), y0 + 150, y0 + 316 - round(76 * K), base="round"))

    g.add(ring(36, CAP + OV - 316)).add(ring(464, -OV))
    g.add(diag(268, 0, 502, CAP, round(122 * K)))
    return g


@glyph("$")
def dollar():
    cx = round(266 * WS)
    rx = round(162 + 18 * (1 - K))
    hw = round(46 * K)
    g = G(cx * 2 - 6)
    g.raw(s_path(cx, rx, CT + OV, BO))
    g.add(box(cx - hw, -96, cx + hw, CAP + 96))
    return g


@glyph("&")
def ampersand():
    x0 = SR
    ow = round(452 * WS)
    x1 = x0 + ow
    cx = (x0 + x1) / 2
    lw = ow - 2 * round(126 * K)
    uw = (ow - 68) - 2 * round(117 * K)
    g = G(x1 + 150)
    g.add(rrect(x0, -OV, x1, round(362 + 26 * K), 190, 190, 190, 190))
    g.add(rrect(x0 + 34, round(362 - 26 * K), x1 - 34, CAP + OV, 172, 172, 172, 172))
    g.cut(window(cx, lw, round(92 * K), 200, round(362 - 56 * K), base="round"))
    g.cut(window(cx, uw, round(362 + 58 * K), 510, CAP - round(88 * K), base="round"))
    leg = diag(cx + 96, 236, x1 + 60, 0, round(156 * K))
    arm = box(x1 - 70, 236, x1 + 126, 236 + round(110 * K))
    g.add(unary_union([leg, arm]))
    return g


@glyph("@")
def at():
    cx, cy, rr = 446, 250, 366
    g = G(892)
    ax = cx + 118 + round(22 * (1 - K))
    u = (rr - (ax - cx)) / 2
    path = [(ax, cy + 120)] + arc(ax + u, cy - 70, u, u * 0.9, 180, 360) + arc(cx, cy, rr, rr, -11, 296)[1:]
    g.raw(path, scale=0.62)
    iw = 332 - 2 * round(116 * K)
    inner = rrect(cx - 176, cy - 176, cx + 156, cy + 176, tl=156, tr=R, br=R, bl=156)
    inner = inner.difference(window(cx - 26 + round(12 * (1 - K)), iw, cy - round(100 + 24 * (1 - K)), cy - 20, cy + round(100 + 24 * (1 - K)), base="round"))
    g.add(inner)
    return g


@glyph("₹")
def rupee():
    x0, x1 = 40, round(500 * WS)
    th2 = round(102 * K)
    y2 = CAP - HB - round(76 + 12 * (1 - K))
    g = G(x1 + 40)
    g.add(box(x0, CAP - HB, x1, CAP))
    g.add(box(x0, y2 - th2, x1, y2))
    g.s([(x0, CT), (round(360 * WS), CT, 149), (round(360 * WS), CT - 298, 149), (x0 + 60, CT - 298)])
    g.add(diag(x0 + round(150 * WS), CT - 298 - HY + 40, x1 - 96, 0, round(188 * K)))
    return g


@glyph("<")
def less():
    g = G(470)
    g.s([(410, 508), (86, 298), (410, 88)], scale=0.8)
    return g


@glyph(">")
def greater():
    g = G(470)
    g.s([(60, 508), (384, 298), (60, 88)], scale=0.8)
    return g


@glyph("^")
def caret():
    g = G(470)
    g.s([(62, 400), (235, 680), (408, 400)], scale=0.8)
    return g


@glyph("~")
def tilde():
    g = G(500)
    g.s([(52, 262), (150, 372, 70), (350, 232, 70), (448, 342)], scale=0.72)
    return g


@glyph("`")
def grave():
    w = round(150 * K)
    b = round(84 * K)
    return G(300).add(Polygon([(40, CAP + 70), (40 + w, CAP + 70), (252, CAP - 110), (252 - b, CAP - 110)]))


def brace(x0):
    """A bracket with a pointed nub on its back."""
    sw = round(130 * K)
    th = round(100 * K)
    return unary_union([box(x0, -200, x0 + sw, 780), box(x0, 780 - th, x0 + 220, 780),
                        box(x0, -200, x0 + 220, -200 + th),
                        Polygon([(x0 + 4, 400), (x0 - round(86 * K), 290), (x0 + 4, 180)])])


@glyph("{")
def brace_l():
    return G(380).add(brace(130))


@glyph("}")
def brace_r():
    return G(380).add(affinity.scale(brace(130), xfact=-1, origin=(190, 0)))


@glyph("€")
def euro():
    shape, x1, cx = c_body(76, (216, 474))
    th = round(84 * K)
    g = G(x1 + SR - 8)
    g.add(shape)
    g.add(rrect(12, 422 - th // 2, cx + 108, 422 + (th - th // 2), R, R, R, R))
    g.add(rrect(12, 268 - th // 2, cx + 84, 268 + (th - th // 2), R, R, R, R))
    return g


@glyph("£")
def pound():
    x0 = 40
    xs = x0 + 92 + VC / 2
    th = round(98 * K)
    g = G(round(520 * WS))
    g.s([(xs, HB), (xs, CT, 150), (round(456 * WS), CT)])
    g.add(rrect(x0, 0, round(476 * WS), HB, R, R, R, R))
    g.add(rrect(x0, 339 - th // 2, round(396 * WS), 339 + (th - th // 2), R, R, R, R))
    return g


# ---------------------------------------------------- extended European Latin
@glyph("Æ")
def cap_AE():
    x0 = 26
    x_stem = round(388 * WS)
    x1 = x_stem + VC + round(228 * WS)
    m0, m1 = round(362 - HB / 2), round(362 + HB / 2)
    g = G(x1 + SR)
    arch = window(x_stem + 70, (x_stem + 70 - x0) * 2, 0, 270, CAP + 120)
    g.add(arch.intersection(box(x0, 0, x_stem + VC, CAP)))
    g.add(rrect(x_stem, 0, x1, CAP, R, R, R, R))
    cw = round(168 + 64 * (1 - K))
    g.cut(cusped(x0 + round(240 * WS) - round(22 * (1 - K)), cw, -20, 118, round(268 + 50 * (1 - K))))
    g.cut(window(x0 + round(266 * WS) - round(16 * (1 - K)), round(108 + 72 * (1 - K)),
                 round(352 - 14 * (1 - K)), round(434 + 20 * (1 - K)), round(554 + 62 * (1 - K)), base="round"))
    g.cut(box(x_stem + VC, m1, x1 + 20, CAP - HB))
    g.cut(box(x_stem + VC, HB, x1 + 20, m0))
    g.cut(box(x1 - 44, m0 - 10, x1 + 20, m1 + 10))
    g.add(corbel(x_stem + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x_stem + VC, HB, 1, 1, 66))
    return g


@glyph("æ")
def low_ae():
    x0 = SR
    x_mid = x0 + round(308 * WS)
    door_e = round(172 + 54 * (1 - K))
    x1 = x_mid + V + door_e + WL - round(8 * K)
    g = G(x1 + SR)
    a_part = rrect(x0, -OV, x_mid + 60, XH + OV, tl=185, tr=110, br=110, bl=180)
    aw = (x_mid - x0) - WL - round(24 * K)
    a_part = a_part.difference(window(x0 + WL + aw / 2, aw, round(76 * K), 155, round(258 + 36 * (1 - K)), base="round"))
    am0, am1 = round(330 + 18 * (1 - K)), round(386 + 38 * (1 - K))
    amr = min(27, max(8, (am1 - am0) // 2))
    a_part = a_part.difference(rrect(x0 - 20, am0, x_mid - 16, am1, tr=amr, br=amr))
    e_part = rrect(x_mid, -OV, x1, XH + OV, tl=110, tr=200, br=200, bl=110)
    cx_e = x_mid + V + door_e / 2
    y_eye = round(292 - 48 * (1 - K))
    m_bot = round(FL + 52 * K * K)
    m_top = y_eye - round(92 * K)
    mr = min(27, max(8, (m_top - m_bot) // 2))
    m_bl = min(m_top - m_bot - mr, round(mr + 140 * (1 - K)))
    e_part = e_part.difference(window(cx_e, door_e, y_eye, y_eye + 46, XH - TA + 4))
    e_part = e_part.difference(rrect(x_mid + V + round(34 * K), m_bot, x1 + 20, m_top, tl=mr, bl=m_bl))
    g.add(unary_union([a_part, e_part]))
    return g


@glyph("Œ")
def cap_OE():
    x0 = SR
    left_ow = round(390 * WS)
    x_mid = x0 + left_ow
    x1 = x_mid + VC + round(224 * WS)
    w_o = left_ow - WC + round(22 * (1 - K)) - round(28 * K)
    m0, m1 = round(362 - HB / 2), round(362 + HB / 2)
    g = G(x1 + SR)
    left = rrect(x0, -OV, x_mid + 64, CAP + OV, tl=250, tr=185, br=185, bl=250)
    left = left.difference(window(x0 + WC + w_o / 2 - round(4 * K), w_o, CFL, 368, CAP - CTA, base="round"))
    right = rrect(x_mid, 0, x1, CAP, R, R, R, R)
    g.add(unary_union([left, right]))
    g.cut(box(x_mid + VC, m1, x1 + 20, CAP - HB))
    g.cut(box(x_mid + VC, HB, x1 + 20, m0))
    g.cut(box(x1 - 44, m0 - 10, x1 + 20, m1 + 10))
    g.add(corbel(x_mid + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x_mid + VC, HB, 1, 1, 66))
    return g


@glyph("œ")
def low_oe():
    x0 = SR
    w_l = WL - round(8 * K)
    door_o = round(168 + 54 * (1 - K))
    door_e = round(172 + 54 * (1 - K))
    x_mid = x0 + w_l + door_o
    x1 = x_mid + V + door_e + w_l
    g = G(x1 + SR)
    left = rrect(x0, -OV, x_mid + V, XH + OV, tl=200, tr=130, br=130, bl=200)
    left = left.difference(window(x0 + w_l + door_o / 2, door_o, FL, 248, XH - TA + 4, base="round"))
    right = rrect(x_mid, -OV, x1, XH + OV, tl=130, tr=200, br=200, bl=130)
    cx_e = x_mid + V + door_e / 2
    y_eye = round(292 - 48 * (1 - K))
    m_bot = round(FL + 52 * K * K)
    m_top = y_eye - round(92 * K)
    mr = min(27, max(8, (m_top - m_bot) // 2))
    m_bl = min(m_top - m_bot - mr, round(mr + 140 * (1 - K)))
    right = right.difference(window(cx_e, door_e, y_eye, y_eye + 46, XH - TA + 4))
    right = right.difference(rrect(x_mid + V + round(34 * K), m_bot, x1 + 20, m_top, tl=mr, bl=m_bl))
    g.add(unary_union([left, right]))
    return g


@glyph("ß")
def eszett():
    x0 = SB
    ow = round(472 * WS)
    rw = round(132 * K + 14 * (1 - K))
    x1 = x0 + ow
    g = G(x1 + SR)
    upper = rrect(x0, round(366 - 30 * K), x1 - 24, ASC,
                  tl=round(215 * (0.84 + 0.16 * K)), tr=round(175 * K + 20 * (1 - K)),
                  br=round(125 * K + 16 * (1 - K)), bl=R)
    lower = rrect(x0, 0, x1, round(366 + 30 * K),
                  tl=R, tr=round(140 * K + 16 * (1 - K)), br=round(180 * K + 18 * (1 - K)), bl=R)
    g.add(unary_union([upper, lower]))
    uw = (x1 - 24) - (x0 + V) - rw
    lw = x1 - (x0 + V) - rw
    g.cut(window(x0 + V + uw / 2, uw, round(366 + 54 * K), 515, ASC - round(86 * K)))
    g.cut(window(x0 + V + lw / 2, lw, round(96 * K + 14 * (1 - K)), 195, round(366 - 58 * K)))
    g.cut(box(x0 + V, -20, x0 + V + round(84 + 24 * (1 - K)), round(110 * K + 10 + 14 * (1 - K))))
    return g


@glyph("Ð")
def cap_eth():
    x0 = 68
    ow = round(546 * WS)
    x1 = x0 + ow
    iw = ow - VC - WC
    th = round(104 * K)
    g = G(x1 + SR)
    g.add(rrect(x0, 0, x1, CAP, tl=R, tr=250, br=250, bl=R))
    g.cut(window(x0 + VC + iw / 2, iw, CFL, 370, CAP - CTA, base="round"))
    g.add(rrect(12, 350 - th // 2, x0 + VC + 84, 350 + (th - th // 2), R, R, R, R))
    return g


@glyph("ð")
def low_eth():
    g = G(0)
    x1 = bowl(g, SR)
    cx = (SR + x1) / 2
    pts = arc(cx - 116, 436, x1 - HX * (1.0 if K == 1.0 else 0.84) - (cx - 116), 322, 0, 84)
    if K < 1.0:
        pts = [(pts[0][0], 290)] + pts
    g.raw(pts, scale=0.84)
    th = round(72 * K)
    bar = rrect(cx - 52, 644 - th // 2, x1 + 12, 644 + (th - th // 2), R, R, R, R)
    g.add(affinity.rotate(bar, 22, origin=(cx + 76, 644)))
    g.adv = x1 + SR
    return g


@glyph("Þ")
def cap_thorn():
    x0 = SB + 6
    ow = round(478 * WS)
    rw = round(132 * K)
    x1 = x0 + ow
    iw = ow - VC - rw
    g = G(x1 + SR)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 124, x1, CAP - 110, tl=R, tr=175, br=175, bl=R))
    g.cut(window(x0 + VC + iw / 2, iw, round(124 + 94 * K), 300, CAP - 110 - round(82 * K), base="round"))
    return g


@glyph("þ")
def low_thorn():
    g = G(0)
    x1 = bowl(g, SB, side="left")
    minaret(g, SB)
    stem(g, SB, DESC, 10)
    g.adv = x1 + SR
    return g


@glyph("Ł")
def cap_lslash():
    x0 = 64
    arm = round(226 * WS)
    th = round(92 * K)
    g = G(x0 + VC + arm + 24)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 0, x0 + VC + arm, HB, R, R, R, R))
    g.add(corbel(x0 + VC, HB, 1, 1, 112))
    bar = rrect(10, 366 - th // 2, x0 + VC + 76, 366 + (th - th // 2), R, R, R, R)
    g.add(affinity.rotate(bar, 22, origin=(x0 + VC / 2, 366)))
    return g


@glyph("ł")
def low_lslash():
    x0 = 62
    th = round(88 * K)
    g = G(x0 * 2 + V)
    minaret(g, x0)
    bar = rrect(10, 304 - th // 2, x0 + V + 52, 304 + (th - th // 2), R, R, R, R)
    g.add(affinity.rotate(bar, 22, origin=(x0 + V / 2, 304)))
    return g
