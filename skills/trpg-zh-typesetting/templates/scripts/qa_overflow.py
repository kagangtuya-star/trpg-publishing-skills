"""Find body text that overflows the content area into the bottom margin (y > 700pt).
   python scripts/qa_overflow.py [pdf]   -> work/qa/overflow.json"""
import json, os, re, sys
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT, chapter_numbers
from runtime import BOOK, FINAL, BODY_BOTTOM, PAGE_H

CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
FOOT = re.compile(r'^(对应原版\s*\d*\s*页|\d+|' + '|'.join(re.escape(t) for t in [BOOK['title']] + [v['title'] for k, v in CFG.items() if k.isdigit()]) + r')$')

def main():
    pdf = sys.argv[1] if len(sys.argv) > 1 else FINAL
    d = pymupdf.open(pdf); hits = []
    st = json.load(open(os.path.join(ROOT, 'work/pdf/state.json')))
    skip = {1, 2} | {st[f'ch{c}_start'] + offset for c in chapter_numbers() for offset in (0, 1)}
    for i, p in enumerate(d):
        if i + 1 in skip: continue
        for b in p.get_text('blocks'):
            t = b[4].strip()
            if b[3] > BODY_BOTTOM + 3 and b[1] < PAGE_H - 43 and t and not all(FOOT.match(x.strip()) for x in t.split('\n') if x.strip()):
                hits.append(dict(page=i + 1, y0=round(b[1]), y1=round(b[3]), text=t[:60]))
    json.dump(hits, open(os.path.join(ROOT, 'work/qa/overflow.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('overflow blocks:', len(hits), 'pages:', sorted({h['page'] for h in hits}))
    if hits: raise SystemExit(1)

if __name__ == '__main__':
    main()
