// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\core\logic.js

window.Logic = {
    createContext: (input, planContext = null) => {
        const user = window.store.user;
        const bodyStatus = Math.max(0, 100 - (user.fatigue * 8));
        const rawTargets = input ? input.targets : null;
        const targets = (Array.isArray(rawTargets) && rawTargets.length > 0) ? rawTargets : (rawTargets ? [rawTargets] : ['全身']);

        return {
            source: planContext ? 'Plan' : 'Single',
            planContext: planContext,
            meta: {
                type: planContext ? planContext.type : (input.type || '力量'),
                targets: planContext ? planContext.targets : targets,
                duration: planContext ? planContext.duration : (input ? (parseInt(input.duration) || 30) : 30),
                level: user.level,
                goal: user.goal,
                gender: user.gender
            },
            constraints: { 
                availableEquip: ['自重', '横杆', '手柄', '健身凳', '泡沫轴'].filter(e => !user.missing.includes(e)),
                forbiddenParts: [...user.pain],
                downgrade: bodyStatus < 55
            },
            phases: [],
            status: { fatigue: bodyStatus }
        };
    },

    confirmCourse: (ctx) => {
        const user = window.store.user;
        let finalTargets = [...ctx.meta.targets];
        const conflict = finalTargets.some(t => ctx.constraints.forbiddenParts.includes(t));
        
        if (conflict) {
            if (ctx.source === 'Plan') finalTargets = ['全身']; 
            else ctx.constraints.downgrade = true;
        }

        let levelStr = user.level;
        if (ctx.constraints.downgrade) {
            const currentLvl = CONSTANTS.LEVEL_MAP[levelStr];
            const newLvl = Math.max(1, currentLvl - 2);
            levelStr = `L${newLvl}`;
        }

        return {
            ...ctx,
            meta: { ...ctx.meta, level: levelStr, targets: finalTargets }
        };
    },

    planPhases: (ctx) => {
        const { duration, type, goal, level } = ctx.meta;
        
        // 1. 查找策略矩阵 (Strategy Matrix Lookup)
        // 优先匹配 Goal + Level
        let strategy = CONFIG.STRATEGY.find(s => s.target === goal && s.level.includes(level));
        // 兜底：匹配 Goal + All
        if (!strategy) strategy = CONFIG.STRATEGY.find(s => s.target === goal && s.level.includes('All'));
        // 最终兜底
        if (!strategy) strategy = CONFIG.STRATEGY[0];

        // 2. 结构规划 (Structure Planning)
        const structWarmup = CONFIG.STRUCTURE.find(s => s.type === '热身');
        const structRelax = CONFIG.STRUCTURE.find(s => s.type === '放松');
        
        const wuTime = Math.min(structWarmup.max, Math.ceil(duration * structWarmup.ratio));
        const cdTime = Math.min(structRelax.max, Math.ceil(duration * structRelax.ratio));
        const mainTime = duration - wuTime - cdTime;

        // 3. 范式适配 (Paradigm Adaptation)
        const paradigmConfig = CONFIG.PARADIGMS.find(p => p.types.includes(type)) || CONFIG.PARADIGMS[0];
        const paradigmName = paradigmConfig.name;

        // 4. 构建环节 (Build Phases)
        const phaseCoeffs = ctx.planContext ? ctx.planContext.phase : { intensity:1.0, volume:1.0 };
        
        // 主训参数修正
        const mainSets = Math.round(strategy.sets * phaseCoeffs.volume);
        const mainIntensity = strategy.intensity * phaseCoeffs.intensity;

        ctx.phases = [
            { 
                type: '热身', 
                duration: wuTime, 
                paradigm: '流式范式', 
                targetCount: Math.min(structWarmup.count, Math.ceil(wuTime / 1.0)), // 假设1min/动作
                strategy: { sets: 1, rest: 0, intensity: 0.4, loadStrategy: '计时' } 
            },
            { 
                type: '主训', 
                duration: mainTime, 
                paradigm: paradigmName, 
                targetCount: 99, // 稍后计算
                strategy: { 
                    ...strategy, 
                    sets: mainSets, 
                    intensity: mainIntensity,
                    loadStrategy: strategy.strategy // Map '推荐' etc.
                },
                coeffs: phaseCoeffs
            },
            { 
                type: '放松', 
                duration: cdTime, 
                paradigm: '流式范式', 
                targetCount: Math.min(structRelax.count, Math.ceil(cdTime / 1.0)),
                strategy: { sets: 1, rest: 0, intensity: 0.3, loadStrategy: '计时' } 
            }
        ];

        // 5. 计算主训动作数量 (Capacity Calculation)
        const mainPhase = ctx.phases[1];
        let singleActionTime = 0;
        if (paradigmName === '间歇范式') singleActionTime = 60 + (mainPhase.strategy.rest || 30);
        else if (paradigmName === '流式范式') singleActionTime = 60;
        else singleActionTime = (mainSets * 45) + ((mainSets - 1) * (mainPhase.strategy.rest || 60)); // 抗阻估算

        mainPhase.targetCount = Math.max(1, Math.floor((mainTime * 60) / singleActionTime));

        return ctx;
    },

    selectActions: (ctx) => {
        const { constraints, meta } = ctx;
        if (DB.length === 0) DB = FALLBACK_DB;

        ctx.phases.forEach(p => {
            // 1. 寻找环节模板 (Segment Template Lookup)
            // 匹配优先级: [部位+等级] > [部位] > [功能+等级] > [功能]
            let tpl = null;
            const targetPart = meta.targets[0]; // 主要部位
            
            // 尝试匹配部位模板
            tpl = CONFIG.SEGMENT_TEMPLATES.find(t => 
                t.type === p.type && 
                t.dim === '部位' && 
                t.target === targetPart && 
                (t.levels.includes(meta.level) || t.levels.includes('All'))
            );

            // 尝试匹配功能模板 (如HIIT)
            if (!tpl && p.type === '主训') {
                tpl = CONFIG.SEGMENT_TEMPLATES.find(t => 
                    t.type === '主训' && 
                    t.dim === '动作功能' && 
                    t.target === meta.goal && // e.g. 减脂 -> 心肺
                    (t.levels.includes(meta.level) || t.levels.includes('All'))
                );
            }

            // 兜底模板
            if (!tpl) {
                // 构造通用模板
                if (p.type === '热身') tpl = CONFIG.SEGMENT_TEMPLATES.find(t => t.id === 'TPL_SEG_001'); // 全身热身
                else if (p.type === '放松') tpl = CONFIG.SEGMENT_TEMPLATES.find(t => t.id === 'TPL_SEG_011'); // 全身放松
                else tpl = CONFIG.SEGMENT_TEMPLATES.find(t => t.id === 'TPL_SEG_021'); // 全身初级主训
            }

            p.template = tpl; // 保存引用

            // 2. 槽位填充 (Slot Filling)
            let selected = [];
            const usedIds = new Set();
            const totalSlots = p.targetCount;
            
            // 分配槽位数量
            const slotsConfig = tpl ? tpl.slots : [{focusDim:'动作构造', focusTarget:'复合动作', w:1.0}];
            
            slotsConfig.forEach(slot => {
                const count = Math.round(totalSlots * slot.w);
                if (count <= 0) return;

                // 筛选候选池
                let candidates = DB.filter(a => {
                    // 硬性风控
                    if (a.equip && a.equip.some(e => !constraints.availableEquip.includes(e))) return false;
                    if (a.pain && a.pain.some(pt => constraints.forbiddenParts.includes(pt))) return false;
                    if (constraints.downgrade && a.impact === '高冲击') return false;
                    if (usedIds.has(a.id)) return false;

                    // 槽位匹配
                    if (slot.focusDim === '部位' && a.part !== slot.focusTarget) return false;
                    if (slot.focusDim === '动作模式' && a.mode !== slot.focusTarget) return false;
                    if (slot.focusDim === '动作功能' && (!a.func || !a.func.includes(slot.focusTarget))) return false;
                    if (slot.focusDim === '动作构造' && a.construct !== slot.focusTarget) return false;
                    if (slot.focusDim === '主动肌' && a.muscle !== slot.focusTarget) return false;

                    // 环节类型匹配 (热身只选热身动作)
                    // if (p.type === '热身' && !a.func.includes('激活')) return false; // 宽松一点

                    return true;
                });

                // 评分排序
                candidates.forEach(a => {
                    a.score = 100 + Math.random() * 20;
                    if (a.difficulty === meta.level) a.score += 30;
                });
                candidates.sort((a,b) => b.score - a.score);

                // 选取
                for(let i=0; i<count && i<candidates.length; i++) {
                    selected.push(candidates[i]);
                    usedIds.add(candidates[i].id);
                }
            });

            // 3. 补齐 (Fill Gaps)
            if (selected.length < totalSlots) {
                const needed = totalSlots - selected.length;
                const leftovers = DB.filter(a => !usedIds.has(a.id) && a.part === targetPart).slice(0, needed);
                selected = selected.concat(leftovers);
            }

            // 4. 排序 (Sorting)
            if (tpl && tpl.sort) {
                selected.sort((a, b) => {
                    for (const rule of tpl.sort) {
                        const res = window.Logic.compareActions(a, b, rule);
                        if (res !== 0) return res;
                    }
                    return 0;
                });
            }

            p.actions = selected;
        });
        return ctx;
    },

    compareActions: (a, b, rule) => {
        const { dim, order, seq } = rule;
        const getVal = (action, dimension) => {
            if (dimension === '动作构造') return action.construct;
            if (dimension === '动作模式') return action.mode;
            if (dimension === '主动肌') return action.muscle;
            if (dimension === '主要配件') return action.equip ? action.equip[0] : '';
            if (dimension === '动作体位') return action.posture;
            if (dimension === '动作难度') return CONSTANTS.LEVEL_MAP[action.difficulty] || 0;
            if (dimension === 'MET值') return action.met || 0;
            if (dimension === '推荐权重') return action.score || 0;
            return 0;
        };

        const valA = getVal(a, dim);
        const valB = getVal(b, dim);

        if (order === '升序') return valA < valB ? -1 : (valA > valB ? 1 : 0);
        if (order === '降序') return valA > valB ? -1 : (valA < valB ? 1 : 0);
        if (order === '自定义') {
            const sequence = seq ? seq.split(',').map(s => s.trim()) : [];
            const idxA = sequence.indexOf(valA);
            const idxB = sequence.indexOf(valB);
            return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
        }
        return 0;
    },

    instantiate: (ctx) => {
        ctx.phases.forEach(phase => {
            const { strategy, coeffs } = phase;
            const iCoeff = coeffs ? coeffs.intensity : 1.0;
            const vCoeff = coeffs ? coeffs.volume : 1.0;

            phase.actions = phase.actions.map(a => {
                const actionParadigm = CONSTANTS.COURSE_TYPES[a.courseType] || '抗阻范式';
                const isLoadPriority = actionParadigm === '抗阻范式' && a.measure !== '计时';

                let sets = Math.round(strategy.sets * vCoeff) || 3;
                let intensity = strategy.intensity * iCoeff;
                let load = 0;
                let reps = '12';
                let base1RM = 20;

                if (isLoadPriority) {
                    if (a.powerModule === '是') {
                        base1RM = a.demoUser1RM || window.UserAbility.oneRM[a.part] || 20;
                        load = Math.round(base1RM * intensity);
                        // 简单RM反推
                        if (intensity >= 0.85) reps = '6';
                        else if (intensity >= 0.75) reps = '10';
                        else reps = '12';
                    } else {
                        reps = '12';
                    }
                } else {
                    reps = (phase.paradigm === '间歇范式') ? '60' : '30';
                }

                // 生成组序列
                let algoSetDetails = [];
                const loadStrat = strategy.loadStrategy || '推荐';
                const stratConfig = CONFIG.LOAD_STRATEGIES.filter(s => s.name === (loadStrat==='推荐'?'递增':loadStrat));

                for(let i=0; i<sets; i++) {
                    let sLoad = load;
                    // 查找对应组的策略配置
                    const rule = stratConfig.find(s => s.index === (i+1).toString()) || stratConfig.find(s => s.index === '3+' || s.index === 'All');
                    
                    if (rule && isLoadPriority) {
                        sLoad = Math.round(load * rule.coeff * 2) / 2;
                    }
                    algoSetDetails.push({ load: sLoad, reps: parseInt(reps) });
                }

                return {
                    ...a,
                    paradigm: actionParadigm,
                    sets,
                    reps,
                    load,
                    setDetails: algoSetDetails,
                    recommendedSetDetails: JSON.parse(JSON.stringify(algoSetDetails)),
                    intensity: Math.round(intensity*100)+'%'
                };
            });
        });
        return ctx;
    },

    runPipeline: (input, planContext) => {
        let ctx = window.Logic.createContext(input, planContext);
        ctx = window.Logic.confirmCourse(ctx);
        ctx = window.Logic.planPhases(ctx);
        ctx = window.Logic.selectActions(ctx);
        ctx = window.Logic.instantiate(ctx);
        return ctx;
    },

    genCourse: (input) => {
        return window.Logic.runPipeline(input, null);
    },

    genPlan: (input) => {
        const weeks = parseInt(input.cycle) || 4;
        const userDays = input.days || [];
        const freq = Math.min(Math.max(userDays.length, 1), 7);
        
        // 1. 匹配计划模板 (Plan Template)
        let template = CONFIG.PLAN_TEMPLATES.find(t => 
            t.freq === freq && 
            t.goal === window.store.user.goal
        );
        if (!template) template = CONFIG.PLAN_TEMPLATES[0];

        // 2. 周期策略 (Phase Strategy)
        let cycleKey = '>4周';
        if (weeks <= 4) cycleKey = weeks + '周';
        const phaseStrat = CONFIG.PHASE_STRATEGIES.find(s => s.cycle === cycleKey) || CONFIG.PHASE_STRATEGIES[3];

        const schedule = [];
        let currentWeek = 1;

        // 3. 生成日程
        phaseStrat.structure.forEach((pName, pIdx) => {
            const allocRatio = phaseStrat.alloc[pIdx];
            const pWeeks = Math.max(1, Math.round(weeks * allocRatio));
            
            // 查找阶段系数 (Mock: 简单映射)
            let pIntensity = 1.0, pVolume = 1.0;
            if (pName === '适应期') { pIntensity=0.8; pVolume=0.8; }
            else if (pName === '突破期') { pIntensity=1.1; pVolume=0.9; }
            else if (pName === '减载期') { pIntensity=0.6; pVolume=0.6; }

            for(let w=0; w<pWeeks && currentWeek<=weeks; w++) {
                const weekData = {
                    week: currentWeek,
                    phase: pName,
                    intensity: pIntensity,
                    volume: pVolume,
                    days: []
                };

                // 填充每日
                const dayMap = {'周一':1, '周二':2, '周三':3, '周四':4, '周五':5, '周六':6, '周日':7};
                for(let d=1; d<=7; d++) {
                    const dayName = CONSTANTS.WEEKDAYS[d-1];
                    const isTrainingDay = userDays.includes(dayName);
                    
                    if (isTrainingDay) {
                        // 简单轮询槽位
                        const slotIdx = (d - 1) % template.basicSlots.length;
                        const slot = template.basicSlots[slotIdx];
                        weekData.days.push({ 
                            dayName, 
                            isTraining: true, 
                            targets: [slot.focusTarget], // 简化：直接取目标
                            title: slot.name 
                        });
                    } else {
                        weekData.days.push({ dayName, isTraining: false });
                    }
                }
                schedule.push(weekData);
                currentWeek++;
            }
        });

        return { meta: input, schedule };
    },

    completeTraining: (ctx) => {
        // Mock Feedback
        window.store.user.fatigue = Math.min(10, window.store.user.fatigue + 2);
        return { prCount: 0 };
    },

    calcRepsFromLoad: (load, oneRM) => {
        if (!oneRM) return 12;
        const pct = load / oneRM;
        if (pct >= 0.9) return 4;
        if (pct >= 0.8) return 8;
        if (pct >= 0.7) return 12;
        return 15;
    }
};
