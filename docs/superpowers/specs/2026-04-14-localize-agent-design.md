# Localization Agent — 设计文档

**日期**: 2026-04-14
**状态**: 待实现
**路径**: `cover-maker/app.py` + `cover-maker/localize_agent.py`

---

## 1. 目标

在现有 `http://127.0.0.1:5299` 工具里新增第三个 Tab「🌐 Localize」，让用户可以通过 Web UI 对任意 special-topic-page 批量生成多语言版本，无需命令行。

---

## 2. 集成方式

**方案 A — 新 Tab 集成**：在现有 Flask app（`app.py`，端口 5299）新增路由，与 Cover Maker / Auto Publish 并排共用同一进程。导航栏新增第三个 tab 入口。

---

## 3. 翻译来源

两种模式，在 UI 上切换：

| 模式 | 说明 |
|---|---|
| Excel 模式 | 上传或指定本地 Excel 文件路径 + sheet 名，走现有 `build_translation_map()` |
| AI 翻译模式 | 无 Excel，调 Gemini API 逐字段翻译，适用于没有 Excel 的新文章 |

当前已有 Excel 的文章（Organize PDF 等14篇）走 Excel 模式；未来新文章走 AI 翻译模式。

---

## 4. 页面结构（`/localize`）

```
┌─────────────────────────────────────────────┐
│  Cover Maker │ Auto Publish │ 🌐 Localize ← │
├─────────────────────────────────────────────┤
│                                             │
│  文章                                       │
│  [下拉：从 CMS 自动拉取英文版列表]  [刷新]   │
│                                             │
│  翻译来源                                   │
│  ◉ Excel   Excel路径: [________] Sheet: [_] │
│  ○ AI 翻译（Gemini）                        │
│                                             │
│  目标语言         [全选] [清空] [未做过的]   │
│  [fr✓][zh-Hant✓][es✓][de][pt][it]...       │
│  绿=已完成 · 蓝=已选 · 红=失败              │
│                                             │
│  [▶ 开始本地化（N 种语言）]                 │
│                                             │
│  进度 ████████░░ 6/18                       │
│  ┌─ 日志 ──────────────────────────────┐   │
│  │ ✓ fr (id=68) — verify 通过          │   │
│  │ ▶ de — POST /localizations...       │   │
│  └────────────────────────────────────┘   │
│                                             │
│  失败条目: [ar 502] [↺ 重试]               │
│                                             │
├─────────────────────────────────────────────┤
│  历史记录                                   │
│  Organize PDF · 2026-04-14 · 18种  [fr][de]…│
│  Extract PDF  · 2026-04-13 · 3种   [fr]…   │
└─────────────────────────────────────────────┘
```

---

## 5. 后端 API

### `GET /localize`
返回 Localize Tab HTML 页面。

### `GET /api/localize/pages`
从 CMS 拉取所有英文版 special-topic-pages，返回：
```json
[
  {"id": 5, "title": "Organize PDF", "slug": "organize-pdf", "locales": ["fr","de","es",...]}
]
```
`locales` 字段表示该页面已有哪些语言版本（用于在格子上显示绿色已完成状态）。

### `GET /api/localize/history`
返回 `localize_history.json` 内容。

### `POST /api/localize/run`
触发本地化任务，返回 SSE 流。

请求体：
```json
{
  "page_id": 5,
  "sheet_name": "Organize PDF",
  "excel_path": "/Users/ice/Downloads/专题页文案与多语言本地化-更新至20260408.xlsx",
  "translation_mode": "excel",
  "locales": ["de", "pt", "it"]
}
```

SSE 事件格式：
```
data: {"type": "start",    "locale": "de"}
data: {"type": "progress", "locale": "de", "step": "POST", "msg": "创建成功 id=71"}
data: {"type": "verify",   "locale": "de", "pass": true,   "warnings": []}
data: {"type": "done",     "locale": "de", "new_id": 71}
data: {"type": "error",    "locale": "ar", "msg": "502 Bad Gateway"}
data: {"type": "finished", "total": 3, "ok": 2, "fail": 1}
```

### `POST /api/localize/retry`
重试单个失败语言。

请求体：
```json
{"page_id": 5, "locale": "ar", "sheet_name": "Organize PDF", "excel_path": "...", "translation_mode": "excel"}
```
同样返回 SSE 流。

---

## 6. 历史记录格式（`localize_history.json`）

```json
[
  {
    "page_id": 5,
    "page_title": "Organize PDF",
    "sheet_name": "Organize PDF",
    "run_at": "2026-04-14T10:00:00Z",
    "results": [
      {"locale": "fr", "new_id": 68, "status": "ok",   "warnings": []},
      {"locale": "ar", "new_id": null, "status": "fail", "error": "502 Bad Gateway"}
    ]
  }
]
```

---

## 7. AI 翻译模式（无 Excel）

当 `translation_mode = "ai"` 时：
- `build_translation_map()` 改为调 Gemini API，传入英文 block 所有文本字段，批量返回目标语言翻译
- MANUAL_PATCHES 机制保留，AI 翻译结果优先级低于 MANUAL_PATCHES
- verify() 逻辑不变

AI 翻译 prompt 结构：
```
将以下 PDF 工具文案从英文翻译成 {locale_name}。
保持专业、自然。软件名（PDF Agile 等）不翻译。
返回 JSON: {"原文": "译文", ...}

文本列表:
["Organize PDF pages", "Merge and split PDF files", ...]
```

---

## 8. 环境配置

| 环境 | CMS Base URL | Token 来源 |
|---|---|---|
| 测试 | `http://pdfagile-cms.aix-test-k8s.iweikan.cn` | `localize_special_topic_page.py` 硬编码 |
| 正式 | `https://cms.pdfagile.com` | 明天提供，存入环境变量 `CMS_TOKEN_PROD` |

UI 上加一个环境切换开关（测试 / 正式），切换后 token 和 base url 同步切换。

---

## 9. 文件结构变动

```
cover-maker/
├── app.py                        ← 新增 /localize 路由 + /api/localize/* 路由
├── localize_agent.py             ← 新文件：SSE 任务执行、历史记录读写、AI翻译模式
├── localize_special_topic_page.py← 现有脚本，不改动，被 localize_agent.py 调用
├── localize_history.json         ← 新建，历史记录持久化
└── docs/superpowers/specs/
    └── 2026-04-14-localize-agent-design.md
```

`app.py` 改动范围：
- 导航栏加第三个 tab 链接
- `import localize_agent`
- 注册 4 个新路由（`/localize`, `/api/localize/pages`, `/api/localize/run`, `/api/localize/retry`）

---

## 10. 实现顺序

1. `localize_agent.py` — 核心逻辑（pages 拉取、SSE runner、history 读写）
2. `app.py` — 注册路由 + 导航 tab
3. Localize Tab HTML — 完整前端页面（内嵌在 app.py 或独立模板文件）
4. AI 翻译模式 — Excel 模式稳定后再加
