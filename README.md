# Cover Maker

用 Python + Pillow 批量生成 YouTube/博客封面图，支持三种品牌模板。

## 功能模式

| 模式 | 尺寸 | 说明 |
|---|---|---|
| **HowToTips** | 1130×860 | 左图右文，纯色背景 + 白色竖线装饰 |
| **HowToTips 2** | 1200×630 | 暖黄背景 + 斜线装饰，左文右图 |
| **PDF Agile Templates** | 1200×630 | 品牌模板：左侧预览图 + 右侧黑底文字 |

## 本地运行（Web GUI）

```bash
pip install -r requirements.txt
python app.py
# 浏览器自动打开 http://127.0.0.1:5299
```

## 本地运行（Tkinter GUI）

```bash
python gui.py
```

> 仅支持 HowToTips 模式。

## CLI 用法

```bash
# HowToTips
python make_cover.py <图片路径> "<标题>" [颜色名或HEX]

# HowToTips 2
python make_howtotips2_cover.py <图片路径> "<标题>" [颜色HEX]

# PDF Agile
python make_pdfagile_cover.py <预览图路径> "<标题>" [输出路径]
```

颜色预设（HowToTips）：`teal` / `tan` / `navy` / `olive` / `rose` / `slate` / `warm`

## 项目结构

```
cover-maker/
├── app.py                    # Flask Web 服务（本地 + Vercel 共用）
├── gui.py                    # Tkinter 桌面 GUI
├── make_cover.py             # HowToTips 封面生成逻辑
├── make_howtotips2_cover.py  # HowToTips 2 封面生成逻辑
├── make_pdfagile_cover.py    # PDF Agile 封面生成逻辑
├── api/
│   └── index.py              # Vercel 入口（import app）
├── assets/                   # 品牌素材（背景、logo 等）
├── fonts/
│   └── Montserrat-Bold.ttf
├── requirements.txt
├── vercel.json
└── CoverMaker.spec           # PyInstaller 打包配置
```

## 部署到 Vercel

```bash
vercel --prod
```

需要在 Vercel 项目设置中把 Python 版本设为 3.11+。

## 打包为 macOS App

```bash
pyinstaller CoverMaker.spec
# 输出：dist/CoverMaker.app
```
