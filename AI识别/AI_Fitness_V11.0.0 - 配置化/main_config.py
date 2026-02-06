import sys
import os
import platform
import time
import tkinter as tk
from tkinter import filedialog
from ctypes import windll, byref, Structure, c_long

# =========================================================================
# 路径与环境配置
# =========================================================================
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Windows 高分屏适配
if platform.system() == 'Windows':
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(2) 
    except:
        try: ctypes.windll.user32.SetProcessDPIAware()
        except: pass

import cv2
import mediapipe as mp
import numpy as np

# 核心模块导入
from core.config import AppConfig, TextConfig, ColorConfig, AlgoConfig
from core.camera import CameraLoader
from core.sound import SoundManager
from ui.renderer import UIRenderer
from utils.smoother import PointSmoother
from logic.spine import SpineAnalyzer
from logic.gatekeeper import Gatekeeper

# [核心修改] 仅导入配置驱动版动作类
try:
    from exercises.press_config import PressExerciseConfig
    from exercises.squat_config import SquatExerciseConfig
except ImportError as e:
    print(f"Fatal Error: Could not import config-driven exercises: {e}")
    print("Please ensure 'press_config.py' and 'squat_config.py' exist and are correct.")
    sys.exit(1)

# [配置版] 窗口标题区分
WINDOW_TITLE = TextConfig.WINDOW_NAME + " [Config Mode]"

# =========================================================================
# 辅助类与函数
# =========================================================================

class RECT(Structure):
    _fields_ = [("left", c_long), ("top", c_long), ("right", c_long), ("bottom", c_long)]

def get_client_rect_size(window_name):
    """获取窗口实际显示区域大小"""
    if platform.system() != 'Windows': return AppConfig.W, AppConfig.H
    try:
        hwnd = windll.user32.FindWindowW(None, window_name)
        if hwnd:
            rect = RECT()
            windll.user32.GetClientRect(hwnd, byref(rect))
            return rect.right, rect.bottom
    except: pass
    return AppConfig.W, AppConfig.H

class Engine:
    """健身动作核心引擎 (纯配置版)"""
    def __init__(self):
        self.sound = SoundManager()
        
        # [核心修改] 仅注册配置版动作
        self.exercises = {
            TextConfig.ACT_PRESS: PressExerciseConfig(self.sound),
            TextConfig.ACT_SQUAT: SquatExerciseConfig(self.sound),
        }
        # 默认启动第一个
        self.current_mode = list(self.exercises.keys())[0]
        self.spine = SpineAnalyzer()
        self.gatekeeper = Gatekeeper()
        self.smoother = PointSmoother(alpha=AlgoConfig.SHRUG_SMOOTH_FACTOR)

    def set_mode(self, mode_name):
        if mode_name in self.exercises and mode_name != self.current_mode:
            self.current_mode = mode_name
            ex = self.exercises[self.current_mode]
            
            # [核心修改] 深度重置状态
            ex.stage = "start"
            ex.counter = 0
            ex.bad_reps = 0
            
            # 重置反馈系统 (FeedbackSystem)
            if hasattr(ex, 'feedback'):
                ex.feedback.reset()
            
            # 重置 GenericExercise 特有状态
            if hasattr(ex, 'fix_memory'): ex.fix_memory = {}
            if hasattr(ex, 'last_rep_results'): ex.last_rep_results = {}
            
            self.gatekeeper.last_act_time = time.time()

    def update(self, pts):
        if not pts: return [], {}
        
        pts = self.smoother.filter(pts)
        current_ex = self.exercises[self.current_mode]
        self.spine.analyze(pts, stage=current_ex.stage)
        
        if not self.gatekeeper.check(pts, self.current_mode, current_ex): 
            return [], pts
        
        shared = { 'max_torso_len': self.spine.get_max_len() }
        vis = current_ex.process(pts, shared)
        
        return vis, pts

    def get_ui_data(self):
        ex = self.exercises[self.current_mode]
        msg, col = ex.get_msg()
        
        # 兼容新旧版 feedback 结构
        error_counts = {}
        if hasattr(ex, 'feedback'):
            error_counts = ex.feedback.error_counts
        elif hasattr(ex, 'error_counts'):
            error_counts = ex.error_counts

        return {
            'mode': self.current_mode, 
            'count': ex.counter, 
            'msg': msg, 
            'msg_col': col, 
            'errs': error_counts, 
            'bad': ex.bad_reps
        }

# =========================================================================
# 主程序入口
# =========================================================================

def main():
    loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(0.1)
    if not loader.ret and not loader.is_video:
        print("Camera not ready."); time.sleep(1.0)
    
    pose = mp.solutions.pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6, model_complexity=1)
    engine = Engine()
    ui = UIRenderer()
    
    menu_open = False
    fps = 0
    prev_time = time.time()
    
    cv2.namedWindow(WINDOW_TITLE, cv2.WINDOW_NORMAL)
    
    def mouse_cb(e, x, y, f, p):
        nonlocal menu_open
        
        cw, ch = get_client_rect_size(WINDOW_TITLE)
        if cw == 0: return
        scale = min(cw / AppConfig.W, ch / AppConfig.H)
        render_w, render_h = int(AppConfig.W * scale), int(AppConfig.H * scale)
        off_x, off_y = (cw - render_w) // 2, (ch - render_h) // 2
        
        if render_w > 0 and render_h > 0:
            lx = int((x - off_x) / scale)
            ly = int((y - off_y) / scale)
        else: lx, ly = -1, -1

        # [核心修改] 仅保留必要的UI交互
        modes = list(engine.exercises.keys())
        if 0 <= lx <= AppConfig.W and 0 <= ly <= AppConfig.H:
            ui.update_hover(lx, ly, menu_open, len(modes), False)
            
            if e == cv2.EVENT_LBUTTONDOWN:
                hit = ui.hit_test(lx, ly, False)
                
                if hit == 'menu_btn': 
                    menu_open = not menu_open
                elif menu_open and hit and hit.startswith('menu_item_'):
                    idx = int(hit.split('_')[2])
                    if 0 <= idx < len(modes): 
                        engine.set_mode(modes[idx])
                        menu_open = False
                elif hit == 'btn_cam': loader.switch_source(0)
                elif hit == 'btn_video':
                    try:
                        root = tk.Tk(); root.withdraw(); root.update()
                        path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4;*.avi;*.mov;*.mkv")])
                        root.destroy()
                        if path: loader.switch_source(path)
                    except: pass
                elif hit == 'btn_play': loader.toggle_pause()
                elif hit == 'seek_bar':
                    rect = ui.hit_boxes['seek_bar']; w = rect[2]-rect[0]
                    if w > 0: loader.seek((lx-rect[0])/w)
                elif menu_open and hit is None: 
                    menu_open = False

    cv2.setMouseCallback(WINDOW_TITLE, mouse_cb)
    
    while loader.running:
        ret, frame = loader.read()
        if not ret or frame is None: 
            time.sleep(0.01); continue
            
        h, w = frame.shape[:2]
        if h != AppConfig.H: 
            scale = AppConfig.H / h; w = int(w * scale); h = AppConfig.H
            frame = cv2.resize(frame, (w, h))
        
        f_l = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8)
        if w >= AppConfig.HALF_W: 
            sx = (w - AppConfig.HALF_W) // 2
            f_l = frame[:, sx : sx + AppConfig.HALF_W].copy()
        else: 
            sx = (AppConfig.HALF_W - w) // 2
            f_l[:, sx : sx + w] = frame
        f_l = cv2.flip(f_l, 1)
        f_r = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8) + 20
        
        curr_time = time.time()
        fps = int(1/(curr_time-prev_time)) if curr_time>prev_time else 0
        prev_time = curr_time
        
        res = pose.process(cv2.cvtColor(f_l, cv2.COLOR_BGR2RGB))
        pts = {}
        if res.pose_landmarks:
             for i, n in {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',27:'la',28:'ra',0:'nose'}.items():
                 lm = res.pose_landmarks.landmark[i]
                 if lm.visibility > 0.5: pts[n] = (int(lm.x*AppConfig.HALF_W), int(lm.y*AppConfig.H))
        
        vis, pts = engine.update(pts)
        data = engine.get_ui_data()
        
        ui.draw_skeleton(f_l, pts, False); ui.draw_visuals(f_l, vis)
        ui.draw_skeleton(f_r, pts, True); ui.draw_visuals(f_r, vis)
        
        if loader.is_video: ui.draw_video_bar(f_l, loader.get_progress(), loader.paused)
        
        final = np.hstack((f_l, f_r))
        
        # [核心修改] 简化UI调用，移除typing和tuning相关
        # [Fix] 传入当前引擎支持的动作列表
        available_modes = list(engine.exercises.keys())
        ui.draw_all_text_layers(final, data['mode'], data['count'], fps, menu_open, "180", False, data['msg'], data['msg_col'], data['errs'], data['bad'], loader.is_video, loader.paused, menu_items=available_modes)
        
        win_w, win_h = get_client_rect_size(WINDOW_TITLE)
        scale = min(win_w / AppConfig.W, win_h / AppConfig.H)
        rw, rh = int(AppConfig.W * scale), int(AppConfig.H * scale)
        off_x, off_y = (win_w - rw) // 2, (win_h - rh) // 2
        
        final_disp = np.zeros((win_h, win_w, 3), dtype=np.uint8)
        if rw > 0 and rh > 0: final_disp[off_y:off_y+rh, off_x:off_x+rw] = cv2.resize(final, (rw, rh))
        cv2.imshow(WINDOW_TITLE, final_disp)
        
        if cv2.waitKey(1) & 0xFF == 27: break

    loader.release(); cv2.destroyAllWindows()

if __name__ == "__main__": main()