"""
人体骨架渲染模块
负责绘制：骨骼连线、关节点、脊柱分析辅助线
"""
import cv2
from core.config import ColorConfig

class SkeletonRenderer:
    def draw(self, img, pts, is_avatar=False):
        """
        绘制骨架
        :param img: OpenCV 图像
        :param pts: 关键点字典
        :param is_avatar: 是否为右侧 Avatar (线条更粗)
        """
        if not pts: return

        # 1. 肢体连线
        limbs = [
            ('ls','le'),('le','lw'), # 左臂
            ('rs','re'),('re','rw'), # 右臂
            ('ls','lh'),('rs','rh'), # 躯干侧边
            ('lh','rh'),('ls','rs'), # 髋/肩连线
            ('lh','lk'),('lk','la'), # 左腿
            ('rh','rk'),('rk','ra')  # 右腿
        ]
        
        line_width = 4 if is_avatar else 2
        
        for u, v in limbs:
            if pts.get(u) and pts.get(v):
                cv2.line(img, pts[u], pts[v], ColorConfig.NEON_BLUE, line_width)
        
        # 2. 脊柱与核心区域 (如果有数据)
        if pts.get('waist') and pts.get('thorax') and pts.get('neck') and pts.get('hip'):
            # 变色逻辑：如果弓背(rounding_bad)则变红，否则紫色
            is_bad = pts.get('rounding_bad', False)
            col = ColorConfig.NEON_RED if is_bad else ColorConfig.NEON_PURPLE
            w = 3 if is_avatar else 2
            
            cv2.line(img, pts['neck'], pts['thorax'], col, w)
            cv2.line(img, pts['thorax'], pts['waist'], col, w)
            cv2.line(img, pts['waist'], pts['hip'], col, w)
            
            cv2.circle(img, pts['thorax'], 5, col, -1)
            cv2.circle(img, pts['waist'], 6, col, -1)

        # 3. 关键点圆圈
        for k, p in pts.items():
            # 排除非物理点或已特殊绘制的点
            # [FIX]: 排除新增的非坐标点 'side_bias' (浮点数) 和 'view_mode' (字符串)
            if p and k not in ['nose', 'neck', 'thorax', 'lumbar', 'waist', 'hip', 'spine_state', 'rounding_bad', 'side_bias', 'view_mode']:
                cv2.circle(img, p, 5, ColorConfig.NEON_YELLOW, -1)
                cv2.circle(img, p, 2, (255,255,255), -1)