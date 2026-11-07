# 通用模板

new_module.py 将 scripts、主题、Vivliostyle 配置和脱敏 JSON 复制到本地模块。这里不含任何具体书籍的素材或译文，不要把模块配置复制回来覆盖模板。

脚本职责：
- zhparse/align/normalize：译稿切单元、中英锚点对齐、语义结构；统计块词表默认偏 PF1。
- extract_en/extract_images：英文角色流与带蒙版图像。
- make_assets/maps/figures/optimize_images：配置化边框扉页、地图替字、插图分类、压缩副本。
- captions：本章图注词表核验。
- render/build：语义源到 HTML、译者署名、串行 Vivliostyle、占位页删除、衬页、书签和元数据。
- runtime：模块配置、浏览器和依赖路径。
- qa_content/qa_overflow/qa_structure/sheet/report_art：内容、版面、结构、联系表和美术报告。
- show_align：对齐调试。

配置和适配格式见 ../references/adapting.md；渲染细节见 ../references/design.md。修改模板后运行仓库 tests，不需要使用任何商业模组来验证通用功能。
