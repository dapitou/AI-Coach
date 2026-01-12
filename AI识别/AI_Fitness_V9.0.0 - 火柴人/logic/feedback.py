from core.config import TextConfig, ColorConfig

class FeedbackSystem:
    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.history = {} # {err_key: [bool, bool...]}
        self.active_feedback = set()
        self.error_counts = {}
        self.bad_reps = 0
        self.current_rep_has_error = False

    def reset(self):
        self.history = {}
        self.active_feedback = set()
        self.error_counts = {}
        self.bad_reps = 0
        self.current_rep_has_error = False

    def process_error(self, err_key, is_good, block_feedback=False, set_msg_callback=None):
        if err_key not in self.history: self.history[err_key] = []
        self.history[err_key].append(is_good)
        if len(self.history[err_key]) > 5: self.history[err_key].pop(0)

        if not is_good:
            self.current_rep_has_error = True
            self.error_counts[err_key] = self.error_counts.get(err_key, 0) + 1

        # Trigger: 2 consecutive bad
        if len(self.history[err_key]) >= 2:
            if not self.history[err_key][-1] and not self.history[err_key][-2]:
                if not block_feedback:
                    self.active_feedback.add(err_key)

        # Release: 1 good
        if is_good and (err_key in self.active_feedback):
            self.active_feedback.remove(err_key)
            self.sound.play('success')
            if set_msg_callback:
                set_msg_callback(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, dur=1.5, priority=2)

        # Continuous feedback sound
        if (err_key in self.active_feedback) and not is_good:
             self.sound.play('error')

    def end_cycle(self, cycle_flags):
        self.current_rep_has_error = False
        
        # Determine if any current errors exist
        has_current_bad = False
        for k, v in cycle_flags.items():
            if not v: has_current_bad = True
            
        if has_current_bad: self.bad_reps += 1
        
        if not self.active_feedback:
            self.sound.play('count')