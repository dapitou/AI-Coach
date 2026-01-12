import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import AlgoConfig, TextConfig, ColorConfig

def process_lunge(engine, pts, vis, scale):
    # 1. 关键点检查
    if not (pts.get('lh') and pts.get('rh') and pts.get('lk') and pts.get('rk') and 
            pts.get('la') and pts.get('ra') and pts.get('lt') and pts.get('rt') and pts.get('lhe') and pts.get('rhe')): 
        return
    
    # 2. 前腿识别
    current_front_idx = 25 if pts['la'][1] > pts['ra'][1] else 26
    idx = engine.lunge_front_idx if engine.lunge_front_idx is not None else current_front_idx
    
    fk = pts['lk'] if idx == 25 else pts['rk']
    fh = pts['lh'] if idx == 25 else pts['rh']
    fa = pts['la'] if idx == 25 else pts['ra']
    
    # 3. 状态机
    hy = fh[1]
    ky = fk[1]
    
    # [核心优化] 获取参考躯干长度
    # 用于动态计算阈值，解决远近问题
    ref_len = engine.max_torso_len if engine.max_torso_len > 0 else 200

    # [优化] 动态下降趋势判定
    # 阈值 = 躯干长度 * 3%
    # 远距离(躯干100px) -> 阈值3px; 近距离(躯干400px) -> 阈值12px
    descent_threshold = ref_len * AlgoConfig.LUNGE_DESCENT_THRESHOLD_RATIO
    is_strictly_descending = hy > (engine.prev_hip_y + descent_threshold)
    
    engine.prev_hip_y = hy 

    # [Start -> Down]
    if engine.stage != "down" and hy > ky - AlgoConfig.LUNGE_DOWN_TH:
        engine.stage = "down"
        engine._reset_flags(["lunge_knee", "depth"]) 
        engine.current_rep_has_error = False
        engine.lunge_front_idx = current_front_idx
        
    # [Down -> Up]
    elif engine.stage == "down" and hy < ky - AlgoConfig.LUNGE_UP_TH:
        engine.stage = "up"
        engine.counter += 1
        engine._end_cycle(["lunge_knee", "depth"]) 
        engine.lunge_front_idx = None

    # 4. 深度判定
    is_deep = hy >= ky - 30
    if engine.stage == "down" and is_deep:
        engine.cycle_flags['depth'] = True

    # 5. 内扣判定
    is_valgus = False
    direction = 'left'
    
    if engine.lunge_front_idx is not None:
        if idx == 25:
            fk, fa, ft, fh_foot = pts['lk'], pts['la'], pts['lt'], pts['lhe']
        else:
            fk, fa, ft, fh_foot = pts['rk'], pts['ra'], pts['rt'], pts['rhe']
        
        foot_mid_x = (ft[0] + fh_foot[0]) / 2
        foot_mid_pt = (int(foot_mid_x), fa[1])
        
        if idx == 25: 
            if fk[0] < foot_mid_x - AlgoConfig.LUNGE_KNEE_TOLERANCE:
                is_valgus = True
                direction = 'right'
        else: 
            if fk[0] > foot_mid_x + AlgoConfig.LUNGE_KNEE_TOLERANCE:
                is_valgus = True
                direction = 'left'
        
        # 交互绘制
        if 'lunge_knee' in engine.active_errs:
            engine._set_msg(TextConfig.ERR_LUNGE_KNEE, ColorConfig.NEON_RED, perm=True)
            if engine.stage == "down":
                vis.append({
                    'type': 'lunge_knee_guide', 
                    'knee': fk, 
                    'ankle': fa,
                    'foot_mid': foot_mid_pt,
                    'direction': direction, 
                    'ok': not is_valgus 
                })

    # 6. 错误触发锁 (使用动态下降判定)
    in_check_zone = hy > ky - AlgoConfig.LUNGE_VALGUS_CHECK_OFFSET
    
    if engine.stage == "down" and is_strictly_descending and in_check_zone:
        if is_valgus:
            engine.cycle_flags['lunge_knee'] = False
        
    # 7. 深度交互
    if 'depth' in engine.active_errs:
        engine._set_msg(TextConfig.ERR_LUNGE_DEPTH, ColorConfig.NEON_RED, perm=True)
        target_pt = (fh[0], fk[1])
        vis.append({'type':'depth', 'p1':fh, 'p2':target_pt, 'ok':is_deep})