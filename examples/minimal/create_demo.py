"""Generate original test PDF locally, then initialize and configure a demo module.

Run from any directory: python examples/minimal/create_demo.py --root /tmp/trpg-demo
Only locally generated inputs/outputs are written. Nothing is downloaded.
"""
import argparse
import importlib.util
import json
import io
from pathlib import Path
import pymupdf
from PIL import Image, ImageDraw

REPO = Path(__file__).resolve().parents[2]


def create(root):
    root = root.resolve()
    source = root / 'local/demo-input'
    if (root / 'modules/demo').exists() or source.exists():
        raise FileExistsError('Demo destination exists; choose a new --root')
    source.mkdir(parents=True)
    doc = pymupdf.open()
    p = doc.new_page(width=603, height=783)
    p.insert_text((70, 90), 'The Star Lantern Stop', fontsize=24, fontname='hebo')
    p.insert_text((70, 150), 'Arrival', fontsize=18, fontname='hebo')
    p.insert_textbox(pymupdf.Rect(70, 190, 530, 350),
                     'At dusk a traveler reaches a wooden shelter with a blue lamp.\n'
                     'A wind chime rings beside a table set with warm tea.\n'
                     'The keeper asks visitors to record the weather and refill the kettle.\n'
                     'There is no battle and no hidden trap.', fontsize=12)
    # Original vector decoration exercises text-removal without borrowing art.
    p.draw_rect(pymupdf.Rect(40, 40, 563, 743), color=(.45, .1, .12), width=2)
    art = Image.new('RGB', (800, 450), (234, 225, 204))
    draw = ImageDraw.Draw(art)
    draw.rectangle((310, 100, 490, 310), fill=(45, 90, 140), outline=(120, 80, 35), width=12)
    draw.line((400, 40, 400, 100), fill=(120, 80, 35), width=12)
    stream = io.BytesIO(); art.save(stream, format='PNG')
    p.insert_image(pymupdf.Rect(70, 380, 530, 640), stream=stream.getvalue())
    doc.save(source / 'original.pdf'); doc.close()
    spec = importlib.util.spec_from_file_location('new_module', REPO / 'skills/trpg-zh-typesetting/tools/new_module.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    dest = module.create('demo', source / 'original.pdf', Path(__file__).parent / 'translation', root)
    config = dest / 'src/config'
    chapters = {'1': {'title': '星灯驿站', 'en': 'The Star Lantern Stop', 'author_en': 'Example Author',
                      'author_zh': '作者：示例作者', 'translator': '示例译者', 'pages': [1, 1], 'title_line': 1,
                      'drop': [], 'parts': {'3': ['第一部分', '抵达驿站']}, 'insert_parts': [], 'maps': []}}
    (config / 'chapters.json').write_text(json.dumps(chapters, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'Next: prepare fonts, then run the documented build commands in {dest}')
    return dest


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root', type=Path, default=REPO)
    create(ap.parse_args().root)
