from dataclasses import dataclass

ERR_NAMES_MAP = {
    'shrug': '耸肩', 'arm': '小臂', 'valgus': '膝扣', 'rounding': '弓背',
    'depth': '深度', 'range': '行程', 'lunge_valgus': '前膝', 
    'lunge_depth': '幅度', 'lunge_knee': '前膝'
}

@dataclass
class AlgoConfig:
    STD_HEIGHT: float = 180.0
    GLOBAL_DIR_FLIP: float = -1.0 # -1: 人朝左, 1: 人朝右 (决定弓背的后方)
    
    # [参数调节] 侧面弓背幅度系数
    # 原值: 6.5 -> 调整为: 8.0 (增强弓背的视觉拱起程度)
    ROUNDING_AMP: float = 8.0  
    
    LATERAL_GAIN: float = 0.5 
    LOC_THORAX: float = 0.33
    LOC_LUMBAR: float = 0.66
    HINGE_TOLERANCE_GAIN: float = 0.50 
    CAMERA_PITCH_TOLERANCE: float = 0.08
    CALIBRATION_RATE: float = 0.05
    VIEW_SIDE_RATIO: float = 0.28  
    VIEW_FRONT_RATIO: float = 0.45 

    # Toggles
    ENABLE_PRESS_ARM: bool = True
    ENABLE_SHRUG: bool = True
    ENABLE_SQUAT_VALGUS: bool = True
    ENABLE_SQUAT_ROUNDING: bool = True
    ENABLE_LUNGE_VALGUS: bool = True

    # Priorities
    PRIORITY_PRESS_ARM: int = 1
    PRIORITY_SHRUG: int = 2
    PRIORITY_SQUAT_VALGUS: int = 1
    PRIORITY_SQUAT_ROUNDING: int = 2

    # Params
    PRESS_VERT_TOLERANCE: int = 20 
    SHRUG_COMPRESSION_TH: float = 0.20
    SHRUG_SMOOTH_FACTOR: float = 0.6
    
    # Spine Physics
    ROUNDING_COMPRESS_TH: float = 0.06 
    SPINE_BEND_GAIN: float = 1.5
    
    SQUAT_CHECK_START_BASE: int = 300
    SQUAT_DOWN_TH_PIXEL: int = 60
    SQUAT_UP_TH_PIXEL: int = 80
    VALGUS_RATIO: float = 1.2 
    
    LUNGE_DROP_DOWN_RATIO: float = 0.12 
    LUNGE_DROP_UP_RATIO: float = 0.08   
    LUNGE_VALGUS_RATIO: float = 1.1 
    LUNGE_DEPTH_TOLERANCE_PIXEL: int = 100 
    HINGE_ANGLE_MIN: float = 15.0
    
    RAISE_HEIGHT_RATIO: float = 0.5
    
    LUNGE_STANCE_X_RATIO: float = 0.5 
    
    COUNT_COOLDOWN: float = 0.3
    GATEKEEPER_TIMEOUT: float = 2.0 
    
    PRESS_START_Y_OFFSET: int = 0
    PRESS_UP_TH: int = 120 

@dataclass(frozen=True)
class TextConfig:
    WINDOW_NAME: str = "AEKE Fitness Mirror V10.0.0 (Pro Spring)"
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
    ERR_PRESS_SHRUG: str = "推起时保持肩部下压"
    
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

TUNING_TREE = {
    TextConfig.ACT_PRESS: [
        {
            'name': '小臂垂直检测',
            'switch': 'ENABLE_PRESS_ARM',
            'prio': 'PRIORITY_PRESS_ARM', 
            'params': [('PRESS_VERT_TOLERANCE', '容忍角度(度)')]
        },
        {
            'name': '耸肩检测',
            'switch': 'ENABLE_SHRUG',
            'prio': 'PRIORITY_SHRUG',
            'params': [('SHRUG_COMPRESSION_TH', '压缩阈值(0-1)')]
        }
    ],
    TextConfig.ACT_SQUAT: [
        {
            'name': '膝盖内扣检测',
            'switch': 'ENABLE_SQUAT_VALGUS',
            'prio': 'PRIORITY_SQUAT_VALGUS',
            'params': [('VALGUS_RATIO', '宽度系数')]
        },
        {
            'name': '弓背检测',
            'switch': 'ENABLE_SQUAT_ROUNDING',
            'prio': 'PRIORITY_SQUAT_ROUNDING',
            'params': [('ROUNDING_COMPRESS_TH', '压缩阈值')] 
        },
        {
            'name': '计次灵敏度',
            'switch': None,
            'params': [
                ('SQUAT_DOWN_TH_PIXEL', '下蹲触发(px)'),
                ('SQUAT_UP_TH_PIXEL', '起立触发(px)')
            ]
        }
    ],
    TextConfig.ACT_LUNGE: [
        {
            'name': '前膝内扣检测',
            'switch': 'ENABLE_LUNGE_VALGUS',
            'params': [('LUNGE_VALGUS_RATIO', '内扣系数')]
        },
        {
            'name': '计次参数',
            'switch': None,
            'params': [
                ('LUNGE_DROP_DOWN_RATIO', '下蹲比例'),
                ('LUNGE_DROP_UP_RATIO', '起立比例')
            ]
        }
    ],
    TextConfig.ACT_RAISE: [
        {
            'name': '耸肩检测',
            'switch': 'ENABLE_SHRUG',
            'prio': 'PRIORITY_SHRUG',
            'params': [('SHRUG_COMPRESSION_TH', '压缩阈值')]
        },
        {
            'name': '高度判定',
            'switch': None,
            'params': [('RAISE_HEIGHT_RATIO', '达标高度系数')]
        }
    ]
}

TUNING_MAP = {} 

PARAM_TIPS = {
    'ENABLE_PRESS_ARM': "开关：是否检测推举过程中的小臂垂直度。",
    'PRESS_VERT_TOLERANCE': "判定小臂是否垂直的容忍角度 (度)。\n越小越严格，建议范围: 15-30。",
    'ENABLE_SHRUG': "开关：是否检测动作过程中的耸肩代偿。",
    'SHRUG_COMPRESSION_TH': "鼻肩垂直距离的压缩比例阈值。\n0.20表示压缩超过20%即判定耸肩。",
    'ENABLE_SQUAT_ROUNDING': "开关：是否检测深蹲时的脊柱弯曲（弓背）。",
    'ROUNDING_COMPRESS_TH': "脊柱弦长压缩阈值 (0-1)。\n数值越小越灵敏，建议: 0.05-0.08。",
    'PRIORITY_PRESS_ARM': "数值越小优先级越高(1>2)。",
    'PRIORITY_SHRUG': "数值越小优先级越高(1>2)。",
    'PRIORITY_SQUAT_VALGUS': "数值越小优先级越高(1>2)。",
    'PRIORITY_SQUAT_ROUNDING': "数值越小优先级越高(1>2)。",
}