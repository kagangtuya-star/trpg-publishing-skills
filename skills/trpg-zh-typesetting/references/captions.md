# 图注

身份必须以原版 CAPTION 角色为依据；不要用邻近统计块或标题猜身份。captions.py 在同页取 y 最近的图注，只是定位候选，同页多图时需人工确认。

中文名逐字取自对应章译稿。配置 caption_glossary.json，按英文图注大写、弯引号转直引号后的值作为键。没有原版图注则不添加。译稿已有词拼接成短语时设 composed=true，并在校对报告中列出。

运行 scripts/captions.py：missing-glossary 或 unattested 导致非零退出；attested 表示逐字命中，composed 仍需人工确认。captions.json 中 manual=true 保留手工覆盖，但这种覆盖不会自动重新核对，必须人工审查。

图注只为 portrait/figure 输出，HTML 文字转义并写入 alt。新增图注、署名或横幅后重做 font_prep.py subset，检查缺字、正文覆盖率和版面溢出。产物、图注词表和审查报告属于具体书籍，不提交到 Skill 仓库。
