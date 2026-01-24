window.Logic = {
    createContext: (input, planContext = null) => {
        const user = window.store.user;
        // Calculate bodyStatus from fatigue (1-10) if not present
        const bodyStatus = Math.max(0, 100 - (user.fatigue * 8));
        
        // Normalize targets to Array
        const rawTargets = input ? input.targets : null;
        const targets = (Array.isArray(rawTargets) && rawTargets.length > 0) ? rawTargets : (rawTargets ? [rawTargets] : ['全身']);

        return {
            source: planContext ? 'Plan' : 'Single',
            planContext: planContext,
            meta: {
                type: planContext ? planContext.type : (input.type || '力量'),
                targets: planContext ? planContext.targets : targets,
                duration: planContext ? planContext.duration : (input ? (parseInt(input.duration) || 30) : 30), // Default 30
                level: user.level,
                goal: user.goal
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
            meta: {
                ...ctx.meta,
                level: levelStr,
                targets: finalTargets
            }
        };
    },

    planPhases: (ctx) => {
        const { duration, type } = ctx.meta;
        
        // NEW RULE: Fixed Formula T/10
        // Warmup/Cooldown Count = ceil(Total Duration / 10)
        // Each action = 30s (0.5 min)
        const wuCount = Math.ceil(duration / 10);
        const cdCount = Math.ceil(duration / 10);
        
        const wuTime = wuCount * 0.5;
        const cdTime = cdCount * 0.5;
        
        const mainTime = duration - wuTime - cdTime;
        
        // Strategy Resolution: Type (Strong) > Goal (Weak)
        let strategyKey = ctx.meta.goal; // Default to goal (e.g. 增肌)
        
        // Type Config Mapping
        const typeConfig = {
            'HIIT': { strategy: 'HIIT', filter: '心肺' },
            '有氧': { strategy: '有氧', filter: '心肺' },
            '瑜伽': { strategy: '瑜伽', filter: '柔韧' },
            '普拉提': { strategy: '普拉提', filter: '体态' },
            '拉伸': { strategy: '拉伸', filter: '恢复' }
        };

        if (typeConfig[type]) {
            strategyKey = typeConfig[type].strategy;
        }

        const mainStrategy = CONFIG.STRATEGY[strategyKey] || CONFIG.STRATEGY['增肌'];
        const wuStrategy = CONFIG.STRATEGY['激活'];
        const cdStrategy = CONFIG.STRATEGY['柔韧'];
        const paradigm = CONSTANTS.COURSE_TYPES[type] || '抗阻范式';

        // 1. Sports Science Adaptation (Level & Goal)
        const level = ctx.meta.level || 'L3';
        const scaling = CONFIG.LEVEL_SCALING[level] || CONFIG.LEVEL_SCALING['L3'];
        const goal = ctx.meta.goal;

        // A. Volume & Intensity Scaling
        let adjustedSets = Math.max(1, Math.round(mainStrategy.sets * scaling.vol));
        let adjustedIntensity = Math.min(1.0, Math.max(0.1, mainStrategy.intensity * scaling.int));
        
        // B. Rest Interval Logic (ATP-CP vs Metabolic)
        // Strength/Power: Needs 2-5min for CNS/ATP recovery.
        // Hypertrophy: Needs 60-90s for metabolic stress.
        // Endurance: Needs <45s to maintain heart rate.
        let baseRest = mainStrategy.rest;
        if (['力量', '爆发'].includes(goal)) baseRest = Math.max(120, baseRest); // Floor 2min
        else if (['增肌'].includes(goal)) baseRest = Math.max(60, Math.min(90, baseRest)); // Clamp 60-90s
        else if (['减脂', '耐力', '心肺'].includes(goal)) baseRest = Math.min(45, baseRest); // Cap 45s

        let adjustedRest = Math.round(baseRest * scaling.rest);
        
        // Flow Paradigm (Yoga/Stretch) allows 0 rest
        if (paradigm === '抗阻范式' || paradigm === '间歇范式') {
            adjustedRest = Math.max(10, adjustedRest);
        }
        let adjustedRestRound = Math.round(adjustedRest * 1.5); 

        // C. Time-Constraint Adaptation (Compression)
        if (duration <= 30) {
            adjustedRest = Math.max(15, Math.round(adjustedRest * 0.7)); // Compress rest by 30%
            adjustedRestRound = Math.round(adjustedRest * 1.5);
        }
        
        // D. Duration Estimation (TUT Based)
        // Estimate Time Under Tension (TUT) per set
        let tut = 45; // Default Hypertrophy (10 reps * 4s tempo)
        if (['力量', '爆发'].includes(goal)) tut = 20; // Low reps
        else if (['减脂', '耐力', '心肺', 'HIIT'].includes(goal)) tut = 60; // High reps/Time
        else if (paradigm === '流式范式') tut = 60; // Flow

        // Calculate cost per action: Sets * (TUT + Rest) - LastRest + RoundRest
        // Actually: (Sets * TUT) + ((Sets - 1) * Rest) + RestRound
        const actionCostSec = (adjustedSets * tut) + ((adjustedSets - 1) * adjustedRest) + adjustedRestRound;
        
        let count = Math.floor((mainTime * 60) / actionCostSec);
        
        // Ensure minimum variety (at least 3 actions if possible)
        if (count < 3 && adjustedSets > 2) {
            // Reduce sets to fit more actions
            adjustedSets--;
            const reducedCost = (adjustedSets * tut) + ((adjustedSets - 1) * adjustedRest) + adjustedRestRound;
            count = Math.floor((mainTime * 60) / reducedCost);
        }

        const phaseStrategy = { ...mainStrategy, sets: adjustedSets, rest: adjustedRest, restRound: adjustedRestRound, intensity: adjustedIntensity };
        const phaseCoeffs = ctx.planContext ? ctx.planContext.phase : { intensity:1.0, volume:1.0 };

        ctx.phases = [
            { type: '热身', duration: wuTime, paradigm: '流式范式', func: '激活', targetCount: wuCount, strategy: { ...wuStrategy, restRound: 0, sets: 1 } },
            { type: '主训', duration: mainTime, paradigm: paradigm, func: ctx.meta.goal, targetCount: Math.max(1, count), strategy: phaseStrategy, coeffs: phaseCoeffs },
            { type: '放松', duration: cdTime, paradigm: '流式范式', func: '放松', targetCount: cdCount, strategy: { ...cdStrategy, restRound: 0, sets: 1 } }
        ];
        return ctx;
    },

    selectActions: (ctx) => {
        const { constraints, meta } = ctx;
        const user = window.store.user;
        const isHeavy = (user.bmi >= 28 && user.level !== 'L5');
        const isMain = (p) => p.type === '主训';

        // Ensure DB is populated
        if (DB.length === 0) DB = FALLBACK_DB;

        const calculateScore = (a, dominantEquip) => {
            let score = 100 + Math.random() * 15;
            const daysSince = (new Date() - a.lastTrained) / (1000 * 3600 * 24);
            if (daysSince > 7) score += 60;
            if (a.isFav) score += 50;
            if (a.difficulty === meta.level) score += 30;
            else if (Math.abs(CONSTANTS.LEVEL_MAP[a.difficulty] - CONSTANTS.LEVEL_MAP[meta.level]) === 1) score += 10;
            else score -= 20;

            // NEW: Equipment Consistency Bonus
            if (dominantEquip && a.equip.includes(dominantEquip)) score += 20;
            
            // NEW: Slot Weight Priority (Simplified: Compound > Isolation)
            if (a.construct === '复合动作') score += 10;

            return { ...a, score };
        };
        
        ctx.phases.forEach(p => {
            // NEW: Phase-level Equipment Tracker (Reset per phase)
            const phaseEquipCounts = {};

            // 0. Safety Filter (Global Constraint - Always Active)
            let pool = DB.filter(a => {
                if (a.equip && a.equip.some(e => !constraints.availableEquip.includes(e))) return false;
                if (a.pain && a.pain.some(pt => constraints.forbiddenParts.includes(pt))) return false;
                if (isHeavy && a.impact === '高冲击') return false;
                if (constraints.downgrade && a.impact === '高冲击') return false;
                return true;
            });

            // Helper: Search with criteria (Supports Relaxation)
            const search = (criteria) => {
                // Determine dominant equipment so far
                let dominantEquip = null;
                let maxEqCount = -1;
                for(let eq in phaseEquipCounts) {
                    if(phaseEquipCounts[eq] > maxEqCount) { maxEqCount = phaseEquipCounts[eq]; dominantEquip = eq; }
                }

                return pool.filter(a => {
                    // Paradigm Check (Strict)
                    const actionParadigm = CONSTANTS.COURSE_TYPES[a.courseType];
                    if (actionParadigm !== p.paradigm) {
                        // Allow Interval actions (like Jumping Jacks) in Flow phases (Warmup/Cooldown)
                        if (!isMain(p) && p.paradigm === '流式范式' && actionParadigm === '间歇范式') {
                            // Pass
                        } else {
                            return false;
                        }
                    }
                    
                    // Part Check
                    if (isMain(p)) {
                        // Main: Must match target parts (or Full Body)
                        // Fallback Level 4 (Keep Skeleton) implies we stick to this.
                        const matchPart = ctx.meta.targets.includes('全身') || ctx.meta.targets.includes(a.part);
                        if (!matchPart) return false;
                    }
                    
                    // Function Check (Relaxable)
                    if (criteria.checkFunc) {
                        if (isMain(p)) {
                            // For main, usually we don't strictly filter by func unless specified, 
                            // but let's assume we prefer the phase function (e.g. Hypertrophy)
                            if (p.func && !a.func.includes(p.func)) return false;
                        } else {
                            // Warmup/Cooldown: Strict function
                            if (!a.func.includes(p.func)) return false;
                        }
                    }

                    // Difficulty Check (Relaxable)
                    if (criteria.checkDiff) {
                        const diffVal = CONSTANTS.LEVEL_MAP[a.difficulty];
                        const userVal = CONSTANTS.LEVEL_MAP[meta.level];
                        if (Math.abs(diffVal - userVal) > 1) return false;
                    }

                    // NEW: Variation Exclusion
                    const getCoreName = (n) => n.replace(/哑铃|杠铃|器械|绳索|自重|史密斯|坐姿|站姿|俯身|上斜|下斜/g, '').trim();
                    const coreName = getCoreName(a.name);
                    const hasVariation = selected.some(s => {
                        const sCore = getCoreName(s.name);
                        const nameMatch = (sCore === coreName || s.name.includes(coreName) || coreName.includes(s.name));
                        // Rule: Exclude if same action core but different equipment (e.g. DB Bench vs Barbell Bench)
                        return nameMatch && s.equip[0] !== a.equip[0];
                    });
                    if (hasVariation) return false;

                    // NEW: Bodyweight Consecutive Exclusion
                    if (a.equip[0] === '自重' && selected.length > 0) {
                        const last = selected[selected.length - 1];
                        if (last.equip[0] === '自重') {
                             if (last.name === a.name || last.name.includes(a.name) || a.name.includes(last.name)) return false;
                        }
                    }

                    return true;
                }).map(a => calculateScore(a, dominantEquip)).sort((a,b) => b.score - a.score);
            };

            let selected = [];
            const usedIds = new Set();
            const needed = p.targetCount;

            // 1. Level 0: Strict Search
            let candidates = search({ checkFunc: true, checkDiff: true });

            // Selection Loop (Top-K Random)
            const pick = (sourceList) => {
                while(selected.length < needed && sourceList.length > 0) {
                    const pickRange = Math.min(sourceList.length, 3);
                    const randomIdx = Math.floor(Math.random() * pickRange);
                    const picked = sourceList[randomIdx];
                    if (!usedIds.has(picked.id)) {
                        selected.push(picked);
                        usedIds.add(picked.id);
                        // Update Session Equip Counts
                        const eq = picked.equip[0];
                        phaseEquipCounts[eq] = (phaseEquipCounts[eq] || 0) + 1;
                    }
                    sourceList.splice(randomIdx, 1);
                }
            };
            pick(candidates);

            // 2. Level 2: Relax Difficulty (Skip L1 Expand Scope as we use Part directly)
            if (selected.length < needed) {
                candidates = search({ checkFunc: true, checkDiff: false }).filter(a => !usedIds.has(a.id));
                pick(candidates);
            }

            // 3. Level 3: Change Nature (Relax Function)
            if (selected.length < needed) {
                candidates = search({ checkFunc: false, checkDiff: false }).filter(a => !usedIds.has(a.id));
                pick(candidates);
            }

            // FIX: 4. Force Fill / Recycle to meet targetCount -> Merge Sets
            if (selected.length > 0 && selected.length < needed) {
                let missing = needed - selected.length;
                let i = 0;
                while (missing > 0) {
                    // Add set to existing actions in round-robin
                    const targetAction = selected[i % selected.length];
                    if (!targetAction.extraSets) targetAction.extraSets = 0;
                    targetAction.extraSets += 1;
                    missing--;
                    i++;
                }
            }

            // 3. 序列编排 (Sequence Arrangement) - 核心逻辑优化
            // 体能分配：复合动作 > 孤立动作 (仅针对抗阻主训)
            if (p.type === '主训' && p.paradigm === '抗阻范式') {
                selected.sort((a, b) => {
                    const scoreA = (a.construct === '复合' ? 1 : 0);
                    const scoreB = (b.construct === '复合' ? 1 : 0);
                    return scoreB - scoreA; // 复合动作排前面
                });
            }

            p.actions = selected;
        });
        return ctx;
    },

    instantiate: (ctx) => {
        const globalStrategy = window.store.courseSettings.loadStrategy;
        
        ctx.phases.forEach(phase => {
            const { strategy, coeffs } = phase;
            const iCoeff = coeffs ? coeffs.intensity : 1.0;
            const vCoeff = coeffs ? coeffs.volume : 1.0;

            phase.actions = phase.actions.map(a => {
                const actionParadigm = CONSTANTS.COURSE_TYPES[a.courseType];

                // 1. 计算模式判定 (Calculation Mode Judgment)
                // 负荷优先模式：抗阻范式 (关注重量)
                // 容量优先模式：间歇/流式范式 (关注时长/次数)
                const isCapacityPriority = (phase.paradigm === '间歇范式' || phase.paradigm === '流式范式' || globalStrategy === '计时');
                const isLoadPriority = !isCapacityPriority;

                // 2. 基准参数计算
                // 组数：优先使用 selectActions 中 Gap Filling 调整后的组数
                let algoSets = a.sets || Math.round(strategy.sets * vCoeff);
                if (a.extraSets) algoSets += a.extraSets;

                // FIX: Enforce Smart Rec (Reset to algo sets if smart mode is ON)
                let sets = algoSets;
                if (!window.store.courseSettings.smartRec && a.sets) {
                    sets = a.sets;
                }
                
                let intensity = strategy.intensity * iCoeff;
                let load = 0;
                let reps = '12';
                let rpe = strategy.rpe || 8;
                let base1RM = 20; // Default fallback

                if (isLoadPriority) {
                    // 模式 A：负荷优先 (定重量 -> 定次数)
                    base1RM = a.demoUser1RM || window.UserAbility.oneRM[a.part] || window.UserAbility.oneRM['全身'] || 20; // Use dynamic 1RM
                    load = Math.round(base1RM * intensity);
                    
                    // Scientific Reps Mapping (NSCA/ACSM Guidelines)
                    // >85% 1RM -> <6 Reps (Strength)
                    // 67-85% 1RM -> 6-12 Reps (Hypertrophy)
                    // <67% 1RM -> >12 Reps (Endurance)
                    let theoReps = 10;
                    if (intensity >= 0.95) theoReps = 2;
                    else if (intensity >= 0.90) theoReps = 4;
                    else if (intensity >= 0.85) theoReps = 6;
                    else if (intensity >= 0.80) theoReps = 8;
                    else if (intensity >= 0.75) theoReps = 10;
                    else if (intensity >= 0.65) theoReps = 12;
                    else theoReps = 15;

                    // RPE 修正
                    reps = Math.max(1, theoReps - (10 - rpe)).toString();
                } else {
                    // 模式 B：容量优先 (定容量 -> 定重量)
                    // 强度系数作用于速度/频率(由教练口令控制)，时长保持与规划层一致(60s)以确保总时长准确
                    reps = (phase.paradigm === '间歇范式') ? '60' : '30';
                    if (phase.type === '热身' || phase.type === '放松') reps = '30';
                }

                // FIX: Preserve existing setDetails if Smart Rec is OFF (Manual Mode)
                // This ensures manual edits are not overwritten by global refreshes (e.g. Replace Action)
                if (!window.store.courseSettings.smartRec && a.setDetails && a.setDetails.length === sets) {
                    return a;
                }

                // Apply Load Strategy (Pyramid etc)
                let setDetails = [];
                let activeStrategy;
                if (window.store.courseSettings.smartRec) {
                    activeStrategy = strategy.strategy; // Use recommended strategy
                } else {
                    activeStrategy = globalStrategy; // Use manual strategy
                }
                if (activeStrategy === '推荐') activeStrategy = '递增'; // Fallback mapping if recommendation is generic

                for(let i=0; i<sets; i++) {
                    let sLoad = load;
                    let sReps = parseInt(reps);
                    // 仅在负荷优先模式下应用金字塔策略
                    if (isLoadPriority) {
                        if (activeStrategy === '递增') {
                            if (i === 0) { sLoad = Math.round(load * 0.85); sReps += 2; }
                            else if (i === 1) { sLoad = Math.round(load * 0.90); sReps += 1; }
                        } else if (activeStrategy === '递减') {
                            if (i === 1) { sLoad = Math.round(load * 0.90); sReps += 2; }
                            else if (i >= 2) { sLoad = Math.round(load * 0.80); sReps += 4; }
                        }
                    }
                    setDetails.push({ load: sLoad, reps: sReps });
                }

                return {
                    ...a,
                    paradigm: actionParadigm,
                    mirror: a.mirror || (a.name && (a.name.includes('单') || a.name.includes('哑铃') || a.name.includes('侧'))),
                    base1RM,
                    sets,
                    reps,
                    load,
                    setDetails,
                    forceMode: strategy.forceMode || '恒力',
                    intensity: Math.round(intensity*100)+'%',
                    rpe
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
        const ctx = window.Logic.runPipeline(input, null);
        return ctx;
    },

    genPlan: (input) => {
        const weeks = parseInt(input.cycle) || 4;
        const userDays = input.days || [];
        const dayMap = {'周一':1, '周二':2, '周三':3, '周四':4, '周五':5, '周六':6, '周日':7};
        const dayNums = userDays.map(d => dayMap[d]).sort();
        const freq = Math.min(Math.max(userDays.length, 1), 7); // Ensure freq is within 1-7
        
        // 1. Select Template based on Frequency & Goal
        // Match Goal AND Gender if specified (e.g. TPL_003 vs TPL_004)
        let template = CONFIG.TEMPLATES.find(t => 
            t.freq === freq && 
            t.goal === window.store.user.goal &&
            (!t.gender || t.gender === window.store.user.gender)
        );
        // Fallback to frequency match only if specific goal/gender match fails
        if (!template) template = CONFIG.TEMPLATES.find(t => t.freq === freq) || CONFIG.TEMPLATES[0]; // Default to first if no freq match (unlikely with 1-5 covered)

        // 2. Select Periodization Model based on User Level
        // Decoupled from user level, default to Linear
        const pModel = input.periodization || '线性周期';
        const phaseSchedule = window.PhaseEngine.generateSchedule(weeks, pModel);
        const schedule = [];
        
        // Map template slots to days
        let slotIdx = 0;
        const dayStrategy = {};
        dayNums.forEach(d => {
            const slotObj = template.slots[slotIdx % template.slots.length];
            // Slot is array of targets e.g. ['全身']
            dayStrategy[d] = { f: slotObj.t, t: slotObj.n }; 
            slotIdx++;
        });
        
        for(let w=1; w<=weeks; w++) {
            const pParams = phaseSchedule[w-1];
            const weekData = {
                week: w,
                phase: pParams.name,
                intensity: pParams.intensity,
                volume: pParams.volume || 1.0, // 修复：透传容量系数，支持线性/波浪周期
                days: []
            };
            
            for(let d=1; d<=7; d++) {
                const s = dayStrategy[d];
                const dayName = ['周一','周二','周三','周四','周五','周六','周日'][d-1];
                if(s) {
                    weekData.days.push({ dayName, isTraining: true, targets: s.f, title: s.t });
                } else {
                    weekData.days.push({ dayName, isTraining: false });
                }
            }
            schedule.push(weekData);
        }
        return { meta: input, schedule };
    },

    // Node 8: 反馈闭环 (Feedback Loop)
    completeTraining: (ctx) => {
        // 1. Update Fatigue (Mock: Reduce status)
        window.store.user.fatigue = Math.min(10, window.store.user.fatigue + 2);
        window.store.calcMetrics(); // Update UI (Requires App to expose this or Logic to call App)
        // Note: Logic shouldn't depend on App UI methods directly ideally, but for demo simplicity:
        if(window.App && window.App.renderProfile) window.App.renderProfile();

        // 2. Update 1RM (Mock: Based on last set of main actions)
        let prCount = 0;
        ctx.phases.forEach(p => {
            if (p.type === '主训' && p.paradigm === '抗阻范式') {
                p.actions.forEach(a => {
                    // Assume user completed the last set successfully
                    const lastSet = a.setDetails[a.setDetails.length-1];
                    if (lastSet && lastSet.load > 0) {
                        if (window.UserAbility.update(a.part, lastSet.load, lastSet.reps)) prCount++;
                    }
                });
            }
        });

        return { prCount };
    },

    // Helper: Calculate Reps from Load based on 1RM
    calcRepsFromLoad: (load, oneRM) => {
        if (!oneRM || oneRM <= 0) return 12;
        const intensity = load / oneRM;
        // Simple table lookup for Demo
        if (intensity >= 1.0) return 1;
        if (intensity >= 0.95) return 2;
        if (intensity >= 0.90) return 4;
        if (intensity >= 0.85) return 6;
        if (intensity >= 0.80) return 8;
        if (intensity >= 0.75) return 10;
        if (intensity >= 0.70) return 12;
        if (intensity >= 0.60) return 15;
        return 20;
    },

    // --- Real-time Update Helpers ---

    updateActionLoad: (action, setIdx, newLoad, strategy) => {
        newLoad = Number(newLoad) || 0; // 强制转为数字，防止输入框字符串导致计算错误
        const sets = action.setDetails;
        const oneRM = action.base1RM || 20;
        const normStrategy = (strategy === '推荐') ? '递增' : strategy; // 策略归一化：推荐默认走递增逻辑
        
        // 1. Update specific set
        sets[setIdx].load = newLoad;
        sets[setIdx].reps = window.Logic.calcRepsFromLoad(newLoad, oneRM);
        
        // 2. Update Base Load & Propagate based on Strategy
        let baseLoad = newLoad;
        
        if (normStrategy === '递增') {
            // Logic: Set 0 (85%), Set 1 (90%), Set 2+ (100%)
            if (setIdx === 0) baseLoad = newLoad / 0.85;
            else if (setIdx === 1) baseLoad = newLoad / 0.90;
            else baseLoad = newLoad;
            
            sets.forEach((s, i) => {
                if (i === setIdx) return; // Skip trigger set
                let factor = 1.0;
                if (i === 0) factor = 0.85;
                else if (i === 1) factor = 0.90;
                s.load = Math.round(baseLoad * factor);
                s.reps = window.Logic.calcRepsFromLoad(s.load, oneRM);
            });
        } else if (normStrategy === '递减') {
            // Logic: Set 0 (100%), Set 1 (90%), Set 2+ (80%)
            if (setIdx === 0) baseLoad = newLoad;
            else if (setIdx === 1) baseLoad = newLoad / 0.90;
            else baseLoad = newLoad / 0.80;
            
            sets.forEach((s, i) => {
                if (i === setIdx) return;
                let factor = 1.0;
                if (i === 1) factor = 0.90;
                else if (i >= 2) factor = 0.80;
                s.load = Math.round(baseLoad * factor);
                s.reps = window.Logic.calcRepsFromLoad(s.load, oneRM);
            });
        } else {
            // '恒定' 或其他未知策略：默认同步所有组重量 (Sync all sets)
            baseLoad = newLoad;
            sets.forEach((s, i) => {
                if (i === setIdx) return;
                s.load = newLoad;
                s.reps = window.Logic.calcRepsFromLoad(s.load, oneRM);
            });
        }
        
        action.load = Math.round(baseLoad); // Update action base load
        return action;
    },

    updateActionReps: (action, setIdx, newReps) => {
        action.setDetails[setIdx].reps = newReps;
        return action;
    },

    recalcActionStrategy: (action, strategy) => {
        // Recalculate all sets based on current base load (action.load) and new strategy
        const sets = action.setDetails;
        const oneRM = action.base1RM || 20;
        const baseLoad = action.load;
        const normStrategy = (strategy === '推荐') ? '递增' : strategy;
        
        sets.forEach((s, i) => {
            let factor = 1.0;
            if (normStrategy === '递增') {
                if (i === 0) factor = 0.85;
                else if (i === 1) factor = 0.90;
            } else if (normStrategy === '递减') {
                if (i === 1) factor = 0.90;
                else if (i >= 2) factor = 0.80;
            }
            s.load = Math.round(baseLoad * factor);
            s.reps = window.Logic.calcRepsFromLoad(s.load, oneRM);
        });
        return action;
    },

    addActionSet: (action, strategy) => {
        const setIdx = action.setDetails.length;
        const oneRM = action.base1RM || 20;
        const baseLoad = action.load;
        const normStrategy = (strategy === '推荐') ? '递增' : strategy;
        
        let factor = 1.0;
        if (normStrategy === '递增') {
            if (setIdx === 0) factor = 0.85;
            else if (setIdx === 1) factor = 0.90;
        } else if (normStrategy === '递减') {
            if (setIdx === 1) factor = 0.90;
            else if (setIdx >= 2) factor = 0.80;
        }
        
        const load = Math.round(baseLoad * factor);
        const reps = window.Logic.calcRepsFromLoad(load, oneRM);
        
        action.setDetails.push({ load, reps });
        return action;
    }
};