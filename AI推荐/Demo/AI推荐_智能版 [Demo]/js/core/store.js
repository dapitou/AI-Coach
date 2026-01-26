// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\core\store.js

window.store = {
    version: 'V27.0',
    user: {
        gender: '男', age: 28, height: 178, weight: 80, targetWeight: 85,
        goal: '增肌', funcGoal: '力量', level: 'L3', style: '传统型', days: ['周一','周三','周五'],
        pain: [], missing: [], bodyType: '均衡标准型', dob: '1995-01-01', fatiguedParts: ['腿部'], duration: 30,
        rhr: 60, fatigue: 3
    },
    activeTab: 'basic',
    courseSettings: { loopMode: '常规组', loadStrategy: '推荐', smartRec: true },
    flow: null,
    step: 0,
    inputs: {},
    replaceState: null,
    libFilter: { part: '全部', tag: '全部' },
    activePlanPhaseIdx: 0
};
