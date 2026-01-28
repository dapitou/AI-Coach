// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\data\config.js

window.CONFIG = {
    // 1.1 策略矩阵 (Strategy Matrix) - 定义不同目标和等级的基准参数
    STRATEGY: [
        { target: '增肌', sets: 4, rest: 90, intensity: 0.75, mode: '常规', strategy: '递增', rpe: 8 },
        { target: '力量', sets: 5, rest: 120, intensity: 0.85, mode: '常规', strategy: '恒定', rpe: 8 },
        { target: '减脂', sets: 4, rest: 30, intensity: 0.65, mode: '循环', strategy: '计时', rpe: 7 },
        { target: '耐力', sets: 4, rest: 30, intensity: 0.50, mode: '超级', strategy: '计时', rpe: 7 },
        { target: '爆发', sets: 4, rest: 150, intensity: 0.70, mode: '常规', strategy: '递增', rpe: 8 },
        { target: '心肺', sets: 4, rest: 20, intensity: 0.65, mode: '循环', strategy: '计时', rpe: 7 },
        { target: 'HIIT', sets: 6, rest: 30, intensity: 0.75, mode: '循环', strategy: '计时', rpe: 8 },
        { target: '有氧', sets: 4, rest: 15, intensity: 0.60, mode: '循环', strategy: '计时', rpe: 6 },
        { target: '瑜伽', sets: 1, rest: 0, intensity: 0.40, mode: '常规', strategy: '计时', rpe: 4 },
        { target: '普拉提', sets: 3, rest: 30, intensity: 0.50, mode: '常规', strategy: '恒定', rpe: 5 },
        { target: '拉伸', sets: 1, rest: 0, intensity: 0.20, mode: '常规', strategy: '计时', rpe: 3 },
        { target: '恢复', sets: 2, rest: 0, intensity: 0.30, mode: '常规', strategy: '恒定', rpe: 3 },
        { target: '柔韧', sets: 2, rest: 0, intensity: 0.30, mode: '常规', strategy: '计时', rpe: 4 },
        { target: '协调', sets: 3, rest: 60, intensity: 0.50, mode: '常规', strategy: '恒定', rpe: 5 },
        { target: '体态', sets: 3, rest: 45, intensity: 0.50, mode: '常规', strategy: '计时', rpe: 5 },
        { target: '激活', sets: 2, rest: 0, intensity: 0.40, mode: '常规', strategy: '恒定', rpe: 4 },
        { target: '平衡', sets: 3, rest: 60, intensity: 0.50, mode: '常规', strategy: '恒定', rpe: 5 },
        { target: '专项', sets: 3, rest: 90, intensity: 0.70, mode: '常规', strategy: '推荐', rpe: 8 }
    ],

    // 1.2 课程环节模板 (Segment Templates) - 定义单节课的微观配方
    SEGMENT_TEMPLATES: [
        // 热身
        { id: 'TPL_SEG_001', name: '热身_全身', dim: '部位', target: '全身', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.5}, {focusDim:'动作功能',focusTarget:'柔韧',w:0.3}, {focusDim:'动作功能',focusTarget:'协调',w:0.2}], sort: [{dim:'主动肌',order:'升序'}, {dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'推荐权重',order:'降序'}] },
        { id: 'TPL_SEG_002', name: '热身_上肢', dim: '部位', target: '上肢', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.5}, {focusDim:'部位',focusTarget:'肩部',w:0.3}, {focusDim:'部位',focusTarget:'胸部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}, {dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'推荐权重',order:'降序'}] },
        { id: 'TPL_SEG_003', name: '热身_下肢', dim: '部位', target: '下肢', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.5}, {focusDim:'部位',focusTarget:'臀部',w:0.3}, {focusDim:'部位',focusTarget:'腿部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}, {dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'推荐权重',order:'降序'}] },
        
        // [NEW] 热身 - 精细化部位 (同步自运营后台)
        { id: 'TPL_SEG_004', name: '热身_胸部', dim: '部位', target: '胸部', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.4}, {focusDim:'部位',focusTarget:'肩部',w:0.4}, {focusDim:'部位',focusTarget:'胸部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_005', name: '热身_背部', dim: '部位', target: '背部', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.4}, {focusDim:'部位',focusTarget:'肩部',w:0.4}, {focusDim:'部位',focusTarget:'背部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_006', name: '热身_肩部', dim: '部位', target: '肩部', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.4}, {focusDim:'部位',focusTarget:'肩部',w:0.4}, {focusDim:'部位',focusTarget:'胸部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_007', name: '热身_手臂', dim: '部位', target: '手臂', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.4}, {focusDim:'部位',focusTarget:'肩部',w:0.4}, {focusDim:'部位',focusTarget:'手臂',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_008', name: '热身_臀部', dim: '部位', target: '臀部', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.4}, {focusDim:'部位',focusTarget:'臀部',w:0.4}, {focusDim:'部位',focusTarget:'腿部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_009', name: '热身_腿部', dim: '部位', target: '腿部', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.4}, {focusDim:'部位',focusTarget:'臀部',w:0.3}, {focusDim:'部位',focusTarget:'腿部',w:0.3}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_010', name: '热身_核心', dim: '部位', target: '核心', type: '热身', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'激活',w:0.5}, {focusDim:'部位',focusTarget:'核心',w:0.3}, {focusDim:'部位',focusTarget:'臀部',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },

        // 主训 - 全身
        { id: 'TPL_SEG_021', name: '全身_初级', dim: '部位', target: '全身', type: '主训', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'动作构造',focusTarget:'复合动作',w:0.6}, {focusDim:'动作构造',focusTarget:'孤立动作',w:0.4}], sort: [{dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        { id: 'TPL_SEG_022', name: '全身_中级', dim: '部位', target: '全身', type: '主训', levels: ['L3','L4'], gender: 'All', count: 99, slots: [{focusDim:'动作模式',focusTarget:'膝主导',w:0.2}, {focusDim:'动作模式',focusTarget:'髋主导',w:0.2}, {focusDim:'动作模式',focusTarget:'水平推',w:0.2}, {focusDim:'动作模式',focusTarget:'水平拉',w:0.2}, {focusDim:'动作模式',focusTarget:'核心稳定',w:0.2}], sort: [{dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        // 主训 - 部位
        { id: 'TPL_SEG_036', name: '胸部_初级', dim: '部位', target: '胸部', type: '主训', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'动作构造',focusTarget:'复合动作',w:0.6}, {focusDim:'动作构造',focusTarget:'孤立动作',w:0.4}], sort: [{dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        { id: 'TPL_SEG_037', name: '胸部_中级', dim: '部位', target: '胸部', type: '主训', levels: ['L3','L4'], gender: 'All', count: 99, slots: [{focusDim:'动作模式',focusTarget:'水平推',w:0.5}, {focusDim:'主动肌',focusTarget:'胸大肌上束',w:0.3}, {focusDim:'主动肌',focusTarget:'胸大肌内侧',w:0.2}], sort: [{dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        { id: 'TPL_SEG_039', name: '背部_初级', dim: '部位', target: '背部', type: '主训', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'动作构造',focusTarget:'复合动作',w:0.6}, {focusDim:'动作模式',focusTarget:'水平拉',w:0.4}], sort: [{dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        { id: 'TPL_SEG_040', name: '背部_中级', dim: '部位', target: '背部', type: '主训', levels: ['L3','L4'], gender: 'All', count: 99, slots: [{focusDim:'动作模式',focusTarget:'垂直拉',w:0.4}, {focusDim:'动作模式',focusTarget:'水平拉',w:0.4}, {focusDim:'主动肌',focusTarget:'竖脊肌',w:0.2}], sort: [{dim:'动作构造',order:'自定义',seq:'复合动作,孤立动作'}, {dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        // 主训 - 功能
        { id: 'TPL_SEG_060', name: 'HIIT_初级', dim: '动作功能', target: '心肺', type: '主训', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'动作功能',focusTarget:'心肺',w:0.7}, {focusDim:'动作模式',focusTarget:'核心稳定',w:0.3}], sort: [{dim:'MET值',order:'降序'}, {dim:'推荐权重',order:'降序'}] },
        // 放松
        { id: 'TPL_SEG_011', name: '放松_全身', dim: '部位', target: '全身', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'动作功能',focusTarget:'恢复',w:0.6}, {focusDim:'动作功能',focusTarget:'柔韧',w:0.4}], sort: [{dim:'主动肌',order:'升序'}, {dim:'推荐权重',order:'降序'}] },
        
        // [NEW] 放松 - 精细化部位 (同步自运营后台)
        { id: 'TPL_SEG_012', name: '放松_上肢', dim: '部位', target: '上肢', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'肩部',w:0.4}, {focusDim:'部位',focusTarget:'背部',w:0.3}, {focusDim:'部位',focusTarget:'胸部',w:0.3}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_013', name: '放松_下肢', dim: '部位', target: '下肢', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'腿部',w:0.5}, {focusDim:'部位',focusTarget:'臀部',w:0.3}, {focusDim:'部位',focusTarget:'下背',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_014', name: '放松_胸部', dim: '部位', target: '胸部', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'胸部',w:0.6}, {focusDim:'部位',focusTarget:'肩部',w:0.4}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_015', name: '放松_背部', dim: '部位', target: '背部', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'背部',w:0.6}, {focusDim:'部位',focusTarget:'肩部',w:0.2}, {focusDim:'部位',focusTarget:'下背',w:0.2}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_016', name: '放松_肩部', dim: '部位', target: '肩部', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'肩部',w:0.7}, {focusDim:'部位',focusTarget:'颈部',w:0.3}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_017', name: '放松_手臂', dim: '部位', target: '手臂', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'手臂',w:0.7}, {focusDim:'部位',focusTarget:'肩部',w:0.3}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_018', name: '放松_臀部', dim: '部位', target: '臀部', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'臀部',w:0.7}, {focusDim:'部位',focusTarget:'下背',w:0.3}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_019', name: '放松_腿部', dim: '部位', target: '腿部', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'腿部',w:0.7}, {focusDim:'部位',focusTarget:'臀部',w:0.3}], sort: [{dim:'主动肌',order:'升序'}] },
        { id: 'TPL_SEG_020', name: '放松_核心', dim: '部位', target: '核心', type: '放松', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'部位',focusTarget:'核心',w:0.5}, {focusDim:'部位',focusTarget:'下背',w:0.5}], sort: [{dim:'主动肌',order:'升序'}] }
    ],

    // 1.4 等级强度系数 (Levels)
    LEVELS: [
        { level: 'L1', coeff: 0.5 },
        { level: 'L2', coeff: 0.8 },
        { level: 'L3', coeff: 1.0 },
        { level: 'L4', coeff: 1.2 },
        { level: 'L5', coeff: 1.5 }
    ],

    // 3.2 难度分布 (Difficulty Distribution)
    DIFF: [
        { level: 'L1', l1: 0.8, l2: 0.2, l3: 0, l4: 0, l5: 0 },
        { level: 'L2', l1: 0.3, l2: 0.6, l3: 0.1, l4: 0, l5: 0 },
        { level: 'L3', l1: 0.1, l2: 0.2, l3: 0.6, l4: 0.1, l5: 0 },
        { level: 'L4', l1: 0, l2: 0.1, l3: 0.3, l4: 0.5, l5: 0.1 },
        { level: 'L5', l1: 0, l2: 0, l3: 0.2, l4: 0.3, l5: 0.5 }
    ],

    // 1.5 计划模板 (Plan Templates) - 定义周排课逻辑
    PLAN_TEMPLATES: [
        { id: 'TPL_HYP_1', name: '一分化 (全身综合)', goal: '增肌', freq: 1, level: 'All', basicSlots: [{name:'全身综合', type:'力量', focusDim:'部位', focusTarget:'全身'}] },
        { id: 'TPL_HYP_2', name: '二分化 (上下肢)', goal: '增肌', freq: 2, level: 'All', basicSlots: [{name:'上肢日', type:'力量', focusDim:'部位', focusTarget:'胸部'}, {name:'下肢日', type:'力量', focusDim:'部位', focusTarget:'腿部'}] },
        { id: 'TPL_HYP_3', name: '三分化 (推拉腿)', goal: '增肌', freq: 3, level: 'All', gender: '男', basicSlots: [{name:'推力日', type:'力量', focusDim:'动作模式', focusTarget:'水平推'}, {name:'拉力日', type:'力量', focusDim:'动作模式', focusTarget:'垂直拉'}, {name:'腿部日', type:'力量', focusDim:'动作模式', focusTarget:'膝主导'}] },
        { id: 'TPL_HYP_4', name: '四分化 (非线性)', goal: '增肌', freq: 4, level: 'All', basicSlots: [{name:'胸臂雕刻', type:'力量', focusDim:'部位', focusTarget:'胸部'}, {name:'臀腿轰炸', type:'力量', focusDim:'部位', focusTarget:'腿部'}, {name:'背肩强化', type:'力量', focusDim:'部位', focusTarget:'背部'}, {name:'核心全身', type:'力量', focusDim:'部位', focusTarget:'核心'}] },
        { id: 'TPL_FAT_3', name: '减脂循环 (3天)', goal: '减脂', freq: 3, level: 'All', basicSlots: [{name:'全身HIIT', type:'HIIT', focusDim:'部位', focusTarget:'全身'}, {name:'有氧耐力', type:'有氧', focusDim:'部位', focusTarget:'全身'}, {name:'核心强化', type:'力量', focusDim:'部位', focusTarget:'核心'}] }
    ],

    // 1.6 训练范式 (Paradigms)
    PARADIGMS: [
        { name: '抗阻范式', types: ['力量', '康复', '高尔夫'], feature: '关注负荷', sets: 3, strategy: '推荐' },
        { name: '间歇范式', types: ['HIIT', '有氧', '搏击'], feature: '关注心率', sets: 4, strategy: '计时' },
        { name: '流式范式', types: ['瑜伽', '普拉提', '拉伸', '冥想'], feature: '关注流动', sets: 1, strategy: '计时' }
    ],

    // 2.1 负荷策略 (Load Strategies)
    LOAD_STRATEGIES: [
        { name: '恒定', index: 'All', coeff: 1.0, inc: 0 },
        { name: '递增', index: '1', coeff: 0.85, inc: 2 },
        { name: '递增', index: '2', coeff: 0.90, inc: 1 },
        { name: '递增', index: '3+', coeff: 1.00, inc: 0 },
        { name: '递减', index: '1', coeff: 1.0, inc: 0 },
        { name: '递减', index: '2', coeff: 0.90, inc: 2 },
        { name: '递减', index: '3+', coeff: 0.80, inc: 4 }
    ],

    // 2.3 阶段周期策略 (Phase Strategies)
    PHASE_STRATEGIES: [
        { cycle: '1周', structure: ['进阶期'], alloc: [1] },
        { cycle: '2周', structure: ['适应期', '进阶期'], alloc: [0.5, 0.5] },
        { cycle: '3周', structure: ['适应期', '进阶期', '突破期'], alloc: [0.33, 0.33, 0.33] },
        { cycle: '4周', structure: ['适应期', '进阶期', '突破期', '减载期'], alloc: [0.25, 0.25, 0.25, 0.25] },
        { cycle: '>4周', structure: ['适应期', '进阶期', '突破期', '减载期'], alloc: [0.25, 0.40, 0.25, 0.10] }
    ],

    // 3.1 推荐因子 (Factors)
    FACTORS: [
        { key: '新鲜奖励', weight: 60, rule: '未练天数 > 7' },
        { key: '收藏奖励', weight: 50, rule: '是否收藏 = True' },
        { key: '探索奖励', weight: 30, rule: '历史训练次数 == 0' },
        { key: '厌倦惩罚', weight: -80, rule: '连续出现次数 ≥ 3' },
        { key: '冷宫惩罚', weight: -50, rule: '移除日期 ≤ 30天' },
        { key: '疲劳惩罚', weight: -50, rule: '辅助肌状态 < 55' }
    ],

    // 4.1 状态适配 (Status)
    STATUS_CONFIG: [
        { range: [85, 100], label: '已恢复', intensity: 1.0, volume: 1.0 },
        { range: [55, 84], label: '恢复中', intensity: 0.9, volume: 1.0 },
        { range: [30, 54], label: '疲劳中', intensity: 0.8, volume: 0.8 },
        { range: [0, 29], label: '已力竭', intensity: 0.5, volume: 0.5 }
    ],

    // 交互流程配置 (Flows)
    FLOWS: {
        'course': [
            { q: "想练点什么？", key: 'type', variant: 'askType', opts: ['力量', '有氧', 'HIIT', '瑜伽', '普拉提', '拉伸'] },
            { q: "重点想练哪个部位？", key: 'targets', variant: 'askTarget', opts: ['全身', '胸部', '背部', '肩部', '手臂', '臀部', '腿部', '核心'], multi: true },
            { q: "今天有多少时间？", key: 'duration', variant: 'askDuration', type: 'slider', min: 20, max: 90, step: 5, unit: '分钟' }
        ],
        'plan': [
            { q: "这个计划想持续多久？", key: 'cycle', variant: 'askCycle', type: 'slider', min: 1, max: 24, step: 1, unit: '周', default: 4 },
            { q: "请选择每周的训练日。", key: 'days', variant: 'askFreq', opts: ['周一','周二','周三','周四','周五','周六','周日'], multi: true },
            { q: "每天平均训练多长时间？", key: 'duration', variant: 'askDuration', type: 'slider', min: 20, max: 60, step: 5, unit: '分钟', default: 30 }
        ]
    }
};
