import cv2
import threading
import time

class CameraLoader:
    def __init__(self, src=0, w=1280, h=720):
        self.cap = cv2.VideoCapture(src)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
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
            self.current_pos = 0; self.seek_req = -1; 
            self.ret = False 
            self.frame = None
            self.paused = False
            
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
        # [Fix] Removed unused 'src' argument
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
        with self.lock:
            return self.ret, self.frame.copy() if self.frame is not None else None

    def release(self):
        self.running = False
        self.cap.release()