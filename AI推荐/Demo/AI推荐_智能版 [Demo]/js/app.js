const App = {
    // Mixin all modules
    ...window.UIUtils,
    ...window.ViewHome,
    ...window.ViewChat,
    ...window.ViewReasoning,
    ...window.ViewResult,
    ...window.ViewLibrary,

    init: () => {
        window.UserAbility.init();
        App.renderProfile();
        // Ensure renderProfileForm is available from ViewHome
        if (App.renderProfileForm) App.renderProfileForm();
        App.initChatScroll();
        
        // Force bind click event to ensure it works
        const btn = document.getElementById('home-start-btn');
        if(btn) btn.onclick = App.startSession;
    },
};

window.App = App;
App.init();