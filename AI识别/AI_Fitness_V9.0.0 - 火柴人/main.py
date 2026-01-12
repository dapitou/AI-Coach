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
from core.config import AppConfig, TextConfig, ColorConfig, AlgoConfig, TUNING_TREE
from core.camera import CameraLoader
from core.sound import SoundManager
from ui.renderer import UIRenderer
from utils.geometry import GeomUtils
from utils.smoother import PointSmoother
from logic.spine import SpineAnalyzer
from logic.gatekeeper import Gatekeeper
from exercises import PressExercise, SquatExercise, LungeExercise, FrontRaiseExercise

# 尝试导入编辑器工具 (如果存在)
try:
    from tools.sprite_editor import SpriteEditor
    HAS_EDITOR = True
except ImportError:
    HAS_EDITOR = False
    print("Warning: tools.sprite_editor not found. Calibration disabled.")

# =========================================================================
# 辅助类与函数
# =========================================================================

class RECT(Structure):
    _fields_ = [("left", c_long), ("top", c_long), ("right", c_long), ("bottom", c_long)]

def get_client_rect_size(window_name):
    """获取窗口实际显示区域大小 (Windows下处理标题栏高度)"""
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
    """健身动作核心引擎"""
    def __init__(self):
        self.sound = SoundManager()
        self.exercises = {
            TextConfig.ACT_PRESS: PressExercise(self.sound),
            TextConfig.ACT_SQUAT: SquatExercise(self.sound),
            TextConfig.ACT_RAISE: FrontRaiseExercise(self.sound),
            TextConfig.ACT_LUNGE: LungeExercise(self.sound)
        }
        self.current_mode = TextConfig.ACT_PRESS
        self.spine = SpineAnalyzer()
        self.gatekeeper = Gatekeeper()
        self.smoother = PointSmoother(alpha=AlgoConfig.SHRUG_SMOOTH_FACTOR)

    def set_mode(self, mode_name):
        if mode_name in self.exercises and mode_name != self.current_mode:
            self.current_mode = mode_name
            ex = self.exercises[self.current_mode]
            ex.stage = "start"
            ex.counter = 0
            ex.bad_reps = 0
            ex.feedback.error_counts.clear() 
            ex.history = {}
            ex.feedback.active_feedback.clear()
            self.gatekeeper.last_act_time = time.time()

    def update(self, pts, world_pts, h_val):
        if not pts: return [], {}
        
        # 1. 平滑处理
        pts = self.smoother.filter(pts)
        
        # 2. 脊柱物理分析
        current_ex = self.exercises[self.current_mode]
        self.spine.analyze(pts, stage=current_ex.stage)
        
        # 3. 动作门控检查 (是否在做当前动作)
        if not self.gatekeeper.check(pts, self.current_mode, current_ex): 
            return [], pts
        
        # 4. 动作计数与纠错
        shared = {
            'max_torso_len': self.spine.get_max_len(),
            'rounding_bad': pts.get('rounding_bad', False),
            'base_shrug_dist': 0 
        }
        vis = current_ex.process(pts, shared)
        
        # 5. 追加通用可视化 (如脊柱红线)
        if pts.get('rounding_bad') and 'rounding' in current_ex.active_feedback:
            vis.append({
                'type': 'rounding_guide', 
                'neck': pts['neck'], 'thorax': pts['thorax'], 
                'waist': pts['waist'], 'hip': pts['hip']
            })
        return vis, pts

    def get_ui_data(self):
        ex = self.exercises[self.current_mode]
        msg, col = ex.get_msg()
        return {
            'mode': self.current_mode, 
            'count': ex.counter, 
            'msg': msg, 
            'msg_col': col, 
            'errs': ex.feedback.error_counts, 
            'bad': ex.bad_reps
        }

def flatten_tuning_tree(mode, params_dict):
    """将树状配置展平为列表，用于 UI 点击检测"""
    flat = []
    groups = TUNING_TREE.get(mode, [])
    for grp in groups:
        if grp.get('switch'):
            flat.append({'key': grp['switch'], 'type': 'bool'})
            if grp.get('prio'): flat.append({'key': grp['prio'], 'type': 'input'})
            is_on = params_dict.get(grp['switch'], 'True') == 'True'
            if not is_on: continue
        else:
            flat.append({'key': None, 'type': 'header'})
        for p_key, _ in grp['params']:
            flat.append({'key': p_key, 'type': 'input'})
    return flat

# =========================================================================
# 主程序入口
# =========================================================================

def main():
    # 1. 初始化摄像头
    loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(0.1)
    if not loader.ret and not loader.is_video:
        print("Camera not ready."); time.sleep(1.0)
    
    # 2. 初始化 AI 模型与引擎
    pose = mp.solutions.pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6, model_complexity=1)
    engine = Engine()
    ui = UIRenderer()
    
    # UI 状态变量
    menu_open = False
    tuning_open = False
    tuning_params = {} 
    tuning_idx = -1 
    is_typing = False
    h_str = "180"
    fps = 0
    prev_time = time.time()
    
    # 创建窗口
    cv2.namedWindow(TextConfig.WINDOW_NAME, cv2.WINDOW_NORMAL)
    # 临时隐藏Tk根窗口用于获取屏幕尺寸
    root = tk.Tk(); root.withdraw(); sw, sh = root.winfo_screenwidth(), root.winfo_screenheight(); root.destroy()
    cv2.resizeWindow(TextConfig.WINDOW_NAME, int(sw*0.9), int(sh*0.9))
    cv2.moveWindow(TextConfig.WINDOW_NAME, int(sw*0.05), int(sh*0.05))
    
    # --- 回调函数：打开火柴人校准器 ---
    def open_sprite_editor():
        if not HAS_EDITOR:
            print("Editor module missing.")
            return

        loader.paused = True # 暂停视频/摄像头
        try:
            # 创建独立的 Tk 环境
            editor_root = tk.Tk()
            editor_root.withdraw() # 隐藏主窗口
            
            # 校准保存后的回调
            def on_save_callback():
                ui.skeleton.reload_assets() # 热重载
                
            # 启动编辑器
            asset_path = os.path.join(project_root, 'assets')
            config_path = os.path.join(asset_path, 'body_config.json')
            
            editor = SpriteEditor(editor_root, asset_path, config_path, callback_reload=on_save_callback)
            
            # 阻塞等待直到编辑器关闭
            editor_root.wait_window(editor)
            editor_root.destroy()
            
        except Exception as e:
            print(f"Failed to open editor: {e}")
        finally:
            loader.paused = False # 恢复播放

    # --- 鼠标回调 ---
    def mouse_cb(e, x, y, f, p):
        nonlocal menu_open, tuning_open, tuning_idx, tuning_params, is_typing
        
        # 滚轮处理 (参数调节)
        if e == cv2.EVENT_MOUSEWHEEL:
            if tuning_open:
                delta = cv2.getMouseWheelDelta(f)
                if delta > 0: ui.widgets.scroll_y -= 40
                else: ui.widgets.scroll_y += 40
                return

        # 坐标映射 (处理窗口缩放)
        cw, ch = get_client_rect_size(TextConfig.WINDOW_NAME)
        if cw == 0: return
        scale = min(cw / AppConfig.W, ch / AppConfig.H)
        render_w, render_h = int(AppConfig.W * scale), int(AppConfig.H * scale)
        off_x, off_y = (cw - render_w) // 2, (ch - render_h) // 2
        
        if render_w > 0 and render_h > 0:
            lx = int((x - off_x) / scale)
            ly = int((y - off_y) / scale)
        else:
            lx, ly = -1, -1

        if 0 <= lx <= AppConfig.W and 0 <= ly <= AppConfig.H:
            ui.update_hover(lx, ly, menu_open, 4, tuning_open)
            
            if e == cv2.EVENT_LBUTTONDOWN:
                hit = ui.hit_test(lx, ly, tuning_open)
                is_typing = (hit == 'height_input')
                
                # 弹窗逻辑
                if tuning_open:
                    if hit == 'modal_close' or hit == 'modal_cancel': 
                        tuning_open = False
                    
                    elif hit == 'btn_calib':
                        # [新增] 点击校准按钮
                        open_sprite_editor()
                        
                    elif hit == 'modal_confirm':
                        # 保存参数到 AlgoConfig
                        for k, v in tuning_params.items():
                            try:
                                if v == 'True': val = True
                                elif v == 'False': val = False
                                else: val = float(v) if '.' in v else int(v)
                                setattr(AlgoConfig, k, val)
                            except: pass
                        tuning_open = False
                        
                    elif hit and hit.startswith('input_'):
                        idx = int(hit.split('_')[1])
                        flat_list = flatten_tuning_tree(engine.current_mode, tuning_params)
                        if 0 <= idx < len(flat_list):
                            item = flat_list[idx]
                            if item['type'] == 'bool':
                                curr = tuning_params.get(item['key'], 'True')
                                new_val = 'False' if curr == 'True' else 'True'
                                tuning_params[item['key']] = new_val
                                try: setattr(AlgoConfig, item['key'], (new_val == 'True'))
                                except: pass
                                tuning_idx = -1 
                            elif item['type'] == 'input':
                                tuning_idx = idx
                    return

                # 主界面按钮逻辑
                if hit == 'menu_btn': 
                    menu_open = not menu_open
                    
                elif menu_open and hit and hit.startswith('menu_item_'):
                    idx = int(hit.split('_')[2])
                    modes = [TextConfig.ACT_PRESS, TextConfig.ACT_SQUAT, TextConfig.ACT_RAISE, TextConfig.ACT_LUNGE]
                    if 0 <= idx < len(modes): engine.set_mode(modes[idx]); menu_open = False
                
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
                    if w>0: loader.seek((lx-rect[0])/w)
                    
                elif hit == 'btn_tune':
                    tuning_open = True
                    # 准备参数副本
                    groups = TUNING_TREE.get(engine.current_mode, [])
                    tuning_params = {}
                    for grp in groups:
                        if grp.get('switch'): tuning_params[grp['switch']] = str(getattr(AlgoConfig, grp['switch']))
                        if grp.get('prio'): tuning_params[grp['prio']] = str(getattr(AlgoConfig, grp['prio']))
                        for p, _ in grp['params']: tuning_params[p] = str(getattr(AlgoConfig, p))
                    tuning_idx = -1
                    
                elif menu_open and hit is None: 
                    menu_open = False

    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)
    
    # =====================================================================
    # 主循环
    # =====================================================================
    while loader.running:
        ret, frame = loader.read()
        if not ret or frame is None: 
            blank = np.zeros((AppConfig.H, AppConfig.W, 3), dtype=np.uint8)
            cv2.putText(blank, "No Signal / Loading...", (50, AppConfig.H//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.imshow(TextConfig.WINDOW_NAME, blank)
            if cv2.waitKey(1) & 0xFF == 27: break
            time.sleep(0.01); continue
            
        # 尺寸适配
        h, w = frame.shape[:2]
        if h != AppConfig.H: 
            scale = AppConfig.H / h; w = int(w * scale); h = AppConfig.H
            frame = cv2.resize(frame, (w, h))
        
        # 左右分屏准备
        f_l = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8)
        if w >= AppConfig.HALF_W: 
            sx = (w - AppConfig.HALF_W) // 2
            f_l = frame[:, sx : sx + AppConfig.HALF_W].copy()
        else: 
            sx = (AppConfig.HALF_W - w) // 2
            f_l[:, sx : sx + w] = frame
        
        f_l = cv2.flip(f_l, 1) # 镜像
        f_r = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8) + 20 # 右侧背景
        
        # 计算 FPS
        curr_time = time.time()
        fps = int(1/(curr_time-prev_time)) if curr_time>prev_time else 0
        prev_time = curr_time
        
        # MediaPipe 推理
        res = pose.process(cv2.cvtColor(f_l, cv2.COLOR_BGR2RGB))
        pts = {}
        if res.pose_landmarks:
             # 映射关键点
             for i, n in {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',27:'la',28:'ra',0:'nose'}.items():
                 lm = res.pose_landmarks.landmark[i]
                 if lm.visibility > 0.5: 
                     pts[n] = (int(lm.x*AppConfig.HALF_W), int(lm.y*AppConfig.H))
        
        # 引擎更新
        vis, pts = engine.update(pts, None, float(h_str) if h_str else 180.0)
        data = engine.get_ui_data()
        
        # 绘制层
        # 左侧：原始骨骼 (Debug用)
        ui.draw_skeleton(f_l, pts, is_avatar=False)
        ui.draw_visuals(f_l, vis)
        
        # 右侧：真实人体 Avatar [关键] is_avatar=True
        ui.draw_skeleton(f_r, pts, is_avatar=True)
        ui.draw_visuals(f_r, vis)
        
        # 视频条
        if loader.is_video: 
            ui.draw_video_bar(f_l, loader.get_progress(), loader.paused)
        
        # 合成最终画面
        final = np.hstack((f_l, f_r))
        
        # 绘制 HUD
        ui.draw_all_text_layers(
            final, data['mode'], data['count'], fps, menu_open, h_str, is_typing, 
            data['msg'], data['msg_col'], data['errs'], data['bad'], 
            loader.is_video, loader.paused
        )
        
        # 绘制弹窗
        if tuning_open or ui.modal_anim_val > 0.01:
            ui.draw_tuning_modal(final, engine.current_mode, tuning_params, tuning_idx, tuning_open)
            
        # 右下角调试信息 (包含 Drift 状态)
        if 'debug_inc' in pts and 'debug_residual' in pts and 'debug_comp_on' in pts:
            comp_state = "ON" if pts['debug_comp_on'] else "OFF"
            state_color = (0, 255, 255) if pts['debug_comp_on'] else (180, 180, 180)
            dbg_text = f"INC:{pts['debug_inc']:.0f}  COMP:{pts['debug_residual']:.1f}%  Drift:{comp_state}"
            tx = AppConfig.W - 380; ty = AppConfig.H - 20
            cv2.putText(final, dbg_text, (tx+1, ty+1), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
            cv2.putText(final, dbg_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
        
        # 显示到窗口
        win_w, win_h = get_client_rect_size(TextConfig.WINDOW_NAME)
        scale_w = win_w / AppConfig.W
        scale_h = win_h / AppConfig.H
        scale = min(scale_w, scale_h)
        rw, rh = int(AppConfig.W * scale), int(AppConfig.H * scale)
        off_x, off_y = (win_w - rw) // 2, (win_h - rh) // 2
        
        final_disp = np.zeros((win_h, win_w, 3), dtype=np.uint8)
        if rw > 0 and rh > 0:
            final_disp[off_y:off_y+rh, off_x:off_x+rw] = cv2.resize(final, (rw, rh))
        cv2.imshow(TextConfig.WINDOW_NAME, final_disp)
        
        # 按键处理
        key = cv2.waitKey(1)
        if key & 0xFF == 27: break # ESC
        
        # 快捷键 'D': 切换漂移补偿
        if key == ord('d') or key == ord('D'):
            AlgoConfig.ENABLE_HIP_DRIFT_COMP = not AlgoConfig.ENABLE_HIP_DRIFT_COMP
            
        # 快捷键 'C': 打开火柴人校准器
        if key == ord('c') or key == ord('C'):
            open_sprite_editor()
        
        # 输入框处理
        if is_typing:
            if key == 8: h_str = h_str[:-1]
            elif 48 <= key <= 57 and len(h_str)<3: h_str += chr(key)
            elif key == 13: is_typing = False
            
        # 参数输入处理
        if tuning_open and tuning_idx != -1:
            flat_list = flatten_tuning_tree(engine.current_mode, tuning_params)
            if 0 <= tuning_idx < len(flat_list):
                item = flat_list[tuning_idx]
                if item['type'] == 'input':
                    curr_val = tuning_params[item['key']]
                    if key == 8: tuning_params[item['key']] = curr_val[:-1]
                    elif (48 <= key <= 57 or key == 46 or key == 45): # 数字, 点, 负号
                        tuning_params[item['key']] += chr(key)
                    elif key == 13: 
                        try: setattr(AlgoConfig, item['key'], float(curr_val) if '.' in curr_val else int(curr_val))
                        except: pass
                        tuning_open = False

    loader.release(); cv2.destroyAllWindows()

if __name__ == "__main__": main()