from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
# Import Detectors
from logic.detectors.rounding import RoundingDetector
from logic.detectors.valgus import ValgusDetector

class SquatExercise(BaseExercise):
    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        # [New] Register Detectors
        self.add_detector(RoundingDetector(
            error_key='rounding',
            msg=TextConfig.ERR_SQUAT_ROUNDING
        ))
        
        self.add_detector(ValgusDetector(
            ratio_threshold=AlgoConfig.VALGUS_RATIO,
            check_mode='inner',
            error_key='valgus',
            msg=TextConfig.ERR_SQUAT_VALGUS
        ))

    def process(self, pts, shared):
        vis = []
        if not (pts.get('hip') and pts.get('lk') and pts.get('rk')):
            return vis

        # 1. Run Detectors
        # Only run Valgus check if we are squatting down a bit (using shared base if available, or simplified check)
        # For simplicity, always run, detector handles safety? 
        # ValgusDetector handles basic coord existence. 
        # Squat logic usually needs to know if we are 'deep enough' to start checking valgus.
        # Let's trust the logic: if we are in "down" stage, check it.
        
        if self.stage == "down":
             vis.extend(self.run_detectors(pts, shared))
        else:
             # Just rounding check
             # Manually running specific detector? No, run_detectors runs all. 
             # We can filter inside detector or just let it run (rounding always bad).
             # Valgus usually only bad under load.
             # Let's adhere to simple: Run all. If Valgus triggers while standing, it's weird but valid feedback.
             # Or we can conditionally run:
             pass 
             
        # Actually, let's just run them. Rounding is always valid. Valgus is valid if knees buckle standing too.
        vis.extend(self.run_detectors(pts, shared))

        # 2. Main Logic
        hip_y = pts['hip'][1]
        
        # Init ref
        if not hasattr(self, 'base_hip_y'): self.base_hip_y = hip_y
        
        # State Machine
        if self.stage == "start":
            if hip_y > self.base_hip_y + AlgoConfig.SQUAT_DOWN_TH_PIXEL:
                self.stage = "down"
                self.min_hip_y = hip_y # Track depth
        elif self.stage == "down":
            self.min_hip_y = max(self.min_hip_y, hip_y)
            if hip_y < self.base_hip_y + 50:
                self.stage = "start"
                
                # Check Depth
                knee_y = (pts['lk'][1] + pts['rk'][1]) / 2
                # If deepest point didn't reach knee height approx
                if self.min_hip_y < knee_y - 50: # Simple threshold
                    self.cycle_flags['depth'] = False
                else:
                    self.cycle_flags['depth'] = True
                    
                self.counter += 1
                self._end_cycle(['rounding', 'valgus', 'depth'])

        # 3. Depth Feedback (Specific)
        if self.stage == "down":
            knee_y = (pts['lk'][1] + pts['rk'][1]) / 2
            if hip_y < knee_y - 50:
                # Show depth guide line
                vis.append({'cmd':'line', 'style':'dash', 'start':(pts['hip'][0]-100, int(knee_y)), 'end':(pts['hip'][0]+100, int(knee_y)), 'color':ColorConfig.NEON_BLUE})
            else:
                # Good depth
                vis.append({'cmd':'check', 'center':pts['hip'], 'color':ColorConfig.NEON_GREEN})

        return vis