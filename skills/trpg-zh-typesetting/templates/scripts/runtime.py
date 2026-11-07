"""Module-local paths and book settings; no source-project dependency."""
import json
import os
from pathlib import Path

ROOT_PATH = Path(__file__).resolve().parents[1]
ROOT = str(ROOT_PATH)
BOOK = json.loads((ROOT_PATH / 'src/config/book.json').read_text(encoding='utf-8'))
ART = json.loads((ROOT_PATH / 'src/config/art.json').read_text(encoding='utf-8'))
TOOLS_ROOT = Path(os.environ.get('TRPG_TOOLS_ROOT', ROOT_PATH / BOOK['tools_root'])).resolve()
FINAL = str(ROOT_PATH / 'output/final' / BOOK['output'])
PAGE_W, PAGE_H = BOOK['page_size']
BODY_BOTTOM = PAGE_H - BOOK['margins'][2]


def chapter_label(n):
    return '〇一二三四五六七八九'[n] if 0 <= n < 10 else str(n)


def browser_path():
    import shutil
    candidate = os.environ.get('VIVLIOSTYLE_BROWSER')
    if candidate:
        found = shutil.which(candidate)
        if found:
            return found
        raise SystemExit(f'Browser not executable: {candidate}')
    for name in ('google-chrome', 'chromium', 'chromium-browser', 'chrome'):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit('Set VIVLIOSTYLE_BROWSER to a local Chromium/Chrome executable.')
