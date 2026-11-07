"""Exercise concurrent compilation, pagination reconciliation and serial parity offline."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import pymupdf
from PIL import Image

REPO = Path(__file__).resolve().parents[1]

# This local stand-in writes real PDFs and records process overlap; no browser needed.
COMPILER = r'''
import json, os, re, sys, time
from pathlib import Path
import pymupdf
root = Path.cwd()
name = Path(os.environ['VS_ENTRY']).stem
started = time.monotonic_ns()
time.sleep(.15)
if name == os.environ.get('FAIL_CHAPTER'):
    raise SystemExit('Deliberate compiler failure')
html = (root/os.environ['VS_ENTRY']).read_text()
reset = int(re.search(r'counter-reset: page (-?\d+)', html)[1])
count = 3 if name == 'front' else json.loads(os.environ['PAGE_COUNTS'])[name] + 1
doc = pymupdf.open()
for i in range(count):
    page = doc.new_page(width=603, height=783)
    page.insert_text((70, 100), f'{name} folio {reset+i+1}')
target = root/os.environ['VS_OUT']
target.parent.mkdir(parents=True, exist_ok=True)
doc.save(target); doc.close()
log = root/'work/events'; log.mkdir(parents=True, exist_ok=True)
(log/f'{name}-{started}.json').write_text(json.dumps(dict(
    name=name, start=started, end=time.monotonic_ns(),
    workspace=os.environ['VS_WORKSPACE'], port=sys.argv[sys.argv.index('--port')+1])))
'''


class ParallelBuildTest(unittest.TestCase):
    def fixture(self, root):
        spec = importlib.util.spec_from_file_location('demo', REPO/'examples/minimal/create_demo.py')
        demo = importlib.util.module_from_spec(spec); spec.loader.exec_module(demo)
        module = demo.create(root)
        cfgpath = module/'src/config/chapters.json'
        original = json.loads(cfgpath.read_text())['1']
        cfg = {str(i): {**original, 'title': f'Chapter {i}', 'en': f'Chapter {i}', 'parts': {}} for i in (1, 2, 3)}
        cfgpath.write_text(json.dumps(cfg))
        (module/'src/config/figures.json').write_text('{}')
        for i in (1, 2, 3):
            (module/f'src/chapters/ch{i}.md').write_text(f'# Chapter {i}\n\n@chapter-opener\n\nOriginal test paragraph.\n')
        Image.new('RGB', (603, 783), 'white').save(module/'assets/processed/frame_recto_front.jpg')
        compiler = root/'compiler.py'; compiler.write_text(COMPILER)
        return module, compiler

    def run_build(self, module, compiler, *args, counts=None, ok=True, **extra):
        env = {**os.environ, 'NODE': sys.executable, 'VIVLIOSTYLE_CLI': str(compiler),
               'VIVLIOSTYLE_BROWSER': sys.executable, 'PAGE_COUNTS': json.dumps(counts or {'ch1': 3, 'ch2': 5, 'ch3': 3}), **extra}
        result = subprocess.run([sys.executable, 'scripts/build.py', *args], cwd=module,
                                env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode == 0, ok, result.stdout + result.stderr)
        return result

    def snapshot(self, module):
        state = json.loads((module/'work/pdf/state.json').read_text())
        final = module/'output/final/book-zh.pdf'
        with pymupdf.open(final) as doc:
            self.assertTrue(all(p.get_label() == str(i+1) for i, p in enumerate(doc)))
            self.assertTrue(all(state[f'ch{i}_start'] % 2 == 0 for i in (1, 2, 3)))
            return state, [p.get_text() for p in doc], doc.get_toc(), doc.metadata

    def test_parallel_folios_serial_parity_incremental_and_failure(self):
        with tempfile.TemporaryDirectory(prefix='parallel-build-') as tmp:
            root = Path(tmp)
            parallel, compiler = self.fixture(root/'parallel')
            serial, other = self.fixture(root/'serial')
            result = self.run_build(parallel, compiler, '--jobs', '2')
            self.assertIn('Compilation: parallel', result.stdout)
            self.run_build(serial, other, '--serial')
            self.assertEqual(self.snapshot(parallel), self.snapshot(serial))
            events = [json.loads(p.read_text()) for p in (parallel/'work/events').glob('ch*.json')]
            self.assertTrue(any(a['start'] < b['start'] < a['end'] for a in events for b in events))
            self.assertLessEqual(max(sum(e['start'] <= point < e['end'] for e in events)
                                     for point in [e['start'] for e in events]), 2)
            self.assertEqual({e['workspace'] for e in events}, {'work/vivliostyle/ch1', 'work/vivliostyle/ch2', 'work/vivliostyle/ch3'})
            self.assertTrue(all(e['port'] == '0' for e in events))
            self.assertEqual(self.snapshot(parallel)[0]['ch3_start'], 14)
            # A longer upstream chapter shifts cached downstream chapters even with --only.
            counts = {'ch1': 7, 'ch2': 5, 'ch3': 3}
            self.run_build(parallel, compiler, '--only', '1', '--jobs', '2', counts=counts)
            self.run_build(serial, other, '--serial', counts=counts)
            self.assertEqual(self.snapshot(parallel), self.snapshot(serial))
            self.assertEqual(self.snapshot(parallel)[0]['ch3_start'], 18)
            final = parallel/'output/final/book-zh.pdf'
            before = final.read_bytes()
            cached_before = [(parallel/f'work/pdf/ch{i}.pdf').read_bytes() for i in (1, 2, 3)]
            state_before = (parallel/'work/pdf/state.json').read_bytes()
            self.run_build(parallel, compiler, '--jobs', '2', FAIL_CHAPTER='ch2', ok=False)
            self.assertEqual(final.read_bytes(), before)
            self.assertEqual([(parallel/f'work/pdf/ch{i}.pdf').read_bytes() for i in (1, 2, 3)], cached_before)
            self.assertEqual((parallel/'work/pdf/state.json').read_bytes(), state_before)
            self.run_build(parallel, compiler, '--jobs', '0', ok=False)
            self.run_build(parallel, compiler, '--serial', '--jobs', '2', ok=False)


if __name__ == '__main__': unittest.main()
