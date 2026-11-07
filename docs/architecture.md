# 架构

Skill 提供决策流程与检查点；Python 工具执行可重复的数据变换；每本书有独立配置、模块脚本和产物。书籍输入与源 Skill 互不覆盖。

## 分层

1. 输入层：input/original.pdf、input/translation/*.md 只读。初始化复制输入，不修改源文件。
2. 盘点与提取：inventory 发现字体和图像；roles.json 的有序规则将文本转为英文角色流；图像提取处理 SMask。
3. 结构层：zhparse 切单元，align 用数字/编号/拉丁词锚点构建单调链并插值，normalize 结合配置和术语推断语义。映射、去重和 drop 都保留可审阅记录。
4. 素材层：art 配置合成边框与章首，maps 替换标签，figures 分类并保存人工覆盖，optimize 只写降采样副本。
5. 表现层：语义 Markdown 与图注渲染 HTML，CSS 控制双栏、统计块、侧栏、扉页与字体；译者字段从章节配置读取并转义。
6. 出版层：build 用当前 Python 解释器调用准备脚本，用配置浏览器逐章编译；删除 dummy，插入奇偶衬页，合并并写目录、书签、页码标签、元数据。
7. QA 层：内容片段核对、底部溢出、结构、逐页低分辨率渲染、联系表与人工审查。

## 路径规则

Skill 位于 skills/trpg-zh-typesetting，模块默认位于仓库 modules。new_module.py 根据自身真实路径确定仓库根，支持符号链接安装。模块 book.tools_root 由初始化器计算成相对路径；TRPG_TOOLS_ROOT 可以覆盖。Python 依赖来自调用者所选解释器，Node CLI 来自依赖根的 node_modules 或 VIVLIOSTYLE_CLI。

HTML 在 build，因此资源引用 ../assets、样式 ../src/styles；CSS 在 src/styles，因此资源引用 ../../assets。字体使用相对链接到本地 fonts；文楷子集属于各自模块。搬迁整个仓库后默认相对路径仍有效；单独搬模块要更新 tools_root 和字体链接。

## 与源项目的差异

保留语义层、动态章节数、统计块分组、图注来源核验、串行编译和 QA；迁入最新浏览器环境变量与章首译者显示。移除六章页码、具体书名、图片 xref、译名、特定第三章 CSS 和封面配置，将数据放入 book/roles/art 等配置。默认不带原版纹理，避免把具体书籍适配误当通用模板。

原 Node 清单和锁逐字节保留；Python 固定版本快照说明来源，不虚构解析器锁。仓库与原项目没有运行时路径依赖。
