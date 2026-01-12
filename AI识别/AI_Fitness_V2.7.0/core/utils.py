import cv2
import numpy as np
import math
import time
import threading
from .config import AppConfig

class CameraLoader:
    def __init__(self, src=0, w=1280, h=720):
        self.w, self.h = w, h
        self.ret, self.frame = False, None
        self.running = True
        self.lock = threading.Lock()
        self.is_video, self.video_len, self.current_pos = False, 0, 0
        self.seek_req = -1 
        self.src = src
        self.paused = False
        self.open_source(src)
        self.t = threading.Thread(target=self._update, daemon=True)
        self.t.start()

    def open_source(self, src):
        with self.lock:
            if hasattr(self, 'cap') and self.cap is not None: self.cap.release()
            self.current_pos = 0; self.seek_req = -1; self.frame = None; self.paused = False
            if isinstance(src, int): self.cap = cv2.VideoCapture(src, cv2.CAP_DSHOW) 
            else: self.cap = cv2.VideoCapture(src)
            if isinstance(src, str):
                self.is_video = True
                self.video_len = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            else:
                self.is_video = False
                self.cap.set(3, self.w); self.cap.set(4, self.h); self.cap.set(5, 30)
            self.src = src

    def switch_source(self, src): self.open_source(src)
    def seek(self, ratio): 
        if self.is_video: self.seek_req = max(0.0, min(1.0, ratio))
    def toggle_pause(self): 
        if self.is_video: self.paused = not self.paused
    def get_progress(self): 
        return (self.current_pos / self.video_len) if (self.is_video and self.video_len > 0) else 0.0

    def _update(self):
        while self.running:
            force = False
            if self.is_video and self.seek_req >= 0:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, int(self.seek_req * self.video_len))
                self.seek_req = -1; force = True
            
            if self.is_video and self.paused and not force:
                time.sleep(0.03); continue
            
            if self.cap.isOpened(): ret, frame = self.cap.read()
            else: ret, frame = False, None
            
            if not ret:
                if self.is_video and self.video_len > 0: self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0); continue
                else: time.sleep(0.1); continue
            
            if self.is_video: self.current_pos = self.cap.get(cv2.CAP_PROP_POS_FRAMES)
            with self.lock: self.ret, self.frame = ret, frame
            time.sleep(0.005 if not self.is_video else 0.03)

    def read(self):
        with self.lock: return (self.ret, self.frame.copy()) if self.frame is not None else (False, None)
    def release(self):
        self.running = False; self.t.join()
        if hasattr(self, 'cap'): self.cap.release()

class GeomUtils:
    @staticmethod
    def dist(p1, p2): return math.hypot(p1[0]-p2[0], p1[1]-p2[1])
    @staticmethod
    def dist_3d(p1, p2): return math.sqrt((p1.x-p2.x)**2 + (p1.y-p2.y)**2 + (p1.z-p2.z)**2)
    @staticmethod
    def is_vertical(p1, p2, tolerance):
        if abs(p1[1]-p2[1]) == 0: return False
        return math.degrees(math.atan(abs(p1[0]-p2[0])/abs(p1[1]-p2[1]))) < tolerance

class PointSmoother:
    def __init__(self, alpha=0.5):
        self.prev = {}
        self.min_a, self.max_a = 0.3, 0.95
    def filter(self, pts):
        res = {}
        for k, v in pts.items():
            if v is None: res[k] = None; continue
            if k not in self.prev or self.prev[k] is None: res[k] = v
            else:
                dist = math.hypot(v[0]-self.prev[k][0], v[1]-self.prev[k][1])
                a = self.min_a + (self.max_a - self.min_a) * min(dist/10.0, 1.0)
                res[k] = (int(a*v[0]+(1-a)*self.prev[k][0]), int(a*v[1]+(1-a)*self.prev[k][1]))
        self.prev = res
        return res

class SoundManager:
    def __init__(self):
        self.sounds = {}
        try:
            import pygame
            pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
            self.ok = True
            self._gen()
        except: self.ok = False
    def _gen(self):
        if not self.ok: return
        import pygame
        def w(f, d, t='s'):
            s = 44100; x = np.linspace(0, d, int(s*d), False)
            y = np.sin(2*np.pi*f*x) if t=='s' else np.sign(np.sin(2*np.pi*f*x))
            return pygame.sndarray.make_sound((y*0.5*32767).astype(np.int16).reshape(-1, 1).repeat(2, 1))
        self.sounds.update({'count': w(880,0.1), 'error': w(150,0.4,'q'), 'success': w(523,0.6)})
    def play(self, n):
        if self.ok and n in self.sounds:
            try: 
                from .config import AppConfig
                self.sounds[n].set_volume(AppConfig.VOL); self.sounds[n].play()
            except: pass