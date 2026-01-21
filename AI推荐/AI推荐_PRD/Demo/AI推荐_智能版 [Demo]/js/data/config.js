const CONFIG = {
    STRATEGY: {
        '增肌': { sets: 4, rest: 90, intensity: 0.75, mode: '常规组', strategy: '推荐', diff: '标准', rpe: 8 },
        '力量': { sets: 5, rest: 180, intensity: 0.85, mode: '常规组', strategy: '恒定', diff: '进阶', rpe: 9 },
        '减脂': { sets: 4, rest: 30, intensity: 0.65, mode: '循环组', strategy: '计时', diff: '标准', rpe: 7 },
        '耐力': { sets: 3, rest: 45, intensity: 0.50, mode: '超级组', strategy: '计时', diff: '标准', rpe: 6 },
        '爆发': { sets: 4, rest: 150, intensity: 0.70, mode: '常规组', strategy: '递增', diff: '进阶', rpe: 9 },
        '心肺': { sets: 4, rest: 20, intensity: 0.65, mode: '循环组', strategy: '计时', diff: '标准', rpe: 7 },
        '激活': { sets: 2, rest: 0, intensity: 0.40, mode: '常规组', strategy: '恒定', diff: '标准', rpe: 4 },
        '柔韧': { sets: 2, rest: 0, intensity: 0.30, mode: '常规组', strategy: '计时', diff: '标准', rpe: 3 },
        'HIIT': { sets: 6, rest: 30, intensity: 0.75, mode: '循环组', strategy: '计时', diff: '标准', rpe: 8 },
        '有氧': { sets: 4, rest: 15, intensity: 0.60, mode: '循环组', strategy: '计时', diff: '标准', rpe: 6 },
        '瑜伽': { sets: 1, rest: 0, intensity: 0.40, mode: '常规组', strategy: '计时', diff: '标准', rpe: 4 },
        '普拉提': { sets: 3, rest: 30, intensity: 0.50, mode: '常规组', strategy: '恒定', diff: '标准', rpe: 5 },
        '拉伸': { sets: 1, rest: 0, intensity: 0.20, mode: '常规组', strategy: '计时', diff: '保守', rpe: 2 },
        '恢复': { sets: 2, rest: 0, intensity: 0.30, mode: '常规组', strategy: '恒定', diff: '保守', rpe: 2 },
        '协调': { sets: 3, rest: 60, intensity: 0.50, mode: '常规组', strategy: '恒定', diff: '标准', rpe: 6 },
        '体态': { sets: 3, rest: 45, intensity: 0.50, mode: '常规组', strategy: '计时', diff: '标准', rpe: 5 },
        '平衡': { sets: 3, rest: 60, intensity: 0.50, mode: '常规组', strategy: '恒定', diff: '标准', rpe: 6 },
        '专项': { sets: 3, rest: 90, intensity: 0.70, mode: '常规组', strategy: '推荐', diff: '标准', rpe: 8 }
    },
    LEVEL_COEFF: { 'L1': 0.5, 'L2': 0.8, 'L3': 1.0, 'L4': 1.2, 'L5': 1.5 },
    LEVEL_SCALING: {
        'L1': { vol: 0.7, int: 0.85, rest: 1.2 },
        'L2': { vol: 0.85, int: 0.9, rest: 1.1 },
        'L3': { vol: 1.0, int: 1.0, rest: 1.0 },
        'L4': { vol: 1.2, int: 1.05, rest: 0.9 },
        'L5': { vol: 1.4, int: 1.1, rest: 0.8 }
    },
    PHASES: {
        '适应期': { intensity: 0.8, volume: 0.8, name: '适应激活期' },
        '进阶期': { intensity: 1.0, volume: 1.0, name: '肌肥大增长期' },
        '突破期': { intensity: 1.1, volume: 0.9, name: '力量突破期' },
        '减载期': { intensity: 0.6, volume: 0.6, name: '减载恢复期' }
    },
    TEMPLATES: [
        { id: 'TPL_001', name: '一分化 (全身)', goal: '增肌', level: 'All', freq: 1, slots: [{n:'全身综合', t:['全身']}] },
        { id: 'TPL_002', name: '二分化 (上下肢)', goal: '增肌', level: 'All', freq: 2, slots: [{n:'上肢力量', t:['胸部','背部','肩部','手臂']}, {n:'下肢力量', t:['臀部','腿部','核心']}] },
        { id: 'TPL_003', name: '三分化 (推拉腿)', goal: '增肌', level: 'All', gender: '男', freq: 3, slots: [{n:'推类力量', t:['胸部','肩部','手臂']}, {n:'拉类力量', t:['背部','核心']}, {n:'腿部驱动', t:['臀部','腿部']}] },
        { id: 'TPL_004', name: '三分化 (臀腿侧重)', goal: '增肌', level: 'All', gender: '女', freq: 3, slots: [{n:'臀腿塑形', t:['臀部','腿部']}, {n:'上肢塑形', t:['胸部','背部','肩部','手臂']}, {n:'臀腿强化', t:['臀部','腿部']}] },
        { id: 'TPL_005', name: '四分化 (非线性)', goal: '增肌', level: 'All', freq: 4, slots: [{n:'胸臂雕刻', t:['胸部','手臂']}, {n:'臀腿轰炸', t:['臀部','腿部']}, {n:'背肩强化', t:['背部','肩部']}, {n:'核心全身', t:['核心','全身']}] },
        { id: 'TPL_006', name: '五分化 (单部位)', goal: '增肌', level: 'All', freq: 5, slots: [{n:'胸部专项', t:['胸部']}, {n:'背部专项', t:['背部']}, {n:'肩部专项', t:['肩部']}, {n:'手臂专项', t:['手臂']}, {n:'臀腿专项', t:['臀部','腿部']}] },
        { id: 'TPL_FAT', name: '减脂循环', goal: '减脂', level: 'All', freq: 3, slots: [{n:'全身燃脂', t:['全身']}, {n:'核心燃脂', t:['核心','全身']}, {n:'全身燃脂', t:['全身']}] }
    ],
    load: [
        { name: '恒定', index: 'All', coeff: 1.0, inc: 0 },
        { name: '递增', index: '1', coeff: 0.85, inc: '+2' },
        { name: '递增', index: '2', coeff: 0.90, inc: '+1' },
        { name: '递增', index: '3+', coeff: 1.00, inc: 0 },
        { name: '递减', index: '1', coeff: 1.0, inc: 0 },
        { name: '递减', index: '2', coeff: 0.90, inc: '+2' },
        { name: '递减', index: '3+', coeff: 0.80, inc: '+4' }
    ],
    FLOWS: {
        'course': [
            { q: "想练点什么？", key: 'type', variant: 'askType', opts: CONSTANTS.ENUMS.COURSE_TYPES },
            { q: "重点想练哪个部位？", key: 'targets', variant: 'askTarget', opts: CONSTANTS.PARTS, multi: true },
            { q: "今天有多少时间？", key: 'duration', variant: 'askDuration', type: 'slider', min: 20, max: 90, step: 5, unit: '分钟' }
        ],
        'plan': [
            { q: "这个计划想持续多久？", key: 'cycle', variant: 'askCycle', type: 'slider', min: 1, max: 24, step: 1, unit: '周', default: 8 },
            { q: "请选择每周的训练日。", key: 'days', variant: 'askFreq', opts: CONSTANTS.WEEKDAYS, multi: true },
            { q: "每天平均训练多长时间？", key: 'duration', variant: 'askDuration', type: 'slider', min: 20, max: 60, step: 5, unit: '分钟', default: 30 }
        ]
    }
};