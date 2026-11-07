"""Render semantic chapter sources (src/chapters/chN.md) to HTML documents in build/.

Source syntax (produced by normalize.py, hand-editable):
  front matter (--- ... ---), '# '..'#### ' headings with optional {.class key="v"} attrs,
  '::: name' ... ':::' containers (readaloud, sidebar, handout, intro, statblock, advancement, rawtable),
  '@figure <id>', '@orig <page>', '@chapter-opener', pipe tables (optional '{.cls}' line before),
  '{.cls} text' paragraph class prefix, inline **bold** / *italic* / raw HTML.
"""
import json, os, re, sys, html
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT
from runtime import BOOK, PAGE_W, PAGE_H, chapter_label

BUILD = os.path.join(ROOT, 'build')
CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
FIGS = json.load(open(os.path.join(ROOT, 'src/config/figures.json'), encoding='utf-8'))
_cap = os.path.join(ROOT, 'src/config/captions.json')      # made by scripts/captions.py
CAPS = json.load(open(_cap, encoding='utf-8')) if os.path.exists(_cap) else {}
CN_NUM = {n: chapter_label(n) for n in range(1000)}

def rel(p):  # asset path relative to build/
    return '../' + p

# ------------------------------------------------------------------ inline
def inline(s):
    s = s.replace('&', '&amp;').replace('&amp;amp;', '&amp;')
    s = re.sub(r'&amp;(#?\w+;)', r'&\1', s)
    # protect allowed raw tags
    s = re.sub(r'<(?!/?(sup|sub|br|strong|em|b|i|span)\b)', '&lt;', s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', s)
    s = re.sub(r'(?<![\*\w])\*(?!\s)([^*\n]+?)(?<!\s)\*(?![\*\w])', r'<i>\1</i>', s)
    s = s.replace('**', '')
    return s

def attrs(s):
    """parse '{.a .b key="v"}' -> (classes, dict)"""
    cls = re.findall(r'\.([\w-]+)', s)
    kv = dict(re.findall(r'([\w-]+)="([^"]*)"', s))
    return cls, kv

STAT_BOLD = ['XP', '先攻', '感官', 'AC', 'hp', 'HP', '生命值', '强韧', '反射', '意志', '防御能力', '免疫', '抗力', '抵抗', '弱点', '伤害减免', 'DR', 'SR',
             '法术抗力', '速度', '近战', '远程', '占据空间', '空间', '触及', '特殊攻击', '类法术能力', '已知法术', '已准备法术', '准备法术', '法术',
             '战斗前', '战斗中', '战斗时', '士气', '基础数值', '力量', '敏捷', '体质', '智力', '感知', '魅力', '基础攻击', 'BAB', 'CMB', 'CMD',
             '专长', '技能', '种族调整', '语言', '特质', '特殊特质', 'SQ', '战斗装备', '其他装备', '装备', '环境', '组织', '宝藏', '光环', '领域', '血统',
             '对立学派', '学派', '恒定', '随意', '防御', '偏好']
STAT_BOLD.sort(key=len, reverse=True)
SB_RE = re.compile(r'(^|[；;]\s*|[，,]\s*(?=(?:反射|意志|敏捷|体质|智力|感知|魅力|CMB|CMD)\b))(' + '|'.join(map(re.escape, STAT_BOLD)) + r')(?=[\s:：+\-—–\d（(]|$)')
SPELL_RE = re.compile(r'^(\d+\s*次\s*/\s*天|\d+\s*/\s*天|每天\s*\d+\s*次|\d+次/日|恒定|随意|[0-9一二三四五六七八九]+\s*(?:级|环)(?:（[^）]*）)?)(?=[—\-–:：\s])')

def stat_line(t):
    t = inline(t)
    t = SB_RE.sub(lambda m: m.group(1) + '<b>' + m.group(2) + '</b>', t, count=0)
    t = SPELL_RE.sub(lambda m: '<b>' + m.group(1) + '</b>', t)
    return t

# ------------------------------------------------------------------ blocks
class Doc:
    def __init__(self, ch, meta):
        self.ch = ch; self.meta = meta; self.out = []; self.ids = {}; self.parts = []; self.maps = []
        self.hcount = 0
    def w(self, s): self.out.append(s)
    def new_id(self, prefix):
        self.hcount += 1
        return f'{prefix}-{self.ch}-{self.hcount}'

def render_table(lines, cls=''):
    rows = [l.strip().strip('|').split('|') for l in lines if l.strip()]
    rows = [[c.strip() for c in r] for r in rows]
    if len(rows) >= 2 and all(re.fullmatch(r':?-{2,}:?', c.replace(' ', '')) for c in rows[1] if c):
        head, body = rows[0], rows[2:]
    else:
        head, body = None, rows
    h = [f'<table class="tbl {cls}">']
    if head: h.append('<thead><tr>' + ''.join(f'<th>{inline(c)}</th>' for c in head) + '</tr></thead>')
    h.append('<tbody>' + ''.join('<tr>' + ''.join(f'<td>{inline(c)}</td>' for c in r) + '</tr>' for r in body) + '</tbody></table>')
    return '\n'.join(h)

def optimized(src):
    """print-weight copy made by scripts/optimize_images.py, if present"""
    stem = os.path.splitext(os.path.basename(src))[0]
    for ext in ('.jpg', '.png'):
        p = os.path.join('assets/optimized', stem + ext)
        if os.path.exists(os.path.join(ROOT, p)): return p
    return src

def figure_html(fid, doc):
    f = FIGS.get(fid)
    if not f: return f'<!-- missing figure {fid} -->'
    kind = f['kind']; src = rel(optimized(f['src']))
    if kind == 'map':
        size = f.get('size', 'wide')
        mid = f'map-{fid}'
        doc.maps.append((f.get('title', ''), mid))
        return (f'<figure class="fig map {size}" id="{mid}"><img src="{src}" alt="{html.escape(f.get("title", ""))}"/>'
                f'<figcaption><span class="maplabel">地图</span>{html.escape(f.get("title", ""))}</figcaption></figure>')
    extra = f' style="width:{f["width"]}"' if f.get('width') else ''
    place = f' {f["place"]}' if f.get('place') else ''
    cap = CAPS.get(fid, {}).get('caption', '') if kind in ('portrait', 'figure') else ''
    capx = f'<figcaption class="figcap">{html.escape(cap)}</figcaption>' if cap else ''
    return f'<figure class="fig {kind}{place}"{extra}><img src="{src}" alt="{html.escape(cap)}"/>{capx}</figure>'

def parse(path):
    txt = open(path, encoding='utf-8').read()
    meta = {}
    m = re.match(r'---\n(.*?)\n---\n', txt, re.S)
    if m:
        for l in m.group(1).split('\n'):
            k, _, v = l.partition(':'); meta[k.strip()] = v.strip()
        txt = txt[m.end():]
    return meta, txt.split('\n')

def render_blocks(lines, doc, start=0, end=None, stop_at=None):
    """render list of source lines -> html list"""
    i = start; n = len(lines) if end is None else end
    para_buf = []
    while i < n:
        l = lines[i]
        s = l.strip()
        if stop_at and s == stop_at: return i
        if not s: i += 1; continue
        if getattr(doc, 'pending_adv', None) and not (s.startswith('##') and 'part' in s) and not s.startswith('@orig'):
            doc.w(doc.pending_adv); doc.pending_adv = None
        if s.startswith('@orig '):
            doc.w(f'<span class="orig" data-p="{s[6:].strip()}"></span>'); i += 1; continue
        if s.startswith('@figure '):
            doc.w(figure_html(s[8:].strip(), doc)); i += 1; continue
        if s == '@chapter-opener':
            i += 1; continue
        if s.startswith(':::') and s != ':::':
            name = s[3:].strip().split()
            kind = name[0]; opts = name[1:]
            j = i + 1; depth = 1
            while j < n:
                t = lines[j].strip()
                if t == ':::':
                    depth -= 1
                    if depth == 0: break
                elif t.startswith(':::') and t != ':::': depth += 1
                j += 1
            body = lines[i + 1:j]
            render_container(kind, opts, body, doc)
            i = j + 1; continue
        mh = re.match(r'^(#{1,6})\s+(.*?)\s*(\{[^}]*\})?\s*$', s)
        if mh:
            lvl = len(mh.group(1)); text = mh.group(2); cls, kv = attrs(mh.group(3) or '')
            render_heading(lvl, text, cls, kv, doc, lines, i)
            if 'part' in cls:
                # absorb following intro container into the part banner
                j = i + 1
                while j < n and (not lines[j].strip() or lines[j].strip().startswith('@orig')):
                    if lines[j].strip().startswith('@orig'): doc.w(f'<span class="orig" data-p="{lines[j].strip()[6:].strip()}"></span>')
                    j += 1
                if j < n and lines[j].strip() == '::: intro':
                    k = j + 1
                    while k < n and lines[k].strip() != ':::': k += 1
                    doc.w('<div class="part-intro">' + ''.join(f'<p>{inline(x.strip())}</p>' for x in lines[j + 1:k] if x.strip()) + '</div>')
                    i = k + 1
                else:
                    i = j
                doc.w('</header>')
                if getattr(doc, 'pending_adv', None):
                    doc.w(doc.pending_adv); doc.pending_adv = None
                continue
            i += 1; continue
        if s.startswith('|') or (s.startswith('{.') and i + 1 < n and lines[i + 1].strip().startswith('|')):
            cls = ''
            if s.startswith('{.'):
                cls = ' '.join(attrs(s)[0]); i += 1
            j = i
            while j < n and lines[j].strip().startswith('|'): j += 1
            doc.w(render_table(lines[i:j], cls)); i = j; continue
        if re.match(r'^[-*]\s+', s):
            items = []
            while i < n and re.match(r'^[-*]\s+', lines[i].strip()):
                items.append(re.sub(r'^[-*]\s+', '', lines[i].strip())); i += 1
            doc.w('<ul>' + ''.join(f'<li>{inline(x)}</li>' for x in items) + '</ul>'); continue
        cls = ''
        mc = re.match(r'^\{([^}]*)\}\s*(.*)$', s)
        if mc:
            cls = ' '.join(attrs('{' + mc.group(1) + '}')[0]); s = mc.group(2)
        doc.w(f'<p class="{cls}">{inline(s)}</p>' if cls else f'<p>{inline(s)}</p>')
        i += 1
    return i

def render_heading(lvl, text, cls, kv, doc, lines, i):
    if 'part' in cls:
        hid = doc.new_id('part')
        label = kv.get('label', '')
        label = re.sub(r'^PART\s*(\d)$', lambda m: '第' + CN_NUM[int(m.group(1))] + '部分', label.strip())
        label = re.sub(r'^第(\d)部分$', lambda m: '第' + CN_NUM[int(m.group(1))] + '部分', label)
        doc.parts.append((label, text, hid))
        doc.w(f'<header class="part-head" id="{hid}">')
        if label: doc.w(f'<div class="part-label"><span>{html.escape(label)}</span></div>')
        m_en = re.match(r'^(.*?)\s*[（(]([A-Za-z][A-Za-z :\'’\-]+)[)）]\s*$', text)
        if m_en:   # "章节结语（CHAPTER CONCLUSION）": English gloss on its own small line
            inner = f'{inline(m_en.group(1))}<span class="pt-en">（{html.escape(m_en.group(2))}）</span>'
        else:
            inner = inline(text)
        cls = 'part-title gloss' if m_en else ('part-title long' if len(re.sub(r'[A-Za-z0-9 ]', '', text)) > 9 else 'part-title')
        doc.w(f'<h2 class="{cls}" data-label="{html.escape(label)}">{inner}</h2>')
        return
    if 'area' in cls:
        code = kv.get('code', '')
        rest = text
        mm = re.match(r'^' + re.escape(code) + r'[\.．\s]*(.*)$', text)
        if mm: rest = mm.group(1)
        crm = re.search(r'\s*([（(]\s*(?:CR|挑战等级)[^）)]*[）)])\s*$', rest)
        cr = ''
        if crm: cr = crm.group(1); rest = rest[:crm.start()]
        hid = doc.new_id('area')
        doc.w(f'<h4 class="area" id="{hid}"><span class="code">{html.escape(code)}</span><span class="name">{inline(rest.strip())}</span>'
              + (f'<span class="cr">{html.escape(cr)}</span>' if cr else '') + '</h4>')
        return
    if 'sbh' in cls:
        doc.w(f'<h4 class="sbh">{inline(text)}</h4>'); return
    tag = {1: 'h2', 2: 'h3', 3: 'h3', 4: 'h4', 5: 'h5', 6: 'h5'}[lvl]
    hid = doc.new_id('h')
    doc.w(f'<{tag} id="{hid}">{inline(text)}</{tag}>')

def render_container(kind, opts, body, doc):
    if kind == 'statblock':
        title = ''; rows = []
        for l in body:
            s = l.strip()
            if not s: continue
            if s.startswith('@title '): title = s[7:]
            elif s.startswith('@sec '): rows.append(f'<div class="sb-sec">{inline(s[5:])}</div>')
            elif s.startswith('@field '): rows.append(f'<p>{stat_line(s[7:])}</p>')
            else: rows.append(f'<p>{stat_line(s)}</p>')
        m = re.search(r'\s*((?:CR|挑战等级)\s*.*)$', title)
        name, cr = (title[:m.start()], m.group(1)) if m else (title, '')
        short = len([r for r in rows if r.startswith('<p>')]) <= 4
        doc.w(f'<section class="statblock{" short" if short else ""}"><div class="sb-title"><span class="sb-name">{inline(name.strip())}</span><span class="sb-cr">{html.escape(cr)}</span></div>'
              + ''.join(rows) + '</section>')
        return
    if kind == 'advancement':
        items = [l.strip() for l in body if l.strip()]
        title = ''
        if items and len(re.sub(r'[#*\s]', '', items[0])) <= 8 and not re.search(r'[。，]', items[0]):
            title = re.sub(r'[#*]', '', items.pop(0)).strip()
        lv = []
        for x in items:
            m = re.match(r'^(\d{1,2})\s+(.*)$', x)
            lv.append(f'<p class="has-lv"><span class="lv">{m.group(1)}</span>{inline(m.group(2))}</p>' if m else f'<p>{inline(x)}</p>')
        doc.pending_adv = '<aside class="advancement">' + (f'<h4 class="sbh">{inline(title)}</h4>' if title else '') + ''.join(lv) + '</aside>'
        return
    if kind in ('sidebar', 'handout') and 'html' in opts:
        raw = '\n'.join(body)
        raw = re.sub(r'<p>\s*<strong>([^<]{1,30})</strong>\s*</p>', r'<h4 class="sbh">\1</h4>', raw, count=1)
        cls = 'handout' if kind == 'handout' else 'sidebar'
        doc.w(f'<aside class="{cls}">{raw}</aside>'); return
    if kind == 'rawtable':
        doc.w('<div class="rawtable">' + '\n'.join(body) + '</div>'); return
    tag = {'readaloud': 'div', 'sidebar': 'aside', 'handout-text': 'aside', 'intro': 'div'}.get(kind, 'div')
    cls = {'handout-text': 'handout'}.get(kind, kind)
    sub = Doc(doc.ch, doc.meta); sub.hcount = doc.hcount; sub.parts = doc.parts; sub.maps = doc.maps
    render_blocks(body, sub)
    doc.hcount = sub.hcount
    doc.w(f'<{tag} class="{cls}">' + '\n'.join(sub.out) + f'</{tag}>')

# ------------------------------------------------------------------ documents
HEAD = '''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"/><title>{title}</title>
<link rel="stylesheet" href="../src/styles/theme.css"/>
<style>{extra}</style></head>
<body class="{bcls}">
'''

def page_css(ch, start_page, lead=0):
    # lead = number of throw-away pages before the real first page (the dummy)
    return f'''
@page {{ size: {PAGE_W}pt {PAGE_H}pt; background-size: {PAGE_W}pt {PAGE_H}pt; }}
@page :left {{ margin: {BOOK['margins'][0]}pt {BOOK['margins'][1]}pt {BOOK['margins'][2]}pt {BOOK['margins'][3]}pt;
  @bottom-left {{ content: {json.dumps(BOOK['title'], ensure_ascii=False)}; }} }}
@page :right {{ margin: {BOOK['margins'][0]}pt {BOOK['margins'][3]}pt {BOOK['margins'][2]}pt {BOOK['margins'][1]}pt; }}
@page opener-a {{ margin: 0; }} @page opener-b {{ margin: 0; }}
@page cover {{ margin: 0; }} @page titlepage {{ margin: 0; }}
.cover, .titlepage, .opener-a, .opener-b {{ height: {PAGE_H}pt; }}
@page :first {{ counter-reset: page {start_page - 1 - lead}; }}
@page :right {{ background-image: url("../assets/processed/frame_recto_{ch}.jpg"); }}
@page opener-a {{ background-image: url("../assets/processed/opener_{ch}_a.jpg"); }}
@page opener-b {{ background-image: url("../assets/processed/opener_{ch}_b.jpg"); }}
'''

def chapter_doc(ch, start_page=1):
    meta, lines = parse(os.path.join(ROOT, f'src/chapters/ch{ch}.md'))
    doc = Doc(ch, meta)
    try: op = lines.index('@chapter-opener')
    except ValueError: op = 0
    body = Doc(ch, meta)
    render_blocks(lines, body, op + 1)
    c = CFG[str(ch)]
    title = meta.get('title', c['title'])
    out = [HEAD.format(title=title, extra=page_css(f'ch{ch}', start_page, lead=1), bcls=f'chapter ch{ch}')]
    out.append('<div class="dummy"></div>')
    # opener spread (the running-title marker lives inside it: a separate element would get a page of its own)
    author = c.get('author_zh') or meta.get('author_zh') or ('BY ' + c.get('author_en', meta.get('author_en', '')).upper())
    translator = c.get('translator', '').strip()
    translator_html = f'<div class="op-translator">译者：{html.escape(translator)}</div>' if translator else ''
    out.append(f'''<section class="opener-a"><div class="running" data-title="{html.escape(title)}"></div><div class="op-num">{CN_NUM[ch] if ch < 10 else ch}</div>
<div class="op-kicker">第{CN_NUM[ch]}章</div><h1 class="op-title" id="chapter-{ch}">{html.escape(title)}</h1>
<div class="op-en">{html.escape(c["en"])}</div><div class="op-author">{html.escape(author)}</div>{translator_html}</section>''')
    toc = ''.join(f'<li><a href="#{hid}"><span class="t">{html.escape((lab + "　") if lab else "")}{html.escape(t)}</span></a></li>' for lab, t, hid in body.parts)
    maps = ''.join(f'<li><a href="#{mid}"><span class="t">{html.escape(t)}</span></a></li>' for t, mid in body.maps)
    out.append(f'''<section class="opener-b"><div class="ob-head">目　录</div><ol class="ob-toc">{toc}</ol>
<div class="ob-head maps">地　图</div><ol class="ob-toc">{maps}</ol></section>''')
    out.append('<main class="content">')
    out.extend(body.out)
    out.append('</main></body></html>')
    os.makedirs(BUILD, exist_ok=True)
    p = os.path.join(BUILD, f'ch{ch}.html')
    open(p, 'w', encoding='utf-8').write('\n'.join(out))
    return p, body

def front_doc(start_page=1, toc_entries=None):
    """cover, title page, contents, translator note, introduction (front zone of ch1)."""
    meta, lines = parse(os.path.join(ROOT, 'src/chapters/ch1.md'))
    try: op = lines.index('@chapter-opener')
    except ValueError: op = len(lines)
    intro = Doc(0, meta)
    render_blocks(lines, intro, 0, op)
    os.makedirs(BUILD, exist_ok=True)
    title, en, subtitle = (html.escape(BOOK[k]) for k in ('title', 'en', 'subtitle'))
    out = [HEAD.format(title=title, extra=page_css('front', start_page), bcls='front')]
    out.append(f'<section class="cover"><div class="cv-kicker">{subtitle}</div><h1 class="cv-title">{title}</h1><div class="cv-en">{en}</div></section>')
    out.append(f'<section class="titlepage"><div class="tp-title">{title}</div><div class="tp-en">{en}</div><div class="tp-sub">{subtitle}</div></section>')
    # contents
    rows = []
    for e in (toc_entries or []):
        cls = e['level']
        rows.append(f'<li class="{cls}"><span class="t">{html.escape(e["title"])}</span><span class="dots"></span><span class="pg">{e["page"]}</span></li>')
    out.append(f'<section class="contents"><div class="running" data-title="{title}"></div><h2 class="contents-title">目　录</h2><ol>' + ''.join(rows) + '</ol>' + open(os.path.join(ROOT, 'src/front/notes.html'), encoding='utf-8').read() + '</section>')
    if intro.out:
        out.append('<main class="content intro">')
        out.append('<header class="part-head intro-head" id="intro"><h2 class="part-title" data-label="">引　言</h2></header>')
        out.extend(intro.out)
        out.append('</main>')
    out.append('</body></html>')
    p = os.path.join(BUILD, 'front.html')
    open(p, 'w', encoding='utf-8').write('\n'.join(out))
    return p

if __name__ == '__main__':
    for a in sys.argv[1:]:
        if a == 'front': front_doc()
        else: chapter_doc(int(a))
