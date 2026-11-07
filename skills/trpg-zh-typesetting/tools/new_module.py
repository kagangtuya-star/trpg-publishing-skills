"""Create a local module; inputs are copied, never modified. No dependencies required."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil

SKILL = Path(__file__).resolve().parents[1]
REPO = SKILL.parents[1]


def create(name, pdf, translations, root):
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', name):
        raise ValueError('Module name must use lowercase letters, digits and hyphens')
    dest = root.resolve() / 'modules' / name
    if dest.exists(): raise FileExistsError(f'Refusing to overwrite: {dest}')
    pdf = pdf.resolve(strict=True)
    files = sorted(translations.resolve(strict=True).glob('*.md'))
    if not files: raise ValueError('No Markdown translations found')
    numbers = []
    for f in files:
        if not re.match(r'^\d{3}(?:\D|$)', f.name): raise ValueError(f'Invalid chapter filename: {f.name}')
        numbers.append(int(f.name[:3]))
    if sorted(numbers) != list(range(1, len(files) + 1)):
        raise ValueError('Chapter numbers must be unique and consecutive, starting at 001')
    for d in ('input/translation', 'scripts', 'src/config', 'src/chapters', 'src/styles', 'src/front',
              'assets/original/img', 'assets/processed', 'assets/optimized', 'assets/fonts',
              'build', 'work/mapping', 'work/qa', 'output/final', 'output/preview', 'output/reports'):
        (dest / d).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(pdf, dest / 'input/original.pdf')
    for f in files: shutil.copyfile(f, dest / 'input/translation' / f.name)
    for f in (dest / 'input').rglob('*'):
        if f.is_file(): f.chmod(f.stat().st_mode & ~0o222)
    template = SKILL / 'templates'
    for f in (template / 'scripts').glob('*.py'): shutil.copyfile(f, dest / 'scripts' / f.name)
    shutil.copyfile(template / 'styles/theme.css', dest / 'src/styles/theme.css')
    shutil.copyfile(template / 'vivliostyle.config.js', dest / 'vivliostyle.config.js')
    shutil.copyfile(template / 'notes.example.html', dest / 'src/front/notes.html')
    for f in (template / 'config').glob('*.example.json'):
        data = json.loads(f.read_text(encoding='utf-8'))
        if f.name == 'book.example.json': data['tools_root'] = os.path.relpath(REPO, dest)
        if f.name == 'chapters.example.json':
            data = {str(n): {**data['1'], 'title': f'第 {n} 章（请配置）', 'en': f'Chapter {n}'} for n in sorted(numbers)}
        (dest / 'src/config' / f.name.replace('.example', '')).write_text(
            json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    font_dir = Path(os.environ.get('TRPG_FONTS', REPO / 'fonts')).resolve()
    for name in ('NotoSerifSC-Regular', 'NotoSerifSC-SemiBold', 'NotoSerifSC-Black',
                 'NotoSansSC-Regular', 'NotoSansSC-Bold', 'Cinzel-Bold', 'CinzelDecorative-Bold'):
        # Relative individual links leave module-specific WenKai subsets independent.
        target = font_dir / (name + '.ttf')
        (dest / 'assets/fonts' / target.name).symlink_to(os.path.relpath(target, dest / 'assets/fonts'))
    (dest / 'AGENTS.md').write_text(
        '# 模组排版\n\n'
        '先读仓库 `skills/trpg-zh-typesetting/SKILL.md`。输入只读，不改译文措辞。\n'
        '配置 `src/config/` 后运行 `python scripts/build.py --prep`，再构建一次使目录收敛。\n'
        'Vivliostyle 逐章串行；运行 qa_content.py --pdf、qa_overflow.py、qa_structure.py。\n'
        '生成的 src/chapters 不手改；检查未命中单元、低文字量页面和全部书签。\n', encoding='utf-8')
    print(f'Created {dest}; configure book/chapters/roles/art JSON before building.')
    return dest


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('name')
    ap.add_argument('pdf', type=Path)
    ap.add_argument('translations', type=Path)
    ap.add_argument('--root', type=Path, default=Path(os.environ.get('TRPG_ROOT', REPO)))
    a = ap.parse_args()
    try: create(a.name, a.pdf, a.translations, a.root)
    except (OSError, ValueError) as e: ap.exit(1, f'{e}\n')


if __name__ == '__main__': main()
