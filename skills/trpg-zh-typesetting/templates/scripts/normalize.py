"""Convert one translated chapter (input/translation/00N *.md) into the semantic
layout source src/chapters/chN.md.

The translation text itself is never rewritten: every source unit is carried over
verbatim (only Markdown/HTML *markup* is normalised).  What this script adds is
structure: block roles (read-aloud, sidebar, stat block, area heading, table ...),
figure placements and original-page anchors.  Roles that cannot be inferred from
the Chinese text alone are transferred from the English original by alignment
(see align.py / extract_en.py).

Usage: python scripts/normalize.py [chapter ...]
"""
import json, os, re, sys, bisect, html
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import units, chapter_files, ROOT, chapter_numbers
import align as AL

CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))

# ---------------------------------------------------------------- helpers
def unbold(s):
    s = s.strip()
    s = re.sub(r'^#+\s*', '', s)
    s = s.replace('\u200b', '')
    t = re.sub(r'\*\*', '', s).strip()
    return t

def clean_inline(s):
    """normalise markup only (escapes, pandoc dashes, entities)."""
    s = s.replace('\u200b', '')
    if re.fullmatch(r'\s*\|?(\s*:?-{3,}:?\s*\|)+\s*:?-*:?\s*\|?\s*', s): return s   # md table separator row
    s = s.replace('------', '——').replace('-----', '——')
    s = re.sub(r'(?<!-)---(?!-)', '—', s)        # pandoc em dash ("体质 ---", "DR 1/---", "CR ---")
    s = re.sub(r'(?<=[\u4e00-\u9fff\d）)])--(?=[\u4e00-\u9fff\d（(])', '–', s)
    s = re.sub(r'\\([\"\'\*\[\]_`#|<>~])', r'\1', s)
    s = html.unescape(s)
    s = re.sub(r'\*\*\s*\*\*', '', s)
    s = re.sub(r'\*\s+\*', '', s)
    return s.strip()

STAT_SECTIONS = {'防御': 'def', '进攻': 'off', '攻击': 'off', '战术': 'tac', '属性': 'stat', '数据': 'stat', '统计': 'stat',
                 '属性值': 'stat', '特殊能力': 'sa', '生态': 'eco', '基础数值': 'base'}
STAT_KEYS = (r'XP|经验|先攻|感官|AC\b|AC\d|AC：|hp\b|HP\b|hp\d|HP\d|生命值|强韧|防御能力|免疫|抗力|抵抗|弱点|DR\b|SR\b|伤害减免|法术抗力|'
             r'速度|近战|远程|占据空间|占据|空间|触及|特殊攻击|类法术能力|法术|已知法术|已准备|准备|领域|血统|学派|对立学派|秘法|神秘|奥术|'
             r'战斗前|战斗中|战斗时|士气|基础数值|力量|敏捷\s*\d|基础攻击|BAB|专长|技能|种族调整|语言|特质|特殊特质|SQ\b|战斗装备|其他装备|装备|'
             r'环境|组织|宝藏|恒定|随意|\d+\s*次\s*/\s*天|\d+\s*/\s*天|每天|每日|\d+(级|环)|[0-9一二三四五六七八九]+级法术|0级|戏法|光环|'
             r'CMB|CMD|特殊能力|反射|意志|攻击|防御|守护者|祈祷|灵能|奥能|变形|魅影|偏好|异能|能力')
STAT_RE = re.compile(r'^\s*(?:\*\*)?\s*(' + STAT_KEYS + r')', re.I)
ALIGN_RE = re.compile(r'^(?:\*\*)?(?:男性|女性|雄性|雌性|守序|中立|混乱|绝对中立|LE|NE|CE|LG|NG|CG|N\b|变体|进阶|年老|年轻|青年|成年|古老|远古|幼年|巨型|大型|中型|小型|超小型|微型|超大型|人类|半精灵|半兽人|精灵|矮人|侏儒|半身人|鼠人|兽人|食人魔|吸血鬼|魔裔)')
SIZE_TYPE_RE = re.compile(r'(微型|超小型|极小型|小型|中型|大型|超大型|巨型|超巨型|庞大).{0,8}(生物|类人|异界|亡灵|不死|魔法兽|动物|虫|龙|构装|元素|妖精|精类|植物|怪物|异怪|泥怪|人型|外来)')
ABILITY_RE = re.compile(r'^(?:\*\*)?[^，。：:]{1,24}[（(](?:超|异|类法|超自然|非凡|Su|Ex|Sp)[^)）]{0,6}[)）]')
CR_RE = re.compile(r'(?:CR|挑战等级)\s*[\d/—\-–]+')
AREA_RE = re.compile(r'^(?:\*\*)?\s*([A-H]\d{1,2}[a-z]?)(?=[\.\s　:：）)\*\u4e00-\u9fff（(])')
TERMINAL = '。！？；…”」"'

def is_stat_line(t):
    u0 = unbold(t)
    if re.match(r'^(宝藏|环境|组织|财宝)\s*[：:]', u0) and '。' in u0: return False   # GM prose ("宝藏：检查A8区域时……。")
    if STAT_RE.match(t): return True
    if ALIGN_RE.match(t) and len(t) < 90 and '。' not in t: return True
    if SIZE_TYPE_RE.search(t) and len(t) < 70 and '。' not in t: return True
    if ABILITY_RE.match(t): return True
    u = unbold(t)
    if len(u) < 90 and re.search(r'(类法术能力|法术|法术能力|已知|准备).{0,8}[（(].{0,4}(CL|施法者等级|施法等级|专注)', u): return True
    if re.match(r'^(任意|随意|恒定|\d+\s*天\s*\d+\s*次|\d+\s*次?\s*/\s*每?[日天]|\d+\s*环|[0-9]级)', u) and len(u) < 200: return True
    if re.match(r'^(?:\*\*)?(?:hp|HP|生命值)?\s*\d+\s*(?:（|\()?见第', t): return True
    return False

def stat_section(t):
    k = re.sub(r'[（(].*?[)）]', '', unbold(t)).strip(' ：:')
    return STAT_SECTIONS.get(k) if len(unbold(t)) <= 24 else None

def is_sbt(t):
    u = unbold(t)
    if len(u) > 70 or '。' in u: return False
    return (bool(re.search(r'(?:CR|挑战等级)\s*[\d/—\-–]+\s*(?:\(\d+\)|（\d+）)?\s*(?:[;；,，]?\s*XP\s*[\d,，]+\s*(?:每个|每名|每只|每人)?)?\s*$', u, re.I))
            or bool(re.search(r'每名\s*XP.*CR\s*\d+$', u))
            or (bool(re.search(r'[（(]\s*(?:CR|挑战等级)\s*[\d/]+\s*[)）]\s*$', u)) and not AREA_RE.match(u)))

# ---------------------------------------------------------------- classify
def classify(ch, U):
    cfg = CFG[str(ch)]
    drops = [tuple(r) for r in cfg.get('drop', [])]
    parts = {int(k): v for k, v in cfg.get('parts', {}).items()}
    adv = cfg.get('advancement')
    front = cfg.get('front')
    for u in U:
        ln = u['line']; raw = u['raw']; t = raw.strip()
        u['zone'] = 'front' if front and front[0] <= ln <= front[1] else 'main'
        if any(a <= ln <= b for a, b in drops): u['k'] = 'drop'; continue
        if cfg.get('title_line') == ln: u['k'] = 'title'; continue
        if ln in parts: u['k'] = 'part'; u['part'] = parts[ln]; continue
        if adv and adv[0] <= ln <= adv[1]: u['k'] = 'adv'; continue
        if u['kind'] == 'html':
            cells = re.findall(r'<td', raw)
            u['k'] = 'box' if len(cells) == 1 else 'htable'; continue
        if u['kind'] == 'mdtable': u['k'] = 'table'; continue
        if re.fullmatch(r'(-{3,}|\*{3,}|_{3,})', t): u['k'] = 'hr'; continue
        if re.match(r'^[-*]\s+\S', t) and not t.startswith('**'): u['k'] = 'li'; continue
        p = unbold(t)
        md_level = len(re.match(r'^#*', t).group(0))
        if is_sbt(t): u['k'] = 'sbt'; continue
        m = AREA_RE.match(p) or AREA_RE.match(t)
        if m and len(p) < 60 and not p.endswith('。'):
            u['k'] = 'area'; u['code'] = m.group(1); continue
        if m and re.match(r'^(?:\*\*)?[A-H]\d{1,2}[a-z]?[\.．]?\s*[^：:]{1,24}[：:]', t):
            u['k'] = 'area_inline'; u['code'] = m.group(1); continue
        if md_level:
            u['k'] = 'heading'; u['mdlevel'] = md_level; continue
        bold_whole = t.startswith('**') and t.rstrip().endswith('**') and t.count('**') == 2
        if bold_whole and len(p) <= 36 and p[-1:] not in TERMINAL + '：:':
            u['k'] = 'heading'; u['mdlevel'] = 0; continue
        if len(p) <= 32 and p[-1:] not in TERMINAL + '：:，,' and not re.match(r'^[\d\-–—]+$', p) and not is_stat_line(t):
            u['k'] = 'heading?'; u['mdlevel'] = 0; continue
        u['k'] = 'p'

def group_statblocks(U):
    """mark units belonging to a stat block (title + lines)."""
    i = 0; n = len(U); sb_id = 0
    while i < n:
        u = U[i]
        if u['k'] != 'sbt': i += 1; continue
        sb_id += 1; u['sb'] = sb_id
        j = i + 1; last_sec = None
        while j < n:
            v = U[j]; t = v['raw'].strip()
            if v['k'] in ('drop',): j += 1; continue
            if v['k'] == 'hr': v['sb'] = sb_id; v['k'] = 'sbhr'; j += 1; continue
            if v['k'] in ('sbt', 'part', 'area', 'box', 'table', 'htable', 'title', 'adv'): break
            sec = stat_section(t)
            if t.startswith('#') and not sec and not is_stat_line(t): break   # a real markdown heading ends the block
            if sec:
                v['k'] = 'sbsec'; v['sec'] = sec; v['sb'] = sb_id; last_sec = sec; j += 1; continue
            if is_stat_line(t) or (last_sec in ('tac', 'sa', 'eco') and v['k'] in ('p', 'heading?', 'heading') and len(unbold(t)) < 400 and not re.match(r'^(?:\*\*)?(生物|宝藏|发展|奖励|故事奖励|陷阱|危害|特征|人物|创造物|怪物|战利品|剧情)', unbold(t))):
                if v['k'] in ('heading', 'heading?', 'p', 'li', 'area_inline'):
                    v['k'] = 'sbl'; v['sb'] = sb_id; j += 1; continue
            # short unrecognised line, but the block clearly continues right after it
            if v['k'] in ('p', 'heading?', 'heading', 'li', 'area_inline') and len(unbold(t)) <= 160 and not unbold(t).endswith('。'):
                ahead = [w for w in U[j + 1:j + 6] if w['k'] not in ('drop', 'hr')][:3]
                if any(w['k'] not in ('sbt', 'part', 'area', 'title') and (stat_section(w['raw'].strip()) or is_stat_line(w['raw'].strip())) for w in ahead):
                    v['k'] = 'sbl'; v['sb'] = sb_id; j += 1; continue
            # short continuation line after a bare field label (e.g. "专长" / next line)
            if U[j - 1].get('k') == 'sbl' and re.fullmatch(r'(?:\*\*)?(专长|技能|装备|语言|战斗装备|其他装备|特殊特质|特质|SQ)(?:\*\*)?[：:]?', U[j - 1]['raw'].strip()) and v['k'] in ('p', 'heading?', 'heading'):
                v['k'] = 'sbl'; v['sb'] = sb_id; v['join_prev'] = True; j += 1; continue
            break
        i = j

# ---------------------------------------------------------------- alignment (refined)
PROSE_EN = {'RA', 'BODY', 'SIDEBAR', 'SBH', 'INTRO', 'HANDOUT', 'H3', 'H4', 'H2', 'TBLH'}
PROSE_ZH = {'p', 'heading', 'heading?', 'li', 'box', 'area_inline', 'adv', 'part'}

def refine_alignment(ch, U):
    zh, en, res, n = AL.build(ch)   # first pass: global anchor interpolation
    # en offsets
    eoff = []; pos = 0
    for r in en: eoff.append(pos); pos += len(r['text']) + 1
    first_run = {}
    for u, r in zip(U, res):
        u['run0'] = r['runs'][0] if r['runs'] else None
        u['votes'] = r['votes']
    # hard anchors
    def nearest(cands, guess):
        if not cands or guess is None: return None
        c = min(cands, key=lambda j: abs(j - guess))
        return c if abs(c - guess) < max(40, len(en) * 0.08) else None
    area_idx = {}
    for j, r in enumerate(en):
        if r['role'] == 'AREA':
            m = re.match(r'^\s*([A-H]\d{1,2}[a-z]?)\b', r['text'])
            if m: area_idx.setdefault(m.group(1), []).append(j)
    sbt_idx = {}
    for j, r in enumerate(en):
        if r['role'] == 'SBT':
            m = re.search(r'CR\s*([\d/]+|—)', r['text'])
            sbt_idx.setdefault(m.group(1) if m else '?', []).append(j)
    pairs = []
    for k, u in enumerate(U):
        g = u.get('run0')
        if u['k'] in ('area', 'area_inline') and u.get('code'):
            j = nearest(area_idx.get(u['code'], []), g)
            if j is not None: pairs.append((k, j))
        elif u['k'] == 'sbt':
            m = re.search(r'(?:CR|挑战等级)\s*([\d/]+|—|-{2,3})', unbold(u['raw']))
            key = m.group(1) if m else '?'
            key = '—' if key.startswith('-') else key
            j = nearest(sbt_idx.get(key, []), g)
            if j is not None: pairs.append((k, j))
    # monotone chain
    pairs.sort()
    tails, tidx, prev = [], [], [-1] * len(pairs)
    for q, (k, j) in enumerate(pairs):
        p = bisect.bisect_left(tails, j)
        if p > 0: prev[q] = tidx[p - 1]
        if p == len(tails): tails.append(j); tidx.append(q)
        else: tails[p] = j; tidx[p] = q
    chain = []; q = tidx[-1] if tidx else -1
    while q >= 0: chain.append(pairs[q]); q = prev[q]
    chain = chain[::-1]
    for k, j in chain: U[k]['anchor'] = j
    bounds = [(-1, -1)] + chain + [(len(U), len(en))]
    for (za, ea), (zb, eb) in zip(bounds, bounds[1:]):
        zu = [k for k in range(za + 1, zb) if U[k]['k'] in PROSE_ZH]
        er = [j for j in range(ea + 1, eb) if en[j]['role'] in PROSE_EN]
        if not zu or not er:
            for k in range(za + 1, zb):
                if U[k].get('run0') is not None: U[k]['run'] = U[k]['run0']
            continue
        zl = [max(4, len(U[k]['plain'])) for k in zu]; ztot = sum(zl)
        el = [max(10, len(en[j]['text'])) for j in er]; etot = sum(el)
        ecum = [0]
        for x in el: ecum.append(ecum[-1] + x)
        acc = 0
        for k, l in zip(zu, zl):
            mid = (acc + l * 0.5) / ztot * etot; acc += l
            p = min(len(er) - 1, max(0, bisect.bisect_right(ecum, mid) - 1))
            U[k]['run'] = er[p]
        # non prose units: nearest run by first pass, clipped into segment
        for k in range(za + 1, zb):
            if 'run' not in U[k]:
                r0 = U[k].get('run0')
                U[k]['run'] = min(max(r0 if r0 is not None else ea + 1, ea + 1), max(ea + 1, eb - 1))
    for k, j in chain: U[k]['run'] = j
    for u in U:
        j = u.get('run')
        if j is not None and 0 <= j < len(en):
            u['en_role'] = en[j]['role']; u['page'] = en[j]['page']; u['en_y'] = en[j]['y']
    return en

# ---------------------------------------------------------------- figures
def load_figures(ch):
    p = os.path.join(ROOT, 'src/config/figures.json')
    if not os.path.exists(p): return []
    figs = json.load(open(p, encoding='utf-8'))
    return [dict(name=k, **v) for k, v in figs.items() if v.get('chapter') == ch and v.get('use', True)]

def place_figures(ch, U, en):
    """return {unit_index: [figure,...]} inserted *before* that unit (at a block boundary)."""
    figs = load_figures(ch)
    out = {}
    # unit start positions by en (page, y)
    keyed = [(U[k]['page'], U[k].get('en_y', 0), k) for k in range(len(U)) if U[k].get('page') and U[k]['k'] != 'drop']
    for f in figs:
        if 'before_line' in f:
            k = next((i for i, u in enumerate(U) if u['line'] >= f['before_line']), len(U) - 1)
        else:
            pg, y = f['page'], f.get('y', 0)
            cands = [k for (p, yy, k) in keyed if (p, yy) >= (pg, y - 5)]
            k = cands[0] if cands else len(U) - 1
            # prefer a unit on the same page that starts after the figure's anchor
        k = boundary_after(U, k, f.get('kind'))
        out.setdefault(k, []).append(f)
    return out

def boundary_after(U, k, kind=None):
    """move k forward so the figure is not inserted inside a stat block / read-aloud run / box run."""
    n = len(U)
    while k < n and (U[k].get('k') in ('sbl', 'sbsec', 'sbhr', 'drop') or (k > 0 and U[k].get('k') == 'p' and U[k].get('role') == 'RA' and U[k - 1].get('role') == 'RA')):
        k += 1
    return min(k, n - 1)

# ---------------------------------------------------------------- emit
def esc_attr(s): return s.replace('"', '&quot;')

def stat_line_md(t):
    t = clean_inline(t)
    t = re.sub(r'\*\*', '', t).strip()
    return t

def emit(ch, U, en, figs_at):
    cfg = CFG[str(ch)]
    out = []
    w = out.append
    w('---')
    w(f'chapter: {ch}')
    w(f'title: {cfg["title"]}')
    w(f'en: {cfg["en"]}')
    w(f'author_en: {cfg.get("author_en", "")}')
    if cfg.get('author_zh'): w(f'author_zh: {cfg["author_zh"]}')
    w('---')
    w('')
    ins = {d['before']: d for d in cfg.get('insert_parts', [])}
    seen_pages = set()
    i = 0; n = len(U)
    open_box = None    # 'readaloud' | 'sidebar'

    def close_box():
        nonlocal open_box
        if open_box: w(':::'); w(''); open_box = None

    def orig_marker(u):
        pg = u.get('page')
        if pg and pg not in seen_pages and (not seen_pages or pg > max(seen_pages)):
            seen_pages.add(pg)
            return f'@orig {pg}'
        return None

    started_main = False
    while i < n:
        u = U[i]
        if u['k'] in ('drop', 'title', 'hr'):
            i += 1; continue
        if u['zone'] == 'main' and not started_main:
            close_box(); started_main = True
            w('@chapter-opener'); w('')
        if u['line'] in ins:
            close_box(); d = ins.pop(u['line'])
            w(f'## {d["title"]} {{.part label="{d["label"]}" inserted="1"}}'); w('')
        if i in figs_at and u['k'] not in ('sbl', 'sbsec'):
            close_box()
            for f in figs_at[i]: w(f'@figure {f["name"]}'); w('')
        m = orig_marker(u)
        if m and u['k'] not in ('sbl', 'sbsec', 'sbhr'):
            w(m)
        k = u['k']
        role = u.get('role')
        if k == 'part':
            close_box(); label, title = u['part']
            w(f'## {title} {{.part label="{label}"}}'); w('')
            i += 1; continue
        if k == 'adv':
            close_box()
            lines = []
            while i < n and U[i]['k'] == 'adv':
                lines.append(clean_inline(re.sub(r'^#+\s*', '', U[i]['raw'].strip()))); i += 1
            w('::: advancement')
            for t in lines:
                t = t.strip('"“”')
                w(t); w('')
            w(':::'); w(''); continue
        if k == 'sbt':
            close_box()
            title = clean_inline(unbold(u['raw']))
            # title split over two lines in the source ("### 人类僵尸" + "挑战等级1/2"): join them
            if re.fullmatch(r'(?:CR|挑战等级)\s*[\d/—\-–]+', title, re.I):
                k2 = len(out) - 1
                while k2 >= 0 and not out[k2].strip(): k2 -= 1
                if k2 >= 0 and re.match(r'^#{2,5} [^{]+$', out[k2]):
                    title = out[k2].lstrip('#').strip() + ' ' + title; del out[k2:]
            w('::: statblock')
            w(f'@title {title}')
            i += 1
            while i < n and (U[i].get('sb') == u['sb'] or (U[i]['k'] == 'drop' and i + 1 < n and U[i + 1].get('sb') == u['sb'])):
                v = U[i]
                if v['k'] == 'drop':
                    pass
                elif v['k'] == 'sbsec':
                    w(f'@sec {clean_inline(unbold(v["raw"]))}')
                elif v['k'] == 'sbl':
                    t = stat_line_md(v['raw'])
                    if v.get('join_prev') and out and out[-1].startswith('@field '):
                        out[-1] = out[-1] + ' ' + t
                    elif re.fullmatch(r'(专长|技能|装备|语言|战斗装备|其他装备|特殊特质|特质|SQ)[：:]?', t):
                        w(f'@field {t}')
                    else:
                        w(t)
                i += 1
            w(':::'); w(''); continue
        if k in ('sbl', 'sbsec', 'sbhr'):
            if k != 'sbhr':    # orphan stat line: never lose it, emit as plain paragraph
                close_box(); w(clean_inline(u['raw'].strip())); w('')
            i += 1; continue
        if k == 'area':
            close_box()
            t = clean_inline(unbold(u['raw']))
            w(f'#### {t} {{.area code="{u["code"]}"}}'); w('')
            i += 1; continue
        if k == 'box':
            close_box()
            cls = 'handout' if (u.get('en_role') == 'HANDOUT' or re.search(r'HANDOUT|附录\s*#|讲义', u['raw'])) else 'sidebar'
            w(f'::: {cls} html')
            w(clean_box_html(u['raw']))
            w(':::'); w(''); i += 1; continue
        if k == 'htable':
            close_box(); w('::: rawtable'); w(clean_box_html(u['raw'])); w(':::'); w(''); i += 1; continue
        if k == 'table':
            close_box(); w('\n'.join(clean_inline(r) for r in u['raw'].split('\n')).replace('|**', '|').replace('**|', '|')); w(''); i += 1; continue
        if k == 'dicetable':
            close_box(); w(u['md']); w(''); i += 1; continue
        if k == 'li':
            if role not in ('RA', 'SIDEBAR'): close_box()
            w(clean_inline(u['raw']));
            if i + 1 >= n or U[i + 1]['k'] != 'li': w('')
            i += 1; continue
        if k in ('heading', 'heading?'):
            t = clean_inline(unbold(u['raw']))
            lvl = u.get('level', 3)
            if lvl == 0:   # demoted to paragraph
                pass
            else:
                if u.get('role') == 'SBH':
                    close_box(); w('::: sidebar'); open_box = 'sidebar'
                    w(f'#### {t} {{.sbh}}'); w('')
                else:
                    if not (open_box == 'sidebar' and u.get('in_sidebar')): close_box()
                    w(f'{"#" * lvl} {t}'); w('')
                i += 1; continue
        # paragraphs
        want = {'RA': 'readaloud', 'SIDEBAR': 'sidebar', 'HANDOUT': 'handout-text', 'INTRO': 'intro'}.get(role)
        if want == 'sidebar' and open_box == 'sidebar':
            pass
        elif want != open_box:
            if not (open_box == 'sidebar' and u.get('in_sidebar')):
                close_box()
                if want: w(f'::: {want}'); open_box = want
        t = clean_inline(u['raw'])
        if k == 'area_inline':
            m = re.match(r'^(?:\*\*)?\s*([A-H]\d{1,2}[a-z]?[\.．]?\s*[^：:*]{1,30}[：:])(?:\*\*)?\s*(.*)$', t)
            if m: t = f'**{m.group(1).strip()}** {m.group(2)}'
            t = '{.area-inline} ' + t
        w(t); w('')
        i += 1
    close_box()
    return '\n'.join(out) + '\n'

def clean_box_html(raw):
    s = raw.replace('\u200b', '')
    s = re.sub(r'<colgroup>.*?</colgroup>', '', s, flags=re.S)
    m = re.search(r'<td[^>]*>(.*)</td>', s, flags=re.S)
    if m and s.count('<td') == 1: s = m.group(1)
    s = re.sub(r'\sstyle="[^"]*"', '', s)
    s = s.replace('------', '——')
    return s.strip()

# ---------------------------------------------------------------- roles & headings
def assign_roles(ch, U):
    for k, u in enumerate(U):
        er = u.get('en_role')
        if u['k'] in ('p', 'li', 'area_inline'):
            u['role'] = er if er in ('RA', 'SIDEBAR', 'HANDOUT', 'INTRO') else 'BODY'
            if u['k'] == 'area_inline': u['role'] = 'BODY'
            # labelled GM paragraphs are never read-aloud
            if u['role'] == 'RA' and re.match(r'^(?:\*\*)?[^，。：:]{1,12}[：:]', unbold(u['raw'])):
                u['role'] = 'BODY'
        elif u['k'] in ('heading', 'heading?'):
            if u['k'] == 'heading?' and er not in ('H2', 'H3', 'H4', 'SBH', 'INTRO', 'AREA', 'H1'):
                u['k'] = 'p'; u['role'] = er if er in ('RA', 'SIDEBAR', 'HANDOUT') else 'BODY'; continue
            u['role'] = 'SBH' if er == 'SBH' else 'H'
            md = u.get('mdlevel', 0)
            if er in ('H3', 'H2'): u['level'] = 3
            elif er in ('H4', 'INTRO'): u['level'] = 4
            elif md and md <= 2: u['level'] = 3
            else: u['level'] = 4 if md >= 4 else 3
    # read-aloud smoothing: a lone RA paragraph between body paragraphs keeps RA only if
    # it directly follows an area heading or a 'read aloud' cue
    for k, u in enumerate(U):
        if u.get('role') == 'RA':
            prev = U[k - 1] if k else None
            if prev and prev['k'] in ('area',) : continue
            if prev and prev.get('role') == 'RA': continue
            nxt = U[k + 1] if k + 1 < len(U) else None
            if nxt and nxt.get('role') == 'RA': continue
            if prev and re.search(r'(朗读|转述|宣读|读出|念出)', prev['raw']): continue
            if len(u['plain']) > 40 and prev and prev['k'] in ('heading', 'heading?'): continue
            if prev and prev.get('role') == 'BODY' and nxt and nxt.get('role') == 'BODY' and len(u['plain']) < 60:
                u['role'] = 'BODY'
    # sidebars: only an SBH-aligned heading opens a sidebar; following SIDEBAR-role paras stay in it.
    # Stray SIDEBAR / HANDOUT / INTRO roles without such evidence fall back to body text.
    in_sb = False; prev_k = None; in_ho = False
    for u in U:
        if u['k'] in ('heading', 'heading?') and u.get('role') == 'SBH': in_sb = True; in_ho = False; prev_k = 'sbh'; continue
        if u['k'] in ('p', 'li'):
            t = unbold(u['raw'])
            if re.match(r'^#?\s*(手记|讲义|附录)\s*#?\s*\d', t) and len(t) < 16:
                u['role'] = 'HANDOUT'; u['ho_label'] = True; in_ho = True; in_sb = False; prev_k = 'p'; continue
            if in_ho and u.get('en_role') in ('HANDOUT', 'BODY', 'RA', 'SIDEBAR') and len(t) > 0:
                u['role'] = 'HANDOUT'; in_ho = u.get('en_role') == 'HANDOUT'; prev_k = 'p'; continue
            in_ho = False
            if in_sb and u.get('en_role') in ('SIDEBAR', 'SBH'):
                u['in_sidebar'] = True; u['role'] = 'SIDEBAR'; prev_k = 'p'; continue
            in_sb = False
            if u.get('role') in ('SIDEBAR', 'HANDOUT'): u['role'] = 'BODY'
            if u.get('role') == 'INTRO' and prev_k not in ('part', 'intro'): u['role'] = 'BODY'
            prev_k = 'intro' if u.get('role') == 'INTRO' else 'p'
        elif u['k'] in ('drop',):
            continue
        else:
            in_sb = False; in_ho = False; prev_k = u['k']

def detect_dice_tables(U):
    """plain-text dice/result tables (lines starting with a number range)."""
    RANGE = re.compile(r'^(?:\*\*)?(\d{1,3}(?:\s*[–\-—~～]+\s*\d{1,3})?|\d{2,3}\+?)(?:\*\*)?\s+(\S.*)$')
    i = 0; n = len(U)
    while i < n:
        u = U[i]
        hdr = None
        if u['k'] in ('heading?', 'p', 'heading') and re.match(r'^(?:\*\*)?d(%|\d+)\b', u['plain']) and len(u['plain']) < 60:
            hdr = i
        if hdr is None: i += 1; continue
        j = i + 1; rows = []
        while j < n and U[j]['k'] in ('p', 'heading?', 'heading') and RANGE.match(clean_inline(U[j]['raw']).replace('**', '')) and len(U[j]['plain']) < 260:
            rows.append(j); j += 1
        if len(rows) >= 2:
            h = clean_inline(U[hdr]['raw']).replace('**', '').split()
            body = []
            ncol = 3 if len(h) >= 3 else 2
            for r in rows:
                t = clean_inline(U[r]['raw']).replace('**', '')
                m = RANGE.match(t); rest = m.group(2)
                if ncol == 3:
                    mm = re.match(r'^(.*\S)\s+(\S+)$', rest)
                    cols = [m.group(1), mm.group(1), mm.group(2)] if mm and len(mm.group(2)) <= 8 else [m.group(1), rest, '']
                else:
                    cols = [m.group(1), rest]
                body.append(cols)
            hh = [h[0], ' '.join(h[1:-1]) if ncol == 3 else ' '.join(h[1:]), h[-1]] if ncol == 3 else [h[0], ' '.join(h[1:])]
            md = '| ' + ' | '.join(hh) + ' |\n|' + '---|' * ncol + '\n' + '\n'.join('| ' + ' | '.join(c.replace('|', '\\|') for c in cols) + ' |' for cols in body)
            U[hdr]['k'] = 'dicetable'; U[hdr]['md'] = '{.dice}\n' + md
            for r in rows: U[r]['k'] = 'drop'; U[r]['merged'] = True
            i = j
        else:
            i += 1

def norm_txt(t):
    return re.sub(r'[\s*#：:]', '', t).lower()

def mark_dup_headings(ch, U):
    """the translation often repeats a markdown heading as a bold line right after it
    (`###### X CR2` + `**X CR2**`).  Keep the heading, drop the exact duplicate; logged for QA."""
    log = []
    for a, b in zip(U, U[1:]):
        m = re.match(r'^#{1,6}\s+(.*)$', a['raw'].strip())
        if m and a['kind'] == 'md' and b['kind'] == 'md' and norm_txt(m.group(1)) and norm_txt(m.group(1)) == norm_txt(b['raw']):
            b['dup'] = True; log.append(dict(heading_line=a['line'], dup_line=b['line'], text=b['raw'].strip()))
    os.makedirs(os.path.join(ROOT, 'work/qa'), exist_ok=True)
    json.dump(log, open(os.path.join(ROOT, f'work/qa/dup_headings_ch{ch}.json'), 'w'), ensure_ascii=False, indent=0)
    return log

def run(ch):
    os.makedirs(os.path.join(ROOT, 'work/mapping'), exist_ok=True)
    U = units(chapter_files()[ch])
    mark_dup_headings(ch, U)
    classify(ch, U)
    for u in U:
        if u.get('dup'): u['k'] = 'drop'
    # "名称（CR 12）" is a stat-block title only when stat lines follow; otherwise an encounter/area heading
    for k, u in enumerate(U):
        if u['k'] == 'sbt' and re.search(r'[（(]\s*(?:CR|挑战等级)\s*[\d/]+\s*[)）]\s*$', unbold(u['raw'])):
            nxt = next((v for v in U[k + 1:] if v['k'] not in ('drop', 'hr')), None)
            if not (nxt and re.match(r'^(?:\*\*)?\s*(XP|经验)', unbold(nxt['raw']), re.I)):
                u['k'] = 'heading'; u['mdlevel'] = len(re.match(r'^#*', u['raw'].strip()).group(0))
    group_statblocks(U)
    en = refine_alignment(ch, U)
    detect_dice_tables(U)
    assign_roles(ch, U)
    figs_at = place_figures(ch, U, en)
    md = emit(ch, U, en, figs_at)
    os.makedirs(os.path.join(ROOT, 'src/chapters'), exist_ok=True)
    open(os.path.join(ROOT, f'src/chapters/ch{ch}.md'), 'w', encoding='utf-8').write(md)
    # unit map for QA / figure placement
    json.dump([{k: u.get(k) for k in ('i', 'line', 'k', 'role', 'en_role', 'page', 'en_y', 'run', 'code', 'sb', 'level', 'merged')} for u in U],
              open(os.path.join(ROOT, f'work/mapping/units_ch{ch}.json'), 'w'), ensure_ascii=False)
    from collections import Counter
    print(ch, Counter(u['k'] for u in U).most_common(), Counter(u.get('role') for u in U if u['k'] == 'p').most_common())

if __name__ == '__main__':
    for ch in (map(int, sys.argv[1:]) if len(sys.argv) > 1 else chapter_numbers()):
        run(ch)
