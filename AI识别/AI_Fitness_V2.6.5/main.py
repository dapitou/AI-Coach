import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
import tkinter as tk
# [新增] 引入 ctypes 用于修复 Windows 缩放问题
import ctypes
from tkinter import filedialog

from config import AppConfig, ColorConfig, TextConfig
from utils import CameraLoader, SoundManager
from ui import UIRenderer
from logic_engine import LogicEngine

def main():
    # [核心修复] 告诉 Windows 该程序感知高 DPI，禁止系统自动缩放
    # 这能解决录屏裁剪、鼠标坐标偏移、画面模糊等一系列问题
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

    root = tk.Tk()
    root.withdraw() 
    
    cam_loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(1.0)
    
    pose = mp.solutions.pose.Pose(
        min_detection_confidence=0.6, 
        min_tracking_confidence=0.6,
        model_complexity=1
    )
    
    sound_mgr = SoundManager()
    engine = LogicEngine(sound_mgr)
    renderer = UIRenderer()
    
    # [优化] 窗口设置
    cv2.namedWindow(TextConfig.WINDOW_NAME, cv2.WINDOW_NORMAL)
    # 强制设置初始窗口大小，确保与逻辑分辨率一致
    cv2.resizeWindow(TextConfig.WINDOW_NAME, AppConfig.W, AppConfig.H)
    
    menu_open = False
    prev_time = time.time()
    fps = 0
    user_height_str = "180"
    is_typing = False
    
    def mouse_cb(e, x, y, f, p):
        nonlocal menu_open, is_typing
        renderer.update_hover(x, y, menu_open)
        
        if cam_loader.is_video and renderer.hover["seek_bar"]:
            if e == cv2.EVENT_LBUTTONDOWN or (e == cv2.EVENT_MOUSEMOVE and (f & cv2.EVENT_FLAG_LBUTTON)):
                bar_start = 60
                bar_width = AppConfig.W - 80
                ratio = (x - bar_start) / bar_width
                cam_loader.seek(ratio)
                return
            
        if cam_loader.is_video and renderer.hover["btn_play"] and e == cv2.EVENT_LBUTTONDOWN:
            cam_loader.toggle_pause()
            return

        if e == cv2.EVENT_LBUTTONDOWN:
            if renderer.hover["btn_cam"]:
                cam_loader.switch_source(0)
                return
            if renderer.hover["btn_video"]:
                root.attributes('-topmost', True)
                file_path = filedialog.askopenfilename(filetypes=[("Video", "*.mp4 *.avi *.mov")])
                root.attributes('-topmost', False)
                if file_path:
                    cam_loader.switch_source(file_path)
                return

            if 260 < x < 480 and 20 < y < 70:
                is_typing = True
                menu_open = False
            else:
                is_typing = False
                if x < 240 and y < 70: 
                    menu_open = not menu_open
                elif menu_open and x < 240:
                    if 75 < y < 130: engine.set_mode(TextConfig.ACT_PRESS)
                    elif 130 < y < 185: engine.set_mode(TextConfig.ACT_SQUAT)
                    elif 185 < y < 240: engine.set_mode(TextConfig.ACT_RAISE)
                    elif 240 < y < 295: engine.set_mode(TextConfig.ACT_LUNGE)
                    menu_open = False

    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)

    while cam_loader.running:
        ret, frame = cam_loader.read()
        if not ret or frame is None: 
            time.sleep(0.01)
            continue
            
        if not cam_loader.is_video:
            frame = cv2.flip(frame, 1)
        
        curr_time = time.time()
        if curr_time - prev_time > 0: 
            fps = int(1 / (curr_time - prev_time))
        prev_time = curr_time
        
        target_h, target_w = AppConfig.H, AppConfig.HALF_W
        h, w = frame.shape[:2]
        
        scale = max(target_h / h, target_w / w)
        rw, rh = int(w * scale), int(h * scale)
        resized = cv2.resize(frame, (rw, rh))
        
        dy = (rh - target_h) // 2
        dx = (rw - target_w) // 2
        dy = max(0, dy)
        dx = max(0, dx)
        
        f_l = resized[dy:dy+target_h, dx:dx+target_w]
        if f_l.shape[0] != target_h or f_l.shape[1] != target_w:
            f_l = cv2.resize(f_l, (target_w, target_h))

        res = pose.process(cv2.cvtColor(f_l, cv2.COLOR_BGR2RGB))
        pts, hints = {}, []
        world_pts = None
        vis_scores = []
        
        if res.pose_landmarks:
            vis_scores = [lm.visibility for lm in res.pose_landmarks.landmark]
            imap = {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',
                    27:'la',28:'ra',29:'lhe',30:'rhe',31:'lt',32:'rt',0:'nose', 7:'le_ear', 8:'re_ear'}
            for i, n in imap.items():
                lm = res.pose_landmarks.landmark[i]
                pts[n] = (int(lm.x * target_w), int(lm.y * target_h))
            world_pts = res.pose_world_landmarks.landmark
            
            try: h_val = float(user_height_str)
            except: h_val = 180.0
            
            hints, pts = engine.update(pts, world_pts, vis_scores, h_val)

        f_r = np.zeros((target_h, target_w, 3), dtype=np.uint8)
        f_r[:] = ColorConfig.BG
        cv2.line(f_r, (0,0), (0,target_h), ColorConfig.GRID, 1)
        
        renderer.draw_skeleton(f_l, pts)
        renderer.draw_skeleton(f_r, pts, is_avatar=True)
        for t in [f_l, f_r]: 
            renderer.draw_hints(t, hints)

        final = np.hstack((f_l, f_r))
        
        msg, msg_col = engine.get_msg()
        renderer.draw_all_text_layers(
            final, 
            engine.mode, 
            engine.counter, 
            fps, 
            menu_open, 
            user_height_str, 
            is_typing, 
            msg, 
            msg_col, 
            engine.error_counts, 
            engine.bad_reps,
            cam_loader.is_video
        )

        if cam_loader.is_video:
            prog = cam_loader.get_progress()
            renderer.draw_video_bar(final, prog, cam_loader.paused)

        cv2.imshow(TextConfig.WINDOW_NAME, final)
        
        key = cv2.waitKey(1)
        if key & 0xFF == 27: 
            break
        
        if is_typing:
            if 48 <= key <= 57: 
                if len(user_height_str) < 3: user_height_str += chr(key)
            elif key == 8: 
                user_height_str = user_height_str[:-1]
        
    cam_loader.release()
    cv2.destroyAllWindows()
    try: pygame.quit()
    except: pass

if __name__ == "__main__":
    main()