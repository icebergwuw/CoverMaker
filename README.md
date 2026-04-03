# Cover Maker

Python + Pillow 批量生成封面图，支持三种品牌模板。

线上地址：https://cover-maker-seven.vercel.app

## 功能模式

| 模式（Tab） | 尺寸 | 说明 |
|---|---|---|
| **HowToTips** | 1130×860 | 左图右文，纯色背景 + 白色竖线装饰 |
| **Blog** | 1200×630 | 彩色背景 + 贝塞尔曲线斜线装饰，左文右图，5套配色模板 |
| **Templates** | 1200×630 | PDF Agile 品牌模板：左侧预览图 + 右侧黑底文字 |

### Blog 模式配色模板（来自 Figma SVG 精确值）

| 模板 | 背景 | 斜线（粗） | 斜线（细） | 文字 |
|---|---|---|---|---|
| 薄荷绿 `mint`   | `#D5FFEC` | `#16724E` | `#222222` | `#222222` |
| 暖黄 `warm`     | `#FFBE4C` | `#F16E3D` | `#000000` | `#5A1E08` |
| 橙黄 `orange`   | `#FFD272` | `#F16E3D` 80% | `#222222` | `#222222` |
| 青绿 `teal`     | `#84DCD4` | `#003ACD` | `#222222` | `#222222` |
| 粉色 `pink`     | `#FFC0E5` | `#EA4B3D` 80% | `#FF8C84` | `#222222` |

## 本地运行

```bash
pip install -r requirements.txt
python app.py
# 浏览器自动打开 http://127.0.0.1:5299
```

## CLI 用法

```bash
# HowToTips
python make_cover.py <图片路径> "<标题>" [颜色名或HEX]
# 颜色预设：teal / tan / navy / olive / rose / slate / warm

# Blog
python make_howtotips2_cover.py <图片路径> "<标题>" [模板名]
# 模板名：mint / warm / orange / teal / pink

# Templates (PDF Agile)
python make_pdfagile_cover.py <预览图路径> "<标题>" [输出路径]
```

## 项目结构

```
cover-maker/
├── app.py                    # Flask Web 服务（本地 + Vercel 共用）
├── gui.py                    # Tkinter 桌面 GUI（仅支持 HowToTips 模式）
├── make_cover.py             # HowToTips 封面生成
├── make_howtotips2_cover.py  # Blog 封面生成（aggdraw bezier 斜线）
├── make_pdfagile_cover.py    # PDF Agile 封面生成
├── api/
│   └── index.py              # Vercel 入口（from app import app）
├── assets/                   # 品牌素材（背景、logo 等）
├── fonts/
│   └── Montserrat-Bold.ttf
├── requirements.txt          # flask, pillow, numpy, aggdraw
├── vercel.json
└── CoverMaker.spec           # PyInstaller 打包配置
```

## 部署

```bash
vercel --prod
```

## 打包为 macOS App

```bash
pyinstaller CoverMaker.spec
# 输出：dist/CoverMaker.app
```
