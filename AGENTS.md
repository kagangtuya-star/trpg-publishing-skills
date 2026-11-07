# trpg-publishing-skills

本文件适用于整个仓库。本仓库只维护可分发的 Skill、工具、模板与原创示例；具体书籍在本地 `modules/`，该目录不提交。

- 排版入口：先读 `skills/trpg-zh-typesetting/SKILL.md`，按需读其 `references/`。安装与操作命令以 `README.md` 为准。
- 通用脚本位于 `skills/trpg-zh-typesetting/templates/scripts/`；初始化工具复制它们到模块。具体书籍修改模块副本，通用修复才修改模板。
- 输入 PDF 与译稿只读，不改译文措辞；`src/chapters/` 是模块生成物，应修改配置或模块脚本后重建。
- 不提交原版、译文正文、美术、地图、封面、字体、PDF、依赖目录、虚拟环境或缓存。演示与测试使用原创占位数据。
- Python 直接依赖见 `pyproject.toml`，固定版本快照见 `requirements.txt`；Node 使用真实 `package-lock.json`。不自动安装依赖，不手编解析器锁文件。
- Vivliostyle 必须逐章串行。浏览器路径使用 `VIVLIOSTYLE_BROWSER`，依赖根和字体路径按 Skill 文档配置。
- 修改后从仓库根运行 `python tools/validate_repository.py`、`python -m unittest discover -s tests -v`，解释器需具备 README 声明的依赖；提交前执行 `git diff --check`。
- 版式/合并逻辑变更还需用原创示例真实编译并做 QA、实际看图；无浏览器集成测试不能替代视觉验收。
- 整体授权状态见 README；未经权利人确认，不补写推测的代码许可证。
