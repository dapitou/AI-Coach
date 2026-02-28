// e:\AI-Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\data\database.js

// ... (Keep FALLBACK_DB as is) ...

let DB = [];

// Async Load Action Library
(async function initDB() {
    // [NEW] Try loading from LocalStorage (Ops Backend Sync)
    try {
        const localDB = localStorage.getItem('AEKE_ACTION_DB');
        if (localDB) {
            const data = JSON.parse(localDB);
            if (Array.isArray(data) && data.length > 0) {
                processData(data);
                console.log(`[ActionLibrary] Loaded ${DB.length} actions from LocalStorage (Ops Sync).`);
                return; // Skip fetch if local data exists
            }
        }
    } catch (e) {
        console.warn("Failed to load LocalStorage DB:", e);
    }

    try {
        const response = await fetch('js/data/动作库.json'); // Adjusted path relative to index.html
        const data = await response.json();
        processData(data);
        console.log(`[ActionLibrary] Loaded ${DB.length} actions from JSON.`);
    } catch (error) {
        console.warn("Failed to load Action Library, using Fallback Data:", error);
        processData(FALLBACK_DB);
    }

    function processData(data) {
        const map = window.CONSTANTS.CN_TO_EN;
        const translate = (val) => map[val] || val;
        const translateArr = (arr) => arr ? arr.map(v => map[v] || v) : [];

        DB = data.map(a => ({
            ...a,
            part: translate(a.part),
            muscle: translate(a.muscle),
            antagonist: translate(a.antagonist),
            mode: translate(a.mode),
            func: translateArr(a.func || []),
            equip: translateArr(a.equip || []),
            pain: translateArr(a.pain || []),
            subPart: translateArr(a.subPart || []),
            difficulty: translate(a.level), // Map level to difficulty
            impact: translate(a.impact),
            construct: translate(a.construct),
            posture: translate(a.posture),
            
            // Mock runtime data if missing
            lastTrained: a.lastTrained || new Date(Date.now() - Math.random() * 1000000000),
            isFav: (a.isFav !== undefined) ? a.isFav : (Math.random() > 0.8),
            demoUser1RM: (a.demoUser1RM !== undefined) ? a.demoUser1RM : (a.defaultWeight ? Math.round(a.defaultWeight * 1.5) : (CONSTANTS.ENUMS.ONE_RM[a.part] || 20))
        }));
    }
})();
