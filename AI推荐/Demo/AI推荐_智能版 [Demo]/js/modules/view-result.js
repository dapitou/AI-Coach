window.ViewResult = {
    startCustomFlow: () => {
        // Create Empty Context
        const ctx = {
            source: 'Custom',
            meta: {
                type: 'Custom',
                targets: [],
                duration: 0,
                level: window.store.user.level,
                goal: window.store.user.goal
            },
            phases: [
                { type: 'Warmup', duration: 0, actions: [], paradigm: 'Flow', strategy: { rest: 0, sets: 1, intensity: 0.4 } },
                { type: 'Main', duration: 0, actions: [], paradigm: 'Resistance', strategy: { rest: 60, restRound: 90, sets: 3, intensity: 0.75, loopMode: 'Regular' } },
                { type: 'Cooldown', duration: 0, actions: [], paradigm: 'Flow', strategy: { rest: 0, sets: 1, intensity: 0.3 } }
            ]
        };
        
        window.store.flow = 'custom';
        window.currentCtx = ctx;
        window.store.activePhaseIdx = 1; // Default to Main
        window.store.courseSettings = { loopMode: 'Regular', loadStrategy: 'Recommended' }; 

        App.showResult();
    },

    showResult: () => {
        const flow = window.store.flow;
        const inputs = window.store.inputs;
        const btnMain = document.getElementById('btn-main-action');
        
        // Reset UI State
        document.getElementById('btn-back-plan').style.display = 'none';
        document.getElementById('btn-close-result').style.display = 'block'; // Show close button on top level
        
        App.switchView('view-result');
        
        if (flow === 'course' || flow === 'custom') {
            document.getElementById('view-result').classList.add('plan-mode');
            btnMain.innerText = window.I18n.t('result_btn_start');
            btnMain.onclick = () => {
                window.ViewWorkout.start(window.currentCtx);
            };
            
            // UI Toggle
            document.getElementById('res-plan-list').style.display = 'none';
            document.getElementById('res-course-content').style.display = 'block';
            document.getElementById('unit-switch').style.display = 'block';

            let ctx = window.currentCtx;
            if (flow === 'course') {
                try {
                    ctx = window.Logic.genCourse(inputs);
                    window.store.courseSettings = { loopMode: 'Regular', loadStrategy: 'Recommended' };
                    window.currentCtx = ctx;
                } catch (e) {
                    console.error("Course Generation Failed:", e);
                    window.App.showToast(window.I18n.t('msg_gen_fail'));
                    return;
                }
                
                const mainIdx = ctx.phases.findIndex(p => p.type === 'Main');
                window.store.activePhaseIdx = mainIdx >= 0 ? mainIdx : 0;
            }

            App.recalculateDurations(ctx); // FIX: Recalculate durations before rendering UI to avoid "locked" 5min
            App.setupCourseResultUI(ctx, window.I18n.t('course_title_suffix', {type: window.I18n.t('enum_' + inputs.type)}));
            App.renderFineTuning(ctx);
            App.initResultScroll();
            
        } else {
            document.getElementById('view-result').classList.add('plan-mode');
            btnMain.innerText = window.I18n.t('result_btn_schedule');
            btnMain.onclick = () => App.openScheduleModal();
            
            // UI Toggle
            document.getElementById('res-plan-list').style.display = 'block';
            document.getElementById('res-course-content').style.display = 'none';
            document.getElementById('unit-switch').style.display = 'block';

            // Default to Linear Periodization internally
            const pModel = '线性周期';
            const plan = window.Logic.genPlan({ ...inputs, periodization: pModel });
            
            // 1. Plan Name: {Level} + {FuncGoal} + "计划"
            const u = window.store.user;
            const toEn = (val) => (window.CONSTANTS && window.CONSTANTS.CN_TO_EN && window.CONSTANTS.CN_TO_EN[val]) ? window.CONSTANTS.CN_TO_EN[val] : val;
            const levelMap = { 'L1':'Beginner', 'L2':'Beginner', 'L3':'Intermediate', 'L4':'Intermediate', 'L5':'Advanced' };
            const levelText = levelMap[u.level] || 'Beginner';
            const funcGoal = toEn(u.funcGoal) || toEn(u.goal) || 'Muscle Gain';
            
            // 3. Plan Intro
            const introMap = {
                'Muscle Gain': {
                    people: window.I18n.t('plan_intro_muscle_people'),
                    pain: window.I18n.t('plan_intro_muscle_pain'),
                    desc: window.I18n.t('plan_intro_muscle_desc'),
                    effect: window.I18n.t('plan_intro_muscle_effect')
                },
                'Weight Loss': {
                    people: window.I18n.t('plan_intro_weight_people'),
                    pain: window.I18n.t('plan_intro_weight_pain'),
                    desc: window.I18n.t('plan_intro_weight_desc'),
                    effect: window.I18n.t('plan_intro_weight_effect')
                },
                'Health': {
                    people: window.I18n.t('plan_intro_health_people'),
                    pain: window.I18n.t('plan_intro_health_pain'),
                    desc: window.I18n.t('plan_intro_health_desc'),
                    effect: window.I18n.t('plan_intro_health_effect')
                }
            };
            // Fallback to '增肌' if goal not found, or map based on main goal
            const mapKey = introMap[toEn(u.goal)] ? toEn(u.goal) : 'Muscle Gain';
            const curIntro = introMap[mapKey];
            
            const planHero = `
                <div class="plan-hero">
                    <div class="plan-hero-title">${window.I18n.t('enum_' + u.level)} ${window.I18n.t('enum_' + funcGoal)} ${window.I18n.t('plan_title_suffix')}</div>
                    <div class="plan-hero-tags">
                        <div class="ph-tag">${window.I18n.t('enum_' + u.level)}</div>
                        <div class="ph-tag">${inputs.cycle} ${window.I18n.t('common_unit_week')}</div>
                        <div class="ph-tag">${inputs.days.length} ${window.I18n.t('common_unit_week').replace('Wks', 'Days')}/Wk</div>
                    </div>
                    <div class="plan-hero-intro">
                        <div style="margin-bottom:4px"><b>${window.I18n.t('plan_intro_label_people')}</b>${curIntro ? curIntro.people : ''}</div>
                        <div style="margin-bottom:4px"><b>${window.I18n.t('plan_intro_label_pain')}</b>${curIntro ? curIntro.pain : ''}</div>
                        <div><b>${window.I18n.t('plan_intro_label_effect')}</b>${curIntro ? curIntro.effect : ''}</div>
                    </div>
                </div>`;
            
            const phases = {};
            const phaseOrder = [];
            plan.schedule.forEach(w => {
                if(!phases[w.phase]) {
                    phases[w.phase] = [];
                    phaseOrder.push(w.phase);
                }
                phases[w.phase].push(w);
            });
            window.store.planPhases = phases;
            window.store.phaseOrder = phaseOrder;

            // 1. Weight Prediction Chart
            const chartHtml = App.renderWeightChart();

            // 2. Top Section HTML (Tabs + Desc + Calendar)
            let topHtml = `<div class="plan-tabs-wrapper" style="padding-top:0;">`;
            
            topHtml += `<div class="plan-flow-container" style="padding:5px 24px 5px 24px; gap:4px;">`;
            phaseOrder.forEach((pName, idx) => {
                const weeks = phases[pName].length;
                const intensity = phases[pName][0].intensity;
                topHtml += `<div class="plan-flow-item ${idx===0?'active':''}" id="flow-item-${idx}" onclick="App.switchPlanPhase(${idx})" style="flex:${weeks}; min-width:0;">
                    <div style="font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${window.I18n.t('enum_' + pName)}</div>
                    <div style="font-size:9px; opacity:0.8;">${weeks} ${window.I18n.t('common_unit_week')} | ${intensity}</div>
                </div>`;
                if (idx < phaseOrder.length - 1) topHtml += `<div class="plan-flow-arrow" style="font-size:10px; color:#444;">→</div>`;
            });
            topHtml += `</div>`;

            topHtml += `<div id="plan-phase-desc-container" style="padding: 0 24px 5px 24px;"></div>`;

            topHtml += `
                <div class="plan-calendar-header">
                    <div>${window.I18n.t('common_weekday_Mon')}</div><div>${window.I18n.t('common_weekday_Tue')}</div><div>${window.I18n.t('common_weekday_Wed')}</div><div>${window.I18n.t('common_weekday_Thu')}</div><div>${window.I18n.t('common_weekday_Fri')}</div><div>${window.I18n.t('common_weekday_Sat')}</div><div>${window.I18n.t('common_weekday_Sun')}</div>
                </div>
            </div>`;

            let html = `
                <div class="plan-layout-container">
                    <div class="plan-static-top">
                        ${planHero}
                        ${chartHtml}
                        ${topHtml}
                    </div>
                    <div id="plan-schedule-container" class="plan-scroll-area"></div>
                </div>`;
            
            document.getElementById('res-plan-list').innerHTML = html;

            // Initial Render of Phase 0
            App.renderPlanPhaseContent(0);
            setTimeout(() => App.updateWeightChart(0), 50);
            App.switchPlanPhase(0); // Trigger desc update
        }
    },

    renderWeightChart: () => {
        const startW = window.store.user.weight;
        const targetW = window.store.user.targetWeight;
        const phases = window.store.planPhases;
        const order = window.store.phaseOrder;
        const unit = window.store.unit || 'kg';
        const isLbs = unit === 'lbs';
        const convert = (w) => isLbs ? Math.round(w * 2.20462) : w;
        
        if (!phases || !order) return '';

        const points = [];
        points.push({ x: 0, y: startW });

        let currentWeek = 0;
        const totalDelta = targetW - startW;
        
        // Phase weight simulation
        const phaseWeights = { 'Adaptation': 0.1, 'Progression': 0.3, 'Growth': 0.3, 'Peak': 0.4, 'Deload': 0.05, 'Recovery': 0.05 };
        let totalPhaseWeight = 0;
        
        order.forEach(pName => {
            let w = 0.2;
            for (const key in phaseWeights) if (pName.includes(key)) w = phaseWeights[key];
            totalPhaseWeight += w;
        });

        let accumulatedDelta = 0;
        order.forEach(pName => {
            const pWeeks = phases[pName].length;
            currentWeek += pWeeks;
            let w = 0.2;
            for (const key in phaseWeights) if (pName.includes(key)) w = phaseWeights[key];
            
            accumulatedDelta += totalDelta * (w / totalPhaseWeight);
            points.push({ x: currentWeek, y: parseFloat((startW + accumulatedDelta).toFixed(1)) });
        });
        // Fix last point
        points[points.length-1].y = targetW;

        const totalWeeks = currentWeek;
        const minW = Math.min(startW, targetW, ...points.map(p=>p.y)) - 0.5;
        const maxW = Math.max(startW, targetW, ...points.map(p=>p.y)) + 0.5;
        const range = maxW - minW || 1;
        
        const width = 100;
        const height = 25;
        const paddingX = 4;
        const paddingY = 6;
        
        // Use time-based mapping for X to align with proportional flow items
        const mapX = (w) => (w / totalWeeks) * (width - paddingX * 2) + paddingX;
        const mapY = (w) => height - paddingY - ((w - minW) / range) * (height - paddingY * 2);

        let pathD = `M ${mapX(points[0].x)} ${mapY(points[0].y)}`;
        points.slice(1).forEach((p) => pathD += ` L ${mapX(p.x)} ${mapY(p.y)}`);
        const fillD = pathD + ` L ${mapX(totalWeeks)} ${height} L ${mapX(0)} ${height} Z`;

        let linesHtml = '';
        for (let i = 0; i < points.length - 1; i++) {
            const p1 = points[i];
            const p2 = points[i+1];
            linesHtml += `<line id="chart-line-${i}" x1="${mapX(p1.x)}" y1="${mapY(p1.y)}" x2="${mapX(p2.x)}" y2="${mapY(p2.y)}" stroke="rgba(255,255,255,0.1)" stroke-width="1" stroke-linecap="round" style="transition:0.3s;" />`;
        }

        let dotsHtml = points.map((p, i) => {
            const displayVal = convert(p.y);
            return `<circle id="chart-dot-${i}" cx="${mapX(p.x)}" cy="${mapY(p.y)}" r="1.5" fill="rgba(255,255,255,0.3)" style="transition:0.3s;" />
                    <text id="chart-text-${i}" x="${mapX(p.x)}" y="${mapY(p.y) - 6}" font-size="2.5" fill="#888" text-anchor="middle" opacity="0.6" style="transition:0.3s;">${displayVal}<tspan font-size="0.7em" fill="#666" dx="1">${unit}</tspan></text>`;
        }).join('');

        return `
        <div id="plan-weight-chart-container" style="margin:0 24px 5px 24px; padding-top:5px;">
            <div style="font-size:10px; color:#666; margin-bottom:5px; display:flex; justify-content:space-between;">
                <span>${window.I18n.t('plan_chart_title')} (${unit})</span>
            </div>
            <svg viewBox="0 0 100 30" style="width:100%; overflow:visible;">
                <defs>
                    <linearGradient id="gradChart" x1="0%" y1="0%" x2="0%" y2="100%">
                        <stop offset="0%" style="stop-color:var(--primary);stop-opacity:0.2" />
                        <stop offset="100%" style="stop-color:var(--primary);stop-opacity:0" />
                    </linearGradient>
                </defs>
                <path d="${fillD}" fill="url(#gradChart)" />
                ${linesHtml}
                ${dotsHtml}
            </svg>
        </div>`;
    },

    updateWeightChart: (activeIdx) => {
        const total = window.store.phaseOrder.length;
        
        // Update Lines
        for(let i=0; i<total; i++) {
            const line = document.getElementById(`chart-line-${i}`);
            if(line) {
                const isActive = (i <= activeIdx);
                line.setAttribute('stroke', isActive ? '#269e70' : 'rgba(255,255,255,0.1)');
                line.setAttribute('stroke-width', isActive ? '1.5' : '1');
            }
        }
        
        // Update Dots
        for(let i=0; i<=total; i++) {
            const dot = document.getElementById(`chart-dot-${i}`);
            const text = document.getElementById(`chart-text-${i}`);
            if(dot && text) {
                // Highlight dots up to the target of current phase
                const isTarget = (i <= activeIdx + 1);
                
                dot.setAttribute('fill', isTarget ? 'var(--primary)' : 'rgba(255,255,255,0.3)');
                dot.setAttribute('r', isTarget ? '2' : '1.5');
                
                text.setAttribute('fill', isTarget ? '#fff' : '#888');
                text.setAttribute('font-weight', isTarget ? 'bold' : 'normal');
                text.setAttribute('opacity', isTarget ? '1' : '0.5');
                text.setAttribute('font-size', isTarget ? '3.5' : '2.5');
            }
        }
    },

    switchPlanPhase: (idx) => {
        window.store.activePlanPhaseIdx = idx;
        
        // Update Tabs UI
        const items = document.querySelectorAll('.plan-flow-item');
        items.forEach((el, i) => {
            if (i === idx) el.classList.add('active');
            else el.classList.remove('active');
        });

        // Update Description
        const pName = window.store.phaseOrder[idx];
        let pDesc = "";
        if (pName.includes("Adaptation")) pDesc = window.I18n.t('phase_desc_adaptation');
        else if (pName.includes("Progression")) pDesc = window.I18n.t('phase_desc_progression');
        else if (pName.includes("Peak")) pDesc = window.I18n.t('phase_desc_peak');
        else if (pName.includes("Deload") || pName.includes("Recovery")) pDesc = window.I18n.t('phase_desc_recover');
        
        const descContainer = document.getElementById('plan-phase-desc-container');
        if(descContainer) descContainer.innerHTML = `<div class="plan-phase-desc-static">${pDesc}</div>`;

        App.renderPlanPhaseContent(idx);
        App.updateWeightChart(idx);
    },

    renderPlanPhaseContent: (idx) => {
        const pName = window.store.phaseOrder[idx];
        const weeks = window.store.planPhases[pName];
        let html = '';

        html += `
        <div class="plan-phase-block" style="animation:fadeIn 0.3s; margin-top:10px;">
            ${weeks.map(w => App.renderPlanWeek(w)).join('')}
        </div>`;

        document.getElementById('plan-schedule-container').innerHTML = html;
    },

    renderPlanWeek: (w) => {
        let daysHtml = '';
        
        let phaseSuffix = "";
        if (w.phase.includes("Adaptation")) phaseSuffix = window.I18n.t('suffix_activation');
        else if (w.phase.includes("Progression")) phaseSuffix = window.I18n.t('suffix_growth');
        else if (w.phase.includes("Peak")) phaseSuffix = window.I18n.t('suffix_peak');
        else if (w.phase.includes("Deload") || w.phase.includes("Recovery")) phaseSuffix = window.I18n.t('suffix_recovery');
        else phaseSuffix = window.I18n.t('suffix_training');

        const level = window.store.user.level;

        w.days.forEach((day, idx) => {
            const d = idx + 1;
            const cls = day.isTraining ? 'training' : 'rest';
            const targetsStr = day.targets ? day.targets.join(',') : '';
            const click = day.isTraining ? `onclick="App.enterPlanDay(${w.week}, ${d}, '${day.dayName}', '${targetsStr}')"` : '';
            
            let content = '';
            if (day.isTraining) {
                let baseTitle = window.I18n.t('enum_' + day.title) || window.I18n.t(day.title) || day.title;
                
                content = `
                    <div class="pdc-title">${baseTitle}</div>
                    <div class="pdc-sub">${window.I18n.t('enum_' + level)}</div>
                `;
            } else {
                content = `<div class="pdc-title" style="font-weight:400; color:#888;">${window.I18n.t('common_status_rest')}</div>`;
            }

            daysHtml += `
            <div class="plan-day-cell ${cls}" ${click}>
                ${content}
            </div>`;
        });
        return `<div style="margin-bottom:10px;">
                    <div style="font-size:10px;color:#666;margin-bottom:4px;padding-left:4px;">${window.I18n.t('plan_week_num', {n: w.week})}</div>
                    <div class="plan-week-row">${daysHtml}</div>
                </div>`;
    },

    enterPlanDay: (week, day, dayName, targetsStr) => {
        const inputs = window.store.inputs;
        const targets = targetsStr.split(',');
        
        // 修复：从 store 中查找当前周的周期系数 (Cycle Coefficients)
        let pIntensity = 1.0;
        let pVolume = 1.0;
        if (window.store.planPhases) {
            const allWeeks = Object.values(window.store.planPhases).flat();
            const wData = allWeeks.find(w => w.week === week);
            if (wData) {
                pIntensity = wData.intensity || 1.0;
                pVolume = wData.volume || 1.0;
            }
        }

        const planContext = { type: 'Strength', targets: targets, duration: parseInt(inputs.duration), title: window.I18n.t('plan_day_title', {day: window.I18n.t('enum_' + dayName)}), phase: { intensity: pIntensity, volume: pVolume }, goal: window.store.user.goal };
        const ctx = window.Logic.runPipeline(null, planContext);
        const mainIdx = ctx.phases.findIndex(p => p.type === 'Main');
        window.store.activePhaseIdx = mainIdx >= 0 ? mainIdx : 0;
        window.store.courseSettings = { loopMode: 'Regular', loadStrategy: 'Recommended' };
        
        // Switch to Course View inside Result
        document.getElementById('view-result').classList.add('plan-mode');
        document.getElementById('res-plan-list').style.display = 'none';
        document.getElementById('res-course-content').style.display = 'block';
        document.getElementById('unit-switch').style.display = 'block';
        
        window.currentCtx = ctx;
        App.recalculateDurations(ctx); // FIX: Recalculate durations before rendering UI
        App.setupCourseResultUI(ctx, `W${week} | ${dayName}`);
        App.renderFineTuning(ctx);
        App.initResultScroll();
        document.getElementById('btn-close-result').style.display = 'none'; // Hide close, show back
        document.getElementById('btn-back-plan').style.display = 'block';
    },

    recalculateLoadStrategy: () => {
        if(!window.currentCtx) return;
        window.currentCtx = window.Logic.instantiate(window.currentCtx);
    },

    setupCourseResultUI: (ctx, title) => {
        const u = window.store.user;
        const isCustom = ctx.source === 'Custom';
        const toEn = (val) => (window.CONSTANTS && window.CONSTANTS.CN_TO_EN && window.CONSTANTS.CN_TO_EN[val]) ? window.CONSTANTS.CN_TO_EN[val] : val;
        
        let hero = '';
        if (isCustom) {
            hero = `
            <div class="plan-hero" style="padding-top:60px; padding-bottom:0;">
                <div class="plan-hero-title" style="display:flex; align-items:center; gap:8px;" onclick="App.expandHeader()">
                    <span id="custom-course-title" contenteditable="true" style="border-bottom:1px dashed rgba(255,255,255,0.3); outline:none;" onblur="window.currentCtx.meta.title = this.innerText">${window.I18n.t('result_title_custom')}</span>
                    <i style="font-size:14px; color:#666; font-style:normal; cursor:pointer;" onclick="document.getElementById('custom-course-title').focus()">✎</i>
                </div>
                <!-- No Tags, No Intro -->
            </div>`;
            // Update header title to match
            document.getElementById('res-title').innerText = window.I18n.t('result_title_custom');
            document.getElementById('res-sub').innerText = window.I18n.t('result_sub_custom');
        } else {
            hero = `
                <div class="plan-hero">
                    <div class="plan-hero-title" onclick="App.expandHeader()">${title}</div>
                    <div class="plan-hero-tags">
                        <div class="ph-tag">${window.I18n.t('enum_' + u.level)}</div>
                        <div class="ph-tag">${ctx.meta.duration}${window.I18n.t('common_unit_min')}</div>
                        <div class="ph-tag">${ctx.meta.targets.map(t => window.I18n.t('enum_' + t)).join('、')}</div>
                    </div>
                    <div class="plan-hero-intro">
                        <div style="margin-bottom:4px"><b>${window.I18n.t('result_intro_label_goal')}</b>${window.I18n.t('enum_' + toEn(ctx.meta.goal))}</div>
                        <div><b>${window.I18n.t('result_intro_label_desc')}</b>${window.I18n.t('result_intro_label_desc')}</div>
                    </div>
                </div>`;
        }

        const stats = `
            <div class="stats-bar" id="res-stats" style="background:transparent; border-bottom:1px solid rgba(255,255,255,0.1);">
                <div>${window.I18n.t('result_stats_time')} <span class="stat-val" id="st-time">--</span></div>
                <div>${window.I18n.t('result_stats_count')} <span class="stat-val" id="st-count">--</span></div>
                <div>${window.I18n.t('result_stats_vol')} <span class="stat-val" id="st-vol">--</span></div>
                <div>${window.I18n.t('result_stats_cal')} <span class="stat-val" id="st-cal">--</span></div>
            </div>`;

        const flowTabs = `<div id="course-flow-tabs" class="plan-flow-container" style="padding:15px 24px 5px 24px; gap:4px;"></div>`;
        const phaseDesc = `<div id="course-phase-desc" style="padding: 0 24px 15px 24px;"></div>`;
        const phaseControls = `<div id="course-phase-controls" style="padding: 0 20px 10px 20px;"></div>`;
        const content = `<div id="res-phase-content" class="plan-scroll-area" style="padding:0 20px 50vh 20px;"></div>`;

        const html = `
            <div class="plan-layout-container">
                <div class="plan-static-top">
                    ${hero}
                    ${stats}
                    ${flowTabs}
                    ${phaseDesc}
                    ${phaseControls}
                </div>
                ${content}
            </div>`;
        
        document.getElementById('res-course-content').innerHTML = html;
    },

    renderFineTuning: (ctx) => {
        App.recalculateDurations(ctx); // Recalculate before rendering
        const resContent = document.getElementById('res-phase-content');
        const resControls = document.getElementById('course-phase-controls');
        const settings = window.store.courseSettings;
        const opts = (arr, val) => arr.map(o => `<option value="${o}" ${o===val?'selected':''}>${window.I18n.t('enum_' + o)}</option>`).join('');
        const unit = window.store.unit || 'kg';

        // Update Flow Tabs
        const tabsContainer = document.getElementById('course-flow-tabs');
        if (tabsContainer) {
            let tabsHtml = '';
            ctx.phases.forEach((p, idx) => {
                const isActive = idx === window.store.activePhaseIdx;
                const dur = p.duration || 0;
                tabsHtml += `<div class="plan-flow-item ${isActive?'active':''}" onclick="App.switchPhase(${idx})" style="flex:${p.duration || 1}; min-width:0;">
                    <div style="font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${window.I18n.t('common_phase_' + (p.type === 'Warmup' ? 'warmup' : p.type === 'Main' ? 'main' : 'cooldown'))}</div>
                    <div style="font-size:9px; opacity:0.8;">${dur}${window.I18n.t('common_unit_min')}</div>
                </div>`;
                if (idx < ctx.phases.length - 1) tabsHtml += `<div class="plan-flow-arrow" style="font-size:10px; color:#444;">→</div>`;
            });
            tabsContainer.innerHTML = tabsHtml;
        }

        let html = ``;

        const pIdx = window.store.activePhaseIdx;
        const p = ctx.phases[pIdx];
        
        // Update Phase Description
        let phaseIntro = '';
        if (p.type === 'Warmup') phaseIntro = window.I18n.t('phase_intro_warmup');
        else if (p.type === 'Main') phaseIntro = window.I18n.t('phase_intro_main');
        else if (p.type === 'Cooldown') phaseIntro = window.I18n.t('phase_intro_cooldown');
        
        const descContainer = document.getElementById('course-phase-desc');
        if (descContainer) {
            descContainer.innerHTML = phaseIntro ? `<div class="plan-phase-desc-static">${phaseIntro}</div>` : '';
        }

        if (p) {
            let controlsHtml = '';
            
            // Unified Controls for ALL phases
            const rest = p.strategy?.rest || 0;
            const restRound = p.strategy?.restRound || 0;
            const pLoadStrategy = p.strategy?.loadStrategy || 'Recommended';
            const pLoopMode = p.strategy?.loopMode || 'Regular';
            const disabledAttr = ''; // Always enabled
            
            controlsHtml = `
            <div class="phase-controls-row">
                <div class="control-group">
                    <span class="cg-label">${window.I18n.t('result_control_load')}</span>
                    <select class="phase-select" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'loadStrategy', this.value)">
                        ${opts(CONSTANTS.ENUMS.LOAD_STRATEGY, pLoadStrategy)}
                    </select>
                </div>
                <div class="control-group">
                    <span class="cg-label">${window.I18n.t('result_control_mode')}</span>
                    <select class="phase-select" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'loopMode', this.value)">${opts(CONSTANTS.ENUMS.LOOP_MODE, pLoopMode)}</select>
                </div>
                <div class="control-group">
                    <span class="cg-label">${window.I18n.t('result_control_rest')}</span>
                    <input type="number" class="phase-select" style="width:38px; text-align:center; padding:2px;" value="${rest}" step="5" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'rest', this.value)"><span style="font-size:10px; color:#666; margin-left:-1px;">s</span>
                </div>
                <div class="control-group">
                    <span class="cg-label">${window.I18n.t('result_control_round')}</span>
                    <input type="number" class="phase-select" style="width:38px; text-align:center; padding:2px;" value="${restRound}" step="5" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'restRound', this.value)"><span style="font-size:10px; color:#666; margin-left:-1px;">s</span>
                </div>
            </div>`;

            if (resControls) {
                resControls.innerHTML = `
            <div class="phase-header-row" style="justify-content:flex-end; margin-bottom:10px;">
                <button class="ad-add-btn" onclick="App.addAction(${pIdx})" style="margin-top:0; width:auto; padding:6px 12px;">${window.I18n.t('result_btn_add_action')}</button>
            </div>
            ${controlsHtml}`;
            }
            
            let listHtml = `<div class="action-list">`;
            
            if (p.actions.length === 0) {
                listHtml += `<div style="text-align:center; padding:30px 0; color:#666; font-size:12px; border:1px dashed #333; border-radius:8px; margin-bottom:10px; cursor:pointer;" onclick="App.addAction(${pIdx})">${window.I18n.t('result_msg_add_action')}</div>`;
            }

            p.actions.forEach((a, aIdx) => {
                if (!a.setDetails || a.setDetails.length !== a.sets) {
                    a.setDetails = [];
                    for(let i=0; i<a.sets; i++) {
                        a.setDetails.push({ load: a.load, reps: a.reps });
                    }
                }

                const isResistance = a.paradigm === 'Resistance';
                const isWarmup = p.type === 'Warmup' || p.type === 'Cooldown';
                const isTimeBased = a.paradigm === 'Interval' || a.paradigm === 'Flow' || a.measure === 'Time';
                const hasPower = a.powerModule === 'Yes';
                const isMirror = a.mirror;
                const repUnit = isTimeBased ? window.I18n.t('common_unit_sec') : window.I18n.t('common_unit_rep');

                const expanded = a.expanded ? 'block' : 'none';
                const arrow = a.expanded ? '▲' : '▼';
                
                const thumb = `<div class="ac-thumb"><i style="font-style:normal; font-size:16px;">📷</i></div>`;
                
                let setDetailsStr = '';
                if (a.setDetails && a.setDetails.length > 0) {
                    let vals = [];
                    let suffix = '';
                    if (isResistance && !isWarmup && !isTimeBased && hasPower) {
                        vals = a.setDetails.map(s => s.load);
                        suffix = unit;
                    } else {
                        vals = a.setDetails.map(s => s.reps);
                        suffix = repUnit;
                    }
                    const showCount = 3;
                    setDetailsStr = vals.slice(0, showCount).join('/');
                    if (suffix) setDetailsStr += suffix;
                    if (vals.length > showCount) setDetailsStr += '...';
                }

                let summary = '';
                if (isResistance && !isWarmup && !isTimeBased && hasPower) {
                    summary = `<span class="ac-tag" style="color:var(--primary)">${a.sets}组</span> <span class="ac-tag">${setDetailsStr}</span>`;
                } else {
                    summary = `<span class="ac-tag" style="color:var(--primary)">${a.sets}组</span> <span class="ac-tag">${setDetailsStr}</span>`;
                }

                let setsHtml = '';
                a.setDetails.forEach((s, sIdx) => {
                    const disabledStyle = ''; // Always enabled

                    const stepperContent = (val, field) => {
                        let stepAttr = '';
                        if (field === 'reps' && isTimeBased) stepAttr = 'step="5"';
                        else if (field === 'load') stepAttr = unit === 'kg' ? 'step="0.5"' : 'step="1"';
                        return `
                        <div class="stepper" style="${disabledStyle}">
                            <div class="step-btn" onclick="window.App.adjustSetData(${pIdx}, ${aIdx}, ${sIdx}, '${field}', -1)">-</div>
                            <input class="step-input" type="number" value="${val}" ${stepAttr} onchange="window.App.updateSetData(${pIdx}, ${aIdx}, ${sIdx}, '${field}', this.value)">
                            <div class="step-btn" onclick="window.App.adjustSetData(${pIdx}, ${aIdx}, ${sIdx}, '${field}', 1)">+</div>
                        </div>
                    `};
                    
                    const stepper = (val, field) => {
                        return stepperContent(val, field);
                    };

                    const mirrorLabel = isMirror ? `<span style="font-size:10px; color:var(--primary); margin-left:4px; border:1px solid var(--primary); padding:0 2px; border-radius:2px;">镜像</span>` : '';

                    let inputs = '';
                    if (isResistance && !isWarmup && !isTimeBased && hasPower) {
                        inputs = `
                            ${stepper(s.load, 'load')} <span style="color:#666;font-size:10px;">${unit}</span>
                            <span style="color:#444; margin:0 5px;">x</span>
                            ${stepper(s.reps, 'reps')} <span style="color:#666;font-size:10px;">${repUnit}</span>${mirrorLabel}
                        `;
                    } else {
                        inputs = `
                            ${stepper(s.reps, 'reps')} <span style="color:#666;font-size:10px;">${repUnit}</span>${mirrorLabel}
                        `;
                    }
                    
                    setsHtml += `
                        <div class="set-row">
                            <div class="set-idx">${sIdx+1}</div>
                            ${inputs}
                            <div class="set-del" onclick="App.removeSet(${pIdx}, ${aIdx}, ${sIdx})">×</div>
                        </div>
                    `;
                });

                setsHtml += `<div class="add-set-btn" onclick="App.addSet(${pIdx}, ${aIdx})">+ 加一组</div>`;
                
                listHtml += `
                <div class="action-card-pro">
                    <div class="ac-del-corner" onclick="event.stopPropagation(); App.deleteAction(${pIdx}, ${aIdx})">✕</div>
                    <div class="ac-header" onclick="App.toggleAction(${pIdx}, ${aIdx})">
                        ${thumb}
                        <div class="ac-info">
                            <div class="ac-title">${a.name}</div>
                            <div class="ac-meta">
                                <span class="ac-tag">${a.part}</span>
                                <span class="ac-tag">${a.muscle}</span>
                                ${summary}
                            </div>
                        </div>
                        <div class="ae-tools" onclick="event.stopPropagation()">
                            <div class="ae-btn" onclick="App.moveAction(${pIdx}, ${aIdx}, -1)">↑</div>
                            <div class="ae-btn" onclick="App.moveAction(${pIdx}, ${aIdx}, 1)">↓</div>
                            <div class="ae-btn" onclick="App.openLibrary(${pIdx}, ${aIdx})">↻</div>
                            <div class="ae-btn" style="border:none; background:transparent;" id="ac-arrow-${pIdx}-${aIdx}">${arrow}</div>
                        </div>
                    </div>
                    
                    <div class="ac-body-exp" id="ac-body-${pIdx}-${aIdx}" style="display:${expanded};">
                        <div class="set-list">
                            ${setsHtml}
                        </div>
                        <div class="ac-footer">
                            <span>强度: ${(a.load > 0 && CONSTANTS.ENUMS.ONE_RM[a.part]) ? Math.round(a.load / CONSTANTS.ENUMS.ONE_RM[a.part] * 100) : '-'}%</span>
                            <span>RPE: ${a.rpe || 8}</span>
                            <span>组间: ${p.strategy?.rest || 60}s</span>
                            <span style="margin-left:auto; color:var(--primary); cursor:pointer; font-weight:600;" onclick="App.resetActionParams(${pIdx}, ${aIdx})">↺ 重置</span>
                        </div>
                        <div class="ac-detail-link" onclick="App.openActionDetail('${a.id}', 'result')">
                            查看动作详情 >
                        </div>
                    </div>
                </div>`;
            });
            listHtml += `</div>`;
            
            resContent.innerHTML = listHtml;
        }
        App.updateStats();
    },

    resetActionParams: (pIdx, aIdx) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        if (action.recommendedSetDetails) {
            action.setDetails = JSON.parse(JSON.stringify(action.recommendedSetDetails));
            action.sets = action.setDetails.length;
            const loads = action.setDetails.map(s => parseFloat(s.load)||0);
            action.load = Math.max(...loads);
            window.App.showToast(window.I18n.t('toast_reset_recommended'));
            App.renderFineTuning(window.currentCtx);
        }
    },

    switchPhase: (idx) => {
        window.store.activePhaseIdx = idx;
        App.renderFineTuning(window.currentCtx);
    },
    
    updatePhaseParam: (pIdx, key, val) => {
        if (window.currentCtx && window.currentCtx.phases[pIdx]) {
            if (key === 'rest' || key === 'restRound') {
                let num = parseInt(val);
                if (isNaN(num) || num < 0) num = 0;
                window.currentCtx.phases[pIdx].strategy[key] = num;
            } else {
                window.currentCtx.phases[pIdx].strategy[key] = val;
            }
            
            if (key === 'loadStrategy') {
                // FIX: 切换策略时，立即基于当前第1组数据应用新梯度，而不是清空重算
                App.applyStrategyToPhase(pIdx, val);
                window.App.showToast(window.I18n.t('toast_strategy_switch', {val: window.I18n.t('enum_' + val)}));
            } else {
                App.renderFineTuning(window.currentCtx);
            }
        }
    },

    // 新增：基于当前数据应用新策略 (核心修复逻辑)
    applyStrategyToPhase: (pIdx, strategy) => {
        const phase = window.currentCtx.phases[pIdx];
        if (!phase || !phase.actions) return;
        
        // 1. 自定义模式：不做任何联动
        if (strategy === 'Custom') return;

        phase.actions.forEach(a => {
            if (!a.setDetails || a.setDetails.length === 0) return;
            
            // 0. 推荐模式：重置为 AI 推荐值
            if (strategy === 'Recommended') {
                if (a.recommendedSetDetails) {
                    a.setDetails = JSON.parse(JSON.stringify(a.recommendedSetDetails));
                    a.sets = a.setDetails.length;
                    const loads = a.setDetails.map(s => parseFloat(s.load)||0);
                    a.load = Math.max(...loads);
                }
                return;
            }

            const isPower = a.powerModule === 'Yes';
            const isTimeBased = a.paradigm === 'Interval' || a.paradigm === 'Flow' || a.measure === 'Time';

            // 1. 获取锚点：取当前所有组中的最大值作为目标负荷 (Peak Load)
            // 这样可以确保无论从递增还是递减切换过来，都以用户设定的"最重一组"为基准
            let targetVal = 0;
            if (isPower) {
                const currentLoads = a.setDetails.map(s => parseFloat(s.load) || 0);
                targetVal = Math.max(...currentLoads, a.load || 0, 20);
            } else {
                const currentReps = a.setDetails.map(s => parseFloat(s.reps) || 0);
                targetVal = Math.max(...currentReps, parseInt(a.reps) || 0, 1);
            }
            
            const base1RM = a.demoUser1RM || window.UserAbility.oneRM[a.part] || 20;
            
            let step = 0;
            let minStep = 0;
            
            if (isPower) {
                minStep = 0.5;
                step = Math.max(minStep, base1RM * 0.05);
            } else {
                minStep = 1;
                step = Math.max(1, Math.round(targetVal * 0.1)); // 10% step for reps/time
            }
            
            const setsCnt = a.setDetails.length;

            if (strategy === 'Constant') {
                // 恒定：所有组 = 目标重量
                a.setDetails.forEach(s => {
                    if (isPower) {
                        s.load = targetVal;
                        if (!isTimeBased) s.reps = window.Logic.calcRepsFromLoad(s.load, base1RM);
                    } else {
                        s.reps = targetVal;
                    }
                });
            } else if (strategy === 'Progressive') {
                // 递增：以目标负荷为终点 (End at Target)
                a.setDetails.forEach((s, i) => {
                    let val = targetVal - (setsCnt - 1 - i) * step;
                    if (isPower) {
                        s.load = Math.max(minStep, Math.round(val * 2) / 2);
                        if (!isTimeBased) s.reps = window.Logic.calcRepsFromLoad(s.load, base1RM);
                    } else {
                        s.reps = Math.max(minStep, Math.round(val));
                    }
                });
            } else if (strategy === 'Regressive') {
                // 递减：以目标负荷为起点 (Start at Target)
                a.setDetails.forEach((s, i) => {
                    let val = targetVal - i * step;
                    if (isPower) {
                        s.load = Math.max(minStep, Math.round(val * 2) / 2);
                        if (!isTimeBased) s.reps = window.Logic.calcRepsFromLoad(s.load, base1RM);
                    } else {
                        s.reps = Math.max(minStep, Math.round(val));
                    }
                });
            }
            
            if (isPower) a.load = targetVal; 
            else a.reps = targetVal;
        });
        App.renderFineTuning(window.currentCtx);
    },

    recalculateDurations: (ctx) => {
        if (!ctx || !ctx.phases) return;
        
        let totalSeconds = 0;

        ctx.phases.forEach(p => {
            let phaseSeconds = 0;
            const rest = p.strategy.rest || 0;
            const restRound = p.strategy.restRound || 0;
            
            p.actions.forEach((a, aIdx) => {
                let actionSeconds = 0;
                const isTimeBased = a.paradigm === 'Interval' || a.paradigm === 'Flow' || a.measure === 'Time';
                const singleDur = a.singleDur || 3;
                
                // Ensure setDetails exists
                if (!a.setDetails) return;
                
                a.setDetails.forEach((s, sIdx) => {
                    let setDur = 0;
                    if (isTimeBased) {
                        setDur = parseInt(s.reps) || 0;
                    } else {
                        setDur = (parseInt(s.reps) || 0) * singleDur;
                    }
                    
                    if (a.mirror) setDur *= 2;
                    
                    actionSeconds += setDur;
                    
                    // Add rest if not last set
                    if (sIdx < a.setDetails.length - 1) {
                        actionSeconds += rest;
                    }
                });
                
                phaseSeconds += actionSeconds;
                
                // Add restRound if not last action
                if (aIdx < p.actions.length - 1) {
                    phaseSeconds += restRound;
                }
            });
            
            // [FIX] Warmup/Relax: Perfect dynamic match (Round). Main: Looser (Ceil).
            if (p.type === 'Main') {
                p.duration = Math.ceil(phaseSeconds / 60);
            } else {
                p.duration = Math.round(phaseSeconds / 60);
            }
            totalSeconds += phaseSeconds;
        });
        
        // Update meta duration
        ctx.meta.duration = Math.ceil(totalSeconds / 60);
    },

    adjustSetData: (pIdx, aIdx, sIdx, field, dir) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        const set = action.setDetails[sIdx];
        const unit = window.store.unit || 'kg';
        
        let step = 1;
        if (field === 'load') step = unit === 'kg' ? 0.5 : 1;
        else if (field === 'reps') {
            const isTimeBased = action.paradigm === 'Interval' || action.paradigm === 'Flow';
            step = isTimeBased ? 5 : 1;
        }
        
        let val = parseFloat(set[field]) || 0;
        val = Math.max(0, val + dir * step);
        
        if (field === 'load' && unit === 'kg') val = Math.round(val * 2) / 2;
        else val = Math.round(val);
        
        App.updateSetData(pIdx, aIdx, sIdx, field, val);
    },

    updateSetData: (pIdx, aIdx, sIdx, field, val) => {
        const phase = window.currentCtx.phases[pIdx];
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        let numVal = parseFloat(val);
        if (isNaN(numVal)) numVal = 0;
        
        if (action.setDetails && action.setDetails[sIdx]) {
            let strat = phase.strategy.loadStrategy || 'Recommended';
            
            // 1. 自定义模式：不做任何联动
            if (strat === 'Custom') {
                action.setDetails[sIdx][field] = numVal;
                if (field === 'load') {
                    const loads = action.setDetails.map(s => parseFloat(s.load)||0);
                    action.load = Math.max(...loads);
                }
                window.App.renderFineTuning(window.currentCtx);
                return;
            }

            // FIX: Auto-switch '推荐' to '递增' on manual edit
            if (field === 'load' && strat === 'Recommended') {
                strat = 'Progressive';
                phase.strategy.loadStrategy = 'Progressive';
                window.App.showToast(window.I18n.t('toast_auto_switch_progressive'));
            }

            action.setDetails[sIdx][field] = numVal;
            
            if (field === 'load') {
                // 2. Apply Strategy Logic (Interpolation)
                if (strat === 'Constant') {
                    action.setDetails.forEach(s => s[field] = numVal);
                } else if (strat === 'Progressive' || strat === 'Regressive') {
                    const sets = action.setDetails.length;
                    if (sets > 2) {
                        const startVal = parseFloat(action.setDetails[0][field]);
                        const endVal = parseFloat(action.setDetails[sets - 1][field]);
                        
                        for (let i = 1; i < sets - 1; i++) {
                            let interpolated = startVal + (endVal - startVal) * (i / (sets - 1));
                            if (field === 'load') interpolated = Math.round(interpolated * 2) / 2;
                            else interpolated = Math.round(interpolated);
                            
                            action.setDetails[i][field] = interpolated;
                        }
                    }
                }
                
                // 3. RM Recalculation (Load -> Reps)
                // Apply to ALL sets if load changed, regardless of phase type (if it's resistance and not time-based)
                const isTimeBased = action.paradigm === 'Interval' || action.paradigm === 'Flow' || a.measure === 'Time';
                if (!isTimeBased && action.paradigm === 'Resistance') {
                    const base1RM = action.demoUser1RM || window.UserAbility.oneRM[action.part] || window.UserAbility.oneRM['全身'] || 20;
                    action.setDetails.forEach((s, idx) => {
                        if (s.load > 0) s.reps = window.Logic.calcRepsFromLoad(s.load, base1RM);
                    });
                    if (action.setDetails.length > 0) action.reps = action.setDetails[0].reps;
                }
            }
            
            // FIX: Update action.load to Peak Load
            if (field === 'load') {
                const loads = action.setDetails.map(s => parseFloat(s.load)||0);
                action.load = Math.max(...loads);
            } else if (sIdx === 0) {
                action[field] = numVal;
            }
        }
        window.App.renderFineTuning(window.currentCtx);
    },

    toggleAction: (pIdx, aIdx) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        action.expanded = !action.expanded;
        const body = document.getElementById(`ac-body-${pIdx}-${aIdx}`);
        const arrow = document.getElementById(`ac-arrow-${pIdx}-${aIdx}`);
        if (body) body.style.display = action.expanded ? 'block' : 'none';
        if (arrow) arrow.innerText = action.expanded ? '▲' : '▼';
        if (action.expanded) App.collapseHeader();
    },

    toggleUnit: () => {
        const current = window.store.unit || 'kg';
        const next = current === 'kg' ? 'lbs' : 'kg';
        window.store.unit = next;
        const sw = document.getElementById('unit-switch');
        sw.classList.toggle('lbs', next === 'lbs');
        sw.querySelector('.unit-knob').innerText = next.toUpperCase();
        
        if (window.store.flow === 'course' || (document.getElementById('res-course-content').style.display !== 'none')) {
            if (window.currentCtx && window.currentCtx.phases) {
                window.currentCtx.phases.forEach(p => {
                    if (p.actions) {
                        p.actions.forEach(a => {
                            const convertKg = (val) => Math.round((val / 2.20462) * 2) / 2;
                            const convertLbs = (val) => Math.round(val * 2.20462);
                            
                            const doConvert = (v) => {
                                if (typeof v !== 'number' || isNaN(v)) return v;
                                return next === 'lbs' ? convertLbs(v) : convertKg(v);
                            };
                            
                            if (typeof a.load === 'number') a.load = doConvert(a.load);
                            
                            if (a.setDetails) {
                                a.setDetails.forEach(s => {
                                    if (typeof s.load === 'number') s.load = doConvert(s.load);
                                });
                            }
                        });
                    }
                });
            }
            App.renderFineTuning(window.currentCtx);
        } else {
            const chartContainer = document.getElementById('plan-weight-chart-container');
            if (chartContainer) {
                chartContainer.outerHTML = App.renderWeightChart();
                App.updateWeightChart(window.store.activePlanPhaseIdx);
            }
        }
    },

    updateGlobalSetting: (key, val) => {
        window.store.courseSettings[key] = val;
        if (key === 'loadStrategy') {
            App.clearSetDetails(); // Force regenerate all
            App.recalculateLoadStrategy();
        }
        App.renderFineTuning(window.currentCtx);
    },

    clearSetDetails: (pIdx = null) => {
        if (!window.currentCtx) return;
        window.currentCtx.phases.forEach((p, idx) => {
            if (pIdx !== null && idx !== pIdx) return;
            p.actions.forEach(a => delete a.setDetails);
        });
    },

    addSet: (pIdx, aIdx) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        action.sets++;
        const lastSet = action.setDetails[action.setDetails.length-1] || { load: action.load, reps: action.reps };
        action.setDetails.push({ ...lastSet });
        
        // Re-apply strategy when adding a set
        const strat = window.currentCtx.phases[pIdx].strategy.loadStrategy || 'Constant';
        if (strat === 'Progressive' || strat === 'Regressive') {
             const sets = action.setDetails.length;
             if (sets > 2) {
                const startVal = parseFloat(action.setDetails[0].load);
                // For adding, we might want to extrapolate or just keep last value. 
                // But to keep consistent with "Interpolation logic", let's re-interpolate if we assume the last set is the target peak/end.
                // However, usually adding a set means extending the progression. 
                // Let's just ensure the new set follows the trend if possible, or just copy last (which is done).
                // But if we want to enforce the "First to Last" interpolation, we need to decide if the NEW last set defines the end or if we extend the slope.
                // Simple approach: If we add a set, we might break the perfect interpolation unless we adjust.
                // Let's just re-run interpolation based on current first and NEW last (which is same as prev last).
                // Actually, if we copy last, the slope flattens at the end. 
                // Let's leave it as copy for now, user can adjust last set to fix slope.
             }
             if (strat === 'Constant') {
                 action.setDetails[action.setDetails.length-1].load = action.setDetails[0].load;
             }
        }
        App.renderFineTuning(window.currentCtx);
    },

    removeSet: (pIdx, aIdx, sIdx) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        if (action.sets > 1) {
            action.sets--;
            action.setDetails.splice(sIdx, 1);
            App.renderFineTuning(window.currentCtx);
        }
    },

    moveAction: (pIdx, aIdx, dir) => {
        const actions = window.currentCtx.phases[pIdx].actions;
        if (aIdx + dir >= 0 && aIdx + dir < actions.length) {
            const temp = actions[aIdx];
            actions[aIdx] = actions[aIdx + dir];
            actions[aIdx + dir] = temp;
            App.renderFineTuning(window.currentCtx);
        }
    },

    updateStats: () => {
        const ctx = window.currentCtx;
        let totalSets = 0, totalActions = 0;
        ctx.phases.forEach(p => {
            totalActions += p.actions.length;
            p.actions.forEach(a => totalSets += a.sets);
        });
        
        // Recalculate duration for custom course
        const totalDur = ctx.meta.duration || ctx.phases.reduce((acc, p) => acc + (p.duration || 0), 0);
        
        document.getElementById('st-time').innerText = totalDur + 'min';
        document.getElementById('st-count').innerText = totalActions + ' ' + window.I18n.t('common_unit_moves');
        document.getElementById('st-vol').innerText = totalSets + ' ' + window.I18n.t('common_unit_set');
        document.getElementById('st-cal').innerText = Math.floor(4.5 * window.store.user.weight * (totalDur/60)) + 'kcal';
    },

    openScheduleModal: () => {
        const days = ['周一','周二','周三','周四','周五','周六','周日'];
        const selected = window.store.inputs.days || window.store.user.days || [];
        const html = days.map(d => {
            const isActive = selected.includes(d);
            const subText = isActive ? '训练' : '休息';
            return `<div class="opt-chip ${isActive?'active':''}" onclick="this.classList.toggle('active'); App.toggleDayText(this)"><span>${d}</span><span class="chat-sub-text">${subText}</span></div>`;
        }).join('');
        document.getElementById('schedule-days-list').innerHTML = html;
        document.getElementById('modal-schedule').classList.add('active');
    },

    confirmSchedule: () => {
        const activeChips = document.querySelectorAll('#schedule-days-list .opt-chip.active');
        const days = Array.from(activeChips).map(c => c.innerText);
        if (days.length === 0) return App.showToast(window.I18n.t('msg_select_day'));
        window.store.inputs.days = days;
        document.getElementById('modal-schedule').classList.remove('active');
        App.switchView('view-schedule');
    },

    deleteAction: (pIdx, aIdx) => {
        if (!window.currentCtx) return;
        App.openConfirmModal(window.I18n.t('confirm_delete_action'), () => {
            try {
                const p = window.currentCtx.phases[pIdx];
                if (p && p.actions) {
                    p.actions.splice(aIdx, 1);
                    
                    // Recalculate phase duration for custom flow
                    if (window.currentCtx.source === 'Custom') {
                        let pDur = 0;
                        p.actions.forEach(a => {
                            const rest = p.strategy.rest || 60;
                            const singleDur = 45; // Approx
                            pDur += (a.sets * (singleDur + rest));
                        });
                        p.duration = Math.ceil(pDur / 60);
                        
                        // Update meta duration
                        window.currentCtx.meta.duration = window.currentCtx.phases.reduce((acc, ph) => acc + (ph.duration || 0), 0);
                    }

                    App.renderFineTuning(window.currentCtx);
                }
            } catch (e) {
                console.error("Delete operation error:", e);
            }
            App.closeConfirmModal();
        });
    },

    reset: () => {
        window.store.flow = null;
        window.store.step = 0;
        window.store.inputs = {};
        window.store.pendingFatigue = null;
        window.store.chatAnchorY = null;

        App.switchView('view-home');
        document.getElementById('profile-card').classList.remove('hidden');
        document.getElementById('chat-history').innerHTML = '';
        document.getElementById('app').classList.remove('state-chat');
        document.getElementById('home-bg-layer').classList.remove('hidden');
    },

    saveTemplate: () => {
        App.showToast(window.I18n.t('app_toast_template_saved'));
    },

    initResultScroll: () => {
        const scrollAreas = document.querySelectorAll('.plan-scroll-area');
        scrollAreas.forEach(scrollArea => {
            let lastScrollTop = 0;
            scrollArea.onscroll = (e) => {
                const st = e.target.scrollTop;
                if (st > lastScrollTop && st > 10) App.collapseHeader();
                else if (st < lastScrollTop) App.expandHeader();
                lastScrollTop = st <= 0 ? 0 : st;
            };
        });
    },

    collapseHeader: () => {
        const container = document.querySelector('.plan-layout-container');
        if (container && !container.classList.contains('collapsed')) container.classList.add('collapsed');
    },

    expandHeader: () => {
        const container = document.querySelector('.plan-layout-container');
        if (container && container.classList.contains('collapsed')) container.classList.remove('collapsed');
    }
};