"""contact sheet of PDF pages: sheet.py in.pdf out.jpg first last [cols] [width]"""
import sys, pymupdf
from PIL import Image, ImageDraw
pdf, out, a, b = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
cols = int(sys.argv[5]) if len(sys.argv) > 5 else 4
W = int(sys.argv[6]) if len(sys.argv) > 6 else 450
d = pymupdf.open(pdf); pages = list(range(a - 1, min(b, len(d))))
if not pages: raise SystemExit('No pages in requested range')
H = int(W * d[pages[0]].rect.height / d[pages[0]].rect.width); rows = (len(pages) + cols - 1) // cols
sh = Image.new('RGB', (cols * W + (cols - 1) * 6, rows * (H + 16)), (90, 90, 90)); dr = ImageDraw.Draw(sh)
for i, p in enumerate(pages):
    pg = d[p]; z = W / pg.rect.width
    pix = pg.get_pixmap(matrix=pymupdf.Matrix(z, z))
    im = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
    x = (i % cols) * (W + 6); y = (i // cols) * (H + 16)
    sh.paste(im, (x, y + 16)); dr.text((x + 3, y + 2), f'p{p + 1}', fill='yellow')
sh.save(out, quality=82)
