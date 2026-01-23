window.store = {
    version: 'V27.0',
    user: {
        gender: '男', age: 28, height: 178, weight: 80, targetWeight: 85,
        goal: '增肌', funcGoal: '', level: 'L3', style: '传统型', days: ['周一','周三','周五'],
        pain: [], missing: [], bodyType: '均衡标准型', dob: '1995-01-01', fatiguedParts: ['腿部'], duration: 30,
        rhr: 60, fatigue: 3
    },
    activeTab: 'basic',
    courseSettings: { loopMode: '常规', loadStrategy: '恒定', smartRec: true },
    flow: null, // 'course' | 'plan'
    step: 0,
    inputs: {},
    replaceState: null, // {pIdx, aIdx}
    libFilter: { part: '全部', tag: '全部' },
    activePlanPhaseIdx: 0
};