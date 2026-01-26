// e:\AI-Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\app.js

const App = {
    // Mixin all modules
    ...window.UIUtils,
    ...window.ViewHome,
    ...window.ViewChat,
    ...window.ViewReasoning,
    ...window.ViewResult,
    ...window.ViewLibrary,

    init: () => {
        // [NEW] Load Dynamic Config from Ops Backend
        try {
            const dynamicConfig = localStorage.getItem('AEKE_AI_CONFIG');
            if (dynamicConfig) {
                const parsed = JSON.parse(dynamicConfig);
                // Deep merge or overwrite CONFIG
                Object.assign(window.CONFIG, parsed);
                console.log('[App] Loaded dynamic AI configuration from Ops Backend.');
            }
        } catch (e) {
            console.warn('[App] Failed to load dynamic config:', e);
        }

        window.UserAbility.init();
        App.renderProfile();
        // Ensure renderProfileForm is available from ViewHome
        if (App.renderProfileForm) App.renderProfileForm();
        App.initChatScroll();
        
        // Force bind click event to ensure it works
        const btn = document.getElementById('home-start-btn');
        if(btn) btn.onclick = App.startSession;

        // Global click to close tooltips
        document.addEventListener('click', (e) => {
            if(App.closeTooltips) App.closeTooltips();
        });
    },
    
    startCustomFlow: () => {
        window.ViewResult.startCustomFlow();
    },

    saveTemplate: () => {
        window.ViewResult.saveTemplate();
    }
};

window.App = App;
App.init();
