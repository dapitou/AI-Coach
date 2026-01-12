import sys
import os

# 路径防御：确保能找到 core
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import cv2
try:
    from core.config import ColorConfig
except ImportError:
    # 兜底
    print(f"Error: Could not import 'core'. Added path: {project_root}")
    raise

class SkeletonRenderer:
    def __init__(self):
        # [UI回滚 & 优化] 定义骨骼连接关系
        self.bones = [
            # 1. 头部 (优化：只连颈部)
            ('nose', 'neck'),
            
            # 2. 手臂 (通过颈部连接)
            ('neck', 'ls'), ('neck', 'rs'),
            ('ls', 'le'), ('le', 'lw'),
            ('rs', 're'), ('re', 'rw'),
            
            # 3. [关键修复] 脊柱中轴 (找回丢失的脊柱线)
            ('neck', 'thorax'), 
            ('thorax', 'waist'), 
            ('waist', 'hip'),
            
            # 4. 腿部 (通过中心髋点连接)
            ('hip', 'lh'), ('hip', 'rh'),
            ('lh', 'lk'), ('lk', 'la'),
            ('rh', 'rk'), ('rk', 'ra')
        ]

    def draw(self, img, pts, is_avatar=False):
        """
        绘制骨骼连线和关键点
        """
        # [UI回滚] 恢复蓝色骨骼 (NEON_BLUE)
        line_color = ColorConfig.NEON_BLUE if not is_avatar else ColorConfig.NEON_YELLOW
        thickness = 2 if not is_avatar else 3

        # 1. 绘制连线
        for (k1, k2) in self.bones:
            if k1 in pts and k2 in pts:
                p1 = pts[k1]
                p2 = pts[k2]
                # 过滤调试数据
                if isinstance(p1, (tuple, list)) and isinstance(p2, (tuple, list)):
                    cv2.line(img, p1, p2, line_color, thickness)

        # [UI回滚] 恢复黄色关节 (NEON_YELLOW)
        point_color = ColorConfig.NEON_YELLOW if not is_avatar else ColorConfig.NEON_GREEN
        radius = 5 if not is_avatar else 4
        
        # 特殊点颜色 (胸腰点用橙色区分)
        special_color = ColorConfig.NEON_ORANGE

        # 2. 绘制关节
        for k, p in pts.items():
            # 过滤非坐标数据 (debug_inc, debug_residual 等)
            if not isinstance(p, (tuple, list)): continue
            if len(p) != 2: continue
            
            if k in ['thorax', 'waist']:
                cv2.circle(img, p, 3, special_color, -1)
            else:
                cv2.circle(img, p, radius, point_color, -1)