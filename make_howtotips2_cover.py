#!/usr/bin/env python3
"""
make_howtotips2_cover.py — 生成 HowToTips v2 封面（暖黄背景+斜线装饰，左文右图）
布局参考 Figma: Wu You's Sketch / Frame 1200x630
"""

import os
from PIL import Image, ImageDraw, ImageFont

# ── 固定尺寸 ──────────────────────────────────────────────
W, H = 1200, 630

# ── 布局参数（来自 Figma）────────────────────────────────
IMG_X, IMG_Y   = 542, 70    # 右侧图片区域左上角
IMG_W, IMG_H   = 620, 500   # 图片区域尺寸
IMG_BORDER     = 12         # 图片白色外框宽度

TEXT_X         = 66         # 标题起始 x
TEXT_Y_TOP     = 80         # 标题起始 y（最高）
TEXT_MAX_W     = 440        # 标题文字最大宽度（不超过图片左边缘）
TEXT_COLOR     = (90, 30, 7)   # #5a1e07 深棕

SUB_X          = 65
SUB_COLOR      = (90, 30, 7)
SUB_FONT_SIZE  = 30
SUB_TEXT       = "PDF Agile for Download"

LOGO_X, LOGO_Y = 30, 30

BG_COLORS = [
    "#ffbe4c",  # 暖橙黄（主色）
    "#ffd272",  # 浅金黄
    "#f5a623",  # 深橙
    "#ffe08a",  # 奶黄
    "#ffcf6b",  # 中黄
]

FONT_SIZE_MAX = 96
FONT_SIZE_MIN = 20
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Bold.ttf")
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")

LINE_SPACING_RATIO = 0.40


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def cover_crop(img, target_w, target_h):
    """object-fit: cover，居中裁剪"""
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))


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
    """自动换行+自动缩小字号，返回 (font, lines)"""
    words = text.split()
    word_count = len(words)

    # 动态最大字号（同 HowToTips 规则）
    if word_count <= 3:
        size_max = FONT_SIZE_MAX
    elif word_count <= 4:
        size_max = 72
    elif word_count <= 6:
        size_max = 64
    elif word_count <= 8:
        size_max = 60
    else:
        size_max = 50

    for size in range(size_max, FONT_SIZE_MIN - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = _wrap(words, font, max_width)
        if not lines:
            continue
        if not all(font.getlength(l) <= max_width for l in lines):
            continue
        return font, lines

    font = ImageFont.truetype(FONT_PATH, FONT_SIZE_MIN)
    return font, _wrap(words, font, max_width)


def make_howtotips2_cover(img_path, title, bg_color="#ffbe4c", output_path=None):
    bg_rgb = hex_to_rgb(bg_color)

    # ── 画布 ──────────────────────────────────────────────
    canvas = Image.new("RGB", (W, H), bg_rgb)

    # ── 背景斜线装饰 ──────────────────────────────────────
    swirl_path = os.path.join(ASSETS_DIR, "bg_swirl.png")
    if os.path.exists(swirl_path):
        swirl = Image.open(swirl_path).convert("RGBA")
        # Figma 中 swirl 起始 x=176（相对frame），宽约1265，高1027
        # 缩放到合适尺寸铺在右侧
        sw, sh = swirl.size   # 1115 x 1020
        scale = H / sh
        new_sw = int(sw * scale)
        swirl = swirl.resize((new_sw, H), Image.LANCZOS)
        # 贴在 x=176 处
        canvas.paste(swirl, (176, 0), swirl)

    # ── 右侧图片 ──────────────────────────────────────────
    src = Image.open(img_path).convert("RGB")
    photo = cover_crop(src, IMG_W, IMG_H)

    # 白色外框背景
    border_rect = Image.new("RGB", (IMG_W + IMG_BORDER * 2, IMG_H + IMG_BORDER * 2), (248, 238, 234))
    canvas.paste(border_rect, (IMG_X - IMG_BORDER, IMG_Y - IMG_BORDER))
    canvas.paste(photo, (IMG_X, IMG_Y))

    draw = ImageDraw.Draw(canvas)

    # ── 左侧主标题 ────────────────────────────────────────
    font, lines = fit_text(title, TEXT_MAX_W)
    line_spacing = int(font.size * LINE_SPACING_RATIO)

    # 计算文字块高度，垂直居中（在 TEXT_Y_TOP 到 IMG_Y+IMG_H 范围内）
    sample_bbox = draw.textbbox((0, 0), lines[0], font=font)
    line_h = sample_bbox[3] - sample_bbox[1]
    top_offset = sample_bbox[1]
    total_text_h = line_h * len(lines) + line_spacing * (len(lines) - 1)

    text_area_h = IMG_Y + IMG_H - TEXT_Y_TOP
    y = TEXT_Y_TOP + (text_area_h - total_text_h) // 2 - top_offset

    for line in lines:
        draw.text((TEXT_X, y), line, font=font, fill=TEXT_COLOR)
        y += line_h + line_spacing

    # ── 副标题 ────────────────────────────────────────────
    try:
        sub_font = ImageFont.truetype(FONT_PATH, SUB_FONT_SIZE)
    except IOError:
        sub_font = ImageFont.load_default()

    sub_y = H - 30 - SUB_FONT_SIZE
    draw.text((SUB_X, sub_y), SUB_TEXT, font=sub_font, fill=SUB_COLOR)

    # ── 输出 ──────────────────────────────────────────────
    if output_path is None:
        base, _ = os.path.splitext(img_path)
        output_path = base + "_ht2_cover.png"

    canvas.save(output_path, "PNG")
    print(f"✓ 已保存：{output_path}")
    return output_path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("用法: python3 make_howtotips2_cover.py <图片路径> \"<标题>\" [颜色HEX]")
        sys.exit(1)
    make_howtotips2_cover(sys.argv[1], sys.argv[2],
                          sys.argv[3] if len(sys.argv) > 3 else "#ffbe4c")
