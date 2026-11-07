---
name: trpg-zh-typesetting
description: 将用户自行提供且有权使用的英文 TRPG PDF 与中文 Markdown 译稿排成中文 PDF。使用 Python、PyMuPDF、Vivliostyle 与 Chromium，处理原版美术、统计块、章首跨页、图注、书签及 QA；适用于模组排版和换书适配，不负责翻译正文。
---

# TRPG 中文 PDF 排版

输入是英文 PDF 和逐章中文 Markdown。输出是可重建的语义源、HTML、成书 PDF 和 QA 报告。先读 [环境](references/environment.md) 和 [管线](references/pipeline.md)，换书时读 [适配](references/adapting.md)。

## 约束

- 用户输入只读；初始化工具复制输入并将副本设为只读。不改译文措辞；疑似笔误、译名差异记入校对报告。标题、表格、转义等格式调整要可追溯。
- 图注和地图新增文字优先逐字取自对应章译稿；组合短语标为 composed，并人工复核。
- 美术来自用户有权使用的本地原版。不得将原版 PDF、译文、图片、字体或产物放入本 Skill 仓库。
- Vivliostyle 逐章串行运行。输入和素材不足时不猜测书籍页码或图片 xref。
- 不自动安装依赖或下载浏览器、字体。构建、内容核验和视觉审查只报告实际完成的结果。
- 本 Skill 不授予发布、提交或对外发送文件的权限；按用户当前授权操作。

## 路径与入口

Skill 目录为 `skills/trpg-zh-typesetting/`；命令从独立仓库根运行。先确定本 Skill 的真实路径（符号链接需 resolve），依赖安装在其所属仓库根，避免使用原项目的 shared 目录。

```bash
python skills/trpg-zh-typesetting/tools/new_module.py my-book /path/original.pdf /path/translations
cd modules/my-book
../../.venv/bin/python scripts/build.py --prep
../../.venv/bin/python scripts/build.py
../../.venv/bin/python scripts/qa_content.py --pdf
../../.venv/bin/python scripts/qa_overflow.py
../../.venv/bin/python scripts/qa_structure.py
../../.venv/bin/python scripts/report_art.py
```

初始化后必须先配置 `src/config/{book,chapters,roles,art,maps,caption_glossary}.json`，准备字体。命令中的 Python 应替换为实际已安装依赖的解释器。模块可以通过 --root 放在其他工作区；依赖根保存在 book.json 的 tools_root，可由 TRPG_TOOLS_ROOT 覆盖。安装整个仓库后通过链接或直接读取使用 Skill；不要只复制 SKILL.md。

## 检查点

1. 盘点字体、配色、章节范围、页码、译者附加物行号和美术。角色规则按顺序匹配，未知字体为 OTHER，需人工处理。
2. 配置结构、英文角色规则、美术边框与扉页。先做一章；统计块分类和中英对齐是启发式，必须核对。
3. 提取素材、地图替字、分类、图注、语义源。检查未命中单元和 drop 明细，禁止静默丢行。
4. 样章确认版心、字体、扉页和译者署名，再逐章串行构建全书。至少构建两次，目录页数和章节起始页须稳定。
5. 运行 QA，实际查看联系表及可疑页。覆盖率仅用于定位，不能替代人工验收。交付构建、QA、校对、美术映射报告。

## 按需参考

- [pipeline.md](references/pipeline.md)：各阶段命令与配置
- [adapting.md](references/adapting.md)：换书、角色规则、美术参数
- [design.md](references/design.md)：CSS、字体、章首与双栏
- [captions.md](references/captions.md)：图注来源与复核
- [qa.md](references/qa.md)：自动检查与人工验收
- [pitfalls.md](references/pitfalls.md)：内容丢失、空白页、字体与浮动陷阱
- [environment.md](references/environment.md)：安装、字体与环境变量
- [templates/README.md](templates/README.md)：模板脚本职责

模板已去除具体书籍配置，保留原管线的可审阅语义层。默认纸色主题可运行，但贴近原版需要用户逐书配置有授权的素材。
