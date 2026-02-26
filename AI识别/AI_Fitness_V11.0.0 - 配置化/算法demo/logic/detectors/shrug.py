from logic.detectors.abstract import BaseDetector
from core.config import ColorConfig

class ShrugDetector(BaseDetector):
    def __init__(self, compression_threshold, error_key='shrug', msg="", color=ColorConfig.NEON_RED):
        super().__init__(error_key, msg, color)
        self.threshold = compression_threshold
        # [New] 基准高度 (鼻-肩垂直距离)
        self.ref_h = 0.0

    def set_reference(self, pts):
        """
        [New] 设置基准距离。
        应在动作最低点(放松态)持续调用。
        """
        h = self._get_vertical_dist(pts)
        if h > 0:
            self.ref_h = h

    def reset(self):
        self.ref_h = 0.0

    def _get_vertical_dist(self, pts):
        if not pts.get('nose'): return 0.0
        
        # 寻找可见的肩膀
        shoulders_y = []
        if pts.get('ls'): shoulders_y.append(pts['ls'][1])
        if pts.get('rs'): shoulders_y.append(pts['rs'][1])
        
        if not shoulders_y: return 0.0
        
        # 计算双肩中点Y (如果只有一个肩，就用一个)
        avg_shoulder_y = sum(shoulders_y) / len(shoulders_y)
        nose_y = pts['nose'][1]
        
        # 垂直距离 = 肩Y - 鼻Y (图像坐标系Y向下增大，肩在下，数值大)
        dist = avg_shoulder_y - nose_y
        return dist

    def detect(self, pts, shared, cycle_flags):
        vis = []
        
        # 如果没有基准值，无法检测
        if self.ref_h < 10: return vis, False

        curr_h = self._get_vertical_dist(pts)
        if curr_h <= 0: return vis, False
        
        # 计算压缩比: (基准 - 当前) / 基准
        # 正常推举时，头和身体相对静止，H应该变化不大。
        # 耸肩时，肩向上(Y减小)，H减小，diff变大。
        diff = self.ref_h - curr_h
        compression = diff / self.ref_h
        
        if compression > self.threshold:
            cycle_flags[self.error_key] = False
            
            # 特效
            if pts.get('ls'):
                start_pt = (pts['ls'][0], pts['ls'][1] - 60)
                vis.append({'cmd':'arrow', 'start':start_pt, 'target':(0, 1), 'color':self.color, 'gap':0, 'len':40, 'mode':'vec'})
                vis.append({'cmd':'circle', 'center':pts['ls'], 'radius':8, 'color':self.color, 'thick':-1})
            if pts.get('rs'):
                start_pt = (pts['rs'][0], pts['rs'][1] - 60)
                vis.append({'cmd':'arrow', 'start':start_pt, 'target':(0, 1), 'color':self.color, 'gap':0, 'len':40, 'mode':'vec'})
                vis.append({'cmd':'circle', 'center':pts['rs'], 'radius':8, 'color':self.color, 'thick':-1})
            
            return vis, True

        return vis, False