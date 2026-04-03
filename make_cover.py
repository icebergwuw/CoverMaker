#!/usr/bin/env python3
"""
make_cover.py — 生成教程封面图
用法：python3 make_cover.py <图片路径> "<标题>" [颜色名或HEX]

颜色预设：
  teal   → #4A8FA0（蓝绿，默认）
  tan    → #C4A882（米棕）
  navy   → #2C4A6E（深蓝）
  olive  → #7A8C5E（橄榄绿）
  rose   → #B5737A（玫瑰红）
  或直接传 HEX，如 #3D7A8A

输出：与输入图片同目录，文件名加 _cover 后缀
"""

import sys
import os
from PIL import Image, ImageDraw, ImageFont

# ── 固定尺寸 ──────────────────────────────────────────────
TOTAL_W   = 1130
TOTAL_H   = 860
LEFT_W    = 654   # 原图比例 660/1140 ≈ 57.9%
RIGHT_W   = TOTAL_W - LEFT_W  # 476

# ── 右侧装饰参数 ─────────────────────────────────────────
LINE_W    = 4    # 白线宽度(px)
LINE_H    = 80   # 白线高度(px)
LINE_GAP  = 28   # 线与文字块的间距(px)

TEXT_MARGIN    = 40     # 文字距右侧边缘内边距
FONT_SIZE_MAX  = 65
FONT_SIZE_MIN  = 25
FONT_PATH      = os.path.join(os.path.dirname(__file__), "fonts", "Montserrat-Bold.ttf")

# ── 颜色预设 ─────────────────────────────────────────────
PRESETS = {
    "teal":  "#4A8FA0",
    "tan":   "#C4A882",
    "navy":  "#2C4A6E",
    "olive": "#7A8C5E",
    "rose":  "#B5737A",
    "slate": "#5E7A8C",
    "warm":  "#B07850",
}

def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def cover_crop(img, target_w, target_h):
    """object-fit: cover — 等比缩放后从左侧裁剪（保留左边内容）"""
    src_w, src_h = img.size
    scale = max(target_w / src_w, target_h / src_h)
    new_w = int(src_w * scale)
    new_h = int(src_h * scale)
    img = img.resize((new_w, new_h), Image.LANCZOS)
    left = (new_w - target_w) // 2  # 居中裁
    top  = (new_h - target_h) // 2
    return img.crop((left, top, left + target_w, top + target_h))

def _wrap(words, font, max_width):
    """贪心分行，返回 lines 列表"""
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

def fit_text(draw, text, max_width, font_path, size_max, size_min):
    """自动换行 + 自动缩小字号，避免孤行，返回 (font, lines)"""
    words = text.split()
    for size in range(size_max, size_min - 1, -2):
        font = ImageFont.truetype(font_path, size)
        lines = _wrap(words, font, max_width)
        if not lines:
            continue
        # 所有行都不超宽才算合法
        if not all(font.getlength(l) <= max_width for l in lines):
            continue
        # 消除孤行（单词行）：把1词的行尝试合并到上一行或下一行
        # 用更小字号重试
        has_orphan = any(len(l.split()) == 1 and l != lines[-1] for l in lines[:-1])
        if has_orphan:
            # 尝试用小2号字体能否消除孤行
            for s2 in range(size - 2, size_min - 1, -2):
                f2 = ImageFont.truetype(font_path, s2)
                l2 = _wrap(words, f2, max_width)
                if not l2:
                    continue
                if not all(f2.getlength(l) <= max_width for l in l2):
                    continue
                orphan2 = any(len(l.split()) == 1 and l != l2[-1] for l in l2[:-1])
                if not orphan2:
                    return f2, l2
            # 找不到更好的就接受原来的
        return font, lines
    # 保底
    font = ImageFont.truetype(font_path, size_min)
    return font, _wrap(words, font, max_width)

def make_cover(img_path, title, color_key="teal", output_path=None, line_spacing_ratio=0.40):
    # 解析颜色
    if color_key.startswith("#"):
        bg_color = hex_to_rgb(color_key)
    else:
        bg_color = hex_to_rgb(PRESETS.get(color_key.lower(), PRESETS["teal"]))

    # 载入并裁剪左侧图
    src = Image.open(img_path).convert("RGB")
    left_img = cover_crop(src, LEFT_W, TOTAL_H)

    # 创建画布
    canvas = Image.new("RGB", (TOTAL_W, TOTAL_H), bg_color)
    canvas.paste(left_img, (0, 0))

    draw = ImageDraw.Draw(canvas)

    # ── 右侧标题文字（先算坐标，再画线）─────────────────
    text_area_w = RIGHT_W - TEXT_MARGIN * 2

    # 根据字数动态调整最大字号：字越多上限越小，避免长文字超出版面
    word_count = len(title.split())
    if word_count <= 4:
        dynamic_max = FONT_SIZE_MAX       # 65，字少可以大
    elif word_count <= 6:
        dynamic_max = 58
    elif word_count <= 9:
        dynamic_max = 50
    else:
        dynamic_max = 42

    font, lines = fit_text(draw, title, text_area_w, FONT_PATH,
                           dynamic_max, FONT_SIZE_MIN)

    line_spacing = int(font.size * line_spacing_ratio)
    sample_bbox = draw.textbbox((0, 0), lines[0], font=font)
    line_h = sample_bbox[3] - sample_bbox[1]
    top_offset = sample_bbox[1]
    total_text_h = line_h * len(lines) + line_spacing * (len(lines) - 1)

    # 整体内容块 = 文字块，垂直居中
    LINE_GAP  = 30   # 线与文字之间的间距
    block_top = (TOTAL_H - total_text_h) // 2

    # 竖线位置
    line_x = LEFT_W + (RIGHT_W - LINE_W) // 2
    top_line_top = 0
    top_line_bot = block_top - LINE_GAP
    bot_line_top = block_top + total_text_h + LINE_GAP
    bot_line_bot = TOTAL_H

    # 上线：从顶部到文字上方
    draw.rectangle([line_x, top_line_top, line_x + LINE_W, top_line_bot],
                   fill=(255, 255, 255))
    # 下线：从文字下方到底部
    draw.rectangle([line_x, bot_line_top, line_x + LINE_W, bot_line_bot],
                   fill=(255, 255, 255))

    # 文字起始 y（垂直居中，补偿 top_offset）
    y = block_top - top_offset

    # ── 渲染文字 ─────────────────────────────────────────
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        line_w = bbox[2] - bbox[0]
        x = LEFT_W + (RIGHT_W - line_w) // 2
        draw.text((x, y), line, font=font, fill=(255, 255, 255))
        y += line_h + line_spacing

    # ── 输出 ─────────────────────────────────────────────
    if output_path is None:
        base, ext = os.path.splitext(img_path)
        output_path = base + "_cover.png"

    canvas.save(output_path, "PNG")
    print(f"✓ 已保存：{output_path}")
    return output_path

# ── CLI 入口 ─────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    img_path  = sys.argv[1]
    title     = sys.argv[2]
    color_key = sys.argv[3] if len(sys.argv) > 3 else "teal"

    if not os.path.exists(img_path):
        print(f"错误：找不到图片 {img_path}")
        sys.exit(1)

    make_cover(img_path, title, color_key)
