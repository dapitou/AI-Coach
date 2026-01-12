from dataclasses import dataclass

# 错误名称映射 (通用)
ERR_NAMES_MAP = {
    'shrug': '耸肩',
    'arm': '小臂',
    'valgus': '膝扣',
    'rounding': '弓背',
    'depth': '深度',
    'range': '行程',
    'lunge_knee': '前膝'
}

@dataclass(frozen=True)
class AlgoConfig:
    STD_HEIGHT: float = 180.0
    
    # [脊柱拟合]
    GLOBAL_DIR_FLIP: float = -1.0 
    LATERAL_GAIN: float = 0.5 
    ROUNDING_AMP: float = 6.5  
    LOC_THORAX: float = 0.33
    LOC_LUMBAR: float = 0.66
    HINGE_TOLERANCE_GAIN: float = 0.50 
    CAMERA_PITCH_TOLERANCE: float = 0.08
    CALIBRATION_RATE: float = 0.05
    VIEW_SIDE_RATIO: float = 0.28  
    VIEW_FRONT_RATIO: float = 0.45 
    
    # [朝向]
    W_NOSE: float = 2.5      
    W_TOE: float = 2.0       
    W_KNEE: float = 1.5      
    W_WRIST: float = 0.5     
    FACING_SMOOTH_ALPHA: float = 0.05

    # [通用阈值]
    PRESS_VERT_TOLERANCE: int = 25
    SHRUG_RATIO_TH: float = 0.35
    SHRUG_SMOOTH_FACTOR: float = 0.6
    
    # [深蹲]
    SQUAT_GATE_STANCE_RATIO: float = 0.5
    SQUAT_GATE_FEET_Y_TOL: float = 0.10
    SQUAT_GATE_ALIGN_TOL: float = 0.15
    SQUAT_GATE_GRAVITY_TOL: float = 0.2
    
    SQUAT_DOWN_TH: int = 80 
    SQUAT_UP_TH: int = 120 
    SQUAT_VALGUS_START_RATIO: float = 0.33
    
    VALGUS_RATIO: float = 1.0
    ROUNDING_COMPRESS_TH: float = 0.01 
    HINGE_ANGLE_MIN: float = 15.0
    
    # [前平举]
    RAISE_GATE_WIDTH_RATIO: float = 2.0
    RAISE_GATE_CENTER_TOL: float = 0.5
    RAISE_HEIGHT_RATIO: float = 0.5
    
    # [弓步蹲]
    LUNGE_STANCE_RATIO: float = 0.5 
    LUNGE_DOWN_TH: int = 80
    LUNGE_UP_TH: int = 150   
    LUNGE_KNEE_TOLERANCE: int = 35 
    LUNGE_VALGUS_CHECK_OFFSET: int = 80
    
    # [计次防抖]
    COUNT_COOLDOWN: float = 0.2
    
    # [门控]
    GATEKEEPER_TIMEOUT: float = 0.5

@dataclass(frozen=True)
class TextConfig:
    WINDOW_NAME: str = "AEKE Fitness Mirror V3.0.3 (Config Fixed)"
    
    # [核心修复] 补全动作名称常量
    ACT_PRESS: str = "推举"
    ACT_SQUAT: str = "深蹲"
    ACT_RAISE: str = "前平举"
    ACT_LUNGE: str = "弓步蹲"
    
    LABEL_COUNT: str = "COUNT"
    LABEL_FPS: str = "FPS"
    LABEL_ACC: str = "正确率"
    LABEL_HEIGHT: str = "身高" 
    UNIT_CM: str = "cm"

    BTN_CAM: str = "摄像头"
    BTN_VIDEO: str = "导入视频"
    
    MSG_GOOD: str = "完美动作！"
    
    TIP_PRESS_DO: str = "请做“推举”动作"
    ERR_PRESS_ARM: str = "小臂全程垂直于地面效果更好！"
    ERR_PRESS_SHRUG: str = "动作中耸肩影响训练效果！"
    
    TIP_SQUAT_DO: str = "请做“深蹲”动作"
    ERR_SQUAT_DEPTH: str = "蹲至大腿平行地面效果更好！"
    ERR_SQUAT_VALGUS: str = "注意膝关节不要内扣！"
    ERR_SQUAT_ROUNDING: str = "背部挺直，不要弓腰！" 
    
    TIP_RAISE_DO: str = "请做“前平举”动作"
    ERR_RAISE_RANGE: str = "肘部抬至与肩等高效果更好"
    
    TIP_LUNGE_DO: str = "请做“弓步蹲”动作"
    ERR_LUNGE_KNEE: str = "前膝向外展开，避免内扣！"
    ERR_LUNGE_DEPTH: str = "前腿蹲至大腿平行地面！"

@dataclass(frozen=True)
class ColorConfig:
    BG: tuple = (15, 15, 20)
    GRID: tuple = (40, 40, 50)
    NEON_BLUE: tuple = (255, 200, 0)
    NEON_GREEN: tuple = (50, 255, 50)
    NEON_RED: tuple = (50, 50, 255)
    NEON_YELLOW: tuple = (0, 215, 255)
    NEON_ORANGE: tuple = (0, 140, 255)
    NEON_PURPLE: tuple = (255, 0, 255)
    FPS: tuple = (0, 255, 128)
    TEXT_MAIN: tuple = (250, 250, 250)
    TEXT_DIM: tuple = (160, 160, 160)
    UI_BORDER_NORMAL: tuple = (60, 60, 60)
    UI_BORDER_ACTIVE: tuple = (0, 215, 255)

@dataclass
class AppConfig:
    W: int = 1280
    H: int = 720
    HALF_W: int = 640
    FONT: str = "msyh.ttc"
    VOL: float = 0.5
    MENU_ANIM_STEP: float = 0.15