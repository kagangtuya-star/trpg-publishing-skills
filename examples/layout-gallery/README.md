# TRPG 模组结构与排版样张

[离线画廊](index.html) · [12 页合订本](pdf/trpg-layout-collection.pdf) · [机器 QA 记录](qa.json)

六套原创、系统中立的两页样张，供比较模组的信息组织和视觉层级。直接打开 `index.html` 查看双页预览，点击预览进入独立 PDF。无需启动服务或安装依赖即可阅读成品。

| 结构 | 样张 | 主要元素 |
| --- | --- | --- |
| 线性章节冒险 | [雾钟修道院](pdf/01-linear.pdf) | 三幕推进、朗读框、场景威胁、钟声进度 |
| 线索调查 | [零时来信](pdf/02-investigation.pdf) | 证据编号、节点关系、证人信息、时间线 |
| 荒野六角探索 | [白盐荒原](pdf/03-hexcrawl.pdf) | 原创六角地图、地标索引、旅行程序、d6 迹象表 |
| 编号地城 | [井底的第七扇门](pdf/04-dungeon.pdf) | 原创房间图、连接关系、机关、区域速查 |
| 城市派系 | [夜市停电事件](pdf/05-factions.pdf) | 派系关系、资源与底线、焦点事件、时钟 |
| 长篇战役 | [远航者纪事](pdf/06-campaign.pdf) | 章节航线、重新上桌、里程碑、跨章影响 |

## 源文件与重建

- `demos.json`：全部原创正文和主题参数。
- `theme.css`：印刷样式。开本 603 × 783 pt，各页版心和页脚固定。
- `build_gallery.py`：生成内联 SVG/HTML，串行调用一次 Vivliostyle，生成书签、页码标签、分册、预览和 QA。
- `pdf/`、`previews/`、`index.html`、`qa.json`：可直接查看的成品。
- `_work/`：临时 HTML、Vivliostyle 配置和字体链接，已忽略。

重建使用仓库根目录的既有 Python/Node 依赖，安装命令见[主 README](../../README.md)。本脚本不会安装依赖或下载浏览器。需要本机已有的 Chromium 和允许嵌入的中文字体：

```bash
# 从仓库根执行；按本机实际位置设置。
export VIVLIOSTYLE_BROWSER=/absolute/path/to/chrome
export TRPG_DEMO_FONT=/absolute/path/to/cjk.ttf
.venv/bin/python examples/layout-gallery/build_gallery.py
```

也支持 `.otf` / `.ttc`；字体变更后须重新检查全部页面。Linux 默认尝试系统文泉驿路径 `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`，其他系统请显式设置字体。可用 `--font /path/to/font` 覆盖环境变量。

脚本支持主工作流相同的 `NODE`、`VIVLIOSTYLE_CLI`、`TRPG_TOOLS_ROOT` 环境变量，默认从仓库根寻找 `node_modules/@vivliostyle/cli/dist/cli.js`。`VIVLIOSTYLE_BROWSER` 未设置时尝试 PATH 中的 `google-chrome`、`chromium` 或 `chromium-browser`。浏览器会启动本地渲染服务，受限环境需允许本地监听。

只生成排版 HTML 与画廊页面、不启动浏览器：

```bash
.venv/bin/python examples/layout-gallery/build_gallery.py --sources-only
```

此模式不会生成或刷新 PDF、预览和 QA；已有成品可能与改后的源码不同。完整构建会覆盖本目录生成物，不会读写用户模块或源项目。它是独立的版式研究渲染器，不通过原版 PDF 提取流程，不能用它替代真实书籍工作流的回归验证。

## 验证与边界

完整构建要求恰好 12 页，并逐套检查原创正文、表头与表格内容是否出现在 PDF 文本层，检测文字越出版心、Type3 字体和渲染警告；失败返回非零。`qa.json` 保存每套结果，双页 JPG 用于人工检查图形、配色与重叠。分册各含两级书签，合订本含六个结构书签，均有页码标签。

本组为紧凑样张：没有完整规则系统或经跑团验证的数值平衡；跨章合订展示的是章节导航结构，没有实现一整本长篇内容。固定两页布局不承诺任意长度正文自动适配。文字覆盖检查和边界检测不能发现所有图文重叠，修改 CSS、字体或数据后必须实际看图。PDF 未做印厂打样、PDF/X、CMYK 或出血验收。

随附版本已用本机现有 Vivliostyle 11.4.0 / Chromium 实际构建：12 页、六套正文覆盖与版心检查全部通过，无 Type3 字体或渲染警告；六张双页预览均已人工查看，并修正了六角网格间距。另实际验证了七份 PDF 的书签、页码标签、开本与字体嵌入，以及“缺失正文”和“页数错误”会触发 QA 失败。没有为本次构建下载依赖、浏览器或字体。

## 原创内容与字体

正文、地点、人物、地图、建筑示意图及关系图均为本仓库此次创建的原创演示数据。图形由脚本内联 SVG 绘制，不使用外部美术、商用模组内容、输入 PDF 或中文译稿。

随附成品使用本机文泉驿正黑（WenQuanYi Zen Hei）字体，并仅在 PDF 内嵌所需子集，不附带字体二进制。构建时核对了系统包的 `copyright`：该字体包含 GPL-2 的文档嵌入例外，使用其字体或未改动部分生成文档不会使文档自动受到 GPL 约束。字体详情见 [文泉驿项目](https://wenq.org/wqy2/index.cgi?ZenHei)；换用其他字体前请自行核对嵌入及分发权限。

这里不为整体源码或文档补写新的许可证。仓库授权状态仍以[主 README 的版权说明](../../README.md#版权与授权)为准。
