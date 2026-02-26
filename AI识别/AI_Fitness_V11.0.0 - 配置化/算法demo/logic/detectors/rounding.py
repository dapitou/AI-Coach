from logic.detectors.abstract import BaseDetector
from core.config import ColorConfig

class RoundingDetector(BaseDetector):
    def __init__(self, error_key='rounding', msg="", color=ColorConfig.NEON_RED):
        super().__init__(error_key, msg, color)
        # 弓背的阈值通常由 SpineAnalyzer 内部计算，这里主要负责消费结果并生成特效

    def detect(self, pts, shared, cycle_flags):
        vis = []
        
        # 核心逻辑：消费 pts['rounding_bad'] 标记
        if pts.get('rounding_bad', False):
            cycle_flags[self.error_key] = False
            
            # 绘制红色脊柱线
            if pts.get('neck') and pts.get('thorax') and pts.get('waist') and pts.get('hip'):
                vis.append({
                    'cmd': 'polyline', 
                    'pts': [pts['neck'], pts['thorax'], pts['waist'], pts['hip']], 
                    'color': self.color, 
                    'thick': 4
                })
                # 核心点高亮
                vis.append({'cmd':'circle', 'center':pts['thorax'], 'radius':8, 'color':self.color, 'thick':-1})
                vis.append({'cmd':'circle', 'center':pts['waist'], 'radius':8, 'color':self.color, 'thick':-1})
            
            return vis, True
            
        return vis, False