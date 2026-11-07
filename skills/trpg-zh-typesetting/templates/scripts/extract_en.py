"""Extract role-tagged text runs from the original English PDF (by font), per chapter.
Output: work/extracted/en/chN.json  -> list of runs {role, text, page, y, x}
"""
import pymupdf, json, re, sys, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
CHAPTERS = {int(k): v['pages'] for k, v in CFG.items() if k.isdigit()}
ROLES = json.load(open(os.path.join(ROOT, 'src/config/roles.json'), encoding='utf-8'))

def role_of(span):
    f, s, col = span['font'], round(span['size'], 1), '%06x' % span['color']
    for rule in ROLES['rules']:
        if 'font_prefix' in rule and not f.startswith(rule['font_prefix']): continue
        if 'color' in rule and col != rule['color']: continue
        if s < rule.get('min_size', 0) or s > rule.get('max_size', float('inf')): continue
        return rule['role']  # null explicitly excludes headers, folios or map labels
    return ROLES.get('default_role', 'OTHER')

def page_lines(page):
    out = []
    W = page.rect.width
    for b in page.get_text('dict')['blocks']:
        if b['type'] != 0: continue
        bx0, by0, bx1, by1 = b['bbox']
        for l in b['lines']:
            roles = {}
            txt = ''
            for s in l['spans']:
                r = role_of(s)
                t = s['text']
                if r is None: continue
                roles[r] = roles.get(r, 0) + len(t.strip())
                txt += t
            if not txt.strip() or not roles: continue
            role = max(roles, key=roles.get)
            if role in ('BODY',) and roles.get('SB', 0) > 0 and roles.get('SB') >= roles['BODY'] * .3: role = 'SB'
            x0, y0, x1, y1 = l['bbox']
            full = (bx1 - bx0) > W * 0.6
            col = 0 if (x0 + x1) / 2 < W / 2 or full else 1
            out.append(dict(role=role, text=txt, x=x0, y=y0, col=col, full=full))
    # reading order: full-width blocks at top band first, then columns
    out.sort(key=lambda r: (r['col'], r['y'], r['x']))
    return out

def main():
    d = pymupdf.open(os.path.join(ROOT, 'input/original.pdf'))
    os.makedirs(os.path.join(ROOT, 'work/extracted/en'), exist_ok=True)
    for ch, (a, b) in CHAPTERS.items():
        runs = []
        for pn in range(a, b + 1):
            for ln in page_lines(d[pn - 1]):
                t = ln['text'].replace('­', '')
                if runs and runs[-1]['role'] == ln['role'] and runs[-1]['page'] == pn and abs(ln['y'] - runs[-1]['ylast']) < 30 and ln['role'] not in ('AREA', 'H1', 'H2', 'H3', 'CAPTION', 'SBT', 'LABEL'):
                    r = runs[-1]
                    if r['text'].endswith('-') and not r['text'].endswith(' -'):
                        r['text'] = r['text'][:-1] + t
                    else:
                        r['text'] += ' ' + t
                    r['ylast'] = ln['y']
                elif runs and runs[-1]['role'] == ln['role'] and ln['role'] in ('AREA', 'H1', 'H2', 'H3', 'SBT') and runs[-1]['page'] == pn and abs(ln['y'] - runs[-1]['ylast']) < 16:
                    runs[-1]['text'] += ' ' + t; runs[-1]['ylast'] = ln['y']
                else:
                    runs.append(dict(role=ln['role'], text=t, page=pn, y=round(ln['y']), ylast=ln['y'], x=round(ln['x'])))
        for r in runs:
            r['text'] = re.sub(r'\s+', ' ', r['text']).strip(); r.pop('ylast')
        json.dump(runs, open(os.path.join(ROOT, f'work/extracted/en/ch{ch}.json'), 'w'), ensure_ascii=False, indent=0)
        print(ch, len(runs))

if __name__ == '__main__':
    main()
