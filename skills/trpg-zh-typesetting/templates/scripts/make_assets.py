"""Build reusable decorative assets from the original PDF art.

* body page frames (verso / recto per chapter) composed from the original frame,
  footer and side-tab pieces, with Chinese chapter labels baked into the side tab
* chapter opener spreads: original opener pages rendered with all English text removed
* cover / title-page backgrounds
Outputs to assets/processed/.
"""
import os, sys, json, io
import pymupdf
from PIL import Image, ImageDraw, ImageFont, ImageFilter
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT
from runtime import ART, BOOK, PAGE_W, PAGE_H

SRC = os.path.join(ROOT, 'input/original.pdf')
IMG = os.path.join(ROOT, 'assets/original/img')
OUT = os.path.join(ROOT, 'assets/processed')
FONTS = os.path.join(ROOT, 'assets/fonts')
CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
PAPER = tuple(ART['paper'])
S = 2.0   # px per pt  (=144 dpi)
W, H = PAGE_W, PAGE_H

meta = json.load(open(os.path.join(ROOT, 'work/extracted/images_meta.json')))
by_xref = {m['xref']: n for n, m in meta.items()}

def img_of(xref):
    return Image.open(os.path.join(IMG, by_xref[xref])).convert('RGBA')

def paste(canvas, xref, bbox):
    x0, y0, x1, y1 = bbox
    im = img_of(xref).resize((max(1, round((x1 - x0) * S)), max(1, round((y1 - y0) * S))), Image.LANCZOS)
    canvas.alpha_composite(im, (round(x0 * S), round(y0 * S)))

def paper():
    c = Image.new('RGBA', (int(W * S), int(H * S)), PAPER + (255,))
    # soft warm vignette
    v = Image.new('L', c.size, 0); d = ImageDraw.Draw(v)
    d.rectangle([60, 60, c.size[0] - 60, c.size[1] - 60], fill=255)
    v = v.filter(ImageFilter.GaussianBlur(120))
    tint = Image.new('RGBA', c.size, (225, 208, 178, 255))
    c = Image.composite(c, tint, v.point(lambda a: 150 + a * 105 // 255))
    return c.convert('RGBA')

def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name) if not name.startswith('/') else name, int(size * S))

def frame_verso():
    c = paper()
    for piece in ART['frame_verso']:
        paste(c, piece['xref'], piece['bbox'])
    c.convert('RGB').save(os.path.join(OUT, 'frame_verso.jpg'), quality=88)

def frame_recto(tag, label, number):
    c = paper()
    for piece in ART['frame_recto']:
        paste(c, piece['xref'], piece['bbox'])
    # Side-tab lettering is deliberately a per-book customization, not a fixed xref/coordinate.
    c.convert('RGB').save(os.path.join(OUT, f'frame_recto_{tag}.jpg'), quality=88)

def strip_text_render(pn, out, drop_xrefs=(), dpi=150, clip=None, lines=False):
    doc = pymupdf.open(SRC)
    page = doc[pn - 1]
    for b in page.get_text('dict')['blocks']:
        if b['type'] != 0: continue
        for l in b['lines']:
            for s in l['spans']:
                if s['text'].strip():
                    r = pymupdf.Rect(s['bbox'])
                    if lines: r.y1 += 3
                    page.add_redact_annot(r)
    page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_TOUCHED if lines else pymupdf.PDF_REDACT_LINE_ART_NONE, text=pymupdf.PDF_REDACT_TEXT_REMOVE)
    pix = page.get_pixmap(dpi=dpi, clip=clip)
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    im.save(os.path.join(OUT, out), quality=90)
    return im

def main():
    os.makedirs(OUT, exist_ok=True)
    frame_verso()
    frame_recto('front', BOOK['title'], None)
    for ch, c in CFG.items():
        if not ch.isdigit(): continue
        frame_recto(f'ch{ch}', c['title'], int(ch))
        pair = ART['openers'].get(ch, [None, None])
        for side, pn in zip(('a', 'b'), pair):
            name = f'opener_ch{ch}_{side}.jpg'
            if pn: strip_text_render(pn, name, lines=(side == 'b'))
            else: paper().convert('RGB').save(os.path.join(OUT, name), quality=88)
    # cover art & title-page art
    for key, name in [('cover_page', 'cover_art.jpg'), ('title_page', 'titlepage.jpg'), ('intro_page', 'intro_art.jpg')]:
        if ART.get(key): strip_text_render(ART[key], name)
        else: paper().convert('RGB').save(os.path.join(OUT, name), quality=88)
    print('assets ok')

if __name__ == '__main__':
    main()
