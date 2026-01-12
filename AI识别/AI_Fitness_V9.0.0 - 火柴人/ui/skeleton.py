import sys
import os
import cv2
import numpy as np
import math
import json
from PIL import Image, ImageOps

# =========================================================================
# 路径防御
# =========================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from core.config import ColorConfig
except ImportError:
    class ColorConfig:
        NEON_BLUE = (255, 200, 0)
        NEON_YELLOW = (0, 255, 255)
        NEON_ORANGE = (0, 165, 255)

# =========================================================================
# 配置读取
# =========================================================================
DEFAULT_SPRITE_CONFIG = {} 

def load_sprite_config():
    config_path = os.path.join(project_root, 'assets', 'body_config.json')
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"[Skeleton] JSON load failed: {e}")
    return {}

# =========================================================================
# 映射关系
# =========================================================================
SYMMETRY_MAP = {
    'head':      ('neck', 'nose', 'neck', 'nose'),
    'torso':     ('neck', 'mid_hip', 'neck', 'mid_hip'),
    'upper_arm': ('rs', 're', 'ls', 'le'),
    'lower_arm': ('re', 'rw', 'le', 'lw'),
    'upper_leg': ('rh', 'rk', 'lh', 'lk'),
    'lower_leg': ('rk', 'ra', 'lk', 'la')
}

class SmartBodySprite:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.original_image = self._load_image(config['path'])
        
        if config.get('mirror_x'): 
            self.original_image = ImageOps.mirror(self.original_image)
        if config.get('mirror_y'): 
            self.original_image = ImageOps.flip(self.original_image)
            
        self.w, self.h = self.original_image.size

    def _load_image(self, path):
        full_path = os.path.join(project_root, 'assets', path)
        if os.path.exists(full_path):
            return Image.open(full_path).convert("RGBA")
        return Image.new('RGBA', (10, 10), (0,0,0,0))

    def get_render_data(self, start_pt, end_pt, global_scale, is_left_side):
        # 1. 镜像处理
        img_to_process = self.original_image
        if is_left_side:
            img_to_process = ImageOps.mirror(img_to_process)

        # 2. UV 坐标
        pu, pv = self.config['pivot']
        eu, ev = self.config['end']

        if is_left_side:
            cur_pu, cur_pv = (1.0 - pu), pv
            cur_eu, cur_ev = (1.0 - eu), ev
        else:
            cur_pu, cur_pv = pu, pv
            cur_eu, cur_ev = eu, ev

        # 3. 向量计算
        # 确保输入是 numpy array
        start_vec = np.array(start_pt)
        end_vec = np.array(end_pt)
        
        screen_vec = end_vec - start_vec
        screen_len = np.linalg.norm(screen_vec)
        if screen_len < 1.0: return None, (0,0)
        bone_angle = math.degrees(math.atan2(screen_vec[1], screen_vec[0]))

        img_vec_x = (cur_eu - cur_pu) * self.w
        img_vec_y = (cur_ev - cur_pv) * self.h
        img_len = math.sqrt(img_vec_x**2 + img_vec_y**2)
        if img_len < 1.0: return None, (0,0)
        img_angle = math.degrees(math.atan2(img_vec_y, img_vec_x))

        # 4. 缩放计算
        def_w, def_h = self.config['default_size']
        
        # 基础宽度缩放
        scale_w_ratio = def_w / self.w
        target_w = int(self.w * scale_w_ratio * global_scale)
        
        # 高度缩放策略
        if self.name == 'head':
            # 头部：锁定长宽比
            target_h = int(self.h * scale_w_ratio * global_scale)
        else:
            # 其他：基于骨骼长度拉伸
            scale_len_ratio = screen_len / img_len
            target_h = int(self.h * scale_len_ratio)

        if target_w < 1 or target_h < 1: return None, (0,0)

        # 5. 变换
        resized = img_to_process.resize((target_w, target_h), Image.LANCZOS)
        
        final_angle = img_angle - bone_angle
        rotated = resized.rotate(final_angle, resample=Image.BICUBIC, expand=True)

        # 6. 对齐
        new_pivot_x = cur_pu * target_w
        new_pivot_y = cur_pv * target_h
        
        cx, cy = target_w / 2.0, target_h / 2.0
        
        rad = math.radians(final_angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        
        px = new_pivot_x - cx
        py = new_pivot_y - cy
        
        rot_px = px * cos_a + py * sin_a
        rot_py = -px * sin_a + py * cos_a
        
        rcx, rcy = rotated.width / 2.0, rotated.height / 2.0
        final_pivot_x = rcx + rot_px
        final_pivot_y = rcy + rot_py
        
        paste_x = int(start_pt[0] - final_pivot_x)
        paste_y = int(start_pt[1] - final_pivot_y)

        return rotated, (paste_x, paste_y)


class SkeletonRenderer:
    def __init__(self):
        self.bones = [
            ('nose', 'neck'), ('neck', 'ls'), ('neck', 'rs'),
            ('ls', 'le'), ('le', 'lw'), ('rs', 're'), ('re', 'rw'),
            ('neck', 'thorax'), ('thorax', 'waist'), ('waist', 'hip'),
            ('hip', 'lh'), ('hip', 'rh'), ('lh', 'lk'), ('lk', 'la'),
            ('rh', 'rk'), ('rk', 'ra')
        ]
        self.sprites = {}
        self.reload_assets()

    def reload_assets(self):
        config = load_sprite_config()
        self.sprites = {}
        self.sorted_parts = []
        
        for name, cfg in config.items():
            if isinstance(cfg.get('default_size'), list):
                cfg['default_size'] = tuple(cfg['default_size'])
            self.sprites[name] = SmartBodySprite(name, cfg)
            
        self.sorted_parts = sorted(config.keys(), key=lambda k: config[k].get('z_index', 0))

    def draw(self, img, pts, is_avatar=False):
        if is_avatar:
            self.draw_realistic_body(img, pts)
        self.draw_skeleton_overlay(img, pts, is_avatar)

    def draw_realistic_body(self, img, pts):
        if not pts: return
        
        # 计算 mid_hip
        # 确保参与计算的点都是坐标元组
        if 'lh' in pts and 'rh' in pts:
            lh = pts['lh']
            rh = pts['rh']
            if isinstance(lh, (list, tuple)) and isinstance(rh, (list, tuple)):
                pts['mid_hip'] = (int((lh[0] + rh[0]) / 2), int((lh[1] + rh[1]) / 2))
            else:
                return
        else: return

        # 全局缩放计算：使用“躯干长度”作为参考
        scale_factor = 1.0
        if 'neck' in pts and 'mid_hip' in pts:
            neck_pt = pts['neck']
            hip_pt = pts['mid_hip']
            
            if isinstance(neck_pt, (list, tuple)) and isinstance(hip_pt, (list, tuple)):
                torso_len = np.linalg.norm(np.array(neck_pt) - np.array(hip_pt))
                BASE_TORSO_LEN = 300.0 
                scale_factor = torso_len / BASE_TORSO_LEN
                scale_factor = np.clip(scale_factor, 0.2, 5.0)

        # 转换 OpenCV -> PIL
        pil_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGBA))
        
        # 渲染循环
        for name in self.sorted_parts:
            if name not in SYMMETRY_MAP: continue
            if name not in self.sprites: continue
            
            r_s, r_e, l_s, l_e = SYMMETRY_MAP[name]
            sprite = self.sprites[name]
            
            # Helper to check point validity
            def is_valid_pt(p): return isinstance(p, (list, tuple)) and len(p) >= 2

            # 右侧
            if r_s in pts and r_e in pts and is_valid_pt(pts[r_s]) and is_valid_pt(pts[r_e]):
                rotated, pos = sprite.get_render_data(pts[r_s], pts[r_e], scale_factor, False)
                if rotated: pil_img.alpha_composite(rotated, pos)
            
            # 左侧
            if l_s != r_s and l_s in pts and l_e in pts and is_valid_pt(pts[l_s]) and is_valid_pt(pts[l_e]):
                rotated, pos = sprite.get_render_data(pts[l_s], pts[l_e], scale_factor, True)
                if rotated: pil_img.alpha_composite(rotated, pos)

        # 转换回 OpenCV
        img[:] = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGR)

    def draw_skeleton_overlay(self, img, pts, is_avatar=False):
        if is_avatar: return 
        
        line_color = ColorConfig.NEON_BLUE
        
        # 绘制骨骼线
        for (k1, k2) in self.bones:
            if k1 in pts and k2 in pts:
                p1 = pts[k1]
                p2 = pts[k2]
                # 严格类型检查：必须是元组或列表，且长度>=2
                if isinstance(p1, (tuple, list)) and len(p1) >= 2 and \
                   isinstance(p2, (tuple, list)) and len(p2) >= 2:
                    start_pt = (int(p1[0]), int(p1[1]))
                    end_pt = (int(p2[0]), int(p2[1]))
                    cv2.line(img, start_pt, end_pt, line_color, 2)
        
        # 绘制关键点
        point_color = ColorConfig.NEON_YELLOW
        for k, p in pts.items():
            if k in ['mid_hip']: continue
            
            # [关键修复] 过滤掉任何非坐标数据（如 float, bool, 或单值）
            if not isinstance(p, (tuple, list)): 
                continue
            if len(p) < 2: 
                continue
                
            try:
                center = (int(p[0]), int(p[1]))
                cv2.circle(img, center, 4, ColorConfig.NEON_YELLOW, -1)
            except:
                continue