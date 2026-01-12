class BaseExercise:
    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.name = ""
        self.stage = "start"
        self.counter = 0
        self.bad_reps = 0
        self.error_counts = {}
        self.active_errs = set()
        self.curr_rep_error = False
        
    def process(self, pts, shared): return [], ("", (0,0,0)), False
    
    def _trigger_error(self, name):
        if name not in self.active_errs:
            self.active_errs.add(name)
            self.error_counts[name] = self.error_counts.get(name, 0) + 1
            self.curr_rep_error = True
            self.sound.play('error')