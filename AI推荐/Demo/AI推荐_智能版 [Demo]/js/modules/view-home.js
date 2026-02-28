// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\modules\view-home.js

window.ViewHome = {
    // ... (Keep FIELD_DESCRIPTIONS)
    FIELD_DESCRIPTIONS: {
        gender: 'desc_gender',
        dob: 'desc_dob',
        height: 'desc_height',
        weight: 'desc_weight',
        bmi: 'desc_bmi',
        rhr: 'desc_rhr',
        mhr: 'desc_mhr',
        fatigue: 'desc_fatigue',
        level: 'desc_level',
        duration: 'desc_duration',
        pain: 'desc_pain',
        missing: 'desc_missing',
        days: 'desc_days',
        style: 'desc_style',
        goal: 'desc_goal',
        funcGoal: 'desc_funcGoal',
        bodyType: 'desc_bodyType',
        targetWeight: 'desc_targetWeight'
    },

    startSession: () => {
        const btn = document.getElementById('home-start-btn');
        if(btn) btn.style.display = 'none';
        
        const content = document.getElementById('home-active-content');
        if(content) content.classList.remove('hidden');
        
        const profile = document.getElementById('profile-card');
        if(profile) profile.classList.remove('hidden');

        App.renderProfile();

        try {
            Voice.init();
            Voice.startListening();
            setTimeout(() => {
                const greeting = window.I18n.t(TEXT_VARIANTS.greeting[Math.floor(Math.random() * TEXT_VARIANTS.greeting.length)]);
                Voice.speak(greeting);
            }, 500);
        } catch (e) {
            console.error("Voice Error:", e);
        }
    },

    openProfile: () => {
        document.getElementById('modal-profile').classList.add('active');
        App.renderProfileForm(); // Ensure form is rendered when opened
    },

    saveProfile: () => {
        App.renderProfile();
        document.getElementById('modal-profile').classList.remove('active');
    },

    renderProfile: () => {
        const u = window.store.user;
        const toEn = (val) => (window.CONSTANTS && window.CONSTANTS.CN_TO_EN && window.CONSTANTS.CN_TO_EN[val]) ? window.CONSTANTS.CN_TO_EN[val] : val;
        try {
            // Use ViewHome.getFatigueInfo directly to be safe
            const fInfo = window.ViewHome.getFatigueInfo(u.fatigue);
            
            let levelText = 'Beginner';
            if (['L3', 'L4'].includes(u.level)) levelText = 'Intermediate';
            if (u.level === 'L5') levelText = 'Advanced';

            const redDot = !u.funcGoal ? '<div class="red-dot"></div>' : '';

            const html = `
                <div class="info-item"><div class="info-label">${window.I18n.t('profile_label_goal')}</div><div class="info-val">${window.I18n.t('enum_' + toEn(u.goal))}</div></div>
                <div class="info-item"><div class="info-label">${window.I18n.t('profile_label_level')}</div><div class="info-val">${window.I18n.t('enum_' + levelText)}</div></div>
                <div class="info-item"><div class="info-label">${window.I18n.t('profile_label_weight')}</div><div class="info-val">${u.weight} kg</div></div>
                <div class="info-item"><div class="info-label">${window.I18n.t('profile_label_fatigue')}</div><div class="info-val">${u.fatigue} - ${window.I18n.t('enum_' + fInfo.label)}</div></div>
            `;
            const display = document.getElementById('profile-display');
            if (display) display.innerHTML = html;
            
            const editBtn = document.querySelector('.edit-btn');
            if (editBtn) editBtn.innerHTML = `${window.I18n.t('home_profile_update')}${redDot}`;
        } catch (e) {
            console.error("Render Profile Error:", e);
        }
    },
    
    getFatigueInfo: (val) => {
        // Use CONFIG.STATUS_CONFIG if available, else fallback
        const config = CONFIG.STATUS_CONFIG || [];
        const status = config.find(s => val * 10 >= s.range[0] && val * 10 <= s.range[1]);
        if (status) {
            let color = '#32C48C';
            if (status.label === 'Fatigued') color = '#FFC107';
            if (status.label === 'Exhausted') color = '#FF5252';
            return { label: status.label, desc: window.I18n.t('status_desc_template').replace('{i}', status.intensity).replace('{v}', status.volume), color: color };
        }
        return { label: 'Unknown', desc: '', color: '#888' };
    },
    
    updateFatigueDisplay: (val) => {
        const info = window.ViewHome.getFatigueInfo(val);
        const valEl = document.getElementById('fatigue-val');
        const descEl = document.getElementById('fatigue-desc');
        if(valEl) {
            valEl.innerText = `${val} - ${window.I18n.t('enum_' + info.label)}`;
            valEl.style.color = info.color;
        }
        if(descEl) descEl.innerText = info.desc;
        
        const slider = document.getElementById('in-fatigue');
        if(slider) {
            const percentage = ((val - 1) / 9) * 100;
            slider.style.background = `linear-gradient(to right, ${info.color} 0%, ${info.color} ${percentage}%, #333 ${percentage}%, #333 100%)`;
        }
    },

    renderProfileForm: () => {
        const u = window.store.user; 
        const activeTab = window.store.activeTab || 'basic';
        const toEn = (val) => (window.CONSTANTS && window.CONSTANTS.CN_TO_EN && window.CONSTANTS.CN_TO_EN[val]) ? window.CONSTANTS.CN_TO_EN[val] : val;
        const opts = (arr, val) => arr.map(o => `<option value="${o}" ${o===toEn(val)?'selected':''}>${window.I18n.t('enum_' + o)}</option>`).join('');
        const fInfo = window.ViewHome.getFatigueInfo(u.fatigue);
        
        const age = new Date().getFullYear() - new Date(u.dob).getFullYear();
        const bmi = (u.weight / ((u.height/100)**2)).toFixed(1);
        const mhr = Math.round(208 - 0.7 * age);
        
        const hasRedDot = !u.funcGoal;

        const label = (text, key) => {
            const desc = window.I18n.t(ViewHome.FIELD_DESCRIPTIONS[key]) || '';
            return `<label class="form-label">${window.I18n.t(text)} <span class="help-icon" onclick="App.toggleTooltip(event, '${key}')">?<div class="field-tooltip" id="tooltip-${key}">${desc}</div></span></label>`;
        };

        const fatigueHtml = `
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label" style="display:flex;justify-content:space-between;">
                    <span style="display:flex;align-items:center;">${window.I18n.t('profile_label_fatigue')} (1-10) <span class="help-icon" onclick="App.toggleTooltip(event, 'fatigue')">?<div class="field-tooltip" id="tooltip-fatigue">${ViewHome.FIELD_DESCRIPTIONS.fatigue}</div></span></span>
                    <span style="display:flex;align-items:center;">${window.I18n.t('profile_label_fatigue')} (1-10) <span class="help-icon" onclick="App.toggleTooltip(event, 'fatigue')">?<div class="field-tooltip" id="tooltip-fatigue">${window.I18n.t(ViewHome.FIELD_DESCRIPTIONS.fatigue)}</div></span></span>
                    <span id="fatigue-val" style="color:${fInfo.color}">${u.fatigue} - ${window.I18n.t('enum_' + fInfo.label)}</span>
                </label>
                <input type="range" id="in-fatigue" min="1" max="10" class="form-input" value="${u.fatigue}" style="height:6px; padding:0; -webkit-appearance:none; background:#333; border-radius:3px;" oninput="window.store.user.fatigue=this.value; App.updateFatigueDisplay(this.value)">
                <div id="fatigue-desc" style="font-size:11px; color:#888; margin-top:12px; padding:10px; background:rgba(255,255,255,0.05); border-radius:6px; line-height:1.4;">${fInfo.desc}</div>
            </div>
        `;
        document.getElementById('profile-fatigue-container').innerHTML = fatigueHtml;
        setTimeout(() => App.updateFatigueDisplay(u.fatigue), 0);

        const tabsContainer = document.querySelector('#modal-profile .tabs');
        if (tabsContainer) {
            const goalDot = hasRedDot ? '<div class="red-dot"></div>' : '';
            tabsContainer.innerHTML = `
                <div class="tab ${activeTab==='basic'?'active':''}" onclick="App.switchTab('basic')">${window.I18n.t('profile_tab_basic')}</div>
                <div class="tab ${activeTab==='pref'?'active':''}" onclick="App.switchTab('pref')">${window.I18n.t('profile_tab_pref')}</div>
                <div class="tab ${activeTab==='goal'?'active':''}" onclick="App.switchTab('goal')">${window.I18n.t('profile_tab_goal')}${goalDot}</div>
            `;
        }
        
        const basicHtml = `
            <div class="tab-content ${activeTab==='basic'?'active':''}" id="tab-basic">
                <div class="form-group">${label('profile_field_gender', 'gender')}<select id="in-gender" class="form-input" onchange="window.store.user.gender=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.GENDER, u.gender)}</select></div>
                <div class="form-group">${label('profile_field_dob', 'dob')}<input type="date" id="in-dob" class="form-input" value="${u.dob}" onchange="window.store.user.dob=this.value; App.renderProfileForm()"></div>
                <div class="form-group">${label('profile_field_height', 'height')}<input type="number" id="in-height" class="form-input" value="${u.height}" onchange="window.store.user.height=parseFloat(this.value); App.renderProfileForm()"></div>
                <div class="form-group">${label('profile_field_weight', 'weight')}<input type="number" id="in-weight" class="form-input" value="${u.weight}" onchange="window.store.user.weight=parseFloat(this.value); App.renderProfileForm()"></div>
                
                <div class="form-group" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">
                    <div>${label('BMI', 'bmi')}<div id="d-bmi" style="font-weight:700; color:${bmi>24?'var(--danger)':'#fff'}">${bmi}</div></div>
                    <div>${label('profile_field_rhr', 'rhr')}<div id="in-rhr" style="font-weight:700;">${u.rhr||60}</div></div>
                    <div>${label('profile_field_mhr', 'mhr')}<div id="d-mhr" style="font-weight:700;">${mhr}</div></div>
                </div>
            </div>
        `;

        const prefHtml = `
            <div class="tab-content ${activeTab==='pref'?'active':''}" id="tab-pref">
                <div class="form-group">${label('profile_label_level', 'level')}<select id="in-level" class="form-input" onchange="window.store.user.level=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.LEVEL, u.level)}</select></div>
                <div class="form-group">${label('profile_field_duration', 'duration')}<input type="number" id="in-duration" class="form-input" value="${u.duration}" onchange="window.store.user.duration=parseInt(this.value); App.renderProfileForm()"></div>
                <div class="form-group">
                    ${label('profile_field_days', 'days')}
                    <div class="options-grid" id="pref-days" style="gap:8px;">
                        ${CONSTANTS.WEEKDAYS.map(d => {
                            const isSel = u.days.includes(d);
                            const dayKey = 'enum_' + d;
                            return `<div class="opt-chip ${isSel?'active':''}" onclick="App.toggleArrayItem('days', '${d}')" style="padding:8px;min-width:40px;flex-direction:column;gap:2px;height:auto;">
                                <span>${window.I18n.t(dayKey)}</span>
                                <span style="font-size:9px;opacity:0.6;font-weight:normal;">${isSel?window.I18n.t('common_status_train'):window.I18n.t('common_status_rest')}</span>
                            </div>`
                        }).join('')}
                    </div>
                </div>
                <div class="form-group">
                    ${label('profile_field_pain', 'pain')}
                    <div class="options-grid" id="pref-pain" style="gap:8px;">
                        ${CONSTANTS.ENUMS.PAIN_AREAS.map(p => `<div class="opt-chip ${u.pain.includes(p)?'active':''}" onclick="App.toggleArrayItem('pain', '${p}')" style="padding:8px;min-width:40px;">${window.I18n.t('enum_' + p)}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group">
                    ${label('profile_field_missing', 'missing')}
                    <div class="options-grid" id="pref-missing" style="gap:8px;">
                        ${CONSTANTS.ENUMS.MISSING_ACCESSORIES.map(m => `<div class="opt-chip ${u.missing.includes(m)?'active':''}" onclick="App.toggleArrayItem('missing', '${m}')" style="padding:8px;min-width:40px;">${window.I18n.t('enum_' + m)}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group">${label('profile_field_style', 'style')}<select id="in-style" class="form-input" onchange="window.store.user.style=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.STYLE, u.style)}</select></div>
            </div>
        `;
        
        const funcGoalDot = hasRedDot ? '<div class="red-dot"></div>' : '';
        
        const goalHtml = `
            <div class="tab-content ${activeTab==='goal'?'active':''}" id="tab-goal">
                <div class="form-group">${label('profile_label_goal', 'goal')}<select id="in-goal" class="form-input" onchange="window.store.user.goal=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.GOAL, u.goal)}</select></div>
                <div class="form-group">${label(`profile_field_func_goal`, 'funcGoal')}${funcGoalDot}<select id="in-func-goal" class="form-input" onchange="window.store.user.funcGoal=this.value; App.renderProfileForm()"><option value="" disabled ${!u.funcGoal?'selected':''}>${window.I18n.t('chat_msg_select_one')}</option>${opts(CONSTANTS.ENUMS.FUNC_GOAL, u.funcGoal)}</select></div>
                <div class="form-group">${label('profile_field_body_type', 'bodyType')}<select id="in-body-type" class="form-input" onchange="window.store.user.bodyType=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.BODY_TYPE, u.bodyType)}</select></div>
                <div class="form-group">${label('profile_field_target_weight', 'targetWeight')}<input type="number" id="in-target-weight" class="form-input" value="${u.targetWeight}" onchange="window.store.user.targetWeight=parseFloat(this.value); App.renderProfileForm()"></div>
            </div>
        `;

        document.getElementById('profile-form').innerHTML = basicHtml + prefHtml + goalHtml;
    },
    
    switchTab: (tabId) => {
        window.store.activeTab = tabId;
        App.renderProfileForm(); 
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        const map = {'basic':0, 'pref':1, 'goal':2};
        document.querySelectorAll('.tab')[map[tabId]].classList.add('active');
    },

    toggleArrayItem: (key, val) => {
        const arr = window.store.user[key];
        const idx = arr.indexOf(val);
        if(idx > -1) arr.splice(idx, 1);
        else arr.push(val);
        App.renderProfileForm();
    },

    startFlow: (type) => {
        if (!window.store.user.funcGoal) {
            App.showToast(window.I18n.t('toast_update_profile'));
            App.openProfile();
            App.switchTab('goal');
            return;
        }
        
        window.store.flow = type;
        window.store.step = 0;
        window.store.inputs = {};
        
        document.getElementById('profile-card').classList.add('hidden');
        
        setTimeout(() => {
            App.switchView('view-chat');
            document.getElementById('app').classList.add('state-chat');
            App.nextStep();
        }, 400);
    },

    toggleTooltip: (e, key) => {
        e.stopPropagation();
        
        const tip = document.getElementById(`tooltip-${key}`);
        const isVisible = tip && tip.classList.contains('active');
        
        App.closeTooltips();
        
        if(!isVisible && tip) {
            const icon = e.currentTarget;
            const rect = icon.getBoundingClientRect();
            
            tip.style.position = 'fixed';
            tip.style.left = (rect.left + rect.width / 2) + 'px';
            tip.style.bottom = 'auto'; // Reset CSS bottom property to prevent conflict
            tip.style.zIndex = '1000';
            
            if (rect.top < 150) {
                tip.style.top = (rect.bottom + 8) + 'px';
                tip.style.transform = 'translate(-50%, 0)';
            } else {
                tip.style.top = (rect.top - 8) + 'px';
                tip.style.transform = 'translate(-50%, -100%)';
            }
            tip.classList.add('active');
        }
    },

    closeTooltips: () => {
        document.querySelectorAll('.field-tooltip').forEach(el => el.classList.remove('active'));
    }
};
