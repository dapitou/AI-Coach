import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import math
import time
from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
from logic.detectors.shrug import ShrugDetector
from utils.geometry import GeomUtils

class LateralRaiseExercise(BaseExercise):
    """
    侧平举动作分析 (Lateral Raise Analysis)
    
    【核心纠错】
    1. 抬肘高度 (Elbow Height): 
       - 目标：肘部抬至与肩部同高 (水平)。
       - 判定：计算大臂与垂直线的夹角，或直接比较 Y 坐标。
    2. 耸肩检测 (Shrug):
       - 复用通用的耸肩检测器，防止斜方肌过度代偿。
    """
    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        # 初始化耸肩检测器
        self.shrug_detector = ShrugDetector(
            compression_threshold=AlgoConfig.SHRUG_COMPRESSION_TH,
            error_key='shrug',
            msg=TextConfig.ERR_PRESS_SHRUG
        )
        
        # --- 核心状态标记 ---
        # [Range]: 初始为 False (默认未达标)，需通过动作证明自己
        self.cycle_flags['range'] = False
        # [Shrug]: 初始为 True (默认合格)，除非检测到耸肩
        self.cycle_flags['shrug'] = True
        
        # [记忆状态] 用于在 Start 阶段保持上一轮的判定结果显示
        self.last_rep_range_ok = True
        
        # [轨迹记录] 存储肘部历史坐标 (timestamp, left_elbow, right_elbow)
        self.elbow_history = []
        self._smooth_le = None
        self._smooth_re = None
        
        # [计时器] 用于熔断机制
        self.up_start_time = 0.0

    def process(self, pts, shared):
        vis = []
        # 安全检查：必须识别到双肩、双肘
        if not (pts.get('ls') and pts.get('rs') and pts.get('le') and pts.get('re')):
            return vis

        # --- 0. 轨迹逻辑 (Elbow Trajectory) --- 增加平滑处理与全局开关
        if AlgoConfig.ENABLE_TRAJECTORY:
            now = time.time()
            le, re = pts['le'], pts['re']
            
            # EMA 平滑处理 (alpha=0.2 保证轨迹丝滑)
            alpha_s = 0.2
            if self._smooth_le is None:
                self._smooth_le, self._smooth_re = le, re
            else:
                self._smooth_le = (int(self._smooth_le[0]*(1-alpha_s) + le[0]*alpha_s), int(self._smooth_le[1]*(1-alpha_s) + le[1]*alpha_s))
                self._smooth_re = (int(self._smooth_re[0]*(1-alpha_s) + re[0]*alpha_s), int(self._smooth_re[1]*(1-alpha_s) + re[1]*alpha_s))
            
            self.elbow_history.append((now, self._smooth_le, self._smooth_re))
            self.elbow_history = [h for h in self.elbow_history if now - h[0] <= 1.0]
            
            if len(self.elbow_history) > 2:
                for i in range(1, len(self.elbow_history)):
                    age = now - self.elbow_history[i][0]
                    alpha_v = max(0.1, 1.0 - age)
                    for side_idx in [1, 2]:
                        vis.append({'cmd': 'line', 'start': self.elbow_history[i-1][side_idx], 'end': self.elbow_history[i][side_idx], 'color': ColorConfig.PINK, 'thick': 3, 'alpha': alpha_v})

        # --- 1. 核心指标计算 ---
        ls, rs = pts['ls'], pts['rs']
        le, re = pts['le'], pts['re']
        
        # 计算实时角度
        l_ang = GeomUtils.angle_vertical(ls, le)
        r_ang = GeomUtils.angle_vertical(rs, re)
        
        # 计算平均肩高和肘高 (图像坐标系 Y 向下增大)
        sy = (ls[1] + rs[1]) / 2
        ey = (le[1] + re[1]) / 2
        
        # [Fix 1] 健壮的躯干长度计算 (Robust Torso Length)
        # 优先使用全局脊柱分析器计算的稳定躯干长，避免因距离远近导致的像素阈值失效
        torso_len = shared.get('max_torso_len', 0)
        
        if torso_len <= 0:
            # 回退策略：如果全局未就绪，尝试本地计算
            if pts.get('lh') and pts.get('rh'):
                hy = (pts['lh'][1] + pts['rh'][1]) / 2
                torso_len = max(hy - sy, 50.0)
            else:
                # 终极回退：基于肩宽估算 (肩宽通常比较稳定)
                # 假设躯干长约为肩宽的 1.5 倍
                shoulder_width = abs(ls[0] - rs[0])
                torso_len = max(shoulder_width * 1.5, 100.0)

        # --- 2. 状态机流转 ---
        # 使用相对比例而非绝对像素，适配不同身高和距离
        
        if self.stage == "start":
            # [Fix 2] 耸肩检测器初始化 (Shrug Init)
            # 必须在放松阶段校准"鼻-肩"基准距离，否则耸肩检测无法工作
            self.shrug_detector.set_reference(pts)

            # [Update] 触发条件：大臂垂直角 > 30° (任一侧)
            if l_ang > 30 or r_ang > 30:
                self.stage = "up"
                self.up_start_time = time.time()
                # [重置标记] 新的一轮开始，重置达标状态
                self.cycle_flags['range'] = False 
                self.cycle_flags['shrug'] = True
        
        elif self.stage == "up":
            # --- A. 耸肩检测 (实时) ---
            # [Update] 约束：仅在大臂抬起 > 45° 时检测
            if l_ang > 45 or r_ang > 45:
                self.shrug_detector.detect(pts, shared, self.cycle_flags)
            
            # --- B. 高度达标判定 (Latch机制) ---
            th = AlgoConfig.LATERAL_RAISE_ANGLE_TH
            
            # 只要有一帧双侧都达标，即标记本轮合格 (Latch True)
            if l_ang > th and r_ang > th:
                self.cycle_flags['range'] = True
            
            # [Update] 结束条件：大臂垂直角 < 20° (双侧)
            if l_ang < 20 and r_ang < 20:
                self.stage = "start"
                self.counter += 1
                
                # [记录结果] 用于 Start 阶段的静态显示
                self.last_rep_range_ok = self.cycle_flags.get('range', False)
                
                # 结算本轮动作
                self._end_cycle(['shrug', 'range'])
                
            # [New] 僵尸熔断机制
            elif (time.time() - self.up_start_time > 5.0) and (l_ang < 30 and r_ang < 30):
                self.stage = "start"
                self.up_start_time = 0

        # --- 3. 可视化渲染 ---
        # 获取由 FeedbackSystem 管理的激活错误列表
        active_errs = self.active_feedback
        
        # >>> 优先级 1: 抬肘高度 (Range) <<<
        # 触发机制：仅当 'range' 在激活列表中时显示 (即上一轮做错了，或错误被锁定)
        if 'range' in active_errs:
            
            # 显绿逻辑：本轮已达标(Up阶段) 或 上一轮是好的(Start阶段)
            if self.stage == "up":
                is_range_good = self.cycle_flags.get('range', False)
            else:
                is_range_good = self.last_rep_range_ok

            th = AlgoConfig.LATERAL_RAISE_ANGLE_TH
            
            # 遍历左右侧分别绘制
            sides_config = [
                ('left', ls, le, 1),  # dir=1 (x+)
                ('right', rs, re, -1) # dir=-1 (x-)
            ]
            
            for side, s_pt, e_pt, x_dir in sides_config:
                # 颜色状态跟随 is_range_good
                color = ColorConfig.NEON_GREEN if is_range_good else ColorConfig.NEON_RED
                
                # 1. 关键线 (Key Line): 肩 -> 肘 (实线)
                vis.append({'cmd': 'line', 'start': s_pt, 'end': e_pt, 'color': color, 'thick': 4})
                
                # 2. 目标线 (Target Line): 肩 -> 水平延伸 (虚线)
                arm_len = GeomUtils.dist(s_pt, e_pt)
                dx = e_pt[0] - s_pt[0]
                if abs(dx) > 20: x_dir = 1 if dx > 0 else -1
                
                target_pt = (int(s_pt[0] + x_dir * arm_len), s_pt[1])
                vis.append({'cmd': 'line', 'style': 'dash', 'start': s_pt, 'end': target_pt, 'color': color, 'thick': 2})
                
                # 3. 目标点 (Target Point): 空心圆
                vis.append({'cmd': 'circle', 'center': target_pt, 'radius': 6, 'color': color, 'thick': 2})
                
                # 4. 关键点 (Key Point): 肘部实心圆
                vis.append({'cmd': 'circle', 'center': e_pt, 'radius': 8, 'color': color, 'thick': -1})
                
                # 5. 引导 (Guide)
                if is_range_good:
                    # 正确：绿色对号 (上移 25px，增大缩放)
                    vis.append({'cmd': 'check', 'center': (target_pt[0], target_pt[1] - 25), 'color': ColorConfig.NEON_GREEN, 'scale': 1.2})
                else:
                    # 错误：红色垂直向上箭头
                    # 优化：箭头长度增加到 70，且与目标点保持 15px 间距
                    arrow_len = 70
                    # 目标点下移 15px 作为箭头的指向终点
                    arrow_target = (target_pt[0], target_pt[1] + 15)
                    # 起点在终点下方 arrow_len 处
                    arrow_start = (arrow_target[0], arrow_target[1] + arrow_len)
                    
                    vis.append({
                        'cmd': 'arrow', 
                        'start': arrow_start,
                        'target': arrow_target, 
                        'color': ColorConfig.NEON_RED, 
                        'mode': 'point', 
                        'gap': 0
                    })

            # 提示词更新
            if not is_range_good:
                self._set_msg(TextConfig.ERR_LATERAL_HEIGHT, ColorConfig.NEON_RED, priority=1)
            else:
                self._set_msg(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, priority=1)
        
        # >>> 优先级 2: 耸肩 (Shrug) <<<
        # 触发机制：同上
        elif 'shrug' in active_errs:
            # 耸肩特效逻辑 (复用 PressExercise 的样式)
            for pt in [ls, rs]:
                vis.append({'cmd':'arrow', 'start':(pt[0], pt[1]-60), 'target':(0, 1), 'color':ColorConfig.NEON_RED, 'gap':0, 'len':40, 'mode':'vec'})
                vis.append({'cmd':'circle', 'center':pt, 'radius':8, 'color':ColorConfig.NEON_RED, 'thick':-1})
            self._set_msg("沉肩，不要耸肩！", ColorConfig.NEON_RED, priority=2)

        return vis
