window.ViewReasoning = {
    startReasoning: () => {
        App.switchView('view-reasoning');
        document.getElementById('app').classList.add('state-reasoning');
        document.querySelector('.siri-container').classList.add('thinking');
        
        const user = window.store.user;
        const inputs = window.store.inputs;
        const flow = window.store.flow;
        const toEn = (val) => (window.CONSTANTS && window.CONSTANTS.CN_TO_EN && window.CONSTANTS.CN_TO_EN[val]) ? window.CONSTANTS.CN_TO_EN[val] : val;
        
        const logs = [];
        logs.push(`${window.I18n.t('reasoning_log_read')}: ${window.I18n.t('enum_' + toEn(user.gender))} / ${window.I18n.t('enum_' + user.level)} / ${window.I18n.t('enum_' + toEn(user.goal))}`);
        
        if (flow === 'course') {
            const targets = Array.isArray(inputs.targets) ? inputs.targets : [inputs.targets];
            const targetStr = targets.map(t => window.I18n.t('enum_' + toEn(t))).join('、');
            logs.push(`${window.I18n.t('reasoning_log_parse')}: ${window.I18n.t('enum_' + toEn(inputs.type))} / ${targetStr}`);
        } else {
            const daysCount = (inputs.days || []).length;
            logs.push(`${window.I18n.t('reasoning_log_parse')}: ${inputs.cycle} ${window.I18n.t('common_unit_week')} / ${daysCount} ${window.I18n.t('reasoning_log_freq')}`);
        }
        
        if (user.pain && user.pain.length) logs.push(`${window.I18n.t('reasoning_log_risk')}: ${window.I18n.t('reasoning_log_avoid')} ${user.pain.map(p => window.I18n.t('enum_' + toEn(p))).join('、')}`);
        else logs.push(`${window.I18n.t('reasoning_log_risk')}: ${window.I18n.t('reasoning_log_no_risk')}`);
        
        const stratObj = CONFIG.STRATEGY.find(s => s.target === toEn(user.goal));
        const stratName = stratObj ? stratObj.strategy : 'Recommended';
        logs.push(`${window.I18n.t('reasoning_log_strategy')}: ${window.I18n.t('enum_' + stratName)} ${window.I18n.t('reasoning_log_model')}`);
        
        logs.push(`${window.I18n.t('reasoning_log_build')}: ${window.I18n.t('reasoning_log_topk')}`);
        logs.push(`${window.I18n.t('reasoning_log_gen')}: ${window.I18n.t('reasoning_log_calc')}`);

        const logContainer = document.getElementById('reasoning-log');
        logContainer.innerHTML = '';
        
        let i = 0; 
        function nextLog() {
            if (i >= logs.length) {
                setTimeout(() => {
                    document.getElementById('app').classList.remove('state-reasoning');
                    document.querySelector('.siri-container').classList.remove('thinking');
                    App.showResult();
                }, 800);
                return;
            }
            const div = document.createElement('div');
            div.className = 'log-item';
            div.innerHTML = `<div class="log-icon"><div class="typing-dot" style="width:4px;height:4px;background:#fff;animation:none;opacity:0.5;"></div></div><span>${logs[i]}</span>`;
            logContainer.appendChild(div);
            if (i > 0) {
                const prev = logContainer.children[i-1];
                prev.classList.remove('active');
                prev.classList.add('done');
                prev.querySelector('.log-icon').innerHTML = '✓';
            }
            div.classList.add('active');
            i++;
            setTimeout(nextLog, 800);
        }
        nextLog();
    }
};