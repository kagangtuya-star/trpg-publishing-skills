"""Render maps from the original pages (raster + vector area codes), replacing the English
titles / legends with Chinese labels from src/config/maps.json.  Area codes (A1, B3a...) are kept.
Output: assets/processed/maps/<stem>.png
"""
import json, os, sys
import pymupdf
from PIL import Image, ImageDraw, ImageFont
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT

DPI = 220
MAPS = json.load(open(os.path.join(ROOT, 'src/config/maps.json'), encoding='utf-8'))
FONT = os.environ.get('TRPG_MAP_FONT', os.path.join(ROOT, 'assets/fonts/NotoSansSC-Bold.ttf'))
HAND = os.environ.get('TRPG_HAND_FONT', os.path.join(ROOT, 'assets/fonts/WenKaiSub-Medium.ttf'))

def main():
    out = os.path.join(ROOT, 'assets/processed/maps'); os.makedirs(out, exist_ok=True)
    for stem, m in MAPS.items():
        pn = int(stem[1:4])
        doc = pymupdf.open(os.path.join(ROOT, 'input/original.pdf'))
        page = doc[pn - 1]
        bb = pymupdf.Rect(m['bbox'])
        jobs = []
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                t = ''.join(s['text'] for s in l['spans']).strip()
                lr = pymupdf.Rect(l['bbox'])
                if not lr.intersects(bb): continue
                if t in m['labels'] and not m.get('keep_original'):
                    s0 = max(l['spans'], key=lambda s: len(s['text']))
                    jobs.append((lr, m['labels'][t] or '', s0['size'], s0['color'], s0['font']))
                    page.add_redact_annot(pymupdf.Rect(lr.x0 - 6, lr.y0 - 4, lr.x1 + 14, lr.y1 + 4))
                elif not lr.intersects(bb):
                    continue
        # text outside the map box (body text) must not be rendered: redact everything outside
        for b in page.get_text('dict')['blocks']:
            if b['type'] != 0: continue
            for l in b['lines']:
                lr = pymupdf.Rect(l['bbox'])
                if not (lr & bb).is_valid or (lr & bb).get_area() < lr.get_area() * 0.5:
                    page.add_redact_annot(lr)
        page.apply_redactions(images=pymupdf.PDF_REDACT_IMAGE_NONE, graphics=pymupdf.PDF_REDACT_LINE_ART_REMOVE_IF_COVERED)
        pix = page.get_pixmap(dpi=DPI, clip=bb)
        im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples).convert('RGBA')
        d = ImageDraw.Draw(im)
        k = DPI / 72
        handout = 'HANDOUT' in ' '.join(m['labels'])
        for lr, zh, size, color, fontname in jobs:
            if not zh: continue
            col = ((color >> 16) & 255, (color >> 8) & 255, color & 255)
            fpath = HAND if handout else FONT
            fs = size * k * (1.0 if handout else 1.05)
            f = ImageFont.truetype(fpath, int(fs))
            cx = (lr.x0 - bb.x0) * k; cy = ((lr.y0 + lr.y1) / 2 - bb.y0) * k
            tw = d.textlength(zh, font=f)
            # keep left alignment for titles, centre for short labels
            if len(zh) <= 3: cx = ((lr.x0 + lr.x1) / 2 - bb.x0) * k - tw / 2
            light = sum(col) > 500
            stroke = (40, 20, 15) if light else (245, 235, 215)
            d.text((cx, cy), zh, font=f, fill=col + (255,), anchor='lm', stroke_width=max(1, int(fs / 9)) if not handout else 0, stroke_fill=stroke)
        im.convert('RGB').save(os.path.join(out, stem + '.png'), optimize=True)
        print(stem, im.size, len(jobs))

if __name__ == '__main__':
    main()
