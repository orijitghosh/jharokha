JHAROKHA
Version 1.000, November 2026
Designed by Arijit Ghosh (https://orijitghosh.github.io/)

A display typeface in three weights. Latin letters built like Mughal
architecture: onion-arch doorways, bud-shaped windows, minaret domes.

IN THE DOWNLOAD
  Jharokha-Regular.ttf     weight 400 — subheads, menus, small display
  Jharokha-Bold.ttf        weight 700 — headings, buttons, signage
  Jharokha-Black.ttf       weight 900 — heavy poster and title slab
  Jharokha-*.woff2         for websites (smallest)
  Jharokha-*.woff          fallback for older browsers
  specimen.html            open in a browser to try all three weights
  OFL.txt                  the licence

WHAT IT COVERS (227 glyphs per weight)
  A-Z, a-z, 0-9, punctuation and symbols, ₹ $ € £
  Western, Northern and Central European letters and accents
  (including AE, OE, eszett, eth, thorn, L with stroke, C S Z N carons)
  Letters for Sanskrit and other Indian languages in Latin script
  (a i u with macron, r l n t d s h m with dots, and so on)

HOW TO USE IT
  Black is built for big sizes (24 px / 18 pt and larger): posters,
  book covers, headlines, logos and signs.
  Bold and Regular open up the doorways and windows so the letters
  stay legible down to 18 px.

  On a website:
    @font-face {
      font-family: "Jharokha";
      font-weight: 400;
      src: url("Jharokha-Regular.woff2") format("woff2"),
           url("Jharokha-Regular.woff") format("woff");
    }
    @font-face {
      font-family: "Jharokha";
      font-weight: 700;
      src: url("Jharokha-Bold.woff2") format("woff2"),
           url("Jharokha-Bold.woff") format("woff");
    }
    @font-face {
      font-family: "Jharokha";
      font-weight: 900;
      src: url("Jharokha-Black.woff2") format("woff2"),
           url("Jharokha-Black.woff") format("woff");
    }
    h1 { font-family: "Jharokha", sans-serif; font-weight: 900; }

LICENCE
  SIL Open Font License 1.1 (see OFL.txt). In short: you may use the
  font for anything, personal or commercial, and you may modify and
  share it, as long as it stays under this licence, keeps the copyright
  notice, and is not sold on its own.
