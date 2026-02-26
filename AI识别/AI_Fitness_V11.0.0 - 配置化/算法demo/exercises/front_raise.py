from exercises.base import BaseExercise
from core.config import TextConfig, AlgoConfig
from logic.detectors.shrug import ShrugDetector
from logic.detectors.rounding import RoundingDetector
from utils.geometry import GeomUtils

class FrontRaiseExercise(BaseExercise):
    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        # 保存实例
        self.shrug_detector = ShrugDetector(
            compression_threshold=AlgoConfig.SHRUG_COMPRESSION_TH, 
            msg=TextConfig.ERR_PRESS_SHRUG
        )
        self.add_detector(self.shrug_detector)
        
        self.add_detector(RoundingDetector(msg=TextConfig.ERR_SQUAT_ROUNDING))

    def process(self, pts, shared):
        vis = []
        if not (pts.get('lw') and pts.get('rw') and pts.get('nose')): return vis
        
        vis.extend(self.run_detectors(pts, shared))
        
        wy = (pts['lw'][1]+pts['rw'][1])/2
        sy = (pts['ls'][1]+pts['rs'][1])/2
        
        if self.stage == "start" and wy < sy:
            self.stage = "up"
        elif self.stage == "up" and wy > sy + 100:
            self.stage = "start"
            self.counter += 1
            self._end_cycle(['shrug', 'rounding', 'range'])
            
            # [Update] Reset Detector
            self.shrug_detector.reset()
            
        if self.stage == "up":
            # Range logic if needed
            pass
            
        return vis