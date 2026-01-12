from logic.detectors.abstract import BaseDetector
from utils.geometry import GeomUtils
from core.config import ColorConfig

class ValgusDetector(BaseDetector):
    def __init__(self, ratio_threshold, check_mode='inner', error_key='valgus', msg="", color=ColorConfig.NEON_RED):
        """
        :param ratio_threshold: 膝盖间距/髋部间距 的阈值
        :param check_mode: 'inner' (防止内扣, 膝距不能太小) 或 'outer' (防止外撇, 膝距不能太大)
        """
        super().__init__(error_key, msg, color)
        self.threshold = ratio_threshold
        self.mode = check_mode

    def detect(self, pts, shared, cycle_flags):
        vis = []
        if not (pts.get('lk') and pts.get('rk') and pts.get('lh') and pts.get('rh')):
            return vis, False

        # 计算宽度
        knee_w = abs(pts['lk'][0] - pts['rk'][0])
        hip_w = abs(pts['lh'][0] - pts['rh'][0])
        
        # 避免除零
        if hip_w < 1: hip_w = 1
        
        ratio = knee_w / hip_w
        is_error = False
        
        if self.mode == 'inner':
            # 内扣：膝盖太近 (ratio < threshold)
            if ratio < self.threshold: is_error = True
        else:
            # 外撇 (可选)
            pass

        if is_error:
            cycle_flags[self.error_key] = False
            
            # 特效：在膝盖画向外的箭头，提示打开
            # 左膝向左，右膝向右
            vis.append({'cmd':'arrow', 'start':pts['lk'], 'target':(-1, 0), 'color':self.color, 'gap':20, 'mode':'vec'})
            vis.append({'cmd':'arrow', 'start':pts['rk'], 'target':(1, 0), 'color':self.color, 'gap':20, 'mode':'vec'})
            # 膝盖红点
            vis.append({'cmd':'circle', 'center':pts['lk'], 'radius':10, 'color':self.color, 'thick':-1})
            vis.append({'cmd':'circle', 'center':pts['rk'], 'radius':10, 'color':self.color, 'thick':-1})
            
            return vis, True

        return vis, False