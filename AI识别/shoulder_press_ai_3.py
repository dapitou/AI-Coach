import cv2
import mediapipe as mp
import numpy as np
import math
from PIL import Image, ImageDraw, ImageFont

# --- 定义低饱和度/未来感配色方案 ---
COLOR_FUTURISTIC_WHITE = (255, 240, 200)   # 科技白/浅蓝 (BGR)
COLOR_ERROR_MUTED = (50, 100, 255)         # 柔和警示橙 (BGR)
COLOR_ENCOURAGE_MUTED = (100, 255, 200)    # 静谧浅绿 (BGR)
COLOR_GUIDE_BAD = (50, 50, 200)            # 辅助线错误 (Muted Red)
COLOR_GUIDE_GOOD = (100, 255, 150)         # 辅助线正确 (Muted Green)
# ------------------------------------


class UIComponents:
    """负责UI渲染、中文文字、Mannequin绘制"""
    def __init__(self):
        # 尝试加载中文字体
        try:
            self.font_large = ImageFont.truetype("msyh.ttc", 36)
            self.font_small = ImageFont.truetype("msyh.ttc", 24)
        except:
            # Fallback handling
            self.font_large = None 
            self.font_small = None
            print("【警告】未找到中文字体，将不显示中文。")

    def draw_chinese_text(self, img, text, pos, color, size='small'):
        """使用PIL绘制中文"""
        img_pil = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        draw = ImageDraw.Draw(img_pil)
        font = self.font_large if size == 'large' else self.font_small
        if font:
            # PIL使用RGB颜色，需要将BGR转为RGB
            rgb_color = (color[2], color[1], color[0]) 
            draw.text(pos, text, font=font, fill=rgb_color)
        else:
            draw.text(pos, text, fill=color)
        return cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)

    def draw_dashed_line(self, img, pt1, pt2, color, thickness=4, gap=15):
        """绘制粗虚线（用于辅助）"""
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

    def draw_mannequin(self, canvas, landmarks, correction_active, vert_l, vert_r, threshold):
        """
        绘制高级 Mannequin，并叠加辅助线
        """
        map_h, map_w, _ = canvas.shape
        mp_pose = mp.solutions.pose
        
        def map_coords(lm):
            # Mannequin 缩放和偏移量
            x = int((lm.x - 0.2) * map_w * 1.5) 
            y = int((lm.y - 0.1) * map_h * 1.5)
            return (x, y)

        points = {i: map_coords(landmarks[i]) for i in range(11, 33)}
        line_color = (100, 100, 100) # 关节连线颜色
        joint_color = (255, 255, 255) # 关节颜色
        thickness = 8 

        connections = [
            (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_SHOULDER.value),
            (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_HIP.value),
            (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_HIP.value),
            (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.RIGHT_HIP.value),
            (mp_pose.PoseLandmark.LEFT_HIP.value, mp_pose.PoseLandmark.LEFT_KNEE.value),
            (mp_pose.PoseLandmark.RIGHT_HIP.value, mp_pose.PoseLandmark.RIGHT_KNEE.value),
            (mp_pose.PoseLandmark.LEFT_KNEE.value, mp_pose.PoseLandmark.LEFT_ANKLE.value),
            (mp_pose.PoseLandmark.RIGHT_KNEE.value, mp_pose.PoseLandmark.RIGHT_ANKLE.value),
            (mp_pose.PoseLandmark.LEFT_SHOULDER.value, mp_pose.PoseLandmark.LEFT_ELBOW.value),
            (mp_pose.PoseLandmark.RIGHT_SHOULDER.value, mp_pose.PoseLandmark.RIGHT_ELBOW.value),
            (mp_pose.PoseLandmark.LEFT_ELBOW.value, mp_pose.PoseLandmark.LEFT_WRIST.value),
            (mp_pose.PoseLandmark.RIGHT_ELBOW.value, mp_pose.PoseLandmark.RIGHT_WRIST.value),
        ]
        
        for p1_idx, p2_idx in connections:
            if p1_idx in points and p2_idx in points:
                cv2.line(canvas, points[p1_idx], points[p2_idx], line_color, thickness)
        
        for idx in points:
            cv2.circle(canvas, points[idx], 6, joint_color, -1)

        if mp_pose.PoseLandmark.LEFT_SHOULDER.value in points and mp_pose.PoseLandmark.RIGHT_SHOULDER.value in points:
             head_mid = (points[mp_pose.PoseLandmark.LEFT_SHOULDER.value][0] + points[mp_pose.PoseLandmark.RIGHT_SHOULDER.value][0]) // 2
             cv2.circle(canvas, (head_mid, points[mp_pose.PoseLandmark.LEFT_SHOULDER.value][1] - 50), 30, line_color, -1)
        
        # 叠加辅助线 (使用低饱和度颜色)
        if correction_active:
            l_elbow_idx = mp_pose.PoseLandmark.LEFT_ELBOW.value
            r_elbow_idx = mp_pose.PoseLandmark.RIGHT_ELBOW.value
            if l_elbow_idx in points and r_elbow_idx in points:
                l_elbow_px = points[l_elbow_idx]
                r_elbow_px = points[r_elbow_idx]
                
                color_l = COLOR_GUIDE_GOOD if vert_l <= threshold else COLOR_GUIDE_BAD
                color_r = COLOR_GUIDE_GOOD if vert_r <= threshold else COLOR_GUIDE_BAD
                
                line_len = int(map_h/3)
                end_l = (l_elbow_px[0], l_elbow_px[1] - line_len)
                end_r = (r_elbow_px[0], r_elbow_px[1] - line_len)
                
                self.draw_dashed_line(canvas, l_elbow_px, end_l, color_l, thickness=5)
                self.draw_dashed_line(canvas, r_elbow_px, end_r, color_r, thickness=5)
            
        return canvas


class ShoulderPressPro:
    def __init__(self):
        # 状态机初始化 (省略不变的代码)
        self.counter = 0; self.stage = None; self.is_active_exercise = False 
        self.streak_bad_forearm = 0; self.streak_good_forearm = 0
        self.streak_bad_shrug = 0; self.streak_good_shrug = 0
        self.err_forearm_active = False; self.err_shrug_active = False
        self.current_rep_bad_forearm = False; self.current_rep_bad_shrug = False
        self.show_encouragement_flag = False 
        self.VERTICAL_THRESHOLD = 20; self.SHRUG_THRESHOLD = 0.25 
        self.ELBOW_ANGLE_UP = 150; self.ELBOW_ANGLE_DOWN = 80
        self.ui = UIComponents()

    def calculate_angle(self, a, b, c=None, mode='3point'):
        a = np.array(a); b = np.array(b)
        if mode == 'vertical':
            vec = a - b; vertical = np.array([0, -1])
            angle = np.degrees(np.arccos(np.dot(vec, vertical) / (np.linalg.norm(vec) * np.linalg.norm(vertical) + 1e-6)))
            if angle > 90: angle = 180 - angle
            return angle
        elif mode == '3point':
            c = np.array(c)
            radians = np.arctan2(c[1]-b[1], c[0]-c[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
            angle = np.abs(radians*180.0/np.pi)
            if angle > 180.0: angle = 360 - angle
            return angle

    def detect_shrug(self, landmarks):
        def get_pos(idx): return np.array([landmarks[idx].x, landmarks[idx].y])
        dist_ear_shoulder_l = np.linalg.norm(get_pos(7) - get_pos(11)); torso_len_l = np.linalg.norm(get_pos(11) - get_pos(23))
        ratio_l = dist_ear_shoulder_l / (torso_len_l + 1e-6)
        dist_ear_shoulder_r = np.linalg.norm(get_pos(8) - get_pos(12)); torso_len_r = np.linalg.norm(get_pos(12) - get_pos(24))
        ratio_r = dist_ear_shoulder_r / (torso_len_r + 1e-6)
        return min(ratio_l, ratio_r)

    def process(self):
        cap = cv2.VideoCapture(0)
        
        # --- 全屏自适应目标尺寸 ---
        W_FINAL = 1920
        H_FINAL = 1080
        W_PANE = W_FINAL // 2 # 960 (左/右分屏宽度)
        H_PANE = H_FINAL      # 1080 (左/右分屏高度)

        cap.set(cv2.CAP_PROP_FRAME_WIDTH, W_FINAL)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H_FINAL)
        # --- --- ---

        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        
        with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret: break
                
                # 图像处理
                frame = cv2.flip(frame, 1)
                h_cam, w_cam, _ = frame.shape  # 摄像头实际捕获的尺寸
                
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                image.flags.writeable = False
                results = pose.process(image)
                image.flags.writeable = True
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # --- 核心缩放步骤 ---
                image_left_pane = cv2.resize(image, (W_PANE, H_PANE), interpolation=cv2.INTER_LINEAR)
                mannequin_canvas = np.zeros((H_PANE, W_PANE, 3), dtype=np.uint8)
                mannequin_canvas[:] = (30, 30, 30) # 深色背景
                full_canvas = np.zeros((H_FINAL, W_FINAL, 3), dtype=np.uint8)
                full_canvas[:, :W_PANE] = image_left_pane
                full_canvas[:, W_PANE:W_FINAL] = mannequin_canvas
                # --- 核心缩放步骤结束 ---


                vert_l, vert_r = 0, 0 
                if results.pose_landmarks:
                    landmarks = results.pose_landmarks.landmark
                    
                    def get_coords(idx): return [landmarks[idx].x, landmarks[idx].y]
                    mp_pose_lm = mp.solutions.pose.PoseLandmark
                    
                    l_shldr, r_shldr = get_coords(mp_pose_lm.LEFT_SHOULDER.value), get_coords(mp_pose_lm.RIGHT_SHOULDER.value)
                    l_elbow, r_elbow = get_coords(mp_pose_lm.LEFT_ELBOW.value), get_coords(mp_pose_lm.RIGHT_ELBOW.value)
                    l_wrist, r_wrist = get_coords(mp_pose_lm.LEFT_WRIST.value), get_coords(mp_pose_lm.RIGHT_WRIST.value)
                    
                    l_elbow_px = tuple(np.multiply(l_elbow, [w_cam, h_cam]).astype(int))
                    r_elbow_px = tuple(np.multiply(r_elbow, [w_cam, h_cam]).astype(int))
                    
                    scale_w = W_PANE / w_cam; scale_h = H_PANE / h_cam
                    l_elbow_px_scaled = tuple(np.multiply(l_elbow_px, [scale_w, scale_h]).astype(int))
                    r_elbow_px_scaled = tuple(np.multiply(r_elbow_px, [scale_w, scale_h]).astype(int))


                    # --- 业务逻辑 ---
                    hands_above_shoulder = (l_wrist[1] < l_shldr[1]) or (r_wrist[1] < r_shldr[1])
                    self.is_active_exercise = hands_above_shoulder

                    if self.is_active_exercise:
                        ang_l = self.calculate_angle(l_shldr, l_elbow, l_wrist, '3point'); ang_r = self.calculate_angle(r_shldr, r_elbow, r_wrist, '3point')
                        avg_arm_angle = (ang_l + ang_r) / 2
                        
                        # --- 关键修正点：修正 vert_r 的计算，确保使用 r_elbow ---
                        vert_l = self.calculate_angle(l_wrist, l_elbow, mode='vertical')
                        vert_r = self.calculate_angle(r_wrist, r_elbow, mode='vertical') # FIXED!
                        
                        is_vert_bad = (vert_l > self.VERTICAL_THRESHOLD) or (vert_r > self.VERTICAL_THRESHOLD)
                        if is_vert_bad: self.current_rep_bad_forearm = True
                        shrug_ratio = self.detect_shrug(landmarks); is_shrug_bad = shrug_ratio < self.SHRUG_THRESHOLD
                        if is_shrug_bad: self.current_rep_bad_shrug = True

                        if avg_arm_angle > self.ELBOW_ANGLE_UP: self.stage = "up"
                        
                        if avg_arm_angle < self.ELBOW_ANGLE_DOWN and self.stage == 'up':
                            self.stage = "down"; self.counter += 1
                            if self.current_rep_bad_forearm: self.streak_bad_forearm += 1; self.streak_good_forearm = 0
                            else: self.streak_good_forearm += 1; self.streak_bad_forearm = 0
                            if self.streak_bad_forearm >= 2: self.err_forearm_active = True
                            if self.streak_good_forearm >= 1 and self.err_forearm_active: self.err_forearm_active = False; self.show_encouragement_flag = True
                            
                            if self.current_rep_bad_shrug: self.streak_bad_shrug += 1; self.streak_good_shrug = 0
                            else: self.streak_good_shrug += 1; self.streak_bad_shrug = 0
                            if self.streak_bad_shrug >= 2: self.err_shrug_active = True
                            if self.streak_good_shrug >= 1 and self.err_shrug_active: self.err_shrug_active = False; self.show_encouragement_flag = True
                            
                            self.current_rep_bad_forearm = False; self.current_rep_bad_shrug = False
                        
                        # 绘制左侧实时辅助线 (使用修正后的逻辑和低饱和度颜色)
                        if self.err_forearm_active:
                            color_l = COLOR_GUIDE_GOOD if vert_l <= self.VERTICAL_THRESHOLD else COLOR_GUIDE_BAD
                            color_r = COLOR_GUIDE_GOOD if vert_r <= self.VERTICAL_THRESHOLD else COLOR_GUIDE_BAD
                            
                            line_len = int(H_PANE/3)
                            end_l = (l_elbow_px_scaled[0], l_elbow_px_scaled[1] - line_len)
                            end_r = (r_elbow_px_scaled[0], r_elbow_px_scaled[1] - line_len)
                            
                            self.ui.draw_dashed_line(full_canvas[:, :W_PANE], l_elbow_px_scaled, end_l, color_l, thickness=4)
                            self.ui.draw_dashed_line(full_canvas[:, :W_PANE], r_elbow_px_scaled, end_r, color_r, thickness=4)
                    
                    # 绘制骨架和 Mannequin
                    mp_drawing.draw_landmarks(full_canvas[:, :W_PANE], results.pose_landmarks, mp_pose.POSE_CONNECTIONS, 
                                              landmark_drawing_spec=mp_drawing.DrawingSpec(color=COLOR_FUTURISTIC_WHITE, thickness=2, circle_radius=4),
                                              connection_drawing_spec=mp_drawing.DrawingSpec(color=COLOR_FUTURISTIC_WHITE, thickness=2))
                    
                    mannequin_canvas = full_canvas[:, W_PANE:W_FINAL]
                    correction_active = self.err_forearm_active
                    self.ui.draw_mannequin(mannequin_canvas, landmarks, correction_active, vert_l, vert_r, self.VERTICAL_THRESHOLD)


                # === 最终 UI 渲染层 ===
                
                cv2.rectangle(full_canvas, (0, 0), (W_FINAL, 100), (30, 30, 30), -1)
                cv2.rectangle(full_canvas, (0, H_FINAL-80), (W_FINAL, H_FINAL), (30, 30, 30), -1)

                cv2.putText(full_canvas, f"REPS: {self.counter}", (20, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, COLOR_FUTURISTIC_WHITE, 2)
                cv2.putText(full_canvas, "AI Sports Vision Pro Max", (W_PANE + 50, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, COLOR_FUTURISTIC_WHITE, 2)

                msg_text = ""; msg_color = COLOR_FUTURISTIC_WHITE 
                
                if not self.is_active_exercise:
                    msg_text = "请做推举动作"; msg_color = COLOR_ERROR_MUTED 
                elif self.err_forearm_active:
                    msg_text = "⚠️ 纠错：小臂全程垂直于地面效果更好！"; msg_color = COLOR_ERROR_MUTED
                elif self.err_shrug_active:
                    msg_text = "⚠️ 纠错：动作中耸肩影响训练效果！"; msg_color = COLOR_ERROR_MUTED
                elif self.show_encouragement_flag:
                    msg_text = "✨ 真棒！动作正确了！"; msg_color = COLOR_ENCOURAGE_MUTED
                    if self.streak_good_forearm >= 2 and self.streak_good_shrug >= 2:
                        self.show_encouragement_flag = False 
                
                if msg_text:
                    full_canvas = self.ui.draw_chinese_text(full_canvas, msg_text, (50, H_FINAL-60), msg_color, 'large')


                cv2.imshow('AI Shoulder Press Pro Max', full_canvas)
                
                if cv2.waitKey(10) & 0xFF == ord('q'):
                    break

        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    app = ShoulderPressPro()
    app.process()