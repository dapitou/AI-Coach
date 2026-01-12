"""
脊柱分析模块 (Spine Physics Engine)
V10.0.0: 2.5D 混合解算 (Hinge Tolerance & Smooth Facing)
复用 SpineAlgo 核心逻辑，适配现有架构
"""
from core.config import AlgoConfig
import numpy as np
import math

class SpineAnalyzer:
    def __init__(self):
        # 对应原代码中的 engine.max_torso_len
        self.max_torso_len = 0.0
        # 对应原代码中的 self.facing_smooth
        self.facing_smooth = 0.0
        
    def get_max_len(self):
        return self.max_torso_len

    def analyze(self, pts, stage="start"):
        """
        核心解算逻辑
        :param pts: 关键点字典
        :param stage: 当前动作阶段 (用于校准最大躯干长)
        """
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
        
        # 3. 动态校准 (Calibration)
        # 复用逻辑: if engine.stage in ["start", "up"]
        if stage in ["start", "up", "prepare"]:
            if curr_len > self.max_torso_len: 
                self.max_torso_len = curr_len
            elif self.max_torso_len > 0: 
                # 平滑更新: 95% 旧值 + 5% 新值
                self.max_torso_len = self.max_torso_len * 0.95 + curr_len * 0.05
            
        # 4. 压缩率计算 (Compression)
        comp = max(0, 1.0 - curr_len/self.max_torso_len) if self.max_torso_len > 0 else 0
        
        # 5. 朝向平滑判定 (Facing Smooth)
        score = 0
        if pts.get('nose'): 
            # 判断鼻子在颈部的左侧还是右侧
            score += np.sign(pts['nose'][0] - neck[0]) * 2.5
        
        # 惯性平滑
        self.facing_smooth = self.facing_smooth * 0.95 + score * 0.05
        face_dir = 1.0 if self.facing_smooth > 0 else -1.0
        
        # 6. 矢量基底构建
        # u: 躯干单位向量 (指向 Hip)
        if curr_len < 1e-6: return
        u = vec / curr_len
        
        # n: 法向量 (垂直于躯干)
        n = np.array([-u[1], u[0]])
        
        # back: 背部朝向 (结合 Global Flip 和 实时朝向)
        back = n * face_dir * AlgoConfig.GLOBAL_DIR_FLIP
        
        # 7. 铰链/俯仰角容差 (Hinge Tolerance)
        # 计算躯干与垂直线的夹角
        inc = abs(math.degrees(math.atan2(vec[0], vec[1]))) # vec[0] is x (horizontal), vec[1] is y (vertical)
        
        # 倾角越大，容忍的压缩量越大 (视为透视投影而非弯曲)
        hinge_tol = min(inc/90.0, 1.0) * AlgoConfig.HINGE_TOLERANCE_GAIN
        real_comp = max(0, comp - hinge_tol)
        
        # 8. 弓背与侧弯解耦 (Rounding & Lateral)
        
        # Rounding (前后弯曲):
        # 如果倾角 > 15度，认为是在此平面上的弯曲，计算 Rounding
        # 否则 (直立时)，负压缩模拟挺胸/挺腰效果
        rounding = real_comp * AlgoConfig.ROUNDING_AMP if inc > 15 else -comp * 0.5
        
        # Lateral (侧弯): 基于左右侧长之差
        # rs-rh (右侧长) - ls-lh (左侧长)
        lateral = (np.linalg.norm(rs-rh) - np.linalg.norm(ls-lh)) * AlgoConfig.LATERAL_GAIN
        
        # 9. 最终偏移合成 (Visual Vectors)
        sagittal = back * (rounding * curr_len)
        lat_vec = n * lateral
        
        # 10. 更新关键点坐标
        pts['neck'] = (int(neck[0]), int(neck[1]))
        pts['hip'] = (int(hip[0]), int(hip[1]))
        
        # 胸椎点: 1/3处 + 侧弯 + 弓背
        t_pt = neck + vec * AlgoConfig.LOC_THORAX + lat_vec + sagittal
        # 腰椎点: 2/3处 + 侧弯 + 弓背(幅度更大 *1.5)
        l_pt = neck + vec * AlgoConfig.LOC_LUMBAR + lat_vec + sagittal * 1.5
        
        pts['thorax'] = (int(t_pt[0]), int(t_pt[1]))
        pts['waist'] = (int(l_pt[0]), int(l_pt[1]))
        
        # 11. 错误标记
        # 只有在倾角显著(>15)且真实压缩超标时才报错
        pts['rounding_bad'] = (inc > 15 and real_comp > AlgoConfig.ROUNDING_COMPRESS_TH)