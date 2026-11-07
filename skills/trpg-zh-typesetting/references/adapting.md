# 换书适配

通用模板不携带具体模组的章节、译名、xref、图注或美术。先初始化模块，在模块内配置和修改；不要为了单本书改写通用模板。

## 配置职责

- book.json：title/en/subtitle/author/subject/keywords/output、page_size=[宽,高]、margins=[上,外,下,内]（pt），tools_root 相对模块根定位 Node 依赖。
- chapters.json：数字章号键，必须从 1 连续；title/en、author_en、可选 author_zh、可选 translator、pages=[原版首页,末页]。translator 在章首独立显示；空值不显示，HTML 会转义。
- roles.json：rules 按先后匹配，font_prefix、min_size、max_size、color（六位小写 hex）均可选；role 为 BODY、RA、SB、SBT、SBH、SIDEBAR、H1–H4、AREA、INTRO、HANDOUT、TBLH、CAPTION、LABEL、OTHER，或 null（忽略）。用 inventory 实测，别照搬字体名。
- art.json：paper 为 RGB；frame_verso/frame_recto 是 [{xref: 整数, bbox: [x0,y0,x1,y1]}]，按顺序叠合。openers 如 {"1":[2,3]} 指 PDF 物理页码；cover_page/title_page/intro_page 可空。excluded_pages、textures、handout_backgrounds 用于避免把底纹和章首当插图。pad_emblem 可为 {"src":"assets/…","bbox":[…]}。空配置生成无素材纸色背景。
- maps.json：图像 stem 为键，如 p001_x10，值包含 bbox、title、labels 和可选 keep_original；不要把示例 xref 当真实配置。
- caption_glossary.json：章节号→英文原版图注大写→{"zh":"本章译名","composed":false}。

地图配置示例（全部为原创占位名）：
```json
{"p001_x10":{"bbox":[60,80,540,400],"title":"星灯驿站","labels":{"STAR LANTERN STOP":"星灯驿站"},"keep_original":false}}
```
章节 parts 示例：{"5":["第一部分","抵达驿站"]}；insert_parts 示例：[{"before":5,"label":"第一部分","title":"抵达驿站"}]。新增标题需取自译稿现有文字并核对来源。

## 必须人工适配的部分

原版页眉页脚排除、跨栏阅读顺序、字体角色、统计块术语、区域编号、地图覆盖和插图身份均需核验。normalize.py / render.py 保留偏 PF1 的统计块词表；其他规则系统须在模块副本中修改，区域字母默认 A–H。

book.page_size/margins 同时影响 HTML、衬页和 QA 阈值，但 CSS 中扉页绝对坐标、图像高度与文字字号不会按比例自动缩放。换开本需改模块 theme.css 并视觉验证。侧标签的逐字栅格化位置因书而异，当前模板不强加旧书坐标；按需要在模块 make_assets.py 中补充。

调整颜色和纹理只修改模块 CSS；已有图片可放到本地 assets 下再引用。默认纯色主题用于启动和测试，不代表已经复刻原版视觉。
