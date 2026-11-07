"""Validate source syntax, Skill links, metadata and dependency configuration offline."""
import ast
import json
from pathlib import Path
import re
import subprocess
import tomllib
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / 'skills/trpg-zh-typesetting'
IGNORED = {'node_modules', '.venv', '__pycache__', '.git', 'modules', 'local', 'fonts'}


def files():
    import os
    for base, dirs, names in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in IGNORED]
        for name in names: yield Path(base) / name


def main():
    count = 0
    for p in files():
        count += 1
        if p.suffix == '.py': ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
        if p.suffix == '.json': json.loads(p.read_text(encoding='utf-8'))
        if p.suffix == '.sh': subprocess.run(['bash', '-n', str(p)], check=True)
        if p.suffix == '.md':
            for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', p.read_text(encoding='utf-8')):
                if '://' in link or link.startswith('#'): continue
                path = link.split('#')[0]
                assert (p.parent / path).exists(), f'Broken Markdown link: {p}: {link}'
    text = (SKILL / 'SKILL.md').read_text(encoding='utf-8')
    match = re.match(r'^---\n(.*?)\n---\n', text, re.S)
    assert match, 'Skill frontmatter missing'
    meta = yaml.safe_load(match[1])
    assert meta['name'] == SKILL.name and isinstance(meta['description'], str)
    assert len(meta['description']) <= 1024
    ui = yaml.safe_load((SKILL / 'agents/openai.yaml').read_text(encoding='utf-8'))
    assert '$' + meta['name'] in ui['interface']['default_prompt']
    assert 25 <= len(ui['interface']['short_description']) <= 64
    project = tomllib.loads((ROOT / 'pyproject.toml').read_text(encoding='utf-8'))
    pins = {line.strip().lower().replace('_', '-') for line in (ROOT / 'requirements.txt').read_text().splitlines()
            if line.strip() and not line.startswith('#')}
    assert all(dep.lower().replace('_', '-') in pins for dep in project['project']['dependencies'])
    package = json.loads((ROOT / 'package.json').read_text())
    lock = json.loads((ROOT / 'package-lock.json').read_text())
    assert package['dependencies'] == lock['packages']['']['dependencies']
    cli = lock['packages']['node_modules/@vivliostyle/cli']
    assert cli['bin']['vivliostyle'] == 'dist/cli.js'
    assert cli['version'] == '11.4.0'
    for p in (SKILL / 'templates/config').glob('*.json'):
        json.loads(p.read_text(encoding='utf-8'))
    assert (SKILL / 'templates/scripts/runtime.py').is_file()
    print(f'Validated {count} source files: Python/JSON/TOML/YAML, shell syntax, links, Skill metadata, dependency pins and npm lock.')


if __name__ == '__main__': main()
