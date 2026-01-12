import sys
import os
import platform

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

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
import time
import tkinter as tk
from tkinter import filedialog
from ctypes import windll, byref, Structure, c_long

from core.config import AppConfig, TextConfig, ColorConfig, AlgoConfig, TUNING_TREE
from core.camera import CameraLoader
from core.sound import SoundManager
from ui.renderer import UIRenderer
from utils.geometry import GeomUtils
from utils.smoother import PointSmoother
from logic.spine import SpineAnalyzer
from logic.gatekeeper import Gatekeeper
from exercises import PressExercise, SquatExercise, LungeExercise, FrontRaiseExercise

class RECT(Structure):
    _fields_ = [("left", c_long), ("top", c_long), ("right", c_long), ("bottom", c_long)]

def get_client_rect_size(window_name):
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
        pts = self.smoother.filter(pts)
        
        current_ex = self.exercises[self.current_mode]
        self.spine.analyze(pts, stage=current_ex.stage)
        
        if not self.gatekeeper.check(pts, self.current_mode, current_ex): return [], pts
        
        shared = {
            'max_torso_len': self.spine.get_max_len(),
            'rounding_bad': pts.get('rounding_bad', False),
            'base_shrug_dist': 0 
        }
        vis = current_ex.process(pts, shared)
        if pts.get('rounding_bad') and 'rounding' in current_ex.active_feedback:
            vis.append({'type': 'rounding_guide', 'neck': pts['neck'], 'thorax': pts['thorax'], 'waist': pts['waist'], 'hip': pts['hip']})
        return vis, pts

    def get_ui_data(self):
        ex = self.exercises[self.current_mode]
        msg, col = ex.get_msg()
        return {'mode': self.current_mode, 'count': ex.counter, 'msg': msg, 'msg_col': col, 'errs': ex.feedback.error_counts, 'bad': ex.bad_reps}

def flatten_tuning_tree(mode, params_dict):
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

def main():
    loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(0.1)
    if not loader.ret and not loader.is_video:
        print("Camera not ready."); time.sleep(1.0)
    
    pose = mp.solutions.pose.Pose(min_detection_confidence=0.6, model_complexity=1)
    engine = Engine()
    ui = UIRenderer()
    
    menu_open = False
    tuning_open = False
    tuning_params = {} 
    tuning_idx = -1 
    
    is_typing = False
    h_str = "180"
    fps = 0
    prev_time = time.time()
    
    cv2.namedWindow(TextConfig.WINDOW_NAME, cv2.WINDOW_NORMAL)
    root = tk.Tk(); root.withdraw(); sw, sh = root.winfo_screenwidth(), root.winfo_screenheight(); root.destroy()
    cv2.resizeWindow(TextConfig.WINDOW_NAME, int(sw*0.9), int(sh*0.9))
    cv2.moveWindow(TextConfig.WINDOW_NAME, int(sw*0.05), int(sh*0.05))
    
    def mouse_cb(e, x, y, f, p):
        nonlocal menu_open, tuning_open, tuning_idx, tuning_params, is_typing
        
        if e == cv2.EVENT_MOUSEWHEEL:
            if tuning_open:
                delta = cv2.getMouseWheelDelta(f)
                if delta > 0: ui.widgets.scroll_y -= 40
                else: ui.widgets.scroll_y += 40
                return

        cw, ch = get_client_rect_size(TextConfig.WINDOW_NAME)
        if cw == 0: return
        
        scale_w = cw / AppConfig.W
        scale_h = ch / AppConfig.H
        scale = min(scale_w, scale_h)
        
        render_w = int(AppConfig.W * scale)
        render_h = int(AppConfig.H * scale)
        
        off_x = (cw - render_w) // 2
        off_y = (ch - render_h) // 2
        
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
                
                if tuning_open:
                    if hit == 'modal_close' or hit == 'modal_cancel': tuning_open = False
                    elif hit == 'modal_confirm':
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

                if hit == 'menu_btn': menu_open = not menu_open
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
                    groups = TUNING_TREE.get(engine.current_mode, [])
                    tuning_params = {}
                    for grp in groups:
                        if grp.get('switch'): tuning_params[grp['switch']] = str(getattr(AlgoConfig, grp['switch']))
                        if grp.get('prio'): tuning_params[grp['prio']] = str(getattr(AlgoConfig, grp['prio']))
                        for p, _ in grp['params']: tuning_params[p] = str(getattr(AlgoConfig, p))
                    tuning_idx = -1
                elif menu_open and hit is None: menu_open = False

    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)
    
    while loader.running:
        ret, frame = loader.read()
        if not ret or frame is None: 
            blank = np.zeros((AppConfig.H, AppConfig.W, 3), dtype=np.uint8)
            cv2.putText(blank, "No Signal / Loading...", (50, AppConfig.H//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2)
            cv2.imshow(TextConfig.WINDOW_NAME, blank)
            if cv2.waitKey(1) & 0xFF == 27: break
            time.sleep(0.01); continue
            
        h, w = frame.shape[:2]
        if h != AppConfig.H: scale = AppConfig.H / h; w = int(w * scale); h = AppConfig.H; frame = cv2.resize(frame, (w, h))
        f_l = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8)
        if w >= AppConfig.HALF_W: sx = (w - AppConfig.HALF_W) // 2; f_l = frame[:, sx : sx + AppConfig.HALF_W].copy()
        else: sx = (AppConfig.HALF_W - w) // 2; f_l[:, sx : sx + w] = frame
        f_l = cv2.flip(f_l, 1)
        
        curr_time = time.time(); fps = int(1/(curr_time-prev_time)) if curr_time>prev_time else 0; prev_time = curr_time
        
        res = pose.process(cv2.cvtColor(f_l, cv2.COLOR_BGR2RGB)); pts = {}
        if res.pose_landmarks:
             for i, n in {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',27:'la',28:'ra',0:'nose'}.items():
                 lm = res.pose_landmarks.landmark[i]
                 if lm.visibility > 0.5: pts[n] = (int(lm.x*AppConfig.HALF_W), int(lm.y*AppConfig.H))
        
        vis, pts = engine.update(pts, None, float(h_str) if h_str else 180.0)
        data = engine.get_ui_data()
        
        f_r = np.zeros((AppConfig.H, AppConfig.HALF_W, 3), dtype=np.uint8) + 20
        ui.draw_skeleton(f_l, pts); ui.draw_skeleton(f_r, pts, True)
        ui.draw_visuals(f_l, vis); ui.draw_visuals(f_r, vis)
        if loader.is_video: ui.draw_video_bar(f_l, loader.get_progress(), loader.paused)
        
        final = np.hstack((f_l, f_r))
        ui.draw_all_text_layers(final, data['mode'], data['count'], fps, menu_open, h_str, is_typing, data['msg'], data['msg_col'], data['errs'], data['bad'], loader.is_video, loader.paused)
        
        if tuning_open or ui.modal_anim_val > 0.01:
            ui.draw_tuning_modal(final, engine.current_mode, tuning_params, tuning_idx, tuning_open)
            
        # [修改] 实时参数调试显示 (包含开关状态)
        if 'debug_inc' in pts and 'debug_residual' in pts and 'debug_comp_on' in pts:
            comp_state = "ON" if pts['debug_comp_on'] else "OFF"
            # 颜色：ON=黄, OFF=灰
            state_color = (0, 255, 255) if pts['debug_comp_on'] else (180, 180, 180)
            
            dbg_text = f"INC:{pts['debug_inc']:.0f}  COMP:{pts['debug_residual']:.1f}%  Drift:{comp_state}"
            
            tx = AppConfig.W - 380
            ty = AppConfig.H - 20
            cv2.putText(final, dbg_text, (tx+1, ty+1), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 2)
            cv2.putText(final, dbg_text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, 0.7, state_color, 2)
        
        # Display
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
        
        key = cv2.waitKey(1)
        if key & 0xFF == 27: break
        
        # [新增] 快捷键 'd' 或 'D' 切换漂移补偿开关
        if key == ord('d') or key == ord('D'):
            AlgoConfig.ENABLE_HIP_DRIFT_COMP = not AlgoConfig.ENABLE_HIP_DRIFT_COMP
        
        if is_typing:
            if key == 8: h_str = h_str[:-1]
            elif 48 <= key <= 57 and len(h_str)<3: h_str += chr(key)
            elif key == 13: is_typing = False
            
        if tuning_open and tuning_idx != -1:
            flat_list = flatten_tuning_tree(engine.current_mode, tuning_params)
            if 0 <= tuning_idx < len(flat_list):
                item = flat_list[tuning_idx]
                if item['type'] == 'input':
                    curr_val = tuning_params[item['key']]
                    if key == 8: tuning_params[item['key']] = curr_val[:-1]
                    elif (48 <= key <= 57 or key == 46): tuning_params[item['key']] += chr(key)
                    elif key == 13: 
                        try: setattr(AlgoConfig, item['key'], float(curr_val) if '.' in curr_val else int(curr_val))
                        except: pass
                        tuning_open = False

    loader.release(); cv2.destroyAllWindows()

if __name__ == "__main__": main()