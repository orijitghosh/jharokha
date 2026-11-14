"""Build the Jharokha release kit: posters and social images.

    python promo.py            every poster  -> promo/*.png (pages in promo/src)
    python promo.py hero mela  only those posters

Each poster is a small web page with the font embedded, photographed by
Chrome (or Edge) without a window. Run make.py first so the font is current.
"""
import base64
import os
import subprocess
import sys
import tempfile

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
TTF = os.path.join(HERE, "fonts", "Jharokha-Regular.ttf")
WOFF = os.path.join(HERE, "fonts", "Jharokha-Regular.woff")
OUT = os.path.join(HERE, "promo")
BROWSERS = [r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"]

MAROON, DEEP, SAFFRON, ORANGE = "#5c1020", "#3d0914", "#ffb627", "#e2572b"
IVORY, INDIGO, TEAL, PINK = "#f8eedb", "#171a45", "#0c5a5a", "#ee7b93"

_font = TTFont(TTF)
_cmap, _hmtx = _font.getBestCmap(), _font["hmtx"]


def units(text):
    """Width of a line in em (ignores kerning). Fails on a missing letter."""
    for ch in text:
        if ord(ch) not in _cmap:
            raise SystemExit(f"Jharokha has no glyph for {ch!r} (in {text!r})")
    return sum(_hmtx[_cmap[ord(ch)]][0] for ch in text) / _font["head"].unitsPerEm


def fit(text, width, most=10000):
    """Font size in px that makes `text` exactly `width` wide."""
    return min(width / units(text), most)


def j(text, size, x, top, color, extra=""):
    """A line of Jharokha. `top` is where the capital letters' tops sit."""
    units(text)
    # with line-height 1 the baseline is 0.8 em below the box top, caps 0.7 em tall
    return (f'<div class="j" style="font-size:{size:.1f}px;left:{x:.0f}px;top:{top - 0.1 * size:.0f}px;'
            f'color:{color};{extra}">{text}</div>')


def small(text, x, top, color, extra=""):
    return f'<div class="s" style="left:{x}px;top:{top}px;color:{color};{extra}">{text}</div>'


def arcade(w, h, size, color, bottom=0):
    """A row of the letter m: a block with onion-arch doorways, as a border."""
    n = int(w / (units("m") * size)) + 3
    return (f'<div class="j" style="font-size:{size}px;left:-{size * 0.05:.0f}px;top:{h - bottom - 0.8 * size:.0f}px;'
            f'color:{color};letter-spacing:-{size * 0.1:.1f}px;white-space:nowrap">{"m" * n}</div>')


# ------------------------------------------------------------------ posters
def hero():
    w, h = 1200, 1800
    a = 1240
    ax = (w - units("A") * a) / 2
    word = fit("Jharokha", 900)
    body = (f'<div style="position:absolute;left:{w / 2 - 430}px;top:300px;width:860px;height:860px;border-radius:50%;'
            f'background:radial-gradient(circle at 50% 38%,{SAFFRON},{ORANGE} 78%)"></div>'
            + j("A", a, ax, 330, IVORY)
            + small("Jharokha Regular", 80, 70, SAFFRON)
            + small("Version 1.000 &nbsp;/&nbsp; 2026", 0, 70, SAFFRON, f"right:80px;left:auto")
            + j("Jharokha", word, (w - 900) / 2, 1290, SAFFRON)
            + small("A display typeface built like Mughal architecture", 0, 1500, IVORY,
                    f"width:{w}px;text-align:center")
            + arcade(w, h, 190, ORANGE))
    return w, h, f"background:radial-gradient(circle at 50% 40%,{MAROON},{DEEP} 85%)", body


def banner():
    w, h = 1600, 900
    word = fit("Jharokha", 1240)
    body = (small("A new display typeface", 0, 96, PINK, f"width:{w}px;text-align:center")
            + j("Jharokha", word, (w - 1240) / 2, 190, SAFFRON)
            + small("Onion-arch doorways &nbsp;/&nbsp; bud windows &nbsp;/&nbsp; minaret domes", 0, 560, IVORY,
                    f"width:{w}px;text-align:center")
            + arcade(w, h, 230, PINK))
    return w, h, f"background:{INDIGO}", body


def square():
    w, h = 1080, 1080
    aa = 700
    ax = (w - units("Aa") * aa) / 2
    body = (j("Aa", aa, ax, 150, MAROON)
            + j("Jharokha", 104, 70, 890, MAROON)
            + small("New display<br>typeface", 0, 900, MAROON, "right:70px;left:auto;text-align:right;line-height:1.7"))
    return w, h, f"background:{SAFFRON}", body


def alphabet():
    w, h = 1200, 1800
    rows = [("ABCDEFGHI", MAROON), ("JKLMNOPQR", ORANGE), ("STUVWXYZ", TEAL),
            ("abcdefghijklm", INDIGO), ("nopqrstuvwxyz", MAROON),
            ("0123456789", ORANGE), ("&#8377;&amp;@?!%#*", TEAL)]
    plain = ["ABCDEFGHI", "JKLMNOPQR", "STUVWXYZ", "abcdefghijklm", "nopqrstuvwxyz", "0123456789", "₹&@?!%#*"]
    lines = ""
    for (text, color), raw in zip(rows, plain):
        size = fit(raw, 1040, most=210)
        lines += f'<div class="jf" style="font-size:{size:.1f}px;color:{color}">{text}</div>'
    body = (j("Jharokha", 96, 80, 84, MAROON)
            + small("Regular &nbsp;/&nbsp; 210 glyphs", 0, 112, MAROON, "right:80px;left:auto")
            + f'<div style="position:absolute;left:80px;top:230px;width:1040px;height:1400px;display:flex;'
              f'flex-direction:column;justify-content:space-between">{lines}</div>'
            + small("Capitals, lowercase, figures, punctuation, the rupee, and accents for European languages "
                    "and Sanskrit in Latin letters", 80, 1700, MAROON, "width:1040px;line-height:1.7;letter-spacing:.2em"))
    return w, h, f"background:{IVORY}", body


def anatomy():
    w, h = 1800, 1200
    parts = [("h", "Door", "n, m, h and r stand on a pointed onion-arch doorway. Turn it over and it is u."),
             ("o", "Bud", "Round letters are solid blocks with a window shaped like a lotus bud."),
             ("i", "Dome", "Tall stems end in a small onion dome, and so do the dots and the full stop."),
             ("A", "Cusps", "The doorways of A, H and M are scalloped, and A carries a pointed finial.")]
    body = j("Built like a building", 104, 90, 92, IVORY) + small("Jharokha Regular", 0, 122, SAFFRON, "right:90px;left:auto")
    col = (w - 180) / 4
    for k, (glyph, name, text) in enumerate(parts):
        x = 90 + k * col
        size = 560
        gx = x + (col - 40 - units(glyph) * size) / 2
        body += (j(glyph, size, gx, 330, SAFFRON)
                 + f'<div style="position:absolute;left:{x:.0f}px;top:800px;width:{col - 40:.0f}px;height:3px;background:{IVORY};opacity:.45"></div>'
                 + j(name, 58, x, 838, IVORY)
                 + f'<div class="t" style="left:{x:.0f}px;top:925px;width:{col - 70:.0f}px;color:{IVORY}">{text}</div>')
    return w, h, f"background:{TEAL}", body


def cities():
    w, h = 1200, 1800
    rows = [("DILLI", MAROON, SAFFRON), ("Jaipur", PINK, MAROON), ("AGRA", IVORY, INDIGO),
            ("Lucknow", TEAL, IVORY), ("KOLKATA", SAFFRON, MAROON), ("Mumbai", INDIGO, PINK),
            ("Hyderabad", ORANGE, IVORY)]
    bands = []
    for text, bg, fg in rows:
        size = fit(text, 1080, most=330)
        hang = any(c in "gjpqy" for c in text)
        bands.append([text, bg, fg, size, size * (1.16 if hang else 0.96)])
    total = sum(b[4] for b in bands)
    if total > h:
        for b in bands:
            b[3] *= h / total
            b[4] *= h / total
        total = h
    spare = (h - total) / len(bands)
    body, y = "", 0
    for text, bg, fg, size, bh in bands:
        bh += spare
        body += (f'<div style="position:absolute;left:0;top:{y:.0f}px;width:{w}px;height:{bh + 1:.0f}px;background:{bg}"></div>'
                 + j(text, size, 60, y + spare / 2 + 0.13 * size, fg))
        y += bh
    return w, h, f"background:{MAROON}", body


def sanskrit():
    w, h = 1200, 1800
    words = [("Rāmāyaṇa", MAROON), ("Mahābhārata", INDIGO), ("Kṛṣṇa", MAROON), ("Śiva Gaṇeśa", INDIGO), ("Aṣṭāṅga", MAROON)]
    lines = ""
    for text, color in words:
        size = fit(text, 1040, most=300)
        lines += f'<div class="jf" style="font-size:{size:.1f}px;color:{color};line-height:1.22">{text}</div>'
    body = (small("Jharokha reads Sanskrit in Latin letters", 80, 84, MAROON)
            + f'<div style="position:absolute;left:80px;top:150px;width:1040px;height:1330px;display:flex;'
              f'flex-direction:column;justify-content:space-between">{lines}</div>'
            + j("āīūṛṝḷṅñṭḍṇśṣḥṁ", fit("āīūṛṝḷṅñṭḍṇśṣḥṁ", 1040), 80, 1560, IVORY)
            + small("Every dot is a small onion dome", 80, 1716, MAROON))
    return w, h, f"background:{PINK}", body


def mela():
    w, h = 1200, 1800
    big = fit("Monsoon", 1040)
    mela_size = fit("MELA", 1040)
    y2 = 170 + big * 0.92
    y3 = y2 + mela_size * 0.82
    body = (small("Sample setting &nbsp;/&nbsp; Jharokha Regular", 80, 80, MAROON)
            + j("Monsoon", big, 80, 170, MAROON)
            + j("MELA", mela_size, 80, y2, IVORY)
            + f'<div style="position:absolute;left:0;top:{y3:.0f}px;width:{w}px;height:{h - y3:.0f}px;background:{INDIGO}"></div>'
            + j("14 to 16 August 2026", fit("14 to 16 August 2026", 1040), 80, y3 + 90, SAFFRON)
            + j("Chai, chaat & music", fit("Chai, chaat & music", 1040), 80, y3 + 262, PINK)
            + j("Dilli Haat", fit("Dilli Haat", 1040), 80, y3 + 440, IVORY)
            + j("Entry ₹50", 104, 80, y3 + 700, SAFFRON)
            + j("From 4 pm", 104, 0, y3 + 700, SAFFRON, "right:80px;left:auto")
            + arcade(w, h, 170, ORANGE))
    return w, h, f"background:{ORANGE}", body


POSTERS = {"hero": hero, "banner": banner, "square": square, "alphabet": alphabet,
           "anatomy": anatomy, "cities": cities, "sanskrit": sanskrit, "mela": mela}
FILES = {"hero": "poster-1-hero", "alphabet": "poster-2-alphabet", "anatomy": "poster-3-anatomy",
         "cities": "poster-4-cities", "sanskrit": "poster-5-sanskrit", "mela": "poster-6-sample-mela",
         "square": "social-square", "banner": "banner-wide"}


def page(w, h, bg, body):
    data = base64.b64encode(open(WOFF, "rb").read()).decode("ascii")
    return f"""<!doctype html><meta charset="utf-8">
<style>
@font-face {{ font-family: J; src: url("data:font/woff;base64,{data}") format("woff"); }}
* {{ margin: 0; box-sizing: border-box; }}
html, body {{ width: {w}px; height: {h}px; overflow: hidden; }}
body {{ position: relative; {bg}; }}
.j {{ position: absolute; font-family: J; line-height: 1; white-space: nowrap; font-kerning: normal; }}
.jf {{ font-family: J; line-height: 1; white-space: nowrap; }}
.s {{ position: absolute; font: 600 21px "Segoe UI", Arial, sans-serif; letter-spacing: .3em; text-transform: uppercase; }}
.t {{ position: absolute; font: 400 23px/1.5 "Segoe UI", Arial, sans-serif; opacity: .9; }}
</style>
{body}
"""


def shoot(html_path, png_path, w, h):
    browser = next((b for b in BROWSERS if os.path.exists(b)), None)
    if not browser:
        raise SystemExit("Chrome or Edge is needed to photograph the posters")
    profile = tempfile.mkdtemp(prefix="jharokha-promo-")
    subprocess.run([browser, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    "--force-device-scale-factor=1", f"--user-data-dir={profile}",
                    f"--window-size={w},{h}", "--virtual-time-budget=3000",
                    f"--screenshot={png_path}", "file:///" + html_path.replace("\\", "/")],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == "__main__":
    names = sys.argv[1:] or list(POSTERS)
    os.makedirs(os.path.join(OUT, "src"), exist_ok=True)
    for name in names:
        w, h, bg, body = POSTERS[name]()
        html_path = os.path.join(OUT, "src", FILES[name] + ".html")
        open(html_path, "w", encoding="utf-8").write(page(w, h, bg, body))
        png_path = os.path.join(OUT, FILES[name] + ".png")
        shoot(html_path, png_path, w, h)
        print(f"{name}: {png_path}")
