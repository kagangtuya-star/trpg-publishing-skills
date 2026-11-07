"""Read-only environment check; never installs dependencies or downloads a browser."""
import importlib.metadata
import os
from pathlib import Path
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parents[1]
bad = sys.version_info < (3, 12)
print('Python:', sys.version.split()[0])
for name in ('pymupdf', 'pillow', 'numpy', 'fonttools', 'PyYAML'):
    try: print(name, importlib.metadata.version(name))
    except importlib.metadata.PackageNotFoundError:
        print('MISSING:', name); bad = True
node = shutil.which(os.environ.get('NODE', 'node'))
if node:
    version = subprocess.check_output([node, '--version'], text=True).strip()
    print('Node:', version)
    parts = tuple(map(int, version.lstrip('v').split('.')[:2]))
    if parts < (22, 12): bad = True; print('Node >=22.12 required')
else: bad = True; print('MISSING: node')
cli = Path(os.environ.get('VIVLIOSTYLE_CLI', root / 'node_modules/@vivliostyle/cli/dist/cli.js'))
print('Vivliostyle CLI:', cli, cli.is_file())
bad |= not cli.is_file()
browser = os.environ.get('VIVLIOSTYLE_BROWSER') or next((shutil.which(n) for n in ('google-chrome', 'chromium', 'chromium-browser') if shutil.which(n)), None)
print('Browser:', browser)
bad |= not bool(browser and shutil.which(browser))
print('pdffonts (optional):', shutil.which('pdffonts'))
raise SystemExit(int(bad))
