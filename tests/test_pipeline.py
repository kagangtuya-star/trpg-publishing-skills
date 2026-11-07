"""Copyright-free integration and regression tests; no network or browser required."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import pymupdf

REPO = Path(__file__).resolve().parents[1]
SKILL = REPO / 'skills/trpg-zh-typesetting'


class PipelineTest(unittest.TestCase):
    def run_script(self, module, name, *args, ok=True, env=None):
        result = subprocess.run([sys.executable, str(module / 'scripts' / name), *args],
                                cwd=module, capture_output=True, text=True,
                                env={**os.environ, **(env or {})})
        if ok: self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else: self.assertNotEqual(result.returncode, 0)
        return result

    def test_original_inputs_semantics_assets_and_qa(self):
        with tempfile.TemporaryDirectory(prefix='trpg-smoke-') as directory:
            root = Path(directory)
            spec = importlib.util.spec_from_file_location('demo', REPO / 'examples/minimal/create_demo.py')
            demo = importlib.util.module_from_spec(spec); spec.loader.exec_module(demo)
            source = REPO / 'examples/minimal/translation/001-starlight.md'
            original_hash = hashlib.sha256(source.read_bytes()).hexdigest()
            module = demo.create(root)
            inp = module / 'input/original.pdf'
            pdf_hash = hashlib.sha256(inp.read_bytes()).hexdigest()
            self.assertEqual(inp.stat().st_mode & 0o222, 0)
            self.run_script(module, 'build.py', '--help')
            duplicate = subprocess.run([sys.executable, str(SKILL / 'tools/new_module.py'), 'demo',
                                        str(inp), str(source.parent), '--root', str(root)], capture_output=True)
            self.assertNotEqual(duplicate.returncode, 0)
            for name in ('extract_en.py', 'extract_images.py', 'make_assets.py', 'maps.py', 'figures.py',
                         'optimize_images.py', 'captions.py', 'normalize.py', 'qa_content.py'):
                self.run_script(module, name)
            figures = json.loads((module / 'src/config/figures.json').read_text())
            self.assertGreater(len(figures), 0, 'Generated original art must exercise extraction and placement')
            self.run_script(module, 'render.py', 'front', '1')
            html = (module / 'build/ch1.html').read_text()
            self.assertNotIn('id="intro"', (module / 'build/front.html').read_text())
            self.assertIn('译者：示例译者', html)
            self.assertIn('星灯驿站', html)
            self.assertNotIn('Curse', html)
            cfgpath = module / 'src/config/chapters.json'
            cfg = json.loads(cfgpath.read_text())
            cfg['1']['translator'] = '<Alice & Bob>'
            cfgpath.write_text(json.dumps(cfg), encoding='utf-8')
            self.run_script(module, 'render.py', '1')
            self.assertIn('&lt;Alice &amp; Bob&gt;', (module / 'build/ch1.html').read_text())
            cfg['1']['translator'] = ''
            cfgpath.write_text(json.dumps(cfg), encoding='utf-8')
            self.run_script(module, 'render.py', '1')
            self.assertNotIn('class="op-translator"', (module / 'build/ch1.html').read_text())
            # A real synthetic PDF exercises overflow and structure QA without Chromium.
            pdf = pymupdf.open()
            for _ in range(5): pdf.new_page(width=603, height=783)
            pdf[3].insert_text((70, 100), 'Original smoke test body', fontsize=12)
            pdf.set_toc([[1, 'Cover', 1], [1, 'Chapter', 2]])
            pdf.set_page_labels([{'startpage': 0, 'prefix': '', 'style': 'D', 'firstpagenum': 1}])
            target = module / 'output/final/book-zh.pdf'
            pdf.save(target); pdf.close()
            state = module / 'work/pdf/state.json'
            state.parent.mkdir(parents=True, exist_ok=True)
            state.write_text(json.dumps({'ch1_start': 2}))
            self.run_script(module, 'qa_overflow.py')
            self.run_script(module, 'qa_structure.py')
            self.run_script(module, 'sheet.py', str(target), str(module / 'output/preview/sheet.jpg'), '1', '5')
            # Deliberate content loss and overflow must fail, not merely print a report.
            semantic = module / 'src/chapters/ch1.md'
            saved = semantic.read_text(); semantic.write_text('Missing all content\n')
            self.run_script(module, 'qa_content.py', ok=False)
            semantic.write_text(saved)
            overflow = module / 'work/overflow-test.pdf'
            doc = pymupdf.open(target)
            doc[3].insert_text((80, 720), 'Intentional overflow', fontsize=12)
            doc.save(overflow); doc.close()
            self.run_script(module, 'qa_overflow.py', str(overflow), ok=False)
            self.assertEqual(hashlib.sha256(inp.read_bytes()).hexdigest(), pdf_hash)
            self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), original_hash)


if __name__ == '__main__': unittest.main()
