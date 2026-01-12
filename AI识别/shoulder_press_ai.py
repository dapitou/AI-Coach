import cv2
import mediapipe as mp
import numpy as np
import math

class ShoulderPressAnalyzer:
    def __init__(self):
        # 状态变量
        self.counter = 0
        self.stage = None  # 'down' or 'up'
        
        # 纠错逻辑变量
        self.correction_mode = False # 是否处于纠错模式
        self.bad_rep_streak = 0      # 连续错误次数
        self.good_rep_streak = 0     # 连续正确次数
        self.current_rep_is_bad = False # 当前这一次动作是否已经出现严重错误
        
        # 阈值设置
        self.VERTICAL_THRESHOLD = 15 # 小臂偏离垂直线超过15度算错误
        self.ELBOW_ANGLE_UP = 150    # 推起到顶的角度
        self.ELBOW_ANGLE_DOWN = 70   # 下放到位的角度

    def calculate_angle_vertical(self, a, b):
        """
        计算线段 ab 与 垂直线(Y轴) 的夹角
        a: 肘部 (x, y)
        b: 手腕 (x, y)
        """
        # 向量 V_arm = (x_wrist - x_elbow, y_wrist - y_elbow)
        # 向量 V_vertical = (0, -1) (图像坐标系y向下，所以向上是-1)
        # 但这里我们只关心与垂直线的偏差，不关心是指向天还是地，取绝对值计算即可
        
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        
        # 使用 atan2 计算角度，结果是弧度
        # 我们想算它偏离Y轴多少度。
        # 如果完全垂直，dx=0，角度应为0。
        # 这是一个简单的三角函数：tan(theta) = dx / dy
        if dy == 0: return 90.0
        
        angle_rad = math.atan(abs(dx) / abs(dy))
        angle_deg = math.degrees(angle_rad)
        
        return angle_deg

    def calculate_elbow_angle(self, a, b, c):
        """计算肘关节角度 (肩-肘-腕)"""
        a = np.array(a) # 肩
        b = np.array(b) # 肘
        c = np.array(c) # 腕
        
        radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
        angle = np.abs(radians*180.0/np.pi)
        if angle > 180.0: angle = 360 - angle
        return angle

    def draw_dashed_line(self, img, pt1, pt2, color, thickness=2, gap=20):
        """绘制虚线辅助线"""
        dist = ((pt1[0]-pt2[0])**2 + (pt1[1]-pt2[1])**2)**0.5
        pts = []
        for i in range(int(dist/gap)):
            r = i*gap/dist
            x = int(pt1[0]*(1-r) + pt2[0]*r)
            y = int(pt1[1]*(1-r) + pt2[1]*r)
            pts.append((x,y))
        
        for i, p in enumerate(pts):
            if i % 2 == 0:
                cv2.circle(img, p, thickness, color, -1)

def run_demo():
    # 初始化 MediaPipe
    mp_drawing = mp.solutions.drawing_utils
    mp_pose = mp.solutions.pose
    
    cap = cv2.VideoCapture(0)
    # 设置分辨率以保证文字清晰
    cap.set(3, 1280)
    cap.set(4, 720)
    
    analyzer = ShoulderPressAnalyzer()
    
    with mp_pose.Pose(min_detection_confidence=0.6, min_tracking_confidence=0.6) as pose:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            
            # 镜像处理，让体验更像照镜子
            frame = cv2.flip(frame, 1)
            h, w, _ = frame.shape
            
            # RGB转换
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            # === 核心逻辑层 ===
            try:
                landmarks = results.pose_landmarks.landmark
                
                # 获取关键点 (左侧 11,13,15; 右侧 12,14,16)
                l_shoulder = [landmarks[11].x, landmarks[11].y]
                l_elbow = [landmarks[13].x, landmarks[13].y]
                l_wrist = [landmarks[15].x, landmarks[15].y]
                
                r_shoulder = [landmarks[12].x, landmarks[12].y]
                r_elbow = [landmarks[14].x, landmarks[14].y]
                r_wrist = [landmarks[16].x, landmarks[16].y]
                
                # 1. 坐标像素化 (用于绘图)
                l_elbow_px = tuple(np.multiply(l_elbow, [w, h]).astype(int))
                r_elbow_px = tuple(np.multiply(r_elbow, [w, h]).astype(int))
                
                # 2. 计算关键指标
                # A. 动作行程角度 (判断起落)
                angle_l = analyzer.calculate_elbow_angle(l_shoulder, l_elbow, l_wrist)
                angle_r = analyzer.calculate_elbow_angle(r_shoulder, r_elbow, r_wrist)
                avg_arm_angle = (angle_l + angle_r) / 2
                
                # B. 垂直度 (判断错误)
                vert_offset_l = analyzer.calculate_angle_vertical(l_elbow, l_wrist)
                vert_offset_r = analyzer.calculate_angle_vertical(r_elbow, r_wrist)
                
                # 判断当前时刻是否严重违规
                is_frame_bad = (vert_offset_l > analyzer.VERTICAL_THRESHOLD) or \
                               (vert_offset_r > analyzer.VERTICAL_THRESHOLD)
                
                if is_frame_bad:
                    analyzer.current_rep_is_bad = True

                # 3. 状态机与计数逻辑
                if avg_arm_angle > analyzer.ELBOW_ANGLE_UP:
                    analyzer.stage = "up"
                    
                if avg_arm_angle < analyzer.ELBOW_ANGLE_DOWN and analyzer.stage == 'up':
                    analyzer.stage = "down"
                    analyzer.counter += 1
                    
                    # === 动作结束时的结算逻辑 ===
                    if analyzer.current_rep_is_bad:
                        analyzer.bad_rep_streak += 1
                        analyzer.good_rep_streak = 0 # 重置好动作连击
                        print(f"Rep {analyzer.counter}: Bad form! Streak: {analyzer.bad_rep_streak}")
                    else:
                        analyzer.good_rep_streak += 1
                        analyzer.bad_rep_streak = 0 # 重置坏动作连击
                        print(f"Rep {analyzer.counter}: Good form! Streak: {analyzer.good_rep_streak}")

                    # 触发/解除纠错模式的判定
                    if analyzer.bad_rep_streak >= 2:
                        analyzer.correction_mode = True
                    
                    if analyzer.correction_mode and analyzer.good_rep_streak >= 1:
                        analyzer.correction_mode = False
                    
                    # 重置当前Rep的状态，准备下一次
                    analyzer.current_rep_is_bad = False

                # === 4. 可视化渲染层 ===
                
                # A. 绘制骨架 (基础)
                mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # B. 纠错模式专用UI (根据PRD需求)
                if analyzer.correction_mode:
                    # 确定辅助线颜色：实时反馈 (只要这一帧垂直了，线就变绿，给用户即时反馈)
                    line_color_l = (0, 255, 0) if vert_offset_l <= analyzer.VERTICAL_THRESHOLD else (0, 0, 255)
                    line_color_r = (0, 255, 0) if vert_offset_r <= analyzer.VERTICAL_THRESHOLD else (0, 0, 255)
                    
                    # 绘制从肘部向上生长的垂直虚线
                    # 长度设为肘腕距离的1.5倍，更明显
                    arm_len_l = np.linalg.norm(np.array(l_wrist) - np.array(l_elbow)) * h * 1.5
                    arm_len_r = np.linalg.norm(np.array(r_wrist) - np.array(r_elbow)) * h * 1.5
                    
                    end_pt_l = (l_elbow_px[0], int(l_elbow_px[1] - arm_len_l))
                    end_pt_r = (r_elbow_px[0], int(r_elbow_px[1] - arm_len_r))
                    
                    analyzer.draw_dashed_line(image, l_elbow_px, end_pt_l, line_color_l, thickness=3)
                    analyzer.draw_dashed_line(image, r_elbow_px, end_pt_r, line_color_r, thickness=3)
                    
                    # 提示文本
                    msg = "Please keep forearms VERTICAL!"
                    color = (0, 0, 255) # Red
                    cv2.rectangle(image, (0, h-100), (w, h), (0,0,0), -1) # 底部黑条背景
                    cv2.putText(image, msg, (50, h-40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)
                
                # C. 鼓励模式 (刚解除纠错时)
                # 这里做一个简单的显示逻辑：如果不在纠错模式，且好动作连击 > 0，显示鼓励
                elif analyzer.good_rep_streak > 0:
                    msg = "Great Job! Perfect Form!"
                    color = (0, 255, 0) # Green
                    cv2.rectangle(image, (0, h-100), (w, h), (200,200,200), -1) 
                    cv2.putText(image, msg, (50, h-40), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2, cv2.LINE_AA)

                # D. 左上角仪表盘
                cv2.rectangle(image, (0,0), (250, 100), (245, 117, 16), -1)
                cv2.putText(image, 'REPS', (15,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 1, cv2.LINE_AA)
                cv2.putText(image, str(analyzer.counter), (15,80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 2, cv2.LINE_AA)
                
                cv2.putText(image, 'MODE', (120,30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,0), 1, cv2.LINE_AA)
                status_text = "FIX" if analyzer.correction_mode else "NORM"
                cv2.putText(image, status_text, (115,80), cv2.FONT_HERSHEY_SIMPLEX, 1.5, (255,255,255), 2, cv2.LINE_AA)

            except Exception as e:
                # print(e) # 调试用
                pass
            
            cv2.imshow('AI Shoulder Press Coach', image)
            if cv2.waitKey(10) & 0xFF == ord('q'):
                break
                
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_demo()