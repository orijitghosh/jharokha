"""The letters: heavy blocks with Mughal architecture cut into them.

  door     n m h r stand on a pointed onion-arch doorway; u is one upside down
  bud      o a b d e g p q ... have a counter shaped like a lotus bud / dome window
  minaret  the tall stems of b d h k l end in an onion dome; the dot of i and j,
           and the full stop, are small domes
  cusps    the doorways of capital A, H and M are cusped (scalloped) arches
"""
from shapely import affinity
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

import engine
from engine import ASC, CAP, DESC, G, XH, arc, box, cusped, rrect, window

SB = 46          # side bearing beside a straight stem
SR = 34          # side bearing beside a round side
OV = 8           # how far round shapes pass the baseline and the top line
V = 150          # lowercase stem
VC = 160         # capital stem
HB = 124         # horizontal bar
R = 4            # tiny softening of square corners
TA = 80          # masonry left above the point of an arch
DOOR = 192       # width of a lowercase doorway
SPRING = 225     # height where a lowercase doorway starts to curve

HX, HY = engine.half()
T = XH - HY          # centre-line of a stroke along the top of lowercase
CT = CAP - HY        # ... along the top of capitals
BO = HY - OV         # centre-line of a round bottom
DB = DESC + HY       # centre-line of a descender's hook

GLYPHS = {}


def glyph(*chars):
    def reg(fn):
        for ch in chars:
            GLYPHS[ch] = fn
        return fn
    return reg


# ------------------------------------------------------------------ parts
def stem(g, x0, y0, y1, w=V):
    g.add(rrect(x0, y0, x0 + w, y1, R, R, R, R))


def minaret(g, x0, w=V):
    """A tall stem ending in an onion dome."""
    stem(g, x0, 0, 646, w)
    g.add(window(x0 + w / 2, w + 12, 615, 650, ASC + 54, swell=0.16))


def dome(cx, y0, w=150):
    """A free-standing onion dome: the dot of i, the full stop."""
    return window(cx, w, y0, y0 + w * 0.56, y0 + w * 1.42, base="round", swell=0.12)


def diag(xa, ya, xb, yb, wd):
    """A slanted bar from (xa, ya) to (xb, yb), cut level at both ends."""
    h = wd / 2
    return Polygon([(xa - h, ya), (xa + h, ya), (xb + h, yb), (xb - h, yb)])


def corbel(x, y, sx, sy, size):
    """A bracket filling the corner where a bar meets a stem, with the
    S-curved profile of the stone brackets under a jharokha balcony.
    (x, y) is the corner; sx = which way the bar runs, sy = the stem."""
    curve = engine._bez((x, y + sy * size), (x + sx * 0.05 * size, y + sy * 0.30 * size),
                        (x + sx * 0.70 * size, y + sy * 0.55 * size), (x + sx * 1.1 * size, y))
    return Polygon([(x - sx * 2, y - sy * 2), (x - sx * 2, y + sy * size)] + curve + [(x + sx * 1.1 * size, y - sy * 2)])


def cross(cx, w, wall, top, clip=None):
    """Two onion arches meeting point to point: X, x and the arms of K, k."""
    v = vee(cx, w, w - 2 * wall, top, 190)
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


def gate(g, x0, door_w=DOOR, stems=2, top=XH, spring=SPRING):
    """A block standing on onion-arch doorways. Returns its right edge."""
    step = door_w + V - (22 if stems > 2 else 0)
    x1 = x0 + V + step * (stems - 1) + (22 if stems > 2 else 0)
    g.add(rrect(x0, 0, x1, top, tl=R, tr=150, br=R, bl=R))
    x = x0 + V
    for _ in range(stems - 1):
        g.cut(window(x + door_w / 2, door_w, -20, spring, top - TA))
        x += step
    return x1


def bowl(g, x0, w=DOOR, side=None):
    """A rounded block with a bud-shaped counter; `side` ('left'/'right') is
    kept square where it meets a stem. Returns its right edge."""
    wl = V if side == "left" else 136
    wr = V if side == "right" else 136
    x1 = x0 + wl + w + wr
    rl = R if side == "left" else 205
    rr = R if side == "right" else 205
    # Beside a stem the block has a flat top and foot, so it keeps to the
    # lines like the stem does; only a fully round block overshoots them.
    ov = 0 if side else OV
    shape = rrect(x0, -ov, x1, XH + ov, tl=rl, tr=rr, br=rr, bl=rl)
    shape = shape.difference(window(x0 + wl + w / 2, w, 94, 250, XH - TA + 4, base="round"))
    g.add(shape)
    return x1


def hook(g, xs, top=150, reach=290):
    """A descender that turns left along the bottom line."""
    g.s([(xs, top), (xs, DB, 160), (xs - reach, DB)])


@glyph(" ", "\u00a0")
def space():
    return G(230)


# ---------------------------------------------------------------- capitals
@glyph("A")
def cap_A():
    x0, w = 30, 548
    cx = x0 + w / 2
    g = G(w + 2 * x0)
    g.add(window(cx, w, 0, 270, CAP + 54))
    g.cut(cusped(cx, 218, -20, 108, 258))
    g.cut(window(cx, 150, 354, 440, 572, base="round"))
    return g


@glyph("B")
def cap_B():
    x0 = SB + 6
    x1 = x0 + VC + 198 + 134
    upper = rrect(x0, 330, x1 - 24, CAP, tl=R, tr=165, br=120, bl=R)
    lower = rrect(x0, 0, x1, 384, tl=R, tr=135, br=180, bl=R)
    g = G(x1 + SR)
    g.add(unary_union([upper, lower]))
    g.cut(window(x0 + VC + 91, 182, 426, 500, CAP - 86))
    g.cut(window(x0 + VC + 102, 204, 100, 190, 298))
    return g


def c_body(x0, mouth):
    x1 = x0 + 150 + 230 + 150
    cx = (x0 + x1) / 2
    shape = rrect(x0, -OV, x1, CAP + OV, 250, 250, 250, 250)
    shape = shape.difference(window(cx, 230, 112, 360, CAP - 92, base="round"))
    shape = shape.difference(box(cx + 56, mouth[0], x1 + 20, mouth[1]))
    return shape, x1, cx


@glyph("C")
def cap_C():
    shape, x1, _ = c_body(SR, (236, 376))
    g = G(x1 + SR - 8)
    g.add(shape)
    return g


@glyph("D")
def cap_D():
    x0 = SB + 6
    x1 = x0 + VC + 236 + 150
    g = G(x1 + SR)
    g.add(rrect(x0, 0, x1, CAP, tl=R, tr=250, br=250, bl=R))
    g.cut(window(x0 + VC + 118, 236, 112, 370, CAP - 92, base="round"))
    return g


@glyph("E")
def cap_E():
    x0 = SB + 6
    x1 = x0 + VC + 240
    g = G(x1 + SR)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(box(x0 + VC, 424, x1 + 20, CAP - HB))
    g.cut(box(x0 + VC, HB, x1 + 20, 300))
    g.cut(box(x1 - 44, 290, x1 + 20, 434))
    g.add(corbel(x0 + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x0 + VC, HB, 1, 1, 66))
    return g


@glyph("F")
def cap_F():
    x0 = SB + 6
    x1 = x0 + VC + 230
    g = G(x1 + 20)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(box(x0 + VC, 424, x1 + 20, CAP - HB))
    g.cut(box(x0 + VC, -20, x1 + 20, 300))
    g.cut(box(x1 - 44, 290, x1 + 20, 434))
    g.add(corbel(x0 + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x0 + VC, 300, 1, -1, 84))
    return g


@glyph("G")
def cap_G():
    shape, x1, cx = c_body(SR, (352, 462))
    shape = unary_union([shape, rrect(cx - 12, 228, x1 - 60, 352, R, R, R, R)])
    g = G(x1 + SR)
    g.add(shape)
    return g


@glyph("H")
def cap_H():
    x0 = SB + 6
    x1 = x0 + VC + 204 + VC
    cx = (x0 + x1) / 2
    g = G(x1 + SB + 6)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(cusped(cx, 204, -20, 125, 296))
    g.cut(box(cx - 102, 420, cx + 102, CAP + 20))
    return g


@glyph("I")
def cap_I():
    x0 = SB + 6
    g = G(x0 * 2 + VC)
    stem(g, x0, 0, CAP, VC)
    return g


@glyph("J")
def cap_J():
    xs = 300
    g = G(xs + VC / 2 + SB + 6)
    g.s([(xs, CAP), (xs, HY, 190), (24, HY)])
    return g


@glyph("K")
def cap_K():
    x0 = SB + 6
    s = x0 + VC
    g = G(s + 338)
    stem(g, x0, 0, CAP, VC)
    g.add(cross(s - 4, 644, 186, CAP, clip=(s - 5, 0, s + 400, CAP)))
    return g


@glyph("L")
def cap_L():
    x0 = SB + 6
    g = G(x0 + VC + 250)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 0, x0 + VC + 226, HB, R, R, R, R))
    g.add(corbel(x0 + VC, HB, 1, 1, 112))
    return g


@glyph("M")
def cap_M():
    x0 = SB + 6
    x1 = x0 + VC + 172 + 150 + 172 + VC
    cx = (x0 + x1) / 2
    g = G(x1 + SB + 6)
    g.add(rrect(x0, 0, x1, CAP, R, R, R, R))
    g.cut(cusped(x0 + VC + 86, 172, -20, 170, 420))
    g.cut(cusped(x1 - VC - 86, 172, -20, 170, 420))
    g.cut(window(cx, 196, -20, 70, 392, flip=CAP / 2))
    return g


@glyph("N")
def cap_N():
    x0 = SB + 6
    x1 = x0 + VC + 236 + VC
    g = G(x1 + SB + 6)
    stem(g, x0, 0, CAP, VC)
    stem(g, x1 - VC, 0, CAP, VC)
    g.poly([(x0, CAP), (x0 + 196, CAP), (x1, 0), (x1 - 196, 0)])
    return g


def o_body(x0):
    x1 = x0 + 150 + 240 + 150
    cx = (x0 + x1) / 2
    shape = rrect(x0, -OV, x1, CAP + OV, 250, 250, 250, 250)
    return shape.difference(window(cx, 240, 112, 370, CAP - 92, base="round")), x1, cx


@glyph("O")
def cap_O():
    shape, x1, _ = o_body(SR)
    g = G(x1 + SR)
    g.add(shape)
    return g


@glyph("P")
def cap_P():
    x0 = SB + 6
    x1 = x0 + VC + 192 + 134
    g = G(x1 + 24)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 286, x1, CAP, tl=R, tr=180, br=180, bl=R))
    g.cut(window(x0 + VC + 96, 192, 392, 480, CAP - 86))
    return g


@glyph("Q")
def cap_Q():
    shape, x1, cx = o_body(SR)
    g = G(x1 + SR)
    g.add(shape)
    g.add(diag(cx + 70, 150, x1 - 10, -118, 136))
    return g


@glyph("R")
def cap_R():
    x0 = SB + 6
    x1 = x0 + VC + 192 + 134
    s = x0 + VC
    g = G(x1 + 34)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 292, x1, CAP, tl=R, tr=180, br=180, bl=R))
    g.cut(window(s + 96, 192, 396, 482, CAP - 86))
    g.add(cross(s - 10, 668, 190, 720, clip=(s - 10, 0, s + 420, 355)))
    return g


def s_path(cx, rx, top, bot):
    mid = (top + bot) / 2 + 9
    return (arc(cx, (top + mid) / 2, rx * 0.95, (top - mid) / 2, 24, 270)
            + arc(cx, (mid + bot) / 2, rx, (mid - bot) / 2, 90, -156)[1:])


@glyph("S")
def cap_S():
    cx = 266
    g = G(cx * 2 - 6)
    g.raw(s_path(cx, 162, CT + OV, BO))
    return g


@glyph("T")
def cap_T():
    x0, w = 18, 500
    g = G(w + 2 * x0)
    g.add(rrect(x0, CAP - HB, x0 + w, CAP, R, R, R, R))
    stem(g, x0 + w / 2 - VC / 2, 0, CAP, VC)
    g.add(corbel(x0 + w / 2 - VC / 2, CAP - HB, -1, -1, 92))
    g.add(corbel(x0 + w / 2 + VC / 2, CAP - HB, 1, -1, 92))
    return g


@glyph("U")
def cap_U():
    x0 = SB + 6
    x1 = x0 + VC + 204 + VC
    g = G(x1 + SB + 6)
    g.add(rrect(x0, -OV, x1, CAP, tl=R, tr=R, br=225, bl=225))
    g.cut(window((x0 + x1) / 2, 204, -20, 250, CAP - 104, flip=CAP / 2))
    return g


def vee(cx, w, inner, top, depth):
    """An upside-down onion arch: V, v and the halves of W, w."""
    out = window(cx, w, 0, 80, top + OV, flip=top / 2)
    return out.difference(window(cx, inner, -30, 80, top - depth, flip=top / 2))


@glyph("V")
def cap_V():
    w = 566
    g = G(w + 36)
    g.add(vee(18 + w / 2, w, 196, CAP, 190))
    return g


@glyph("W")
def cap_W():
    w, step = 470, 312
    g = G(w + step + 36)
    g.add(vee(18 + w / 2, w, 150, CAP, 200))
    g.add(vee(18 + w / 2 + step, w, 150, CAP, 200))
    return g


@glyph("X")
def cap_X():
    x0, w = 20, 548
    g = G(w + 2 * x0)
    g.add(cross(x0 + w / 2, w, 182, CAP))
    return g


@glyph("Y")
def cap_Y():
    x0, w = 14, 560
    cx = x0 + w / 2
    g = G(w + 2 * x0)
    v = vee(cx, w, w - 2 * 184, CAP, 190)
    g.add(affinity.scale(v, yfact=0.62, origin=(cx, CAP + OV)).intersection(box(0, 0, w + 2 * x0, CAP)))
    stem(g, cx - VC / 2, 0, 330, VC)
    return g


@glyph("Z")
def cap_Z():
    x0, x1 = 34, 34 + 470
    g = G(x1 + 34)
    g.add(box(x0, CAP - HB, x1, CAP))
    g.add(box(x0, 0, x1, HB))
    g.add(sway(x0 + 100, HB - 2, x1 - 100, CAP - HB + 2, 200))
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
    g.cut(box((SR + x1) / 2 + 44, 150, x1 + 20, 262))
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
    x1 = x0 + 136 + w + 136
    cx = (x0 + x1) / 2
    g = G(x1 + SR)
    g.add(rrect(x0, -OV, x1, XH + OV, 205, 205, 205, 205))
    g.cut(window(cx, w, 292, 338, XH - TA + 4))               # the eye
    g.cut(rrect(cx - 62, 146, x1 + 20, 200, tl=27, bl=27))   # the mouth
    return g


@glyph("f")
def f():
    xs = 40 + 62 + V / 2
    g = G(xs + 204)
    g.s([(xs, 0), (xs, ASC - HY, 150), (xs + 194, ASC - HY)])
    g.s([(20, T), (xs + 190, T)])
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
    x0 = 112
    xs = x0 + V / 2
    g = G(x0 + V + SB)
    g.s([(xs, XH), (xs, DB, 150), (xs - 196, DB)])
    g.add(dome(xs, XH + 58))
    return g


@glyph("k")
def k():
    s = SB + V
    g = G(s + 294)
    minaret(g, SB)
    g.add(cross(s - 4, 560, 166, XH, clip=(s - 5, 0, s + 400, XH)))
    return g


@glyph("l")
def l_():
    g = G(SB * 2 + V)
    minaret(g, SB)
    return g


@glyph("m")
def m():
    g = G(0)
    x1 = gate(g, SB, door_w=166, stems=3)
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
    x1 = gate(g, SB, door_w=150)
    g.cut(box(SB + V + 86, -20, x1 + 10, 318))
    g.adv = x1 + 14
    return g


@glyph("s")
def s():
    cx = 238
    g = G(cx * 2 - 6)
    g.raw(s_path(cx, 132, T + OV, BO))
    return g


@glyph("t")
def t():
    xs = 40 + 60 + V / 2
    g = G(xs + 252)
    g.s([(xs, 560), (xs, HY, 150), (xs + 206, HY)])
    g.s([(22, T), (xs + 216, T)])
    g.add(window(xs, V, 540, 592, 716))
    return g


def u_body(g, x0):
    x1 = x0 + V + DOOR + V
    g.add(rrect(x0, 0, x1, XH, tl=R, tr=R, br=R, bl=150))
    g.cut(window((x0 + x1) / 2, DOOR, -20, SPRING, XH - TA, flip=XH / 2))
    return x1


@glyph("u")
def u():
    g = G(0)
    x1 = u_body(g, SB)
    g.adv = x1 + SB
    return g


@glyph("v")
def v():
    w = 462
    g = G(w + 32)
    g.add(vee(16 + w / 2, w, 156, XH, 150))
    return g


@glyph("w")
def w_():
    w, step = 400, 262
    g = G(w + step + 32)
    g.add(vee(16 + w / 2, w, 124, XH, 158))
    g.add(vee(16 + w / 2 + step, w, 124, XH, 158))
    return g


@glyph("x")
def x():
    x0, w = 18, 468
    g = G(w + 2 * x0)
    g.add(cross(x0 + w / 2, w, 164, XH))
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
    x0, x1 = 30, 30 + 404
    g = G(x1 + 30)
    g.add(box(x0, XH - HB, x1, XH))
    g.add(box(x0, 0, x1, HB))
    g.add(sway(x0 + 92, HB - 2, x1 - 92, XH - HB + 2, 184))
    return g


# ------------------------------------------------------------------ digits
@glyph("0")
def d0():
    x0 = SR
    x1 = x0 + 140 + 190 + 140
    g = G(x1 + SR)
    g.add(rrect(x0, -OV, x1, CAP + OV, 215, 215, 215, 215))
    g.cut(window((x0 + x1) / 2, 196, 112, 365, CAP - 92, base="round"))
    return g


@glyph("1")
def d1():
    g = G(372)
    stem(g, 150, 0, CAP, VC)
    flag = window(150 + VC, 2 * (VC + 88), 436, 470, CAP + 4)       # half an onion arch
    g.add(flag.intersection(box(0, 436, 150 + VC, CAP)))
    return g


@glyph("2")
def d2():
    cx = 250
    g = G(500)
    g.raw(arc(cx, 470, 142, CT + OV - 470, 172, -42) + [(120, 96)])
    g.add(box(46, 0, 462, HB))
    return g


@glyph("3")
def d3():
    cx, top, mid = 240, CT + OV, 368
    g = G(494)
    g.raw(arc(cx, (top + mid) / 2, 142, (top - mid) / 2, 158, -90)
          + arc(cx, (mid + BO) / 2, 152, (mid - BO) / 2, 90, -156)[1:])
    g.cut(box(-200, 290, 168, 450))      # trim the middle bar so it stays inside the 3
    return g


@glyph("4")
def d4():
    g = G(552)
    stem(g, 306, 0, CAP, VC)
    g.add(box(28, 168, 526, 168 + HB))
    g.add(diag(120, 280, 378, CAP, 176))
    return g


@glyph("5")
def d5():
    cx, cy = 246, 240
    g = G(516)
    g.add(box(72, CAP - HB, 448, CAP))
    g.add(box(72, 372, 72 + V, CAP))
    g.add(corbel(72 + V, CAP - HB, 1, -1, 70))
    g.raw(arc(cx, cy, 160, cy - BO, 146, -152))
    return g


@glyph("6")
def d6():
    x0 = SR
    x1 = x0 + 136 + DOOR + 136
    g = G(x1 + SR)
    shape = rrect(x0, -OV, x1, 436, 205, 205, 205, 205)
    g.add(shape.difference(window((x0 + x1) / 2, DOOR, 94, 240, 352, base="round")))
    g.s([(x0 + 75, 372), (x0 + 75, CT, 210), (x1 - 66, CT)])
    return g


@glyph("7")
def d7():
    g = G(492)
    g.add(box(30, CAP - HB, 468, CAP))
    g.add(sway(196, 0, 376, CAP - HB + 2, 184))
    return g


@glyph("8")
def d8():
    x0 = SR
    x1 = x0 + 452
    cx = (x0 + x1) / 2
    g = G(x1 + SR)
    g.add(rrect(x0, -OV, x1, 388, 190, 190, 190, 190))
    g.add(rrect(x0 + 24, 336, x1 - 24, CAP + OV, 176, 176, 176, 176))
    g.cut(window(cx, 200, 92, 200, 306, base="round"))
    g.cut(window(cx, 172, 416, 515, CAP - 86, base="round"))
    return g


@glyph("9")
def d9():
    x0 = SR
    x1 = x0 + 136 + DOOR + 136
    g = G(x1 + SR)
    shape = rrect(x0, 264, x1, CAP + OV, 205, 205, 205, 205)
    g.add(shape.difference(window((x0 + x1) / 2, DOOR, 360, 505, CAP - 90, base="round")))
    g.s([(x1 - 75, 345), (x1 - 75, HY, 210), (x0 + 66, HY)])
    return g


# ------------------------------------------------------------- punctuation
PW = 150 + 2 * SB      # advance of a dot


def comma_shape(x0, y=0):
    return Polygon([(x0, y + 150), (x0 + 150, y + 150), (x0 + 150, y + 10),
                    (x0 + 52, y - 150), (x0 - 12, y - 150), (x0 + 62, y), (x0, y)])


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
    g.poly([(cx - 82, CAP), (cx + 82, CAP), (cx + 52, 262), (cx - 52, 262)])
    g.add(dome(cx, -OV))
    return g


@glyph("?")
def question():
    cx = 226
    g = G(452)
    g.raw(arc(cx, 500, 138, CT + OV - 500, 168, -52) + [(cx, 318), (cx, 262)])
    g.add(dome(cx, -OV))
    return g


def tick(x0):
    return Polygon([(x0, CAP), (x0 + 140, CAP), (x0 + 104, CAP - 236), (x0 + 36, CAP - 236)])


def curly_close(x0):
    s = affinity.scale(comma_shape(0, 0), xfact=0.92, yfact=0.92, origin=(0, 150))
    return affinity.translate(s, x0, CAP - 150)


def curly_open(x0):
    s = affinity.rotate(curly_close(0), 180, origin=(69, CAP - 138))
    return affinity.translate(s, x0, 0)


@glyph("'")
def quote():
    return G(140 + 2 * 40).add(tick(40))


@glyph('"')
def dquote():
    return G(140 * 2 + 44 + 2 * 40).add(tick(40)).add(tick(40 + 184))


@glyph("\u2018")
def quote_l():
    return G(138 + 72).add(curly_open(36))


@glyph("\u2019")
def quote_r():
    return G(138 + 72).add(curly_close(36))


@glyph("\u201c")
def dquote_l():
    return G(138 * 2 + 34 + 72).add(curly_open(36)).add(curly_open(36 + 172))


@glyph("\u201d")
def dquote_r():
    return G(138 * 2 + 34 + 72).add(curly_close(36)).add(curly_close(36 + 172))


@glyph("\u2026")
def ellipsis():
    w, step = 126, 186
    g = G(SB * 2 + w + step * 2)
    for k in range(3):
        g.add(dome(SB + w / 2 + k * step, -OV, w))
    return g


@glyph("\u2022")
def bullet():
    return G(PW + 24).add(dome((PW + 24) / 2, 210, 156))


@glyph("\u00b0")
def degree():
    r_out, r_in = 122, 48
    cx, cy = 32 + r_out, CAP + OV - r_out
    return G(cx * 2).add(Point(cx, cy).buffer(r_out, 32).difference(Point(cx, cy).buffer(r_in, 32)))


@glyph("-")
def hyphen():
    return G(260 + 2 * SB).add(box(SB, 236, SB + 260, 236 + HB))


@glyph("\u2013")
def endash():
    return G(430 + 2 * SB).add(box(SB, 236, SB + 430, 236 + HB))


@glyph("\u2014")
def emdash():
    return G(760 + 2 * 30).add(box(30, 236, 790, 236 + HB))


@glyph("_")
def underscore():
    return G(520).add(box(0, -160, 520, -60))


@glyph("(")
def paren_l():
    g = G(340)
    g.raw(arc(SB + 75 + 250, 270, 250, 560, 116, 244))
    return g


@glyph(")")
def paren_r():
    g = G(340)
    g.raw(arc(340 - (SB + 75 + 250), 270, 250, 560, 64, -64))
    return g


@glyph("[")
def bracket_l():
    g = G(SB + 290)
    g.add(box(SB, -200, SB + V, 780)).add(box(SB, 670, SB + 264, 780)).add(box(SB, -200, SB + 264, -90))
    return g


@glyph("]")
def bracket_r():
    g = G(SB + 290)
    x1 = 290
    g.add(box(x1 - V, -200, x1, 780)).add(box(x1 - 264, 670, x1, 780)).add(box(x1 - 264, -200, x1, -90))
    return g


@glyph("/")
def slash():
    return G(430).add(diag(92, -110, 338, 780, 150))


@glyph("\\")
def backslash():
    return G(430).add(diag(338, -110, 92, 780, 150))


@glyph("|")
def pipe():
    return G(2 * 70 + 130).add(box(70, -200, 200, 780))


@glyph("+")
def plus():
    return G(480).add(box(40, 236, 440, 236 + HB)).add(box(240 - 66, 98, 240 + 66, 498))


@glyph("=")
def equal():
    return G(480).add(box(40, 336, 440, 446)).add(box(40, 150, 440, 260))


@glyph("*")
def asterisk():
    g = G(420)
    bar = box(210 - 40, 540 - 150, 210 + 40, 540 + 150)
    for ang in (0, 60, 120):
        g.add(affinity.rotate(bar, ang, origin=(210, 540)))
    return g


@glyph("#")
def hash_():
    g = G(610)
    g.add(diag(170, 0, 250, CAP, 122)).add(diag(370, 0, 450, CAP, 122))
    g.add(box(50, 436, 580, 546)).add(box(30, 160, 560, 270))
    return g


@glyph("%")
def percent():
    g = G(770)

    def ring(x0, y0):
        r = rrect(x0, y0, x0 + 270, y0 + 316, 132, 132, 132, 132)
        return r.difference(window(x0 + 135, 74, y0 + 84, y0 + 150, y0 + 240, base="round"))

    g.add(ring(36, CAP + OV - 316)).add(ring(464, -OV))
    g.add(diag(268, 0, 502, CAP, 122))
    return g


@glyph("$")
def dollar():
    cx = 266
    g = G(cx * 2 - 6)
    g.raw(s_path(cx, 162, CT + OV, BO))
    g.add(box(cx - 46, -96, cx + 46, CAP + 96))
    return g


@glyph("&")
def ampersand():
    x0 = SR
    x1 = x0 + 452
    cx = (x0 + x1) / 2
    g = G(x1 + 150)
    g.add(rrect(x0, -OV, x1, 388, 190, 190, 190, 190))
    g.add(rrect(x0 + 34, 336, x1 - 34, CAP + OV, 172, 172, 172, 172))
    g.cut(window(cx, 200, 92, 200, 306, base="round"))
    g.cut(window(cx, 150, 420, 510, CAP - 88, base="round"))
    leg = diag(cx + 96, 236, x1 + 60, 0, 156)
    arm = box(x1 - 70, 236, x1 + 126, 236 + 110)
    g.add(unary_union([leg, arm]))
    return g


@glyph("@")
def at():
    cx, cy, rr = 446, 250, 366
    g = G(892)
    ax = cx + 118
    u = (rr - 118) / 2
    path = [(ax, cy + 120)] + arc(ax + u, cy - 70, u, u * 0.9, 180, 360) + arc(cx, cy, rr, rr, -11, 296)[1:]
    g.raw(path, scale=0.62)
    inner = rrect(cx - 176, cy - 176, cx + 156, cy + 176, tl=156, tr=R, br=R, bl=156)
    inner = inner.difference(window(cx - 26, 100, cy - 100, cy - 20, cy + 100, base="round"))
    g.add(inner)
    return g


@glyph("₹")
def rupee():
    x0, x1 = 40, 500
    g = G(x1 + 40)
    g.add(box(x0, CAP - HB, x1, CAP))
    g.add(box(x0, CAP - HB - 190, x1, CAP - 190 - 14))
    g.s([(x0, CT), (360, CT, 149), (360, CT - 298, 149), (x0 + 60, CT - 298)])
    g.add(diag(x0 + 150, CT - 298 - HY + 40, x1 - 96, 0, 188))
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
    return G(300).add(Polygon([(40, CAP + 70), (190, CAP + 70), (252, CAP - 110), (168, CAP - 110)]))


def brace(x0):
    """A bracket with a pointed nub on its back."""
    return unary_union([box(x0, -200, x0 + 130, 780), box(x0, 680, x0 + 220, 780),
                        box(x0, -200, x0 + 220, -100),
                        Polygon([(x0 + 4, 400), (x0 - 86, 290), (x0 + 4, 180)])])


@glyph("{")
def brace_l():
    return G(380).add(brace(130))


@glyph("}")
def brace_r():
    return G(380).add(affinity.scale(brace(130), xfact=-1, origin=(190, 0)))


@glyph("€")
def euro():
    shape, x1, cx = c_body(76, (216, 474))
    g = G(x1 + SR - 8)
    g.add(shape)
    g.add(rrect(12, 380, cx + 108, 464, R, R, R, R))
    g.add(rrect(12, 226, cx + 84, 310, R, R, R, R))
    return g


@glyph("£")
def pound():
    x0 = 40
    xs = x0 + 92 + VC / 2
    g = G(520)
    g.s([(xs, HB), (xs, CT, 150), (456, CT)])
    g.add(rrect(x0, 0, 476, HB, R, R, R, R))
    g.add(rrect(x0, 290, 396, 388, R, R, R, R))
    return g


# ---------------------------------------------------- extended European Latin
@glyph("Æ")
def cap_AE():
    x0, x_stem = 26, 388
    x1 = x_stem + VC + 228
    g = G(x1 + SR)
    arch = window(x_stem + 70, (x_stem + 70 - x0) * 2, 0, 270, CAP + 120)
    g.add(arch.intersection(box(x0, 0, x_stem + VC, CAP)))
    g.add(rrect(x_stem, 0, x1, CAP, R, R, R, R))
    g.cut(cusped(x0 + 240, 168, -20, 118, 268))
    g.cut(window(x0 + 266, 108, 352, 434, 554, base="round"))
    g.cut(box(x_stem + VC, 424, x1 + 20, CAP - HB))
    g.cut(box(x_stem + VC, HB, x1 + 20, 300))
    g.cut(box(x1 - 44, 290, x1 + 20, 434))
    g.add(corbel(x_stem + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x_stem + VC, HB, 1, 1, 66))
    return g


@glyph("æ")
def low_ae():
    x0 = SR
    x_mid = x0 + 308
    door_e = 172
    x1 = x_mid + V + door_e + 128
    g = G(x1 + SR)
    a_part = rrect(x0, -OV, x_mid + 60, XH + OV, tl=185, tr=110, br=110, bl=180)
    a_part = a_part.difference(window(x0 + 202, 152, 76, 155, 258, base="round"))
    a_part = a_part.difference(rrect(x0 - 20, 330, x_mid - 16, 386, tr=27, br=27))
    e_part = rrect(x_mid, -OV, x1, XH + OV, tl=110, tr=200, br=200, bl=110)
    cx_e = x_mid + V + door_e / 2
    e_part = e_part.difference(window(cx_e, door_e, 292, 338, XH - TA + 4))
    e_part = e_part.difference(rrect(cx_e - 52, 146, x1 + 20, 200, tl=27, bl=27))
    g.add(unary_union([a_part, e_part]))
    return g


@glyph("Œ")
def cap_OE():
    x0, w_o = SR, 212
    x_mid = x0 + 146 + w_o + 32
    x1 = x_mid + VC + 224
    g = G(x1 + SR)
    left = rrect(x0, -OV, x_mid + 64, CAP + OV, tl=250, tr=185, br=185, bl=250)
    left = left.difference(window(x0 + 146 + w_o / 2, w_o, 112, 368, CAP - 92, base="round"))
    right = rrect(x_mid, 0, x1, CAP, R, R, R, R)
    g.add(unary_union([left, right]))
    g.cut(box(x_mid + VC, 424, x1 + 20, CAP - HB))
    g.cut(box(x_mid + VC, HB, x1 + 20, 300))
    g.cut(box(x1 - 44, 290, x1 + 20, 434))
    g.add(corbel(x_mid + VC, CAP - HB, 1, -1, 66))
    g.add(corbel(x_mid + VC, HB, 1, 1, 66))
    return g


@glyph("œ")
def low_oe():
    x0, w_l, door_o, door_e = SR, 128, 168, 172
    x_mid = x0 + w_l + door_o
    x1 = x_mid + V + door_e + 128
    g = G(x1 + SR)
    left = rrect(x0, -OV, x_mid + V, XH + OV, tl=200, tr=130, br=130, bl=200)
    left = left.difference(window(x0 + w_l + door_o / 2, door_o, 94, 248, XH - TA + 4, base="round"))
    right = rrect(x_mid, -OV, x1, XH + OV, tl=130, tr=200, br=200, bl=130)
    cx_e = x_mid + V + door_e / 2
    right = right.difference(window(cx_e, door_e, 292, 338, XH - TA + 4))
    right = right.difference(rrect(cx_e - 52, 146, x1 + 20, 200, tl=27, bl=27))
    g.add(unary_union([left, right]))
    return g


@glyph("ß")
def eszett():
    x0 = SB
    x1 = x0 + V + 190 + 132
    g = G(x1 + SR)
    upper = rrect(x0, 336, x1 - 24, ASC, tl=215, tr=175, br=125, bl=R)
    lower = rrect(x0, 0, x1, 396, tl=R, tr=140, br=180, bl=R)
    g.add(unary_union([upper, lower]))
    g.cut(window(x0 + V + 86, 172, 420, 515, ASC - 86))
    g.cut(window(x0 + V + 95, 190, 96, 195, 308))
    g.cut(box(x0 + V, -20, x0 + V + 84, 110))
    return g


@glyph("Ð")
def cap_eth():
    x0 = 68
    x1 = x0 + VC + 236 + 150
    g = G(x1 + SR)
    g.add(rrect(x0, 0, x1, CAP, tl=R, tr=250, br=250, bl=R))
    g.cut(window(x0 + VC + 118, 236, 112, 370, CAP - 92, base="round"))
    g.add(rrect(12, 298, x0 + VC + 84, 298 + 104, R, R, R, R))
    return g


@glyph("ð")
def low_eth():
    g = G(0)
    x1 = bowl(g, SR)
    cx = (SR + x1) / 2
    pts = arc(cx - 116, 436, x1 - 68 - (cx - 116), 322, 0, 84)
    g.raw(pts, scale=0.84)
    bar = rrect(cx - 52, 608, x1 + 12, 680, R, R, R, R)
    g.add(affinity.rotate(bar, 22, origin=(cx + 76, 644)))
    g.adv = x1 + SR
    return g


@glyph("Þ")
def cap_thorn():
    x0 = SB + 6
    x1 = x0 + VC + 186 + 132
    g = G(x1 + SR)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 124, x1, CAP - 110, tl=R, tr=175, br=175, bl=R))
    g.cut(window(x0 + VC + 93, 186, 218, 300, CAP - 192, base="round"))
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
    g = G(x0 + VC + 250)
    stem(g, x0, 0, CAP, VC)
    g.add(rrect(x0, 0, x0 + VC + 226, HB, R, R, R, R))
    g.add(corbel(x0 + VC, HB, 1, 1, 112))
    bar = rrect(10, 320, x0 + VC + 76, 412, R, R, R, R)
    g.add(affinity.rotate(bar, 22, origin=(x0 + VC / 2, 366)))
    return g


@glyph("ł")
def low_lslash():
    x0 = 62
    g = G(x0 * 2 + V)
    minaret(g, x0)
    bar = rrect(10, 260, x0 + V + 52, 348, R, R, R, R)
    g.add(affinity.rotate(bar, 22, origin=(x0 + V / 2, 304)))
    return g
