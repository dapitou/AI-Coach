import time
from config import TextConfig, AlgoConfig, ColorConfig
from utils import PointSmoother, GeomUtils
from algorithms.spine import SpineAlgo
from algorithms.press import process_press
from algorithms.squat import process_squat
from algorithms.front_raise import process_front_raise
from algorithms.lunge import process_lunge

class LogicEngine:
    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.mode = TextConfig.ACT_PRESS
        self.counter = 0
        self.bad_reps = 0 
        self.current_rep_has_error = False 
        self.stage = "start"
        self.history = {}
        self.active_errs = set()
        self.error_counts = {} 
        self.msg = ""
        self.msg_color = ColorConfig.TEXT_DIM
        self.msg_timer = 0
        self.last_act = time.time()
        self.cycle_flags = {}
        self.max_torso_len = 0.0
        self.base_shrug_dist = 0
        self.neck_curr_smooth = 0.0
        self.prev_hip_y = 0
        self.stand_hip_y = 0.0 
        self.lunge_front_idx = None 
        self.last_count_time = 0.0 
        self.facing_score_smooth = 0.0 
        self.smoother = PointSmoother(alpha=AlgoConfig.SHRUG_SMOOTH_FACTOR)
        self.spine_algo = SpineAlgo()

    def set_mode(self, m):
        if self.mode == m: return
        self.mode = m
        self.counter = 0
        self.bad_reps = 0
        self.error_counts = {}
        self.history = {}
        self.active_errs = set()
        self.msg = ""
        self.stage = "start"
        self.max_torso_len = 0.0
        self.stand_hip_y = 0.0
        self.lunge_front_idx = None
        self.last_act = time.time() - 100.0 

    def update(self, pts, world_pts, vis_scores, user_height_cm):
        if not pts: return []
        vis = []
        pts = self.smoother.filter(pts)
        scale = user_height_cm / AlgoConfig.STD_HEIGHT
        
        self.spine_algo.update(self, pts)
        
        if not self._gatekeeper(pts):
            return vis, pts
            
        if self.mode == TextConfig.ACT_PRESS: process_press(self, pts, vis, scale)
        elif self.mode == TextConfig.ACT_SQUAT: process_squat(self, pts, vis, scale)
        elif self.mode == TextConfig.ACT_RAISE: process_front_raise(self, pts, vis, scale)
        elif self.mode == TextConfig.ACT_LUNGE: process_lunge(self, pts, vis, scale)
        
        if pts.get('rounding_bad') and 'rounding' in self.active_errs:
            vis.append({'type': 'rounding_guide', 'neck': pts['neck'], 'thorax': pts['thorax'], 'waist': pts['waist'], 'hip': pts['hip']})
            
        return vis, pts

    def _gatekeeper(self, pts):
        is_similar = False
        tip = ""
        
        if self.mode == TextConfig.ACT_PRESS:
            tip = TextConfig.TIP_PRESS_DO
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                wrist_y = (pts['lw'][1]+pts['rw'][1])/2
                shou_y = (pts['ls'][1]+pts['rs'][1])/2
                if wrist_y < shou_y + 200: is_similar = True
                
        elif self.mode == TextConfig.ACT_SQUAT:
            tip = TextConfig.TIP_SQUAT_DO
            if (pts.get('ls') and pts.get('rs') and pts.get('lh') and pts.get('rh') and 
                pts.get('la') and pts.get('ra') and pts.get('lk')):
                
                shoulder_w = GeomUtils.dist(pts['ls'], pts['rs'])
                torso_len = GeomUtils.dist(
                    ((pts['ls'][0]+pts['rs'][0])/2, (pts['ls'][1]+pts['rs'][1])/2),
                    ((pts['lh'][0]+pts['rh'][0])/2, (pts['lh'][1]+pts['rh'][1])/2)
                )
                
                if shoulder_w > 0 and torso_len > 0:
                    ankle_w = GeomUtils.dist(pts['la'], pts['ra'])
                    is_feet_open = ankle_w > shoulder_w * AlgoConfig.SQUAT_GATE_STANCE_RATIO
                    feet_y_diff = abs(pts['la'][1] - pts['ra'][1])
                    is_feet_level = feet_y_diff < torso_len * AlgoConfig.SQUAT_GATE_FEET_Y_TOL
                    shoulder_cx = (pts['ls'][0] + pts['rs'][0]) / 2
                    hip_cx = (pts['lh'][0] + pts['rh'][0]) / 2
                    is_body_align = abs(shoulder_cx - hip_cx) < shoulder_w * AlgoConfig.SQUAT_GATE_ALIGN_TOL
                    feet_cx = (pts['la'][0] + pts['ra'][0]) / 2
                    is_gravity_align = abs(hip_cx - feet_cx) < shoulder_w * AlgoConfig.SQUAT_GATE_GRAVITY_TOL
                    is_upright = pts['ls'][1] < pts['lh'][1]

                    if is_feet_open and is_feet_level and is_body_align and is_gravity_align and is_upright:
                        is_similar = True
                
        elif self.mode == TextConfig.ACT_RAISE:
            tip = TextConfig.TIP_RAISE_DO
            if pts.get('lw') and pts.get('rw') and pts.get('ls') and pts.get('rs'):
                shoulder_w = GeomUtils.dist(pts['ls'], pts['rs'])
                wrist_w = GeomUtils.dist(pts['lw'], pts['rw'])
                cond_width = wrist_w < shoulder_w * AlgoConfig.RAISE_GATE_WIDTH_RATIO
                wrist_cx = (pts['lw'][0] + pts['rw'][0]) / 2
                shoulder_cx = (pts['ls'][0] + pts['rs'][0]) / 2
                cond_center = abs(wrist_cx - shoulder_cx) < shoulder_w * AlgoConfig.RAISE_GATE_CENTER_TOL
                
                if shoulder_w > 0 and cond_width and cond_center:
                    is_similar = True
        
        elif self.mode == TextConfig.ACT_LUNGE:
            tip = TextConfig.TIP_LUNGE_DO
            if pts.get('lt') and pts.get('rt') and pts.get('ls') and pts.get('rs'):
                foot_x_dist = abs(pts['lt'][0] - pts['rt'][0])
                shoulder_w = GeomUtils.dist(pts['ls'], pts['rs'])
                
                # [修复] 变量名对齐: LUNGE_STANCE_RATIO (去掉 _X)
                if foot_x_dist > shoulder_w * AlgoConfig.LUNGE_STANCE_RATIO:
                    is_similar = True

        if is_similar:
            self.last_act = time.time()
            if self.msg == tip: self.msg = ""
            return True
        else:
            if time.time() - self.last_act > AlgoConfig.GATEKEEPER_TIMEOUT:
                if not self.active_errs: self._set_msg(tip, ColorConfig.NEON_RED, perm=True)
            return False

    def _check_shrug_adaptive(self, p, scale, stage_check="up"):
        if not (p.get('ls') and p.get('rs') and p.get('le_ear') and p.get('re_ear')): return
        shou_y = (p['ls'][1] + p['rs'][1]) / 2
        ear_y = (p['le_ear'][1] + p['re_ear'][1]) / 2
        curr_dist = max(0, shou_y - ear_y)
        self.neck_curr_smooth = curr_dist
        is_relax = (self.stage != stage_check)
        if is_relax:
            if curr_dist > 0:
                if self.base_shrug_dist == 0: self.base_shrug_dist = self.neck_curr_smooth
                else: self.base_shrug_dist = max(self.base_shrug_dist, self.neck_curr_smooth)
            if 'shrug' in self.active_errs:
                self.active_errs.remove('shrug')
                self.cycle_flags['shrug'] = True
        if self.stage == stage_check and self.base_shrug_dist > 0:
            ratio = self.neck_curr_smooth / (self.base_shrug_dist + 1e-6)
            if ratio < AlgoConfig.SHRUG_RATIO_TH: self.cycle_flags['shrug'] = False

    def _reset_flags(self, keys):
        for k in keys:
            if k in ["depth", "range", "lunge_knee"]: self.cycle_flags[k] = False
            else: self.cycle_flags[k] = True

    def _end_cycle(self, keys):
        fixed, triggered = False, False
        
        if time.time() - self.last_count_time < AlgoConfig.COUNT_COOLDOWN:
            return 

        for i, k in enumerate(keys):
            res = self.cycle_flags.get(k, True)
            
            if not res:
                self.error_counts[k] = self.error_counts.get(k, 0) + 1
                self.current_rep_has_error = True

            st = self._update_hist(k, res)
            is_active = (st == 'TRIGGER') or (k in self.active_errs)
            
            if is_active and not res:
                triggered = True
                for lower_k in keys[i+1:]:
                    if lower_k in self.active_errs: self.active_errs.remove(lower_k)
                break
            if st == 'FIXED': fixed = True
        
        if self.current_rep_has_error: self.bad_reps += 1

        if triggered: self.sound.play('error')
        elif fixed:
            self.sound.play('success')
            if not self.active_errs: self._set_msg(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, 3.0)
        elif not any(k in self.active_errs for k in keys):
            self.sound.play('count')
            
        self.last_count_time = time.time()

    def _update_hist(self, k, res, block=False):
        if k not in self.history: self.history[k] = []
        self.history[k].append(res)
        if len(self.history[k]) > 5: self.history[k].pop(0)
        if k in self.active_errs:
            if res:
                self.active_errs.remove(k)
                return 'FIXED'
        else:
            if not block and len(self.history[k])>=2 and not any(self.history[k][-2:]):
                self.active_errs.add(k)
                return 'TRIGGER'
        return 'NONE'

    def _set_msg(self, t, c, dur=0, perm=False):
        if time.time() < self.msg_timer: return
        self.msg, self.msg_color = t, c
        self.msg_timer = (time.time() + dur) if dur > 0 else 0

    def get_msg(self):
        if time.time() < self.msg_timer or self.msg_timer == 0: return self.msg, self.msg_color
        return "", ColorConfig.TEXT_DIM