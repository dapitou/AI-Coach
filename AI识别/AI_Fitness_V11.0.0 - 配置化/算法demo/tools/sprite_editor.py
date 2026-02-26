import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw, ImageOps
import json
import os
import math
import numpy as np
import copy

# =========================================================================
# 1. 全局配置
# =========================================================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
ASSETS_DIR = os.path.join(project_root, 'assets')
CONFIG_PATH = os.path.join(ASSETS_DIR, 'body_config.json')

# 虚拟世界坐标系 (World Space)
WORLD_W, WORLD_H = 1000, 1000
CX, CY = WORLD_W // 2, 100

# --- A-Pose 默认骨架 (World Space) ---
DEFAULT_POSE = {
    'nose':   (CX, CY),
    'neck':   (CX, CY + 80),
    # A-Pose
    'rs':     (CX + 110, CY + 90),   'ls':     (CX - 110, CY + 90),
    're':     (CX + 240, CY + 180),  'le':     (CX - 240, CY + 180),
    'rw':     (CX + 350, CY + 250),  'lw':     (CX - 350, CY + 250),
    'mid_hip': (CX, CY + 380),
    'rh':     (CX + 60, CY + 380),   'lh':     (CX - 60, CY + 380),
    'rk':     (CX + 60, CY + 650),   'lk':     (CX - 60, CY + 650),
    'ra':     (CX + 60, CY + 880),   'la':     (CX - 60, CY + 880)
}

SKELETON_LINKS = [
    ('nose','neck'), ('neck','mid_hip'),
    ('mid_hip','lh'), ('mid_hip','rh'),
    ('ls','rs'), ('ls','le'), ('le','lw'), ('rs','re'), ('re','rw'),
    ('lh','lk'), ('lk','la'), ('rh','rk'), ('rk','ra')
]

SYMMETRY_MAP = {
    'head':      ('neck', 'nose', 'neck', 'nose'),
    'torso':     ('neck', 'mid_hip', 'neck', 'mid_hip'),
    'upper_arm': ('rs', 're', 'ls', 'le'),
    'lower_arm': ('re', 'rw', 'le', 'lw'),
    'upper_leg': ('rh', 'rk', 'lh', 'lk'),
    'lower_leg': ('rk', 'ra', 'lk', 'la')
}

MIRROR_NODES = {
    'ls': 'rs', 'rs': 'ls', 'le': 're', 're': 'le',
    'lw': 'rw', 'rw': 'lw', 'lh': 'rh', 'rh': 'lh',
    'lk': 'rk', 'rk': 'lk', 'la': 'ra', 'ra': 'la'
}

DEFAULT_Z = {
    'lower_leg': 1, 'upper_leg': 1,
    'torso': 2, 'head': 3,
    'lower_arm': 4, 'upper_arm': 4
}

# =========================================================================
# 2. 历史记录管理器
# =========================================================================
class HistoryManager:
    def __init__(self, limit=100):
        self.limit = limit
        self.undo_stack = []
        self.redo_stack = []

    def push(self, state):
        # state is (config, pose) deepcopy
        self.undo_stack.append(state)
        if len(self.undo_stack) > self.limit:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_state):
        if not self.undo_stack: return None
        # Push current to redo
        self.redo_stack.append(current_state)
        return self.undo_stack.pop()

    def redo(self, current_state):
        if not self.redo_stack: return None
        # Push current to undo
        self.undo_stack.append(current_state)
        return self.redo_stack.pop()

# =========================================================================
# 3. 主编辑器
# =========================================================================
class FullBodyRigger(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AEKE 骨骼绑定工作台 (Pro)")
        self.geometry("1600x1000")
        self.state("zoomed")

        # --- 核心数据 ---
        self.config = {}
        self.current_pose = copy.deepcopy(DEFAULT_POSE)
        self.raw_images = {}
        self.tk_refs = []
        self.transform_cache = {}
        
        # --- 视图状态 (Viewport) ---
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.drag_middle_start = None

        # --- 编辑状态 ---
        self.selected_part = None
        self.editing_bone_mode = False # 是否处于骨骼编辑模式
        self.editing_anchor_mode = False # 是否处于锚点编辑模式
        
        self.history = HistoryManager()
        self.last_mouse = (0, 0)
        self.dragging = False
        self.drag_target = None # 'body', 'pivot', 'end', 'node'

        # 初始化
        self._ensure_dir()
        self._load_config()
        self._load_images()
        self._setup_ui()
        
        # 初始居中
        self._reset_view()
        
        # 记录初始状态
        self._save_snapshot()

    def _ensure_dir(self):
        if not os.path.exists(ASSETS_DIR):
            try: os.makedirs(ASSETS_DIR)
            except: pass

    def _load_config(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except: self.config = {}
        
        for part in SYMMETRY_MAP.keys():
            if part not in self.config:
                self.config[part] = {
                    "path": f"{part}.png",
                    "pivot": [0.5, 0.1], 
                    "end": [0.5, 0.9], 
                    "default_size": [100, 200],
                    "z_index": DEFAULT_Z.get(part, 1),
                    "mirror_x": False, "mirror_y": False
                }

    def _load_images(self):
        for name, cfg in self.config.items():
            path = os.path.join(ASSETS_DIR, cfg['path'])
            if os.path.exists(path):
                self.raw_images[name] = Image.open(path).convert("RGBA")
            else:
                img = Image.new('RGBA', (100, 200), (100, 100, 100, 100))
                draw = ImageDraw.Draw(img)
                draw.rectangle((0,0,100,200), outline="white", width=2)
                draw.text((10,90), name, fill="white")
                self.raw_images[name] = img

    def _reset_view(self):
        # 简单居中：假设画布宽1200
        canvas_w = 1200
        self.pan_x = canvas_w / 2 - CX
        self.pan_y = 50

    # =========================================================================
    # 坐标转换系统 (Viewport Transform)
    # =========================================================================
    def to_screen(self, wx, wy):
        """ World -> Screen """
        sx = (wx * self.zoom) + self.pan_x
        sy = (wy * self.zoom) + self.pan_y
        return sx, sy

    def to_world(self, sx, sy):
        """ Screen -> World """
        wx = (sx - self.pan_x) / self.zoom
        wy = (sy - self.pan_y) / self.zoom
        return wx, wy

    # =========================================================================
    # UI 构建
    # =========================================================================
    def _setup_ui(self):
        panel = tk.Frame(self, width=380, bg="#f0f0f0")
        panel.pack(side=tk.LEFT, fill=tk.Y)
        panel.pack_propagate(False)

        # 标题区
        tk.Label(panel, text="组件属性 (Properties)", font=("微软雅黑", 12, "bold"), bg="#f0f0f0").pack(pady=10)

        # 1. 状态指示器
        self.lbl_selected = tk.Label(panel, text="未选中", font=("Arial", 14), bg="#ddd", height=2)
        self.lbl_selected.pack(fill=tk.X, padx=10)
        self.lbl_status = tk.Label(panel, text="准备就绪", fg="#666", bg="#f0f0f0")
        self.lbl_status.pack(pady=5)

        # 2. 快捷操作栏
        action_frame = tk.Frame(panel, bg="#f0f0f0")
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        tk.Button(action_frame, text="↩ 撤销 (Ctrl+Z)", command=self._undo).pack(side=tk.LEFT, expand=True, fill=tk.X)
        tk.Button(action_frame, text="↪ 重做 (Ctrl+Y)", command=self._redo).pack(side=tk.LEFT, expand=True, fill=tk.X)

        # 3. 镜像控制
        mirror_frame = tk.LabelFrame(panel, text="图片镜像 (Flip)", bg="#f0f0f0", padx=10, pady=10)
        mirror_frame.pack(fill=tk.X, padx=10, pady=10)
        tk.Button(mirror_frame, text="↔ 水平翻转", command=lambda: self._toggle_mirror('x')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        tk.Button(mirror_frame, text="↕ 垂直翻转", command=lambda: self._toggle_mirror('y')).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # 4. 尺寸缩放
        scale_frame = tk.LabelFrame(panel, text="尺寸缩放 (Size)", bg="#f0f0f0", padx=10, pady=10)
        scale_frame.pack(fill=tk.X, padx=10, pady=10)

        tk.Label(scale_frame, text="整体缩放 (Uniform):", bg="#f0f0f0").pack(anchor="w")
        self.var_uniform = tk.DoubleVar(value=1.0)
        s_uni = tk.Spinbox(scale_frame, from_=0.1, to=5.0, increment=0.05, textvariable=self.var_uniform, command=self._on_uniform_change)
        s_uni.pack(fill=tk.X)
        s_uni.bind('<Return>', self._on_uniform_change)

        grid = tk.Frame(scale_frame, bg="#f0f0f0")
        grid.pack(fill=tk.X, pady=10)
        tk.Label(grid, text="W:", bg="#f0f0f0").grid(row=0, column=0)
        self.var_w = tk.IntVar()
        sb_w = tk.Spinbox(grid, from_=10, to=2000, increment=5, textvariable=self.var_w, width=8, command=self._on_manual_size)
        sb_w.grid(row=0, column=1, padx=5)
        sb_w.bind('<Return>', self._on_manual_size)

        tk.Label(grid, text="H:", bg="#f0f0f0").grid(row=0, column=2)
        self.var_h = tk.IntVar()
        sb_h = tk.Spinbox(grid, from_=10, to=2000, increment=5, textvariable=self.var_h, width=8, command=self._on_manual_size)
        sb_h.grid(row=0, column=3, padx=5)
        sb_h.bind('<Return>', self._on_manual_size)

        # 5. 层级
        z_frame = tk.LabelFrame(panel, text="渲染层级 (Z-Index)", bg="#f0f0f0", padx=10, pady=10)
        z_frame.pack(fill=tk.X, padx=10, pady=5)
        self.var_z = tk.IntVar()
        tk.Scale(z_frame, from_=0, to=10, orient=tk.HORIZONTAL, variable=self.var_z, command=self._on_z_change).pack(fill=tk.X)

        # 6. 保存
        tk.Button(panel, text="💾 保存配置 (SAVE)", bg="#4CAF50", fg="white", font=("Arial", 12, "bold"), height=2, command=self._save_config).pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=20)

        # === 画布 ===
        self.canvas = tk.Canvas(self, bg="#2b2b2b", cursor="crosshair")
        self.canvas.pack(side=tk.RIGHT, expand=True, fill=tk.BOTH)
        self._refresh_canvas()
        
        # 事件绑定
        self.canvas.bind("<ButtonPress-1>", self._on_mouse_down)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        
        # 视图控制
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<ButtonPress-2>", self._on_pan_start) # 中键
        self.canvas.bind("<B2-Motion>", self._on_pan_drag)
        self.canvas.bind("<ButtonPress-3>", self._on_pan_start) # 右键
        self.canvas.bind("<B3-Motion>", self._on_pan_drag)

        # 快捷键
        self.bind("<Control-z>", lambda e: self._undo())
        self.bind("<Control-y>", lambda e: self._redo())

    # =========================================================================
    # 渲染系统
    # =========================================================================
    def _refresh_canvas(self):
        self.canvas.delete("all")
        self.tk_refs = []
        self.transform_cache = {}

        # 绘制无限网格
        self._draw_grid()

        # 1. 渲染组件
        items = sorted(self.config.keys(), key=lambda k: (self.config[k].get('z_index', 0)))
        
        for name in items:
            if name not in self.raw_images: continue
            if name not in SYMMETRY_MAP: continue

            r_start, r_end, l_start, l_end = SYMMETRY_MAP[name]
            
            # 右侧 (标准侧)
            self._draw_single_instance(name, r_start, r_end, is_left=False)
            
            # 左侧 (镜像侧)
            if l_start != r_start:
                self._draw_single_instance(name, l_start, l_end, is_left=True)

        # 2. 渲染骨架连线
        for k1, k2 in SKELETON_LINKS:
            p1 = self.to_screen(*self.current_pose[k1])
            p2 = self.to_screen(*self.current_pose[k2])
            self.canvas.create_line(p1, p2, fill="#666666", width=2, tags="overlay")

        # 3. 渲染骨骼节点
        for k, p_world in self.current_pose.items():
            sx, sy = self.to_screen(*p_world)
            
            # 只有在骨骼编辑模式下，或者选中该骨骼时，才高亮/变大
            if self.editing_bone_mode:
                color = "#FFFF00"  # 黄色
                radius = 6
                outline = "red"
            else:
                color = "#00AAFF" # 蓝色
                radius = 4
                outline = "white"
            
            tag = f"node:{k}"
            self.canvas.create_oval(sx-radius, sy-radius, sx+radius, sy+radius, 
                                    fill=color, outline=outline, tags=("bone_node", tag))

        # 4. 渲染组件锚点 (仅在锚点编辑模式)
        if self.editing_anchor_mode and self.selected_part:
            self._draw_gizmos(self.selected_part)

    def _draw_grid(self):
        # 简单的视口网格
        # 找到视口边界对应的世界坐标
        w, h = self.canvas.winfo_width(), self.canvas.winfo_height()
        if w < 10: w, h = 1200, 900
        
        start_x, start_y = self.to_world(0, 0)
        end_x, end_y = self.to_world(w, h)
        
        step = 50
        # 对齐 step
        start_idx_x = int(start_x // step)
        end_idx_x = int(end_x // step) + 1
        
        for i in range(start_idx_x, end_idx_x):
            wx = i * step
            sx, _ = self.to_screen(wx, 0)
            color = "#444444" if i % 4 == 0 else "#333333"
            self.canvas.create_line(sx, 0, sx, h, fill=color)

        start_idx_y = int(start_y // step)
        end_idx_y = int(end_y // step) + 1
        for i in range(start_idx_y, end_idx_y):
            wy = i * step
            _, sy = self.to_screen(0, wy)
            color = "#444444" if i % 4 == 0 else "#333333"
            self.canvas.create_line(0, sy, w, sy, fill=color)

    def _draw_single_instance(self, name, start_k, end_k, is_left):
        cfg = self.config[name]
        raw_img = self.raw_images[name]
        
        # 镜像逻辑：
        # 如果是左侧，强制先水平镜像，然后再应用用户的镜像配置
        # 这样能保证左手和右手是对称的
        img_to_draw = raw_img.copy()
        
        if is_left:
             img_to_draw = ImageOps.mirror(img_to_draw)

        # 用户手动镜像
        if cfg.get('mirror_x'): img_to_draw = ImageOps.mirror(img_to_draw)
        if cfg.get('mirror_y'): img_to_draw = ImageOps.flip(img_to_draw)

        # World 坐标
        start_pt = np.array(self.current_pose[start_k])
        end_pt = np.array(self.current_pose[end_k])

        screen_vec = end_pt - start_pt
        screen_len = np.linalg.norm(screen_vec)
        
        # Image 坐标
        w, h = img_to_draw.size
        pu, pv = cfg['pivot']
        eu, ev = cfg['end']
        
        # 左侧的 Pivot/End 也是镜像的
        if is_left:
            # Pivot X 需要翻转 (1.0 - u)
            # 注意：如果我们之前做了 ImageOps.mirror，那么 UV 坐标系也变了
            # 这里的逻辑比较绕。简化：
            # 假设 config 存的是右侧(标准)的 UV。
            # 当渲染左侧时，图片镜像了，所以 UV 的 X 也要镜像。
            cur_pu, cur_pv = (1.0 - pu), pv
            cur_eu, cur_ev = (1.0 - eu), ev
        else:
            cur_pu, cur_pv = pu, pv
            cur_eu, cur_ev = eu, ev
            
        img_vec = np.array([(cur_eu - cur_pu)*w, (cur_ev - cur_pv)*h])
        img_len = np.linalg.norm(img_vec)
        img_angle = math.degrees(math.atan2(img_vec[1], img_vec[0]))
        bone_angle = math.degrees(math.atan2(screen_vec[1], screen_vec[0]))

        # 缩放
        def_w, def_h = cfg['default_size']
        scale_w = def_w / w
        scale_len = screen_len / img_len if img_len > 0 else 1.0
        
        # 最终像素尺寸 (应用视图缩放)
        render_scale = self.zoom
        target_w = int(w * scale_w * render_scale)
        target_h = int(h * scale_len * render_scale)
        
        if target_w < 1 or target_h < 1: return

        # 变换
        resized = img_to_draw.resize((target_w, target_h), Image.LANCZOS)
        final_angle = img_angle - bone_angle
        rotated = resized.rotate(final_angle, resample=Image.BICUBIC, expand=True)
        
        # 对齐
        cx, cy = target_w/2, target_h/2
        new_pivot_x = cur_pu * target_w
        new_pivot_y = cur_pv * target_h
        
        rad = math.radians(final_angle)
        cos_a = math.cos(rad); sin_a = math.sin(rad)
        px = new_pivot_x - cx; py = new_pivot_y - cy
        
        rot_px = px * cos_a + py * sin_a
        rot_py = -px * sin_a + py * cos_a
        
        rcx, rcy = rotated.width/2, rotated.height/2
        
        # 屏幕坐标 (World -> Screen)
        sx_start, sy_start = self.to_screen(*start_pt)
        
        paste_x = sx_start - (rcx + rot_px)
        paste_y = sy_start - (rcy + rot_py)
        
        # 绘制
        tk_img = ImageTk.PhotoImage(rotated)
        self.tk_refs.append(tk_img)
        
        # 选中高亮
        if name == self.selected_part and not self.editing_bone_mode:
            outline_col = "#00FF00" if not self.editing_anchor_mode else "#888"
            dash = (2,2) if not self.editing_anchor_mode else None
            self.canvas.create_rectangle(paste_x, paste_y, paste_x+rotated.width, paste_y+rotated.height, 
                                         outline=outline_col, width=1, dash=dash, tags="img_bound")
        
        # 如果是 anchor mode，让图片变暗一点？(可选)
        
        tag_side = "L" if is_left else "R"
        tag = f"part:{name}:{tag_side}"
        self.canvas.create_image(paste_x, paste_y, image=tk_img, anchor="nw", tags=("img", tag))
        
        # 缓存逆变换数据
        self.transform_cache[tag] = {
            'name': name,
            'is_left': is_left,
            'angle': final_angle,
            'scale_w': scale_w * render_scale,
            'scale_h': scale_len * render_scale,
            'orig_size': (w, h)
        }

    def _draw_gizmos(self, name):
        # 绘制红绿点 (World Space -> Screen Space)
        # 只在 Anchor 模式下显示
        r_start, r_end, l_start, l_end = SYMMETRY_MAP[name]
        
        self._draw_gizmo_dots(r_start, r_end)
        if r_start != l_start:
             self._draw_gizmo_dots(l_start, l_end)

    def _draw_gizmo_dots(self, sk, ek):
        ps = self.to_screen(*self.current_pose[sk])
        pe = self.to_screen(*self.current_pose[ek])
        r = 6
        self.canvas.create_oval(ps[0]-r, ps[1]-r, ps[0]+r, ps[1]+r, fill="#00FF00", outline="white", tags="gizmo")
        self.canvas.create_oval(pe[0]-r, pe[1]-r, pe[0]+r, pe[1]+r, fill="#FF0000", outline="white", tags="gizmo")

    # =========================================================================
    # 交互处理
    # =========================================================================
    def _save_snapshot(self):
        state = (copy.deepcopy(self.config), copy.deepcopy(self.current_pose))
        self.history.push(state)

    def _undo(self):
        current = (copy.deepcopy(self.config), copy.deepcopy(self.current_pose))
        prev = self.history.undo(current)
        if prev:
            self.config, self.current_pose = prev
            self._update_ui_state()
            self._refresh_canvas()

    def _redo(self):
        current = (copy.deepcopy(self.config), copy.deepcopy(self.current_pose))
        next_state = self.history.redo(current)
        if next_state:
            self.config, self.current_pose = next_state
            self._update_ui_state()
            self._refresh_canvas()

    def _on_mouse_down(self, event):
        x, y = event.x, event.y
        self.last_mouse = (x, y)
        self.dragging = True
        self.drag_target = None
        
        self._save_snapshot() # 开始操作前保存状态

        # 1. 骨骼编辑模式检测
        if self.editing_bone_mode:
            items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
            for item in items:
                tags = self.canvas.gettags(item)
                for t in tags:
                    if t.startswith("node:"):
                        # 只有在编辑模式下，点击骨骼才算拖拽
                        self.selected_part = None # 互斥
                        self.drag_target = t.split(":")[1] # node name
                        return
        
        # 2. 锚点编辑模式检测 (Gizmo)
        if self.editing_anchor_mode and self.selected_part:
            # 简单距离检测
            r_s, r_e, l_s, l_e = SYMMETRY_MAP[self.selected_part]
            checks = [(r_s, 'pivot'), (r_e, 'end')]
            if r_s != l_s: checks.extend([(l_s, 'pivot'), (l_e, 'end')])
            
            for node, kind in checks:
                sx, sy = self.to_screen(*self.current_pose[node])
                if math.hypot(x-sx, y-sy) < 10:
                    self.drag_target = kind
                    return

        # 3. 组件检测 (摆放模式/进入选中)
        items = self.canvas.find_overlapping(x-1, y-1, x+1, y+1)
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            for t in tags:
                if t.startswith("part:"):
                    name = t.split(":")[1]
                    self.selected_part = name
                    self.editing_bone_mode = False # 互斥
                    # 如果之前不是 anchor mode，则进入 placement mode
                    if not self.editing_anchor_mode:
                        self.drag_target = 'body' # 拖拽图片
                    
                    self.drag_instance_tag = t # 记录拖的是左边还是右边
                    self._update_ui_state()
                    self._refresh_canvas()
                    return

        # 空白处点击
        self.selected_part = None
        self.editing_bone_mode = False
        self.editing_anchor_mode = False
        self._update_ui_state()
        self._refresh_canvas()

    def _on_double_click(self, event):
        x, y = event.x, event.y
        
        # 检测骨骼 -> 进入骨骼编辑
        items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)
        for item in items:
            tags = self.canvas.gettags(item)
            for t in tags:
                if t.startswith("node:"):
                    self.editing_bone_mode = True
                    self.editing_anchor_mode = False
                    self.selected_part = None
                    self._update_ui_state()
                    self._refresh_canvas()
                    return

        # 检测组件 -> 切换 Anchor/Placement
        for item in reversed(items):
            tags = self.canvas.gettags(item)
            for t in tags:
                if t.startswith("part:"):
                    self.editing_bone_mode = False
                    self.editing_anchor_mode = not self.editing_anchor_mode
                    self.selected_part = t.split(":")[1]
                    self._update_ui_state()
                    self._refresh_canvas()
                    return

    def _on_mouse_drag(self, event):
        if not self.dragging: return
        dx = (event.x - self.last_mouse[0])
        dy = (event.y - self.last_mouse[1])
        self.last_mouse = (event.x, event.y)
        
        # 转换为 World Space Delta
        w_dx = dx / self.zoom
        w_dy = dy / self.zoom

        # A. 拖拽骨骼
        if self.editing_bone_mode and self.drag_target:
            node = self.drag_target
            wx, wy = self.current_pose[node]
            self.current_pose[node] = (wx + w_dx, wy + w_dy)
            
            # 镜像同步
            if node in MIRROR_NODES:
                mn = MIRROR_NODES[node]
                mwx, mwy = self.current_pose[mn]
                # 对称逻辑: X反向，Y同向
                # 需要以 CX 为轴心?
                # 简化逻辑：直接应用 delta. Left X moved +10 -> Right X moved -10
                self.current_pose[mn] = (mwx - w_dx, mwy + w_dy)
            
            self._refresh_canvas()
            return

        # B. 拖拽组件 / 锚点
        if self.selected_part and self.drag_target:
            # 需要逆向计算 UV Delta
            # 获取当前拖拽实例的 Transform
            tag = getattr(self, 'drag_instance_tag', None)
            # 如果是 anchor drag，可能没有 set tag，需推断
            if not tag:
                # 简单推断：在屏幕左边就是左，右边就是右 (假设A-Pose)
                if event.x < self.to_screen(CX, 0)[0]: tag = f"part:{self.selected_part}:L"
                else: tag = f"part:{self.selected_part}:R"
            
            info = self.transform_cache.get(tag)
            if not info:
                # Fallback
                for k, v in self.transform_cache.items():
                    if v['name'] == self.selected_part:
                        info = v; break
            
            if info:
                # 逆旋转
                rad = math.radians(-info['angle'])
                cos_a = math.cos(rad); sin_a = math.sin(rad)
                
                # 这里用 Screen Delta 还是 World Delta? 
                # TransformInfo 里的 scale 是包含了 zoom 的。
                # 所以我们应该用 Screen Delta (dx, dy) 进行逆算。
                
                local_dx = dx * cos_a + dy * sin_a
                local_dy = -dx * sin_a + dy * cos_a
                
                raw_dx = local_dx / info['scale_w']
                raw_dy = local_dy / info['scale_h']
                
                du = raw_dx / info['orig_size'][0]
                dv = raw_dy / info['orig_size'][1]
                
                # 如果是左侧，UV的X方向是反的 (因为镜像了)
                if info['is_left']:
                    du = -du
                
                cfg = self.config[self.selected_part]
                
                if not self.editing_anchor_mode and self.drag_target == 'body':
                    # 摆放模式：图片动 = Pivot动
                    # 鼠标往右 -> 图片往右 -> Pivot相对于图片左移 -> U 减小
                    cfg['pivot'][0] -= du
                    cfg['pivot'][1] -= dv
                    cfg['end'][0] -= du
                    cfg['end'][1] -= dv
                    
                elif self.editing_anchor_mode:
                    if self.drag_target == 'pivot':
                        cfg['pivot'][0] -= du
                        cfg['pivot'][1] -= dv
                    elif self.drag_target == 'end':
                        cfg['end'][0] -= du
                        cfg['end'][1] -= dv
                
                self._refresh_canvas()

    def _on_mouse_up(self, event):
        self.dragging = False

    # =========================================================================
    # 视图控制
    # =========================================================================
    def _on_zoom(self, event):
        scale = 1.1 if event.delta > 0 else 0.9
        self.zoom *= scale
        self._refresh_canvas()

    def _on_pan_start(self, event):
        self.drag_middle_start = (event.x, event.y)

    def _on_pan_drag(self, event):
        if not self.drag_middle_start: return
        dx = event.x - self.drag_middle_start[0]
        dy = event.y - self.drag_middle_start[1]
        self.pan_x += dx
        self.pan_y += dy
        self.drag_middle_start = (event.x, event.y)
        self._refresh_canvas()

    # =========================================================================
    # UI 状态更新
    # =========================================================================
    def _update_ui_state(self):
        if self.editing_bone_mode:
            self.lbl_selected.config(text="⚠️ 骨骼编辑模式", bg="#FFFF00", fg="black")
            self.lbl_status.config(text="拖拽黄色节点调整骨架 (自动镜像)")
            return

        if self.editing_anchor_mode:
            self.lbl_selected.config(text=f"锚点编辑: {self.selected_part}", bg="#E91E63", fg="white")
            self.lbl_status.config(text="拖拽红绿点调整关节位置")
        elif self.selected_part:
            self.lbl_selected.config(text=f"摆放模式: {self.selected_part}", bg="#2196F3", fg="white")
            self.lbl_status.config(text="拖拽图片以对齐骨架")
        else:
            self.lbl_selected.config(text="未选中", bg="#ddd", fg="black")
            self.lbl_status.config(text="双击组件或骨骼进入编辑")
            
        if self.selected_part:
            cfg = self.config[self.selected_part]
            self.var_z.set(cfg.get('z_index', 0))
            w, h = cfg['default_size']
            self.var_w.set(w)
            self.var_h.set(h)
            self.var_uniform.set(1.0)

    def _toggle_mirror(self, axis):
        if not self.selected_part: return
        self._save_snapshot()
        key = "mirror_x" if axis == 'x' else "mirror_y"
        self.config[self.selected_part][key] = not self.config[self.selected_part][key]
        self._refresh_canvas()

    def _on_manual_size(self, event=None):
        if not self.selected_part: return
        self._save_snapshot()
        w, h = self.var_w.get(), self.var_h.get()
        self.config[self.selected_part]['default_size'] = [w, h]
        self._refresh_canvas()

    def _on_uniform_change(self, event=None):
        if not self.selected_part: return
        try: ratio = self.var_uniform.get()
        except: return
        if ratio == 1.0: return
        
        self._save_snapshot()
        cfg = self.config[self.selected_part]
        w, h = cfg['default_size']
        new_w, new_h = int(w*ratio), int(h*ratio)
        cfg['default_size'] = [new_w, new_h]
        
        self.var_w.set(new_w)
        self.var_h.set(new_h)
        self.var_uniform.set(1.0)
        self._refresh_canvas()

    def _on_z_change(self, val):
        if self.selected_part:
            self._save_snapshot()
            self.config[self.selected_part]['z_index'] = int(val)
            self._refresh_canvas()

    def _save_config(self):
        try:
            with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            messagebox.showinfo("Saved", "配置已保存！")
        except Exception as e:
            messagebox.showerror("Error", str(e))

if __name__ == "__main__":
    app = FullBodyRigger()
    app.mainloop()