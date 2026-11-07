"""Check merged PDF structure; low-text pages require human review."""
import json
from pathlib import Path
import re
import pymupdf
from runtime import ROOT_PATH, FINAL
from zhparse import chapter_numbers


def main():
    state = json.loads((ROOT_PATH / 'work/pdf/state.json').read_text())
    doc = pymupdf.open(FINAL)
    issues = []
    for ch in chapter_numbers():
        page = state[f'ch{ch}_start']
        if page % 2 or not 1 <= page < len(doc): issues.append(f'Invalid opener: ch{ch}, p{page}')
    toc = doc.get_toc()
    for level, title, page in toc:
        if not 1 <= page <= len(doc):
            issues.append(f'Bookmark out of range: {title}'); continue
        if level == 2:
            big = ''.join(s['text'] for b in doc[page - 1].get_text('dict')['blocks']
                          for line in b.get('lines', []) if max(s['size'] for s in line['spans']) >= 18
                          for s in line['spans'])
            norm = lambda text: ''.join(c for c in text if c.isalnum())
            if norm(title)[:4] not in norm(big): issues.append(f'Part bookmark off: {title}, p{page}')
    fonts = sorted({font[2] for page in doc for font in page.get_fonts() if font[2] == 'Type3'})
    if fonts: issues.append('Type3 fonts found')
    if any(page.get_label() != str(i + 1) for i, page in enumerate(doc)):
        issues.append('Page labels are not consecutive decimal numbers')
    text = ''.join(page.get_text() for page in doc)
    if '**' in text or '##' in text: issues.append('Markdown markers in PDF')
    pymupdf.TOOLS.mupdf_warnings()
    for page in doc: page.get_pixmap(dpi=20)
    warnings = pymupdf.TOOLS.mupdf_warnings()
    if warnings: issues.append('MuPDF rendering warnings')
    result = dict(pages=len(doc), bookmarks=len(toc), issues=issues, warnings=warnings,
                  low_text_pages=[i + 1 for i, p in enumerate(doc) if len(p.get_text().strip()) < 40])
    target = ROOT_PATH / 'work/qa/structure.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    if issues: raise SystemExit(1)


if __name__ == '__main__': main()
