const FALLBACK_DB = [];

let DB = [];

// Async Load Action Library
(async function initDB() {
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
        DB = data.map(a => ({
            ...a,
            pain: a.pain || [], // Ensure array to prevent crash
            equip: a.equip || [], // Ensure array to prevent crash
            lastTrained: new Date(Date.now() - Math.random() * 1000000000),
            isFav: Math.random() > 0.8,
            demoUser1RM: (a.demoUser1RM !== undefined) ? a.demoUser1RM : (a.defaultWeight ? Math.round(a.defaultWeight * 1.5) : (CONSTANTS.ENUMS.ONE_RM[a.part] || 20))
        }));
    }
})();