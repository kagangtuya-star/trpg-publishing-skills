# QA 与验收

在模块目录运行：
```bash
$P scripts/qa_content.py --pdf
$P scripts/qa_overflow.py
$P scripts/qa_structure.py
$P scripts/report_art.py
pdffonts output/final/book-zh.pdf
$P scripts/sheet.py output/final/book-zh.pdf output/preview/sheet.jpg 1 40 8 230
```
最后两项需要实际文件名；pdffonts 为可选 Poppler 工具，字体结构也由 qa_structure 检查。

- content_check.json：译稿单元去标记后做 24 字重叠片段核对，允许跨栏拆为两段；语义 ≥99.9%、PDF ≥99.7%，不达标退出 1。每条 missing 与 dropped 都需解释；低于门槛不能通过改阈值掩盖丢字。表格逐格复核，标题前缀或排版拆分可产生误报。
- overflow.json：按 book.json 的版心下沿检测底部溢出，排除封面及章首跨页和匹配的页脚，命中退出 1。不能检测所有横向、容器和图像重叠。
- structure.json：书签范围、部分横幅定位、页码标签、章首偶数页、Type3 字体、渲染警告及低文字量页。低文字量页只列出待人工查看，不自动判定空白。
- art_mapping.md：列出美术放置锚点。成书页按图像尺寸匹配是启发式，尺寸相同的图片可能误定位，必须人工抽查。
- 图注：missing/unattested 为 0，composed 和 manual 全部人工复核。

自动 QA 不等于出版验收。逐张查看全书联系表，可疑页放大；重点检查扉页后空白、统计块丢行、地图英文残留、插图重叠、字体字重与缺字、目录和书签。把配置 drop、去重和未命中列入报告，原译文保持不变。

目录至少构建两次，比较 work/pdf/state.json 中的 front_pages、chN_start、chN_pages 和 toc；尚未稳定时继续完整构建，不能用 --only 宣布全书稳定。

交付 output/reports/build_report.md、qa_report.md、proofreading_report.md、art_mapping.md，数字与最后一次构建一致。视觉审查必须实际打开图片，不把脚本执行当成目检。
