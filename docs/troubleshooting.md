# 排障

- Node 版本错误：真实锁中的 Vivliostyle 要求 ≥22.12，系统 Node 18 不足；选定满足版本的 Node 并设 NODE。不要自行重新生成锁绕过依赖。
- 找不到浏览器：显式设置 VIVLIOSTYLE_BROWSER 并检查执行权限。CLI 接受 --executable-browser，不接受配置中的 browser 对象。Linux Python/Node 配 Linux 浏览器，Windows 版本配 Windows 路径。
- .env 没生效：脚本不自动读取，Bash 执行 set -a; source .env; set +a。
- 新模块找不到配置：必须用 new_module.py 初始化；模板的 *.example.json 会复制为实际 JSON 名。真实章节范围、角色规则需手动配置。
- 找不到 CLI：检查 book.tools_root 或 TRPG_TOOLS_ROOT；VIVLIOSTYLE_CLI 指向 dist/cli.js。单独搬模块也要修字体链接。
- 译稿文件解析失败：名称以唯一三位章号开头，章节从 001 连续；UTF-8。不要把两个同章文件静默覆盖。
- 覆盖率低：查看 content_check.json 和 units_chN；确认 drop/去重、统计块孤儿行、标题替换、表格与跨栏。禁止靠删除输入或放宽阈值掩盖问题。
- 章首后空白：检查零高度 orig/running 与 break-before；生成低文字量页清单并实际放大。章首页必须是合并后偶数物理页。
- 译者未显示：检查章节 translator 非空，render 和 CSS 都来自当前模板，完成重建；查看 HTML 中 op-translator。
- PDF 有 Type3/缺字：核对静态 glyf TTF、独立字重 family、中文回退和子集字符；新增文字后重做 subset。检查实际 PDF 字体，不能仅看 CSS。
- 图像/地图错误：在 figures.json 手改并保留 use/kind/placement；配置排除底纹。地图 redaction 可能破坏矢量描边，检查渲染图并保留原版。
- 目录页码变化：完整构建两次或直到 state 稳定，最后不要只运行 --only。章首占位页由 build 删除，不手删真实页面。
- 并行内存不足或浏览器退出：用 --jobs 2 降低并发，或 --serial（等同 --jobs 1）。默认最多 4 个任务；提取和素材准备仍按顺序。已有模块须同时更新 build.py 和 vivliostyle.config.js，才能获得独立工作目录；不要同时对同一模块启动两次构建。
- 并行页码超过“章节数 + 1”轮仍未稳定：查看 work/pdf/state.json、HTML 的 page counter 和会受页码宽度影响的 CSS，使用 --serial 定位；构建器会停止，不发布未稳定的合订本。
- 图片压缩后 PDF 报错：不要 rewrite_images 成书；使用构建前 optimize_images 的副本。
- QA 提示低文字量：可能是艺术页、衬页、空白或漏字，需逐页确认；列表不是自动通过结论。
- 依赖未安装：check_env 返回非零是预期。按 README 手动安装，本工具不会联网修复。当前发布的测试边界见 validation.md。
