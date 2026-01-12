import sys
import os
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path: sys.path.insert(0, current_dir)

import cv2
import mediapipe as mp
import numpy as np
import time
import pygame
import tkinter as tk
from tkinter import filedialog
import ctypes

from core.config import AppConfig, ColorConfig, TextConfig
from core.utils import CameraLoader, SoundManager
from core.ui import UIRenderer
from core.spine import SpineAlgo
from exercises.press import PressExercise
from exercises.squat import SquatExercise
from exercises.front_raise import FrontRaiseExercise
from exercises.lunge import LungeExercise

def main():
    try: ctypes.windll.user32.SetProcessDPIAware()
    except: pass
    
    root = tk.Tk(); root.withdraw()
    cam_loader = CameraLoader(0, AppConfig.W, AppConfig.H)
    time.sleep(1.0)
    
    pose = mp.solutions.pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6, model_complexity=1)
    
    sound_mgr = SoundManager()
    renderer = UIRenderer()
    spine_algo = SpineAlgo()
    
    exercises = [
        PressExercise(sound_mgr),
        SquatExercise(sound_mgr),
        FrontRaiseExercise(sound_mgr),
        LungeExercise(sound_mgr)
    ]
    current_ex_idx = 0
    
    cv2.namedWindow(TextConfig.WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(TextConfig.WINDOW_NAME, AppConfig.W, AppConfig.H)
    
    menu_open = False
    prev_time = time.time()
    fps = 0
    user_height_str = "180"
    is_typing = False
    
    class EngineState:
        def __init__(self): self.stage = "start"; self.max_torso_len = 0
    eng_state = EngineState()

    def mouse_cb(e, x, y, f, p):
        nonlocal menu_open, is_typing, current_ex_idx
        renderer.update_hover(x, y, menu_open, len(exercises))
        
        if cam_loader.is_video:
            if renderer.hover['seek_bar'] and (e==cv2.EVENT_LBUTTONDOWN or (e==cv2.EVENT_MOUSEMOVE and (f & cv2.EVENT_FLAG_LBUTTON))):
                cam_loader.seek((x - 60) / (AppConfig.W - 80))
                return
            if renderer.hover['btn_play'] and e==cv2.EVENT_LBUTTONDOWN:
                cam_loader.toggle_pause()
                return

        if e == cv2.EVENT_LBUTTONDOWN:
            if renderer.hover['btn_cam']: cam_loader.switch_source(0); return
            if renderer.hover['btn_video']:
                root.attributes('-topmost', True)
                path = filedialog.askopenfilename(parent=root, filetypes=[("Video", "*.mp4 *.avi *.mov")])
                root.attributes('-topmost', False)
                if path: cam_loader.switch_source(path)
                return
            
            if 260 < x < 480 and 20 < y < 70:
                is_typing = True; menu_open = False; return
            
            is_typing = False
            if x < 240 and y < 70: menu_open = not menu_open
            elif menu_open and x < 240:
                for i in range(len(exercises)):
                    if 75 + i*55 <= y <= 75 + i*55 + 50:
                        current_ex_idx = i; menu_open = False
                        exercises[i].stage = "start"; exercises[i].counter = 0
                        break
    
    cv2.setMouseCallback(TextConfig.WINDOW_NAME, mouse_cb)

    while cam_loader.running:
        ret, frame = cam_loader.read()
        if not ret or frame is None: time.sleep(0.01); continue
            
        if not cam_loader.is_video: frame = cv2.flip(frame, 1)
        
        curr_time = time.time()
        if curr_time - prev_time > 0: fps = int(1 / (curr_time - prev_time))
        prev_time = curr_time
        
        # Crop
        th, tw = AppConfig.H, AppConfig.HALF_W
        h, w = frame.shape[:2]
        scale = max(th/h, tw/w)
        rw, rh = int(w*scale), int(h*scale)
        resized = cv2.resize(frame, (rw, rh))
        dy, dx = (rh-th)//2, (rw-tw)//2
        f_l = cv2.resize(resized[dy:dy+th, dx:dx+tw], (tw, th))

        # AI
        res = pose.process(cv2.cvtColor(f_l, cv2.COLOR_BGR2RGB))
        pts = {}
        if res.pose_landmarks:
            imap = {11:'ls',12:'rs',13:'le',14:'re',15:'lw',16:'rw',23:'lh',24:'rh',25:'lk',26:'rk',
                    27:'la',28:'ra',29:'lhe',30:'rhe',31:'lt',32:'rt',0:'nose', 7:'le_ear', 8:'re_ear'}
            for i, n in imap.items():
                lm = res.pose_landmarks.landmark[i]
                pts[n] = (int(lm.x*tw), int(lm.y*th))
        
        active_ex = exercises[current_ex_idx]
        eng_state.stage = active_ex.stage
        spine_algo.update(eng_state, pts)

        try: h_val = float(user_height_str)
        except: h_val = 180.0
        
        vis_elements, feedback, gate_passed = active_ex.process(pts, {'rounding_bad': pts.get('rounding_bad'), 'max_len': eng_state.max_torso_len})
        
        f_r = np.zeros((th, tw, 3), dtype=np.uint8)
        f_r[:] = ColorConfig.BG
        cv2.line(f_r, (0,0), (0,th), ColorConfig.GRID, 1)
        
        renderer.draw_skeleton(f_l, pts)
        renderer.draw_skeleton(f_r, pts, is_avatar=True)
        renderer.draw_visuals(f_l, vis_elements)

        final = np.hstack((f_l, f_r))
        
        act_names = [e.name for e in exercises]
        renderer.draw_ui_overlay(
            final, active_ex.name, act_names, 
            active_ex.counter, fps, menu_open, user_height_str, is_typing,
            feedback[0], feedback[1], 
            active_ex.error_counts, active_ex.bad_reps,
            cam_loader.is_video, cam_loader.paused
        )
        
        if cam_loader.is_video:
            renderer.draw_video_bar(final, cam_loader.get_progress(), cam_loader.paused)

        cv2.imshow(TextConfig.WINDOW_NAME, final)
        key = cv2.waitKey(1)
        if key & 0xFF == 27: break
        
        if is_typing:
            if 48 <= key <= 57: user_height_str += chr(key)
            elif key == 8: user_height_str = user_height_str[:-1]

    cam_loader.release()
    cv2.destroyAllWindows()
    try: pygame.quit()
    except: pass

if __name__ == "__main__":
    main()