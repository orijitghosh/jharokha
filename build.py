"""Build the font files and a proof image.   python build.py ["proof text" ...]"""
import importlib
import os
import sys

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from PIL import Image, ImageDraw, ImageFont

import engine

HERE = os.path.dirname(os.path.abspath(__file__))
FAMILY = "Jharokha"
STYLE = "Regular"
# The letters are drawn on a 1000-unit em. The font file uses a grid FINE
# times finer, so curves stay smooth when a letter fills a poster.
FINE = 4

NAMES = {" ": "space"}


def glyph_name(ch):
    if ch in NAMES:
        return NAMES[ch]
    if ch.isascii() and ch.isalnum():
        return ch if not ch.isdigit() else "d" + ch
    return "uni%04X" % ord(ch)


def build(out_path, glyphs_mod="letters"):
    mod = importlib.import_module(glyphs_mod)
    order, cmap, glyf, hmtx = [".notdef"], {}, {}, {}

    pen = TTGlyphPen(None)
    for pts in ([(60, 0), (60, 700), (440, 700), (440, 0)],
                [(110, 50), (390, 50), (390, 650), (110, 650)]):
        pts = [(x * FINE, y * FINE) for x, y in pts]
        pen.moveTo(pts[0])
        for p in pts[1:]:
            pen.lineTo(p)
        pen.closePath()
    glyf[".notdef"] = pen.glyph()
    hmtx[".notdef"] = (500 * FINE, 60 * FINE)

    for ch, fn in mod.GLYPHS.items():
        g = fn()
        name = glyph_name(ch)
        pen = TTGlyphPen(None)
        xmin = None
        for contour in g.contours():
            pts = [(round(x * FINE), round(y * FINE)) for x, y in contour]
            clean = [p for i, p in enumerate(pts) if p != pts[i - 1]]
            if len(clean) < 3:
                continue
            pen.moveTo(clean[0])
            for p in clean[1:]:
                pen.lineTo(p)
            pen.closePath()
            m = min(p[0] for p in clean)
            xmin = m if xmin is None else min(xmin, m)
        order.append(name)
        cmap[ord(ch)] = name
        glyf[name] = pen.glyph()
        hmtx[name] = (round(g.adv * FINE), xmin or 0)

    fb = FontBuilder(engine.UPM * FINE, isTTF=True)
    fb.setupGlyphOrder(order)
    fb.setupCharacterMap(cmap)
    fb.setupGlyf(glyf)
    fb.setupHorizontalMetrics(hmtx)
    fb.setupHorizontalHeader(ascent=900 * FINE, descent=-300 * FINE)
    # Windows will not install a font without a full name, a unique ID and
    # a PostScript name.
    fb.setupNameTable({"familyName": FAMILY, "styleName": STYLE,
                       "uniqueFontIdentifier": f"{FAMILY}-{STYLE}:1.000",
                       "fullName": f"{FAMILY} {STYLE}", "psName": f"{FAMILY}-{STYLE}",
                       "version": "Version 1.000"})
    fb.setupOS2(sTypoAscender=900 * FINE, sTypoDescender=-300 * FINE, sTypoLineGap=0,
                usWinAscent=940 * FINE, usWinDescent=300 * FINE,
                sxHeight=engine.XH * FINE, sCapHeight=engine.CAP * FINE,
                fsSelection=0x40, achVendID="NONE", fsType=0)
    fb.setupPost()
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    fb.save(out_path)
    return len(order) - 1


def proof(font_path, lines, out_path, size=150, pad=50,
          ink=(38, 24, 20), paper=(247, 240, 226)):
    font = ImageFont.truetype(font_path, size)
    line_h = int(size * 1.28)
    widths = [font.getlength(t) for t in lines]
    img = Image.new("RGB", (int(max(widths)) + pad * 2, line_h * len(lines) + pad * 2), paper)
    d = ImageDraw.Draw(img)
    for i, t in enumerate(lines):
        d.text((pad, pad + i * line_h), t, font=font, fill=ink)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)


# Run make.py to build the font and its proof sheets.
