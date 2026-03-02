// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\data\constants.js

window.CONSTANTS = {
    PARTS: ['Full Body', 'Chest', 'Back', 'Shoulder', 'Arm', 'Glute', 'Leg', 'Core'],
    WEEKDAYS: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'],
    
    // 映射数据 (Mappings)
    MAPPINGS: {
        // [SYNC] 全量器械库 (用于计算可用器械)
        EQUIPMENT_LIST: ['Bodyweight', 'Barbell', 'Dumbbell', 'Bench', 'Foam Roller', 'Ankle Strap', 'Yoga Mat', 'Yoga Block', 'Rope'],
        // [NEW] 部位关联映射 (用于热身/放松的精准过滤)
        RELATED_PARTS: {
            'Chest': ['Shoulder', 'Arm'],
            'Back': ['Shoulder', 'Arm'],
            'Shoulder': ['Chest', 'Back', 'Arm'],
            'Arm': ['Shoulder', 'Chest', 'Back'],
            'Leg': ['Glute'],
            'Glute': ['Leg'],
            'Core': ['Glute'],
            'Full Body': ['Chest', 'Back', 'Shoulder', 'Arm', 'Glute', 'Leg', 'Core']
        },
        // 解剖学层级
        ANATOMY: {
            'Upper Body': ['Chest', 'Back', 'Shoulder', 'Arm'],
            'Lower Body': ['Glute', 'Leg'],
            'Core': ['Core'],
            'Full Body': ['Full Body']
        },
        // 动作模式 -> 主练部位
        MODE_TO_PART: {
            'Push_H': 'Chest', 'Push_V': 'Shoulder',
            'Pull_H': 'Back', 'Pull_V': 'Back',
            'Squat': 'Leg', 'Hinge': 'Glute',
            'Lunge': 'Leg', 'Rotation': 'Core',
            'Core_Stability': 'Core', 'Gait': 'Full Body'
        },
        // 强度换算
        INTENSITY: {
            'L1': { load: 0.6, reps: 10, rest: 45 },
            'L2': { load: 0.7, reps: 12, rest: 60 },
            'L3': { load: 0.75, reps: 12, rest: 90 },
            'L4': { load: 0.85, reps: 8, rest: 120 },
            'L5': { load: 0.90, reps: 5, rest: 180 }
        }
    },

    LEVEL_MAP: { 'L1':1, 'L2':2, 'L3':3, 'L4':4, 'L5':5 },
    
    COURSE_TYPES: {
        'Strength': 'Resistance', 'Rehab': 'Resistance', 'Golf': 'Resistance',
        'HIIT': 'Interval', 'Cardio': 'Interval', 'Combat': 'Interval',
        'Yoga': 'Flow', 'Pilates': 'Flow', 'Stretch': 'Flow', 'Meditation': 'Flow', 'Qigong': 'Flow'
    }, 
    
    ENUMS: {
        ONE_RM: { 'Chest': 60, 'Back': 70, 'Leg': 100, 'Glute': 90, 'Shoulder': 30, 'Arm': 25, 'Core': 40, 'Full Body': 50 },
        GENDER: ['Male', 'Female'],
        LEVEL: ['L1', 'L2', 'L3', 'L4', 'L5'],
        GOAL: ['Muscle Gain', 'Weight Loss', 'Health'],
        FUNC_GOAL: ['Muscle Gain', 'Strength', 'Endurance', 'Power', 'Fat Loss', 'Cardio', 'Recovery', 'Flexibility', 'Coordination', 'Posture', 'Specific', 'Activation', 'Balance'],
        STYLE: ['Traditional', 'Varied', 'Aggressive'],
        BODY_TYPE: ['Balanced', 'Muscular', 'Lean', 'Bodybuilder'],
        LOOP_MODE: ['Regular', 'Circuit'],
        LOAD_STRATEGY: ['Recommended', 'Constant', 'Progressive', 'Regressive', 'Custom'],
        COURSE_TYPES: ['Strength', 'Cardio', 'HIIT', 'Combat', 'Pilates', 'Yoga', 'Stretch', 'Qigong', 'Rehab', 'Meditation', 'Golf'],
        PAIN_AREAS: ['None', 'Wrist', 'Elbow', 'Shoulder', 'Lower Back', 'Hip', 'Knee', 'Ankle'],
        MISSING_ACCESSORIES: ['Bench', 'Yoga Block', 'Foam Roller', 'Barbell', 'Dumbbell']
    },

    CN_TO_EN: {
        '男': 'Male', '女': 'Female',
        '增肌': 'Muscle Gain', '减重': 'Weight Loss', '健康': 'Health',
        '力量': 'Strength', '耐力': 'Endurance', '爆发': 'Power', '减脂': 'Fat Loss', '心肺': 'Cardio', '恢复': 'Recovery', '柔韧': 'Flexibility', '协调': 'Coordination', '体态': 'Posture', '专项': 'Specific', '激活': 'Activation', '平衡': 'Balance',
        '传统型': 'Traditional', '多变型': 'Varied', '激进型': 'Aggressive',
        '均衡标准型': 'Balanced', '标准肌肉型': 'Muscular', '紧致精瘦型': 'Lean', '健美肌肉型': 'Bodybuilder',
        '常规': 'Regular', '循环': 'Circuit', '常规组': 'Regular', '循环组': 'Circuit',
        '推荐': 'Recommended', '恒定': 'Constant', '递增': 'Progressive', '递减': 'Regressive', '自定义': 'Custom',
        '有氧': 'Cardio', 'HIIT': 'HIIT', '搏击': 'Combat', '普拉提': 'Pilates', '瑜伽': 'Yoga', '拉伸': 'Stretch', '气功': 'Qigong', '康复': 'Rehab', '冥想': 'Meditation', '高尔夫': 'Golf',
        '无': 'None', '手腕': 'Wrist', '肘部': 'Elbow', '肩部': 'Shoulder', '腰部': 'Lower Back', '髋部': 'Hip', '膝盖': 'Knee', '脚踝': 'Ankle',
        '健身凳': 'Bench', '瑜伽砖': 'Yoga Block', '泡沫轴': 'Foam Roller', '横杆': 'Barbell', '手柄': 'Dumbbell', '自重': 'Bodyweight', '踝带': 'Ankle Strap', '瑜伽垫': 'Yoga Mat', '双头绳': 'Rope',
        '全身': 'Full Body', '胸部': 'Chest', '背部': 'Back', '手臂': 'Arm', '臀部': 'Glute', '腿部': 'Leg', '核心': 'Core',
        '周一': 'Mon', '周二': 'Tue', '周三': 'Wed', '周四': 'Thu', '周五': 'Fri', '周六': 'Sat', '周日': 'Sun',
        '热身': 'Warmup', '主训': 'Main', '放松': 'Cooldown',
        '抗阻范式': 'Resistance', '间歇范式': 'Interval', '流式范式': 'Flow',
        '水平推': 'Push_H', '垂直推': 'Push_V', '水平拉': 'Pull_H', '垂直拉': 'Pull_V', '髋主导': 'Hinge', '膝主导': 'Squat', '弓步': 'Lunge', '旋转': 'Rotation', '核心稳定': 'Core_Stability', '步态': 'Gait',
        '复合动作': 'Compound', '孤立动作': 'Isolation',
        '无冲击': 'No Impact', '低冲击': 'Low Impact', '高冲击': 'High Impact',
        '初级': 'Beginner', '中级': 'Intermediate', '高级': 'Advanced',
        '已恢复': 'Recovered', '恢复中': 'Recovering', '疲劳中': 'Fatigued', '已力竭': 'Exhausted',
        '适应期': 'Adaptation', '进阶期': 'Progression', '突破期': 'Peak', '减载期': 'Deload',
        '动作构造': 'Construct', '动作模式': 'Mode', '主动肌': 'Muscle', '主要配件': 'Equip', '动作体位': 'Posture', '动作难度': 'Difficulty', 'MET值': 'MET', '推荐权重': 'Score', '动作功能': 'Func', '单双侧': 'Unilateral', '冲击等级': 'Impact', '随机': 'Random', '部位': 'Part',
        '上肢': 'Upper Body', '下肢': 'Lower Body',

        // Muscles
        '胸大肌中束': 'Pectoralis Major Middle',
        '胸大肌上束': 'Pectoralis Major Upper',
        '胸大肌下束': 'Pectoralis Major Lower',
        '胸大肌内侧': 'Pectoralis Major Inner',
        '胸大肌外侧': 'Pectoralis Major Outer',
        '背阔肌': 'Latissimus Dorsi',
        '中背': 'Middle Back',
        '上背': 'Upper Back',
        '下背': 'Lower Back Muscle',
        '斜方肌': 'Trapezius',
        '竖脊肌': 'Erector Spinae',
        '三角肌前束': 'Deltoid Anterior',
        '三角肌中束': 'Deltoid Middle',
        '三角肌后束': 'Deltoid Posterior',
        '肩袖': 'Rotator Cuff',
        '肱二头肌': 'Biceps Brachii',
        '肱三头肌': 'Triceps Brachii',
        '前臂肌群': 'Forearm Muscles',
        '腹直肌': 'Rectus Abdominis',
        '腹斜肌': 'Obliques',
        '核心肌群': 'Core Muscles',
        '前锯肌': 'Serratus Anterior',
        '臀大肌': 'Gluteus Maximus',
        '臀中肌': 'Gluteus Medius',
        '股四头肌': 'Quadriceps',
        '腘绳肌': 'Hamstrings',
        '内收肌': 'Adductors',
        '腓肠肌': 'Gastrocnemius',
        '比目鱼肌': 'Soleus',
        '胫骨前肌': 'Tibialis Anterior',
        '小腿肌群': 'Calf Muscles',
        '髂腰肌': 'Iliopsoas',
        '全身肌群': 'Whole Body Muscles'
    }
};
