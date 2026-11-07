"""Split a translated chapter Markdown into source units (paragraph / html block / md table)."""
import re, glob, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def chapter_numbers():
    """chapter numbers declared in src/config/chapters.json (keys that are digits), ascending"""
    import json
    cfg = json.load(open(os.path.join(ROOT, 'src/config/chapters.json'), encoding='utf-8'))
    return sorted(int(k) for k in cfg if k.isdigit())

def chapter_files():
    fs = sorted(glob.glob(os.path.join(ROOT, 'input/translation/*.md')))
    out = {}
    for f in fs:
        name = os.path.basename(f)
        if not re.match(r'^\d{3}(?:\D|$)', name):
            raise ValueError(f'Translation name must start with a three-digit chapter number: {name}')
        ch = int(name[:3])
        if ch in out: raise ValueError(f'Duplicate chapter number: {ch}')
        out[ch] = f
    missing = set(chapter_numbers()) - set(out)
    if missing: raise ValueError(f'Missing translation chapters: {sorted(missing)}')
    return out

def plain(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = s.replace('\\', '').replace('**', '').replace('------', '——')
    s = re.sub(r'^#+\s*', '', s)
    return s.strip()

def units(path):
    lines = open(path, encoding='utf-8').read().split('\n')
    out = []; i = 0
    while i < len(lines):
        ln = lines[i]
        if not ln.strip(): i += 1; continue
        if ln.strip().startswith('<div') or ln.strip().startswith('<table'):
            j = i; depth_end = '</div>' if ln.strip().startswith('<div') else '</table>'
            while j < len(lines) and depth_end not in lines[j]: j += 1
            raw = '\n'.join(lines[i:j + 1]); out.append(dict(kind='html', raw=raw, line=i + 1)); i = j + 1; continue
        if ln.lstrip().startswith('|'):
            j = i
            while j < len(lines) and lines[j].lstrip().startswith('|'): j += 1
            out.append(dict(kind='mdtable', raw='\n'.join(lines[i:j]), line=i + 1)); i = j; continue
        out.append(dict(kind='md', raw=ln, line=i + 1)); i += 1
    for k, u in enumerate(out):
        u['i'] = k; u['plain'] = plain(u['raw'])
    return out
