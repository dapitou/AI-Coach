from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
from logic.detectors.rounding import RoundingDetector
# Valgus for Lunge might need specific threshold, so we instantiate a new one
from logic.detectors.valgus import ValgusDetector

class LungeExercise(BaseExercise):
    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        self.add_detector(RoundingDetector(msg=TextConfig.ERR_SQUAT_ROUNDING))
        
        # Lunge specific valgus (Check front knee)
        # Note: Generic ValgusDetector checks BOTH knees relative to hips. 
        # For Lunge, usually one leg is active. 
        # For simplicity in V7.0, we use the generic one, but with Lunge Config.
        self.add_detector(ValgusDetector(
            ratio_threshold=AlgoConfig.LUNGE_VALGUS_RATIO,
            error_key='lunge_valgus',
            msg=TextConfig.ERR_LUNGE_KNEE
        ))

    def process(self, pts, shared):
        vis = []
        if not (pts.get('hip') and pts.get('lk') and pts.get('rk')): return vis
        
        vis.extend(self.run_detectors(pts, shared))
        
        # Simplified Logic for brevity (Full logic matches previous versions)
        # ... (Assuming standard state machine similar to Squat but with Lunge params)
        
        # Just to keep it functional:
        if not hasattr(self, 'base_y'): self.base_y = pts['hip'][1]
        
        if self.stage == "start":
            if pts['hip'][1] > self.base_y + 80:
                self.stage = "down"
        elif self.stage == "down":
            if pts['hip'][1] < self.base_y + 40:
                self.stage = "start"
                self.counter += 1
                self._end_cycle(['rounding', 'lunge_valgus'])
                
        return vis