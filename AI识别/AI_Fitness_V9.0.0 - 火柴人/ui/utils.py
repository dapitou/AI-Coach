"""
UI 基础工具模块
提供颜色转换、文本绘制、形状绘制等底层原子操作。
"""
import cv2
import numpy as np
from PIL import ImageDraw

def bgr2rgb(color):
    """将 BGR 颜色元组转换为 RGB (供 PIL 使用)"""
    return (int(color[2]), int(color[1]), int(color[0]))

def draw_box_with_alpha(img, rect, color, alpha=0.2):
    """
    绘制半透明矩形背景 (直接操作 OpenCV 图像)
    :param img: OpenCV 图像数组
    :param rect: (x1, y1, x2, y2)
    :param color: BGR 颜色元组
    :param alpha: 透明度
    """
    x1, y1, x2, y2 = map(int, rect)
    # 边界保护
    h, w = img.shape[:2]
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(w, x2), min(h, y2)
    
    if x2 <= x1 or y2 <= y1: return

    sub = img[y1:y2, x1:x2]
    # 创建纯色块
    overlay = np.full_like(sub, color, dtype=np.uint8)
    
    # 混合：原图 * (1-alpha) + 颜色块 * alpha
    cv2.addWeighted(sub, 1.0 - alpha, overlay, alpha, 0, sub)

def draw_text_shadow(draw, x, y, text, font, color):
    """绘制带黑色阴影的文本"""
    draw.text((x+2, y+2), text, font=font, fill=(0,0,0))
    draw.text((x, y), text, font=font, fill=bgr2rgb(color))

def draw_centered_text(draw, rect, text, font, color, shadow=True):
    """
    在矩形区域内绝对居中绘制文本 (水平+垂直)
    使用 anchor='mm' 实现精确对齐
    """
    cx = (rect[0] + rect[2]) // 2
    cy = (rect[1] + rect[3]) // 2
    rgb = bgr2rgb(color)
    
    if shadow:
        draw.text((cx+2, cy+2), text, font=font, fill=(0,0,0), anchor="mm")
    draw.text((cx, cy), text, font=font, fill=rgb, anchor="mm")