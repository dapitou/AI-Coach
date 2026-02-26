"""
脊柱分析模块 (Spine Physics Engine)
V24.1.0: 基准值漂移修复版 (Baseline Drift Fix)
修复：
1. 解决了"保持弓背姿态时，红线逐渐变直消失"的Bug。
   - 原因：旧版会在任何静止状态下更新基准长，导致基准长被弓背时的短长度"同化"。
   - 修复：引入"直立门控"，仅当俯身角度小于10度时，才允许基准值向下修正。
2. 架构调整：将角度计算和朝向判定提前，以便在校准阶段使用。
"""
from core.config import AlgoConfig
import numpy as np
import math

class SpineAnalyzer:
    def __init__(self):
        self.max_torso_len = 0.0
        self.facing_smooth = 0.0
        self.view_mode = 'side' 
        
    def get_max_len(self):
        return self.max_torso_len

    def analyze(self, pts, stage="start"):
        # 1. 完整性检查
        if not (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh')): 
            return
        
        # 2. 基础几何计算
        ls, rs = np.array(pts['ls']), np.array(pts['rs'])
        lh, rh = np.array(pts['lh']), np.array(pts['rh'])
        neck = (ls + rs) / 2
        hip = (lh + rh) / 2
        vec = hip - neck 
        curr_len = np.linalg.norm(vec)
        
        # 3. [架构调整] 提前计算矢量基底 & 朝向 (为了计算角度)
        u = vec / curr_len
        n = np.array([-u[1], u[0]])
        
        score = 0
        if pts.get('nose'): 
            score += np.sign(pts['nose'][0] - neck[0]) * 2.5
        self.facing_smooth = self.facing_smooth * 0.95 + score * 0.05
        face_dir = 1.0 if self.facing_smooth > 0 else -1.0
        back = n * face_dir * AlgoConfig.GLOBAL_DIR_FLIP
        
        # 4. [架构调整] 提前计算俯身角度 (Signed Inc)
        raw_angle = math.degrees(math.atan2(vec[0], vec[1]))
        inc = -raw_angle * face_dir
        
        # ==========================================================
        # 5. [核心修复] 动态校准 (带直立门控)
        # ==========================================================
        if stage in ["start", "up", "prepare"]:
            # 情况A: 当前长度 > 历史最大值
            # 逻辑: 无条件更新。因为人不会变长，变长说明之前没站直，或者换了人。
            if curr_len > self.max_torso_len: 
                self.max_torso_len = curr_len
            
            # 情况B: 当前长度 < 历史最大值 (需要收敛)
            # 逻辑: 只有当"接近站直(角度<10度)"时，才允许缩短基准值。
            # 防止在弓背/俯身时，基准值被错误地拉低，导致弓背检测失效。
            elif self.max_torso_len > 0:
                if abs(inc) < 10.0: # <--- 直立门控
                    self.max_torso_len = self.max_torso_len * 0.95 + curr_len * 0.05
        
        if self.max_torso_len <= 0 or curr_len < 1e-6: return

        # 6. 视图门控
        shoulder_w = np.linalg.norm(ls - rs)
        hip_w = np.linalg.norm(lh - rh)
        s_ratio = shoulder_w / self.max_torso_len
        h_ratio = hip_w / self.max_torso_len
        
        is_strict_side = (s_ratio < AlgoConfig.VIEW_SIDE_TH) and (h_ratio < AlgoConfig.VIEW_SIDE_TH)
        is_strict_front = (s_ratio > AlgoConfig.VIEW_FRONT_TH) or (h_ratio > AlgoConfig.VIEW_FRONT_TH)
        
        if is_strict_side: self.view_mode = 'side'
        elif is_strict_front: self.view_mode = 'front'
        else: self.view_mode = 'neutral'
        
        # ==========================================================
        # 核心解算逻辑
        # ==========================================================
        
        curve_val = 0.0
        visual_dir = -1.0
        lateral_val = 0.0
        real_rounding = 0.0
        
        len_left = np.linalg.norm(lh - ls)
        len_right = np.linalg.norm(rh - rs)
        diff = len_right - len_left
        base_lateral = 0.0
        if abs(diff) > self.max_torso_len * 0.03:
             base_lateral = diff * AlgoConfig.LATERAL_GAIN
        
        # 调试数据
        pts['debug_inc'] = inc
        pts['debug_residual'] = 0.0
        pts['debug_comp_on'] = AlgoConfig.ENABLE_HIP_DRIFT_COMP
        
        if self.view_mode == 'front':
            curve_val = 0.01 
            visual_dir = -1.0 
            lateral_val = base_lateral
                
        elif self.view_mode == 'side':
            # --- Step 1: 髋点漂移修复 ---
            drift_comp_ratio = 0.0
            if AlgoConfig.ENABLE_HIP_DRIFT_COMP:
                if inc > 0:
                    inc_rad = math.radians(inc)
                    drift_comp_ratio = math.sin(inc_rad) * AlgoConfig.HIP_DRIFT_GAIN
            
            fixed_len = curr_len * (1.0 + drift_comp_ratio)
            
            # --- Step 2: 斜边恒定对比 ---
            expected_len = self.max_torso_len
            residual = 1.0 - (fixed_len / expected_len)
            real_rounding = residual
            
            # 更新调试数据
            pts['debug_residual'] = residual * 100.0
            
            # 5. 幅度计算 & 方向修正 (V24.0.0 修正后的逻辑)
            raw_curve = 0.0
            if residual > 0:
                # 弓背: visual_dir = -1.0 (向背部)
                raw_curve = residual * AlgoConfig.ROUNDING_AMP
                visual_dir = -1.0 
            else:
                # 挺腰: visual_dir = 1.0 (向腹部)
                raw_curve = abs(residual) * AlgoConfig.ARCHING_AMP
                visual_dir = 1.0
            
            # 6. 渐近阻尼
            curve_val = self.apply_organic_saturation(raw_curve)
                
            lateral_val = 0.0
            
        else: # neutral
            lateral_val = base_lateral * 0.5
            curve_val = 0.0
            real_rounding = 0.0

        # ==========================================================
        # 8. 偏移合成
        # ==========================================================
        
        sagittal_offset = back * (curve_val * curr_len * visual_dir)
        lateral_offset = n * lateral_val
        
        pts['neck'] = (int(neck[0]), int(neck[1]))
        pts['hip'] = (int(hip[0]), int(hip[1]))
        
        t_pt = neck + vec * AlgoConfig.LOC_THORAX + lateral_offset + sagittal_offset * 0.9
        l_pt = neck + vec * AlgoConfig.LOC_LUMBAR + lateral_offset + sagittal_offset * 1.1
        
        pts['thorax'] = (int(t_pt[0]), int(t_pt[1]))
        pts['waist'] = (int(l_pt[0]), int(l_pt[1]))
        
        pts['rounding_bad'] = (self.view_mode == 'side' and real_rounding > AlgoConfig.ROUNDING_COMPRESS_TH)

    def apply_organic_saturation(self, x):
        limit = AlgoConfig.SPINE_DAMPING_LIMIT
        if x < 0: return 0.0
        return x / (1.0 + x / limit)