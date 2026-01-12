import cv2
import mediapipe as mp
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont
from dataclasses import dataclass
from typing import List, Tuple, Dict

# ==========================================
# 1. 系统配置 (Config)
# ==========================================
class Config:
    WINDOW_NAME = "AI Fitness Pro - Final"
    
    # 内部渲染分辨率 (32:9 超宽屏布局: 1920x540)
    # 左屏: 960x540 (摄像头) | 右屏: 960x540 (数字孪生)
    CANVAS_W = 1920
    CANVAS_H = 540
    HALF_W = 960
    
    # 颜色库 (BGR)
    C_BG = (20, 20, 30)           # 墨黑背景
    C_GRID = (40, 40, 50)         # 网格
    C_OK = (0, 255, 0)            # 纯绿 (正确)
    C_ERR = (0, 0, 255)           # 纯红 (错误)
    C_WARN = (0, 255, 255)        # 黄色
    C_WHITE = (255, 255, 255)
    C_TWIN_BODY = (100, 100, 100) # 灰色躯干
    C_TWIN_LINE = (200, 200, 200) # 浅灰骨骼
    
    # 阈值
    VISIBILITY_THRESH = 0.5
    
    # 字体设置 (Windows 常见中文字体)
    FONTS = ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/arial.ttf"]

# ==========================================
# 2. 基础工具 (Utils)
# ==========================================
class Utils:
    @staticmethod
    def calc_angle(a, b, c):
        if not (a and b and c): return 0
        a, b, c = np.array(a), np.array(b), np.array(c)
        rad = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        ang = np.abs(rad * 180.0 / np.pi)
        return 360 - ang if ang > 180 else ang

    @staticmethod
    def draw_text_pil(img_bgr, text, pos, color, size, anchor="lt"):
        """ 使用PIL绘制中文，绝对可靠 """
        img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        
        font = None
        for fp in Config.FONTS:
            try:
                font = ImageFont.truetype(fp, size)
                break
            except:
                continue
        if font is None: font = ImageFont.load_default()
        
        # 计算位置
        bbox = draw.textbbox((0, 0), text, font=font)
        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x, y = pos
        if "c" in anchor: x -= w // 2
        if "m" in anchor: y -= h // 2
        
        draw.text((x, y), text, font=font, fill=color[::-1]) # RGB -> BGR
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

# ==========================================
# 3. 核心逻辑状态机 (Logic Core)
# ==========================================
class ErrorTracker:
    """ 单个错误项的追踪器 """
    def __init__(self, name):
        self.name = name
        self.consecutive_count = 0  # 连续错误计数
        self.is_active = False      # 是否处于纠错显示模式
        self.current_rep_bad = False # 当前动作循环是否出错

    def reset_rep_flag(self):
        """ 新动作开始，重置当前Flag """
        self.current_rep_bad = False

    def mark_bad(self):
        """ 动作过程中检测到错误 """
        self.current_rep_bad = True

    def finish_rep(self):
        """ 动作结束，结算状态 """
        if self.current_rep_bad:
            # 本次错了
            self.consecutive_count += 1
            # 连续2次错 -> 激活纠错
            if self.consecutive_count >= 2:
                self.is_active = True
        else:
            # 本次对了 -> 立即重置
            self.consecutive_count = 0
            self.is_active = False # 只有做对一次，立马解除

class LogicEngine:
    def __init__(self):
        self.pose = mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5, model_complexity=1)
        self.mode = "推举"
        self.count = 0
        self.stage = "UP" # UP/DOWN
        
        # 错误追踪器集合
        self.trackers = {
            "press_vertical": ErrorTracker("小臂不垂直"),
            "press_shrug": ErrorTracker("耸肩"),
            "squat_depth": ErrorTracker("深蹲幅度不足"),
            "squat_valgus": ErrorTracker("膝盖内扣")
        }
        
        # 视觉反馈数据
        self.visual_lines = []  # 存线段
        self.visual_circles = [] # 存圆
        self.msg_text = ""
        self.msg_color = Config.C_OK

    def switch_mode(self, mode):
        self.mode = mode
        self.count = 0
        self.stage = "UP"
        for t in self.trackers.values():
            t.consecutive_count = 0
            t.is_active = False
            t.current_rep_bad = False

    def update(self, frame_rgb, w, h):
        # 1. MediaPipe推理
        res = self.pose.process(frame_rgb)
        self.visual_lines = []
        self.visual_circles = []
        kp = {}
        
        if not res.pose_landmarks:
            self.msg_text = "未检测到人体"
            self.msg_color = Config.C_WARN
            return kp

        # 2. 关键点映射
        lm = res.pose_landmarks.landmark
        idx = mp.solutions.pose.PoseLandmark
        def g(i): 
            if lm[i].visibility < Config.VISIBILITY_THRESH: return None
            return (int(lm[i].x * w), int(lm[i].y * h))

        kp = {
            'nose': g(idx.NOSE),
            'l_sh': g(idx.LEFT_SHOULDER), 'r_sh': g(idx.RIGHT_SHOULDER),
            'l_el': g(idx.LEFT_ELBOW), 'r_el': g(idx.RIGHT_ELBOW),
            'l_wr': g(idx.LEFT_WRIST), 'r_wr': g(idx.RIGHT_WRIST),
            'l_hip': g(idx.LEFT_HIP), 'r_hip': g(idx.RIGHT_HIP),
            'l_knee': g(idx.LEFT_KNEE), 'r_knee': g(idx.RIGHT_KNEE),
            'l_ank': g(idx.LEFT_ANKLE), 'r_ank': g(idx.RIGHT_ANKLE),
            'l_foot': g(idx.LEFT_FOOT_INDEX), 'r_foot': g(idx.RIGHT_FOOT_INDEX)
        }

        # 3. 逻辑分发
        if self.mode == "推举": self._process_press(kp)
        elif self.mode == "深蹲": self._process_squat(kp)
        
        # 4. 生成提示文字
        self._generate_msg()
        
        return kp

    def _process_press(self, kp):
        # --- 计次逻辑 ---
        if kp['l_el'] and kp['l_sh'] and kp['l_wr']:
            angle = Utils.calc_angle(kp['l_sh'], kp['l_el'], kp['l_wr'])
            # 推举: 150度+为直臂(UP), 90度-为底端(DOWN)
            if angle > 150:
                if self.stage == "DOWN":
                    self.stage = "UP"
                    self.count += 1
                    self._on_rep_end(["press_vertical", "press_shrug"])
            elif angle < 90:
                if self.stage == "UP":
                    self.stage = "DOWN"
                    self._on_rep_start(["press_vertical", "press_shrug"])

        # --- 纠错检测 (实时打标) ---
        if self.stage in ["UP", "DOWN"]: # 动作中
            # 1. 小臂垂直检测
            if kp['l_el'] and kp['l_wr'] and kp['r_el'] and kp['r_wr']:
                # 只有手高于肘才算
                if kp['l_wr'][1] < kp['l_el'][1]:
                    # 阈值判断
                    bad_l = abs(kp['l_el'][0] - kp['l_wr'][0]) > 40
                    bad_r = abs(kp['r_el'][0] - kp['r_wr'][0]) > 40
                    
                    if bad_l or bad_r:
                        self.trackers["press_vertical"].mark_bad()
                    
                    # --- 动效绘制 (仅当Active时显示) ---
                    tracker = self.trackers["press_vertical"]
                    if tracker.is_active:
                        # 总是绘制辅助线，颜色随实时状态变
                        for (el, wr, is_bad) in [(kp['l_el'], kp['l_wr'], bad_l), (kp['r_el'], kp['r_wr'], bad_r)]:
                            color = Config.C_ERR if is_bad else Config.C_OK
                            # 垂直向上的线
                            self.visual_lines.append((el, (el[0], el[1]-200), color, 3))

            # 2. 耸肩检测
            if kp['nose'] and kp['l_sh'] and kp['r_sh']:
                sh_y = (kp['l_sh'][1] + kp['r_sh'][1]) / 2
                sh_w = abs(kp['l_sh'][0] - kp['r_sh'][0])
                neck = abs(kp['nose'][1] - sh_y)
                if neck < sh_w * 0.25:
                    self.trackers["press_shrug"].mark_bad()
                    # 耸肩无动效要求

    def _process_squat(self, kp):
        # --- 计次逻辑 ---
        if kp['l_hip'] and kp['l_knee'] and kp['l_ank']:
            angle = Utils.calc_angle(kp['l_hip'], kp['l_knee'], kp['l_ank'])
            if angle > 160:
                if self.stage == "DOWN":
                    self.stage = "UP"
                    self.count += 1
                    self._on_rep_end(["squat_depth", "squat_valgus"])
            elif angle < 100:
                if self.stage == "UP":
                    self.stage = "DOWN"
                    self._on_rep_start(["squat_depth", "squat_valgus"])
            
            # --- 纠错检测 (下蹲过程中) ---
            if angle < 140:
                # 1. 深度
                hip_y = (kp['l_hip'][1] + kp['r_hip'][1]) / 2
                knee_y = (kp['l_knee'][1] + kp['r_knee'][1]) / 2
                # Y向下为正。DeepEnough: HipY >= KneeY
                is_deep = hip_y >= knee_y
                if not is_deep and angle < 110: # 接近底端才判错
                    self.trackers["squat_depth"].mark_bad()
                
                # 动效 (Active时显示)
                if self.trackers["squat_depth"].is_active:
                    c = Config.C_OK if is_deep else Config.C_ERR
                    mh = ((kp['l_hip'][0]+kp['r_hip'][0])//2, int(hip_y))
                    mk = ((kp['l_knee'][0]+kp['r_knee'][0])//2, int(knee_y))
                    self.visual_circles.append((mh, 8, c, True))
                    self.visual_circles.append((mk, 8, c, False))
                    self.visual_lines.append((mh, mk, c, 2))

                # 2. 内扣
                if kp['l_foot'] and kp['r_foot']:
                    bad_l = abs(kp['l_knee'][0] - kp['l_foot'][0]) > 30
                    bad_r = abs(kp['r_knee'][0] - kp['r_foot'][0]) > 30
                    if bad_l or bad_r:
                        self.trackers["squat_valgus"].mark_bad()
                    
                    if self.trackers["squat_valgus"].is_active:
                        for (foot, is_bad) in [(kp['l_foot'], bad_l), (kp['r_foot'], bad_r)]:
                            c = Config.C_ERR if is_bad else Config.C_OK
                            self.visual_lines.append((foot, (foot[0], foot[1]-150), c, 3))

    def _on_rep_start(self, keys):
        for k in keys: self.trackers[k].reset_rep_flag()

    def _on_rep_end(self, keys):
        for k in keys: self.trackers[k].finish_rep()

    def _generate_msg(self):
        # 优先级: Active Errors -> Success (last rep) -> Idle
        active_errs = [t.name for t in self.trackers.values() if t.is_active]
        
        if active_errs:
            # 取第一个错误显示
            if "小臂" in active_errs[0]: txt = "纠错：小臂全程垂直于地面效果更好！"
            elif "耸肩" in active_errs[0]: txt = "纠错：动作中耸肩影响训练效果！"
            elif "幅度" in active_errs[0]: txt = "纠错：蹲至大腿平行地面地面效果更好！"
            elif "内扣" in active_errs[0]: txt = "纠错：注意膝关节不要内扣！"
            else: txt = "注意动作标准"
            self.msg_text = txt
            self.msg_color = Config.C_ERR
        else:
            # 没有Active错误
            if self.count > 0:
                self.msg_text = "真棒！动作正确了！"
                self.msg_color = Config.C_OK
            else:
                self.msg_text = f"请做“{self.mode}”动作"
                self.msg_color = Config.C_ERR

# ==========================================
# 4. 渲染引擎 (Renderer)
# ==========================================
class App:
    def __init__(self):
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        self.logic = LogicEngine()
        self.menu_open = False
        
        cv2.namedWindow(Config.WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.setMouseCallback(Config.WINDOW_NAME, self._mouse_handler)

    def _mouse_handler(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            # 需要把窗口坐标映射回 Canvas (1920x540) 坐标
            # 这里简化逻辑，假设用户没有把窗口缩放得太离谱
            # 按钮区在左上角
            if 20 < x < 200 and 20 < y < 80:
                self.menu_open = not self.menu_open
            
            if self.menu_open:
                if 20 < x < 200 and 80 < y < 130:
                    self.logic.switch_mode("推举")
                    self.menu_open = False
                elif 20 < x < 200 and 130 < y < 180:
                    self.logic.switch_mode("深蹲")
                    self.menu_open = False

    def draw_canvas(self, frame_cam, kp):
        # 1. 创建全尺寸画布
        canvas = np.zeros((Config.CANVAS_H, Config.CANVAS_W, 3), dtype=np.uint8)
        canvas[:] = Config.C_BG # 填充背景
        
        # 2. 处理左侧摄像头画面 (960x540)
        h, w = frame_cam.shape[:2]
        # 缩放至高度540
        scale = Config.CANVAS_H / h
        new_w = int(w * scale)
        img_left = cv2.resize(frame_cam, (new_w, Config.CANVAS_H))
        img_left = cv2.flip(img_left, 1) # 镜像
        
        # 绘制视觉辅助 (在 Left Image 上)
        # 注意: logic中的坐标是基于 resize 之前的
        # 我们需要在 logic.update 传入 resize 之后的宽，或者在这里映射
        # 为了精确，我们让 logic.update 接收 img_left 的宽
        
        # 贴入左侧
        off_x = (Config.HALF_W - new_w) // 2
        canvas[:, off_x:off_x+new_w] = img_left
        
        # 在画布上绘制辅助线 (基于画布坐标)
        # Logic 返回的坐标已经是基于 960x540 (如果我们在update里传入的话)
        # 让我们调整 logic.update 的调用
        
        # 3. 绘制右侧数字孪生 (Digital Twin)
        self._draw_twin(canvas, kp, Config.HALF_W, 0)
        
        # 4. 绘制UI层 (最上层)
        self._draw_ui(canvas)
        
        return canvas

    def _draw_twin(self, canvas, kp, offset_x, offset_y):
        # 绘制区域中心
        cx = offset_x + Config.HALF_W // 2
        cy = Config.CANVAS_H // 2
        
        if not kp: return

        # 坐标映射: 假设原始坐标中心在 (960/2, 540/2)
        # 我们需要把它们搬运到 cx, cy
        def tr(pt):
            if pt is None: return None
            # 原始宽960, 高540.
            # 归一化到中心
            tx = pt[0] - 480 
            ty = pt[1] - 270
            return (int(cx + tx), int(cy + ty))

        # 1. 躯干 (Fill Poly) - 强制构建
        pts_body = []
        l_sh, r_sh = tr(kp.get('l_sh')), tr(kp.get('r_sh'))
        l_hip, r_hip = tr(kp.get('l_hip')), tr(kp.get('r_hip'))
        
        # 容错补全
        if l_sh and r_sh:
            if not l_hip and not r_hip: # 只有上半身
                l_hip = (l_sh[0], l_sh[1] + 200)
                r_hip = (r_sh[0], r_sh[1] + 200)
            elif not l_hip: l_hip = (l_sh[0], r_hip[1])
            elif not r_hip: r_hip = (r_sh[0], l_hip[1])
            
            pts_body = np.array([l_sh, r_sh, r_hip, l_hip], np.int32)
            cv2.fillPoly(canvas, [pts_body], Config.C_TWIN_BODY)
            cv2.polylines(canvas, [pts_body], True, Config.C_WHITE, 2)
            
            # 头部
            if kp.get('nose'):
                nose = tr(kp['nose'])
                r = int(abs(l_sh[0]-r_sh[0]) * 0.35)
                cv2.circle(canvas, nose, r, Config.C_TWIN_BODY, -1)
                cv2.circle(canvas, nose, r, Config.C_WHITE, 2)

        # 2. 四肢
        limbs = [('l_sh','l_el'), ('l_el','l_wr'), ('r_sh','r_el'), ('r_el','r_wr'),
                 ('l_hip','l_knee'), ('l_knee','l_ank'), ('l_ank','l_foot'),
                 ('r_hip','r_knee'), ('r_knee','r_ank'), ('r_ank','r_foot')]
        
        for p1, p2 in limbs:
            tp1, tp2 = tr(kp.get(p1)), tr(kp.get(p2))
            if tp1 and tp2:
                cv2.line(canvas, tp1, tp2, Config.C_TWIN_LINE, 4)
                cv2.circle(canvas, tp1, 5, Config.C_WHITE, -1)

    def _draw_ui(self, canvas):
        # 1. 菜单按钮 (左上角)
        cv2.rectangle(canvas, (20, 20), (200, 70), Config.C_GRID, -1)
        cv2.rectangle(canvas, (20, 20), (200, 70), Config.C_WARN, 2)
        canvas = Utils.draw_text_pil(canvas, f"模式: {self.logic.mode}", (30, 25), Config.C_WHITE, 30)
        
        if self.menu_open:
            cv2.rectangle(canvas, (20, 70), (200, 170), (10,10,10), -1)
            canvas = Utils.draw_text_pil(canvas, "推举", (30, 80), Config.C_WHITE, 30)
            canvas = Utils.draw_text_pil(canvas, "深蹲", (30, 130), Config.C_WHITE, 30)

        # 2. 计数器 (正中央) - 巨大
        cx = Config.CANVAS_W // 2
        cy = 80
        # 底圆
        cv2.circle(canvas, (cx, cy), 60, Config.C_BG, -1)
        cv2.circle(canvas, (cx, cy), 60, Config.C_WARN, 4)
        # 数字
        txt = str(self.logic.count)
        canvas = Utils.draw_text_pil(canvas, txt, (cx, cy), Config.C_OK, 80, "cm")
        
        # 3. 底部提示栏
        bar_y = Config.CANVAS_H - 80
        cv2.rectangle(canvas, (0, bar_y), (Config.CANVAS_W, Config.CANVAS_H), Config.C_GRID, -1)
        cv2.line(canvas, (0, bar_y), (Config.CANVAS_W, bar_y), Config.C_WARN, 2)
        if self.logic.msg_text:
            canvas = Utils.draw_text_pil(canvas, self.logic.msg_text, (Config.CANVAS_W//2, bar_y + 40), self.logic.msg_color, 40, "cm")

    def run(self):
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret: break
            
            # 为了保证坐标一致性，先做一次统一Resize
            # 把摄像头画面 Resize 到 960x540 用于推理和显示左屏
            # 保持比例
            h, w = frame.shape[:2]
            target_h = Config.CANVAS_H
            target_w = int(w * (target_h / h))
            frame_resized = cv2.resize(frame, (target_w, target_h))
            frame_resized = cv2.flip(frame_resized, 1)
            
            # 核心推理 (传入Resize后的尺寸)
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            kp = self.logic.update(frame_rgb, target_w, target_h)
            
            # 渲染全画布
            canvas = self.draw_canvas(frame_resized, kp)
            
            # 补充绘制: 视觉辅助线 (因为线是在Logic里生成的，基于target_w/h坐标)
            # 需要加上左屏偏移量 off_x
            off_x = (Config.HALF_W - target_w) // 2
            
            for line in self.logic.visual_lines:
                pt1, pt2, color, thick = line
                p1 = (pt1[0] + off_x, pt1[1])
                p2 = (pt2[0] + off_x, pt2[1])
                cv2.line(canvas, p1, p2, color, thick)
                
            for circle in self.logic.visual_circles:
                pt, r, color, fill = circle
                p = (pt[0] + off_x, pt[1])
                th = -1 if fill else 2
                cv2.circle(canvas, p, r, color, th)

            # 显示 (最终Resize适应屏幕)
            cv2.imshow(Config.WINDOW_NAME, canvas)
            
            if cv2.waitKey(1) & 0xFF == 27: break
            
        self.cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    App().run()