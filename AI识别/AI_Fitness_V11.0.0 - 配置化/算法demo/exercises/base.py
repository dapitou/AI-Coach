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
        
        self.detectors = []

    def add_detector(self, detector):
        self.detectors.append(detector)
        self.cycle_flags[detector.error_key] = True

    def run_detectors(self, pts, shared):
        all_vis = []
        for d in self.detectors:
            config_key = f"ENABLE_{d.error_key.upper()}"
            if hasattr(AlgoConfig, config_key):
                if not getattr(AlgoConfig, config_key):
                    continue
            
            if d.error_key not in self.cycle_flags:
                self.cycle_flags[d.error_key] = True
                
            vis, is_err = d.detect(pts, shared, self.cycle_flags)
            all_vis.extend(vis)
        return all_vis

    def process(self, pts, shared):
        return []

    def _set_msg(self, t, c, dur=0, perm=False, priority=0):
        if priority < self.msg_priority and time.time() < self.msg_timer: return
        self.msg, self.msg_color = t, c
        self.msg_timer = (time.time() + dur) if dur > 0 else 0
        self.msg_priority = priority

    def get_msg(self):
        if self.msg_timer > 0 and time.time() > self.msg_timer:
            self.msg = ""
            self.msg_priority = 0
            self.msg_timer = 0
            return "", ColorConfig.TEXT_DIM
        return self.msg, self.msg_color 

    def _end_cycle(self, keys):
        if time.time() - self.last_count_time < AlgoConfig.COUNT_COOLDOWN: return
        
        self.current_rep_has_error = False
        is_bad_rep = False
        
        # Sort by priority
        def get_prio(k):
            map_prio = {
                'arm': 'PRIORITY_PRESS_ARM',
                'shrug': 'PRIORITY_SHRUG',
                'valgus': 'PRIORITY_SQUAT_VALGUS',
                'lunge_valgus': 'PRIORITY_SQUAT_VALGUS',
                'rounding': 'PRIORITY_SQUAT_ROUNDING'
            }
            cfg_name = map_prio.get(k, f"PRIORITY_{k.upper()}")
            return getattr(AlgoConfig, cfg_name, 99)

        sorted_keys = sorted(keys, key=get_prio)
        
        for k in sorted_keys:
            cfg_enable = f"ENABLE_{k.upper()}"
            if hasattr(AlgoConfig, cfg_enable) and not getattr(AlgoConfig, cfg_enable):
                continue

            is_good = self.cycle_flags.get(k, True)
            if not is_good: is_bad_rep = True
            
            self.feedback.process_error(k, is_good, set_msg_callback=self._set_msg)
            
        if is_bad_rep: 
            self.bad_reps += 1
            # [Fix] Play Error Sound if bad rep
            self.sound.play('error') 
        else:
            if not self.feedback.active_feedback:
                self.sound.play('count')
            
        self.last_count_time = time.time()
        
        for k in self.cycle_flags:
            self.cycle_flags[k] = True
        
    @property
    def active_feedback(self):
        return self.feedback.active_feedback
        
    @property
    def error_counts(self):
        return self.feedback.error_counts