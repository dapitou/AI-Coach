from dataclasses import dataclass

ERR_NAMES_MAP = {
    'shrug': '耸肩', 'arm': '小臂', 'valgus': '膝扣', 'rounding': '弓背',
    'depth': '深度', 'range': '行程', 'lunge_valgus': '前膝', 
    'lunge_depth': '幅度', 'lunge_knee': '前膝'
}

@dataclass
class AlgoConfig:
    STD_HEIGHT: float = 180.0
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

    PRESS_VERT_TOLERANCE: int = 25
    SHRUG_RATIO_TH: float = 0.35
    SHRUG_SMOOTH_FACTOR: float = 0.6
    
    SQUAT_CHECK_START_BASE: int = 300
    SQUAT_DOWN_TH_PIXEL: int = 80
    SQUAT_UP_TH_PIXEL: int = 120
    VALGUS_RATIO: float = 1.2 
    
    LUNGE_DROP_DOWN_RATIO: float = 0.12 
    LUNGE_DROP_UP_RATIO: float = 0.08   
    LUNGE_VALGUS_RATIO: float = 1.1 
    LUNGE_VALGUS_START_RATIO: float = 0.33 
    LUNGE_VALGUS_CHECK_OFFSET: int = 60 
    LUNGE_DEPTH_TOLERANCE_PIXEL: int = 100 
    
    ROUNDING_COMPRESS_TH: float = 0.01 
    HINGE_ANGLE_MIN: float = 15.0
    
    RAISE_HEIGHT_RATIO: float = 0.5
    RAISE_GATE_WIDTH_RATIO: float = 2.0
    RAISE_GATE_CENTER_TOL: float = 0.5
    
    LUNGE_STANCE_X_RATIO: float = 0.5 
    LUNGE_KNEE_TOLERANCE_PIXEL: int = 35
    
    COUNT_COOLDOWN: float = 0.2
    GATEKEEPER_TIMEOUT: float = 2.0 
    SQUAT_GATE_STANCE_RATIO: float = 0.5
    SQUAT_GATE_FEET_Y_TOL: float = 0.10

@dataclass(frozen=True)
class TextConfig:
    WINDOW_NAME: str = "AEKE Fitness Mirror V6.4.0 (Tooltips)"
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
    BTN_TUNE: str = "动作调参"
    
    BTN_CONFIRM: str = "确认"
    BTN_CANCEL: str = "取消"
    LBL_TUNING: str = "参数调节"

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
    MODAL_BG: tuple = (0, 0, 0) 

@dataclass
class AppConfig:
    W: int = 1280
    H: int = 720
    HALF_W: int = 640
    FONT: str = "msyh.ttc"
    VOL: float = 0.5
    MENU_ANIM_STEP: float = 0.15 

# Key: Action Name, Value: List of (Attr Name, Display Label)
TUNING_MAP = {
    TextConfig.ACT_PRESS: [
        ('PRESS_VERT_TOLERANCE', '垂直容忍度(度)'),
        ('SHRUG_RATIO_TH', '耸肩判定比例')
    ],
    TextConfig.ACT_SQUAT: [
        ('SQUAT_DOWN_TH_PIXEL', '下蹲触发像素'),
        ('VALGUS_RATIO', '内扣系数'),
        ('SQUAT_CHECK_START_BASE', '检查起始偏移')
    ],
    TextConfig.ACT_LUNGE: [
        ('LUNGE_DROP_DOWN_RATIO', '下蹲触发比例'),
        ('LUNGE_VALGUS_RATIO', '内扣系数'),
        ('LUNGE_DEPTH_TOLERANCE_PIXEL', '深度容忍(px)')
    ],
    TextConfig.ACT_RAISE: [
        ('RAISE_HEIGHT_RATIO', '高度比例'),
        ('SHRUG_RATIO_TH', '耸肩判定比例')
    ]
}

# [New] Parameter Tooltips
# Key: Param Attr Name, Value: (Definition, Range, Effect)
PARAM_TIPS = {
    'PRESS_VERT_TOLERANCE': "判定小臂是否垂直的容忍角度。\n建议范围: 15-35\n数值越小要求越严，数值越大越容易达标。",
    'SHRUG_RATIO_TH': "当前肩耳距离与基准距离的比值阈值。\n建议范围: 0.2-0.5\n低于此值判定为耸肩。数值越大越容易触发耸肩警告。",
    'SQUAT_DOWN_TH_PIXEL': "髋部下降多少像素视为开始下蹲。\n建议范围: 50-100\n防止微小晃动误判为下蹲。",
    'VALGUS_RATIO': "膝盖间距与髋部间距的最小比例。\n建议范围: 1.0-1.4\n小于此比例(如1.2)判定为内扣。数值越大要求膝盖打得越开。",
    'SQUAT_CHECK_START_BASE': "下蹲多少像素后开始检测内扣。\n建议范围: 100-400\n避免在刚开始下蹲时误报。",
    'LUNGE_DROP_DOWN_RATIO': "身体下沉幅度占躯干长度的比例。\n建议范围: 0.10-0.20\n决定动作开始计次的灵敏度。",
    'LUNGE_VALGUS_RATIO': "弓步前腿内扣的判定系数。\n建议范围: 1.0-1.3\n数值越大，对膝盖外展要求越高。",
    'LUNGE_DEPTH_TOLERANCE_PIXEL': "臀部距离膝盖高度的像素容差。\n建议范围: 50-150\n数值越大，对下蹲深度的要求越宽松。",
    'RAISE_HEIGHT_RATIO': "手腕抬起高度判定。\n建议范围: 0.4-0.6\n决定动作达标的高度线。"
}