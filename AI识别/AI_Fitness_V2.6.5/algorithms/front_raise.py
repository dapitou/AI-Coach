from config import AlgoConfig, TextConfig
from utils import GeomUtils

def process_front_raise(engine, pts, vis, scale):
    if not (pts.get('lw') and pts.get('rw') and pts.get('le') and pts.get('re') and pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh')): return

    wrist_y = (pts['lw'][1] + pts['rw'][1]) / 2
    shou_y = (pts['ls'][1] + pts['rs'][1]) / 2
    hip_y = (pts['lh'][1] + pts['rh'][1]) / 2 
    
    start_th = hip_y - 100
    end_th = hip_y - 50
    
    if engine.stage != "up" and wrist_y < start_th:
        engine.stage = "up"
        engine._reset_flags(["range", "shrug"])
        engine.current_rep_has_error = False
    elif engine.stage == "up" and wrist_y > end_th:
        engine.stage = "down"
        engine.counter += 1
        engine._end_cycle(["range", "shrug"])

    if engine.stage == "up":
        if pts['le'][1] <= pts['ls'][1] or pts['re'][1] <= pts['rs'][1]: 
            engine.cycle_flags['range'] = True

    engine._check_shrug_adaptive(pts, scale, "up")
    
    if 'range' in engine.active_errs:
        engine._set_msg(TextConfig.ERR_RAISE_RANGE, (50, 50, 255), perm=True)
        vis.append({'type':'raise_guide', 'shoulder':pts['ls'], 'elbow':pts['le'], 'side':'left', 'ok':engine.cycle_flags['range']})
        vis.append({'type':'raise_guide', 'shoulder':pts['rs'], 'elbow':pts['re'], 'side':'right', 'ok':engine.cycle_flags['range']})
    elif 'shrug' in engine.active_errs:
        engine._set_msg(TextConfig.ERR_PRESS_SHRUG, (50, 50, 255), perm=True)