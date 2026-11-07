# 管线与命令

仓库根记为 R，Skill 目录记为 K；在模块目录设置 P 为绝对 Python 路径。不要把相对 .venv 路径当成跨目录通用变量。

1. 初始化：从仓库根运行 python K/tools/new_module.py my-book 原版.pdf 译稿目录。源输入不动，复制件只读；目标模块已存在则拒绝。章节文件必须是 001 开头，章号唯一且连续。
2. 盘点：在模块目录运行 $P <K绝对路径>/tools/inventory.py input/original.pdf；输出字体/字号/颜色、图像、地图和图注候选。生成联系表并人工确定章节页码。
3. 填写配置。chapters.json 的 pages 是 PDF 物理页码（1 起），不是印刷页码。title_line、front、drop、advancement、parts、insert_parts 的行号指输入 Markdown 的 1 起行号。front 仅用于第一章的全书引言。drop 只排除已确认的非正文，记录理由。
4. 运行 scripts/extract_en.py 和 scripts/extract_images.py；前者读取 roles.json，后者提取有透明蒙版的图像并记录 images_meta/image_usage。编写 art.json、maps.json，核查字体和图片授权。
5. scripts/make_assets.py 生成边框和去文字扉页；maps.py 渲染地图并替换配置中的标签；figures.py 分类插图（手改 use/kind/size/place/width/before_line/note 会保留）；optimize_images.py 生成印刷副本。
6. captions.py 生成图注，normalize.py 对齐译稿并生成语义源。qa_content.py 检查覆盖率。角色、地图和图注必须人工确认。
7. scripts/build.py --only 1 生成样章；确认双栏、字体、译者署名、章节跨页及正文起点。
8. scripts/build.py --prep 按依赖顺序执行提取、素材、图注与语义源，再默认并行编译章节（最多 4 个任务）。--jobs N 调整并发，--serial 或 --jobs 1 串行编译；两种模式都自动校正章节起始页、按章序合并。配置确认后至少再运行一次 scripts/build.py。首次 --only 会补建其他缺失章，不能当作只编译一章的性能承诺。
9. 全书运行 QA 和 report_art.py，实际查看联系表，编写构建/QA/校对报告。

## 数据流

input/original.pdf → 英文角色流、原版图像 → 地图与边框、figures.json

input/translation/*.md + 角色流 + chapters.json → src/chapters/chN.md

语义源 + theme.css + captions.json → build/*.html → Vivliostyle → work/pdf/*.pdf
各章 PDF → 删除章前占位页 → 奇偶衬页 → 合并、目录、书签、页码标签、元数据 → output/final/

语义源支持 ::: readaloud/sidebar/handout/statblock/advancement/intro/rawtable、@figure ID、@orig 页码、@chapter-opener、带 {.part} 的标题和 Markdown 表格。生成物会覆盖，不直接手改；修改配置或模块脚本后重建。

## 一键重建前提

--prep 会重新执行已有配置，不会猜测角色、美术或行号。准备好输入、字体、配置后运行：
```bash
$P scripts/build.py --prep
$P scripts/build.py
$P scripts/qa_content.py --pdf
$P scripts/qa_overflow.py
$P scripts/qa_structure.py
$P scripts/report_art.py
```
