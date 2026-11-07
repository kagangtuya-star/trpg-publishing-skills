import json, sys, os
sys.path.insert(0, 'scripts')
from zhparse import units, chapter_files
ch=int(sys.argv[1]); a=int(sys.argv[2]); b=int(sys.argv[3])
A=json.load(open(f'work/mapping/align_ch{ch}.json'))
zh=units(chapter_files()[ch])
for u,r in zip(zh[a:b],A['units'][a:b]):
    v=r['votes']; role=max(v,key=v.get) if v else '-'
    print(f"{u['i']:4d} p{r['page']} {role:7s} {u['plain'][:60]}")
