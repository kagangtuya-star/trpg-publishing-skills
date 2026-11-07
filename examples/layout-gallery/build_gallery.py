"""Build six original two-page TRPG layout studies, PDFs, previews and offline gallery.

Requires the repository's installed Python dependencies, Vivliostyle and a local browser.
No downloads. No source-project files or external art are needed.
"""
import argparse
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
import pymupdf
from PIL import Image

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]


def esc(s): return html.escape(str(s), quote=True)


def svg_text(x, y, text, fill, size=10, anchor='middle'):
    return f'<text x="{x}" y="{y}" fill="{fill}" font-size="{size}" text-anchor="{anchor}">{esc(text)}</text>'


def diagram(kind, color):
    dark = '#263a3b'
    s = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 620 194" style="font-family:Demo CJK,sans-serif" role="img">']
    if kind == 'abbey':
        s += [f'<circle cx="460" cy="56" r="35" fill="{color}" opacity=".1"/>',
              f'<path d="M50 161L130 161L130 103L168 77L206 103L206 161L276 161L276 57L310 23L344 57L344 161L414 161L414 103L452 77L490 103L490 161L570 161" fill="{color}" opacity=".8"/>',
              '<path d="M281 59H339M288 66V90M331 66V90M303 110V159M317 110V159" stroke="#f4efe4" fill="none" stroke-width="4"/>',
              '<circle cx="310" cy="77" r="15" fill="#f4efe4"/><path d="M310 66V77L319 83" stroke="#7d242b" fill="none" stroke-width="2"/>']
        for y in (135, 151, 170):
            s.append(f'<path d="M0 {y} Q80 {y-17} 160 {y}T320 {y}T480 {y}T640 {y}" fill="none" stroke="#f4efe4" stroke-width="12" opacity=".8"/>')
        s += [svg_text(82, 47, 'I · 院门', color, 10), svg_text(530, 47, 'III · 钟楼', color, 10), svg_text(310, 186, '每一次钟响，都改变同一座建筑。', color, 10)]
    elif kind == 'clues':
        s.append(f'<path d="M118 69L307 69L500 69M118 69Q310 180 500 69" fill="none" stroke="{color}" stroke-width="1.5" stroke-dasharray="5 4"/>')
        for x, no, title, detail in [(118,'E01','邮局','蓝色纸纤维'),(307,'E02','灯塔','重复的潮位'),(500,'E03','六码头','未来的目击')]:
            s += [f'<rect x="{x-71}" y="31" width="142" height="76" fill="#fffdf4" stroke="{color}"/>',
                  svg_text(x, 50, no, color, 9), svg_text(x, 74, title, dark, 15), svg_text(x, 93, detail, color, 9)]
        s += [svg_text(310, 156, '共同结论：最后一班船正在提前靠岸', color, 12), svg_text(310, 178, '地点可互相导向；关键证据保留替代入口。', color, 9)]
    elif kind == 'hex':
        for row in range(3):
            for col in range(9):
                # Flat-top hexes: horizontal step 1.5r, vertical step sqrt(3)r.
                cx = 143 + col * 40.5; cy = 32 + row * math.sqrt(3)*27 + (col % 2) * math.sqrt(3)*13.5
                points = ' '.join(f'{cx+27*math.cos(math.radians(60*k)):.1f},{cy+27*math.sin(math.radians(60*k)):.1f}' for k in range(6))
                fill = '#d6d4b4' if (row + col) % 4 == 0 else 'none'
                s.append(f'<polygon points="{points}" fill="{fill}" stroke="#b7ba9b" stroke-width=".8"/>')
        s.append(f'<path d="M143 78.8Q230 40 305 78.8T467 125.5" fill="none" stroke="{color}" stroke-dasharray="4 4" stroke-width="2"/>')
        for x,y,t in [(143,78.8,'A1'),(305,78.8,'B2'),(467,125.5,'C3')]:
            s += [f'<circle cx="{x}" cy="{y}" r="15" fill="{color}"/>',svg_text(x,y+4,t,'#fff9e8',10)]
        s += [svg_text(32, 37, 'N', color, 13),f'<path d="M32 46V86M26 57L32 46L38 57" stroke="{color}" fill="none"/>',svg_text(310, 185, '每格约半日行程 · 虚线为已知商路', color, 10)]
    elif kind == 'dungeon':
        for x in range(0,621,20): s.append(f'<path d="M{x} 0V194" stroke="#cfd9d9" stroke-width=".4"/>')
        for y in range(0,195,20): s.append(f'<path d="M0 {y}H620" stroke="#cfd9d9" stroke-width=".4"/>')
        s.append(f'<path d="M90 69H232V135H354V69H470M90 69V135H354M232 69V28H470V69" fill="none" stroke="{color}" stroke-width="12"/>')
        for x,y,w,h,n in [(45,42,90,54,'01'),(194,42,76,54,'02'),(314,105,80,61,'03'),(49,112,82,54,'04'),(316,41,78,55,'05'),(432,40,87,57,'06')]:
            s += [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="#edf0ee" stroke="{color}" stroke-width="2"/>',
                  f'<circle cx="{x+w/2}" cy="{y+h/2}" r="13" fill="{color}"/>',svg_text(x+w/2,y+h/2+4,n,'#fff9ed',10)]
        s += [f'<path d="M470 98V149H556" fill="none" stroke="{color}" stroke-dasharray="4 4" stroke-width="2"/>',svg_text(561,171,'第七道影',color,10),svg_text(220,186,'实线：已知通路　虚线：不稳定连接',color,9)]
    elif kind == 'factions':
        for d in ['M130 60Q300 -6 490 60','M130 60Q130 145 310 137','M490 60Q490 145 310 137']:
            s.append(f'<path d="{d}" stroke="{color}" stroke-width="1.2" fill="none"/>')
        for x,y,title,detail in [(130,65,'灯匠会','线路 / 秩序'),(490,65,'摊贩联社','消息 / 自由'),(310,137,'巡夜队','封桥 / 失物')]:
            s += [f'<rect x="{x-61}" y="{y-23}" width="122" height="47" rx="23" fill="{color}"/>',svg_text(x,y-1,title,'#fff6ed',13),svg_text(x,y+14,detail,'#e8d9df',8)]
        s += [svg_text(310,31,'供电 ↔ 登记',color,10),svg_text(185,128,'庇护',color,9),svg_text(435,128,'线索',color,9),svg_text(310,188,'黑色木箱：所有利益交汇的焦点',color,10)]
    else:
        for x,y,r in [(33,29,1),(74,115,2),(142,33,1),(209,162,1),(295,27,2),(372,150,1),(450,33,1),(555,138,2),(584,51,1)]:
            s.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#ddca99"/>')
        s.append('<path d="M72 107Q170 10 250 83T420 83T554 100" stroke="#d5bb7a" stroke-width="2" fill="none" stroke-dasharray="4 5"/>')
        for x,y,n,t in [(72,107,'I','港口承诺'),(230,76,'II','航道失约'),(400,103,'III','回声群岛'),(554,100,'IV','归航之地')]:
            s += [f'<circle cx="{x}" cy="{y}" r="18" fill="#203b55" stroke="#ddca99"/>',svg_text(x,y+4,n,'#fff5d5',12),svg_text(x,y+37,t,'#f3e6c2',10)]
        s.append(svg_text(310,183,'让后续章节回应开篇的承诺。','#dbc79c',10))
    s.append('</svg>')
    return ''.join(s)


def clock(color, kind):
    parts = ['<svg viewBox="0 0 225 110" xmlns="http://www.w3.org/2000/svg">']
    labels = {'abbey':['抵达','发现','抉择'], 'clues':['事实','解释','复核'], 'hex':['清晨','行进','扎营'],
              'dungeon':['观察','互动','后果'], 'factions':['目标','代价','变化'], 'voyage':['回顾','选择','传递']}[kind]
    for i, label in enumerate(labels):
        x = 36 + 76*i
        parts += [f'<circle cx="{x}" cy="42" r="22" fill="none" stroke="{color}" stroke-width="1"/>',
                  svg_text(x,48,f'0{i+1}',color,15),svg_text(x,87,label,color,11)]
        if i < 2: parts.append(f'<path d="M{x+25} 42H{x+50}" stroke="{color}"/>')
    return ''.join(parts)+'</svg>'


def render(demos, offset=0):
    css = (HERE / 'theme.css').read_text(encoding='utf-8')
    out = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><title>TRPG 中文排版结构样张</title><style>'+css+'</style></head><body>']
    for i, d in enumerate(demos, offset + 1):
        cls = ['linear','investigation','hexcrawl','dungeon','factions','campaign'][i-1]
        style = f'--accent:{d["accent"]};--paper:{d["paper"]}'
        def top(page):
            return f'<section class="sheet {cls} p{page}" style="{style}"><div class="topline"><span>TRPG PUBLISHING / LAYOUT STUDIES</span><span>{esc(d["kind"])}</span></div>'
        def bottom(page):
            return f'<footer class="bottom"><span>{esc(d["title"])} · 原创排版样张</span><span class="page-number">{i:02d} — {page:02d} / 02</span></footer></section>'
        out += [top(1), f'<header class="hero"><div class="serial">{i:02d}</div><p class="eyebrow">{esc(d["code"])} / {esc(d["en"])}</p><h1>{esc(d["title"])}</h1><p class="subtitle">{esc(d["subtitle"])}</p></header>',
                '<div class="spec">'+''.join('<span>'+esc(x)+'</span>' for x in d['spec'])+'</div>',
                '<p class="lead">'+esc(d['intro'])+'</p>', '<figure class="art">'+diagram(d['diagram'],d['accent'])+'</figure>',
                '<aside class="readaloud"><span class="label">场景开场 · 可供朗读</span><p>'+esc(d['readaloud'])+'</p></aside>',
                '<div class="three">'+''.join('<section><h3>'+esc(t)+'</h3><p>'+esc(p)+'</p></section>' for t,p in d['sections'])+'</div>',bottom(1),
                top(2),'<p class="eyebrow">RUNNING THE ADVENTURE / 主持人参考</p><h2>'+esc(d['p2_title'])+'</h2><p class="lead">'+esc(d['p2_intro'])+'</p>',
                '<div class="toolrow"><aside class="panel"><h3>'+esc(d['stats'][0])+'</h3>'+''.join('<p>'+esc(x)+'</p>' for x in d['stats'][1:])+'</aside>',
                '<section class="procedure"><h3>桌边操作顺序</h3>'+clock(d['accent'],d['diagram'])+'<p>把线索与代价说清楚，再把下一步交还给玩家。</p></section></div>',
                '<p class="table-title">'+esc({'abbey':'钟声进度与场景变化','clues':'今晚的时间线','hex':'荒原迹象表','dungeon':'区域速查','factions':'派系时钟','voyage':'章节里程碑'}[d['diagram']])+'</p>',
                '<table><thead><tr>'+''.join('<th>'+esc(x)+'</th>' for x in d['table_headers'])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(x)+'</td>' for x in row)+'</tr>' for row in d['rows'])+'</tbody></table>',
                '<section class="ending"><h3>收束与后续</h3><p>'+esc(d['ending'])+'</p></section>',bottom(2)]
    out.append('</body></html>')
    return '\n'.join(out)


def normalized(text): return ''.join(c for c in text if c.isalnum())


def expected(d):
    return [d[k] for k in ('title','subtitle','intro','readaloud','p2_title','p2_intro','ending')] + d['spec'] + d['stats'] + d['table_headers'] + [x for pair in d['sections'] for x in pair] + [x for row in d['rows'] for x in row]


def export_and_check(raw, demos):
    pdfdir, previews = HERE / 'pdf', HERE / 'previews'
    pdfdir.mkdir(exist_ok=True); previews.mkdir(exist_ok=True)
    book = pymupdf.open(raw)
    if len(book) != len(demos)*2: raise RuntimeError(f'Expected {len(demos)*2} pages, got {len(book)}; inspect overflow before exporting.')
    book.set_toc([[1,d['kind']+' · '+d['title'],i*2+1] for i,d in enumerate(demos)])
    book.set_metadata({'title':'TRPG 中文模组结构与排版样张','author':'TRPG Publishing Skills · 原创示例','subject':'六种模组结构的两页版式研究','creator':'Vivliostyle + PyMuPDF'})
    book.set_page_labels([{'startpage':0,'prefix':'','style':'D','firstpagenum':1}])
    book.save(pdfdir/'trpg-layout-collection.pdf',garbage=3,deflate=True)
    reports=[]
    for i,d in enumerate(demos):
        two=pymupdf.open();two.insert_pdf(book,from_page=i*2,to_page=i*2+1)
        two.set_toc([[1,d['title'],1],[2,d['p2_title'],2]])
        two.set_metadata({'title':d['title']+' · '+d['kind'],'author':'TRPG Publishing Skills · 原创示例','creator':'Vivliostyle + PyMuPDF'})
        two.set_page_labels([{'startpage':0,'prefix':'','style':'D','firstpagenum':1}])
        path=pdfdir/(d['id']+'.pdf');two.save(path,garbage=3,deflate=True)
        target=normalized(''.join(p.get_text() for p in two)); missing=[]
        for text in expected(d):
            n=normalized(text)
            if n not in target: missing.append(text[:28])
        out_of_bounds=[]
        for pi,page in enumerate(two):
            for block in page.get_text('dict')['blocks']:
                for line in block.get('lines',[]):
                    rect=pymupdf.Rect(line['bbox'])
                    if rect.x0 < 27 or rect.x1 > 576 or rect.y0 < 20 or rect.y1 > 765:
                        out_of_bounds.append({'page':pi+1,'bbox':[round(x,1) for x in rect]})
        fonts=sorted({f[2] for p in two for f in p.get_fonts()})
        pymupdf.TOOLS.mupdf_warnings()
        thumbs=[]
        for page in two:
            pix=page.get_pixmap(matrix=pymupdf.Matrix(1.05,1.05))
            thumbs.append(Image.frombytes('RGB',(pix.width,pix.height),pix.samples))
        spread=Image.new('RGB',(thumbs[0].width*2+18,thumbs[0].height),(211,210,201))
        spread.paste(thumbs[0],(0,0));spread.paste(thumbs[1],(thumbs[0].width+18,0))
        spread.save(previews/(d['id']+'.jpg'),quality=89,optimize=True)
        warning=pymupdf.TOOLS.mupdf_warnings()
        reports.append({'id':d['id'],'pages':len(two),'missing_text':missing,'out_of_bounds':out_of_bounds,'font_types':fonts,'render_warnings':warning,'bytes':path.stat().st_size})
        two.close()
    report={'engine':'Vivliostyle / Chromium','original_content':True,'total_pages':len(book),'styles':reports}
    (HERE/'qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if any(r['missing_text'] or r['out_of_bounds'] or r['render_warnings'] or 'Type3' in r['font_types'] for r in reports):
        raise RuntimeError('PDF QA failed; see qa.json. Do not describe the gallery as validated.')
    print(f'Exported {len(demos)} two-page PDFs and {len(book)}-page collection; all text accounted for, bounds/font/render checks passed.')


def gallery(demos):
    rows=[]
    for i,d in enumerate(demos,1):
        rows.append(f'<article><div class="caption"><span>{i:02d} / {esc(d["kind"])}</span><a href="pdf/{d["id"]}.pdf">打开两页 PDF ↗</a></div><a class="spread" href="pdf/{d["id"]}.pdf"><img src="previews/{d["id"]}.jpg" alt="{esc(d["title"])}双页排版预览" loading="lazy"></a><div class="details"><h2>{esc(d["title"])}</h2><p>{esc(d["intro"])}</p></div></article>')
    (HERE/'index.html').write_text('''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>TRPG 排版结构样张</title><style>
*{box-sizing:border-box}body{margin:0;background:#e9e7df;color:#26352f;font-family:system-ui,"WenQuanYi Zen Hei",sans-serif}main{max-width:1160px;margin:auto;padding:64px 32px}header{border-top:5px solid #26352f;padding-top:22px;margin-bottom:64px}.kicker{font-size:12px;letter-spacing:.2em}h1{font-size:clamp(32px,5vw,60px);font-weight:500;letter-spacing:.02em;margin:28px 0 18px}header p{max-width:680px;line-height:1.9;color:#5d645b}a{color:inherit;text-underline-offset:5px}.download{display:inline-block;margin-top:18px;border-bottom:1px solid;padding:0 0 8px;text-decoration:none}article{margin:0 0 72px}.caption{display:flex;justify-content:space-between;font-size:13px;letter-spacing:.06em;margin:0 0 15px}.spread{display:block}.spread img{width:100%;height:auto;display:block;box-shadow:0 12px 30px #26352f16}.details{display:flex;gap:36px;margin-top:18px}.details h2{width:32%;margin:0;font-size:24px;font-weight:500}.details p{flex:1;margin:0;font-size:14px;line-height:1.85;color:#62685e}footer{font-size:12px;line-height:1.9;border-top:1px solid #9ba092;padding-top:20px;color:#62685e}@media(max-width:650px){main{padding:32px 16px}.details{display:block}.details h2{width:auto;margin-bottom:10px}.caption{font-size:11px;gap:15px}article{margin-bottom:40px}}
</style><main><header><div class="kicker">TRPG PUBLISHING SKILLS / LAYOUT STUDIES</div><h1>六种结构，十二页冒险。</h1><p>从线性章节到城市沙盒，展示不同模组怎样组织桌边信息。所有文字、地图与图表均为原创样张；可直接查看 PDF，也可用本目录的源文件重新构建。</p><a class="download" href="pdf/trpg-layout-collection.pdf">下载 12 页合订本 ↗</a></header>'''+''.join(rows)+'''<footer>原创排版样张 · Python / Vivliostyle / Chromium / PyMuPDF<br>不含第三方模组正文或美术。字体仅以 PDF 文档子集嵌入，详情见本目录 README.md。</footer></main></html>''',encoding='utf-8')


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--sources-only',action='store_true',help='Generate print HTML and offline gallery without launching a browser')
    ap.add_argument('--font',type=Path,default=Path(os.environ.get('TRPG_DEMO_FONT','/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc')))
    mode=ap.add_mutually_exclusive_group()
    mode.add_argument('--serial',action='store_true',help='Compile the complete gallery in one browser job')
    mode.add_argument('--jobs',type=int,default=min(4,os.cpu_count() or 1),help='Maximum simultaneous demo builds (default: up to 4 CPU cores)')
    a=ap.parse_args()
    if a.jobs < 1: ap.error('--jobs must be a positive integer')
    jobs=1 if a.serial else a.jobs
    demos=json.loads((HERE/'demos.json').read_text(encoding='utf-8'))
    if len(demos)!=6 or len({d['id'] for d in demos})!=6: raise ValueError('Expected six uniquely named layout studies')
    work=HERE/'_work';work.mkdir(exist_ok=True)
    (work/'book.html').write_text(render(demos),encoding='utf-8')
    gallery(demos)
    if a.sources_only: print('Generated original HTML sources and offline gallery.');return
    font=a.font.resolve(strict=True)
    link=work/'demo.ttf'
    if link.is_symlink(): link.unlink()
    elif link.exists(): raise FileExistsError('Refusing to replace a non-symlink demo.ttf')
    link.symlink_to(font)
    node=os.environ.get('NODE','node')
    root=Path(os.environ.get('TRPG_TOOLS_ROOT',REPO))
    cli=Path(os.environ.get('VIVLIOSTYLE_CLI',root/'node_modules/@vivliostyle/cli/dist/cli.js'))
    if not cli.is_file(): raise FileNotFoundError('Install dependencies as documented, or set VIVLIOSTYLE_CLI / TRPG_TOOLS_ROOT')
    browser=os.environ.get('VIVLIOSTYLE_BROWSER') or next((shutil.which(n) for n in ('google-chrome','chromium','chromium-browser') if shutil.which(n)),None)
    if not browser: raise RuntimeError('Set VIVLIOSTYLE_BROWSER to a local browser executable')
    command=[node,str(cli.resolve()),'build','-c','vivliostyle.config.cjs','--port','0','--executable-browser',browser,'--log-level','silent']
    config="module.exports={title:'TRPG 原创排版样张',language:'zh-CN',entry:['book.html'],output:['all.raw.pdf'],workspaceDir:'.',timeout:1800000};\n"
    print(f'Compilation: {"serial" if jobs==1 else "parallel"}, jobs={jobs}',flush=True)
    if jobs==1:
        (work/'vivliostyle.config.cjs').write_text(config,encoding='utf-8')
        subprocess.run(command,cwd=work,check=True)
    else:
        tasks=[]
        for i,d in enumerate(demos):
            task=work/d['id'];task.mkdir(exist_ok=True)
            (task/'book.html').write_text(render([d],offset=i),encoding='utf-8')
            (task/'vivliostyle.config.cjs').write_text(config,encoding='utf-8')
            fontlink=task/'demo.ttf'
            if fontlink.is_symlink(): fontlink.unlink()
            elif fontlink.exists(): raise FileExistsError('Refusing to replace a non-symlink demo.ttf')
            fontlink.symlink_to(font)
            tasks.append(task)
        def compile_demo(task):
            subprocess.run(command,cwd=task,check=True)
            print(f'  {task.name}: compiled',flush=True)
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            list(pool.map(compile_demo,tasks))
        # PDF merging and rendering run on the main thread (PyMuPDF is not thread-safe).
        merged=pymupdf.open()
        for task in tasks:
            with pymupdf.open(task/'all.raw.pdf') as part:
                if len(part)!=2: raise RuntimeError(f'{task.name}: expected 2 pages, got {len(part)}')
                merged.insert_pdf(part)
        merged.save(work/'all.raw.pdf',garbage=3,deflate=True);merged.close()
    export_and_check(work/'all.raw.pdf',demos)
    print('Offline gallery:',HERE/'index.html')


if __name__=='__main__': main()
