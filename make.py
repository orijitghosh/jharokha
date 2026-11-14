"""Build Jharokha: font files, proof sheets, the specimen page and the zip.

    python make.py                 fonts + proofs/charset.png + proofs/sample.png
    python make.py "Some words"    fonts + proofs/proof.png with those lines
"""
import os
import re
import sys
import unicodedata
import zipfile

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont, newTable

import accents
import build
import letters

CHARSET = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "abcdefghijklm", "nopqrstuvwxyz",
           "0123456789 ₹$€£%", ".,:;!?'\"\u2018\u2019\u201c\u201d\u2026\u2022\u00b0",
           "-\u2013\u2014_()[]{}/\\| +=*#&@<>^~`"]
ACCENTS = ["ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏ", "ÑÒÓÔÕÖØÙÚÛÜÝŸ", "àáâãäåçèéêëìíîïñ", "òóôõöøùúûüýÿ ¡¿",
           "ÆæŒœ ß Ðð Þþ Łł",
           "ĀĒĪŌŪ ṚṜḶṄṬḌṆŚṢḤṀṂ", "āēīōū ṛṝḷṅṭḍṇśṣḥṁṃ", "ĆČŃŠŞŹŻŽ ćčńšşźżž",
           "Rāmāyaṇa Maṇḍala Gaṅgā", "Mahābhārata Prāṇāyāma", "Café señor über façade"]
SAMPLE = ["Jharokha", "Namaste Dilli", "Chandni Chowk", "Taj Mahal, Agra",
          "Quick brown fox", "jumps over lazy dogs", "₹ 1,234,567.89 & more"]
INK, PAPER = (28, 28, 32), (250, 247, 240)
EXTRA_BASE = {"Ø": "O", "Œ": "O", "ø": "o", "œ": "o", "æ": "a", "Ł": "L"}


def _kern_fea():
    """Build kerning rules covering base letters and their accented forms.
    Tall lowercase (b d h i j k l t, ð) stays out so domes never hit T or Y."""
    fam_all = {ch: [ch] for ch in letters.GLYPHS if ch.isascii() and ch.isalpha()}
    fam_flat = {ch: [ch] for ch in fam_all}
    fam_above = {ch: [] for ch in fam_all}
    for ch in letters.GLYPHS:
        if ch.isascii():
            continue
        parts = unicodedata.normalize("NFD", ch)
        base = EXTRA_BASE.get(ch) or parts[0]
        if base not in fam_all:
            continue
        fam_all[base].append(ch)
        has_above = any(accents.MARKS.get(m, (None, None))[1] == "above" for m in parts[1:])
        if base.islower() and has_above:
            fam_above[base].append(ch)
        else:
            fam_flat[base].append(ch)

    def cls(chars, pool=fam_all):
        return "[" + " ".join(build.glyph_name(c) for b in chars for c in pool[b]) + "]"

    return f"""
@low        = {cls("acdegoqs")};
@lowx_flat  = {cls("acdegoqsmnpruvwxyz", fam_flat)};
@lowx_above = {cls("acdegoqsmnpruvwxyz", fam_above)};
@tvwy       = {cls("TVWY")};
@stop       = [uni002E uni002C uni2026];
feature kern {{
    pos {cls("T")} @lowx_flat -96;
    pos {cls("T")} @lowx_above -52;
    pos {cls("F")} @low -30;
    pos {cls("P")} @low -28;
    pos {cls("VW")} @low -34;
    pos {cls("Y")} @lowx_flat -80;
    pos {cls("Y")} @lowx_above -46;
    pos {cls("TVWYFP")} @stop -96;
    pos {cls("rvwy")} @stop -50;
    pos {cls("A")} @tvwy -46;
    pos @tvwy {cls("A")} -46;
    pos {cls("L")} @tvwy -84;
    pos {cls("L")} {cls("vwy")} -40;
    pos {cls("K")} {cls("OCGQoce")} -24;
    pos {cls("f")} @low -18;
    pos {cls("r")} @low -14;
}} kern;
"""


def finish(ttf):
    """Add kerning and the name records, then save TTF, WOFF and WOFF2."""
    font = TTFont(ttf)
    # kerning is written in 1000-unit ems; the file's grid is build.FINE times finer
    kern = re.sub(r"-\d+(?=;)", lambda v: str(int(v.group()) * build.FINE), _kern_fea())
    addOpenTypeFeaturesFromString(font, kern)
    name = font["name"]
    for name_id, text in ((0, "Copyright 2026 Arijit Ghosh"),
                          (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                               "This license is available with a FAQ at: https://openfontlicense.org"),
                          (14, "https://openfontlicense.org"),
                          (9, "Arijit Ghosh"),
                          (10, "A heavy display face. Latin letters built like Mughal architecture: "
                               "onion-arch doorways, bud-shaped windows, minaret domes.")):
        name.setName(text, name_id, 3, 1, 0x409)
    # No hinting in this font: ask Windows to smooth it at every size and
    # not snap the outlines to the pixel grid (which makes stems wobble).
    # Say which scripts and code pages the font covers; some apps filter on it.
    font["OS/2"].recalcUnicodeRanges(font)
    font["OS/2"].ulCodePageRange1 = 0b11          # Latin 1 and Latin 2
    font["OS/2"].usWeightClass = 900
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000A}
    font["gasp"] = gasp
    font.save(ttf)
    font.flavor = "woff"
    font.save(ttf[:-4] + ".woff")
    font.flavor = "woff2"
    font.save(ttf[:-4] + ".woff2")
    embed(ttf[:-4] + ".woff")


def pack():
    """Zip up what people download."""
    here = build.HERE
    files = ["fonts/Jharokha-Regular.ttf", "fonts/Jharokha-Regular.woff",
             "fonts/Jharokha-Regular.woff2", "fonts/README.txt",
             "specimen.html", "OFL.txt"]
    with zipfile.ZipFile(os.path.join(here, "Jharokha-1.000.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(here, f), "Jharokha/" + os.path.basename(f))


def embed(woff):
    """Put the font inside specimen.html so the page works on its own."""
    import base64
    import re
    page = os.path.join(build.HERE, "specimen.html")
    data = base64.b64encode(open(woff, "rb").read()).decode("ascii")
    html = open(page, encoding="utf-8").read()
    face = '@font-face { font-family: "Jharokha"; src: url("data:font/woff;base64,%s") format("woff"); }' % data
    html = re.sub(r"@font-face \{[^}]*\}", lambda _: face, html, count=1)
    open(page, "w", encoding="utf-8").write(html)


if __name__ == "__main__":
    ttf = os.path.join(build.HERE, "fonts", "Jharokha-Regular.ttf")
    n = build.build(ttf, "letters")
    finish(ttf)
    print(f"{n} glyphs -> {ttf}")
    proofs = os.path.join(build.HERE, "proofs")
    if sys.argv[1:]:
        build.proof(ttf, sys.argv[1:], os.path.join(proofs, "proof.png"), size=120, pad=36, ink=INK, paper=PAPER)
    else:
        build.proof(ttf, CHARSET, os.path.join(proofs, "charset.png"), size=92, pad=36, ink=INK, paper=PAPER)
        build.proof(ttf, ACCENTS, os.path.join(proofs, "accents.png"), size=92, pad=36, ink=INK, paper=PAPER)
        build.proof(ttf, SAMPLE, os.path.join(proofs, "sample.png"), size=104, pad=36,
                    ink=(122, 30, 36), paper=(250, 243, 230))
        pack()
