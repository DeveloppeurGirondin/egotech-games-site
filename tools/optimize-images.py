# -*- coding: utf-8 -*-
"""
Regenere les derives AVIF/WebP servis par le site a partir des PNG/JPG d'origine.

    python tools/optimize-images.py

Idempotent : un derive plus recent que sa source n'est pas reconstruit (--force pour tout refaire).
Seuls les derives sont references par index.html ; les PNG d'origine restent les masters.

Dependance : Pillow (pip install "Pillow>=11") pour l'ecriture AVIF.
"""
import glob
import os
import sys

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORCE = "--force" in sys.argv

SHOTS = "assets/screenshots/just-one-more-season"
SHOT_WIDTHS = (800, 1600)      # 800 = vignettes de la galerie, 1600 = visionneuse
PORTRAIT_WIDTHS = (320, 640)

AVIF_Q = 62   # valide sur les captures : le texte d'interface reste net
WEBP_Q = 80


def derive(src, widths):
    """Ecrit <src sans extension>-<largeur>.{avif,webp} a cote de la source."""
    base = os.path.splitext(src)[0]
    made = 0
    im = None
    for w in widths:
        targets = ["%s-%d.%s" % (base, w, ext) for ext in ("avif", "webp")]
        if not FORCE and all(os.path.exists(t) and os.path.getmtime(t) >= os.path.getmtime(src)
                             for t in targets):
            continue
        if im is None:
            im = Image.open(src).convert("RGB")
        if im.width < w:
            continue
        r = im.resize((w, round(w * im.height / im.width)), Image.LANCZOS)
        r.save(targets[0], quality=AVIF_Q, speed=5)
        r.save(targets[1], quality=WEBP_Q, method=6)
        made += 2
    return made


def main():
    os.chdir(ROOT)
    made = 0

    for lang in ("fr", "en"):
        for f in sorted(glob.glob("%s/%s/*.png" % (SHOTS, lang))):
            made += derive(f, SHOT_WIDTHS)

    made += derive("assets/alexandre/alexandre.jpg", PORTRAIT_WIDTHS)

    # Image Open Graph : les crawlers sociaux n'acceptent ni AVIF ni WebP, d'ou le JPEG.
    og = "assets/og-image.jpg"
    src = "%s/fr/01_open_space.png" % SHOTS
    if FORCE or not os.path.exists(og) or os.path.getmtime(og) < os.path.getmtime(src):
        Image.open(src).convert("RGB").resize((1200, 675), Image.LANCZOS) \
            .crop((0, 22, 1200, 652)) \
            .save(og, quality=84, optimize=True, progressive=True)
        made += 1

    served = sum(os.path.getsize(f)
                 for f in glob.glob("assets/**/*-*.avif", recursive=True)
                 + glob.glob("assets/**/*-*.webp", recursive=True))
    print("%d fichier(s) ecrit(s) ; %.1f Mo de derives servis" % (made, served / 1048576.0))


if __name__ == "__main__":
    main()
