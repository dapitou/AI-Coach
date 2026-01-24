window.ViewLibrary = {
    openActionDetail: (id, source) => {
        window.store.detailActionId = id;
        window.store.detailSource = source;
        window.store.detailTab = 'intro';
        document.getElementById('modal-action-detail').classList.add('active');
        App.renderActionDetail();
    },

    closeActionDetail: () => {
        document.getElementById('modal-action-detail').classList.remove('active');
    },

    switchDetailTab: (tab) => {
        window.store.detailTab = tab;
        App.renderActionDetail();
    },

    renderActionDetail: () => {
        const id = window.store.detailActionId;
        const source = window.store.detailSource;
        const tab = window.store.detailTab;
        const action = DB.find(a => a.id === id) || FALLBACK_DB.find(a => a.id === id);
        if (!action) return;

        const tabs = ['intro', 'teach', 'history'];
        const tabNames = {'intro':'简介', 'teach':'教学', 'history':'历史'};
        document.getElementById('detail-tabs').innerHTML = tabs.map(t => 
            `<div class="tab ${t===tab?'active':''}" onclick="App.switchDetailTab('${t}')">${tabNames[t]}</div>`
        ).join('');

        let html = '';
        if (tab === 'intro') {
            const antagonist = action.antagonist || '无';
            const synergist = (action.subPart && action.subPart.length) ? action.subPart.join('、') : '无';
            const stabilizer = '核心肌群';
            const paradigm = action.paradigm || CONSTANTS.COURSE_TYPES[action.courseType] || '抗阻范式';
            const mirrorTag = action.mirror ? `<div class="ad-tag" style="color:var(--primary); border-color:var(--primary);">镜像</div>` : '';

            let addBtn = '';
            if (source === 'library') {
                addBtn = `<button class="ad-add-btn" onclick="App.confirmDetailAdd('${id}')">＋ 添加动作</button>`;
            }

            html = `
                <div class="ad-video"><div style="font-size:12px;">动作演示视频</div></div>
                <div class="ad-header">
                    <div style="display:flex; justify-content:space-between; align-items:start; margin-bottom:10px;">
                        <div class="ad-title" style="margin-bottom:0;">${action.name}</div>${addBtn}
                    </div>
                    <div class="ad-tags"><div class="ad-tag">${action.part}</div><div class="ad-tag">${action.construct || '复合动作'}</div><div class="ad-tag">${action.difficulty}</div>${mirrorTag}</div>
                </div>
                <div class="ad-section"><div class="ad-sec-title">基本信息</div><div class="info-grid"><div class="info-card"><div class="ic-label">器械</div><div class="ic-val">${action.equip[0]}</div></div><div class="info-card"><div class="ic-label">冲击</div><div class="ic-val">${action.impact}</div></div><div class="info-card"><div class="ic-label">范式</div><div class="ic-val">${paradigm.replace('范式','')}</div></div></div></div>
                <div class="ad-section"><div class="ad-sec-title">肌群参与</div><div class="muscle-map"><div class="muscle-card"><div class="mc-label">主动肌 (Agonist)</div><div class="mc-val highlight">${action.muscle}</div></div><div class="muscle-card"><div class="mc-label">拮抗肌 (Antagonist)</div><div class="mc-val">${antagonist}</div></div><div class="muscle-card"><div class="mc-label">辅助肌 (Synergist)</div><div class="mc-val">${synergist}</div></div><div class="muscle-card"><div class="mc-label">稳定肌 (Stabilizer)</div><div class="mc-val">${stabilizer}</div></div></div></div>
                <div class="ad-section"><div class="ad-sec-title">动作说明</div><div class="desc-box">${action.name}是一个经典的${action.part}训练动作，主要针对${action.muscle}进行强化。通过${action.construct || '复合'}运动模式，能够有效提升${action.func.join('与')}能力。适合${action.difficulty}及以上水平训练者。</div></div>
            `;
        } else if (tab === 'teach') {
            html = `
                <div class="ad-video"><div style="font-size:12px;">教学讲解视频</div></div>
                <div class="ad-section"><div class="ad-sec-title">动作要点</div><ul style="font-size:13px; color:#ccc; padding-left:20px; margin-bottom:20px; line-height:1.8;"><li>保持核心收紧，背部挺直，避免脊柱过度伸展。</li><li>动作过程中控制速度，离心阶段（下放）控制在2-3秒。</li><li>呼吸配合：发力时呼气，还原时吸气。</li><li>注意力集中在${action.muscle}的收缩感上。</li></ul></div>
                <div class="ad-section"><div class="ad-sec-title" style="color:var(--danger);">常见错误</div><ul style="font-size:13px; color:#ccc; padding-left:20px; line-height:1.8;"><li>耸肩或含胸，导致斜方肌代偿。</li><li>关节锁死，增加关节压力。</li><li>重量过大导致动作变形，借力明显。</li></ul></div>
            `;
        } else if (tab === 'history') {
            const historyData = [
                { date: '10-01', vol: 1200 }, { date: '10-05', vol: 1350 }, { date: '10-10', vol: 1400 },
                { date: '10-15', vol: 1300 }, { date: '10-20', vol: 1500 }, { date: '10-25', vol: 1600 }
            ];
            const rmTrend = [20, 22, 22, 25, 25, 28];
            
            html = `
                <div class="ad-section"><div class="ad-sec-title">预估 1RM 趋势</div><div style="background:#1a1a1a; height:150px; border-radius:8px; display:flex; align-items:flex-end; justify-content:space-around; padding:10px; border:1px solid #333;">${rmTrend.map(h => `<div style="width:10%; background:var(--primary); height:${h*3}px; border-radius:2px 2px 0 0; opacity:0.8;"></div>`).join('')}</div></div>
                <div class="ad-section"><div class="ad-sec-title">近期变化</div><div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:10px;"><div style="background:#1a1a1a; padding:10px; border-radius:6px; text-align:center; border:1px solid #333;"><div style="font-size:10px; color:#888;">近1周</div><div style="color:var(--primary); font-weight:700;">+2%</div></div><div style="background:#1a1a1a; padding:10px; border-radius:6px; text-align:center; border:1px solid #333;"><div style="font-size:10px; color:#888;">近1月</div><div style="color:var(--primary); font-weight:700;">+5%</div></div><div style="background:#1a1a1a; padding:10px; border-radius:6px; text-align:center; border:1px solid #333;"><div style="font-size:10px; color:#888;">近3月</div><div style="color:var(--primary); font-weight:700;">+12%</div></div></div></div>
                <div class="ad-section"><div class="ad-sec-title">训练记录</div>${historyData.map(h => `<div style="display:flex; justify-content:space-between; padding:12px 0; border-bottom:1px solid #222; font-size:13px;"><span style="color:#888;">${h.date}</span><span style="font-weight:600;">${h.vol} kg</span></div>`).join('')}</div>
            `;
        }
        document.getElementById('action-detail-body').innerHTML = html;
        document.getElementById('action-detail-footer').style.display = 'none';
    },

    confirmDetailAdd: (id) => {
        const state = window.store.replaceState;
        if (!state.selectedIds) state.selectedIds = [];
        if (state.mode === 'replace') {
             state.selectedIds = [id];
             App.confirmReplace();
        } else {
             if (!state.selectedIds.includes(id)) state.selectedIds.push(id);
             App.renderLibraryList(); 
        }
        App.closeActionDetail();
    },

    addAction: (pIdx) => {
        window.store.replaceState = { pIdx, mode: 'add' };
        let defaultPart = '全部';
        if (window.currentCtx && window.currentCtx.meta && window.currentCtx.meta.targets && window.currentCtx.meta.targets.length > 0) {
            defaultPart = window.currentCtx.meta.targets[0];
        }
        window.store.libFilter = { part: defaultPart, equip:[], difficulty:[], impact:[], showPanel: false };
        App.renderLibraryFilters();
        App.renderLibraryList();
        App.switchView('view-library');
    },

    openLibrary: (pIdx, aIdx, source = 'result') => {
        window.store.replaceState = { pIdx, aIdx, mode: 'replace', source };
        const currentAction = window.currentCtx.phases[pIdx].actions[aIdx];
        window.store.libFilter = { part: currentAction.part, equip:[], difficulty:[], impact:[], showPanel: false };
        App.renderLibraryFilters();
        App.renderLibraryList();
        App.switchView('view-library');
    },

    closeLibrary: () => {
        const source = window.store.replaceState?.source;
        if (source === 'workout') {
            App.switchView('view-workout');
        } else {
            App.switchView('view-result');
        }
        window.store.replaceState = null;
    },

    renderLibraryFilters: () => {
        const parts = ['全部', ...CONSTANTS.PARTS];
        const { part, showPanel } = window.store.libFilter;
        
        const tabsHtml = parts.map(p => 
            `<div class="lib-filter-tag ${p === part ? 'active' : ''}" onclick="App.setLibFilter('part', '${p}')">${p}</div>`
        ).join('');
        
        const toggleHtml = `
            <div class="lib-filter-toggle ${showPanel ? 'active' : ''}" onclick="App.toggleLibFilterPanel()">
                <i style="font-style:normal; font-size:14px;">≡</i>
            </div>
        `;
        
        document.getElementById('lib-parts').innerHTML = `<div class="lib-tags-container">${tabsHtml}</div>${toggleHtml}`;

        let panel = document.getElementById('lib-filter-panel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'lib-filter-panel';
            panel.className = 'lib-filter-panel';
            document.getElementById('lib-parts').after(panel);
        }
        
        if (showPanel) panel.classList.add('active'), App.renderFilterPanelContent(panel); else panel.classList.remove('active');
    },

    setLibFilter: (key, val) => {
        window.store.libFilter[key] = val;
        App.renderLibraryFilters();
        App.renderLibraryList();
    },

    toggleLibFilterPanel: () => {
        window.store.libFilter.showPanel = !window.store.libFilter.showPanel;
        App.renderLibraryFilters();
    },

    renderFilterPanelContent: (container) => {
        const f = window.store.libFilter;
        const renderSec = (label, key, opts) => `
            <div class="filter-sec">
                <div class="filter-label">${label}</div>
                <div class="filter-chips">
                    ${opts.map(o => `
                        <div class="f-chip ${(f[key]||[]).includes(o) ? 'active' : ''}" onclick="App.toggleLibFilterOpt('${key}', '${o}')">${o}</div>
                    `).join('')}
                </div>
            </div>
        `;
        
        const equips = ['自重', '横杆', '手柄', '健身凳', '泡沫轴', '哑铃'];
        const diffs = ['L1', 'L2', 'L3', 'L4', 'L5'];
        const impacts = ['无冲击', '低冲击', '高冲击'];
        
        container.innerHTML = renderSec('器械', 'equip', equips) + renderSec('难度', 'difficulty', diffs) + renderSec('冲击', 'impact', impacts) + `<div class="filter-btn-row"><div class="f-chip" onclick="App.resetLibFilters()">重置</div><div class="f-chip active" onclick="App.toggleLibFilterPanel()">收起</div></div>`;
    },

    toggleLibFilterOpt: (key, val) => {
        const arr = window.store.libFilter[key] || [];
        const idx = arr.indexOf(val);
        if (idx > -1) arr.splice(idx, 1);
        else arr.push(val);
        window.store.libFilter[key] = arr;
        App.renderLibraryFilters();
        App.renderLibraryList();
    },
    
    resetLibFilters: () => {
        window.store.libFilter.equip = [];
        window.store.libFilter.difficulty = [];
        window.store.libFilter.impact = [];
        App.renderLibraryFilters();
        App.renderLibraryList();
    },

    renderLibraryList: () => {
        const { part, equip, difficulty, impact } = window.store.libFilter;
        let list = DB;
        
        if (part !== '全部') list = list.filter(a => a.part === part);
        if (equip && equip.length) list = list.filter(a => a.equip.some(e => equip.includes(e)));
        if (difficulty && difficulty.length) list = list.filter(a => difficulty.includes(a.difficulty));
        if (impact && impact.length) list = list.filter(a => impact.includes(a.impact));
        
        const groups = {};
        list.forEach(a => {
            const func = (a.func && a.func.length) ? a.func[0] : '其他';
            if (!groups[func]) groups[func] = [];
            groups[func].push(a);
        });
        
        let html = '';
        if (list.length === 0) {
            html = `<div style="text-align:center; color:#666; padding:20px;">无匹配动作</div>`;
        } else {
            Object.keys(groups).sort().forEach(gName => {
                html += `<div class="lib-group-title">${gName}</div>`;
                html += groups[gName].map(a => {
                    const isSelected = (window.store.replaceState.selectedIds || []).includes(a.id);
                    const mirrorTag = a.mirror ? `<span style="font-size:9px; color:var(--primary); border:1px solid var(--primary); padding:0 2px; border-radius:2px; margin-left:4px;">镜像</span>` : '';
                    return `
                    <div class="lib-item ${isSelected ? 'selected' : ''}" onclick="App.openActionDetail('${a.id}', 'library')"><div class="lib-thumb"></div><div class="lib-info"><div class="lib-name">${a.name}${mirrorTag}</div><div class="lib-meta">${a.part} · ${a.muscle} · ${a.equip[0]} · ${a.difficulty}</div></div><div class="lib-check-area" onclick="event.stopPropagation(); App.selectLibAction('${a.id}')"><div class="lib-check"></div></div></div>`;
                }).join('');
            });
        }
        document.getElementById('lib-list').innerHTML = html;
    },

    selectLibAction: (id) => {
        const state = window.store.replaceState;
        if (!state.selectedIds) state.selectedIds = [];
        if (state.mode === 'replace') {
            state.selectedIds = [id];
        } else {
            const idx = state.selectedIds.indexOf(id);
            if (idx > -1) state.selectedIds.splice(idx, 1);
            else state.selectedIds.push(id);
        }
        App.renderLibraryList();
    },

    confirmReplace: () => {
        const { pIdx, aIdx, selectedIds, mode, source } = window.store.replaceState;
        if (!selectedIds || selectedIds.length === 0) return App.closeLibrary();
        
        if (mode === 'add') {
            selectedIds.forEach(id => {
                const newAction = DB.find(a => a.id === id);
                if (newAction) {
                    const rawAction = JSON.parse(JSON.stringify(newAction));
                    window.currentCtx.phases[pIdx].actions.push(rawAction);
                }
            });
        } else {
            const newAction = DB.find(a => a.id === selectedIds[0]);
            if (newAction) {
                const rawAction = JSON.parse(JSON.stringify(newAction));
                window.currentCtx.phases[pIdx].actions[aIdx] = rawAction;
            }
        }
        
        // Recalculate duration for Custom Course
        if (window.currentCtx.source === 'Custom') {
            const p = window.currentCtx.phases[pIdx];
            let pDur = 0;
            p.actions.forEach(a => {
                const rest = p.strategy.rest || 60;
                const singleDur = 45; // Approx
                pDur += ((a.sets || 3) * (singleDur + rest));
            });
            p.duration = Math.ceil(pDur / 60);
            window.currentCtx.meta.duration = window.currentCtx.phases.reduce((acc, ph) => acc + (ph.duration || 0), 0);
        }

        App.recalculateLoadStrategy();
        
        if (source === 'workout') {
            window.ViewWorkout.onActionReplaced(pIdx, aIdx);
            App.closeLibrary(); // Will switch back to workout based on source check
        } else {
            App.renderFineTuning(window.currentCtx);
            App.closeLibrary();
        }
    }
};