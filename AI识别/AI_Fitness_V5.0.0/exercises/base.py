import time
from core.config import AlgoConfig, ColorConfig, TextConfig
from logic.feedback import FeedbackSystem
from logic.common_checks import CommonChecks

class BaseExercise:
    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.feedback = FeedbackSystem(sound_mgr)
        self.common = CommonChecks()
        
        self.stage = "start"
        self.counter = 0
        self.bad_reps = 0
        
        self.cycle_flags = {}
        self.current_rep_has_error = False
        self.last_count_time = 0
        
        self.msg = ""
        self.msg_color = ColorConfig.TEXT_DIM
        self.msg_priority = 0
        self.msg_timer = 0

    def process(self, pts, shared):
        return []

    def _set_msg(self, t, c, dur=0, perm=False, priority=0):
        # Priority check: Higher priority overwrites lower
        if priority < self.msg_priority and time.time() < self.msg_timer: return
        
        self.msg, self.msg_color = t, c
        self.msg_timer = (time.time() + dur) if dur > 0 else 0
        self.msg_priority = priority

    def get_msg(self):
        # [Fix] Auto-hide message if timer expired
        if self.msg_timer > 0 and time.time() > self.msg_timer:
            self.msg = ""
            self.msg_priority = 0
            self.msg_timer = 0
            return "", ColorConfig.TEXT_DIM
            
        return self.msg, self.msg_color 

    def _end_cycle(self, keys):
        if time.time() - self.last_count_time < AlgoConfig.COUNT_COOLDOWN: return
        
        self.current_rep_has_error = False
        
        for k in keys:
            is_good = self.cycle_flags.get(k, True)
            self.feedback.process_error(k, is_good, set_msg_callback=self._set_msg)
            
        if any(not self.cycle_flags.get(k, True) for k in keys):
             self.bad_reps += 1
        
        if not self.feedback.active_feedback:
            self.sound.play('count')
            
        self.last_count_time = time.time()
        
    @property
    def active_feedback(self):
        return self.feedback.active_feedback
        
    @property
    def error_counts(self):
        return self.feedback.error_counts