window.ViewResult = {
    showResult: () => {
        const flow = window.store.flow;
        const inputs = window.store.inputs;
        const btnMain = document.getElementById('btn-main-action');
        
        // Reset UI State
        document.getElementById('btn-back-plan').style.display = 'none';
        document.getElementById('btn-close-result').style.display = 'block'; // Show close button on top level
        
        App.switchView('view-result');
        
        if (flow === 'course') {
            document.getElementById('view-result').classList.add('plan-mode');
            btnMain.innerText = '开始训练';
            btnMain.onclick = () => {
                window.ViewWorkout.start(window.currentCtx);
            };
            
            // UI Toggle
            document.getElementById('res-plan-list').style.display = 'none';
            document.getElementById('res-course-content').style.display = 'block';
            document.getElementById('unit-switch').style.display = 'block';

            const ctx = window.Logic.genCourse(inputs);
            window.store.courseSettings = { loopMode: '常规组', loadStrategy: '恒定', smartRec: true };
            window.currentCtx = ctx;
            
            const mainIdx = ctx.phases.findIndex(p => p.type === '主训');
            window.store.activePhaseIdx = mainIdx >= 0 ? mainIdx : 0;

            App.setupCourseResultUI(ctx, `${inputs.type}训练`);
            App.renderFineTuning(ctx);
            
        } else {
            document.getElementById('view-result').classList.add('plan-mode');
            btnMain.innerText = '加入日程';
            btnMain.onclick = () => App.openScheduleModal();
            
            // UI Toggle
            document.getElementById('res-plan-list').style.display = 'block';
            document.getElementById('res-course-content').style.display = 'none';
            document.getElementById('unit-switch').style.display = 'block';

            const plan = window.Logic.genPlan(inputs);
            
            // 1. Plan Name: {Level} + {FuncGoal} + "计划"
            const u = window.store.user;
            const levelMap = { 'L1':'初级', 'L2':'初级', 'L3':'中级', 'L4':'中级', 'L5':'高级' };
            const levelText = levelMap[u.level] || '初级';
            const funcGoal = u.funcGoal || u.goal || '增肌';
            
            // 3. Plan Intro
            const introMap = {
                '增肌': {
                    people: '体型单薄或渴望肌肉线条的人群',
                    pain: '突破增肌平台期，解决力量增长停滞',
                    desc: '采用科学的分化训练体系，结合渐进超负荷原则',
                    effect: '有效促进肌肉肥大与力量增长'
                },
                '减重': {
                    people: '体脂较高或需要体重管理的人群',
                    pain: '解决代谢缓慢、体脂难以顽固堆积的问题',
                    desc: '结合高强度间歇(HIIT)与有氧训练，最大化运动后过量氧耗(EPOC)',
                    effect: '快速燃烧脂肪，重塑紧致身材'
                },
                '健康': {
                    people: '久坐少动或亚健康人群',
                    pain: '改善体能下降、易疲劳及体态问题',
                    desc: '注重全身功能性训练，平衡柔韧、协调与心肺能力',
                    effect: '提升综合体能，焕发身体活力'
                }
            };
            // Fallback to '增肌' if goal not found, or map based on main goal
            const mapKey = introMap[u.goal] ? u.goal : '增肌';
            const curIntro = introMap[mapKey];
            
            const planHero = `
                <div class="plan-hero">
                    <div class="plan-hero-title">${levelText}${funcGoal}计划</div>
                    <div class="plan-hero-tags">
                        <div class="ph-tag">${u.level}</div>
                        <div class="ph-tag">${inputs.cycle}周</div>
                        <div class="ph-tag">${inputs.days.length}天/周</div>
                    </div>
                    <div class="plan-hero-intro">
                        <div style="margin-bottom:4px"><b>适应人群</b>${curIntro.people}</div>
                        <div style="margin-bottom:4px"><b>解决痛点</b>${curIntro.pain}</div>
                        <div><b>预期效果</b>${curIntro.effect}</div>
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
                    <div style="font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${pName.substr(0,4)}</div>
                    <div style="font-size:9px; opacity:0.8;">${weeks}周 | ${intensity}</div>
                </div>`;
                if (idx < phaseOrder.length - 1) topHtml += `<div class="plan-flow-arrow" style="font-size:10px; color:#444;">→</div>`;
            });
            topHtml += `</div>`;

            topHtml += `<div id="plan-phase-desc-container" style="padding: 0 24px 5px 24px;"></div>`;

            topHtml += `
                <div class="plan-calendar-header">
                    <div>周一</div><div>周二</div><div>周三</div><div>周四</div><div>周五</div><div>周六</div><div>周日</div>
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
        const phaseWeights = { '适应': 0.1, '进阶': 0.3, '增长': 0.3, '突破': 0.4, '减载': 0.05, '恢复': 0.05 };
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
                <span>体重预测 (${unit})</span>
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
        if (pName.includes("适应")) pDesc = "建立神经适应，激活目标肌群，为后续高强度训练打基础。";
        else if (pName.includes("增长")) pDesc = "增加训练容量，最大化代谢压力，促进肌肉肥大。";
        else if (pName.includes("突破")) pDesc = "提高训练强度，冲击力量瓶颈，突破平台期。";
        else if (pName.includes("恢复")) pDesc = "降低负荷，消除积累疲劳，实现超量恢复。";
        
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
        if (w.phase.includes("适应")) phaseSuffix = "激活";
        else if (w.phase.includes("增长")) phaseSuffix = "增长";
        else if (w.phase.includes("突破")) phaseSuffix = "突破";
        else if (w.phase.includes("恢复")) phaseSuffix = "恢复";
        else phaseSuffix = "训练";

        const level = window.store.user.level;

        w.days.forEach((day, idx) => {
            const d = idx + 1;
            const cls = day.isTraining ? 'training' : 'rest';
            const targetsStr = day.targets ? day.targets.join(',') : '';
            const click = day.isTraining ? `onclick="App.enterPlanDay(${w.week}, ${d}, '${day.dayName}', '${targetsStr}')"` : '';
            
            let content = '';
            if (day.isTraining) {
                let baseTitle = day.title.replace('力量','').replace('训练','');
                if(baseTitle.length > 4) baseTitle = baseTitle.substr(0,4);
                
                content = `
                    <div class="pdc-title">${baseTitle}${phaseSuffix}</div>
                    <div class="pdc-sub">${level}</div>
                `;
            } else {
                content = `<div class="pdc-title" style="font-weight:400; color:#888;">休息</div>`;
            }

            daysHtml += `
            <div class="plan-day-cell ${cls}" ${click}>
                ${content}
            </div>`;
        });
        return `<div style="margin-bottom:10px;">
                    <div style="font-size:10px;color:#666;margin-bottom:4px;padding-left:4px;">第 ${w.week} 周</div>
                    <div class="plan-week-row">${daysHtml}</div>
                </div>`;
    },

    enterPlanDay: (week, day, dayName, targetsStr) => {
        const inputs = window.store.inputs;
        const targets = targetsStr.split(',');
        const planContext = { type: '力量', targets: targets, duration: parseInt(inputs.duration), title: `${dayName}训练`, phase: { intensity: 1.0, volume: 1.0 }, goal: window.store.user.goal };
        const ctx = window.Logic.runPipeline(null, planContext);
        const mainIdx = ctx.phases.findIndex(p => p.type === '主训');
        window.store.activePhaseIdx = mainIdx >= 0 ? mainIdx : 0;
        window.store.courseSettings = { loopMode: '常规组', loadStrategy: '恒定', smartRec: true };
        
        // Switch to Course View inside Result
        document.getElementById('view-result').classList.add('plan-mode');
        document.getElementById('res-plan-list').style.display = 'none';
        document.getElementById('res-course-content').style.display = 'block';
        document.getElementById('unit-switch').style.display = 'block';
        
        window.currentCtx = ctx;
        App.setupCourseResultUI(ctx, `W${week} | ${dayName}`);
        App.renderFineTuning(ctx);
        document.getElementById('btn-close-result').style.display = 'none'; // Hide close, show back
        document.getElementById('btn-back-plan').style.display = 'block';
    },

    toggleSmartRec: () => {
        window.store.courseSettings.smartRec = !window.store.courseSettings.smartRec;
        App.recalculateLoadStrategy();
        App.renderFineTuning(window.currentCtx);
    },

    recalculateLoadStrategy: () => {
        if(!window.currentCtx) return;
        window.currentCtx = window.Logic.instantiate(window.currentCtx);
    },

    setupCourseResultUI: (ctx, title) => {
        const u = window.store.user;
        const hero = `
            <div class="plan-hero">
                <div class="plan-hero-title">${title}</div>
                <div class="plan-hero-tags">
                    <div class="ph-tag">${u.level}</div>
                    <div class="ph-tag">${ctx.meta.duration}分钟</div>
                    <div class="ph-tag">${ctx.meta.targets.join('、')}</div>
                </div>
                <div class="plan-hero-intro">
                    <div style="margin-bottom:4px"><b>训练目标</b>${ctx.meta.goal}</div>
                    <div><b>课程简介</b>本课程针对${ctx.meta.targets.join('、')}设计，旨在通过${ctx.meta.type}训练提升${ctx.meta.goal}能力。</div>
                </div>
            </div>`;

        const stats = `
            <div class="stats-bar" id="res-stats" style="background:transparent; border-bottom:1px solid rgba(255,255,255,0.1);">
                <div>时长 <span class="stat-val" id="st-time">--</span></div>
                <div>动作 <span class="stat-val" id="st-count">--</span></div>
                <div>容量 <span class="stat-val" id="st-vol">--</span></div>
                <div>消耗 <span class="stat-val" id="st-cal">--</span></div>
            </div>`;

        const flowTabs = `<div id="course-flow-tabs" class="plan-flow-container" style="padding:15px 24px 5px 24px; gap:4px;"></div>`;
        const phaseDesc = `<div id="course-phase-desc" style="padding: 0 24px 15px 24px;"></div>`;
        const content = `<div id="res-phase-content" class="plan-scroll-area" style="padding:0 20px 20px 20px;"></div>`;

        const html = `
            <div class="plan-layout-container">
                <div class="plan-static-top">
                    ${hero}
                    ${stats}
                    ${flowTabs}
                    ${phaseDesc}
                </div>
                ${content}
            </div>`;
        
        document.getElementById('res-course-content').innerHTML = html;
    },

    renderFineTuning: (ctx) => {
        const resContent = document.getElementById('res-phase-content');
        const settings = window.store.courseSettings;
        const opts = (arr, val) => arr.map(o => `<option ${o===val?'selected':''}>${o}</option>`).join('');
        const unit = window.store.unit || 'kg';
        const isSmart = settings.smartRec;

        // Update Flow Tabs
        const tabsContainer = document.getElementById('course-flow-tabs');
        if (tabsContainer) {
            let tabsHtml = '';
            ctx.phases.forEach((p, idx) => {
                const isActive = idx === window.store.activePhaseIdx;
                tabsHtml += `<div class="plan-flow-item ${isActive?'active':''}" onclick="App.switchPhase(${idx})" style="flex:${p.duration}; min-width:0;">
                    <div style="font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${p.type}</div>
                    <div style="font-size:9px; opacity:0.8;">${p.duration}min</div>
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
        if (p.type === '热身') phaseIntro = '通过低强度动态动作激活目标肌群，提升核心体温，为正式训练做好准备。';
        else if (p.type === '主训') phaseIntro = '本课程的核心训练环节，请保持专注，控制动作节奏，感受肌肉发力。';
        else if (p.type === '放松') phaseIntro = '通过静态拉伸缓解肌肉紧张，促进代谢废物排出，加速身体恢复。';
        
        const descContainer = document.getElementById('course-phase-desc');
        if (descContainer) {
            descContainer.innerHTML = `<div class="plan-phase-desc-static">${phaseIntro}</div>`;
        }

        if (p) {
            let controlsHtml = '';
            
            const smartRecHtml = `
                <div class="control-group" style="margin-right:10px;">
                    <span class="cg-label">智能推荐</span>
                    <div class="smart-switch ${isSmart?'active':''}" onclick="App.toggleSmartRec()">
                        <div class="smart-knob"></div>
                    </div>
                </div>`;

            if (p.type === '主训') {
                const rest = p.strategy?.rest || 60;
                const restRound = p.strategy?.restRound || Math.round(rest * 1.5);
                const disabledAttr = isSmart ? 'disabled style="opacity:0.5; pointer-events:none;"' : '';
                
                controlsHtml = `
                <div class="phase-controls-row">
                    ${smartRecHtml}
                    <div class="control-group" onclick="if(${isSmart}) window.App.showToast('请关闭智能推荐自定义编辑')">
                        <span class="cg-label">负荷</span>
                        <select class="phase-select" ${disabledAttr} onchange="App.updateGlobalSetting('loadStrategy', this.value)">
                            ${opts(CONSTANTS.ENUMS.LOAD_STRATEGY, settings.loadStrategy)}
                        </select>
                    </div>
                    <div class="control-group" onclick="if(${isSmart}) window.App.showToast('请关闭智能推荐自定义编辑')">
                        <span class="cg-label">模式</span>
                        <select class="phase-select" ${disabledAttr} onchange="App.updateGlobalSetting('loopMode', this.value)">${opts(CONSTANTS.ENUMS.LOOP_MODE, settings.loopMode)}</select>
                    </div>
                    <div class="control-group" onclick="if(${isSmart}) window.App.showToast('请关闭智能推荐自定义编辑')">
                        <span class="cg-label">组间</span>
                        <input type="number" class="phase-select" style="width:45px; text-align:center; padding:4px 2px;" value="${rest}" step="5" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'rest', this.value)"><span style="font-size:10px; color:#666; margin-left:-4px;">s</span>
                    </div>
                    <div class="control-group" onclick="if(${isSmart}) window.App.showToast('请关闭智能推荐自定义编辑')">
                        <span class="cg-label">轮间</span>
                        <input type="number" class="phase-select" style="width:45px; text-align:center; padding:4px 2px;" value="${restRound}" step="5" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'restRound', this.value)"><span style="font-size:10px; color:#666; margin-left:-4px;">s</span>
                    </div>
                </div>`;
            } else {
                const rest = p.strategy?.rest || 0;
                const restRound = p.strategy?.restRound || 0;
                const disabledAttr = isSmart ? 'disabled style="opacity:0.5; pointer-events:none;"' : '';
                
                controlsHtml = `
                <div class="phase-controls-row">
                    ${smartRecHtml}
                    <div class="control-group" onclick="if(${isSmart}) window.App.showToast('请关闭智能推荐自定义编辑')">
                        <span class="cg-label">组间</span>
                        <input type="number" class="phase-select" style="width:45px; text-align:center; padding:4px 2px;" value="${rest}" step="5" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'rest', this.value)"><span style="font-size:10px; color:#666; margin-left:-4px;">s</span>
                    </div>
                    <div class="control-group" onclick="if(${isSmart}) window.App.showToast('请关闭智能推荐自定义编辑')">
                        <span class="cg-label">轮间</span>
                        <input type="number" class="phase-select" style="width:45px; text-align:center; padding:4px 2px;" value="${restRound}" step="5" ${disabledAttr} onchange="App.updatePhaseParam(${pIdx}, 'restRound', this.value)"><span style="font-size:10px; color:#666; margin-left:-4px;">s</span>
                    </div>
                </div>`;
            }

            html += `
            <div class="phase-header-row" style="justify-content:flex-end; margin-bottom:10px;">
                <button class="ad-add-btn" onclick="App.addAction(${pIdx})" style="margin-top:0; width:auto; padding:6px 12px;">＋ 添加动作</button>
            </div>
            
            ${controlsHtml}
            
            <div class="action-list">`;
            
            p.actions.forEach((a, aIdx) => {
                if (!a.setDetails || a.setDetails.length !== a.sets) {
                    a.setDetails = [];
                    for(let i=0; i<a.sets; i++) {
                        a.setDetails.push({ load: a.load, reps: a.reps });
                    }
                }

                const isResistance = a.paradigm === '抗阻范式';
                const isWarmup = p.type === '热身' || p.type === '放松';
                const isTimeBased = a.paradigm === '间歇范式' || a.paradigm === '流式范式';
                const isMirror = a.mirror;
                const repUnit = isTimeBased ? 's' : '';

                const expanded = a.expanded ? 'block' : 'none';
                const arrow = a.expanded ? '▲' : '▼';
                
                const thumb = `<div class="ac-thumb"><i style="font-style:normal; font-size:16px;">📷</i></div>`;
                
                let setDetailsStr = '';
                if (a.setDetails && a.setDetails.length > 0) {
                    let vals = [];
                    let suffix = '';
                    if (isResistance && !isWarmup && !isTimeBased) {
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
                if (isResistance && !isWarmup && !isTimeBased) {
                    summary = `<span class="ac-tag" style="color:var(--primary)">${a.sets}组 x ${a.reps}</span> <span class="ac-tag">${setDetailsStr}</span>`;
                } else {
                    summary = `<span class="ac-tag" style="color:var(--primary)">${a.sets}组</span> <span class="ac-tag">${setDetailsStr}</span>`;
                }

                let setsHtml = '';
                a.setDetails.forEach((s, sIdx) => {
                    let isDisabled = isSmart;
                    if (!isSmart && !isWarmup && isResistance) {
                        const strat = settings.loadStrategy;
                        if (strat === '递增' || strat === '递减') {
                            if (sIdx > 0 && sIdx < a.setDetails.length - 1) isDisabled = true;
                        }
                    }
                    const disabledStyle = isDisabled ? 'opacity:0.5; pointer-events:none;' : '';

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
                        return (isDisabled && isSmart) ? `<div onclick="window.App.showToast('请关闭智能推荐自定义编辑')">${stepperContent(val, field)}</div>` : stepperContent(val, field);
                    };

                    const mirrorLabel = isMirror ? `<span style="font-size:10px; color:var(--primary); margin-left:4px; border:1px solid var(--primary); padding:0 2px; border-radius:2px;">双侧</span>` : '';

                    let inputs = '';
                    if (isResistance && !isWarmup && !isTimeBased) {
                        inputs = `
                            ${stepper(s.load, 'load')} <span style="color:#666;font-size:10px;">${unit}</span>
                            <span style="color:#444; margin:0 5px;">x</span>
                            ${stepper(s.reps, 'reps')} <span style="color:#666;font-size:10px;">次</span>${mirrorLabel}
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
                            <div class="set-del" style="${isSmart?'opacity:0.3;pointer-events:none':''}" onclick="App.removeSet(${pIdx}, ${aIdx}, ${sIdx})">×</div>
                        </div>
                    `;
                });

                setsHtml += `<div class="add-set-btn" onclick="App.addSet(${pIdx}, ${aIdx})">+ 加一组</div>`;
                
                html += `
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
                        </div>
                        <div class="ac-detail-link" onclick="App.openActionDetail('${a.id}', 'result')">
                            查看动作详情 >
                        </div>
                    </div>
                </div>`;
            });
            html += `</div>`;
        }

        resContent.innerHTML = html;
        App.updateStats();
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
            App.renderFineTuning(window.currentCtx);
        }
    },

    adjustSetData: (pIdx, aIdx, sIdx, field, dir) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        const set = action.setDetails[sIdx];
        const unit = window.store.unit || 'kg';
        
        let step = 1;
        if (field === 'load') step = unit === 'kg' ? 0.5 : 1;
        else if (field === 'reps') {
            const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式';
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
            let strat = window.store.courseSettings.loadStrategy;
            const isSmart = window.store.courseSettings.smartRec;
            
            action.setDetails[sIdx][field] = numVal;
            
            if (!isSmart && field === 'load') {
                // 1. Auto-detect Strategy Change based on First/Last Set
                if (sIdx === 0 || sIdx === action.setDetails.length - 1) {
                    const sets = action.setDetails.length;
                    if (sets >= 2) {
                        const firstVal = parseFloat(action.setDetails[0].load);
                        const lastVal = parseFloat(action.setDetails[sets - 1].load);
                        
                        let newStrat = strat;
                        if (firstVal === lastVal) newStrat = '恒定';
                        else if (firstVal < lastVal) newStrat = '递增';
                        else if (firstVal > lastVal) newStrat = '递减';
                        
                        if (newStrat !== strat) {
                            window.store.courseSettings.loadStrategy = newStrat;
                            strat = newStrat;
                            window.App.showToast(`策略已自动切换为: ${newStrat}`);
                        }
                    }
                }

                // 2. Apply Strategy Logic (Interpolation)
                if (strat === '恒定') {
                    action.setDetails.forEach(s => s[field] = numVal);
                } else if (strat === '递增' || strat === '递减') {
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
                const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式' || action.measure === '计时';
                if (!isTimeBased && action.paradigm === '抗阻范式') {
                    const base1RM = action.demoUser1RM || window.UserAbility.oneRM[action.part] || window.UserAbility.oneRM['全身'] || 20;
                    action.setDetails.forEach((s, idx) => {
                        if (s.load > 0) s.reps = window.Logic.calcRepsFromLoad(s.load, base1RM);
                    });
                    if (action.setDetails.length > 0) action.reps = action.setDetails[0].reps;
                }
            }
            
            if (sIdx === 0) action[field] = numVal;
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
        if (key === 'loadStrategy') App.recalculateLoadStrategy();
        App.renderFineTuning(window.currentCtx);
    },

    addSet: (pIdx, aIdx) => {
        const action = window.currentCtx.phases[pIdx].actions[aIdx];
        action.sets++;
        const lastSet = action.setDetails[action.setDetails.length-1] || { load: action.load, reps: action.reps };
        action.setDetails.push({ ...lastSet });
        
        // Re-apply strategy when adding a set
        const strat = window.store.courseSettings.loadStrategy;
        if (!window.store.courseSettings.smartRec && (strat === '递增' || strat === '递减')) {
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
             if (strat === '恒定') {
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
        document.getElementById('st-time').innerText = ctx.meta.duration + 'min';
        document.getElementById('st-count').innerText = totalActions + '个';
        document.getElementById('st-vol').innerText = totalSets + '组';
        document.getElementById('st-cal').innerText = Math.floor(4.5 * window.store.user.weight * (ctx.meta.duration/60)) + 'kcal';
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
        if (days.length === 0) return App.showToast("请至少选择一天");
        window.store.inputs.days = days;
        document.getElementById('modal-schedule').classList.remove('active');
        App.switchView('view-schedule');
    },

    deleteAction: (pIdx, aIdx) => {
        if (!window.currentCtx) return;
        App.openConfirmModal('确定要删除该动作吗？', () => {
            try {
                const p = window.currentCtx.phases[pIdx];
                if (p && p.actions) {
                    p.actions.splice(aIdx, 1);
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
    }
};