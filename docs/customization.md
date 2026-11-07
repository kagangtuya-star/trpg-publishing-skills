# 定制指南

先读 [配置参考](../skills/trpg-zh-typesetting/references/adapting.md)。new_module.py 将完整模板复制到模块；具体书籍修改模块副本，通用缺陷才修 Skill 模板。

## 章节与署名

chapters.json 数字键从 1 连续。pages 是原版物理页码范围，title_line 是译稿章标题行；parts 映射原译稿行号到 [部分标签,标题]。front 仅用于第一章的全书引言，advancement 为升级轨迹行段。drop 排除已核验的非正文范围。author_zh 优先于 author_en；translator 可空，非空时在章首页独立显示。

修改标题、图注或署名后重做字体子集。不要删除译文中真实正文来满足覆盖率。

## 原版风格

roles.json 以更具体的字体/颜色/字号规则在前，通用规则在后，role=null 排除页码和边注。默认 Helvetica 示例只适合原创测试，不代表真实 TRPG 的字体映射。

art.json 的边框片段使用提取元数据中的 xref 和页面 pt 坐标；openers 指两个原版页。地图用 maps.json 的 bbox、labels 替字，保留区域编号。默认空美术生成纸色背景。需要原版纹理时在本地 CSS 引用本地素材，验证标签覆盖没有损坏地图。

## 主题与开本

theme.css 控制字体、配色、组件和扉页绝对坐标。book.json 的开本和边距会传入 HTML、衬页与 QA；改尺寸后仍需重测章首作者/译者位置、目录高度、插图最大高度。默认 CSS 不是自动缩放布局系统。

所有插图尽量页顶/栏顶浮动，避免栏底右浮动。字体每字重一个 family，装饰字体提供中文回退。修改后做样章和全套 QA。

## 规则系统与脚本

默认统计块术语主要适合 PF1。其他规则系统调整 normalize.py 的 STAT/CR/AREA 识别和 render.py 的字段粗体；通过孤儿行保留、内容覆盖及真实统计块抽查核验。对齐有大量数字/拉丁文时效果更好，叙事段落仍需人工审阅。

## 运行位置

默认模块位于 modules/<name>；--root 创建其他工作区时，相对 tools_root 仍指向 Skill 所属仓库。搬迁后可更新该值或设 TRPG_TOOLS_ROOT。TRPG_FONTS 在初始化时决定字体链接目标；更改环境变量不会自动重写已存在的链接。
