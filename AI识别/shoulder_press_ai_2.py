import cv2
import mediapipe as mp
import numpy as np
import time
from PIL import Image, ImageDraw, ImageFont

class UIComponents:
    """负责UI渲染、中文文字、小地图绘制"""
    def __init__(self):
        # 尝试加载中文字体，Windows下通常有微软雅黑，Mac下有PingFang
        # 如果报错，请修改为你电脑上确切的字体路径
        try:
            self.font_large = ImageFont.truetype("msyh.ttc", 32) # Windows默认
            self.font_small = ImageFont.truetype("msyh.ttc", 20)
        except:
            try:
                self.font_large = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 32) # Mac默认
                self.font_small = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 20)
            except:
                # 降级方案
                self.font_large = None 
                self.font_small = None
                print("【警告】未找到中文字体，将不显示中文。请指定字体路径。")

    def draw_chinese_text(self, img, text, pos, color, size='small'):
        """OpenCV不支持中文，使用PIL绘制"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        font = self.font_large if size == 'large' else self.font_small
        if font:
            draw.text(pos, text, font=font, fill=color)
        else:
            draw.text(pos, text, fill=color) # 默认字体
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def draw_dashed_line(self, img, pt1, pt2, color, thickness=2, gap=15):
        """绘制粗虚线"""
        dist = ((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)**0.5
        if dist == 0: return
        pts = []
        for i in range(int(dist/gap)):
            r = i*gap/dist
            x = int(pt1[0]*(1-r) + pt2[0]*r)
            y = int(pt1[1]*(1-r) + pt2[1]*r)
            pts.append((x,y))
        
        for i, p in enumerate(pts):
            if i % 2 == 0:
                cv2.circle(img, p, thickness, color, -1)

    def draw_mini_map(self, img, landmarks, mp_pose):
        """右下角独立火柴人"""
        h, w, _ = img.shape
        map_size = 200
        map_bg = np.zeros((map_size, map_size, 3), dtype=np.uint8)
        
        # 绘制简单的火柴人连接
        connections = mp_pose.POSE_CONNECTIONS
        
        # 提取需要的点并缩放到小地图
        points_map = {}
        for idx, lm in enumerate(landmarks):
            # 只要上半身关键点 11-24
            if 11 <= idx <= 24: 
                # 归一化坐标映射到 map_size
                # 简单居中处理：假设人cx在0.5, cy在0.5
                cx = int(lm.x * map_size)
                cy = int(lm.y * map_size) 
                # 修正位置让其居中显示
                cx = int((lm.x - 0.2) * map_size * 1.5) # 稍微放大
                cy = int((lm.y - 0.1) * map_size * 1.5)
                points_map[idx] = (cx, cy)
                cv2.circle(map_bg, (cx, cy), 3, (0, 255, 255), -1)

        # 连线
        for p1_idx, p2_idx in connections:
            if p1_idx in points_map and p2_idx in points_map:
                cv2.line(map_bg, points_map[p1_idx], points_map[p2_idx], (255, 255, 255), 2)

        # 叠加到主图右下角
        img[h-map_size:h, w-map_size:w] = map_bg


class ShoulderPressPro:
    def __init__(self):
        # 核心计数与状态
        self.counter = 0
        self.stage = None # 'up' or 'down'
        self.is_active_exercise = False # 动作相似度：是否在做推举
        
        # 纠错逻辑计数器 (Streak)
        self.streak_bad_forearm = 0
        self.streak_good_forearm = 0
        self.streak_bad_shrug = 0
        self.streak_good_shrug = 0
        
        # 当前是否处于报错状态 (常显Flag)
        self.err_forearm_active = False
        self.err_shrug_active = False
        
        # 当前单次动作内的错误标记
        self.current_rep_bad_forearm = False
        self.current_rep_bad_shrug = False
        
        # 阈值参数
        self.VERTICAL_THRESHOLD = 20 # 小臂垂直容差度数
        self.SHRUG_THRESHOLD = 0.25  # 耸肩系数 (耳肩距离/躯干长度)，越小越耸肩
        self.ELBOW_ANGLE_UP = 150
        self.ELBOW_ANGLE_DOWN = 80

        self.ui = UIComponents()

    def calculate_angle(self, a, b, c=None, mode='3point'):
        """通用角度计算"""
        a = np.array(a)
        b = np.array(b)
        
        if mode == 'vertical':
            # 计算向量 b->a 与 垂直线(0, -1) 的夹角 (用于小臂)
            # a: wrist, b: elbow
            vec = a - b
            vertical = np.array([0, -1])
            # 简单的几何计算，取绝对值
            angle = np.degrees(np.arccos(np.dot(vec, vertical) / (np.linalg.norm(vec) * np.linalg.norm(vertical) + 1e-6)))
            # 如果大于90度（手朝下了），修正一下
            if angle > 90: angle = 180 - angle
            return angle
            
        elif mode == '3point':
            c = np.array(c)
            radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            angle = np.abs(radians*180.0/np.pi)
            if angle > 180.0: angle = 360 - angle
            return angle

    def detect_shrug(self, landmarks):
        """
        耸肩检测算法：
        计算 (耳朵到肩膀距离) / (肩膀到髋部距离) 的比例。
        耸肩时，耳朵和肩膀会靠近，比率变小。
        """
        def get_pos(idx): return np.array([landmarks[idx].x, landmarks[idx].y])
        
        # 左右侧分别计算
        dist_ear_shoulder_l = np.linalg.norm(get_pos(7) - get_pos(11)) # 左耳-左肩
        torso_len_l = np.linalg.norm(get_pos(11) - get_pos(23))        # 左肩-左髋
        ratio_l = dist_ear_shoulder_l / (torso_len_l + 1e-6)

        dist_ear_shoulder_r = np.linalg.norm(get_pos(8) - get_pos(12))
        torso_len_r = np.linalg.norm(get_pos(12) - get_pos(24))
        ratio_r = dist_ear_shoulder_r / (torso_len_r + 1e-6)

        # 返回最小的比率（最严重的耸肩）
        return min(ratio_l, ratio_r)

    def process(self):
        cap = cv2.VideoCapture(0)
        # 设置高分辨率
        cap.set(3, 1280)
        cap.set(4, 720)

        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        
        with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                # 镜像 + 颜色转换
                frame = cv2.flip(frame, 1)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = pose.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                
                h, w, _ = image.shape

                # === 逻辑处理区 ===
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    
                    # 1. 提取关键点坐标
                    def get_coords(idx): 
                        return [landmarks[idx].x, landmarks[idx].y]
                    
                    # 关键关节
                    l_shldr, r_shldr = get_coords(11), get_coords(12)
                    l_elbow, r_elbow = get_coords(13), get_coords(14)
                    l_wrist, r_wrist = get_coords(15), get_coords(16)
                    
                    # 像素坐标 (用于绘图)
                    l_elbow_px = tuple(np.multiply(l_elbow, [w, h]).astype(int))
                    r_elbow_px = tuple(np.multiply(r_elbow, [w, h]).astype(int))
                    l_wrist_px = tuple(np.multiply(l_wrist, [w, h]).astype(int))
                    r_wrist_px = tuple(np.multiply(r_wrist, [w, h]).astype(int))

                    # 2. 动作相似度判断 (Is Active?)
                    # 简单逻辑：手腕如果高于肩膀，且在运动，认为是推举状态
                    hands_above_shoulder = (l_wrist[1] < l_shldr[1]) or (r_wrist[1] < r_shldr[1])
                    if hands_above_shoulder:
                        self.is_active_exercise = True
                    else:
                        # 如果手垂下太久，可以视为休息（此处简化，只看当前帧）
                        # 实际商业级可以加个计时器
                        self.is_active_exercise = False

                    if self.is_active_exercise:
                        # --- 计算指标 ---
                        # A. 肘关节角度 (用于计数)
                        ang_l = self.calculate_angle(l_shldr, l_elbow, l_wrist, '3point')
                        ang_r = self.calculate_angle(r_shldr, r_elbow, r_wrist, '3point')
                        avg_arm_angle = (ang_l + ang_r) / 2

                        # B. 小臂垂直度 (纠错1)
                        vert_l = self.calculate_angle(l_wrist, l_elbow, mode='vertical')
                        vert_r = self.calculate_angle(r_wrist, r_elbow, mode='vertical')
                        is_vert_bad = (vert_l > self.VERTICAL_THRESHOLD) or (vert_r > self.VERTICAL_THRESHOLD)
                        if is_vert_bad: self.current_rep_bad_forearm = True

                        # C. 耸肩检测 (纠错2)
                        shrug_ratio = self.detect_shrug(landmarks)
                        is_shrug_bad = shrug_ratio < self.SHRUG_THRESHOLD
                        if is_shrug_bad: self.current_rep_bad_shrug = True

                        # --- 状态机与计数 (State Machine) ---
                        if avg_arm_angle > self.ELBOW_ANGLE_UP:
                            self.stage = "up"
                        
                        if avg_arm_angle < self.ELBOW_ANGLE_DOWN and self.stage == 'up':
                            self.stage = "down"
                            self.counter += 1
                            
                            # === 结算本次元动作 (Cycle Check) ===
                            # 1. 小臂垂直逻辑
                            if self.current_rep_bad_forearm:
                                self.streak_bad_forearm += 1
                                self.streak_good_forearm = 0
                            else:
                                self.streak_good_forearm += 1
                                self.streak_bad_forearm = 0
                            
                            # 触发/解除
                            if self.streak_bad_forearm >= 2: self.err_forearm_active = True
                            if self.streak_good_forearm >= 1: self.err_forearm_active = False
                            
                            # 2. 耸肩逻辑
                            if self.current_rep_bad_shrug:
                                self.streak_bad_shrug += 1
                                self.streak_good_shrug = 0
                            else:
                                self.streak_good_shrug += 1
                                self.streak_bad_shrug = 0
                                
                            # 触发/解除
                            if self.streak_bad_shrug >= 2: self.err_shrug_active = True
                            if self.streak_good_shrug >= 1: self.err_shrug_active = False

                            # 重置单次标记
                            self.current_rep_bad_forearm = False
                            self.current_rep_bad_shrug = False

                    # === 可视化渲染层 (Rendering) ===
                    
                    # 1. 基础骨架
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                    
                    # 2. 辅助线交互 (Visual Guides)
                    # 如果触发了垂直错误，或者正在进行纠错时的实时反馈
                    if self.err_forearm_active:
                        # 实时变色：此刻做对了是绿，做错了是红
                        color_l = (0, 255, 0) if vert_l <= self.VERTICAL_THRESHOLD else (0, 0, 255)
                        color_r = (0, 255, 0) if vert_r <= self.VERTICAL_THRESHOLD else (0, 0, 255)
                        
                        # 画长出的虚线
                        # 计算虚线终点 (向上延伸)
                        line_len = int(h/3)
                        end_l = (l_elbow_px[0], l_elbow_px[1] - line_len)
                        end_r = (r_elbow_px[0], r_elbow_px[1] - line_len)
                        
                        self.ui.draw_dashed_line(image, l_elbow_px, end_l, color_l, thickness=4)
                        self.ui.draw_dashed_line(image, r_elbow_px, end_r, color_r, thickness=4)

                    # 3. 小地图 (Mini Map)
                    self.ui.draw_mini_map(image, landmarks, mp_pose)

                # === UI 界面层 (UI Overlay) ===
                
                # 半透明背景条
                overlay = image.copy()
                cv2.rectangle(overlay, (0, 0), (400, 180), (40, 40, 40), -1) # 左上信息栏
                
                # 底部提示栏背景
                cv2.rectangle(overlay, (0, h-80), (w, h), (30, 30, 30), -1)
                
                alpha = 0.8
                image = cv2.addWeighted(overlay, alpha, image, 1 - alpha, 0)
                
                # 1. 计次显示
                cv2.putText(image, f"REPS: {self.counter}", (20, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, (255, 255, 255), 2)
                
                # 2. 状态/相似度提示
                status_color = (100, 255, 100) if self.is_active_exercise else (200, 200, 200)
                status_text = "训练中" if self.is_active_exercise else "待机中 (请举起手)"
                image = self.ui.draw_chinese_text(image, status_text, (20, 80), status_color, 'small')

                # 3. 智能纠错提示区 (Priority System)
                # 优先级：垂直错误 > 耸肩错误 > 鼓励 > 默认
                msg_text = ""
                msg_color = (255, 255, 255)
                
                if self.err_forearm_active:
                    msg_text = "⚠️ 纠错：小臂全程垂直于地面效果更好！"
                    msg_color = (50, 50, 255) # Red
                elif self.err_shrug_active:
                    msg_text = "⚠️ 纠错：动作中耸肩影响训练效果！"
                    msg_color = (50, 150, 255) # Orange/Red
                elif self.is_active_exercise and not self.err_forearm_active and not self.err_shrug_active and self.counter > 0:
                    # 简单的鼓励逻辑：在动作Up阶段显示
                    if self.stage == 'up':
                        msg_text = "✨ 真棒！动作正确了！"
                        msg_color = (50, 255, 50) # Green
                
                if msg_text:
                    # 居中显示在底部
                    image = self.ui.draw_chinese_text(image, msg_text, (50, h-60), msg_color, 'large')

                # 4. 关闭按钮提示
                cv2.putText(image, "Press 'q' to Quit", (w-200, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (150, 150, 150), 1)

                cv2.imshow('AI Shoulder Press Pro', image)
                
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = ShoulderPressPro()
    app.process()