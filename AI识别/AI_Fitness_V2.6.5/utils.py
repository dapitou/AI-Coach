import cv2
import numpy as np
import math
import time
import threading
from config import AppConfig

class CameraLoader:
    def __init__(self, src=0, w=1280, h=720):
        self.w, self.h = w, h
        self.ret = False
        self.frame = None
        self.running = True
        self.lock = threading.Lock()
        
        self.is_video = False
        self.video_len = 0
        self.current_pos = 0
        self.seek_req = -1 
        self.src = src
        
        # [新增] 暂停状态
        self.paused = False
        
        self.open_source(src)
        
        self.t = threading.Thread(target=self._update, daemon=True)
        self.t.start()

    def open_source(self, src):
        with self.lock:
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
            
            self.current_pos = 0
            self.seek_req = -1
            self.frame = None 
            self.paused = False # 切换源默认播放
            
            if isinstance(src, int):
                self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) 
            else:
                self.cap = cv2.VideoCapture(src)
            
            if isinstance(src, str):
                self.is_video = True
                self.video_len = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            else:
                self.is_video = False
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.w)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.h)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            self.src = src

    def switch_source(self, src):
        self.open_source(src)

    def seek(self, ratio):
        if self.is_video:
            self.seek_req = max(0.0, min(1.0, ratio))
    
    def toggle_pause(self):
        """切换播放/暂停"""
        if self.is_video:
            self.paused = not self.paused

    def get_progress(self):
        if not self.is_video or self.video_len == 0: return 0.0
        return self.current_pos / self.video_len

    def _update(self):
        while self.running:
            # 处理 Seek (即使暂停也要允许 Seek 并更新一帧)
            force_read = False
            if self.is_video and self.seek_req >= 0:
                target_frame = int(self.seek_req * self.video_len)
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, target_frame)
                self.seek_req = -1
                force_read = True # Seek后强制读取一帧以更新画面

            # 暂停逻辑
            if self.is_video and self.paused and not force_read:
                time.sleep(0.03)
                continue

            if self.cap.isOpened():
                ret, frame = self.cap.read()
            else:
                ret, frame = False, None
            
            if not ret:
                if self.is_video and self.video_len > 0:
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    time.sleep(0.1)
                    continue
            
            if self.is_video:
                self.current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)

            with self.lock:
                self.ret, self.frame = ret, frame
            
            time.sleep(0.005 if not self.is_video else 0.03)

    def read(self):
        with self.lock:
            # 如果暂停中，返回最后一帧
            if self.frame is None: return False, None
            return True, self.frame.copy()

    def release(self):
        self.running = False
        self.t.join()
        if hasattr(self, 'cap'):
            self.cap.release()

# (GeomUtils, PointSmoother, SoundManager 保持不变，省略以节省篇幅)
# 请务必保留原文件中的这些类
class GeomUtils:
    @staticmethod
    def dist(p1, p2):
        return math.hypot(p1[0]-p2[0], p1[1]-p2[1])

    @staticmethod
    def dist_3d(p1, p2):
        return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2)

    @staticmethod
    def is_vertical(p1, p2, tolerance):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return False
        return math.degrees(math.atan(dx / dy)) < tolerance

    @staticmethod
    def calc_inclination(p1, p2):
        dx = abs(p1[0] - p2[0])
        dy = abs(p1[1] - p2[1])
        if dy == 0: return 90.0
        return math.degrees(math.atan(dx/dy))

class PointSmoother:
    def __init__(self, alpha=0.5):
        self.prev_pts = {}
        self.min_alpha = 0.3
        self.max_alpha = 0.95

    def filter(self, current_pts):
        if not self.prev_pts:
            self.prev_pts = current_pts
            return current_pts
        smoothed = {}
        for k, v in current_pts.items():
            if v is None: 
                smoothed[k] = None
                continue
            if k not in self.prev_pts or self.prev_pts[k] is None:
                smoothed[k] = v
            else:
                prev = self.prev_pts[k]
                dist = math.hypot(v[0]-prev[0], v[1]-prev[1])
                dynamic_alpha = self.min_alpha + (self.max_alpha - self.min_alpha) * min(dist / 10.0, 1.0)
                sx = int(dynamic_alpha * v[0] + (1 - dynamic_alpha) * prev[0])
                sy = int(dynamic_alpha * v[1] + (1 - dynamic_alpha) * prev[1])
                smoothed[k] = (sx, sy)
        self.prev_pts = smoothed
        return smoothed

class SoundManager:
    def __init__(self):
        self.sounds = {}
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.HAS_AUDIO = True
            self._gen_sounds()
        except:
            self.HAS_AUDIO = False

    def _gen_wave(self, freq, dur, type='sine'):
        try:
            import pygame
            sr = 44100
            t = np.linspace(0, dur, int(sr*dur), False)
            if type == 'sine': w = np.sin(2*np.pi*freq*t)
            elif type == 'square': w = np.sign(np.sin(2*np.pi*freq*t))
            w *= np.linspace(1, 0, len(t)) * 0.5
            audio = (w * 32767).astype(np.int16)
            return pygame.sndarray.make_sound(np.column_stack((audio, audio)))
        except: return None

    def _gen_sounds(self):
        if not self.HAS_AUDIO: return
        self.sounds['count'] = self._gen_wave(880, 0.1)
        self.sounds['error'] = self._gen_wave(150, 0.4, 'square')
        try:
            import pygame
            t = np.linspace(0, 0.6, int(44100*0.6), False)
            w = (np.sin(2*np.pi*523*t) + np.sin(2*np.pi*659*t) + np.sin(2*np.pi*784*t))/3
            w *= np.linspace(1, 0, len(t)) * 0.5
            audio = (w * 32767).astype(np.int16)
            self.sounds['success'] = pygame.sndarray.make_sound(np.column_stack((audio, audio)))
        except: pass

    def play(self, name):
        if self.HAS_AUDIO and name in self.sounds:
            try:
                import config
                self.sounds[name].set_volume(config.AppConfig.VOL)
                self.sounds[name].play()
            except: pass