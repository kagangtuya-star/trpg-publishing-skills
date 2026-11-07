"""Classify original art and write src/config/figures.json (hand-editable afterwards).

Each entry: chapter, page (original page), y (pt), kind, src (asset path), use.
kinds: scene (full-width page float), scene-col (column float), figure (tall cut-out, column),
       portrait (small bust cut-out, float in column), map (full-width/whole page, labels in Chinese),
       handout-bg (parchment texture used for handouts, not placed), skip
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT
from runtime import ART

CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
meta = json.load(open(os.path.join(ROOT, 'work/extracted/images_meta.json')))
MAPS = json.load(open(os.path.join(ROOT, 'src/config/maps.json'), encoding='utf-8'))

OPENER_PAGES = set(ART['excluded_pages']) | {p for pair in ART['openers'].values() for p in pair}
OPENER_PAGES |= {ART[k] for k in ('cover_page', 'title_page', 'intro_page') if ART.get(k)}
TEXTURE = set(ART['textures'])
HANDOUT_BG = set(ART['handout_backgrounds'])

def chapter_of(pg):
    for ch, c in CFG.items():
        if ch.isdigit() and c['pages'][0] <= pg <= c['pages'][1]: return int(ch)

def main():
    out = {}
    path = os.path.join(ROOT, 'src/config/figures.json')
    old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    for fn, m in sorted(meta.items(), key=lambda t: (t[1]['pages'][0], t[0])):
        stem = fn.rsplit('.', 1)[0]
        pg = m['pages'][0]
        if len(m['pages']) > 2 or chapter_of(pg) is None: continue
        w, h = m['w'], m['h']
        x0, y0, x1, y1 = m['bbox_first']
        dw, dh = x1 - x0, y1 - y0
        if w * h < 120000 or dw < 90: continue
        if pg in OPENER_PAGES: continue
        if stem in TEXTURE:
            continue
        if stem in HANDOUT_BG:
            kind = 'handout-bg'
        elif stem in MAPS:
            kind = 'map'
        elif m['alpha']:
            # transparent cut-outs: tall figures vs busts / objects
            kind = 'figure' if h / w > 1.3 else 'portrait'
        else:
            if h / w > 1.15 and dh > 600: kind = 'fullpage'
            else: kind = 'scene'
        e = dict(chapter=chapter_of(pg), page=pg, y=round(y0), x=round(x0), kind=kind,
                 src=f'assets/original/img/{fn}', use=kind not in ('handout-bg',))
        if kind == 'map':
            e['src'] = f'assets/processed/maps/{stem}.png'
            e['title'] = MAPS[stem]['title']
            e['size'] = 'fullpage' if MAPS[stem]['bbox'][3] - MAPS[stem]['bbox'][1] > 450 else 'wide'
        if stem in old:   # keep manual edits
            for k in ('use', 'kind', 'size', 'before_line', 'width', 'place', 'note'):
                if k in old[stem]: e[k] = old[stem][k]
        out[stem] = e
    json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    from collections import Counter
    print(len(out), Counter(v['kind'] for v in out.values()))

if __name__ == '__main__':
    main()
