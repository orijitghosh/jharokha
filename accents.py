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
from engine import CAP, G, XH, rrect
from letters import GLYPHS, OV, R, SB, V, dome, glyph, stem

# Western European letters, then the letters used to write Indian languages
# in Latin script (IAST / ISO 15919), then a few Central European ones.
COVER = ("ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏÑÒÓÔÕÖÙÚÛÜÝàáâãäåçèéêëìíîïñòóôõöùúûüýÿ"
         "ĀāĒēĪīŌōŪūṚṛṜṝḶḷṄṅÑñṬṭḌḍṆṇŚśṢṣḤḥṀṁṂṃ"
         "ĆćČčŃńŠšŞşŹźŻżŽž")

GAP_LOW, GAP_CAP = 40, 30     # air between a letter and the mark above it
BELOW = -OV - 38              # top of a mark under the baseline


def _stroke(pts, scale):
    return G(0).s(pts, scale=scale).geometry()


def _acute():
    return Polygon([(-58, 0), (10, 0), (92, 142), (-26, 142)])


def _grave():
    return affinity.scale(_acute(), xfact=-1, origin=(0, 0))


def _circumflex():
    return Polygon([(-132, 0), (-56, 0), (0, 64), (56, 0), (132, 0), (0, 146)])


def _caron():
    return affinity.scale(_circumflex(), yfact=-1, origin=(0, 73))


def _dieresis():
    return dome(-72, 0, 96).union(dome(72, 0, 96))


def _dot():
    return dome(0, 0, 112)


def _macron():
    return rrect(-124, 22, 124, 104, R, R, R, R)


def _tilde():
    return _stroke([(-136, 24), (-62, 104, 46), (62, 30, 46), (136, 110)], 0.56)


def _ring():
    return Point(0, 80).buffer(80, 32).difference(Point(0, 80).buffer(30, 32))


def _cedilla():
    # a short heavy tail, drawn like the comma so it stays clear at this weight
    return Polygon([(-40, 20), (44, 20), (44, -64), (-8, -156), (-70, -156), (-22, -64), (-40, -64)])


# combining mark -> (shape, where): "above", "below", or "hang" (joined on)
MARKS = {
    "̀": (_grave, "above"), "́": (_acute, "above"),
    "̂": (_circumflex, "above"), "̃": (_tilde, "above"),
    "̄": (_macron, "above"), "̇": (_dot, "above"),
    "̈": (_dieresis, "above"), "̊": (_ring, "above"),
    "̌": (_caron, "above"), "̣": (_dot, "below"),
    "̧": (_cedilla, "hang"),
}

# where a mark below sits when the letter is not symmetrical
STEM_X = {"r": SB + V / 2}


def _dotless_i():
    g = G(SB * 2 + V)
    stem(g, SB, 0, XH)
    return g


def _compose(ch):
    parts = unicodedata.normalize("NFD", ch)
    base, marks = parts[0], parts[1:]

    def make():
        above = [m for m in marks if MARKS[m][1] == "above"]
        src = _dotless_i() if base == "i" and above else GLYPHS[base]()
        geo = src.geometry()
        x0, _, x1, top = geo.bounds
        cx = (x0 + x1) / 2
        g = G(src.adv).add(geo)
        y = top + (GAP_CAP if base.isupper() else GAP_LOW)
        for m in marks:
            fn, where = MARKS[m]
            shape = fn()
            if where == "above":
                if base.isupper():                      # flatter over capitals
                    shape = affinity.scale(shape, yfact=0.84, origin=(0, 0))
                g.add(affinity.translate(shape, cx, y))
                y = shape.bounds[3] + y + 26            # the next mark stacks on top
            elif where == "below":
                h = shape.bounds[3]
                g.add(affinity.translate(shape, STEM_X.get(base, cx), BELOW - h))
            else:
                g.add(affinity.translate(shape, cx, 0))
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
        g.add(letters.diag(x1 - 40, y1 + 46, x0 + 40, y0 - 46, 74))
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
