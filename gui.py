#!/usr/bin/env python3
"""
Cover Maker GUI
拖入图片 → 填标题 → 选颜色 → 生成
"""

import os
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

# 确保能找到 make_cover
sys.path.insert(0, os.path.dirname(__file__))
from make_cover import make_cover, PRESETS

# ── 颜色配置（显示名 → key）────────────────────────────
COLOR_OPTIONS = [
    ("Teal 蓝绿",  "teal"),
    ("Tan 米棕",   "tan"),
    ("Navy 深蓝",  "navy"),
    ("Olive 橄榄", "olive"),
    ("Rose 玫瑰",  "rose"),
    ("Slate 石板", "slate"),
    ("Warm 暖棕",  "warm"),
]

PREVIEW_W = 565
PREVIEW_H = 430

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Cover Maker")
        self.resizable(False, False)
        self.configure(bg="#1e1e1e")

        self.img_path   = tk.StringVar()
        self.title_var  = tk.StringVar()
        self.color_key  = tk.StringVar(value="teal")
        self.output_path = None
        self._preview_img = None  # 防止GC

        self._build_ui()
        self._update_color_swatch()

    # ── UI 构建 ────────────────────────────────────────
    def _build_ui(self):
        PAD = 16
        BG  = "#1e1e1e"
        FG  = "#f0f0f0"
        ACC = "#4A8FA0"
        ENTRY_BG = "#2d2d2d"
        FONT_LBL  = ("SF Pro Display", 12)
        FONT_BOLD = ("SF Pro Display", 13, "bold")
        FONT_BTN  = ("SF Pro Display", 13, "bold")

        # ── 左列：控制区 ──────────────────────────────
        left = tk.Frame(self, bg=BG, width=300)
        left.pack(side="left", fill="y", padx=(PAD, 8), pady=PAD)
        left.pack_propagate(False)

        # 标题
        tk.Label(left, text="Cover Maker", bg=BG, fg=ACC,
                 font=("SF Pro Display", 18, "bold")).pack(anchor="w", pady=(0, 20))

        # 图片选择
        tk.Label(left, text="图片", bg=BG, fg=FG, font=FONT_LBL).pack(anchor="w")
        img_row = tk.Frame(left, bg=BG)
        img_row.pack(fill="x", pady=(4, 12))
        self._img_entry = tk.Entry(img_row, textvariable=self.img_path,
                                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                                   relief="flat", font=FONT_LBL, width=22)
        self._img_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))
        tk.Button(img_row, text="选择", command=self._pick_image,
                  bg="#3a3a3a", fg=FG, relief="flat", font=FONT_LBL,
                  activebackground="#4a4a4a", cursor="hand2",
                  padx=10).pack(side="left")

        # 标题输入
        tk.Label(left, text="标题", bg=BG, fg=FG, font=FONT_LBL).pack(anchor="w")
        title_frame = tk.Frame(left, bg=ENTRY_BG, highlightbackground="#444",
                               highlightthickness=1)
        title_frame.pack(fill="x", pady=(4, 12))
        self._title_entry = tk.Text(title_frame, height=3, wrap="word",
                                    bg=ENTRY_BG, fg=FG, insertbackground=FG,
                                    relief="flat", font=FONT_LBL,
                                    padx=8, pady=6)
        self._title_entry.pack(fill="x")
        self._title_entry.bind("<KeyRelease>", lambda e: self._schedule_preview())

        # 颜色选择
        tk.Label(left, text="背景颜色", bg=BG, fg=FG, font=FONT_LBL).pack(anchor="w")
        color_grid = tk.Frame(left, bg=BG)
        color_grid.pack(fill="x", pady=(4, 12))
        self._color_btns = {}
        for i, (label, key) in enumerate(COLOR_OPTIONS):
            hex_c = PRESETS[key]
            btn = tk.Button(color_grid, text="", width=3, height=1,
                            bg=hex_c, relief="flat", cursor="hand2",
                            command=lambda k=key: self._select_color(k))
            btn.grid(row=i // 4, column=i % 4, padx=3, pady=3, sticky="w")
            self._color_btns[key] = btn

        # 颜色标签行
        self._color_label = tk.Label(left, text="", bg=BG, fg="#aaa", font=FONT_LBL)
        self._color_label.pack(anchor="w", pady=(0, 4))

        # 自定义HEX
        hex_row = tk.Frame(left, bg=BG)
        hex_row.pack(fill="x", pady=(0, 16))
        tk.Label(hex_row, text="自定义 #", bg=BG, fg="#aaa", font=FONT_LBL).pack(side="left")
        self._hex_entry = tk.Entry(hex_row, width=8,
                                   bg=ENTRY_BG, fg=FG, insertbackground=FG,
                                   relief="flat", font=FONT_LBL)
        self._hex_entry.pack(side="left", ipady=5, padx=(2, 6))
        tk.Button(hex_row, text="应用", command=self._apply_hex,
                  bg="#3a3a3a", fg=FG, relief="flat", font=FONT_LBL,
                  activebackground="#4a4a4a", cursor="hand2",
                  padx=8).pack(side="left")

        # 生成按钮
        self._gen_btn = tk.Button(left, text="生成封面", command=self._generate,
                                  bg=ACC, fg="white", relief="flat",
                                  font=FONT_BTN, cursor="hand2",
                                  activebackground="#3a7f90", pady=10)
        self._gen_btn.pack(fill="x", pady=(4, 8))

        # 打开文件按钮
        self._open_btn = tk.Button(left, text="在 Finder 中显示",
                                   command=self._reveal_in_finder,
                                   bg="#2d2d2d", fg="#aaa", relief="flat",
                                   font=FONT_LBL, cursor="hand2",
                                   activebackground="#3a3a3a", pady=6,
                                   state="disabled")
        self._open_btn.pack(fill="x")

        # 状态栏
        self._status = tk.Label(left, text="拖入图片或点击选择", bg=BG,
                                fg="#777", font=("SF Pro Display", 11),
                                wraplength=270, justify="left")
        self._status.pack(anchor="w", pady=(12, 0))

        # ── 右列：预览区 ──────────────────────────────
        right = tk.Frame(self, bg="#141414")
        right.pack(side="left", fill="both", expand=True, padx=(0, PAD), pady=PAD)

        self._canvas = tk.Canvas(right, width=PREVIEW_W, height=PREVIEW_H,
                                 bg="#141414", highlightthickness=0)
        self._canvas.pack(expand=True)
        self._canvas.create_text(PREVIEW_W // 2, PREVIEW_H // 2,
                                 text="预览区", fill="#444",
                                 font=("SF Pro Display", 14),
                                 tags="placeholder")

        # 拖拽支持
        self.drop_target_register = getattr(self, 'drop_target_register', None)
        self._setup_drag_drop()

    # ── 拖拽 ────────────────────────────────────────
    def _setup_drag_drop(self):
        """macOS 上通过 tkinterdnd2 支持拖拽，没装就跳过"""
        try:
            from tkinterdnd2 import DND_FILES, TkinterDnD
            self.drop_target_register(DND_FILES)
            self.dnd_bind('<<Drop>>', self._on_drop)
        except Exception:
            pass

    def _on_drop(self, event):
        path = event.data.strip().strip("{}")
        if os.path.isfile(path):
            self.img_path.set(path)
            self._schedule_preview()

    # ── 事件 ────────────────────────────────────────
    def _pick_image(self):
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("图片", "*.png *.jpg *.jpeg *.webp *.bmp"), ("所有", "*.*")]
        )
        if path:
            self.img_path.set(path)
            self._schedule_preview()

    def _select_color(self, key):
        self.color_key.set(key)
        self._update_color_swatch()
        self._schedule_preview()

    def _update_color_swatch(self):
        key = self.color_key.get()
        label = next((l for l, k in COLOR_OPTIONS if k == key), key)
        self._color_label.config(text=f"当前：{label}  {PRESETS.get(key, key)}")
        # 高亮选中的色块
        for k, btn in self._color_btns.items():
            btn.config(relief="solid" if k == key else "flat",
                       bd=2 if k == key else 0)

    def _apply_hex(self):
        val = self._hex_entry.get().strip().lstrip("#")
        if len(val) == 6:
            self.color_key.set("#" + val)
            self._color_label.config(text=f"当前：#{val}")
            for btn in self._color_btns.values():
                btn.config(relief="flat", bd=0)
            self._schedule_preview()

    # ── 预览（防抖，500ms后触发）───────────────────
    _preview_timer = None

    def _schedule_preview(self):
        if self._preview_timer:
            self.after_cancel(self._preview_timer)
        self._preview_timer = self.after(500, self._do_preview)

    def _do_preview(self):
        img_path = self.img_path.get().strip()
        title    = self._title_entry.get("1.0", "end").strip()
        color    = self.color_key.get()

        if not img_path or not os.path.isfile(img_path) or not title:
            return

        try:
            import tempfile
            tmp = tempfile.mktemp(suffix=".png")
            make_cover(img_path, title, color, output_path=tmp)
            img = Image.open(tmp)
            img.thumbnail((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
            self._preview_img = ImageTk.PhotoImage(img)
            self._canvas.delete("all")
            self._canvas.create_image(PREVIEW_W // 2, PREVIEW_H // 2,
                                      anchor="center", image=self._preview_img)
            os.unlink(tmp)
        except Exception as e:
            self._set_status(f"预览失败：{e}", error=True)

    # ── 生成 ─────────────────────────────────────────
    def _generate(self):
        img_path = self.img_path.get().strip()
        title    = self._title_entry.get("1.0", "end").strip()
        color    = self.color_key.get()

        if not img_path or not os.path.isfile(img_path):
            messagebox.showerror("错误", "请先选择图片")
            return
        if not title:
            messagebox.showerror("错误", "请输入标题")
            return

        self._gen_btn.config(state="disabled", text="生成中…")
        self._set_status("正在生成…")

        def run():
            try:
                out = make_cover(img_path, title, color)
                self.output_path = out
                self.after(0, self._on_done, out)
            except Exception as e:
                self.after(0, self._set_status, f"失败：{e}", True)
                self.after(0, lambda: self._gen_btn.config(state="normal", text="生成封面"))

        threading.Thread(target=run, daemon=True).start()

    def _on_done(self, out):
        self._gen_btn.config(state="normal", text="生成封面")
        self._open_btn.config(state="normal")
        self._set_status(f"✓ 已保存：{os.path.basename(out)}")
        # 更新预览为最终输出
        try:
            img = Image.open(out)
            img.thumbnail((PREVIEW_W, PREVIEW_H), Image.LANCZOS)
            self._preview_img = ImageTk.PhotoImage(img)
            self._canvas.delete("all")
            self._canvas.create_image(PREVIEW_W // 2, PREVIEW_H // 2,
                                      anchor="center", image=self._preview_img)
        except Exception:
            pass

    def _reveal_in_finder(self):
        if self.output_path and os.path.exists(self.output_path):
            os.system(f'open -R "{self.output_path}"')

    def _set_status(self, msg, error=False):
        self._status.config(text=msg, fg="#e05555" if error else "#aaa")


if __name__ == "__main__":
    app = App()
    app.mainloop()
