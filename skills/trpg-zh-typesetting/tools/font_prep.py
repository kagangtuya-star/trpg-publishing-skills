"""Prepare print fonts in fonts/ (phase 0 / after translation changes).

  python tools/font_prep.py instances            # static TrueType instances from the Noto variable fonts
  python tools/font_prep.py subset <module_dir>  # WenKai subset covering every character the module can print

Why: Chrome embeds CFF/OTF/TTC fonts as Type3 (blurry, not searchable). Static glyf TrueType instances made
with fontTools varLib.instancer embed as CID TrueType (Type0). Each weight gets its own family name, because
Vivliostyle picks the wrong face when one family declares several weights.
Expected inputs in fonts/ (download manually, see references/environment.md):
  NotoSerifSC-VF.ttf, NotoSansSC-VF.ttf  (Google Fonts NotoSerifSC[wght].ttf / NotoSansSC[wght].ttf, renamed)
  LXGWWenKai-Regular.ttf, LXGWWenKai-Medium.ttf
"""
import os, sys, glob, subprocess
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

FONTS = os.environ.get('TRPG_FONTS') or str(Path(__file__).resolve().parents[3] / 'fonts')
INSTANCES = [('NotoSerifSC-VF.ttf', 400, 'NotoSerifSC-Regular', 'Noto Serif SC Book'),
             ('NotoSerifSC-VF.ttf', 600, 'NotoSerifSC-SemiBold', 'Noto Serif SC Semi'),
             ('NotoSerifSC-VF.ttf', 900, 'NotoSerifSC-Black', 'Noto Serif SC Blk'),
             ('NotoSansSC-VF.ttf', 400, 'NotoSansSC-Regular', 'Noto Sans SC Book'),
             ('NotoSansSC-VF.ttf', 700, 'NotoSansSC-Bold', 'Noto Sans SC Bd'),
             ('Cinzel.ttf', 700, 'Cinzel-Bold', 'Cinzel Book Bold')]
# characters that must always be present in the WenKai subset (punctuation, symbols, circled numbers...)
UNICODES = 'U+0020-007E,U+00A0-00FF,U+2000-206F,U+3000-303F,U+FF00-FFEF,U+2460-24FF,U+25A0-25FF,U+2600-27BF'

def set_names(f, family, ps):
    n = f['name']
    for rec in list(n.names):
        if rec.nameID in (1, 2, 3, 4, 6, 16, 17): n.removeNames(nameID=rec.nameID)
    for nid, val in ((1, family), (2, 'Regular'), (3, ps), (4, family), (6, ps)):
        n.setName(val, nid, 3, 1, 0x409); n.setName(val, nid, 1, 0, 0)

def instances():
    for src, w, ps, family in INSTANCES:
        out = os.path.join(FONTS, ps + '.ttf')
        if os.path.exists(out): print('keep', out); continue
        vf = TTFont(os.path.join(FONTS, src))
        st = instancer.instantiateVariableFont(vf, {'wght': w}, overlap=instancer.OverlapMode.KEEP_AND_SET_FLAGS)
        set_names(st, family, ps)
        st.save(out); print('wrote', out)

def subset(module):
    output = os.path.join(module, 'assets/fonts')
    os.makedirs(output, exist_ok=True)
    txt = os.path.join(module, 'work', 'wenkai_chars.txt')
    os.makedirs(os.path.dirname(txt), exist_ok=True)
    with open(txt, 'w', encoding='utf-8') as o:
        for p in glob.glob(os.path.join(module, 'input/translation/*.md')) + glob.glob(os.path.join(module, 'src/config/*.json')) \
                + glob.glob(os.path.join(module, 'src/front/*.html')) + glob.glob(os.path.join(module, 'scripts/render.py')):
            o.write(open(p, encoding='utf-8').read())
    py = os.path.join(os.path.dirname(sys.executable), 'pyftsubset')
    for w in ('Regular', 'Medium'):
        subprocess.run([py, os.path.join(FONTS, f'LXGWWenKai-{w}.ttf'), f'--text-file={txt}', f'--unicodes={UNICODES}',
                        '--layout-features=*', f'--output-file={os.path.join(output, f"WenKaiSub-{w}.ttf")}'], check=True)
        f = TTFont(os.path.join(output, f'WenKaiSub-{w}.ttf')); set_names(f, f'WenKaiSub {w}', f'WenKaiSub-{w}'); f.save(os.path.join(output, f'WenKaiSub-{w}.ttf'))
        print('wrote', f'WenKaiSub-{w}.ttf', len(f.getBestCmap()), 'glyphs')

if __name__ == '__main__':
    if sys.argv[1:2] == ['instances']: instances()
    elif sys.argv[1:2] == ['subset']: subset(sys.argv[2])
    else: print(__doc__)
