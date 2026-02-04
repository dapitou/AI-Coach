import json
import os
import time
import re
import math
from exercises.base import BaseExercise
from core.config import ColorConfig
from utils.geometry import GeomUtils

class GenericExercise(BaseExercise):
    """
    通用动作分析引擎 (Generic Motion Analysis Engine)
    
    职责：
    1. 读取并解析 JSON 动作配置文件。
    2. 执行通用的生物力学计算 (虚拟点、动态基准)。
    3. 驱动通用状态机 (State Machine)。
    4. 渲染通用视觉元素 (Visual Elements)。
    
    【纠错判定模式汇总 (Correction Modes)】
    1. latch_fail (一票否决 / 全程纠错):
       - 初始: 合格 (True)
       - 逻辑: 默认合格，全程或指定区间内只要出现错误，即锁定为不合格，无法挽回。
       - 场景: 严禁出现的代偿 (如推举耸肩、小臂不垂直)。
    2. latch_pass (达成即过 / 区间达标):
       - 初始: 不合格 (False)
       - 逻辑: 默认不合格，只要在区间内达标一次(极值点)，即锁定为合格。
       - 场景: 幅度类指标 (如深蹲深度、侧平举高度)。
    3. strict_pass (过程修正 / 区间保持):
       - 初始: 不合格 (False)
       - 逻辑: 需在区间内达标(修正)并保持正确姿态直到离开区间。
       - 场景: 姿态保持类 (如深蹲膝内扣)。
    4. realtime (实时跟随):
       - 逻辑: 无记忆，所见即所得。
       - 场景: 辅助线、非关键性软提示。
    
    任何具体的动作 (如深蹲、推举) 只需要继承此类并指定 config_file 即可。
    """

    # MediaPipe 关键点 ID 映射表
    MP_MAP = {
        0: 'nose', 11: 'ls', 12: 'rs', 13: 'le', 14: 're', 15: 'lw', 16: 'rw',
        23: 'lh', 24: 'rh', 25: 'lk', 26: 'rk', 27: 'la', 28: 'ra', 29: 'lt', 30: 'rt',
        31: 'lf', 32: 'rf'
    }

    def __init__(self, sound_mgr, config_file):
        super().__init__(sound_mgr)
        self.config_file = config_file
        self.config = self._load_config()
        
        # --- 引擎状态存储 ---
        self.dynamic_vars = {} 
        self._init_dynamic_vars()
        
        self.v_pts = {}          # 虚拟点缓存
        self.down_start_time = 0.0 # 状态机计时
        self.latch_states = {}   # [Fix] 状态锁定记忆 (替代简单的 fix_memory)
        self.last_rep_results = {} # 上一轮结果
        self.styles = self.config.get('styles', {})

    def _load_config(self):
        """加载并解析带注释的 JSON 配置文件"""
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            # 自动去 '配置文件' 目录下寻找
            json_path = os.path.join(project_root, '配置文件', self.config_file)
            
            if not os.path.exists(json_path):
                print(f"[GenericEngine] Config file not found: {json_path}")
                return {}

            with open(json_path, 'r', encoding='utf-8') as f:
                content = f.read()
                content = re.sub(r'//.*', '', content) # 去除 // 注释
                return json.loads(content)
        except Exception as e:
            print(f"[GenericEngine] JSON parse error: {e}")
            return {}

    def _init_dynamic_vars(self):
        for var in self.config.get('dynamic_vars', []):
            self.dynamic_vars[var['name']] = 0.0

    def _get_pt(self, pid, raw_pts):
        """获取点坐标 (支持 原始点ID 和 虚拟点ID)"""
        if isinstance(pid, int) and pid < 100:
            key = self.MP_MAP.get(pid)
            return raw_pts.get(key)
        elif pid in self.v_pts:
            return self.v_pts[pid]
        return None

    def _calc_virtual_points(self, raw_pts):
        """计算虚拟关键点"""
        for vp in self.config.get('virtual_points', []):
            pid = vp['id']
            calc_type = vp['calc']
            
            if calc_type == 'midpoint':
                srcs = [self._get_pt(s, raw_pts) for s in vp['sources']]
                if all(srcs):
                    x = sum(p[0] for p in srcs) / len(srcs)
                    y = sum(p[1] for p in srcs) / len(srcs)
                    self.v_pts[pid] = (int(x), int(y))
            
            elif calc_type == 'projection_vertical':
                src = self._get_pt(vp['source'], raw_pts)
                if src:
                    off_y = vp.get('offset_y', 0)
                    self.v_pts[pid] = (src[0], src[1] + off_y)
            
            elif calc_type == 'offset':
                src = self._get_pt(vp['source'], raw_pts)
                if src:
                    self.v_pts[pid] = (src[0] + vp.get('offset_x', 0), src[1] + vp.get('offset_y', 0))
            
            elif calc_type == 'compose':
                # [New] 组合点：取 source_x 的 X 和 source_y 的 Y
                px = self._get_pt(vp['source_x'], raw_pts)
                py = self._get_pt(vp['source_y'], raw_pts)
                if px and py:
                    self.v_pts[pid] = (px[0], py[1])

    def _update_dynamic_vars(self, raw_pts):
        """更新动态基准值"""
        for var in self.config.get('dynamic_vars', []):
            name = var['name']
            
            curr_val = 0.0
            if var['source_type'] == 'distance_y':
                p1 = self._get_pt(var['points'][0], raw_pts)
                p2 = self._get_pt(var['points'][1], raw_pts)
                if p1 and p2: curr_val = abs(p1[1] - p2[1])
            
            if curr_val <= 0: continue

            # [Optimization] 统一使用"智能基准校准"策略 (Smart Calibration)
            # 逻辑：Max Hold + Damping + Decay
            
            # 1. 全局微衰减 (防止基准值卡死在虚高位置)
            decay = var.get('decay', 0.9995)
            self.dynamic_vars[name] *= decay
            
            # 2. 状态门控更新 (仅在特定状态下，如 START，尝试推高基准值)
            active_state = var.get('active_state', 'START').lower()
            if self.stage == active_state:
                if curr_val > self.dynamic_vars[name]:
                    damping = var.get('damping', 0.05) # 默认 0.05 的阻尼
                    self.dynamic_vars[name] = self.dynamic_vars[name] * (1.0 - damping) + curr_val * damping
            
            # 3. 强制初始化 (首帧保护)
            if self.dynamic_vars[name] < 1.0 and curr_val > 10.0: 
                self.dynamic_vars[name] = curr_val

    def _get_metric_value(self, metric_cfg, raw_pts):
        """获取用于状态机或条件的度量值 (完全动态化)"""
        name = metric_cfg if isinstance(metric_cfg, str) else metric_cfg.get('metric')
        if name == 'compression_ratio':
            # [Fix] 支持自定义基准变量名，不再硬编码 'standing_baseline'
            base_var_name = 'standing_baseline'
            if isinstance(metric_cfg, dict):
                base_var_name = metric_cfg.get('baseline', base_var_name)
            
            base_val = self.dynamic_vars.get(base_var_name, 1.0)
            
            # 动态查找定义该基准值的点对
            points = None
            # 1. 优先使用 metric_cfg 中显式指定的 points
            if isinstance(metric_cfg, dict) and 'points' in metric_cfg:
                points = metric_cfg['points']
            else:
                # 2. 否则从 dynamic_vars 配置中反查
                for var in self.config.get('dynamic_vars', []):
                    if var['name'] == base_var_name and 'points' in var:
                        points = var['points']
                        break
            
            if not points: points = [101, 102] # 默认回退
            
            p1 = self._get_pt(points[0], raw_pts)
            p2 = self._get_pt(points[1], raw_pts)
            
            curr_dist = 0.0
            if p1 and p2: curr_dist = abs(p1[1] - p2[1])
            
            return curr_dist / max(base_val, 1.0)
            
        elif name == 'vertical_diff':
            # 计算垂直差值 (p1.y - p2.y)
            points = metric_cfg.get('points', [])
            if len(points) >= 2:
                p1 = self._get_pt(points[0], raw_pts)
                p2 = self._get_pt(points[1], raw_pts)
                if p1 and p2: return p1[1] - p2[1] # Y轴向下为正: p1在下则为正
        
        elif name == 'angle':
            # [New] 支持角度计算 (用于动力链)
            pts = [self._get_pt(p, raw_pts) for p in metric_cfg.get('points', [])]
            if len(pts) == 3 and all(pts):
                return GeomUtils.angle(pts[0], pts[1], pts[2])
                
        return 0.0

    def _update_state_machine(self, raw_pts):
        """状态机流转"""
        sm_config = self.config['evaluation']['state_machine']
        current_time = time.time()
        # 注意：这里不再预计算 ratio，而是根据配置动态计算
        
        if self.stage != "down":
            cfg = sm_config['trigger_down']
            val = self._get_metric_value(cfg, raw_pts)
            
            # 支持 < 和 > 操作符
            triggered = (val < cfg['threshold']) if cfg.get('operator') == '<' else (val > cfg['threshold'])
            
            if triggered:
                self.stage = "down"
                self.down_start_time = current_time
                self.latch_states = {} # [Fix] 重置锁定状态
                self.cycle_flags = {}
        
        elif self.stage == "down":
            cfg = sm_config['trigger_up']
            val = self._get_metric_value(cfg, raw_pts)
            
            triggered = (val > cfg['threshold']) if cfg.get('operator') == '>' else (val < cfg['threshold'])
            
            if triggered:
                self.stage = "start"
                self.counter += 1
                
                eval_cfg = self.config['evaluation']
                check_ids = [c['id'] for c in eval_cfg['conditions']]
                
                for cid in check_ids:
                    res = self.cycle_flags.get(cid, False)
                    self.last_rep_results[cid] = res
                
                self._end_cycle(check_ids)
            
            zb = sm_config.get('zombie_breaker')
            if zb:
                if (current_time - self.down_start_time > zb['timeout_sec']):
                    reset_cond = zb['reset_condition']
                    val = self._get_metric_value(reset_cond, raw_pts)
                    if val > reset_cond['threshold']: # 假设熔断通常是 >
                        self.stage = "start"

    def _evaluate_conditions(self, raw_pts):
        """条件评估"""
        results = {}
        eval_cfg = self.config['evaluation']
        
        # [Fix] 获取逻辑控制配置
        logic_ctrl = eval_cfg.get('logic_control', {})
        
        for cond in eval_cfg['conditions']:
            cid = cond['id']
            ctype = cond['type']
            is_good = True
            
            if ctype == 'ratio_width':
                n_pts = [self._get_pt(p, raw_pts) for p in cond['numerator_points']]
                d_pts = [self._get_pt(p, raw_pts) for p in cond['denominator_points']]
                if all(n_pts) and all(d_pts):
                    num = abs(n_pts[0][0] - n_pts[1][0])
                    den = abs(d_pts[0][0] - d_pts[1][0])
                    val = num / max(den, 1.0)
                    if val < cond.get('min', 0.0): is_good = False
            
            elif ctype == 'ratio_vertical_dynamic':
                pts = [self._get_pt(p, raw_pts) for p in cond['points']]
                if all(pts):
                    dist = abs(pts[0][1] - pts[1][1])
                    base = self.dynamic_vars.get(cond['baseline_var'], 1.0)
                    val = dist / max(base, 1.0)
                    if val > cond.get('max', 999.0): is_good = False
                    # [New] 支持 min 阈值 (用于耸肩检测: 压缩率不能太小 -> 距离不能太短)
                    if val < cond.get('min', -999.0): is_good = False

            elif ctype == 'angle_vertical':
                # 垂直角度检测 (支持单双侧定义)
                # points: [[p1, p2], [p3, p4]]
                pts_groups = cond['points']
                if len(pts_groups) > 0 and not isinstance(pts_groups[0], list):
                    pts_groups = [pts_groups] # 兼容单组配置
                
                threshold = cond.get('max', 20.0)
                side_mode = cond.get('side_mode', 'any') # [New] 单双侧定义: any | all
                
                fail_count = 0
                for pair in pts_groups:
                    p1 = self._get_pt(pair[0], raw_pts)
                    p2 = self._get_pt(pair[1], raw_pts)
                    if p1 and p2:
                        dx = abs(p1[0] - p2[0])
                        dy = abs(p1[1] - p2[1])
                        angle = 90.0 if dy == 0 else math.degrees(math.atan(dx/dy))
                        if angle > threshold: fail_count += 1
                
                # [New] 单双侧判定逻辑
                if side_mode == 'any' and fail_count > 0: is_good = False
                elif side_mode == 'all' and fail_count == len(pts_groups): is_good = False
            
            elif ctype == 'deviation':
                # [New] 共线/偏移检测 (Collinearity)
                # points: [start, end, target] -> 计算 target 到 start-end 直线的距离
                # 场景: 弓背检测 (肩-髋连线，背部点偏移)
                if len(cond['points']) == 3:
                    p_start = self._get_pt(cond['points'][0], raw_pts)
                    p_end = self._get_pt(cond['points'][1], raw_pts)
                    p_target = self._get_pt(cond['points'][2], raw_pts)
                    
                    if p_start and p_end and p_target:
                        # 点到直线距离公式
                        x0, y0 = p_target
                        x1, y1 = p_start
                        x2, y2 = p_end
                        
                        num = abs((x2-x1)*(y1-y0) - (x1-x0)*(y2-y1))
                        den = math.hypot(x2-x1, y2-y1)
                        dist = num / max(den, 1.0)
                        
                        # 归一化偏移量 (相对于直线长度的百分比)
                        if cond.get('normalize', True):
                            dist /= max(den, 1.0)
                        
                        if dist > cond.get('max', 0.1): is_good = False
            
            elif ctype == 'chain_sync':
                # [New] 动力链同步检测 (Kinetic Chain Sync)
                # 逻辑: 比较两个指标的线性关系 |m1 - (m2 * scale + offset)| <= tolerance
                # 场景: 硬拉伸膝与伸髋同步
                m1 = self._get_metric_value(cond['metric_1'], raw_pts)
                m2 = self._get_metric_value(cond['metric_2'], raw_pts)
                
                scale = cond.get('scale', 1.0)
                offset = cond.get('offset', 0.0)
                tolerance = cond.get('tolerance', 15.0)
                
                diff = abs(m1 - (m2 * scale + offset))
                if diff > tolerance: is_good = False
            
            # --- 3. 核心纠错模式处理 (Correction Modes) ---
            # [逻辑闭环] 将 4 种代码模式归纳为 2 大类：
            # 1. 全程纠错 (Full Process): latch_fail (无约束)
            # 2. 区间纠错 (Interval): latch_pass, strict_pass, latch_fail (带约束)
            
            mode = cond.get('correction_mode', 'realtime')
            
            # [通用约束计算] 计算当前帧是否处于"有效纠错区间"
            # 默认为 True (全程有效)，除非配置了 correction_constraint
            in_fix_range = True
            constraint = cond.get('correction_constraint')
            if constraint:
                metric_val = self._get_metric_value(constraint, raw_pts)
                if 'max' in constraint and metric_val > constraint['max']: in_fix_range = False
                if 'min' in constraint and metric_val < constraint['min']: in_fix_range = False
                if 'threshold' in constraint:
                    th = constraint['threshold']
                    op = constraint.get('operator', '>')
                    if op == '>' and not (metric_val > th): in_fix_range = False
                    elif op == '<' and not (metric_val < th): in_fix_range = False
            
            # 初始化 Latch 状态
            if cid not in self.latch_states:
                if mode == 'latch_fail': self.latch_states[cid] = True  # 默认好，坏一次就死
                elif mode == 'latch_pass': self.latch_states[cid] = False # 默认坏，好一次就行
                elif mode == 'strict_pass': self.latch_states[cid] = False # 默认坏，需在修正区修好
            
            if mode == 'realtime':
                results[cid] = is_good
                
            elif mode == 'latch_fail': # 推举: 耸肩/小臂 (一票否决)
                # [增强] 支持区间禁忌：只有在区间内(in_fix_range)犯错，才会被锁定为失败
                if in_fix_range and not is_good: 
                    self.latch_states[cid] = False
                results[cid] = self.latch_states[cid]
                
            elif mode == 'latch_pass': # 深蹲: 深度 (一次达标即可)
                # [增强] 支持区间达标：只有在区间内(in_fix_range)达标，才会被锁定为成功
                if in_fix_range and is_good: 
                    self.latch_states[cid] = True
                results[cid] = self.latch_states[cid]
                
            elif mode == 'strict_pass': # 过程修正 (Process Fix)
                # 逻辑：区间内已修正 AND 修正后保持至离开区间
                if in_fix_range:
                    # 在区间内：实时跟随，但记录状态
                    # 如果当前帧是好的，标记为True；如果坏了，标记为False (破功重置)
                    if is_good: self.latch_states[cid] = True
                    else: self.latch_states[cid] = False 
                    results[cid] = self.latch_states[cid]
                else:
                    # 在区间外：保持离开区间那一刻的状态 (锁定结果)
                    results[cid] = self.latch_states[cid]

        # --- 4. 优先级压制 (Priority Suppression) ---
        # 复刻深蹲逻辑：如果膝内扣(P1)报错，强制认为深度(P2)是好的，避免双重报错
        if logic_ctrl.get('suppress_lower_priority', False):
            # 找出所有失败的条件
            failed_conds = [c for c in eval_cfg['conditions'] if not results.get(c['id'], True)]
            if failed_conds:
                # 按优先级排序 (数值小优先级高)
                failed_conds.sort(key=lambda x: x.get('priority', 99))
                top_fail = failed_conds[0]
                
                # 将所有比 top_fail 优先级低的失败条件强制置为 True
                for c in failed_conds[1:]:
                    # [Fix] 必须同时更新 results 和 cycle_flags，确保计数和渲染都认为它是好的
                    cid_suppressed = c['id']
                    results[cid_suppressed] = True
                    if self.stage == "down":
                        self.cycle_flags[cid_suppressed] = True
            
            if self.stage == "down":
                self.cycle_flags[cid] = results[cid]
        
        return results

    def _resolve_color(self, key):
        if key == 'good': return ColorConfig.NEON_GREEN
        if key == 'bad': return ColorConfig.NEON_RED
        return ColorConfig.NEON_BLUE

    def _render_elements(self, raw_pts, results):
        """渲染引擎"""
        vis = []
        elements = self.config.get('elements', [])
        logic_ctrl = self.config['evaluation'].get('logic_control', {})
        exclusive = logic_ctrl.get('display_mode') == 'exclusive'
        active_fb = self.active_feedback

        # [Fix] 渲染仲裁核心逻辑 (Rendering Arbitration)
        # 目标：严格复刻 squat.py 的 if-elif 逻辑
        # 规则：
        # 1. 仅考虑在 active_feedback 中的条件 (除非 active_feedback 为空且我们需要默认显示)
        # 2. 优先显示“报错”的条件 (Bad > Good)
        # 3. 同等状态下，优先显示“高优先级”的条件 (Priority High > Low)
        
        display_cid = None
        if exclusive:
            # 1. 获取所有相关条件并按优先级排序
            sorted_conds = sorted(self.config['evaluation']['conditions'], key=lambda x: x.get('priority', 99))
            
            # 2. 寻找最高优先级的“报错”条件
            current_results = results if self.stage == "down" else self.last_rep_results
            
            for c in sorted_conds:
                cid = c['id']
                if cid in active_fb and not current_results.get(cid, True):
                    display_cid = cid
                    break
            
            # 3. 如果没有报错，寻找最高优先级的“通过”条件
            if display_cid is None:
                for c in sorted_conds:
                    cid = c['id']
                    if cid in active_fb:
                        display_cid = cid
                        break

        for elem in elements:
            ref = elem.get('condition_ref')
            draw_cfg = None
            
            if ref:
                # 互斥过滤：如果确定了 display_cid，且当前元素不属于它，则跳过
                if exclusive and display_cid and ref != display_cid: continue
                
                # [Fix] 核心修复：仅渲染在 active_feedback 中的条件
                # 防止在动作正确(未激活错误)时，显示了纠错特效(如绿勾或红箭头)
                if ref not in active_fb: continue
                
                # 状态获取
                res_map = results if self.stage == "down" else self.last_rep_results
                is_good = res_map.get(ref, True)
                
                if is_good and 'on_good' in elem: draw_cfg = elem['on_good']
                elif not is_good and 'on_bad' in elem: draw_cfg = elem['on_bad']
            else:
                draw_cfg = elem
            
            if not draw_cfg: continue
            
            etype = draw_cfg.get('type', elem.get('type'))
            color = self._resolve_color(draw_cfg.get('style_key', 'default'))
            
            if etype == 'line':
                p1 = self._get_pt(draw_cfg.get('from'), raw_pts)
                p2 = self._get_pt(draw_cfg.get('to'), raw_pts)
                if p1 and p2:
                    style = 'dash' if draw_cfg.get('is_dashed') else 'solid'
                    vis.append({'cmd': 'line', 'start': p1, 'end': p2, 'color': color, 'thick': draw_cfg.get('width', 2), 'style': style})
            
            elif etype == 'arrow':
                p1 = self._get_pt(draw_cfg.get('start') or draw_cfg.get('from'), raw_pts)
                if 'to' in draw_cfg:
                    p2 = self._get_pt(draw_cfg['to'], raw_pts)
                    if p1 and p2:
                        vis.append({'cmd': 'arrow', 'start': p1, 'target': p2, 'color': color, 'mode': 'point', 'gap': 25})
                elif 'direction' in draw_cfg:
                    if p1:
                        vis.append({'cmd': 'arrow', 'start': p1, 'target': (1,0), 'color': color, 'mode': 'vec'})

            elif etype == 'circle':
                c = self._get_pt(draw_cfg.get('center'), raw_pts)
                if c:
                    vis.append({'cmd': 'circle', 'center': c, 'radius': draw_cfg.get('radius', 10), 'color': color, 'thick': -1})
            
            elif etype == 'icon':
                c = self._get_pt(draw_cfg.get('center'), raw_pts)
                if c and draw_cfg.get('icon_name') == 'check':
                    vis.append({'cmd': 'check', 'center': c, 'color': color, 'scale': 1.2})

        return vis

    def process(self, pts, shared):
        vis = []
        if not self.config: return vis
        self._calc_virtual_points(pts)
        self._update_dynamic_vars(pts)
        self._update_state_machine(pts)
        results = self._evaluate_conditions(pts)
        vis.extend(self._render_elements(pts, results))
        return vis