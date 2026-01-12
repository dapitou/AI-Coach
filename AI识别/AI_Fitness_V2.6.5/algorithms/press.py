from config import AlgoConfig, TextConfig
from utils import GeomUtils

def process_press(engine, pts, vis, scale):
    if not (pts.get('lw') and pts.get('rw') and pts.get('le') and pts.get('re') and pts.get('ls') and pts.get('rs')): return
    wrist_y = (pts['lw'][1]+pts['rw'][1])/2
    shou_y = (pts['ls'][1]+pts['rs'][1])/2
    nose_y = pts['nose'][1] if pts.get('nose') else 0
    
    if engine.stage != "up" and wrist_y < nose_y - 50:
        engine.stage = "up"
        engine._reset_flags(["arm", "shrug"])
        engine.current_rep_has_error = False
    elif engine.stage == "up" and wrist_y > nose_y:
        engine.stage = "down"
        engine.counter += 1
        engine._end_cycle(["arm", "shrug"])
    
    lok = GeomUtils.is_vertical(pts['lw'], pts['le'], AlgoConfig.PRESS_VERT_TOLERANCE)
    rok = GeomUtils.is_vertical(pts['rw'], pts['re'], AlgoConfig.PRESS_VERT_TOLERANCE)
    if not (lok and rok): engine.cycle_flags['arm'] = False
    
    engine._check_shrug_adaptive(pts, scale, "up")
    
    if 'arm' in engine.active_errs:
        engine._set_msg(TextConfig.ERR_PRESS_ARM, (50, 50, 255), perm=True)
        if pts['le']: vis.append({'type':'press_guide', 'elbow':pts['le'], 'wrist':pts['lw'], 'ok':lok})
        if pts['re']: vis.append({'type':'press_guide', 'elbow':pts['re'], 'wrist':pts['rw'], 'ok':rok})
    elif 'shrug' in engine.active_errs:
        engine._set_msg(TextConfig.ERR_PRESS_SHRUG, (50, 50, 255), perm=True)