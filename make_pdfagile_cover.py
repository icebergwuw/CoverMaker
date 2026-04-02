#!/usr/bin/env python3
"""
make_pdfagile_cover.py — 生成 PDF Agile 模板封面图（1200×630）
用法：python3 make_pdfagile_cover.py <预览图路径> "<标题文字>" [输出路径]
"""

import sys, os
from PIL import Image, ImageDraw, ImageFont

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
FONT_PATH  = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts", "Montserrat-Bold.ttf")

W, H = 1200, 630

# Figma 实测坐标（1x）
PREVIEW_MAX_W, PREVIEW_MAX_H = 560, 400 # 预览图最大尺寸（更大）
PREVIEW_X, PREVIEW_Y       = 55, 108    # 预览图左上角
PREVIEW_ROTATE             = 0.0        # 不旋转

# 文案区：右半边黑色区域内
TEXT_X                     = 710
TEXT_PADDING_R             = 50
TEXT_MAX_W                 = W - TEXT_X - TEXT_PADDING_R  # 465
TEXT_MAX_H                 = 280

LOGO_X, LOGO_Y             = 951, 556
LOGO_W, LOGO_H             = 218, 50

BLACK_X, BLACK_Y, BLACK_S  = 600, -168, 1009

FONT_SIZE_MAX = 48
FONT_SIZE_MIN = 20


def _wrap(text, font, max_w):
    words = text.split()
    lines, cur = [], ""
    for w in words:
        test = (cur + " " + w).strip()
        if font.getlength(test) <= max_w:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def fit_text(text, max_w, max_h):
    dummy = ImageDraw.Draw(Image.new("RGB", (1, 1)))
    for size in range(FONT_SIZE_MAX, FONT_SIZE_MIN - 1, -2):
        font = ImageFont.truetype(FONT_PATH, size)
        lines = _wrap(text, font, max_w)
        if not lines:
            continue
        if not all(font.getlength(l) <= max_w for l in lines):
            continue
        sb = dummy.textbbox((0, 0), lines[0], font=font)
        lh = sb[3] - sb[1]
        sp = int(size * 0.2)
        total_h = lh * len(lines) + sp * (len(lines) - 1)
        if total_h <= max_h:
            return font, lines
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE_MIN)
    return font, _wrap(text, font, max_w)


def _drop_shadow(img, offset_y=6, blur=30, color=(225, 182, 182)):
    """给图片加底部 drop shadow，返回带阴影的新图（尺寸略大）"""
    import math
    pad = blur * 2
    w, h = img.size
    shadow_img = Image.new("RGBA", (w + pad * 2, h + pad * 2), (0, 0, 0, 0))
    # 阴影色块（用图片的alpha mask）
    shadow_color = Image.new("RGBA", (w, h), (*color, 255))
    mask = img.split()[3] if img.mode == "RGBA" else None
    shadow_img.paste(shadow_color, (pad, pad + offset_y), mask)
    # 模糊
    from PIL.ImageFilter import GaussianBlur
    shadow_img = shadow_img.filter(GaussianBlur(radius=blur // 3))
    # 合成原图
    shadow_img.paste(img, (pad, pad), img if img.mode == "RGBA" else None)
    return shadow_img, pad


def make_pdfagile_cover(preview_path, title, output_path=None):
    canvas = Image.new("RGBA", (W, H), (255, 248, 252, 255))

    # 1. 背景装饰层
    bg = Image.open(os.path.join(ASSETS_DIR, "pdfagile_bg.png")).convert("RGBA")
    bg = bg.resize((W, H), Image.LANCZOS)
    canvas.alpha_composite(bg)

    # 2. 黑底（负坐标裁剪处理）
    black = Image.open(os.path.join(ASSETS_DIR, "pdfagile_black.png")).convert("RGBA")
    black = black.resize((BLACK_S, BLACK_S), Image.LANCZOS)
    src_x = max(0, -BLACK_X)
    src_y = max(0, -BLACK_Y)
    dst_x = max(0, BLACK_X)
    dst_y = max(0, BLACK_Y)
    crop_w = min(BLACK_S - src_x, W - dst_x)
    crop_h = min(BLACK_S - src_y, H - dst_y)
    black_crop = black.crop((src_x, src_y, src_x + crop_w, src_y + crop_h))
    canvas.alpha_composite(black_crop, (dst_x, dst_y))

    draw = ImageDraw.Draw(canvas)

    # 3. 预览图（左半边垂直居中，轻微旋转，带 drop shadow）
    if preview_path and os.path.exists(preview_path):
        prev = Image.open(preview_path).convert("RGBA")
        pw, ph = prev.size
        scale = min(PREVIEW_MAX_W / pw, PREVIEW_MAX_H / ph)
        nw, nh = int(pw * scale), int(ph * scale)
        prev = prev.resize((nw, nh), Image.LANCZOS)

        # 轻微旋转（expand=True 防止裁切）
        rotated = prev.rotate(-PREVIEW_ROTATE, expand=True, resample=Image.BICUBIC)

        # 加阴影
        shadowed, pad = _drop_shadow(rotated, offset_y=6, blur=30, color=(225, 182, 182))

        # 垂直居中：shadowed 比原图大 pad*2，paste 时左上角要减 pad
        # 让原图（在 shadowed 内偏移 pad）垂直居中于画布
        py = (H - shadowed.size[1]) // 2  # shadowed 整体居中
        canvas.alpha_composite(shadowed, (PREVIEW_X - pad, py))

    # 4. 文案（右半边黑色区域内垂直居中，白色 Montserrat Bold）
    font, lines = fit_text(title, TEXT_MAX_W, TEXT_MAX_H)
    sb = draw.textbbox((0, 0), lines[0], font=font)
    lh = sb[3] - sb[1]
    top_off = sb[1]
    sp = int(font.size * 0.22)
    total_h = lh * len(lines) + sp * (len(lines) - 1)
    # 垂直居中于画布（黑底覆盖整个右侧高度）
    y = (H - total_h) // 2 - top_off
    for line in lines:
        draw.text((TEXT_X, y), line, font=font, fill=(255, 255, 255, 255))
        y += lh + sp

    # 5. Logo（右下角）
    logo = Image.open(os.path.join(ASSETS_DIR, "pdfagile_logo.png")).convert("RGBA")
    logo = logo.resize((LOGO_W, LOGO_H), Image.LANCZOS)
    canvas.alpha_composite(logo, (LOGO_X, LOGO_Y))

    # 6. 输出
    result = canvas.convert("RGB")
    if output_path is None:
        base = os.path.splitext(preview_path)[0] if preview_path else "pdfagile"
        output_path = base + "_cover.png"
    result.save(output_path, "PNG")
    print(f"✓ 已保存：{output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    make_pdfagile_cover(sys.argv[1], sys.argv[2],
                        sys.argv[3] if len(sys.argv) > 3 else None)
