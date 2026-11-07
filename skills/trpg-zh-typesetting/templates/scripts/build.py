"""Build the whole book.

  python scripts/build.py              # render + compile all parts (serially) + merge
  python scripts/build.py --prep       # also regenerate assets, maps, figures, semantic sources
  python scripts/build.py --only 3     # recompile only chapter 3 (others reused), then merge

Each part (front matter, chapters 1-6) is compiled by Vivliostyle separately (memory-safe),
with its starting page number passed in, so folios are continuous.  Chapters start on a
verso (opener spread); a decorative pad page is inserted where needed.  The merged PDF gets
a full outline (chapters / parts / sections / keyed areas), page labels and metadata.
"""
import json, os, re, subprocess, sys, time
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT, chapter_numbers
from runtime import BOOK, ART, TOOLS_ROOT, FINAL, PAGE_W, PAGE_H, browser_path

V = os.environ.get('VIVLIOSTYLE_CLI', str(TOOLS_ROOT / 'node_modules/@vivliostyle/cli/dist/cli.js'))
PY = sys.executable
WORK = os.path.join(ROOT, 'work/pdf')
STATE = os.path.join(WORK, 'state.json')

def sh(cmd, env=None):
    t = time.time()
    r = subprocess.run(cmd, cwd=ROOT, env={**os.environ, **(env or {})}, capture_output=True, text=True)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-3000:]); raise SystemExit(f'failed: {cmd}')
    return time.time() - t

def compile_html(name):
    out = os.path.join(WORK, f'{name}.raw.pdf')
    dt = sh([os.environ.get('NODE', 'node'), V, 'build', '--executable-browser', browser_path(), '--log-level', 'silent'],
            env={'VS_TITLE': BOOK['title'], 'VS_ENTRY': f'build/{name}.html', 'VS_OUT': f'work/pdf/{name}.raw.pdf'})
    d = pymupdf.open(out)
    if name.startswith('ch'): d.delete_page(0)          # dummy leading page
    d.save(os.path.join(WORK, f'{name}.pdf'), garbage=3, deflate=True)
    n = len(d); d.close()
    print(f'  {name}: {n} pages, {dt:.0f}s')
    return n

def pad_page(path):
    """decorative recto filler page (frame + crown emblem)."""
    d = pymupdf.open(); p = d.new_page(width=PAGE_W, height=PAGE_H)
    p.insert_image(p.rect, filename=os.path.join(ROOT, 'assets/processed/frame_recto_front.jpg'))
    if ART.get('pad_emblem'):
        e = ART['pad_emblem']
        p.insert_image(pymupdf.Rect(e['bbox']), filename=os.path.join(ROOT, e['src']))
    d.save(path)

def heading_index(pdf_path, doc, first_page):
    """locate rendered headings (parts, sections, areas) by sequential text search."""
    d = pymupdf.open(pdf_path)
    alnum = lambda t: ''.join(c for c in t if c.isalnum())
    texts = [alnum(d[i].get_text()) for i in range(len(d))]
    # part banners (23 pt): match only large lines, else the opener TOC or a body sentence quoting the title wins
    big = [alnum(''.join(l2 for b in d[i].get_text('dict')['blocks'] for l in b.get('lines', [])
                         if max(s['size'] for s in l['spans']) >= 18 for l2 in [''.join(s['text'] for s in l['spans'])]))
           for i in range(len(d))]
    res = []; cur = 0
    for lvl, title in doc:
        key = alnum(title)[:12]
        if not key: continue
        pool = big if lvl == 2 else texts
        if lvl == 2: key = key[:4]                         # banner keeps only the Chinese title (English gloss is smaller)
        for i in range(cur, min(len(texts), cur + 12)):   # bounded: a miss must not swallow the rest
            if key in pool[i]:
                res.append((lvl, title, first_page + i)); cur = i; break
    return res

def outline_items(ch):
    """(level, title) in reading order from the semantic source."""
    items = []
    lines = open(os.path.join(ROOT, f'src/chapters/ch{ch}.md'), encoding='utf-8').read().split('\n')
    if '@chapter-opener' in lines: lines = lines[lines.index('@chapter-opener') + 1:]   # ch1 front zone is in front.pdf
    for l in lines:
        s = l.strip()
        m = re.match(r'^(#{2,4})\s+(.*?)\s*(\{[^}]*\})?$', s)
        if not m: continue
        title = re.sub(r'\*\*', '', m.group(2)); attr = m.group(3) or ''
        if 'sbh' in attr: continue
        if 'part' in attr: items.append((2, title))
        elif 'area' in attr: items.append((4, title))
        elif len(m.group(1)) <= 3: items.append((3, title))
    return items

def main():
    global render
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--prep', action='store_true')
    ap.add_argument('--only', type=int, choices=chapter_numbers())
    ns = ap.parse_args()
    args = sys.argv[1:]
    os.makedirs(WORK, exist_ok=True); os.makedirs(os.path.dirname(FINAL), exist_ok=True)
    if ns.prep:
        for s in ('extract_en.py', 'extract_images.py', 'make_assets.py', 'maps.py', 'figures.py', 'optimize_images.py', 'captions.py', 'normalize.py'):
            print('prep', s); sh([PY, f'scripts/{s}'])
    import render  # load freshly generated figures/captions only after --prep
    only = None
    if ns.only is not None: only = str(ns.only)
    state = json.load(open(STATE)) if os.path.exists(STATE) else {}
    cfg = render.CFG
    has_intro = bool(cfg['1'].get('front'))
    # 1) front matter (placeholder TOC first time, page count is what matters)
    toc = state.get('toc', [])
    if only is None or not os.path.exists(os.path.join(WORK, 'front.pdf')):
        placeholder = []
        for ch in chapter_numbers():
            placeholder.append(dict(level='chapter', title=f'第{render.CN_NUM[ch]}章　{cfg[str(ch)]["title"]}', page=0))
            placeholder.extend(dict(level='part', title=t, page=0) for lvl, t in outline_items(ch) if lvl == 2)
        render.front_doc(1, toc or placeholder)
        state['front_pages'] = compile_html('front')
    page = state['front_pages'] + 1
    if (page % 2) == 1:   # chapters must start on an even (verso) page
        state['front_pad'] = True; page += 1
    else:
        state['front_pad'] = False
    # 2) chapters
    starts = {}
    for ch in chapter_numbers():
        starts[ch] = page
        key = f'ch{ch}'
        if only is None or only == str(ch) or state.get(f'{key}_start') != page or not os.path.exists(os.path.join(WORK, f'{key}.pdf')):
            render.chapter_doc(ch, page)
            state[f'{key}_pages'] = compile_html(key)
            state[f'{key}_start'] = page
        n = state[f'{key}_pages']
        page += n
        state[f'{key}_pad'] = (page % 2 == 1)
        if state[f'{key}_pad']: page += 1
    total = page - 1
    # 3) TOC + outline
    toc = [dict(level='front', title='引　言', page=state['front_pages'] - state.get('intro_pages', 0))] if has_intro else []
    outline = []
    for ch in chapter_numbers():
        c = cfg[str(ch)]
        hs = heading_index(os.path.join(WORK, f'ch{ch}.pdf'), outline_items(ch), starts[ch])
        toc.append(dict(level='chapter', title=f'第{render.CN_NUM[ch]}章　{c["title"]}', page=starts[ch]))
        outline.append([1, f'第{render.CN_NUM[ch]}章　{c["title"]}', starts[ch]])
        for lvl, t, p in hs:
            if lvl == 2: toc.append(dict(level='part', title=t, page=p))
            outline.append([lvl, t, p])
    # intro start page: find in front pdf
    fd = pymupdf.open(os.path.join(WORK, 'front.pdf'))
    intro_page = next((i + 1 for i in range(len(fd)) if '引言' in re.sub(r'\s', '', fd[i].get_text()) and i > 2), 4)
    fd.close()
    if has_intro: toc[0]['page'] = intro_page
    def intro_at():
        fd = pymupdf.open(os.path.join(WORK, 'front.pdf'))
        r = next((i + 1 for i in range(len(fd)) if '引言' in re.sub(r'\s', '', fd[i].get_text()) and i > 2), 4)
        fd.close(); return r
    for _ in range(3):       # the real TOC can change the front-matter length -> intro page; iterate to a fixed point
        if toc == state.get('toc') and os.path.exists(os.path.join(WORK, 'front.pdf')): break
        state['toc'] = [dict(e) for e in toc]
        render.front_doc(1, toc)
        n = compile_html('front')
        if n >= starts[1]: raise SystemExit(f'front matter grew to {n} pages; rerun build.py without --only')
        if has_intro:
            intro_page = intro_at(); toc[0]['page'] = intro_page
    json.dump(state, open(STATE, 'w'), ensure_ascii=False, indent=1)
    # 4) merge
    pad = os.path.join(WORK, 'pad.pdf'); pad_page(pad)
    book = pymupdf.open()
    def add(path):
        s = pymupdf.open(path); book.insert_pdf(s); s.close()
    add(os.path.join(WORK, 'front.pdf'))
    while len(book) + 1 < starts[1]: add(pad)     # keep chapter folios fixed if the real TOC is shorter
    for ch in chapter_numbers():
        assert len(book) + 1 == starts[ch], (ch, len(book), starts[ch])
        add(os.path.join(WORK, f'ch{ch}.pdf'))
        if state[f'ch{ch}_pad']: add(pad)
    toc_pdf = [[1, '封面', 1], [1, '目录', 3]]
    if has_intro: toc_pdf.append([1, '引言', intro_page])
    # make levels consecutive for PyMuPDF
    last = 1
    for lvl, t, p in outline:
        lvl = min(lvl, last + 1); toc_pdf.append([lvl, t, p]); last = lvl
    book.set_toc(toc_pdf)
    book.set_metadata({'title': BOOK['title'], 'author': BOOK['author'],
                       'subject': BOOK['subject'], 'keywords': BOOK['keywords'],
                       'creator': 'Vivliostyle + PyMuPDF', 'producer': 'trpg-publishing build.py'})
    book.set_page_labels([{'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1}])
    book.save(FINAL, garbage=3, deflate=True)
    print('book:', len(book), 'pages ->', FINAL, f'({os.path.getsize(FINAL) / 1e6:.1f} MB)')

if __name__ == '__main__':
    main()
