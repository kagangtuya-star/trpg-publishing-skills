"""Art <-> content mapping report: output/reports/art_mapping.md
For every placed figure: chapter, original page, kind, source file, the semantic-source line it is
anchored before, the nearest heading, and the final book page where it is rendered."""
import json, os, re, sys
import pymupdf
sys.path.insert(0, os.path.dirname(__file__))
from zhparse import ROOT, chapter_numbers
from runtime import FINAL

def main():
    figs = json.load(open(os.path.join(ROOT, 'src/config/figures.json'), encoding='utf-8'))
    maps = json.load(open(os.path.join(ROOT, 'src/config/maps.json'), encoding='utf-8'))
    st = json.load(open(os.path.join(ROOT, 'work/pdf/state.json')))
    caps = json.load(open(os.path.join(ROOT, 'src/config/captions.json'), encoding='utf-8'))
    book = pymupdf.open(FINAL)
    rows = []
    for ch in chapter_numbers():
        lines = open(os.path.join(ROOT, f'src/chapters/ch{ch}.md'), encoding='utf-8').read().split('\n')
        head = ''; opener = lines.index('@chapter-opener') if '@chapter-opener' in lines else 0
        # rendered page of each figure: chapter pdf pages carrying an image of the same pixel size
        cpdf = pymupdf.open(os.path.join(ROOT, f'work/pdf/ch{ch}.pdf'))
        sizes = {}
        for pi, p in enumerate(cpdf):
            for im in p.get_images(full=True):
                sizes.setdefault((im[2], im[3]), []).append(pi)
        for n, l in enumerate(lines, 1):
            m = re.match(r'^#{2,4}\s+(.*?)\s*(\{.*\})?$', l)
            if m: head = re.sub(r'\*\*', '', m.group(1))
            m = re.match(r'^@figure\s+(\S+)', l)
            if not m: continue
            fid = m.group(1); f = figs.get(fid, {})
            src = f.get('src', '')
            stem = os.path.splitext(os.path.basename(src))[0]
            opt = next((p for p in (f'assets/optimized/{stem}.jpg', f'assets/optimized/{stem}.png') if os.path.exists(os.path.join(ROOT, p))), src)
            page = ''
            try:
                from PIL import Image
                w, h = Image.open(os.path.join(ROOT, opt)).size
                pg = sizes.get((w, h))
                if pg: page = str(st[f'ch{ch}_start'] + pg[0]) if not (ch == 1 and n < opener) else ''
            except Exception:
                pass
            zone = '引言' if (ch == 1 and n < opener) else f'第{ch}章'
            title = maps.get(fid, {}).get('title', '') if f.get('kind') == 'map' else caps.get(fid, {}).get('caption', '')
            rows.append((zone, f.get('page', ''), f.get('kind', ''), fid, title, head if not (ch == 1 and n < opener) else head, n, page, opt))
    os.makedirs(os.path.join(ROOT, 'output/reports'), exist_ok=True)
    out = ['# 美术资源—内容映射表', '',
           f'共放置 {len(rows)} 幅（含地图 {sum(1 for r in rows if r[2] == "map")} 幅）。'
           '“原版页”为插图在英文原版中的页码；“锚点”为语义源 `src/chapters/chN.md` 中 `@figure` 所在行及其所属最近标题；'
           '“图注 / 地图标题”：地图为中文化标题；角色、怪物、物品图为成书图注（来源与核对见 `src/config/caption_glossary.json`、校对报告第 4 节）。“成书页”按图像像素尺寸在章节 PDF 中检出（引言部分在 front.pdf，未列页码）。', '',
           '| 区段 | 原版页 | 类型 | 资源 ID | 图注 / 地图标题 | 所属标题 | 源行 | 成书页 | 使用文件 |', '|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        out.append('| ' + ' | '.join(str(x).replace('|', '/') for x in r) + ' |')
    excluded = [k for k, v in figs.items() if not v.get('use') or v.get('kind') == 'handout-bg']
    out += ['', '## 未作为插图放置的资源', '',
            '- 讲义羊皮纸底纹（handout-bg，用作讲义框背景）：' + '、'.join(k for k, v in figs.items() if v.get('kind') == 'handout-bg'),
            '- 纯红色锦缎纹理（原版侧栏底图）与两块空白装饰牌：见 `scripts/figures.py` 中 `TEXTURE` 集合，已排除。',
            '- 章首页、书名页、目录缩略图等：由 `scripts/make_assets.py` 处理为页面背景（去除英文文字后的章首跨页、封面、书名页、边框）。',
            f'- 其余在 figures.json 中 use=false 的条目：{", ".join(k for k in excluded if figs[k].get("kind") != "handout-bg") or "无"}']
    open(os.path.join(ROOT, 'output/reports/art_mapping.md'), 'w', encoding='utf-8').write('\n'.join(out) + '\n')
    print(len(rows), 'figures;', sum(1 for r in rows if r[7]), 'with book page')

if __name__ == '__main__':
    main()
