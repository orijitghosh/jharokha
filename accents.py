"""Accented letters for Jharokha, composed from the base letters in letters.py.

Each accented letter is its base letter plus marks. Which marks go on which
letter comes from Unicode's own decomposition, so adding a letter is one
character in COVER below.

  dots       small onion domes (dieresis, dot above, dot below)
  circumflex a pointed arch
"""
import unicodedata

from shapely import affinity
from shapely.geometry import Point, Polygon

import letters
from engine import CAP, G, XH, cusped, rrect, window
from letters import GLYPHS, dome, stem

# Western European letters, then the letters used to write Indian languages
# in Latin script (IAST / ISO 15919), then a few Central European ones.
COVER = ("ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝŸàáâãäåçèéêëìíîïñòóôõöùúûüýÿ"
         "ĀāĒēĪīŌōŪūṚṛṜṝḶḷṄṅÑñṬṭḌḍṆṇŚśṢṣḤḥṀṁṂṃ"
         "ĆćČčŃńŠšŞşŹźŻżŽž")

GAP_LOW, GAP_CAP = 40, 30     # air between a letter and the mark above it
MIN_SB = 28                   # keep wide marks on I and i from touching neighbours
WIDE_MARKS = {"̂", "̃", "̄", "̈", "̌"}


def _stroke(pts, scale):
    return G(0).s(pts, scale=scale).geometry()


def _acute():
    k = letters.K
    b, t = round(34 * k), round(59 * k)
    h = round(142 * (0.85 + 0.15 * k))
    return Polygon([(-24 - b, 0), (-24 + b, 0), (33 + t, h), (33 - t, h)])


def _grave():
    return affinity.scale(_acute(), xfact=-1, origin=(0, 0))


def _circumflex():
    k = letters.K
    span = round(132 * (0.90 + 0.10 * k))
    fw = round(76 * k)
    h = round(146 * (0.88 + 0.12 * k))
    yi = h - round(82 * k)
    return Polygon([(-span, 0), (-span + fw, 0), (0, yi), (span - fw, 0), (span, 0), (0, h)])


def _caron():
    c = _circumflex()
    return affinity.scale(c, yfact=-1, origin=(0, c.bounds[3] / 2))


def _dieresis():
    k = letters.K
    dw = round(96 * (0.15 + 0.85 * k))
    dx = round(72 * (0.88 + 0.12 * k))
    return dome(-dx, 0, dw).union(dome(dx, 0, dw))


def _dot():
    return dome(0, 0, round(112 * (0.15 + 0.85 * letters.K)))


def _macron():
    k, r = letters.K, letters.R
    hw = round(124 * (0.90 + 0.10 * k))
    th = round(82 * k)
    return rrect(-hw, 22, hw, 22 + th, r, r, r, r)


def _tilde():
    return _stroke([(-136, 24), (-62, 104, 46), (62, 30, 46), (136, 110)], 0.56)


def _ring():
    k = letters.K
    ro = round(80 * (0.88 + 0.12 * k))
    ri = ro - round(50 * k)
    return Point(0, ro).buffer(ro, 32).difference(Point(0, ro).buffer(ri, 32))


def _cedilla():
    # a short heavy tail, drawn like the comma so it stays clear at every weight
    k = letters.K
    base = Polygon([(-40, 20), (44, 20), (44, -64), (-8, -156), (-70, -156), (-22, -64), (-40, -64)])
    return affinity.scale(base, xfact=k, yfact=0.80 + 0.20 * k, origin=(0, 20))


# combining mark -> (shape, where): "above", "below", or "hang" (joined on)
MARKS = {
    "̀": (_grave, "above"), "́": (_acute, "above"),
    "̂": (_circumflex, "above"), "̃": (_tilde, "above"),
    "̄": (_macron, "above"), "̇": (_dot, "above"),
    "̈": (_dieresis, "above"), "̊": (_ring, "above"),
    "̌": (_caron, "above"), "̣": (_dot, "below"),
    "̧": (_cedilla, "hang"),
}


def _dotless_i():
    g = G(letters.SB * 2 + letters.V)
    stem(g, letters.SB, 0, XH)
    return g


def _short_A():
    """Capital A with a slightly tucked finial so marks align with E, I, O, U."""
    k = letters.K
    x0 = round(30 + 8 * (1 - k))
    w = round(548 * letters.WS)
    cx = x0 + w / 2
    g = G(w + 2 * x0)
    g.add(window(cx, w, 0, 270, CAP + 16))
    g.cut(cusped(cx, w - 2 * round(165 * k), -20, 108, round(258 + 56 * (1 - k))))
    g.cut(window(cx, round(146 + 112 * (1 - k)), round(344 - 14 * (1 - k)),
                 round(424 + 22 * (1 - k)), round(548 + 66 * (1 - k)), base="round"))
    return g


def _compose(ch):
    parts = unicodedata.normalize("NFD", ch)
    base, marks = parts[0], parts[1:]

    def make():
        above = [m for m in marks if MARKS[m][1] == "above"]
        if base == "i" and above:
            src = _dotless_i()
        elif base == "A" and above:
            src = _short_A()
        else:
            src = GLYPHS[base]()
        geo = src.geometry()
        x0, _, x1, top = geo.bounds
        cx = (x0 + x1) / 2
        g = G(src.adv).add(geo)
        y = (CAP + 24) if (base == "A" and above) else (top + (GAP_CAP if base.isupper() else GAP_LOW))
        below = -letters.OV - 38
        for m in marks:
            fn, where = MARKS[m]
            shape = fn()
            if where == "above":
                if base in ("I", "i") and m in WIDE_MARKS:
                    shape = affinity.scale(shape, xfact=0.80, origin=(0, 0))
                if base.isupper():                      # flatter over capitals
                    shape = affinity.scale(shape, yfact=0.84, origin=(0, 0))
                g.add(affinity.translate(shape, cx, y))
                y = shape.bounds[3] + y + 26            # the next mark stacks on top
            elif where == "below":
                h = shape.bounds[3]
                sx = (letters.SB + letters.V / 2) if base == "r" else cx
                g.add(affinity.translate(shape, sx, below - h))
            else:
                g.add(affinity.translate(shape, cx, 0))
        full = g.geometry()
        bx0, _, bx1, _ = full.bounds
        pad = max(0, MIN_SB - bx0, MIN_SB - (g.adv - bx1))
        if pad > 0:
            return G(g.adv + 2 * pad).add(affinity.translate(full, pad, 0))
        return g
    return make


for _ch in COVER:
    if _ch not in GLYPHS:
        GLYPHS[_ch] = _compose(_ch)


def _slashed(base):
    def make():
        src = GLYPHS[base]()
        geo = src.geometry()
        x0, y0, x1, y1 = geo.bounds
        g = G(src.adv).add(geo)
        g.add(letters.diag(x1 - 40, y1 + 46, x0 + 40, y0 - 46, round(74 * letters.K)))
        return g
    return make


GLYPHS["Ø"] = _slashed("O")
GLYPHS["ø"] = _slashed("o")


def _turned(base):
    """¡ and ¿: the mark turned upside down, hanging from the x-height."""
    def make():
        src = GLYPHS[base]()
        geo = affinity.rotate(src.geometry(), 180, origin=(src.adv / 2, XH / 2))
        return G(src.adv).add(geo)
    return make


GLYPHS["¡"] = _turned("!")
GLYPHS["¿"] = _turned("?")
