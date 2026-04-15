# Cover Maker & Auto Publish & Localize

本地 Flask 工具集，提供三个功能页面：

| 页面 | 路径 | 说明 |
|---|---|---|
| Cover Maker | `/` | 批量生成封面图（三种品牌模板） |
| Auto Publish | `/auto-publish` | AI 全自动选题→写文→翻译→发布 |
| Localize | `/localize` | 多语言本地化，从 Excel 读取译文写入 CMS |

---

## 快速启动

```bash
cd cover-maker
python3 app.py
```

浏览器会自动打开 `http://127.0.0.1:5299`。局域网同事可访问 `http://<你的IP>:5299`。

---

## 环境变量配置

所有密钥统一放在 `.env`（已加入 `.gitignore`，不会提交到 git）。

复制模板：
```bash
cp .env.example .env
```

然后填入对应值：

| 变量 | 说明 |
|---|---|
| `CMS_TOKEN_TEST` | 测试环境 CMS Bearer Token |
| `CMS_BASE_TEST` | 测试环境 CMS 地址 |
| `CMS_TOKEN_PROD` | 正式环境 CMS Bearer Token |
| `CMS_BASE_PROD` | 正式环境 CMS 地址 |
| `FE_BASE_TEST` | 测试环境前端地址 |
| `FE_BASE_PROD` | 正式环境前端地址 |
| `TAVILY_API_KEY` | Tavily 搜索 API Key |
| `GEMINI_API_KEY` | Google Gemini API Key |

> 线上部署（Railway）时，在 Railway 控制台 Variables 里填入以上变量，不需要 `.env` 文件。

---

## 项目结构

```
cover-maker/
├── app.py                        # Flask 主服务，启动入口
├── auto_publish.py               # Auto Publish 逻辑
├── publish_article.py            # 发布文章到 CMS（测试环境）
├── localize_agent.py             # Localize 逻辑，支持 test/prod 双环境
├── localize_html.py              # Localize 页面 HTML/JS
├── localize_special_topic_page.py# 专题页本地化核心逻辑
├── make_cover.py                 # HowToTips 封面生成
├── make_howtotips2_cover.py      # Blog 封面生成（aggdraw bezier 斜线）
├── make_pdfagile_cover.py        # PDF Agile 封面生成
├── api/
│   └── index.py                  # Vercel 入口
├── assets/                       # 品牌素材
├── fonts/                        # 字体文件
├── .env                          # 本地密钥（不提交 git）
├── .env.example                  # 密钥模板（提交 git）
├── .gitignore
├── requirements.txt
├── railway.json
└── vercel.json
```

---

## Cover Maker 模板说明

| 模板 | 尺寸 | 入口文件 |
|---|---|---|
| HowToTips | 1130×860 | `make_cover.py` |
| Blog | 1200×630 | `make_howtotips2_cover.py` |
| PDF Agile Templates | 1200×630 | `make_pdfagile_cover.py` |

### Blog 配色

| 名称 | 背景 |
|---|---|
| `mint` | `#D5FFEC` |
| `warm` | `#FFBE4C` |
| `orange` | `#FFD272` |
| `teal` | `#84DCD4` |
| `pink` | `#FFC0E5` |

---

## 依赖安装

```bash
pip install -r requirements.txt
# 或 macOS 系统 Python：
/usr/bin/python3 -m pip install -r requirements.txt --user
```

---

## 部署

**Railway**（推荐）：push 到 GitHub，Railway 自动部署，在控制台 Variables 里配置环境变量。

**Vercel**：
```bash
vercel --prod
```
