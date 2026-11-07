"""Captions for character / monster / item art (figure kinds `portrait` and `figure`).

Identity comes from the ORIGINAL book: the CAPTION run (role CAPTION in work/extracted/en/chN.json) on the
same original page, nearest in y. Its Chinese form is looked up in src/config/caption_glossary.json
(per chapter, spelling attested in that chapter's translation). Images without an original caption get none.
Each glossary entry that is not `composed` must occur verbatim in that chapter's translation (checked here).
Manual entries in src/config/captions.json (`"manual": true`) are never overwritten; set "caption": "" to suppress.
Writes src/config/captions.json and work/qa/captions_review.json.
"""
import json, os, re, sys
from collections import Counter
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT, chapter_files, chapter_numbers

def norm(t):
    return re.sub(r'\s+', ' ', t.replace('’', "'").replace('‘', "'")).strip().upper()

def main():
    figs = json.load(open(os.path.join(ROOT, 'src/config/figures.json'), encoding='utf-8'))
    gloss = json.load(open(os.path.join(ROOT, 'src/config/caption_glossary.json'), encoding='utf-8'))
    path = os.path.join(ROOT, 'src/config/captions.json')
    old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
    out, review = {}, []
    files = chapter_files()
    text = {ch: open(files[ch], encoding='utf-8').read() for ch in chapter_numbers()}
    caps = {ch: [r for r in json.load(open(os.path.join(ROOT, f'work/extracted/en/ch{ch}.json'))) if r['role'] == 'CAPTION']
            for ch in chapter_numbers()}
    for fid, f in sorted(figs.items()):
        if not f.get('use') or f['kind'] not in ('portrait', 'figure') or not f.get('chapter'): continue
        if fid in old and old[fid].get('manual'):
            out[fid] = old[fid]; continue
        ch = f['chapter']
        same = [r for r in caps[ch] if r['page'] == f['page']]
        if not same:
            out[fid] = dict(caption='', en='', source='no-original-caption', page=f['page'])
            review.append(dict(id=fid, page=f['page'], issue='no caption in original')); continue
        en = norm(min(same, key=lambda r: abs(r['y'] - f['y']))['text'])
        g = gloss.get(str(ch), {}).get(en)
        if not g:
            out[fid] = dict(caption='', en=en, source='missing-glossary', page=f['page'])
            review.append(dict(id=fid, page=f['page'], en=en, issue='not in caption_glossary.json')); continue
        src = 'composed' if g.get('composed') else 'attested'
        if src == 'attested' and g['zh'].strip('《》') not in text[ch]:
            src = 'unattested'
        out[fid] = dict(caption=g['zh'], en=en, source=src, page=f['page'])
        if src != 'attested' or g.get('note'):
            review.append(dict(id=fid, page=f['page'], en=en, caption=g['zh'], issue=src, note=g.get('note', '')))
    json.dump(out, open(path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    os.makedirs(os.path.join(ROOT, 'work/qa'), exist_ok=True)
    json.dump(review, open(os.path.join(ROOT, 'work/qa/captions_review.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(out), Counter(v['source'] for v in out.values()))
    if any(v['source'] in ('missing-glossary', 'unattested') for v in out.values()):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
