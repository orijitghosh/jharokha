"""Build Jharokha: font files (Regular, Bold, Black), proof sheets, specimen and zip.

    python make.py                 all 3 weights + proofs/*.png + Jharokha-1.000.zip
    python make.py "Some words"    all 3 weights + proofs/proof.png with those lines
"""
import base64
import os
import re
import sys
import unicodedata
import zipfile

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.ttLib import TTFont, newTable
from PIL import Image, ImageDraw, ImageFont

import accents
import build
import letters

WEIGHTS = [
    ("Regular", 400, 0.60),
    ("Bold", 700, 0.79),
    ("Black", 900, 1.00),
]

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


def finish(ttf, weight_class):
    """Add kerning and the name records, then save TTF, WOFF and WOFF2."""
    font = TTFont(ttf)
    # kerning is written in 1000-unit ems; the file's grid is build.FINE times finer
    kern = re.sub(r"-\d+(?=;)", lambda v: str(int(v.group()) * build.FINE), _kern_fea())
    addOpenTypeFeaturesFromString(font, kern)
    name = font["name"]
    for name_id, text in ((0, "Copyright 2026 Arijit Ghosh (https://orijitghosh.github.io/)"),
                          (13, "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
                               "This license is available with a FAQ at: https://openfontlicense.org"),
                          (14, "https://openfontlicense.org"),
                          (9, "Arijit Ghosh"),
                          (12, "https://orijitghosh.github.io/"),
                          (10, "A display face built like Mughal architecture: "
                               "onion-arch doorways, bud-shaped windows, minaret domes.")):
        name.setName(text, name_id, 3, 1, 0x409)
    # No hinting in this font: ask Windows to smooth it at every size and
    # not snap the outlines to the pixel grid (which makes stems wobble).
    font["OS/2"].recalcUnicodeRanges(font)
    font["OS/2"].ulCodePageRange1 = 0b11          # Latin 1 and Latin 2
    font["OS/2"].usWeightClass = weight_class
    gasp = newTable("gasp")
    gasp.version = 1
    gasp.gaspRange = {0xFFFF: 0x000A}
    font["gasp"] = gasp
    font.save(ttf)
    font.flavor = "woff"
    font.save(ttf[:-4] + ".woff")
    font.flavor = "woff2"
    font.save(ttf[:-4] + ".woff2")


def embed(woff2_by_weight):
    """Put all three weights inside specimen.html so the page works on its own."""
    page = os.path.join(build.HERE, "specimen.html")
    html = open(page, encoding="utf-8").read()
    rules = ["/* @FONT-FACES */"]
    for wclass, path in woff2_by_weight.items():
        data = base64.b64encode(open(path, "rb").read()).decode("ascii")
        rules.append(f'  @font-face {{ font-family: "Jharokha"; font-weight: {wclass}; '
                     f'src: url("data:font/woff2;base64,{data}") format("woff2"); }}')
    rules.append("  /* /@FONT-FACES */")
    block = "\n".join(rules)
    html = re.sub(r"/\* @FONT-FACES \*/.*?/\* /@FONT-FACES \*/", lambda _: block, html, count=1, flags=re.S)
    open(page, "w", encoding="utf-8").write(html)


def weights_proof(ttfs, out_path):
    """Render a side-by-side specimen comparing Regular, Bold and Black."""
    pad = 44
    ink, maroon, paper = (38, 24, 20), (122, 30, 36), (250, 243, 230)
    rows = []
    for style, wclass, _ in WEIGHTS:
        f_big = ImageFont.truetype(ttfs[style], 96)
        f_med = ImageFont.truetype(ttfs[style], 48)
        f_tag = ImageFont.truetype(ttfs["Bold"], 22)
        rows.append((f"{style.upper()} {wclass}", f_tag, f_big, f_med))

    headline = "Jharokha — Chandni Chowk"
    subline = "ABCDEFGHIJKLM  abcdefghijklm  0123456789 ₹$€£  Rāmāyaṇa"
    small_text = "Regular 400 at 20 px: Old Delhi doorways, lotus-bud windows & minaret domes stay open at small sizes."
    f_small = ImageFont.truetype(ttfs["Regular"], 20)

    max_w = max(
        max(r[2].getlength(headline) for r in rows),
        max(r[3].getlength(subline) for r in rows),
        f_small.getlength(small_text),
    )
    w = int(max_w) + pad * 2
    h = pad * 2 + len(rows) * 222 + 56
    img = Image.new("RGB", (w, h), paper)
    d = ImageDraw.Draw(img)
    y = pad
    for label, f_tag, f_big, f_med in rows:
        d.text((pad, y), label, font=f_tag, fill=maroon)
        d.text((pad, y + 32), headline, font=f_big, fill=ink)
        d.text((pad, y + 144), subline, font=f_med, fill=ink)
        y += 222
    d.line([(pad, y + 6), (w - pad, y + 6)], fill=(210, 194, 172), width=2)
    d.text((pad, y + 24), small_text, font=f_small, fill=maroon)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path)


def pack():
    """Zip up what people download."""
    here = build.HERE
    files = []
    for style, _, _ in WEIGHTS:
        for ext in (".ttf", ".woff", ".woff2"):
            files.append(f"fonts/Jharokha-{style}{ext}")
    files += ["fonts/README.txt", "specimen.html", "OFL.txt"]
    with zipfile.ZipFile(os.path.join(here, "Jharokha-1.000.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        for f in files:
            z.write(os.path.join(here, f), "Jharokha/" + os.path.basename(f))


if __name__ == "__main__":
    ttfs, woff2s = {}, {}
    for style, wclass, k in WEIGHTS:
        letters.set_weight(k)
        ttf = os.path.join(build.HERE, "fonts", f"Jharokha-{style}.ttf")
        n = build.build(ttf, "letters", style=style, weight_class=wclass)
        finish(ttf, wclass)
        ttfs[style] = ttf
        woff2s[wclass] = ttf[:-4] + ".woff2"
        print(f"{n} glyphs -> {ttf}")
    embed(woff2s)
    proofs = os.path.join(build.HERE, "proofs")
    if sys.argv[1:]:
        lines = sys.argv[1:]
        f_list = [(s, ImageFont.truetype(ttfs[s], 108)) for s, _, _ in WEIGHTS]
        pad, lh = 36, 138
        mw = max(f.getlength(t) for _, f in f_list for t in lines)
        img = Image.new("RGB", (int(mw) + pad * 2, pad * 2 + lh * len(lines) * len(f_list)), PAPER)
        d = ImageDraw.Draw(img)
        y = pad
        for t in lines:
            for _, f in f_list:
                d.text((pad, y), t, font=f, fill=INK)
                y += lh
        os.makedirs(proofs, exist_ok=True)
        img.save(os.path.join(proofs, "proof.png"))
    else:
        blk = ttfs["Black"]
        build.proof(blk, CHARSET, os.path.join(proofs, "charset.png"), size=92, pad=36, ink=INK, paper=PAPER)
        build.proof(blk, ACCENTS, os.path.join(proofs, "accents.png"), size=92, pad=36, ink=INK, paper=PAPER)
        build.proof(blk, SAMPLE, os.path.join(proofs, "sample.png"), size=104, pad=36,
                    ink=(122, 30, 36), paper=(250, 243, 230))
        weights_proof(ttfs, os.path.join(proofs, "weights.png"))
        pack()
