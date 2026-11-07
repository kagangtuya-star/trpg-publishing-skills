"""Extract every raster image of the original PDF (with soft-mask alpha) and record where it is used.

  python scripts/extract_images.py [out_dir]

Outputs (default out_dir = module root):
  assets/original/img/p{first_page:03d}_x{xref}.{png|jpg}   png when the image has a soft mask
  work/extracted/images_meta.json   {file: {xref, w, h, pages, bbox_first, alpha}}
  work/extracted/image_usage.json   {xref: {pages, bboxes, w, h}}
Only pages up to the last chapter page in src/config/chapters.json are scanned (untranslated appendices skipped).
Images under 1800 px area or with a side under 20 px are skipped (rules, bullets, specks).
"""
import json, os, sys
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT

def main():
    base = sys.argv[1] if len(sys.argv) > 1 else ROOT
    img_dir = os.path.join(base, 'assets/original/img'); os.makedirs(img_dir, exist_ok=True)
    ex_dir = os.path.join(base, 'work/extracted'); os.makedirs(ex_dir, exist_ok=True)
    doc = pymupdf.open(os.path.join(ROOT, 'input/original.pdf'))
    cfg = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
    last = max(c['pages'][1] for k, c in cfg.items() if k.isdigit())
    usage = {}
    for pi, page in enumerate(doc):
        if pi + 1 > last: break
        for im in page.get_images(full=True):
            xref, smask, w, h = im[0], im[1], im[2], im[3]
            if w * h < 1800 or min(w, h) < 20: continue
            rects = page.get_image_rects(xref)
            u = usage.setdefault(xref, dict(pages=[], bboxes=[], w=w, h=h, smask=smask))
            if pi + 1 not in u['pages']:
                u['pages'].append(pi + 1)
                u['bboxes'].append([round(v) for v in rects[0]] if rects else None)
    meta = {}
    for xref, u in usage.items():
        pix = pymupdf.Pixmap(doc, xref)
        if u['smask']:
            mask = pymupdf.Pixmap(doc, u['smask'])
            try: pix = pymupdf.Pixmap(pix, mask)
            except Exception: pass
        if pix.n - pix.alpha >= 4:                       # CMYK -> RGB
            pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
        alpha = bool(pix.alpha)
        if not alpha and doc.extract_image(xref)['ext'] in ('jpeg', 'jpg', 'jpx'):
            name = f'p{u["pages"][0]:03d}_x{xref}.jpg'          # keep the original JPEG stream as-is
            open(os.path.join(img_dir, name), 'wb').write(doc.extract_image(xref)['image'])
        else:
            name = f'p{u["pages"][0]:03d}_x{xref}.png'
            pix.save(os.path.join(img_dir, name))
        meta[name] = dict(xref=xref, w=u['w'], h=u['h'], pages=u['pages'], bbox_first=u['bboxes'][0], alpha=alpha)
    json.dump(meta, open(os.path.join(ex_dir, 'images_meta.json'), 'w'), indent=0)
    json.dump({str(k): {kk: vv for kk, vv in v.items() if kk != 'smask'} for k, v in usage.items()},
              open(os.path.join(ex_dir, 'image_usage.json'), 'w'), indent=0)
    print(len(meta), 'images ->', img_dir)

if __name__ == '__main__':
    main()
