# 版式系统

语义源与表现分离：normalize.py 负责结构，render.py 负责 HTML，theme.css 负责排版，build.py 负责串行编译和合并。

默认开本 603×783 pt，双栏、17 pt 栏距，正文 9.1/15.4 pt。左右页内外边距对调；页边显示书名/章名和对应原版页码。book.json 覆盖开本和边距，细部组件坐标仍需人工适配。

字体每个字重独立 family（Book Serif、Book Semi、Book Black、Book Sans、Book Sans Bold）；朗读框和图注用文楷；拉丁装饰字体后必须有中文回退。只用静态 glyf TrueType 作为 PDF 主字体，完成后检查实际嵌入字体类型。

章首有两页：左页章名、英文名、作者、可选译者；右页章内目录与地图目录，用 target-counter 引用实时页码。每章编译时先加 dummy 页让跨页从左页开始，编译后删掉，起始 page counter 相应减一。CSS 不含特定第 N 章的样式。

插图使用页顶或栏顶浮动；统计块允许长块分断，短块尽量保留；保留朗读框、侧栏、升级进度、讲义和表格。纹理默认纯色；原版纸面、边框、章首由本地 art 配置构建，仓库不附版权图片。

避免 text-shadow（可能重复 PDF 文本）、右浮动落栏底（溢出）、零高度 marker 紧接强制分页（空白页）。首横幅应取消不必要的 break-before；任何布局改动后都检查低文字量页面及书签。
