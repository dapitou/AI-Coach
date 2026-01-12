from config import AlgoConfig, TextConfig

def process_squat(engine, pts, vis, scale):
    if not (pts.get('lh') and pts.get('rh') and pts.get('lk') and pts.get('rk') and 
            pts.get('lt') and pts.get('rt') and pts.get('la') and pts.get('ra')): return
    
    hy = (pts['lh'][1]+pts['rh'][1])/2
    ky = (pts['lk'][1]+pts['rk'][1])/2
    
    if engine.prev_hip_y == 0: engine.prev_hip_y = hy
    is_descending = hy > (engine.prev_hip_y + 2) 
    engine.prev_hip_y = hy 

    if engine.stage != "down" and hy > ky - AlgoConfig.SQUAT_DOWN_TH:
        engine.stage = "down"
        engine._reset_flags(["rounding", "valgus", "depth"])
        engine.current_rep_has_error = False
        
    elif engine.stage == "down" and hy < ky - AlgoConfig.SQUAT_UP_TH:
        engine.stage = "up"
        engine.counter += 1
        engine._end_cycle(["rounding", "valgus", "depth"])
        
    is_deep = hy >= ky - 30
    
    l_foot_x = (pts['lt'][0] + pts['la'][0]) / 2
    r_foot_x = (pts['rt'][0] + pts['ra'][0]) / 2
    knee_dist = abs(pts['lk'][0] - pts['rk'][0])
    foot_dist = abs(l_foot_x - r_foot_x)
    is_valgus = knee_dist < (foot_dist * AlgoConfig.VALGUS_RATIO)
    l_in = pts['lk'][0] > l_foot_x 
    r_in = pts['rk'][0] < r_foot_x
    l_fail = is_valgus and l_in
    r_fail = is_valgus and r_in
    if is_valgus and not l_fail and not r_fail: l_fail = r_fail = True
    
    in_valgus_check_zone = hy > ky - 200
    
    if engine.stage == "down" and is_descending and in_valgus_check_zone:
        if l_fail or r_fail: engine.cycle_flags['valgus'] = False
        if pts.get('rounding_bad'): engine.cycle_flags['rounding'] = False
    
    if engine.stage == "down" and is_deep: engine.cycle_flags['depth'] = True
        
    show_rounding = "rounding" in engine.active_errs
    show_valgus = "valgus" in engine.active_errs and not show_rounding
    show_depth = "depth" in engine.active_errs and not show_valgus and not show_rounding
    
    if show_rounding:
        engine._set_msg(TextConfig.ERR_SQUAT_ROUNDING, (50, 50, 255), perm=True)
    elif show_valgus:
        engine._set_msg(TextConfig.ERR_SQUAT_VALGUS, (50, 50, 255), perm=True)
        if pts['lk']: vis.append({'type':'bounce_arrow', 'start':pts['lk'], 'side':'left', 'ok':not l_fail})
        if pts['rk']: vis.append({'type':'bounce_arrow', 'start':pts['rk'], 'side':'right', 'ok':not r_fail})
    elif show_depth:
        engine._set_msg(TextConfig.ERR_SQUAT_DEPTH, (50, 50, 255), perm=True)
        p1 = ((pts['lh'][0]+pts['rh'][0])//2, int(hy))
        p2 = ((pts['lk'][0]+pts['rk'][0])//2, int(ky))
        vis.append({'type':'depth', 'p1':p1, 'p2':p2, 'ok':is_deep})