"""Inventory of an original PDF for role mapping (phase 1).

  python tools/inventory.py input/original.pdf [first_page last_page] > work/inventory.md

Prints (markdown):
  1. font table: (font, size, colour) -> characters, pages, sample text. Use it to write role_of() in extract_en.py.
  2. per-page image summary: count, largest image size, alpha, area share -> spot openers, full-page art, textures.
  3. map candidates: pages where >=4 area-code-like labels (A1, 12, B3a) sit inside a large (not page-size) image (heuristic; confirm visually).
  4. caption candidates: short upper-case lines whose font is used rarely (art captions -> captions.py).
"""
import re, sys, collections
import pymupdf

def main():
    d = pymupdf.open(sys.argv[1])
    a = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    b = int(sys.argv[3]) if len(sys.argv) > 3 else len(d)
    fonts = collections.defaultdict(lambda: dict(chars=0, pages=set(), sample=''))
    pages, maps, caps = [], [], collections.Counter()
    capsample = collections.defaultdict(list)
    for pn in range(a, b + 1):
        p = d[pn - 1]; W, H = p.rect.width, p.rect.height
        lines = []
        for blk in p.get_text('dict')['blocks']:
            if blk['type'] != 0: continue
            for l in blk['lines']:
                t = ''.join(s['text'] for s in l['spans']).strip()
                if not t: continue
                lines.append((pymupdf.Rect(l['bbox']), t, l['spans'][0]))
                for s in l['spans']:
                    k = (s['font'], round(s['size'], 1), '%06x' % s['color'])
                    f = fonts[k]; f['chars'] += len(s['text'].strip()); f['pages'].add(pn)
                    if len(f['sample']) < 60: f['sample'] += s['text'].strip()[:60 - len(f['sample'])] + ' '
        imgs = []
        for im in p.get_images(full=True):
            for r in p.get_image_rects(im[0]):
                imgs.append((r, im[2], im[3], bool(im[1])))
        share = sum(r.get_area() for r, *_ in imgs) / (W * H) if imgs else 0
        big = max(imgs, key=lambda t: t[0].get_area()) if imgs else None
        pages.append((pn, len(imgs), f'{big[1]}x{big[2]}' if big else '', any(t[3] for t in imgs), round(share, 2)))
        boxes = [r for r, *_ in imgs if W * H * .12 < r.get_area() < W * H * .95]   # page-size textures are not maps
        on = [t for r, t, s in lines if re.fullmatch(r'[A-Z]{0,2}\d{1,2}[a-z]?', t)
              and any(b.contains(pymupdf.Point((r.x0 + r.x1) / 2, (r.y0 + r.y1) / 2)) for b in boxes)]
        if len(on) >= 4: maps.append((pn, len(on), ' '.join(on[:12])))
        for r, t, s in lines:
            if 3 <= len(t) <= 40 and t.upper() == t and any(c.isalpha() for c in t):
                k = (s['font'], round(s['size'], 1)); caps[k] += 1
                if len(capsample[k]) < 4: capsample[k].append(f'p{pn}:{t}')
    print('# Inventory\n\n## 1. Fonts (font | size | colour | chars | pages | sample)\n')
    print('| font | size | colour | chars | pages | sample |\n|---|---|---|---|---|---|')
    for k, f in sorted(fonts.items(), key=lambda t: -t[1]['chars']):
        ps = sorted(f['pages'])
        print(f'| {k[0]} | {k[1]} | {k[2]} | {f["chars"]} | {ps[0]}–{ps[-1]} ({len(ps)}) | {f["sample"].strip().replace("|", "/")} |')
    print('\n## 2. Pages (page | images | largest px | alpha | image area share)\n')
    print('| page | n | largest | alpha | share |\n|---|---|---|---|---|')
    for r in pages: print('| ' + ' | '.join(map(str, r)) + ' |')
    print('\n## 3. Map candidates (page | short labels over the largest image | sample)\n')
    for r in maps: print(f'- p{r[0]}: {r[1]} labels — {r[2]}')
    print('\n## 4. Upper-case short lines by font (caption / heading candidates)\n')
    for k, n in caps.most_common(25): print(f'- {k[0]} {k[1]}pt × {n}: ' + ' ; '.join(capsample[k]))

if __name__ == '__main__':
    main()
