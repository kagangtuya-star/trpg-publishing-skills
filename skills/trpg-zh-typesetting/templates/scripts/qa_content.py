"""Content completeness check.

  python scripts/qa_content.py            # source Markdown -> semantic md (src/chapters)
  python scripts/qa_content.py --pdf      # also source Markdown -> per-chapter PDF text (work/pdf/chN.pdf)

Every unit of the translation (one line / html block / table) is normalised (markup, spaces and
punctuation removed) and cut into 24-char shingles; each shingle must be found in the target text.
Units removed on purpose (config `drop` ranges, duplicated headings) are reported separately.
Writes work/qa/content_check.json and prints a summary.
"""
import json, os, re, sys, html as H
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT, units, chapter_files, chapter_numbers
from runtime import BODY_BOTTOM, BOOK

CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
K = 24

def norm(t):
    t = H.unescape(re.sub(r'<[^>]+>', '', t))
    t = re.sub(r'\{[^}]*\}', '', t)                       # attribute lists
    t = re.sub(r'^@(title|sec|field|figure|orig)\b', '', t, flags=re.M)
    t = t.replace('\\"', '"')
    # keep only CJK, latin letters and digits
    return ''.join(ch for ch in t.lower() if ch.isalnum())

def shingles(s):
    if len(s) <= K: return [s] if s else []
    step = K // 2
    return [s[i:i + K] for i in range(0, len(s) - K + 1, step)] + [s[-K:]]

def split_ok(x, tgt):
    """text crossing a column/page break (with a float, sidebar or footer in between) is found in two pieces"""
    return any(x[:i] in tgt and x[i:] in tgt for i in range(3, len(x) - 2))

def pdf_text(ch):
    import pymupdf
    d = pymupdf.open(os.path.join(ROOT, f'work/pdf/ch{ch}.pdf'))
    out = []
    for p in d:   # body area only: drop folios, running titles and "对应原版" markers in the page margins
        out.extend(b[4] for b in p.get_text('blocks', sort=False) if b[1] < BODY_BOTTOM + 6 and b[3] > 40)
    return '\n'.join(out)

def check(ch, target_text):
    cfg = CFG[str(ch)]
    drops = [tuple(r) for r in cfg.get('drop', [])]
    dup = {d['dup_line'] for d in json.load(open(os.path.join(ROOT, f'work/qa/dup_headings_ch{ch}.json'), encoding='utf-8'))}
    tgt = norm(target_text)
    missing, dropped, total, found = [], [], 0, 0
    for u in units(chapter_files()[ch]):
        ln = u['line']
        if any(a <= ln <= b for a, b in drops):
            dropped.append(dict(line=ln, kind='config-drop', text=u['raw'][:80])); continue
        if ln in dup:
            dropped.append(dict(line=ln, kind='dup-heading', text=u['raw'][:80])); continue
        if re.fullmatch(r'\s*(-{3,}|\*{3,}|_{3,})\s*', u['raw']):
            continue        # horizontal rules
        src = u['raw']
        if u['kind'] == 'mdtable':
            src = re.sub(r'^\s*\|?[\s:|-]+\|?\s*$', '', src, flags=re.M)
        s = norm(src)
        if not s: continue
        sh = shingles(s); total += len(sh)
        miss = [x for x in sh if x not in tgt and not split_ok(x, tgt)]
        found += len(sh) - len(miss)
        if miss:
            missing.append(dict(line=ln, missing=len(miss), of=len(sh), text=u['raw'][:120]))
    return dict(chapter=ch, shingles=total, found=found, coverage=round(found / max(total, 1), 5),
                missing_units=missing, dropped_units=dropped)

def main():
    use_pdf = '--pdf' in sys.argv
    res = {}
    for ch in chapter_numbers():
        md = open(os.path.join(ROOT, f'src/chapters/ch{ch}.md'), encoding='utf-8').read()
        r = dict(semantic=check(ch, md))
        if use_pdf:
            txt = pdf_text(ch)
            if ch == 1:   # front-matter part of ch1 lives in front.pdf
                import pymupdf
                txt = '\n'.join(b[4] for p in pymupdf.open(os.path.join(ROOT, 'work/pdf/front.pdf')) for b in p.get_text('blocks') if b[1] < BODY_BOTTOM + 6) + '\n' + txt
            r['pdf'] = check(ch, txt)
        res[ch] = r
        for k, v in r.items():
            print(f'ch{ch} {k:8s} coverage {v["coverage"]:.4%}  missing units {len(v["missing_units"])}  dropped {len(v["dropped_units"])}')
    json.dump(res, open(os.path.join(ROOT, 'work/qa/content_check.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if any(v['semantic']['coverage'] < .999 or (use_pdf and v['pdf']['coverage'] < .997) for v in res.values()):
        raise SystemExit(1)

if __name__ == '__main__':
    main()
