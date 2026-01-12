from core.base import BaseExercise
from core.config import ColorConfig, AlgoConfig, TextConfig
import time

class LungeExercise(BaseExercise):
    def __init__(self, s):
        super().__init__(s)
        self.name = TextConfig.ACT_LUNGE
        self.last_t = 0
        self.prev_hy = 0
        self.stand_y = 0
        self.front_idx = None
        
    def process(self, pts, shared):
        vis = []
        # Gatekeeper
        if not (pts.get('lt') and pts.get('rt') and pts.get('ls') and pts.get('rs')):
             return vis, (TextConfig.TIP_LUNGE_DO, ColorConfig.NEON_RED), False
        
        fd = abs(pts['lt'][0]-pts['rt'][0])
        sw = abs(pts['ls'][0]-pts['rs'][0])
        if fd <= sw * 0.5: return vis, (TextConfig.TIP_LUNGE_DO, ColorConfig.NEON_RED), False
        
        if not pts.get('lk'): return vis, ("", 0), True
        
        curr_front = 25 if pts['la'][1] > pts['ra'][1] else 26
        idx = self.front_idx if self.front_idx else curr_front
        
        fk = pts['lk'] if idx == 25 else pts['rk']
        fh = pts['lh'] if idx == 25 else pts['rh']
        
        hy, ky = fh[1], fk[1]
        if self.stand_y == 0 or hy < self.stand_y: self.stand_y = hy
        
        if self.prev_hy == 0: self.prev_hy = hy
        desc = hy > self.prev_hy + 5 
        self.prev_hy = hy
        
        drop = hy - self.stand_y
        max_drop = (shared.get('max_len', 200))
        
        if self.stage != "down" and drop > max_drop * 0.15:
            self.stage = "down"; self.curr_rep_error = False; self.active_errs.clear()
            self.front_idx = curr_front
        elif self.stage == "down" and drop < max_drop * 0.1:
            self.stage = "up"
            if time.time()-self.last_t > 0.2:
                self.counter += 1; self.sound.play('count'); self.last_t = time.time()
                if self.curr_rep_error: self.bad_reps += 1
                else: self.sound.play('success')
            self.front_idx = None

        # Correction
        valgus = False
        direction = 'left'
        
        if self.front_idx:
            fa = pts['la'] if idx == 25 else pts['ra']
            ft = pts['lt'] if idx == 25 else pts['rt']
            fheel = pts['lhe'] if idx == 25 else pts['rhe']
            mid = (ft[0]+fheel[0])/2
            
            if idx == 25:
                if fk[0] < mid - 35: valgus = True; direction = 'right'
            else:
                if fk[0] > mid + 35: valgus = True; direction = 'left'
            
            # 只有下蹲到底部才判定错误
            if self.stage == "down" and desc and drop > max_drop * 0.2 and valgus:
                self._trigger_error('lunge_knee')
            
            # 只要 active_errs 里有，就显示UI引导
            if 'lunge_knee' in self.active_errs:
                # 构造符合 UI 接口的字典
                if self.stage == "down":
                    vis.append({
                        'type': 'lunge_knee_guide', 
                        'knee': fk, 
                        'ankle': fa,
                        'direction': direction,
                        'ok': not valgus
                    })
                return vis, (TextConfig.ERR_LUNGE_KNEE, ColorConfig.NEON_RED), True

        return vis, ("", ColorConfig.TEXT_DIM), True