// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\modules\i18n-manager.js
window.I18n = {
    currentLang: 'zh_CN',
    data: {},
    
    init: () => {
        // 1. Load Data (Robust Check)
        if (window.I18nData && Object.keys(window.I18nData).length > 0) {
            I18n.data = window.I18nData;
            console.log(`[I18n] Loaded ${Object.keys(I18n.data).length} keys.`);
        } else {
            console.error("[I18n] Critical Error: I18nData not found or empty!");
            I18n.data = {};
        }

        // 2. Load Language Preference
        const saved = localStorage.getItem('AEKE_LANG');
        if (saved && I18n.isSupported(saved)) {
            I18n.currentLang = saved;
        } else {
            I18n.currentLang = 'zh_CN';
        }
        console.log(`[I18n] Initialized with language: ${I18n.currentLang}`);
        
        // 3. Sync UI
        const select = document.getElementById('lang-select');
        if (select) select.value = I18n.currentLang;

        // 4. Initial Render
        I18n.updateDOM();
    },

    isSupported: (lang) => {
        const supported = ['zh_CN', 'zh_HK', 'en_US', 'es_ES', 'ru_RU', 'de_DE', 'fr_FR', 'pt_PT', 'it_IT', 'ar_SA', 'ja_JP', 'ko_KR', 'pl_PL', 'th_TH'];
        return supported.includes(lang);
    },

    setLanguage: (lang) => {
        if (!I18n.isSupported(lang)) return;
        console.log(`[I18n] Switching to: ${lang}`);
        
        I18n.currentLang = lang;
        localStorage.setItem('AEKE_LANG', lang);
        
        // Sync UI
        const select = document.getElementById('lang-select');
        if (select && select.value !== lang) select.value = lang;

        // Update Static Text
        I18n.updateDOM();
        
        // Force Refresh Dynamic Views
        if (window.ViewHome && document.getElementById('view-home').classList.contains('active')) {
            window.ViewHome.renderProfile();
        }
        if (window.ViewResult && document.getElementById('view-result').classList.contains('active')) {
            window.ViewResult.showResult();
        }
        if (window.ViewLibrary && document.getElementById('view-library').classList.contains('active')) {
            window.ViewLibrary.renderLibraryFilters();
            window.ViewLibrary.renderLibraryList();
        }
    },

    t: (key, params = {}) => {
        if (!key) return '';
        
        // Handle Enum Keys (e.g. "enum_增肌")
        let lookupKey = key;
        
        // Check if data exists
        const entry = I18n.data[lookupKey];
        
        if (!entry) {
            // Fallback: If key starts with enum_, return the suffix
            if (typeof key === 'string' && key.startsWith('enum_')) {
                return key.replace('enum_', '');
            }
            return key;
        }
        
        // Get Translation
        let text = entry[I18n.currentLang];
        
        // Fallbacks
        if (text === undefined || text === null || text === '') text = entry['zh_CN']; // Fallback to CN
        if (text === undefined || text === null || text === '') text = entry['en_US']; // Fallback to EN
        if (text === undefined || text === null || text === '') text = key; // Fallback to Key
        
        if (typeof text !== 'string') text = String(text);

        // Replace Params
        Object.keys(params).forEach(k => {
            text = text.replace(new RegExp(`{${k}}`, 'g'), params[k]);
        });
        
        return text;
    },

    updateDOM: () => {
        // Update text content
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            if (key) el.innerText = I18n.t(key);
        });

        // Update placeholders
        document.querySelectorAll('[data-i18n-ph]').forEach(el => {
            const key = el.getAttribute('data-i18n-ph');
            if (key) el.placeholder = I18n.t(key);
        });
        
        // RTL Support
        if (I18n.currentLang === 'ar_SA') {
            document.body.classList.add('rtl-mode');
            document.body.style.direction = 'rtl';
        } else {
            document.body.classList.remove('rtl-mode');
            document.body.style.direction = 'ltr';
        }
    },

    exportConfig: () => {
        if (typeof XLSX === 'undefined') {
            alert("无法加载 Excel 导出库 (XLSX)，请检查网络连接。");
            return;
        }

        try {
            const headers = ['Key', 'Description', 'Char Check', 'zh_CN', 'zh_HK', 'en_US', 'es_ES', 'ru_RU', 'de_DE', 'fr_FR', 'pt_PT', 'it_IT', 'ar_SA', 'ja_JP', 'ko_KR', 'pl_PL', 'th_TH'];
            
            const data = [];
            Object.keys(I18n.data).sort().forEach(key => {
                const item = I18n.data[key];
                const row = {
                    'Key': key,
                    'Description': item.desc || '',
                    'Char Check': item.limit || '',
                    'zh_CN': item.zh_CN || '',
                    'zh_HK': item.zh_HK || '',
                    'en_US': item.en_US || '',
                    'es_ES': item.es_ES || '',
                    'ru_RU': item.ru_RU || '',
                    'de_DE': item.de_DE || '',
                    'fr_FR': item.fr_FR || '',
                    'pt_PT': item.pt_PT || '',
                    'it_IT': item.it_IT || '',
                    'ar_SA': item.ar_SA || '',
                    'ja_JP': item.ja_JP || '',
                    'ko_KR': item.ko_KR || '',
                    'pl_PL': item.pl_PL || '',
                    'th_TH': item.th_TH || ''
                };
                data.push(row);
            });

            const ws = XLSX.utils.json_to_sheet(data, { header: headers });
            const wb = XLSX.utils.book_new();
            XLSX.utils.book_append_sheet(wb, ws, "I18n Config");
            XLSX.writeFile(wb, "AEKE_I18n_Config.xlsx");
        } catch (e) {
            console.error("Export failed:", e);
            alert("导出失败，请查看控制台日志。");
        }
    }
};
