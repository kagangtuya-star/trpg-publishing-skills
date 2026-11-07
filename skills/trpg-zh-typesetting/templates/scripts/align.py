"""Anchor-based alignment of ZH translation units to EN role runs.
Uses numeric / area-code / latin-word token k-grams as anchors, monotone chain (LIS),
then piecewise-linear interpolation of character offsets.
Writes work/mapping/align_chN.json: per ZH unit -> en run indices, role votes, en pages.
"""
import json, re, os, sys, bisect
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import units, chapter_files, ROOT, chapter_numbers

TOK = re.compile(r'[A-Z]\d{1,2}[a-z]?\b|\d[\d,]*|[A-Za-z]{5,}')

def toks(text, base):
    out = []
    for m in TOK.finditer(text):
        t = m.group(0)
        if t[0].isdigit(): t = t.replace(',', '')
        elif not (t[0].isupper() and t[1:2].isdigit()): t = t.lower()
        out.append((t, base + m.start()))
    return out

def build(ch):
    os.makedirs(os.path.join(ROOT, 'work/mapping'), exist_ok=True)
    en = json.load(open(os.path.join(ROOT, f'work/extracted/en/ch{ch}.json')))
    en = [r for r in en if not (r['role'] == 'LABEL' and 'HANDOUT' not in r['text'])]
    zh = units(chapter_files()[ch])
    eoff = []; pos = 0; etok = []
    for r in en:
        eoff.append(pos); etok += toks(r['text'], pos); pos += len(r['text']) + 1
    etot = pos
    zoff = []; pos = 0; ztok = []
    for u in zh:
        zoff.append(pos); ztok += toks(u['plain'], pos); pos += len(u['plain']) + 1
    ztot = pos
    K = 3
    egrams = {}
    for i in range(len(etok) - K + 1):
        g = tuple(t for t, _ in etok[i:i + K]); egrams.setdefault(g, []).append(etok[i][1])
    pairs = []
    for i in range(len(ztok) - K + 1):
        g = tuple(t for t, _ in ztok[i:i + K])
        if all(x.isdigit() and len(x) == 1 for x in g): continue
        cands = egrams.get(g)
        if not cands: continue
        zp = ztok[i][1]; exp = zp / ztot * etot
        c = [e for e in cands if abs(e - exp) < 0.15 * etot]
        if 0 < len(c) <= 3:
            for e in c: pairs.append((zp, e))
    # longest increasing chain (strict in both)
    pairs.sort(key=lambda p: (p[0], -p[1]))
    tails = []; tails_idx = []; prev = [-1] * len(pairs)
    for k, (z, e) in enumerate(pairs):
        j = bisect.bisect_left(tails, e)
        if j > 0: prev[k] = tails_idx[j - 1]
        if j == len(tails): tails.append(e); tails_idx.append(k)
        else: tails[j] = e; tails_idx[j] = k
    chain = []; k = tails_idx[-1] if tails_idx else -1
    while k >= 0: chain.append(pairs[k]); k = prev[k]
    chain = [(0, 0)] + chain[::-1] + [(ztot, etot)]
    zs = [c[0] for c in chain]; es = [c[1] for c in chain]
    def f(z):
        j = bisect.bisect_right(zs, z) - 1; j = max(0, min(j, len(zs) - 2))
        z0, z1, e0, e1 = zs[j], zs[j + 1], es[j], es[j + 1]
        return e0 + (e1 - e0) * ((z - z0) / (z1 - z0) if z1 > z0 else 0)
    res = []
    for u, zo in zip(zh, zoff):
        a, b = f(zo), f(zo + max(1, len(u['plain'])))
        if b < a: a, b = b, a
        votes = {}; runs = []
        j = max(0, bisect.bisect_right(eoff, a) - 1)
        while j < len(en) and eoff[j] <= b:
            s, t = eoff[j], eoff[j] + len(en[j]['text'])
            ov = max(0, min(b, t) - max(a, s)) + (1 if s <= a <= t else 0)
            if ov > 0:
                votes[en[j]['role']] = votes.get(en[j]['role'], 0) + ov; runs.append(j)
            j += 1
        res.append(dict(i=u['i'], line=u['line'], runs=runs, votes=votes,
                        page=en[runs[0]]['page'] if runs else None))
    json.dump(dict(anchors=len(chain), en=en, units=res), open(os.path.join(ROOT, f'work/mapping/align_ch{ch}.json'), 'w'), ensure_ascii=False)
    return zh, en, res, len(chain)

if __name__ == '__main__':
    for ch in (map(int, sys.argv[1:]) if len(sys.argv) > 1 else chapter_numbers()):
        zh, en, res, n = build(ch)
        print('ch', ch, 'zh units', len(zh), 'en runs', len(en), 'anchors', n)
