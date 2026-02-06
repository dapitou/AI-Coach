import math
import time
from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
from logic.detectors.valgus import ValgusDetector

class SquatExercise(BaseExercise):
    """
    深蹲动作分析核心类 (Squat Analysis Core) - V24.3 Final Locked
    
    【核心特性】
    1. 动态基准系统 (Dynamic Calibration): 
       抛弃固定的像素阈值，采用"当前垂直距离 / 站立基准距离"的压缩率(Ratio)判定。
       完美适配不同距离、不同身高的用户。
    
    2. 极强抗噪设计 (Heavy Damping):
       在基准值更新时引入 0.01 的极低权重，彻底屏蔽伸懒腰、摄像头抖动造成的瞬间骨骼漂移，
       防止基准值虚高导致无法触发下蹲判定。
    
    3. 状态熔断机制 (Zombie State Breaker):
       如果用户卡在"下蹲状态"超过 6秒 且实际站姿较高，强制重置状态机，实现"自动解套"。
       
    4. 修正记忆 (Correction Memory):
       只有在深蹲底部(纠错区)真正修正过姿态，才算合格。支持起身后保持上一轮的判定结果。
    """

    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        # --- 1. 初始化检测器 ---
        # 膝内扣检测器：仅使用其几何计算能力 (detect方法)，不使用其自带的绘图 (msg为空)
        self.valgus_detector = ValgusDetector(
            ratio_threshold=AlgoConfig.VALGUS_RATIO,
            check_mode='inner',
            error_key='valgus',
            msg="" 
        )
        
        # --- 2. 核心状态变量 ---
        # [基准值] 站立状态下的"髋-膝"垂直投影距离。初始化为0，等待首帧自动校准。
        self.base_h_dist = 0.0
        
        # 上一帧的髋部Y坐标 (继承自BaseExercise的习惯，用于辅助判断方向)
        self.prev_hip_y = 0
        
        # [熔断计时器] 记录进入"下蹲(Down)"状态的时间戳
        self.down_start_time = 0.0
        
        # --- 3. 修正记忆与结算状态 ---
        # [膝内扣]
        self.has_fixed_valgus = False   # 本轮动作中，是否曾经在纠错区将膝盖打开过(修正成功)
        self.last_rep_valgus_ok = True  # 上一轮动作结束时的最终结果 (用于站立时显示红/绿)
        
        # [下蹲幅度]
        self.has_fixed_depth = False    # 本轮动作中，是否曾经蹲到位过
        self.last_rep_depth_ok = True   # 上一轮动作结束时的最终结果

    def process(self, pts, shared):
        """
        每帧核心处理逻辑
        """
        vis = []
        
        # ----------------------------------------------------------
        # 0. 基础安全检查 (Safety Check)
        # ----------------------------------------------------------
        # 必须确保左右髋(lh, rh)和左右膝(lk, rk)都存在，否则无法计算
        if not (pts.get('lh') and pts.get('rh') and pts.get('lk') and pts.get('rk')):
            return vis

        # ----------------------------------------------------------
        # 1. 计算核心生物力学指标 (Biomechanics Metrics)
        # ----------------------------------------------------------
        
        # 计算髋部和膝盖的中心点坐标
        hy = (pts['lh'][1] + pts['rh'][1]) / 2
        ky = (pts['lk'][1] + pts['rk'][1]) / 2
        
        hip_mid = (int((pts['lh'][0] + pts['rh'][0]) / 2), int(hy))
        knee_mid = (int((pts['lk'][0] + pts['rk'][0]) / 2), int(ky))
        
        # [关键指标] 当前的"髋-膝"垂直距离
        # 站立时最大(约等于大腿长)，下蹲时减小(因为大腿变平)
        curr_h_dist = abs(ky - hy)
        
        # [数据清洗] 如果距离过小(小于30px)，通常意味着人离得极远或检测错误
        # 此时暂停处理，防止除零错误或逻辑乱飘
        if curr_h_dist < 30.0 and self.base_h_dist < 30.0:
            return vis

        # ----------------------------------------------------------
        # 2. 智能基准校准 (Smart Calibration) - 极稳版
        # ----------------------------------------------------------
        
        # [策略 A] 全局微衰减 (Global Decay)
        # 每一帧让基准值自动衰减 0.05% (乘以 0.9995)。
        # 目的：如果系统因一次误判导致基准值虚高，通过时间流逝，它会自动降下来，
        # 从而避免"永久卡死"在无法触发下蹲的状态。
        if self.base_h_dist > 0:
            self.base_h_dist *= 0.9995

        # [策略 B] 站立阶段的抗噪更新 (Anti-Noise Update)
        # 仅在 Start 状态下，且当前高度大于基准值时，才尝试更新基准值。
        if self.stage == "start":
            if curr_h_dist > self.base_h_dist:
                # [核心抗噪逻辑] 阻尼系数 = 0.01 (极低)
                # 公式：新基准 = 旧基准 * 0.99 + 当前值 * 0.01
                # 意义：只有当用户"持续"站得比记录值高，基准值才会慢慢爬升。
                # 瞬间的噪声（如1-5帧的跳变）几乎无法撼动基准值，彻底解决了"偶发失灵"问题。
                self.base_h_dist = self.base_h_dist * 0.99 + curr_h_dist * 0.01
        
        # [首帧初始化] 如果还没基准值，瞬间对齐当前值，避免除以零
        if self.base_h_dist < 1.0:
            self.base_h_dist = max(curr_h_dist, 10.0)
            
        # ----------------------------------------------------------
        # 3. 压缩率计算 (Compression Ratio)
        # ----------------------------------------------------------

        safe_base = max(self.base_h_dist, 1.0)
        # Ratio = 当前垂直距离 / 站立基准距离
        # 站立时 ≈ 1.0，深蹲到底时 ≈ 0.0
        compression_ratio = curr_h_dist / safe_base
        
        # [判定区域定义]
        # 1. 纠错范围 (Fix Range): Ratio < 0.30
        # 只有蹲得够深(进入高压区)，才允许用户修正动作，防止站立时误修正。
        IN_FIX_RANGE_RATIO = 0.30
        in_fix_range = compression_ratio < IN_FIX_RANGE_RATIO
        
        # 2. 深度达标 (Depth Check): Ratio < 配置阈值 (默认0.15)
        is_deep_frame = compression_ratio < AlgoConfig.SQUAT_DEPTH_RATIO
        
        if self.prev_hip_y == 0: self.prev_hip_y = hy
        
        # ----------------------------------------------------------
        # 4. 动作状态机 (State Machine with Breaker)
        # ----------------------------------------------------------
        
        current_time = time.time()
        
        if self.stage != "down":
             # >>> 状态切换：从 站立(Start) -> 下蹲(Down)
             # 触发条件：压缩率小于下蹲阈值 (例如 0.85)
             if compression_ratio < AlgoConfig.SQUAT_DOWN_RATIO:
                 self.stage = "down"
                 self.down_start_time = current_time # [记录时间] 用于熔断检测
                 
                 # [重置记忆] 新的一轮开始，必须重新证明自己
                 self.has_fixed_valgus = False
                 self.has_fixed_depth = False 
                 # 初始假设：Valgus是好的(True)，Depth是坏的(False)
                 self.cycle_flags['valgus'] = True 
                 self.cycle_flags['depth'] = False 
                 
        elif self.stage == "down":
             # >>> 状态切换：从 下蹲(Down) -> 站立(Start) [正常完成]
             # 触发条件：压缩率恢复到起立阈值 (例如 0.92)
             if compression_ratio > AlgoConfig.SQUAT_UP_RATIO:
                 self.stage = "start"
                 self.counter += 1
                 
                 # [核心结算] 记录本轮最终结果，用于站立时持久化显示
                 self.last_rep_valgus_ok = self.cycle_flags.get('valgus', True)
                 self.last_rep_depth_ok = self.cycle_flags.get('depth', False)
                 
                 # 提交计数与语音
                 self._end_cycle(['valgus', 'depth'])
             
             # >>> [熔断机制] 僵尸状态检测 (Zombie State Breaker) <<<
             # 条件1: 处于 Down 状态超过 6秒
             # 条件2: 压缩率 > 0.75 (说明人其实站得挺高，并没有在深蹲)
             # 结论: 系统可能因噪声误判卡在了 Down 状态。
             elif (current_time - self.down_start_time > 6.0) and (compression_ratio > 0.75):
                 # [强制重置] 回到 Start 状态，但不计次
                 self.stage = "start"
                 # 可选：强制将基准值拉回到当前高度，加速恢复
                 self.base_h_dist = curr_h_dist 
        
        self.prev_hip_y = hy

        # ----------------------------------------------------------
        # 5. 逻辑判定 (Detection Logic) - 仅在下蹲时执行
        # ----------------------------------------------------------
        
        is_valgus_frame = False
        
        if self.stage == "down":
            # --- A. 膝内扣检测 ---
            _, is_valgus_frame = self.valgus_detector.detect(pts, shared, {})
            
            # [记忆更新] 如果在纠错区内且姿态正确 -> 记为"已修正"
            if in_fix_range and (not is_valgus_frame):
                self.has_fixed_valgus = True
            
            # [标志位更新] 
            # 只有当前没内扣 AND 曾经修好过，才算合格 (True)
            # 否则只要有一帧内扣，或者没修好，都算不合格 (False)
            if is_valgus_frame:
                self.cycle_flags['valgus'] = False
            else:
                if self.has_fixed_valgus:
                    self.cycle_flags['valgus'] = True
                else:
                    self.cycle_flags['valgus'] = False 

            # --- B. 深度检测 ---
            # [记忆更新] 只要有一帧蹲到位了 -> 记为"已到位"
            if is_deep_frame:
                self.has_fixed_depth = True
            
            # [标志位更新]
            self.cycle_flags['depth'] = self.has_fixed_depth

        # ----------------------------------------------------------
        # 6. 特效渲染 (Visuals) - 全局执行
        # ----------------------------------------------------------
        
        # 获取由 FeedbackSystem 管理的激活错误列表
        active_errs = self.active_feedback
        
        # >>> 优先级 1: 膝内扣特效 (Valgus Visuals) <<<
        if 'valgus' in active_errs:
            
            # [显绿逻辑]
            # 下蹲中：实时没内扣 + 曾经修好过
            # 站立中：上一把结果是好的
            if self.stage == "down":
                show_green_valgus = (not is_valgus_frame) and self.has_fixed_valgus
            else:
                show_green_valgus = self.last_rep_valgus_ok
            
            # [辅助线] 足部垂线 (绿色虚线) - 始终显示以提供参考
            for side, ankle_key, toe_key in [('left', 'la', 'lf'), ('right', 'ra', 'rf')]:
                if pts.get(ankle_key):
                    foot_x = pts[ankle_key][0]
                    foot_y = pts[ankle_key][1]
                    if pts.get(toe_key):
                        foot_x = (foot_x + pts[toe_key][0]) // 2
                        foot_y = (foot_y + pts[toe_key][1]) // 2
                    
                    vis.append({'cmd': 'line', 'style': 'dash', 'start': (foot_x, foot_y), 'end': (foot_x, foot_y - 150), 'color': ColorConfig.NEON_GREEN, 'thick': 2})

            # [主特效] 箭头 or 对号
            if show_green_valgus:
                # 状态：正确 -> 绿色对号
                vis.append({'cmd':'check', 'center':pts['lk'], 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
                vis.append({'cmd':'check', 'center':pts['rk'], 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
            else:
                # 状态：错误 -> 红色外展箭头
                vis.append({'cmd':'arrow', 'start':pts['lk'], 'target':(1, 0), 'color':ColorConfig.NEON_RED, 'gap':35, 'mode':'vec'})
                vis.append({'cmd':'arrow', 'start':pts['rk'], 'target':(-1, 0), 'color':ColorConfig.NEON_RED, 'gap':35, 'mode':'vec'})
                self._set_msg("注意膝关节不要内扣！", ColorConfig.NEON_RED, priority=2)
            
            # [互斥锁] 纠正膝盖时，强制认为深度合格，防止多重报错
            if self.stage == "down": 
                self.cycle_flags['depth'] = True

        # >>> 优先级 2: 下蹲幅度特效 (Depth Visuals) <<<
        elif 'depth' in active_errs:
            
            # [显绿逻辑] 同上
            if self.stage == "down":
                show_green_depth = self.has_fixed_depth
            else:
                show_green_depth = self.last_rep_depth_ok
            
            # 计算间距，用于绘制美观的箭头
            raw_dist = math.hypot(hip_mid[0]-knee_mid[0], hip_mid[1]-knee_mid[1])
            GAP_START = 25 
            GAP_END = 25   
            draw_len = max(0, int(raw_dist - GAP_START - GAP_END))
            
            # [New] 绘制目标线 (双膝连线中点的水平线)
            t_col = ColorConfig.NEON_GREEN if show_green_depth else ColorConfig.NEON_RED
            vis.append({'cmd': 'line', 'style': 'dash', 'start': (knee_mid[0]-60, knee_mid[1]), 'end': (knee_mid[0]+60, knee_mid[1]), 'color': t_col, 'thick': 2})

            if not show_green_depth:
                # 状态：未达标 -> 红色向下箭头
                vis.append({'cmd':'circle', 'center':hip_mid, 'radius':12, 'color':ColorConfig.NEON_RED, 'thick':-1})
                vis.append({'cmd':'circle', 'center':knee_mid, 'radius':12, 'color':ColorConfig.NEON_RED, 'thick':3})
                if draw_len > 10:
                    vis.append({'cmd': 'arrow', 'start': hip_mid, 'target': knee_mid, 'color': ColorConfig.NEON_RED, 'mode': 'point', 'gap': GAP_START, 'len': draw_len})
                self._set_msg("蹲至大腿平行地面效果更好！", ColorConfig.NEON_RED, priority=2)
            else:
                # 状态：达标 -> 绿色对号
                vis.append({'cmd':'circle', 'center':hip_mid, 'radius':12, 'color':ColorConfig.NEON_GREEN, 'thick':-1})
                vis.append({'cmd':'circle', 'center':knee_mid, 'radius':12, 'color':ColorConfig.NEON_GREEN, 'thick':3})
                vis.append({'cmd': 'check', 'center': hip_mid, 'color': ColorConfig.NEON_GREEN, 'scale': 1.5})
                self._set_msg("完美动作！", ColorConfig.NEON_GREEN, priority=2)

        return vis