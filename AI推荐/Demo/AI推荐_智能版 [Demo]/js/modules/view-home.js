// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\modules\view-home.js

window.ViewHome = {
    // ... (Keep FIELD_DESCRIPTIONS)
    FIELD_DESCRIPTIONS: {
        gender: '生理特征，影响代谢公式',
        dob: '自动计算年龄并保持更新',
        height: '体态参数，单位为cm',
        weight: '计算BMI及运动卡路里消耗的基础参数',
        bmi: '动作“冲击等级”规避',
        rhr: '评估心肺能力、计算储备心率（体测后自动更新）',
        mhr: '定义训练强度区间',
        fatigue: '修正当日训练负荷',
        level: '能力评级，决定推荐难度',
        duration: '生成课程的默认时长',
        pain: '动作“疼痛部位”规避',
        missing: '动作“动作配件”规避',
        days: '确认全局训练日和休息日，用于计划日程配置',
        style: '体验偏好，如传统或激进',
        goal: '宏观目标，用于粗粒度筛选',
        funcGoal: '微观目标，用于精准匹配',
        bodyType: '用于运动计划推荐',
        targetWeight: '用于运动计划推荐'
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
                const greeting = TEXT_VARIANTS.greeting[Math.floor(Math.random() * TEXT_VARIANTS.greeting.length)];
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
        try {
            const fInfo = App.getFatigueInfo(u.fatigue);
            
            let levelText = '初级';
            if (['L3', 'L4'].includes(u.level)) levelText = '中级';
            if (u.level === 'L5') levelText = '高级';

            const redDot = !u.funcGoal ? '<div class="red-dot"></div>' : '';

            const html = `
                <div class="info-item"><div class="info-label">主要目标</div><div class="info-val">${u.goal}</div></div>
                <div class="info-item"><div class="info-label">运动等级</div><div class="info-val">${levelText}</div></div>
                <div class="info-item"><div class="info-label">当前体重</div><div class="info-val">${u.weight} kg</div></div>
                <div class="info-item"><div class="info-label">主观疲劳度</div><div class="info-val">${u.fatigue} - ${fInfo.label}</div></div>
            `;
            const display = document.getElementById('profile-display');
            if (display) display.innerHTML = html;
            
            const editBtn = document.querySelector('.edit-btn');
            if (editBtn) editBtn.innerHTML = `更新 >${redDot}`;
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
            if (status.label.includes('疲劳')) color = '#FFC107';
            if (status.label.includes('力竭')) color = '#FF5252';
            return { label: status.label, desc: `强度系数:${status.intensity}, 容量系数:${status.volume}`, color: color };
        }
        return { label: '未知', desc: '', color: '#888' };
    },
    
    updateFatigueDisplay: (val) => {
        const info = App.getFatigueInfo(val);
        const valEl = document.getElementById('fatigue-val');
        const descEl = document.getElementById('fatigue-desc');
        if(valEl) {
            valEl.innerText = `${val} - ${info.label}`;
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
        const opts = (arr, val) => arr.map(o => `<option ${o===val?'selected':''}>${o}</option>`).join('');
        const fInfo = App.getFatigueInfo(u.fatigue);
        
        const age = new Date().getFullYear() - new Date(u.dob).getFullYear();
        const bmi = (u.weight / ((u.height/100)**2)).toFixed(1);
        const mhr = Math.round(208 - 0.7 * age);
        
        const hasRedDot = !u.funcGoal;

        const label = (text, key) => {
            const desc = ViewHome.FIELD_DESCRIPTIONS[key] || '';
            return `<label class="form-label">${text} <span class="help-icon" onclick="App.toggleTooltip(event, '${key}')">?<div class="field-tooltip" id="tooltip-${key}">${desc}</div></span></label>`;
        };

        const fatigueHtml = `
            <div class="form-group" style="margin-bottom:0;">
                <label class="form-label" style="display:flex;justify-content:space-between;">
                    <span style="display:flex;align-items:center;">主观疲劳 (1-10) <span class="help-icon" onclick="App.toggleTooltip(event, 'fatigue')">?<div class="field-tooltip" id="tooltip-fatigue">${ViewHome.FIELD_DESCRIPTIONS.fatigue}</div></span></span>
                    <span id="fatigue-val" style="color:${fInfo.color}">${u.fatigue} - ${fInfo.label}</span>
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
                <div class="tab ${activeTab==='basic'?'active':''}" onclick="App.switchTab('basic')">基础</div>
                <div class="tab ${activeTab==='pref'?'active':''}" onclick="App.switchTab('pref')">偏好</div>
                <div class="tab ${activeTab==='goal'?'active':''}" onclick="App.switchTab('goal')">目标${goalDot}</div>
            `;
        }
        
        const basicHtml = `
            <div class="tab-content ${activeTab==='basic'?'active':''}" id="tab-basic">
                <div class="form-group">${label('性别', 'gender')}<select id="in-gender" class="form-input" onchange="window.store.user.gender=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.GENDER, u.gender)}</select></div>
                <div class="form-group">${label('生日', 'dob')}<input type="date" id="in-dob" class="form-input" value="${u.dob}" onchange="window.store.user.dob=this.value; App.renderProfileForm()"></div>
                <div class="form-group">${label('身高 (cm)', 'height')}<input type="number" id="in-height" class="form-input" value="${u.height}" onchange="window.store.user.height=parseFloat(this.value); App.renderProfileForm()"></div>
                <div class="form-group">${label('体重 (kg)', 'weight')}<input type="number" id="in-weight" class="form-input" value="${u.weight}" onchange="window.store.user.weight=parseFloat(this.value); App.renderProfileForm()"></div>
                
                <div class="form-group" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">
                    <div>${label('BMI', 'bmi')}<div style="font-weight:700; color:${bmi>24?'var(--danger)':'#fff'}">${bmi}</div></div>
                    <div>${label('静息心率', 'rhr')}<div style="font-weight:700;">${u.rhr||60}</div></div>
                    <div>${label('最大心率', 'mhr')}<div style="font-weight:700;">${mhr}</div></div>
                </div>
            </div>
        `;

        const prefHtml = `
            <div class="tab-content ${activeTab==='pref'?'active':''}" id="tab-pref">
                <div class="form-group">${label('运动等级', 'level')}<select id="in-level" class="form-input" onchange="window.store.user.level=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.LEVEL, u.level)}</select></div>
                <div class="form-group">${label('每日运动时长 (min)', 'duration')}<input type="number" class="form-input" value="${u.duration}" onchange="window.store.user.duration=parseInt(this.value); App.renderProfileForm()"></div>
                <div class="form-group">
                    ${label('每周训练日', 'days')}
                    <div class="options-grid" id="pref-days" style="gap:8px;">
                        ${CONSTANTS.WEEKDAYS.map(d => {
                            const isSel = u.days.includes(d);
                            return `<div class="opt-chip ${isSel?'active':''}" onclick="App.toggleArrayItem('days', '${d}')" style="padding:8px;min-width:40px;flex-direction:column;gap:2px;height:auto;">
                                <span>${d}</span>
                                <span style="font-size:9px;opacity:0.6;font-weight:normal;">${isSel?'训练':'休息'}</span>
                            </div>`
                        }).join('')}
                    </div>
                </div>
                <div class="form-group">
                    ${label('疼痛部位', 'pain')}
                    <div class="options-grid" id="pref-pain" style="gap:8px;">
                        ${CONSTANTS.ENUMS.PAIN_AREAS.map(p => `<div class="opt-chip ${u.pain.includes(p)?'active':''}" onclick="App.toggleArrayItem('pain', '${p}')" style="padding:8px;min-width:40px;">${p}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group">
                    ${label('缺失配件', 'missing')}
                    <div class="options-grid" id="pref-missing" style="gap:8px;">
                        ${CONSTANTS.ENUMS.MISSING_ACCESSORIES.map(m => `<div class="opt-chip ${u.missing.includes(m)?'active':''}" onclick="App.toggleArrayItem('missing', '${m}')" style="padding:8px;min-width:40px;">${m}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group">${label('喜欢的训练风格', 'style')}<select class="form-input" onchange="window.store.user.style=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.STYLE, u.style)}</select></div>
            </div>
        `;
        
        const funcGoalDot = hasRedDot ? '<div class="red-dot"></div>' : '';
        
        const goalHtml = `
            <div class="tab-content ${activeTab==='goal'?'active':''}" id="tab-goal">
                <div class="form-group">${label('主要目标', 'goal')}<select id="in-goal" class="form-input" onchange="window.store.user.goal=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.GOAL, u.goal)}</select></div>
                <div class="form-group">${label(`功能目标${funcGoalDot}`, 'funcGoal')}<select id="in-func-goal" class="form-input" onchange="window.store.user.funcGoal=this.value; App.renderProfileForm()"><option value="" disabled ${!u.funcGoal?'selected':''}>请选择</option>${opts(CONSTANTS.ENUMS.FUNC_GOAL, u.funcGoal)}</select></div>
                <div class="form-group">${label('目标体型', 'bodyType')}<select id="in-body-type" class="form-input" onchange="window.store.user.bodyType=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.BODY_TYPE, u.bodyType)}</select></div>
                <div class="form-group">${label('目标体重 (kg)', 'targetWeight')}<input type="number" id="in-target-weight" class="form-input" value="${u.targetWeight}" onchange="window.store.user.targetWeight=parseFloat(this.value); App.renderProfileForm()"></div>
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
            App.showToast('请更新运动档案');
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
        App.closeTooltips();
        const tip = document.getElementById(`tooltip-${key}`);
        if(tip) tip.classList.add('active');
    },

    closeTooltips: () => {
        document.querySelectorAll('.field-tooltip').forEach(el => el.classList.remove('active'));
    }
};
