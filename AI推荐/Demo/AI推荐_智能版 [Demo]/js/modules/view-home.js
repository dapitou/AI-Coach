window.ViewHome = {
    startSession: () => {
        // 1. UI Update MUST happen immediately
        const btn = document.getElementById('home-start-btn');
        if(btn) btn.style.display = 'none'; // Hide immediately
        
        const content = document.getElementById('home-active-content');
        if(content) content.classList.remove('hidden');
        
        const profile = document.getElementById('profile-card');
        if(profile) profile.classList.remove('hidden');

        // 2. Synchronous Voice Activation (Critical for iOS/Android Permissions)
        try {
            Voice.init();
            Voice.startListening(); // Must be direct response to user gesture
            
            // Speak greeting after a tiny delay to allow mic to activate first
            setTimeout(() => {
                const greeting = TEXT_VARIANTS.greeting[Math.floor(Math.random() * TEXT_VARIANTS.greeting.length)];
                Voice.speak(greeting);
            }, 500);
        } catch (e) {
            console.error("Voice Error:", e);
            alert("语音服务启动异常，已切换至触控模式");
        }
    },

    openProfile: () => {
        document.getElementById('modal-profile').classList.add('active');
    },

    saveProfile: () => {
        App.renderProfile();
        document.getElementById('modal-profile').classList.remove('active');
    },

    renderProfile: () => {
        const u = window.store.user;
        const fInfo = App.getFatigueInfo(u.fatigue);
        const html = `
            <div class="info-item"><div class="info-label">主要目标</div><div class="info-val" style="color:var(--primary)">${u.goal}</div></div>
            <div class="info-item"><div class="info-label">运动等级</div><div class="info-val">${u.level}</div></div>
            <div class="info-item"><div class="info-label">当前体重</div><div class="info-val">${u.weight} kg</div></div>
            <div class="info-item"><div class="info-label">主观疲劳度</div><div class="info-val" style="color:${fInfo.color}">${u.fatigue} - ${fInfo.label}</div></div>
        `;
        document.getElementById('profile-display').innerHTML = html;
    },
    
    getFatigueInfo: (val) => {
        if (val <= 2) return { label: '超量恢复', desc: '神经系统与肌糖原完全填充，适合冲击 PR (1RM) 或高强度爆发力训练。', color: '#32C48C' };
        if (val <= 4) return { label: '完全恢复', desc: '身体机能处于基准水平，适合进行常规容量的抗阻或代谢训练。', color: '#32C48C' };
        if (val <= 6) return { label: '功能性疲劳', desc: '存在轻微 DOMS 或神经疲劳，建议维持中等强度，避免力竭组。', color: '#FFC107' };
        if (val <= 8) return { label: '非功能性疲劳', desc: '显著的肌肉酸痛或心率变异性 (HRV) 下降，建议执行减载周 (Deload) 或主动恢复。', color: '#FF9800' };
        return { label: '过度训练', desc: '极度疲劳、免疫力下降或有伤痛风险，必须完全休息。', color: '#FF5252' };
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
    },

    renderProfileForm: () => {
        const u = window.store.user; 
        const activeTab = window.store.activeTab || 'basic';
        const opts = (arr, val) => arr.map(o => `<option ${o===val?'selected':''}>${o}</option>`).join('');
        const fInfo = App.getFatigueInfo(u.fatigue);
        
        const age = new Date().getFullYear() - new Date(u.dob).getFullYear();
        const bmi = (u.weight / ((u.height/100)**2)).toFixed(1);
        const mhr = Math.round(208 - 0.7 * age);
        
        const basicHtml = `
            <div class="tab-content ${activeTab==='basic'?'active':''}" id="tab-basic">
                <div class="form-group"><label class="form-label">性别</label><select id="in-gender" class="form-input" onchange="window.store.user.gender=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.GENDER, u.gender)}</select></div>
                <div class="form-group"><label class="form-label">生日</label><input type="date" id="in-dob" class="form-input" value="${u.dob}" onchange="window.store.user.dob=this.value; App.renderProfileForm()"></div>
                <div class="form-group"><label class="form-label">身高 (cm)</label><input type="number" id="in-height" class="form-input" value="${u.height}" onchange="window.store.user.height=parseFloat(this.value); App.renderProfileForm()"></div>
                <div class="form-group"><label class="form-label">体重 (kg)</label><input type="number" id="in-weight" class="form-input" value="${u.weight}" onchange="window.store.user.weight=parseFloat(this.value); App.renderProfileForm()"></div>
                
                <div class="form-group" style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px; background:rgba(255,255,255,0.05); padding:10px; border-radius:8px;">
                    <div><label class="form-label" style="font-size:10px;">BMI</label><div style="font-weight:700; color:${bmi>24?'var(--danger)':'#fff'}">${bmi}</div></div>
                    <div><label class="form-label" style="font-size:10px;">静息心率</label><input type="number" id="in-rhr" value="${u.rhr||60}" style="width:100%;background:transparent;border:none;border-bottom:1px solid #444;color:#fff;font-weight:700;padding:0;" onchange="window.store.user.rhr=this.value"></div>
                    <div><label class="form-label" style="font-size:10px;">最大心率</label><div style="font-weight:700;">${mhr}</div></div>
                </div>

                <div class="form-group">
                    <label class="form-label" style="display:flex;justify-content:space-between;">
                        <span>主观疲劳 (1-10)</span>
                        <span id="fatigue-val" style="color:${fInfo.color}">${u.fatigue} - ${fInfo.label}</span>
                    </label>
                    <input type="range" id="in-fatigue" min="1" max="10" class="form-input" value="${u.fatigue}" oninput="window.store.user.fatigue=this.value; App.updateFatigueDisplay(this.value)">
                    <div id="fatigue-desc" style="font-size:11px; color:#888; margin-top:8px; padding:8px; background:rgba(255,255,255,0.05); border-radius:4px;">${fInfo.desc}</div>
                </div>
            </div>
        `;
        
        const prefHtml = `
            <div class="tab-content ${activeTab==='pref'?'active':''}" id="tab-pref">
                <div class="form-group"><label class="form-label">运动等级</label><select id="in-level" class="form-input" onchange="window.store.user.level=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.LEVEL, u.level)}</select></div>
                <div class="form-group"><label class="form-label">每日运动时长 (min)</label><input type="number" class="form-input" value="${u.duration}" onchange="window.store.user.duration=parseInt(this.value); App.renderProfileForm()"></div>
                <div class="form-group">
                    <label class="form-label">疼痛部位</label>
                    <div class="options-grid" id="pref-pain" style="gap:8px;">
                        ${CONSTANTS.ENUMS.PAIN_AREAS.map(p => `<div class="opt-chip ${u.pain.includes(p)?'active':''}" onclick="App.toggleArrayItem('pain', '${p}')" style="padding:8px;min-width:40px;">${p}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">缺失配件</label>
                    <div class="options-grid" id="pref-missing" style="gap:8px;">
                        ${CONSTANTS.ENUMS.MISSING_ACCESSORIES.map(m => `<div class="opt-chip ${u.missing.includes(m)?'active':''}" onclick="App.toggleArrayItem('missing', '${m}')" style="padding:8px;min-width:40px;">${m}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group">
                    <label class="form-label">每周训练日</label>
                    <div class="options-grid" id="pref-days" style="gap:8px;">
                        ${['周一','周二','周三','周四','周五','周六','周日'].map(d => `<div class="opt-chip ${u.days.includes(d)?'active':''}" onclick="App.toggleArrayItem('days', '${d}')" style="padding:8px;min-width:40px;">${d}</div>`).join('')}
                    </div>
                </div>
                <div class="form-group"><label class="form-label">喜欢的训练风格</label><select class="form-input" onchange="window.store.user.style=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.STYLE, u.style)}</select></div>
            </div>
        `;
        
        const goalHtml = `
            <div class="tab-content ${activeTab==='goal'?'active':''}" id="tab-goal">
                <div class="form-group"><label class="form-label">主要目标</label><select id="in-goal" class="form-input" onchange="window.store.user.goal=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.GOAL, u.goal)}</select></div>
                <div class="form-group"><label class="form-label">功能目标</label><select id="in-func-goal" class="form-input" onchange="window.store.user.funcGoal=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.FUNC_GOAL, u.funcGoal)}</select></div>
                <div class="form-group"><label class="form-label">目标体型</label><select id="in-body-type" class="form-input" onchange="window.store.user.bodyType=this.value; App.renderProfileForm()">${opts(CONSTANTS.ENUMS.BODY_TYPE, u.bodyType)}</select></div>
                <div class="form-group"><label class="form-label">目标体重 (kg)</label><input type="number" id="in-target-weight" class="form-input" value="${u.targetWeight}" onchange="window.store.user.targetWeight=parseFloat(this.value); App.renderProfileForm()"></div>
            </div>
        `;

        document.getElementById('profile-form').innerHTML = basicHtml + prefHtml + goalHtml;
    },
    
    switchTab: (tabId) => {
        window.store.activeTab = tabId;
        // Re-render form needs full implementation in renderProfileForm
        // For now, let's assume App.renderProfileForm is available or we use ViewHome.renderProfileForm
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
        if (!window.store.user.goal) return alert('请先完善运动档案');
        
        window.store.flow = type;
        window.store.step = 0;
        window.store.inputs = {};
        
        document.getElementById('profile-card').classList.add('hidden');
        
        setTimeout(() => {
            App.switchView('view-chat');
            document.getElementById('app').classList.add('state-chat');
            App.nextStep();
        }, 400);
    }
};