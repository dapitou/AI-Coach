import time
from core.config import TextConfig, AlgoConfig, ColorConfig

class Gatekeeper:
    def __init__(self):
        self.last_act_time = time.time()
    
    # [Fix] Accept 'exercise' object to read/write msg state directly
    def check(self, pts, mode, exercise):
        # Always pass if active (DOWN state)
        if exercise.stage == "down": return True
        
        is_similar = False
        tip = ""
        
        if mode == TextConfig.ACT_PRESS:
            tip = TextConfig.TIP_PRESS_DO
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                # Hands above shoulders (roughly)
                if (pts['lw'][1]+pts['rw'][1])/2 < (pts['ls'][1]+pts['rs'][1])/2 + 200: is_similar = True
                
        elif mode == TextConfig.ACT_SQUAT:
            tip = TextConfig.TIP_SQUAT_DO
            if pts.get('lh') and pts.get('rh'):
                # Hips visible and not too narrow (side view check)
                if abs(pts['lh'][0]-pts['rh'][0]) > 20: is_similar = True
        
        elif mode == TextConfig.ACT_RAISE:
            tip = TextConfig.TIP_RAISE_DO
            if pts.get('lw'): is_similar = True
            
        elif mode == TextConfig.ACT_LUNGE:
            tip = TextConfig.TIP_LUNGE_DO
            if pts.get('lh') and pts.get('rh') and (pts.get('lk') or pts.get('rk')):
                if abs(pts['lh'][0]-pts['rh'][0]) > 20: is_similar = True
                
        if is_similar:
            self.last_act_time = time.time()
            # [Restore Logic] Clear hint immediately if it matches current tip
            if exercise.msg == tip:
                exercise.msg = ""
                exercise.msg_priority = 0
            return True
        else:
            if time.time() - self.last_act_time > AlgoConfig.GATEKEEPER_TIMEOUT:
                # Show tip
                exercise._set_msg(tip, ColorConfig.NEON_RED, perm=True, priority=1)
            return False