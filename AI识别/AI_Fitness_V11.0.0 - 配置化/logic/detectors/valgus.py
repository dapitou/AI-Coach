from logic.detectors.abstract import BaseDetector

class ValgusDetector(BaseDetector):
    """
    膝盖内扣检测器 (纯逻辑版)
    
    职责：仅负责计算膝盖与髋部的宽度比，判断是否存在内扣风险。
    不负责任何特效渲染（特效由 SquatExercise 主类接管）。
    """
    def __init__(self, ratio_threshold, check_mode='inner', error_key='valgus', msg="", color=None):
        """
        :param ratio_threshold: 膝盖间距/髋部间距 的阈值
        :param check_mode: 'inner' (防止内扣)
        """
        # 这里的 msg 和 color 已经不再被内部使用，但保留参数位以兼容 BaseDetector 调用
        super().__init__(error_key, msg, color)
        self.threshold = ratio_threshold
        self.mode = check_mode

    def detect(self, pts, shared, cycle_flags):
        """
        :return: (vis, is_error) 
                 vis: 始终为空列表 (渲染由主类负责)
                 is_error: True 表示当前帧存在内扣，False 表示正常
        """
        vis = [] # [Optimization] 始终返回空，不再负责画图
        
        # 1. 关键点检查
        if not (pts.get('lk') and pts.get('rk') and pts.get('lh') and pts.get('rh')):
            return vis, False

        # 2. 核心计算 (标准不变: 膝宽 / 髋宽)
        knee_w = abs(pts['lk'][0] - pts['rk'][0])
        hip_w = abs(pts['lh'][0] - pts['rh'][0])
        
        # 避免除零保护
        if hip_w < 1: hip_w = 1.0
        
        ratio = knee_w / hip_w
        is_error = False
        
        # 3. 阈值判定
        if self.mode == 'inner':
            # 内扣：膝盖太近 (ratio < threshold)
            if ratio < self.threshold: 
                is_error = True
        
        # 4. 状态更新
        # 虽然主类可能传入了空字典屏蔽此操作，但保留此行符合 Detect 接口规范
        if is_error:
            cycle_flags[self.error_key] = False

        # [Optimization] 直接返回结果，不再生成任何 arrow/circle 特效
        return vis, is_error