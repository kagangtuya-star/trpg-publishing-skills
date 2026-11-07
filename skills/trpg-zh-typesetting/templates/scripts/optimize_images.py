"""Make print-weight copies of the placed figures (assets/optimized/), so the PDF stays a sane size.

- opaque images -> JPEG q86; images with real transparency -> PNG (RGBA, optimized)
- downsampled to ~220 dpi at the largest size they can be placed at
Originals in assets/original/img and assets/processed/maps are left untouched;
render.py uses the optimized copy when it exists.
"""
import json, os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT

FIGS = json.load(open(os.path.join(ROOT, 'src/config/figures.json'), encoding='utf-8'))
OUT = os.path.join(ROOT, 'assets/optimized')
# longest side in px at ~220 dpi for the largest placement of each kind
MAXPX = {'scene': 1500, 'fullpage': 2000, 'map': 2000, 'figure': 1100, 'portrait': 800}

def target(src):
    return os.path.join(OUT, os.path.splitext(os.path.basename(src))[0])

def main():
    os.makedirs(OUT, exist_ok=True)
    before = after = 0
    for fid, f in FIGS.items():
        if not f.get('use') or f['kind'] == 'handout-bg': continue
        src = os.path.join(ROOT, f['src'])
        im = Image.open(src); im.load()
        lim = MAXPX.get(f['kind'], 1500)
        if max(im.size) > lim:
            k = lim / max(im.size)
            im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
        alpha = im.mode in ('RGBA', 'LA', 'P') and im.convert('RGBA').getchannel('A').getextrema()[0] < 250
        if alpha:
            out = target(src) + '.png'; im.convert('RGBA').save(out, optimize=True)
        else:
            out = target(src) + '.jpg'; im.convert('RGB').save(out, quality=86, optimize=True, progressive=False)
        for ext in ('.png', '.jpg'):          # drop a stale copy with the other extension
            o = target(src) + ext
            if o != out and os.path.exists(o): os.remove(o)
        before += os.path.getsize(src); after += os.path.getsize(out)
    print(f'optimized figures: {before / 1e6:.1f} MB -> {after / 1e6:.1f} MB')

if __name__ == '__main__':
    main()
