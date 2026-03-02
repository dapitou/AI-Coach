// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\data\config.js

window.CONFIG = {
    // 1.1 策略矩阵 (Strategy Matrix) - 定义不同目标和等级的基准参数
    STRATEGY: [
        { target: 'Muscle Gain', sets: 4, rest: 90, intensity: 0.75, mode: 'Regular', strategy: 'Progressive', rpe: 8 },
        { target: 'Strength', sets: 5, rest: 120, intensity: 0.85, mode: 'Regular', strategy: 'Constant', rpe: 8 },
        { target: 'Fat Loss', sets: 4, rest: 30, intensity: 0.65, mode: 'Circuit', strategy: 'Constant', rpe: 7 }, // Time-based usually Constant load (time)
        { target: 'Endurance', sets: 4, rest: 30, intensity: 0.50, mode: 'Circuit', strategy: 'Constant', rpe: 7 },
        { target: 'Power', sets: 4, rest: 150, intensity: 0.70, mode: 'Regular', strategy: 'Progressive', rpe: 8 },
        { target: 'Cardio', sets: 4, rest: 20, intensity: 0.65, mode: 'Circuit', strategy: 'Constant', rpe: 7 },
        { target: 'HIIT', sets: 6, rest: 30, intensity: 0.75, mode: 'Circuit', strategy: 'Constant', rpe: 8 },
        { target: 'Cardio', sets: 4, rest: 15, intensity: 0.60, mode: 'Circuit', strategy: 'Constant', rpe: 6 },
        { target: 'Yoga', sets: 1, rest: 0, intensity: 0.40, mode: 'Regular', strategy: 'Constant', rpe: 4 },
        { target: 'Pilates', sets: 3, rest: 30, intensity: 0.50, mode: 'Regular', strategy: 'Constant', rpe: 5 },
        { target: 'Stretch', sets: 1, rest: 0, intensity: 0.20, mode: 'Regular', strategy: 'Constant', rpe: 3 },
        { target: 'Recovery', sets: 2, rest: 0, intensity: 0.30, mode: 'Regular', strategy: 'Constant', rpe: 3 },
        { target: 'Flexibility', sets: 2, rest: 0, intensity: 0.30, mode: 'Regular', strategy: 'Constant', rpe: 4 },
        { target: 'Coordination', sets: 3, rest: 60, intensity: 0.50, mode: 'Regular', strategy: 'Constant', rpe: 5 },
        { target: 'Posture', sets: 3, rest: 45, intensity: 0.50, mode: 'Regular', strategy: 'Constant', rpe: 5 },
        { target: 'Activation', sets: 2, rest: 0, intensity: 0.40, mode: 'Regular', strategy: 'Constant', rpe: 4 },
        { target: 'Balance', sets: 3, rest: 60, intensity: 0.50, mode: 'Regular', strategy: 'Constant', rpe: 5 },
        { target: 'Specific', sets: 3, rest: 90, intensity: 0.70, mode: 'Regular', strategy: 'Recommended', rpe: 8 }
    ],

    // 1.2 课程环节模板 (Segment Templates) - 定义单节课的微观配方
    SEGMENT_TEMPLATES: [
        // 热身
        { id: 'TPL_SEG_001', name: 'Warmup_FullBody', dim: 'Part', target: 'Full Body', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.5}, {focusDim:'Func',focusTarget:'Flexibility',w:0.3}, {focusDim:'Func',focusTarget:'Coordination',w:0.2}], sort: [{dim:'Muscle',order:'升序'}, {dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Score',order:'降序'}] },
        { id: 'TPL_SEG_002', name: 'Warmup_Upper', dim: 'Part', target: 'Upper Body', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.5}, {focusDim:'Part',focusTarget:'Shoulder',w:0.3}, {focusDim:'Part',focusTarget:'Chest',w:0.2}], sort: [{dim:'Muscle',order:'升序'}, {dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Score',order:'降序'}] },
        { id: 'TPL_SEG_003', name: 'Warmup_Lower', dim: 'Part', target: 'Lower Body', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.5}, {focusDim:'Part',focusTarget:'Glute',w:0.3}, {focusDim:'Part',focusTarget:'Leg',w:0.2}], sort: [{dim:'Muscle',order:'升序'}, {dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Score',order:'降序'}] },
        
        // [NEW] 热身 - 精细化部位 (同步自运营后台)
        { id: 'TPL_SEG_004', name: 'Warmup_Chest', dim: 'Part', target: 'Chest', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.4}, {focusDim:'Part',focusTarget:'Shoulder',w:0.4}, {focusDim:'Part',focusTarget:'Chest',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_005', name: 'Warmup_Back', dim: 'Part', target: 'Back', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.4}, {focusDim:'Part',focusTarget:'Shoulder',w:0.4}, {focusDim:'Part',focusTarget:'Back',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_006', name: 'Warmup_Shoulder', dim: 'Part', target: 'Shoulder', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.4}, {focusDim:'Part',focusTarget:'Shoulder',w:0.4}, {focusDim:'Part',focusTarget:'Chest',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_007', name: 'Warmup_Arm', dim: 'Part', target: 'Arm', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.4}, {focusDim:'Part',focusTarget:'Shoulder',w:0.4}, {focusDim:'Part',focusTarget:'Arm',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_008', name: 'Warmup_Glute', dim: 'Part', target: 'Glute', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.4}, {focusDim:'Part',focusTarget:'Glute',w:0.4}, {focusDim:'Part',focusTarget:'Leg',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_009', name: 'Warmup_Leg', dim: 'Part', target: 'Leg', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.4}, {focusDim:'Part',focusTarget:'Glute',w:0.3}, {focusDim:'Part',focusTarget:'Leg',w:0.3}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_010', name: 'Warmup_Core', dim: 'Part', target: 'Core', type: 'Warmup', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Activation',w:0.5}, {focusDim:'Part',focusTarget:'Core',w:0.3}, {focusDim:'Part',focusTarget:'Glute',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },

        // 主训 - 全身
        { id: 'TPL_SEG_021', name: 'Main_FullBody_L1', dim: 'Part', target: 'Full Body', type: 'Main', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'Construct',focusTarget:'Compound',w:0.6}, {focusDim:'Construct',focusTarget:'Isolation',w:0.4}], sort: [{dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        { id: 'TPL_SEG_022', name: 'Main_FullBody_L3', dim: 'Part', target: 'Full Body', type: 'Main', levels: ['L3','L4'], gender: 'All', count: 99, slots: [{focusDim:'Mode',focusTarget:'Squat',w:0.2}, {focusDim:'Mode',focusTarget:'Hinge',w:0.2}, {focusDim:'Mode',focusTarget:'Push_H',w:0.2}, {focusDim:'Mode',focusTarget:'Pull_H',w:0.2}, {focusDim:'Mode',focusTarget:'Core_Stability',w:0.2}], sort: [{dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        // 主训 - 部位
        { id: 'TPL_SEG_036', name: 'Main_Chest_L1', dim: 'Part', target: 'Chest', type: 'Main', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'Construct',focusTarget:'Compound',w:0.6}, {focusDim:'Construct',focusTarget:'Isolation',w:0.4}], sort: [{dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        { id: 'TPL_SEG_037', name: 'Main_Chest_L3', dim: 'Part', target: 'Chest', type: 'Main', levels: ['L3','L4'], gender: 'All', count: 99, slots: [{focusDim:'Mode',focusTarget:'Push_H',w:0.5}, {focusDim:'Muscle',focusTarget:'胸大肌上束',w:0.3}, {focusDim:'Muscle',focusTarget:'胸大肌内侧',w:0.2}], sort: [{dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        { id: 'TPL_SEG_039', name: 'Main_Back_L1', dim: 'Part', target: 'Back', type: 'Main', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'Construct',focusTarget:'Compound',w:0.6}, {focusDim:'Mode',focusTarget:'Pull_H',w:0.4}], sort: [{dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        { id: 'TPL_SEG_040', name: 'Main_Back_L3', dim: 'Part', target: 'Back', type: 'Main', levels: ['L3','L4'], gender: 'All', count: 99, slots: [{focusDim:'Mode',focusTarget:'Pull_V',w:0.4}, {focusDim:'Mode',focusTarget:'Pull_H',w:0.4}, {focusDim:'Muscle',focusTarget:'竖脊肌',w:0.2}], sort: [{dim:'Construct',order:'自定义',seq:'Compound,Isolation'}, {dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        // 主训 - 功能
        { id: 'TPL_SEG_060', name: 'Main_HIIT_L1', dim: 'Func', target: 'Cardio', type: 'Main', levels: ['L1','L2'], gender: 'All', count: 99, slots: [{focusDim:'Func',focusTarget:'Cardio',w:0.7}, {focusDim:'Mode',focusTarget:'Core_Stability',w:0.3}], sort: [{dim:'MET',order:'降序'}, {dim:'Score',order:'降序'}] },
        // 放松
        { id: 'TPL_SEG_011', name: 'Cooldown_FullBody', dim: 'Part', target: 'Full Body', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Func',focusTarget:'Recovery',w:0.6}, {focusDim:'Func',focusTarget:'Flexibility',w:0.4}], sort: [{dim:'Muscle',order:'升序'}, {dim:'Score',order:'降序'}] },
        
        // [NEW] 放松 - 精细化部位 (同步自运营后台)
        { id: 'TPL_SEG_012', name: 'Cooldown_Upper', dim: 'Part', target: 'Upper Body', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Shoulder',w:0.4}, {focusDim:'Part',focusTarget:'Back',w:0.3}, {focusDim:'Part',focusTarget:'Chest',w:0.3}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_013', name: 'Cooldown_Lower', dim: 'Part', target: 'Lower Body', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Leg',w:0.5}, {focusDim:'Part',focusTarget:'Glute',w:0.3}, {focusDim:'Part',focusTarget:'Lower Back',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_014', name: 'Cooldown_Chest', dim: 'Part', target: 'Chest', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Chest',w:0.6}, {focusDim:'Part',focusTarget:'Shoulder',w:0.4}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_015', name: 'Cooldown_Back', dim: 'Part', target: 'Back', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Back',w:0.6}, {focusDim:'Part',focusTarget:'Shoulder',w:0.2}, {focusDim:'Part',focusTarget:'Lower Back',w:0.2}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_016', name: 'Cooldown_Shoulder', dim: 'Part', target: 'Shoulder', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Shoulder',w:0.7}, {focusDim:'Part',focusTarget:'Neck',w:0.3}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_017', name: 'Cooldown_Arm', dim: 'Part', target: 'Arm', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Arm',w:0.7}, {focusDim:'Part',focusTarget:'Shoulder',w:0.3}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_018', name: 'Cooldown_Glute', dim: 'Part', target: 'Glute', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Glute',w:0.7}, {focusDim:'Part',focusTarget:'Lower Back',w:0.3}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_019', name: 'Cooldown_Leg', dim: 'Part', target: 'Leg', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Leg',w:0.7}, {focusDim:'Part',focusTarget:'Glute',w:0.3}], sort: [{dim:'Muscle',order:'升序'}] },
        { id: 'TPL_SEG_020', name: 'Cooldown_Core', dim: 'Part', target: 'Core', type: 'Cooldown', levels: ['All'], gender: 'All', count: 6, slots: [{focusDim:'Part',focusTarget:'Core',w:0.5}, {focusDim:'Part',focusTarget:'Lower Back',w:0.5}], sort: [{dim:'Muscle',order:'升序'}] }
    ],

    // 1.4 等级强度系数 (Levels)
    LEVELS: [
        { level: 'L1', capacity: 0.6, intensity: 0.6, rest: 1.5, strategy: 'Constant' },
        { level: 'L2', capacity: 0.8, intensity: 0.8, rest: 1.2, strategy: 'Constant' },
        { level: 'L3', capacity: 1.0, intensity: 1.0, rest: 1.0, strategy: 'Progressive' },
        { level: 'L4', capacity: 1.2, intensity: 1.1, rest: 0.8, strategy: 'Progressive' },
        { level: 'L5', capacity: 1.4, intensity: 1.2, rest: 0.6, strategy: 'Regressive' }
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
        { id: 'TPL_HYP_1', name: 'Split_1_FullBody', goal: 'Muscle Gain', freq: 1, level: 'All', basicSlots: [{name:'Full Body', type:'Strength', focusDim:'Part', focusTarget:'Full Body'}] },
        { id: 'TPL_HYP_2', name: 'Split_2_UpperLower', goal: 'Muscle Gain', freq: 2, level: 'All', basicSlots: [{name:'Upper Body', type:'Strength', focusDim:'Part', focusTarget:'Chest'}, {name:'Lower Body', type:'Strength', focusDim:'Part', focusTarget:'Leg'}] },
        { id: 'TPL_HYP_3', name: 'Split_3_PPL', goal: 'Muscle Gain', freq: 3, level: 'All', gender: 'Male', basicSlots: [{name:'Push', type:'Strength', focusDim:'Mode', focusTarget:'Push_H'}, {name:'Pull', type:'Strength', focusDim:'Mode', focusTarget:'Pull_V'}, {name:'Legs', type:'Strength', focusDim:'Mode', focusTarget:'Squat'}] },
        { id: 'TPL_HYP_4', name: 'Split_4_NonLinear', goal: 'Muscle Gain', freq: 4, level: 'All', basicSlots: [{name:'Chest & Arm', type:'Strength', focusDim:'Part', focusTarget:'Chest'}, {name:'Glute & Leg', type:'Strength', focusDim:'Part', focusTarget:'Leg'}, {name:'Back & Shoulder', type:'Strength', focusDim:'Part', focusTarget:'Back'}, {name:'Core & Full', type:'Strength', focusDim:'Part', focusTarget:'Core'}] },
        { id: 'TPL_FAT_3', name: 'FatLoss_Circuit_3', goal: 'Fat Loss', freq: 3, level: 'All', basicSlots: [{name:'Full Body HIIT', type:'HIIT', focusDim:'Part', focusTarget:'Full Body'}, {name:'Cardio', type:'Cardio', focusDim:'Part', focusTarget:'Full Body'}, {name:'Core', type:'Strength', focusDim:'Part', focusTarget:'Core'}] }
    ],

    // 1.6 训练范式 (Paradigms)
    PARADIGMS: [
        { name: 'Resistance', types: ['Strength', 'Rehab', 'Golf'], feature: 'Load Focus', sets: 3, strategy: 'Recommended' },
        { name: 'Interval', types: ['HIIT', 'Cardio', 'Combat'], feature: 'HR Focus', sets: 4, strategy: 'Constant' },
        { name: 'Flow', types: ['Yoga', 'Pilates', 'Stretch', 'Meditation'], feature: 'Flow Focus', sets: 1, strategy: 'Constant' }
    ],

    // 2.1 负荷策略 (Load Strategies)
    LOAD_STRATEGIES: [
        { name: 'Constant', index: 'All', coeff: 1.0, inc: 0 },
        { name: 'Progressive', index: '1', coeff: 0.85, inc: 2 },
        { name: 'Progressive', index: '2', coeff: 0.90, inc: 1 },
        { name: 'Progressive', index: '3+', coeff: 1.00, inc: 0 },
        { name: 'Regressive', index: '1', coeff: 1.0, inc: 0 },
        { name: 'Regressive', index: '2', coeff: 0.90, inc: 2 },
        { name: 'Regressive', index: '3+', coeff: 0.80, inc: 4 }
    ],

    // 2.3 阶段周期策略 (Phase Strategies)
    PHASE_STRATEGIES: [
        { cycle: '1周', structure: ['Progression'], alloc: [1] },
        { cycle: '2周', structure: ['Adaptation', 'Progression'], alloc: [0.5, 0.5] },
        { cycle: '3周', structure: ['Adaptation', 'Progression', 'Peak'], alloc: [0.33, 0.33, 0.33] },
        { cycle: '4周', structure: ['Adaptation', 'Progression', 'Peak', 'Deload'], alloc: [0.25, 0.25, 0.25, 0.25] },
        { cycle: '>4周', structure: ['Adaptation', 'Progression', 'Peak', 'Deload'], alloc: [0.25, 0.40, 0.25, 0.10] }
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
        { range: [85, 100], label: 'Recovered', capacity: 1.1, intensity: 1.1 },
        { range: [55, 84], label: 'Recovering', capacity: 1.0, intensity: 1.0 },
        { range: [30, 54], label: 'Fatigued', capacity: 0.8, intensity: 0.8 },
        { range: [0, 29], label: 'Exhausted', capacity: 0.5, intensity: 0.5 }
    ],

    // 交互流程配置 (Flows)
    FLOWS: {
        'course': [
            { q: "想练点什么？", key: 'type', variant: 'askType', opts: ['Strength', 'Cardio', 'HIIT', 'Yoga', 'Pilates', 'Stretch'] },
            { q: "重点想练哪个部位？", key: 'targets', variant: 'askTarget', opts: ['Full Body', 'Chest', 'Back', 'Shoulder', 'Arm', 'Glute', 'Leg', 'Core'], multi: true },
            { q: "今天有多少时间？", key: 'duration', variant: 'askDuration', type: 'slider', min: 20, max: 90, step: 5, unit: 'min' }
        ],
        'plan': [
            { q: "这个计划想持续多久？", key: 'cycle', variant: 'askCycle', type: 'slider', min: 1, max: 24, step: 1, unit: 'Week', default: 4 },
            { q: "请选择每周的训练日。", key: 'days', variant: 'askFreq', opts: ['Mon','Tue','Wed','Thu','Fri','Sat','Sun'], multi: true },
            { q: "每天平均训练多长时间？", key: 'duration', variant: 'askDuration', type: 'slider', min: 20, max: 60, step: 5, unit: 'min', default: 30 }
        ]
    }
};
