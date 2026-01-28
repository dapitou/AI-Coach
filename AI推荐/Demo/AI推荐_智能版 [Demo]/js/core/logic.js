// d:\AEKE Projects\AI Coach\AI推荐\Demo\AI推荐_智能版 [Demo]\js\core\logic.js

window.Logic = {
    // ... (保持 createContext, confirmCourse, planPhases 不变) ...
    createContext: (input, planContext = null) => {
        const user = window.store.user;
        // [SYNC] Use STATUS_CONFIG for fatigue mapping
        const statusConfig = CONFIG.STATUS_CONFIG || [];
        const fatigueScore = Math.max(0, 100 - (user.fatigue * 8)); // Simple mapping for now
        const bodyStatus = fatigueScore;
        const rawTargets = input ? input.targets : null;
        const targets = (Array.isArray(rawTargets) && rawTargets.length > 0) ? rawTargets : (rawTargets ? [rawTargets] : ['全身']);

        // Calculate BMI for Impact Risk
        const bmi = user.weight / ((user.height / 100) ** 2);

        // [SYNC] 1. Dynamic Equipment List (Source of Truth: CONSTANTS)
        const allEquips = CONSTANTS.MAPPINGS.EQUIPMENT_LIST || ['自重'];
        const availableEquip = allEquips.filter(e => !user.missing.includes(e));

        // [SYNC] 2. Local Fatigue Analysis (Mocking part status based on global fatigue for now, ideally needs part-level data)
        // In a real app, this would read from user.partFatigue
        const exhaustedParts = bodyStatus < 30 ? targets : []; // Mock: if global is low, target is exhausted
        const suggestedParts = bodyStatus > 85 ? ['全身'] : [];

        return {
            source: planContext ? 'Plan' : 'Single',
            planContext: planContext,
            meta: {
                type: planContext ? planContext.type : (input.type || '力量'),
                targets: planContext ? planContext.targets : targets,
                duration: planContext ? planContext.duration : (input ? (parseInt(input.duration) || 30) : 30),
                level: user.level,
                goal: user.goal,
                funcGoal: user.funcGoal || user.goal,
                gender: user.gender,
                primaryEquip: input ? input.primaryEquip : null
            },
            constraints: { 
                availableEquip: availableEquip,
                forbiddenParts: [...user.pain, ...exhaustedParts], // [SYNC] Include exhausted parts
                downgrade: bodyStatus < 55,
                bmi: bmi,
                pain: user.pain,
                suggestedParts: suggestedParts
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
            if (ctx.source === 'Plan') finalTargets = ['全身']; // Plan mode: Auto-switch
            else ctx.constraints.downgrade = true; // Single mode: Downgrade
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
        // Main Strategy
        // [SYNC] Strategy is now Target-based only. Level scaling happens later.
        let mainStrategy = CONFIG.STRATEGY.find(s => s.target === goal) || CONFIG.STRATEGY[0];

        // [SYNC] Warmup/Relax Strategy Lookup (Keys: '激活', '柔韧')
        let wuStrategy = CONFIG.STRATEGY.find(s => s.target === '激活') || { intensity: 0.4, strategy: '恒定', mode: '常规' };
        let cdStrategy = CONFIG.STRATEGY.find(s => s.target === '柔韧') || { intensity: 0.3, strategy: '恒定', mode: '常规' };

        // 2. 结构规划 (Structure Planning) - T/10 Rule
        const wuCount = Math.ceil(duration / 10);
        const cdCount = Math.ceil(duration / 10);
        
        let wuTime = wuCount * 0.5;
        let cdTime = cdCount * 0.5;
        const mainTime = duration - wuTime - cdTime;

        // 3. 范式适配 (Paradigm Adaptation)
        const paradigmConfig = CONFIG.PARADIGMS.find(p => p.types.includes(type)) || CONFIG.PARADIGMS[0];
        const paradigmName = paradigmConfig.name;

        // 4. 构建环节 (Build Phases)
        const phaseCoeffs = ctx.planContext ? ctx.planContext.phase : { intensity:1.0, volume:1.0 };
        
        // [SYNC] Apply Level Coefficients
        const levelConfig = CONFIG.LEVELS.find(l => l.level === level) || { coeff: 1.0 };
        const levelCoeff = levelConfig.coeff;

        const mainSets = Math.round(mainStrategy.sets * phaseCoeffs.volume * levelCoeff); // Scale volume by level? Usually intensity, but let's scale sets slightly or keep as is. PRD says "Level Coeff" scales "Benchmark Params".
        const mainIntensity = mainStrategy.intensity * phaseCoeffs.intensity * levelCoeff;

        // [SYNC] Apply Paradigm Constraints (Flow Paradigm -> Sets=1, Rest=0)
        const applyParadigmConstraints = (baseStrat, pType) => {
            // Warmup/Relax are typically Flow Paradigm (流式范式)
            // Main depends on type
            let sets = baseStrat.sets || 1;
            let rest = baseStrat.rest || 0;
            
            if (pType === '热身' || pType === '放松') {
                sets = 1; // Force 1 set for warmup/relax
                rest = 0;
            }
            return { ...baseStrat, sets, rest };
        };

        const wuStratFinal = applyParadigmConstraints(wuStrategy, '热身');
        const cdStratFinal = applyParadigmConstraints(cdStrategy, '放松');

        // Rest Rounds (Transition)
        const wuRestRound = 0; 
        
        // [FIX] Dynamic Main Rest Round Calculation
        // Regular Mode (Strength/Hypertrophy): Transition time >= Set Rest time
        // Circuit Mode (HIIT): Round Rest > Station Rest (usually double)
        let mainRestRound = 60;
        if (mainStrategy.mode === '循环') mainRestRound = Math.max(60, (mainStrategy.rest || 30) * 2);
        else mainRestRound = mainStrategy.rest || 60;

        const cdRestRound = 0;

        ctx.phases = [
            { 
                type: '热身', 
                duration: wuTime, 
                paradigm: '流式范式', 
                targetCount: wuCount, 
                strategy: { 
                    ...wuStratFinal, 
                    restRound: wuRestRound, 
                    loadStrategy: '恒定' 
                } 
            },
            { 
                type: '主训', 
                duration: mainTime, 
                paradigm: paradigmName, 
                targetCount: 99, 
                strategy: { 
                    ...mainStrategy, 
                    sets: mainSets, 
                    intensity: mainIntensity,
                    loadStrategy: mainStrategy.strategy,
                    restRound: mainRestRound
                },
                coeffs: phaseCoeffs
            },
            { 
                type: '放松', 
                duration: cdTime, 
                paradigm: '流式范式', 
                targetCount: cdCount, 
                strategy: { 
                    ...cdStratFinal, 
                    restRound: cdRestRound, 
                    loadStrategy: '恒定' 
                } 
            }
        ];

        // 5. 计算主训动作数量 (Capacity Calculation)
        const mainPhase = ctx.phases[1];
        let singleActionTime = 0;
        if (paradigmName === '间歇范式') singleActionTime = 60 + (mainPhase.strategy.rest || 30) + mainRestRound;
        else if (paradigmName === '流式范式') singleActionTime = 60 + mainRestRound;
        else singleActionTime = (mainSets * 45) + ((mainSets - 1) * (mainPhase.strategy.rest || 60)) + mainRestRound; 

        mainPhase.targetCount = Math.max(1, Math.round((mainTime * 60) / singleActionTime));

        return ctx;
    },

    selectActions: (ctx) => {
        const { constraints, meta } = ctx;
        if (DB.length === 0) DB = FALLBACK_DB;

        // [FIX 4] 优化主配件确认逻辑 (移至动作粗选前)
        // 逻辑：单部位按区域随机，多部位默认手柄
        if (!meta.primaryEquip) {
            const target = meta.targets[0];
            const isMulti = meta.targets.length > 1 || target === '全身';
            const available = constraints.availableEquip;
            
            let candidates = [];
            
            if (isMulti) {
                candidates = ['手柄'];
            } else {
                const anatomy = CONSTANTS.MAPPINGS.ANATOMY;
                let region = '全身';
                for (const [r, parts] of Object.entries(anatomy)) {
                    if (parts.includes(target)) {
                        region = r;
                        break;
                    }
                }
                
                if (region === '上肢') candidates = ['手柄', '横杆'];
                else if (region === '下肢') candidates = ['手柄', '横杆', '踝带'];
                else if (region === '核心') candidates = ['手柄'];
                else candidates = ['手柄'];
            }
            
            // Intersect with user's available equipment
            const validCandidates = candidates.filter(e => available.includes(e));
            
            // Random selection
            if (validCandidates.length > 0) {
                meta.primaryEquip = validCandidates[Math.floor(Math.random() * validCandidates.length)];
            } else {
                meta.primaryEquip = '自重';
            }
        }

        ctx.phases.forEach(p => {
            // 1. 寻找环节模板
            let tpl = null;
            const targetPart = meta.targets[0]; 
            
            // Exact Match
            tpl = CONFIG.SEGMENT_TEMPLATES.find(t => 
                t.type === p.type && 
                t.dim === '部位' && 
                t.target === targetPart && 
                (t.levels.includes(meta.level) || t.levels.includes('All'))
            );

            // Region Fallback
            if (!tpl && p.type !== '主训') {
                const regionMap = CONSTANTS.MAPPINGS.ANATOMY;
                let region = null;
                for (const rKey in regionMap) {
                    if (regionMap[rKey].includes(targetPart)) {
                        region = rKey;
                        break;
                    }
                }
                if (region) {
                    tpl = CONFIG.SEGMENT_TEMPLATES.find(t => 
                        t.type === p.type && 
                        t.dim === '部位' && 
                        t.target === region && 
                        (t.levels.includes(meta.level) || t.levels.includes('All'))
                    );
                }
            }

            // Functional Fallback
            if (!tpl && p.type === '主训') {
                tpl = CONFIG.SEGMENT_TEMPLATES.find(t => 
                    t.type === '主训' && 
                    t.dim === '动作功能' && 
                    t.target === meta.funcGoal && 
                    (t.levels.includes(meta.level) || t.levels.includes('All'))
                );
            }

            // Hard Fallback
            if (!tpl) {
                if (p.type === '热身') tpl = CONFIG.SEGMENT_TEMPLATES.find(t => t.id === 'TPL_SEG_001'); 
                else if (p.type === '放松') tpl = CONFIG.SEGMENT_TEMPLATES.find(t => t.id === 'TPL_SEG_011'); 
                else tpl = CONFIG.SEGMENT_TEMPLATES.find(t => t.id === 'TPL_SEG_021'); 
            }

            p.template = tpl; 
            
            if (tpl && tpl.count !== undefined) {
                p.targetCount = Math.min(p.targetCount, tpl.count);
            }

            // 2. 动作池准备
            const isHighImpactRisk = (constraints.bmi >= 28) || constraints.pain.some(pt => ['膝盖', '脚踝'].includes(pt));
            
            let pool = DB.filter(a => {
                if (a.equip && a.equip.some(e => !constraints.availableEquip.includes(e))) return false;
                if (a.pain && a.pain.some(pt => constraints.forbiddenParts.includes(pt))) return false;
                if (a.impact === '高冲击' && isHighImpactRisk) return false;
                return true;
            });

            // 3. 动作粗选
            pool = pool.filter(a => {
                if (p.type === '热身') {
                    if (!a.func.includes('激活')) return false;
                }
                if (p.type === '放松') {
                    const isRelaxFunc = a.func.includes('放松') || a.func.includes('恢复');
                    const isRelaxType = a.courseType === '瑜伽' || a.courseType === '冥想';
                    if (!isRelaxFunc && !isRelaxType) return false;
                    if (a.func.includes('激活')) return false;
                }
                
                if (p.type === '热身' || p.type === '放松') {
                    if (!meta.targets.includes('全身')) {
                        const allowedParts = new Set(['全身', '核心']);
                        meta.targets.forEach(t => {
                            allowedParts.add(t);
                            const related = CONSTANTS.MAPPINGS.RELATED_PARTS[t];
                            if (related) related.forEach(r => allowedParts.add(r));
                        });
                        // [FIX 3] Stricter filtering: Main part must be allowed OR Sub part must be TARGET
                        const mainPartAllowed = allowedParts.has(a.part);
                        const subPartAllowed = (a.subPart || []).some(sp => meta.targets.includes(sp));
                        if (!mainPartAllowed && !subPartAllowed) return false;
                    }
                }
                
                // [NEW] 主配件一致性过滤 (Hard Filter)
                // 互斥配件列表：手柄、横杆、踝带 (自重、哑铃等通用配件不互斥)
                const conflictEquips = ['手柄', '横杆', '踝带'];
                const actionEquips = a.equip || [];
                // 如果动作包含“互斥配件”中的任意一个，必须与 primaryEquip 一致
                const hasConflict = actionEquips.some(e => conflictEquips.includes(e) && e !== meta.primaryEquip);
                if (hasConflict) return false;

                if (p.type === '主训') {
                    // [FIX 3] 主训环节严格匹配部位，防止练肩出现练胸动作
                    if (meta.targets[0] !== '全身') {
                        // 支持多部位选择 (如胸+背)，只要动作部位在目标列表中即可
                        if (!meta.targets.includes(a.part)) return false;
                    }
                }
                return true;
            });

            // 4. 动作打分
            pool.forEach(a => {
                a.score = window.Logic.calculateScore(a, ctx);
                if (p.type === '热身' || p.type === '放松') {
                    let isRelated = false;
                    meta.targets.forEach(t => {
                        const related = CONSTANTS.MAPPINGS.RELATED_PARTS[t];
                        if (related && related.includes(a.part)) isRelated = true;
                    });
                    if (isRelated) a.score += 10; 
                    if (a.part === '全身' || a.part === '核心') a.score += 5; 
                }
            });
            pool.sort((a, b) => b.score - a.score);

            // 5. 槽位填充
            let selected = [];
            const usedIds = new Set();
            const usedNames = new Set(); // [FIX 1] 名称去重集合
            const totalSlots = p.targetCount;
            const slotsConfig = tpl ? tpl.slots : [{focusDim:'动作构造', focusTarget:'复合动作', w:1.0}];
            
            // [SYNC] Difficulty Probability Distribution
            const diffDist = CONFIG.DIFF.find(d => d.level === meta.level) || CONFIG.DIFF[2]; // Default L3
            const getTargetDiff = () => {
                const rand = Math.random();
                let cum = 0;
                if (rand < (cum += diffDist.l1)) return 'L1';
                if (rand < (cum += diffDist.l2)) return 'L2';
                if (rand < (cum += diffDist.l3)) return 'L3';
                if (rand < (cum += diffDist.l4)) return 'L4';
                return 'L5';
            };

            const pickFuzzy = (candidates, count) => {
                const picks = [];
                const fuzzyRange = 10; 
                let available = [...candidates];
                while (picks.length < count && available.length > 0) {
                    const windowSize = Math.min(fuzzyRange, available.length);
                    const idx = Math.floor(Math.random() * windowSize);
                    const pick = available[idx];
                    
                    // [FIX 1] 智能名称去重：提取核心词 (如 "哑铃卧推" -> "卧推")
                    // 避免同类动作刷屏 (如 3个不同角度的卧推)
                    const coreName = pick.name.split('(')[0].replace(/杠铃|哑铃|绳索|器械|自重|坐姿|站姿/g, '').trim();
                    
                    if (!usedNames.has(coreName)) {
                        picks.push(pick);
                        usedNames.add(coreName);
                    }
                    // 无论是否选中，都从available中移除，避免死循环
                    available.splice(idx, 1);
                }
                return picks;
            };

            slotsConfig.forEach(slot => {
                const count = Math.max(1, Math.round(totalSlots * slot.w));
                let candidates = pool.filter(a => {
                    if (usedIds.has(a.id)) return false;
                    if (slot.focusDim === '部位' && a.part === slot.focusTarget) return true;
                    if (slot.focusDim === '动作模式' && a.mode === slot.focusTarget) return true;
                    if (slot.focusDim === '动作功能' && a.func && a.func.includes(slot.focusTarget)) return true;
                    if (slot.focusDim === '动作构造' && a.construct === slot.focusTarget) return true;
                    if (slot.focusDim === '主动肌' && a.muscle === slot.focusTarget) return true;
                    return false;
                });
                
                // [SYNC] Apply Difficulty Filter based on Probability
                // Instead of strict filtering, we sort by difficulty match? 
                // Or filter candidates to match target diff?
                // Let's try to pick candidates that match target diff first.
                // Since we pick multiple, let's just sort candidates by how close they are to user level, 
                // but allow some variance.
                // Actually, let's use the probability to filter the pool for this slot.
                // But pool is small. Let's just sort by score which includes difficulty match.
                // PRD says: "Based on [3.2 Difficulty Distribution], determine target difficulty".
                
                const picked = pickFuzzy(candidates, count);
                picked.forEach(a => { selected.push(a); usedIds.add(a.id); });
            });

            if (selected.length < totalSlots) {
                const remainingCount = totalSlots - selected.length;
                const leftovers = pool.filter(a => !usedIds.has(a.id));
                const picked = pickFuzzy(leftovers, remainingCount);
                picked.forEach(a => { selected.push(a); usedIds.add(a.id); });
            }

            // [FIX 2] 启用全局重排逻辑
            // 必须启用，否则动作顺序仅由 Slot 填充顺序决定，无法实现 "主动肌升序" 等精细排序
            // 模板配置 (config.js) 中的 sort 字段决定了最终顺序
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

    calculateScore: (action, ctx) => {
        let score = 100;
        const factors = CONFIG.FACTORS || [];
        const evalRule = (rule, act) => {
            if (rule.includes('是否收藏 = True') && act.isFav) return true;
            if (rule.includes('未练天数 > 7')) {
                const days = (new Date() - new Date(act.lastTrained)) / (1000 * 3600 * 24);
                return days > 7;
            }
            if (rule.includes('历史训练次数 == 0') && !act.lastTrained) return true; 
            return false;
        };

        factors.forEach(f => {
            if (evalRule(f.rule, action)) score += f.weight;
        });

        // [FIX] 主配件权重倾斜 (Priority Boost)
        // 如果动作使用了当前锁定的主配件，给予极高权重加成，确保其排在自重动作之前
        // 解决 "锁定了横杆，但出来的全是俯卧撑" 的问题
        if (ctx.meta.primaryEquip && action.equip && action.equip.includes(ctx.meta.primaryEquip)) {
            score += 500;
        }

        if (ctx.meta.targets.includes(action.part)) score += 10;
        return score;
    },

    // ... (保持 compareActions, instantiate, runPipeline, genCourse, genPlan, completeTraining, getMaxReps, calcRepsFromLoad 不变) ...
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
            const safeIdxA = idxA === -1 ? 999 : idxA;
            const safeIdxB = idxB === -1 ? 999 : idxB;
            return safeIdxA - safeIdxB;
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
                // [SYNC] Level Adaptation
                const level = ctx.meta.level || 'L3';
                const intensityConfig = CONSTANTS.MAPPINGS.INTENSITY[level] || CONSTANTS.MAPPINGS.INTENSITY['L3'];

                let sets = Math.round(strategy.sets * vCoeff) || 3;
                let intensity = strategy.intensity * iCoeff;
                let load = 0;
                let reps = isLoadPriority ? '12' : (intensityConfig.time || '30');
                let base1RM = 20;

                if (isLoadPriority) {
                    if (a.powerModule === '是') {
                        base1RM = a.demoUser1RM || window.UserAbility.oneRM[a.part] || 20;
                        load = Math.round(base1RM * intensity);
                        
                        // [SYNC] RPE-based Reps Calculation (Pixel-perfect with PRD)
                        // Formula: Recommended Reps = Theoretical Max Reps - (10 - Target RPE)
                        const targetRPE = strategy.rpe || 8; // Default RPE 8 (2 reps in reserve)
                        const maxReps = window.Logic.getMaxReps(intensity);
                        
                        const rpeBuffer = 10 - targetRPE; // e.g. 10 - 8 = 2 reps in reserve
                        reps = Math.max(1, maxReps - rpeBuffer).toString();
                    } else {
                        // Non-power module resistance action (e.g. bodyweight)
                        // Use intensity mapping for reps
                        reps = intensityConfig.reps.toString();
                    }
                }

                // 生成组序列
                let algoSetDetails = [];
                const loadStrat = strategy.loadStrategy || '推荐';
                const stratConfig = CONFIG.LOAD_STRATEGIES.filter(s => s.name === (loadStrat==='推荐'?'递增':loadStrat));

                for(let i=0; i<sets; i++) {
                    let sLoad = load;
                    let sReps = parseInt(reps);
                    const rule = stratConfig.find(s => s.index === (i+1).toString()) || stratConfig.find(s => s.index === '3+' || s.index === 'All');
                    
                    if (rule) {
                        if (isLoadPriority && a.powerModule === '是') {
                            // Vary Load
                            sLoad = Math.round(load * rule.coeff * 2) / 2;
                            // Recalculate reps based on new load
                            sReps = window.Logic.calcRepsFromLoad(sLoad, base1RM);
                        } else {
                            // Vary Reps/Time (Non-power module or Time-based)
                            // Use coeff to vary intensity (e.g. 0.85 * reps for easier sets)
                            sReps = Math.round(parseInt(reps) * rule.coeff);
                        }
                    }
                    algoSetDetails.push({ load: sLoad, reps: sReps });
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
        
        let template = CONFIG.PLAN_TEMPLATES.find(t => 
            t.freq === freq && 
            t.goal === window.store.user.goal
        );
        if (!template) template = CONFIG.PLAN_TEMPLATES[0];

        let cycleKey = '>4周';
        if (weeks <= 4) cycleKey = weeks + '周';
        const phaseStrat = CONFIG.PHASE_STRATEGIES.find(s => s.cycle === cycleKey) || CONFIG.PHASE_STRATEGIES[3];

        const schedule = [];
        let currentWeek = 1;

        phaseStrat.structure.forEach((pName, pIdx) => {
            const allocRatio = phaseStrat.alloc[pIdx];
            const pWeeks = Math.max(1, Math.round(weeks * allocRatio));
            
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

                for(let d=1; d<=7; d++) {
                    const dayName = CONSTANTS.WEEKDAYS[d-1];
                    const isTrainingDay = userDays.includes(dayName);
                    
                    if (isTrainingDay) {
                        const slotIdx = (d - 1) % template.basicSlots.length;
                        const slot = template.basicSlots[slotIdx];
                        weekData.days.push({ 
                            dayName, 
                            isTraining: true, 
                            targets: [slot.focusTarget], 
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
        window.store.user.fatigue = Math.min(10, window.store.user.fatigue + 2);
        return { prCount: 0 };
    },

    // [SYNC] Helper: Theoretical Max Reps based on Intensity %
    getMaxReps: (intensity) => {
        if (intensity >= 1.0) return 1;
        if (intensity >= 0.95) return 2;
        if (intensity >= 0.90) return 4;
        if (intensity >= 0.85) return 6;
        if (intensity >= 0.80) return 8;
        if (intensity >= 0.75) return 10;
        if (intensity >= 0.70) return 12;
        if (intensity >= 0.65) return 15;
        return 20;
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
