"""Build Jharokha: font files, proof sheets, the specimen page and the zip.

    python make.py                 fonts + proofs/charset.png + proofs/sample.png
    python make.py "Some words"    fonts + proofs/proof.png with those lines
"""
import os
import re
import sys
import zipfile

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont, newTable

import accents  # noqa: F401  (adds the accented letters to letters.GLYPHS)
import build

CHARSET = ["ABCDEFGHIJKLM", "NOPQRSTUVWXYZ", "abcdefghijklm", "nopqrstuvwxyz",
           "0123456789 ₹$%", ".,:;!?'\"-\u2013\u2014_()[]{}/\\|", "+=*#&@<>^~`"]
ACCENTS = ["ÀÁÂÃÄÅÇÈÉÊËÌÍÎÏ", "ÑÒÓÔÕÖØÙÚÛÜÝ", "àáâãäåçèéêëìíîïñ", "òóôõöøùúûüýÿ ¡¿",
           "ĀĒĪŌŪ ṚṜḶṄṬḌṆŚṢḤṀṂ", "āēīōū ṛṝḷṅṭḍṇśṣḥṁṃ", "ĆČŃŠŞŹŻŽ ćčńšşźżž",
           "Rāmāyaṇa Maṇḍala Gaṅgā", "Mahābhārata Prāṇāyāma", "Café señor über façade"]
SAMPLE = ["Jharokha", "Namaste Dilli", "Chandni Chowk", "Taj Mahal, Agra",
          "Quick brown fox", "jumps over lazy dogs", "₹ 1,234,567.89 & more"]
INK, PAPER = (28, 28, 32), (250, 247, 240)

# Pairs that need pulling together. Tall lowercase (b d h i j k l t) is left
# out on purpose: its domes would run into the capital's overhang.
KERN = """
@low   = [a c d e g o q s];
@lowx  = [a c d e g o q s m n p r u v w x y z];
@stop  = [uni002E uni002C];
feature kern {
    pos T @lowx -96;
    pos F @low -30;
    pos [V W] @low -34;
    pos Y @lowx -80;
    pos [T V W Y F P] @stop -96;
    pos [r v w y] @stop -50;
    pos A [T V W Y] -46;
    pos [T V W Y] A -46;
    pos L [T V W Y] -84;
    pos L [v w y] -40;
    pos K [O C G Q o c e] -24;
    pos f [a c d e g o q s] -18;
    pos r [a c d e g o q s] -14;
} kern;
"""


def finish(ttf):
    """Add kerning and the name records, then save TTF and WOFF."""
    font = TTFont(ttf)
    # kerning is written in 1000-unit ems; the file's grid is build.FINE times finer
    kern = re.sub(r"-\d+(?=;)", lambda v: str(int(v.group()) * build.FINE), KERN)
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
    embed(ttf[:-4] + ".woff")


def pack():
    """Zip up what people download."""
    here = build.HERE
    files = ["fonts/Jharokha-Regular.ttf", "fonts/Jharokha-Regular.woff", "fonts/README.txt",
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
