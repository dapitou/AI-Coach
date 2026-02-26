import math
import time
from exercises.base import BaseExercise
from core.config import TextConfig, ColorConfig, AlgoConfig
from utils.geometry import GeomUtils
from logic.detectors.shrug import ShrugDetector
# [Modification] 移除了 RoundingDetector 导入

class PressExercise(BaseExercise):
    """
    推举动作分析核心类 (Press Analysis Core) - V24.11 Logic Commented
    
    【核心特性】
    1. 动态基准与防抖 (Dynamic Reference & Anti-Shake): 
       - 在 Start 阶段智能更新"鼻-肩"垂直距离基准，引入衰减机制防止基准卡死。
       - 耸肩检测引入连续帧计数器，有效过滤瞬间骨骼抖动造成的误判。
       
    2. 全程严判逻辑 (Strict Process Judgment):
       - 耸肩判定采用"一票否决制"：动作过程中只要出现持续耸肩，本轮即判定为不合格。
       - 只有全程保持沉肩状态，且完整完成动作循环，才视为一次有效修正。
       
    3. 多维度实时检测 (Multi-dimensional Detection):
       - 耸肩检测基于相对位移压缩率，解耦绝对像素距离。
       - 小臂检测基于几何垂直度，支持每一帧的实时状态计算。
    """

    def __init__(self, sound_mgr):
        super().__init__(sound_mgr)
        
        # --- 1. 初始化检测器 ---
        # [耸肩检测器] 
        # 采用"手动接管"模式：不使用 add_detector 加入自动循环。
        # 原因：我们需要精确控制其检测时机（仅在手举高时）和特效渲染逻辑（严师模式）。
        self.shrug_detector = ShrugDetector(
            compression_threshold=AlgoConfig.SHRUG_COMPRESSION_TH,
            error_key='shrug',
            msg="" # 禁用内部文案，由外部 process 函数统一控制
        )
        
        # [Modification] 移除了弓背检测器 (RoundingDetector) 的初始化
        
        # --- 2. 核心状态变量 ---
        # [基准值] 鼻-肩垂直距离 (Relaxed Neck-Shoulder Distance)
        # 用于计算耸肩的压缩率。
        self.shrug_ref_h = 0.0
        
        # [防抖计数器] 记录连续耸肩帧数，防止瞬间骨骼抖动误判
        self.shrug_bad_frames = 0
        
        # [结果记忆] 记录上一轮动作的最终判定结果
        self.last_rep_shrug_ok = True 
        self.last_rep_arm_ok = True   
        
        # [奖励计时器] 记录耸肩动作完美结束的时间戳
        # 用于在动作结束后显示 1秒 的绿色成功特效
        self.shrug_success_ts = 0.0
        
        # [轨迹记录] 存储手腕历史坐标
        self.wrist_history = []
        self._smooth_lw = None
        self._smooth_rw = None

    def process(self, pts, shared):
        """
        每帧核心处理逻辑
        """
        vis = []
        
        # 0. 基础安全检查 (Safety Check)
        # 必须确保 鼻、肩、肘、腕 关键点全部存在
        if not (pts.get('lw') and pts.get('rw') and pts.get('le') and pts.get('re') and 
                pts.get('nose') and pts.get('ls') and pts.get('rs')): 
            return vis

        # --- 0. 轨迹逻辑 (Wrist Trajectory) --- 增加平滑处理与全局开关
        if AlgoConfig.ENABLE_TRAJECTORY:
            now = time.time()
            lw, rw = pts['lw'], pts['rw']
            
            # EMA 平滑处理
            alpha_s = 0.2
            if self._smooth_lw is None:
                self._smooth_lw, self._smooth_rw = lw, rw
            else:
                self._smooth_lw = (int(self._smooth_lw[0]*(1-alpha_s) + lw[0]*alpha_s), int(self._smooth_lw[1]*(1-alpha_s) + lw[1]*alpha_s))
                self._smooth_rw = (int(self._smooth_rw[0]*(1-alpha_s) + rw[0]*alpha_s), int(self._smooth_rw[1]*(1-alpha_s) + rw[1]*alpha_s))
            
            self.wrist_history.append((now, self._smooth_lw, self._smooth_rw))
            self.wrist_history = [h for h in self.wrist_history if now - h[0] <= 1.0]
            
            if len(self.wrist_history) > 2:
                for i in range(1, len(self.wrist_history)):
                    age = now - self.wrist_history[i][0]
                    alpha_v = max(0.1, 1.0 - age)
                    for side_idx in [1, 2]:
                        vis.append({'cmd': 'line', 'start': self.wrist_history[i-1][side_idx], 'end': self.wrist_history[i][side_idx], 'color': ColorConfig.PINK, 'thick': 3, 'alpha': alpha_v})

        # ==========================================================
        # 1. 状态机流转 & 基准值校准
        # ==========================================================
        
        wrist_y = (pts['lw'][1] + pts['rw'][1]) / 2
        nose_y = pts['nose'][1]
        
        # [基准校准] 仅在 Start (放松/准备) 阶段进行
        if self.stage == "start":
            # 1. 调用检测器更新基准 (内部逻辑：取最大放松距离)
            self.shrug_detector.set_reference(pts)
            
            # 2. 同步基准值到本地变量
            if self.shrug_ref_h > 0:
                self.shrug_ref_h *= 0.9995 # 全局微衰减，防止基准卡死
            
            # 读取当前距离并更新
            avg_shoulder_y = (pts['ls'][1] + pts['rs'][1]) / 2
            curr_shrug_dist = avg_shoulder_y - nose_y
            if curr_shrug_dist > self.shrug_ref_h:
                self.shrug_ref_h = self.shrug_ref_h * 0.95 + curr_shrug_dist * 0.05
            
            # 首帧初始化保护
            if self.shrug_ref_h < 1.0:
                self.shrug_ref_h = max(curr_shrug_dist, 10.0)

        # >>> 状态切换：Start -> Down (开始推举)
        # 触发条件：手腕举过鼻子上方 50px
        if self.stage == "start" and wrist_y < nose_y - 50:
            self.stage = "down"
            self.shrug_bad_frames = 0
            
            # [标志位初始化] 默认假设动作是完美的 (True)
            self.cycle_flags['shrug'] = True 
            self.cycle_flags['arm'] = True 

        # >>> 状态切换：Down -> Start (结束推举)
        # 触发条件：手腕回到鼻子下方
        elif self.stage == "down" and wrist_y > nose_y:
            self.stage = "start"
            self.counter += 1
            
            # [耸肩成功判定]
            # 条件：1. 系统处于耸肩纠错模式 (active_feedback有shrug)
            #       2. 本轮动作全程保持合格 (cycle_flags['shrug']为True)
            # 结果：记录当前时间，触发后续 1秒 的绿色奖励特效
            if 'shrug' in self.active_feedback and self.cycle_flags.get('shrug', True):
                self.shrug_success_ts = time.time() 
            
            # [动作结算] 提交给 FeedbackSystem 进行计次和语音反馈
            # [Modification] 移除了 'rounding'
            check_keys = ['shrug']
            if AlgoConfig.ENABLE_PRESS_ARM: check_keys.append('arm')
            self._end_cycle(check_keys)

        # ==========================================================
        # 2. 实时逻辑判定 (仅在 Down 发力阶段)
        # ==========================================================
        if self.stage == "down":
             # 前置条件：只有当手肘高于肩膀一定程度(真正推起)时才开始检测
             # 这里简化判断：手腕高于手肘
             wrists_high = (pts['lw'][1] < pts['le'][1]) and (pts['rw'][1] < pts['re'][1])
             
             if wrists_high:
                 # A. [耸肩检测]
                 # 手动调用 detect，它会计算压缩率并更新 cycle_flags['shrug']
                 self.shrug_detector.detect(pts, shared, self.cycle_flags)
                 
                 # B. [小臂垂直检测]
                 if AlgoConfig.ENABLE_PRESS_ARM:
                    tol = AlgoConfig.PRESS_VERT_TOLERANCE
                    lok = GeomUtils.is_vertical(pts['lw'], pts['le'], tol)
                    rok = GeomUtils.is_vertical(pts['rw'], pts['re'], tol)
                    # 只要有一只手不垂直，本轮标记为不合格
                    if not (lok and rok): 
                         self.cycle_flags['arm'] = False
                 
                 # [Modification] 移除了 C. [其他通用检测] (如弓背) 的调用
                 # vis.extend(self.run_detectors(pts, shared))

        # ==========================================================
        # 3. 特效渲染 (Visual Feedback)
        # ==========================================================
        # 获取当前被激活的错误 (由全局状态机 FeedbackSystem 仲裁)
        active_errs = self.active_feedback

        # ----------------------------------------------------------
        # 模块 A: 耸肩特效 (Shrug Visuals)
        # 作用范围：仅肩部关键点 (ls, rs)
        # ----------------------------------------------------------
        
        # 判定是否显示特效：
        # 1. 'shrug' 被激活 (纠错中)
        # 2. 或者 处于成功后的奖励时间窗 (1秒内)
        is_shrug_active = 'shrug' in active_errs
        is_success_window = (time.time() - self.shrug_success_ts) < 1.0
        
        if AlgoConfig.ENABLE_SHRUG and (is_shrug_active or is_success_window):
            
            # [颜色逻辑]
            # 奖励期 -> 绿 (Green)
            # 纠错期 -> 红 (Red) - 即使当前帧没耸肩，只要没做完一轮，就一直红
            show_green = is_success_window
            show_red = is_shrug_active and (not show_green)
            
            # [绘制逻辑]
            if show_green or show_red:
                for side, pt in [('left', pts['ls']), ('right', pts['rs'])]:
                    if show_green:
                        # 状态：成功 (Success) -> 绿色对号
                        vis.append({'cmd':'check', 'center':(pt[0], pt[1]-30), 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
                    else:
                        # 状态：纠错/警示 (Warning) -> 红色向下箭头
                        # 箭头从肩上方60px指向肩膀，意为"沉肩"
                        start_pt = (pt[0], pt[1] - 60)
                        vis.append({
                            'cmd':'arrow', 
                            'start':start_pt, 'target':(0, 1), 
                            'color':ColorConfig.NEON_RED, 
                            'gap':0, 'len':40, 'mode':'vec'
                        })
                        vis.append({'cmd':'circle', 'center':pt, 'radius':8, 'color':ColorConfig.NEON_RED, 'thick':-1})

                # [文案提示] 仅在红色警示时显示
                if show_red:
                    self._set_msg(TextConfig.ERR_PRESS_SHRUG, ColorConfig.NEON_RED, priority=2)

        # ----------------------------------------------------------
        # 模块 B: 小臂特效 (Arm Visuals)
        # 作用范围：肘部 (le, re) 至 手腕 (lw, rw)
        # ----------------------------------------------------------
        if 'arm' in active_errs and AlgoConfig.ENABLE_PRESS_ARM:
             
             # 重新计算实时几何状态，用于每一帧的动态渲染
             tol = AlgoConfig.PRESS_VERT_TOLERANCE
             lok = GeomUtils.is_vertical(pts['lw'], pts['le'], tol)
             rok = GeomUtils.is_vertical(pts['rw'], pts['re'], tol)
             
             # 特殊处理：Start阶段保持上一轮的错误状态提示 (可选)
             if self.stage == "start" and not self.last_rep_arm_ok:
                 pass 

             # 遍历左右手进行绘制
             for side, wrist, elbow, is_ok in [
                 ('left', pts['lw'], pts['le'], lok), 
                 ('right', pts['rw'], pts['re'], rok)
             ]:
                 # 颜色：根据实时状态切换 红/绿
                 col = ColorConfig.NEON_GREEN if is_ok else ColorConfig.NEON_RED
                 
                 # 1. [辅助线] 绿色虚线 (始终显示，作为标准参考)
                 # 长度与当前小臂等长，方向垂直向上
                 arm_len = int(GeomUtils.dist(wrist, elbow))
                 target_pt = (elbow[0], elbow[1] - arm_len)
                 
                 vis.append({'cmd':'line', 'style':'dash', 'start':elbow, 'end':target_pt, 'color':ColorConfig.NEON_GREEN, 'thick':2})
                 
                 # 2. [目标点] 辅助线顶端的空心圆 (绿色)
                 vis.append({'cmd':'circle', 'center':target_pt, 'radius':12, 'color':ColorConfig.NEON_GREEN, 'thick':2})
                 
                 # 3. [手腕点] 实心圆 (随状态变色)
                 vis.append({'cmd':'circle', 'center':wrist, 'radius':8, 'color':col, 'thick':-1})
                 
                 # 4. [指示器] 动态箭头 或 对号
                 if not is_ok:
                     # 错 -> 红色箭头，从手腕指向目标点投影位置
                     vis.append({'cmd':'arrow', 'start':wrist, 'target':(target_pt[0], wrist[1]), 'color':ColorConfig.NEON_RED, 'mode':'point', 'gap':20})
                 else:
                     # 对 -> 绿色对号，显示在手腕上方
                     vis.append({'cmd':'check', 'center':(wrist[0], wrist[1]-30), 'color':ColorConfig.NEON_GREEN, 'scale':1.2})
             
             # [文案提示]
             # 只要有一只手不垂直，就显示红色提示
             if not (lok and rok):
                 self._set_msg(TextConfig.ERR_PRESS_ARM, ColorConfig.NEON_RED, priority=1)
             
        return vis