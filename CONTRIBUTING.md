# 贡献约定

整体代码和文档授权状态尚待权利人确认；提交补丁不代表自动授予本仓库未声明的许可证。贡献者需确认自己对贡献内容拥有相应权利，不加入第三方模组正文、美术、地图、封面、字体或私密信息。

通用改动只针对 Skill、模板和工具；具体书籍适配留在本地 modules。保持译稿只读与措辞完整，保留去重/drop/图注来源的审查能力。不要为了演示将真实模组配置、译者身份或大段译文加入仓库。

验证：
```bash
.venv/bin/python tools/validate_repository.py
.venv/bin/python -m unittest discover -s tests -v
git diff --check
```
改变分页、字体、扉页、浮动或合并逻辑时，还需在具备完整环境的本机用原创示例做真实构建和视觉 QA，并说明实际检查范围。无浏览器测试不能证明最终分页合格。

Python 依赖改动同时更新 pyproject.toml 与准确的版本快照并说明解析/验证环境；不要手编声称由解析器生成的锁。Node 依赖变更需经明确需求、使用真实 npm 生成锁并审阅，不能只改 lock 的版本号或校验值。不要提交 node_modules、虚拟环境、缓存或产物。

提交前逐项审查 git diff --cached --name-only 和暂存文本；.gitignore 是防线之一，不能替代版权和敏感内容审查。
