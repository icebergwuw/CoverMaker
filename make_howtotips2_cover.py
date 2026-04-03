#!/usr/bin/env python3
"""
make_howtotips2_cover.py — 生成 HowToTips v2 封面
斜线装饰直接从 Figma SVG 路径数据绘制（aggdraw bezier），精确还原。
输出尺寸 1520x992（Figma 原稿 380x248 × 4，比例完全一致）。
"""

import os
import aggdraw
from PIL import Image, ImageDraw, ImageFont

# ── Figma 原稿尺寸 & 放大倍数 ────────────────────────────
FW, FH = 380, 248
SCALE  = 4

# ── 输出尺寸 ─────────────────────────────────────────────
W, H = FW * SCALE, FH * SCALE   # 1520 x 992

SX = SCALE   # x 方向放大倍数
SY = SCALE   # y 方向放大倍数（等比，不变形）

# ── SVG 路径数据（来自 Figma，380x248 坐标系）─────────────
# 粗线（stroke-width 24）和细线（stroke-width 0.5）共用同一形状，略有偏移
SWIRL_PATH_THICK = (
    "M231.451 1.548 C155.18 50.657 124.384 96.262 173.651 80.786 "
    "C222.918 65.311 419.936 -102.446 330.97 -1.311 "
    "C242.004 99.825 70.159 246.621 182.668 164.754 "
    "C295.177 82.886 531.52 -128.074 392.098 35.564 "
    "C252.676 199.202 4.984 322.033 167.272 248.379 "
    "C329.561 174.725 415.668 113.18 376.903 169.703"
)
SWIRL_PATH_THIN = (
    "M207.278 12.514 C131.012 61.606 100.222 107.203 149.488 91.738 "
    "C198.755 76.273 395.755 -91.439 306.801 9.675 "
    "C217.848 110.789 46.019 257.546 158.519 175.704 "
    "C271.02 93.862 507.34 -117.044 367.938 46.560 "
    "C228.537 210.164 -19.148 332.942 143.137 259.323 "
    "C305.421 185.704 391.522 124.178 352.765 180.691"
)

# ── 布局参数（Figma 原稿坐标，运行时 × SCALE）────────────
# 米白框（#F9EFEA）：x=158, y=58, w=210, h=133
# 图片内容：x=162, y=63, w=201, h=123（内缩4px）
_IMG_BORDER_X = 158
_IMG_BORDER_Y = 58
_IMG_BORDER_W = 210
_IMG_BORDER_H = 133

_IMG_X = 162
_IMG_Y = 63
_IMG_W = 201
_IMG_H = 123

IMG_BORDER_X = _IMG_BORDER_X * SCALE
IMG_BORDER_Y = _IMG_BORDER_Y * SCALE
IMG_BORDER_W = _IMG_BORDER_W * SCALE
IMG_BORDER_H = _IMG_BORDER_H * SCALE

IMG_X = _IMG_X * SCALE
IMG_Y = _IMG_Y * SCALE
IMG_W = _IMG_W * SCALE
IMG_H = _IMG_H * SCALE

# 文字区域：x从20开始，右边界到158，垂直居中整个画面
TEXT_X     = 20  * SCALE
TEXT_Y_TOP = 20  * SCALE
TEXT_MAX_W = 132 * SCALE   # 158-20-6(margin) = 132



FONT_SIZE_MAX = int(H * 0.14)   # ≈138px，与原稿字号比例一致
FONT_SIZE_MIN = int(H * 0.03)
FONT_PATH     = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Bold.ttf")

LINE_SPACING_RATIO = 0.40

# ── 5 套 Figma 模板（颜色直接来自 SVG 源文件）────────────
# 格式：(显示名称, 背景色, 粗线色, 粗线opacity, 细线色, 细线opacity, 文字色)
TEMPLATES = {
    "mint":   ("薄荷绿", "#D5FFEC", "#16724E", 1.0, "#222222", 1.0,  "#222222"),
    "warm":   ("暖黄",   "#FFBE4C", "#F16E3D", 1.0, "#000000", 1.0,  "#5A1E08"),
    "orange": ("橙黄",   "#FFD272", "#F16E3D", 0.8, "#222222", 1.0,  "#222222"),
    "teal":   ("青绿",   "#84DCD4", "#003ACD", 1.0, "#222222", 1.0,  "#222222"),
    "pink":   ("粉色",   "#FFC0E5", "#EA4B3D", 0.8, "#FF8C84", 1.0,  "#222222"),
}
DEFAULT_TEMPLATE = "teal"


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def hex_to_rgba(h, opacity=1.0):
    r, g, b = hex_to_rgb(h)
    a = int(opacity * 255)
    return (r, g, b, a)


def cover_crop(img, target_w, target_h):
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


def scale_svg_path(path_str, sx, sy):
    """
    将 SVG path 中所有数字坐标按 sx/sy 缩放。
    支持 M, C 指令（够用了，路径只有这两种）。
    """
    import re
    def scale_pair(m):
        x, y = float(m.group(1)), float(m.group(2))
        return f"{x * sx:.2f} {y * sy:.2f}"
    return re.sub(r'(-?[\d.]+)\s+(-?[\d.]+)', scale_pair, path_str)


def draw_swirl(canvas: Image.Image,
               thick_hex, thick_opacity,
               thin_hex,  thin_opacity):
    """
    在画布上用 aggdraw 绘制两条贝塞尔曲线装饰。
    路径坐标已按 SX/SY 放大到 1200×630。
    """
    # 放大路径
    path_thick = scale_svg_path(SWIRL_PATH_THICK, SX, SY)
    path_thin  = scale_svg_path(SWIRL_PATH_THIN,  SX, SY)

    thick_rgba = hex_to_rgba(thick_hex, thick_opacity)
    thin_rgba  = hex_to_rgba(thin_hex,  thin_opacity)

    # aggdraw 在 RGBA 模式画布上工作
    agg = aggdraw.Draw(canvas)
    agg.setantialias(True)

    # 粗线（原 24px → 放大后约 24 * (SX+SY)/2 ≈ 70px）
    thick_w = 24 * (SX + SY) / 2
    pen_thick = aggdraw.Pen(thick_rgba[:3], thick_w, thick_rgba[3])
    sym_thick = aggdraw.Symbol(path_thick)
    agg.symbol((0, 0), sym_thick, pen_thick)

    # 细线（原 0.5px → 放大后约 1.4px）
    thin_w = max(0.5 * (SX + SY) / 2, 1.0)
    pen_thin = aggdraw.Pen(thin_rgba[:3], thin_w, thin_rgba[3])
    sym_thin = aggdraw.Symbol(path_thin)
    agg.symbol((0, 0), sym_thin, pen_thin)

    agg.flush()


def _wrap(words, font, max_width):
    lines, current = [], ""
    for word in words:
        test = (current + " " + word).strip()
        if font.getlength(test) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def fit_text(text, max_width):
    words = text.split()
    wc = len(words)
    if wc <= 3:   size_max = int(H * 0.14)
    elif wc <= 4: size_max = int(H * 0.12)
    elif wc <= 6: size_max = int(H * 0.10)
    elif wc <= 8: size_max = int(H * 0.09)
    else:         size_max = int(H * 0.08)

    for size in range(size_max, FONT_SIZE_MIN - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = _wrap(words, font, max_width)
        if not lines:
            continue
        if all(font.getlength(l) <= max_width for l in lines):
            return font, lines

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE_MIN)
    return font, _wrap(words, font, max_width)


def make_howtotips2_cover(img_path, title, template=DEFAULT_TEMPLATE, output_path=None):
    """
    img_path   — 右侧配图
    title      — 封面标题
    template   — mint / warm / orange / teal / pink
    """
    if template not in TEMPLATES:
        template = DEFAULT_TEMPLATE
    _name, bg_hex, thick_hex, thick_op, thin_hex, thin_op, text_hex = TEMPLATES[template]

    bg_rgb   = hex_to_rgb(bg_hex)
    text_rgb = hex_to_rgb(text_hex)

    # ── 画布（RGBA，方便 aggdraw 混合）──────────────────
    canvas = Image.new("RGBA", (W, H), bg_rgb + (255,))

    # ── 斜线装饰 ─────────────────────────────────────────
    draw_swirl(canvas, thick_hex, thick_op, thin_hex, thin_op)

    # ── 右侧图片 ─────────────────────────────────────────
    src = Image.open(img_path).convert("RGB")
    photo = cover_crop(src, IMG_W, IMG_H)

    # 米白色外框
    border_rect = Image.new("RGB", (IMG_BORDER_W, IMG_BORDER_H), (249, 239, 234))
    canvas.paste(border_rect, (IMG_BORDER_X, IMG_BORDER_Y))
    canvas.paste(photo, (IMG_X, IMG_Y))
    canvas.paste(photo, (IMG_X, IMG_Y))

    # ── 文字（垂直居中于整个画面）──────────────────────
    draw = ImageDraw.Draw(canvas)

    font, lines = fit_text(title, TEXT_MAX_W)
    line_spacing = int(font.size * LINE_SPACING_RATIO)
    sample_bbox  = draw.textbbox((0, 0), lines[0], font=font)
    line_h       = sample_bbox[3] - sample_bbox[1]
    top_offset   = sample_bbox[1]
    total_text_h = line_h * len(lines) + line_spacing * (len(lines) - 1)
    y = (H - total_text_h) // 2 - top_offset

    for line in lines:
        draw.text((TEXT_X, y), line, font=font, fill=text_rgb)
        y += line_h + line_spacing

    # ── 输出 ─────────────────────────────────────────────
    if output_path is None:
        base, _ = os.path.splitext(img_path)
        output_path = base + "_ht2_cover.png"

    canvas.convert("RGB").save(output_path, "PNG")
    print(f"✓ 已保存：{output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python3 make_howtotips2_cover.py <图片路径> \"<标题>\" [模板]")
        print("模板: mint / warm / orange / teal / pink")
        sys.exit(1)
    make_howtotips2_cover(sys.argv[1], sys.argv[2],
                          sys.argv[3] if len(sys.argv) > 3 else DEFAULT_TEMPLATE)
