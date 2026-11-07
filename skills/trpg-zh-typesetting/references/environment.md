# 环境与依赖

完整安装命令见仓库根 README.md。需要 Python ≥3.12（排除 3.14.1）、Node ≥22.12、npm、Chrome/Chromium。推荐 Linux 或 WSL，8 GB 内存时逐章串行。Node 版本来自真实 package-lock.json 中 Vivliostyle 11.4.0 的 engines；不要沿用旧项目 Node 18 的要求。

Python 直接依赖在 pyproject.toml，requirements.txt 固定直接和传递依赖版本。它是版本快照，非哈希锁；未生成或虚构 uv.lock。不要自动安装。用户安装命令为：
```bash
python3.13 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
PUPPETEER_SKIP_DOWNLOAD=1 PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=1 npm ci
```
保留的 package.json 与 package-lock.json 来自源 shared/tools，两个文件逐字节保留。npm ci 不下载浏览器；本机需自行准备 Chromium。初始化脚本只建立本地目录和 .env，不安装依赖。脚本不会自动读取 .env，Bash 使用 set -a; source .env; set +a。

## 字体

仓库不附字体。用户自行从合法来源取得静态 TrueType 或变量 TrueType：
- NotoSerifSC-VF.ttf、NotoSansSC-VF.ttf；
- LXGWWenKai-Regular.ttf、LXGWWenKai-Medium.ttf；
- Cinzel.ttf（变量）、CinzelDecorative-Bold.ttf（静态）。

放入仓库 fonts/ 或用 TRPG_FONTS 指定后，运行：
```bash
.venv/bin/python skills/trpg-zh-typesetting/tools/font_prep.py instances
.venv/bin/python skills/trpg-zh-typesetting/tools/font_prep.py subset modules/my-book
```
实例化输出 NotoSerifSC-Regular/SemiBold/Black、NotoSansSC-Regular/Bold、Cinzel-Bold。初始化工具在模块 assets/fonts 中建立指向这些字体及 CinzelDecorative-Bold 的相对链接；文楷子集写到模块自己的 assets/fonts，避免不同书籍互相覆盖。新增图注、署名后重做子集。替换字体时同时修改模块 theme.css 的文件名和 family。

## 环境变量

VIVLIOSTYLE_BROWSER 是浏览器可执行文件路径，支持带空格的路径；未设时尝试系统 google-chrome/chromium/chromium-browser/chrome。NODE 可指定 Node；VIVLIOSTYLE_CLI 可指定 CLI 的 dist/cli.js；TRPG_TOOLS_ROOT 覆盖依赖根；TRPG_MAP_FONT/TRPG_HAND_FONT 覆盖地图栅格字字体。TRPG_ROOT 只控制初始化目的根。TRPG_FONTS 控制字体准备输入目录，初始化时也用于字体链接目标。所有可执行程序必须与当前操作系统一致，WSL 不混用 Windows Python 的 .venv。
