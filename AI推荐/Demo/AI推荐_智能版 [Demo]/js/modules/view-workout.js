window.ViewWorkout = {
    state: {
        ctx: null,
        phaseIdx: 0,
        actionIdx: 0,
        setIdx: 0,
        status: 'idle', // countdown, working, resting, paused, finished
        timer: 0, // seconds
        setTimer: 0,
        totalTime: 0,
        currentReps: 0,
        targetReps: 0,
        currentPower: 0,
        currentStroke: 0,
        powerHistory: [],
        strokeHistory: [],
        interval: null,
        isPaused: false,
        currentLoad: 20,
        isDialDragging: false,
        side: null, // 'L' | 'R' | null
        lastAngle: 0,
        simState: {
            activeKey: null, // 'z' or 'm'
            direction: 0, // 1: concentric, -1: eccentric
            maxPower: 0
        }
    },

    start: (ctx) => {
        // Init State
        const s = ViewWorkout.state;
        s.ctx = ctx;
        s.phaseIdx = 0;
        s.actionIdx = 0;
        s.setIdx = 0;
        s.totalTime = 0;
        s.powerHistory = []; // Stores per-rep peak power: {val, side}
        s.strokeHistory = new Array(100).fill({val:0, side:null});
        s.isPaused = false;
        
        App.switchView('view-workout');
        
        // Start Global Timer
        if (s.interval) clearInterval(s.interval);
        s.interval = setInterval(ViewWorkout.tick, 100); // 100ms tick for smooth UI

        // Setup Header
        const header = document.querySelector('.wk-header');
        if(header) {
            header.innerHTML = `
                <div class="wk-header-left">
                    <div class="wk-close-btn" onclick="App.openConfirmModal('确定要结束训练吗？', () => { window.ViewWorkout.finishWorkout(); App.closeConfirmModal(); })">✕</div>
                </div>
                <div class="wk-header-center">
                    <div class="wk-progress-container">
                        <div class="wk-progress-info"><span>课程进度</span><span id="wk-prog-text">0%</span></div>
                        <div class="wk-progress-track"><div class="wk-progress-fill" id="wk-prog-fill"></div></div>
                    </div>
                </div>
                <div class="wk-header-right">
                    <div class="wk-time-badge" id="wk-total-time">00:00</div>
                </div>
            `;
        }

        ViewWorkout.initDial();
        ViewWorkout.initSimControls();
        ViewWorkout.prepareSet();
        
        // Inject Sim Controls UI
        const simHTML = `
            <div class="sim-hint">键盘模拟</div>
            <div class="sim-btn">按住 Z (左侧)</div>
            <div class="sim-btn">按住 M (右侧)</div>
            <div class="sim-hint" style="margin-top:5px">松开回程计次</div>
            <div class="sim-btn" onclick="window.ViewWorkout.simTime()" style="margin-top:10px;">>> 加速 (X)</div>
        `;
        const simContainer = document.querySelector('.sim-controls');
        if(simContainer) simContainer.innerHTML = simHTML;
    },

    prepareSet: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const set = action.setDetails[s.setIdx];
        
        if (!set) {
            console.error("Set details missing, skipping...");
            return ViewWorkout.finishSet(); // Auto-skip if error
        }

        s.status = 'countdown';
        s.timer = 3; // 3s countdown
        s.setTimer = 0;
        s.currentReps = 0;
        s.targetReps = parseInt(set.reps) || 0; // Ensure number for calculation
        s.currentPower = 0;
        s.currentStroke = 0;
        s.side = action.mirror ? 'L' : null;
        
        // Check Power Module
        const hasPower = action.powerModule === '是';
        const dialWrapper = document.getElementById('wk-dial-wrapper');
        const dialControls = document.querySelector('.wk-dial-controls');
        const charts = document.querySelectorAll('.wk-dash-col');
        
        if (hasPower) {
            if(dialWrapper) dialWrapper.style.visibility = 'visible';
            if(dialControls) dialControls.style.visibility = 'visible';
            charts.forEach(c => c.style.visibility = 'visible');
        } else {
            if(dialWrapper) dialWrapper.style.visibility = 'hidden';
            if(dialControls) dialControls.style.visibility = 'hidden';
            charts.forEach(c => c.style.visibility = 'hidden');
        }

        // Auto-set Weight
        s.currentLoad = (set.load !== undefined && set.load !== null) ? set.load : 20;
        ViewWorkout.updateDialUI();

        // Show Toast
        if (hasPower) ViewWorkout.showDialToast();

        // Hide active counter (fade out)
        const counter = document.getElementById('wk-active-counter');
        if(counter) counter.classList.remove('visible');
        
        // Force hide rest overlay immediately
        const restOverlay = document.getElementById('wk-overlay-rest');
        if(restOverlay) restOverlay.classList.remove('active');

        ViewWorkout.render();
        ViewWorkout.renderActionList();
        ViewWorkout.renderCountdown();
    },

    tick: () => {
        const s = ViewWorkout.state;
        if (s.isPaused) return;
        
        ViewWorkout.updateSimLogic();

        // Global Stats
        if (s.status !== 'finished') s.totalTime += 0.1;

        // State Machine
        if (s.status === 'countdown') {
            s.timer -= 0.1;
            if (s.timer <= 0) {
                s.status = 'working';
                s.timer = 0;
                
                // Hide countdown overlay
                const cntOverlay = document.getElementById('wk-overlay-cnt');
                if(cntOverlay) cntOverlay.classList.remove('active');
                // Show active counter (fade in)
                const counter = document.getElementById('wk-active-counter');
                if(counter) counter.classList.add('visible');
                
                ViewWorkout.render();
            } else {
                ViewWorkout.updateCountdownUI();
            }
        } else if (s.status === 'working') {
            s.setTimer += 0.1;
            
            // Auto-finish time-based sets
            const phase = s.ctx.phases[s.phaseIdx];
            const action = phase.actions[s.actionIdx];
            const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式' || action.measure === '计时';
            
            if (isTimeBased && s.setTimer >= s.targetReps) { // targetReps stores seconds for time-based
                ViewWorkout.finishSet();
                if (s.status !== 'working') return;
            }
            
            ViewWorkout.updateDashboard();
            ViewWorkout.drawPowerChart();
            ViewWorkout.drawStrokeChart();
            
            // Emphasis Animation
            const counterEl = document.getElementById('wk-active-counter');
            if (counterEl) {
                let isEmphasis = false;
                if (isTimeBased) {
                    if (s.targetReps - s.setTimer <= 5) isEmphasis = true;
                } else {
                    if (s.targetReps - s.currentReps <= 3 && s.targetReps > 3) isEmphasis = true;
                }
                if (isEmphasis) counterEl.classList.add('emphasis');
                else counterEl.classList.remove('emphasis');
            }
        } else if (s.status === 'resting') {
            s.timer -= 0.1;
            if (s.timer <= 0) {
                ViewWorkout.nextSet();
            } else {
                ViewWorkout.updateRestUI();
            }
        }
    },

    finishSet: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const loopMode = phase.strategy.loopMode || '常规组';
        
        // Handle Mirrored Sets (L -> R)
        if (action.mirror && s.side === 'L') {
            s.side = 'R';
            s.setTimer = 0;
            s.currentReps = 0;
            s.currentPower = 0;
            s.currentStroke = 0;
            ViewWorkout.render(); // Update UI to show Right side
            return; // Skip rest, continue working
        }

        // Determine Rest Time
        let restTime = 0;
        let isRoundSwitch = false;
        
        // Use strategy values directly, default to 0 if undefined to avoid fabricating data
        const strategyRest = parseInt(phase.strategy.rest) || 0;
        // If restRound is undefined, fallback to rest (or 0 if rest is 0)
        const strategyRestRound = (phase.strategy.restRound !== undefined && phase.strategy.restRound !== "") ? parseInt(phase.strategy.restRound) : strategyRest;

        if (loopMode === '循环组' || loopMode === '超级组') {
            // Circuit Logic: Rest between actions, RestRound after full cycle
            // Check if this is the last action in the phase
            const isLastActionInPhase = s.actionIdx >= phase.actions.length - 1;
            if (isLastActionInPhase) {
                isRoundSwitch = true;
                restTime = strategyRestRound;
            } else {
                restTime = strategyRest;
            }
        } else {
            // Regular Logic: Rest between sets, RestRound between actions
            const isLastSetInAction = s.setIdx >= action.sets - 1;
            if (isLastSetInAction) {
                isRoundSwitch = true;
                restTime = strategyRestRound;
            } else {
                restTime = strategyRest;
            }
        }

        // Check for Workout Finish
        // We need to peek if nextSet will overflow
        // But simpler: nextSet handles index increment. If it overflows phase, we check there.
        // Let's just set rest. If nextSet detects end of workout, it handles it.
        // Wait, we need to know if we should rest. If workout ends, no rest.
        
        // Peek next state
        let nextP = s.phaseIdx, nextA = s.actionIdx, nextS = s.setIdx;
        let finished = false;

        if (loopMode === '循环组' || loopMode === '超级组') {
             nextA++;
             if (nextA >= phase.actions.length) {
                 nextA = 0;
                 nextS++;
                 // Assuming all actions in circuit have same sets, or we skip finished ones
                 // For simplicity, use first action's sets as circuit sets
                 if (nextS >= phase.actions[0].sets) {
                     nextP++;
                     nextA = 0;
                     nextS = 0;
                 }
             }
        } else {
            nextS++;
            if (nextS >= action.sets) {
                nextS = 0;
                nextA++;
                if (nextA >= phase.actions.length) {
                    nextA = 0;
                    nextP++;
                }
            }
        }

        if (nextP >= s.ctx.phases.length) {
            finished = true;
        }

        if (finished) {
            ViewWorkout.finishWorkout();
        } else if (restTime > 0) {
            s.status = 'resting';
            s.timer = restTime;
            ViewWorkout.renderRest();
        } else {
            ViewWorkout.nextSet();
        }
    },

    nextSet: () => {
        const s = ViewWorkout.state;
        // Prevent multiple calls if already transitioning
        if (s.status === 'transition') return;
        s.status = 'transition';

        const phase = s.ctx.phases[s.phaseIdx];
        const loopMode = phase.strategy.loopMode || '常规组';

        if (loopMode === '循环组' || loopMode === '超级组') {
            // Circuit: Action -> Action -> ... -> Next Set
            // Find next valid action that has sets remaining
            let nextA = s.actionIdx + 1;
            let nextS = s.setIdx;
            let found = false;
            
            // Search for next available slot
            for (let i = 0; i < phase.actions.length * 10; i++) { // Safety limit
                if (nextA >= phase.actions.length) {
                    nextA = 0;
                    nextS++;
                }
                // Check if this action has this set
                if (nextS < phase.actions[nextA].sets) {
                    s.actionIdx = nextA;
                    s.setIdx = nextS;
                    found = true;
                    break;
                } else {
                    const maxSets = Math.max(...phase.actions.map(a => a.sets));
                    if (nextS >= maxSets) break; // Phase done
                    nextA++;
                }
            }
            
            if (!found) {
                // Move to next phase
                s.phaseIdx++;
                s.actionIdx = 0;
                s.setIdx = 0;
            }
        } else {
            // Regular: Set -> Set -> ... -> Next Action
            const action = phase.actions[s.actionIdx];
            if (s.setIdx < action.sets - 1) {
                s.setIdx++;
            } else {
                s.setIdx = 0;
                if (s.actionIdx < phase.actions.length - 1) {
                    s.actionIdx++;
                } else {
                    s.actionIdx = 0;
                    s.phaseIdx++;
                }
            }
        }

        if (s.phaseIdx >= s.ctx.phases.length) {
            ViewWorkout.finishWorkout();
            return;
        }

        ViewWorkout.prepareSet();
    },

    finishWorkout: () => {
        const s = ViewWorkout.state;
        s.status = 'finished';
        clearInterval(s.interval);
        ViewWorkout.removeSimControls();
        
        // Show Summary
        App.switchView('view-summary');
        
        const totalMin = Math.floor(s.totalTime / 60);
        const totalSec = Math.floor(s.totalTime % 60);
        const kcal = Math.floor(s.totalTime * 0.15 * (window.store.user.weight / 60)); // Mock algo
        
        document.getElementById('sum-time').innerText = `${totalMin}:${totalSec < 10 ? '0'+totalSec : totalSec}`;
        document.getElementById('sum-cal').innerText = kcal;
        
        // Update User Profile (Mock)
        window.store.user.fatigue = Math.min(10, window.store.user.fatigue + 1);
    },

    // --- Simulation Controls ---
    
    initSimControls: () => {
        document.addEventListener('keydown', ViewWorkout.handleKeyDown);
        document.addEventListener('keyup', ViewWorkout.handleKeyUp);
    },

    removeSimControls: () => {
        document.removeEventListener('keydown', ViewWorkout.handleKeyDown);
        document.removeEventListener('keyup', ViewWorkout.handleKeyUp);
    },

    handleKeyDown: (e) => {
        const s = ViewWorkout.state;
        
        if (e.key.toLowerCase() === 'x') {
            ViewWorkout.simTime();
            return;
        }

        if (s.status !== 'working') return;
        if (e.key.toLowerCase() === 'z') {
            s.simState.activeKey = 'z';
            s.simState.direction = 1;
            s.side = 'L';
        } else if (e.key.toLowerCase() === 'm') {
            s.simState.activeKey = 'm';
            s.simState.direction = 1;
            s.side = 'R';
        }
    },

    handleKeyUp: (e) => {
        const s = ViewWorkout.state;
        if (e.key.toLowerCase() === 'z' || e.key.toLowerCase() === 'm') {
            s.simState.direction = -1;
        }
    },

    updateSimLogic: () => {
        const s = ViewWorkout.state;
        if (s.status !== 'working') return;

        // Stroke Simulation
        if (s.simState.direction === 1) {
            s.currentStroke = Math.min(100, s.currentStroke + 5);
            s.currentPower = Math.min(300, s.currentPower + 10 + Math.random()*10);
            s.simState.maxPower = Math.max(s.simState.maxPower, s.currentPower);
        } else if (s.simState.direction === -1) {
            s.currentStroke = Math.max(0, s.currentStroke - 5);
            s.currentPower = Math.max(0, s.currentPower - 10);
            
            // Count Rep on return to 0
            if (s.currentStroke === 0 && s.simState.activeKey) {
                s.currentReps++;
                s.powerHistory.push({ val: s.simState.maxPower, side: s.side });
                s.simState.activeKey = null;
                s.simState.direction = 0;
                s.simState.maxPower = 0;
                ViewWorkout.checkRepFinish();
            }
        }
    },

    checkRepFinish: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式' || action.measure === '计时';

        if (!isTimeBased && s.currentReps >= s.targetReps) {
            ViewWorkout.finishSet();
        }
    },

    simTime: () => {
        const s = ViewWorkout.state;
        if (s.status === 'working') s.setTimer += 5;
        else if (s.status === 'resting' || s.status === 'countdown') s.timer -= 5;
    },

    // --- Rendering ---

    render: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const set = action.setDetails[s.setIdx];
        const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式' || action.measure === '计时';

        // Top Screen Info
        let topInfo = document.querySelector('.wk-top-info');
        if (!topInfo) {
            topInfo = document.querySelector('.wk-overlay-info');
            if (topInfo) {
                topInfo.classList.add('wk-top-info');
            } else {
                topInfo = document.createElement('div');
                topInfo.className = 'wk-top-info';
                document.querySelector('.wk-video-area').appendChild(topInfo);
            }
        }
        
        let nameSuffix = '';
        if (s.side === 'L') nameSuffix = ' (左侧)';
        if (s.side === 'R') nameSuffix = ' (右侧)';
        
        const targetStr = isTimeBased ? `${s.targetReps}s` : `${s.targetReps}次`;
        
        topInfo.innerHTML = `
            <div class="wk-phase-label">${phase.type}</div>
            <div class="wk-main-title">${action.name}${nameSuffix}</div>
            <div class="wk-sub-info">第 ${s.setIdx + 1} / ${action.sets} 组 · 目标 ${targetStr}</div>
        `;

        // Update Action List Overlay
        document.getElementById('wk-al-name').innerText = phase.type;
        document.getElementById('wk-al-set').innerText = `${action.name} ${s.setIdx + 1}/${action.sets}`;
        
        // Update Progress Bar
        const pct = s.totalSets > 0 ? Math.min(100, (s.completedSets / s.totalSets) * 100) : 0;
        const fill = document.getElementById('wk-prog-fill');
        const text = document.getElementById('wk-prog-text');
        if(fill) fill.style.width = `${pct}%`;
        if(text) text.innerText = `${Math.round(pct)}%`;
    },

    renderCountdown: () => {
        const el = document.getElementById('wk-overlay-cnt');
        if(el) {
            el.style.display = 'flex'; // Ensure flex layout
            // Force reflow for transition
            void el.offsetWidth;
            el.classList.add('active');
        }
        ViewWorkout.updateCountdownUI();
    },

    updateCountdownUI: () => {
        const s = ViewWorkout.state;
        document.getElementById('wk-cnt-num').innerText = Math.ceil(s.timer);
    },

    renderRest: () => {
        const el = document.getElementById('wk-overlay-rest');
        if(el) {
            el.style.display = 'flex';
            void el.offsetWidth;
            el.classList.add('active');
        }
        
        // Hide active counter during rest
        const counter = document.getElementById('wk-active-counter');
        if(counter) {
            counter.classList.remove('visible');
            counter.classList.remove('emphasis');
        }

        ViewWorkout.updateRestUI();
    },

    updateRestUI: () => {
        const s = ViewWorkout.state;
        document.getElementById('wk-rest-time').innerText = Math.ceil(s.timer);
    },

    updateDashboard: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式' || action.measure === '计时';

        // Power Decay
        // if (s.currentPower > 0) s.currentPower *= 0.95; // Handled by sim logic now
        
        // Stroke Simulation (Sine wave if working)
        if (s.status !== 'working') {
             s.currentStroke = 0;
        }
        
        // Total Time
        const m = Math.floor(s.totalTime / 60);
        const sec = Math.floor(s.totalTime % 60);
        document.getElementById('wk-total-time').innerText = `${m < 10 ? '0'+m : m}:${sec < 10 ? '0'+sec : sec}`;

        // Active Counter (Bottom Screen)
        let counterVal = '';
        if (isTimeBased) {
            counterVal = Math.ceil(s.targetReps - s.setTimer) + 's';
        } else {
            counterVal = s.currentReps + '次';
        }
        
        // Inject counter into dashboard if not present
        let counterEl = document.getElementById('wk-active-counter');
        if (!counterEl) {
            counterEl = document.createElement('div');
            counterEl.id = 'wk-active-counter';
            counterEl.className = 'wk-active-counter';
            const center = document.querySelector('.wk-dash-center');
            if(center) center.insertBefore(counterEl, center.firstChild);
        }
        counterEl.innerText = counterVal;

        // Fix: Ensure visibility if working (handles case where element was created after countdown finished)
        if (s.status === 'working' && !counterEl.classList.contains('visible')) {
            counterEl.classList.add('visible');
        }
    },

    drawPowerChart: () => {
        const s = ViewWorkout.state;
        const cvs = document.getElementById('wk-power-chart');
        if (!cvs) return;
        const ctx = cvs.getContext('2d');
        // Resize canvas to display size
        if (cvs.width !== cvs.clientWidth) {
            cvs.width = cvs.clientWidth;
            cvs.height = cvs.clientHeight;
        }
        const w = cvs.width;
        const h = cvs.height;

        ctx.clearRect(0, 0, w, h);
        
        // Show last 10 reps
        const displayData = s.powerHistory.slice(-10);
        const barWidth = w / 10;

        for (let i = 0; i < displayData.length; i++) {
            const item = displayData[i];
            const barH = (item.val / 300) * h;
            const x = i * barWidth;
            const y = h - barH;
            ctx.fillStyle = item.side === 'R' ? '#0a84ff' : '#32C48C';
            ctx.fillRect(x + 2, y, barWidth - 4, barH);
        }
    },

    drawStrokeChart: () => {
        const s = ViewWorkout.state;
        const cvs = document.getElementById('wk-stroke-chart');
        if (!cvs) return;
        const ctx = cvs.getContext('2d');
        if (cvs.width !== cvs.clientWidth) {
            cvs.width = cvs.clientWidth;
            cvs.height = cvs.clientHeight;
        }
        const w = cvs.width;
        const h = cvs.height;

        s.strokeHistory.push({val: s.currentStroke, side: s.side});
        s.strokeHistory.shift();

        ctx.clearRect(0, 0, w, h);
        
        ctx.lineWidth = 3;
        // Draw segments to handle color changes
        for (let i = 0; i < s.strokeHistory.length; i++) {
            const point = s.strokeHistory[i];
            const x = (i / (s.strokeHistory.length - 1)) * w;
            const y = h - (point.val / 100) * h;
            ctx.fillStyle = point.side === 'R' ? '#0a84ff' : '#32C48C';
            ctx.fillRect(x, y, 2, 2); // Simple dot rendering for multi-color line
        }
    },

    // --- Dial Logic ---
    initDial: () => {
        const wrapper = document.getElementById('wk-dial-wrapper');
        if(!wrapper) return;
        
        // Update SVG Path for 2/3 circle with gap at bottom
        // Start 135 deg (bottom left), End 45 deg (bottom right) via Top
        // Coordinates for r=40, c=50,50
        // Start: x=21.72, y=78.28
        // End: x=78.28, y=78.28
        
        // Inject Toast
        if (!wrapper.querySelector('.wk-dial-toast')) {
            wrapper.insertAdjacentHTML('beforeend', '<div class="wk-dial-toast" id="wk-dial-toast">已为你推荐重量</div>');
        }

        const track = wrapper.querySelector('.wk-dial-track');
        const progress = wrapper.querySelector('.wk-dial-progress');
        const d = "M 21.72 78.28 A 40 40 0 1 1 78.28 78.28";
        if(track) track.setAttribute('d', d);
        if(progress) {
            progress.setAttribute('d', d);
            // Total length approx 188.5
            progress.style.strokeDasharray = 188.5;
        }

        const handleMove = (e) => {
            if (!ViewWorkout.state.isDialDragging) return;
            e.preventDefault();
            const rect = wrapper.getBoundingClientRect();
            const cx = rect.left + rect.width / 2;
            const cy = rect.top + rect.height / 2;
            const clientX = e.touches ? e.touches[0].clientX : e.clientX;
            const clientY = e.touches ? e.touches[0].clientY : e.clientY;
            
            // Calculate angle
            let angle = Math.atan2(clientY - cy, clientX - cx) * 180 / Math.PI;
            // atan2: Right=0, Bottom=90, Left=180, Top=-90
            // Map to 0-360 where 0 is Bottom-Left (135 deg in standard)
            
            // Standard degrees: 135 (Start) -> -90 (Top) -> 45 (End)
            // We want a continuous value.
            // Rotate so Start is 0.
            // Start is 135. 
            // angle - 135.
            // 135 - 135 = 0.
            // 45 - 135 = -90 -> +360 = 270.
            // -90 (Top) - 135 = -225 -> +360 = 135.
            
            let relativeAngle = angle - 135;
            if (relativeAngle < 0) relativeAngle += 360;
            
            // Clamp to 0 - 270
            if (relativeAngle > 270) {
                // Closer to start or end?
                if (relativeAngle > 315) relativeAngle = 0; // Snap to start
                else relativeAngle = 270; // Snap to end
            }
            
            // Map 0-270 to Weight 2-50
            const pct = relativeAngle / 270;
            const w = 2 + pct * (50 - 2);
            
            // Snap to 0.5
            const snapped = Math.round(w * 2) / 2;
            
            if (snapped !== ViewWorkout.state.currentLoad) {
                ViewWorkout.state.currentLoad = snapped;
                ViewWorkout.updateDialUI();
            }
        };

        wrapper.addEventListener('mousedown', (e) => {
            ViewWorkout.state.isDialDragging = true;
            document.addEventListener('mousemove', handleMove);
            document.addEventListener('mouseup', () => {
                ViewWorkout.state.isDialDragging = false;
                document.removeEventListener('mousemove', handleMove);
            }, {once:true});
            handleMove(e); // Immediate update
        });
        
        wrapper.addEventListener('touchstart', (e) => {
            ViewWorkout.state.isDialDragging = true;
            document.addEventListener('touchmove', handleMove, {passive:false});
            document.addEventListener('touchend', () => {
                ViewWorkout.state.isDialDragging = false;
                document.removeEventListener('touchmove', handleMove);
            }, {once:true});
        });
    },

    adjustWeight: (delta) => {
        let v = ViewWorkout.state.currentLoad + delta;
        v = Math.max(2, Math.min(50, v));
        v = Math.round(v * 2) / 2; // 0.5 step
        ViewWorkout.state.currentLoad = v;
        ViewWorkout.updateDialUI();
    },

    updateDialUI: () => {
        const val = ViewWorkout.state.currentLoad;
        document.getElementById('wk-dial-val').innerText = val.toFixed(1);
        
        // Update Progress Arc
        // Total length approx 188.5
        const maxLen = 188.5;
        const pct = (val - 2) / (50 - 2);
        const offset = maxLen - (pct * maxLen);
        document.getElementById('wk-dial-progress').style.strokeDashoffset = offset;
    },

    showDialToast: () => {
        const t = document.getElementById('wk-dial-toast');
        if(t) {
            t.classList.add('show');
            setTimeout(() => t.classList.remove('show'), 3000);
        }
    },

    // --- Action List Logic ---
    toggleActionList: () => {
        document.getElementById('wk-action-list').classList.toggle('expanded');
    },

    renderActionList: () => {
        const ctx = ViewWorkout.state.ctx;
        const currentP = ViewWorkout.state.phaseIdx;
        const currentA = ViewWorkout.state.actionIdx;
        
        let html = '';
        ctx.phases.forEach((p, pIdx) => {
            html += `<div class="wk-al-phase">${p.type}</div>`;
            p.actions.forEach((a, aIdx) => {
                const isActive = (pIdx === currentP && aIdx === currentA);
                const mirrorBadge = a.mirror ? '<span class="wk-al-badge">双侧</span>' : '';
                
                // Calculate completed sets
                let completed = 0;
                if (pIdx < currentP) completed = a.sets;
                else if (pIdx === currentP && aIdx < currentA) completed = a.sets;
                else if (pIdx === currentP && aIdx === currentA) completed = ViewWorkout.state.setIdx;
                
                const progress = `<span style="${isActive ? 'color:var(--primary)' : 'color:#666'}">${completed}/${a.sets}</span>`;
                html += `
                <div class="wk-al-item ${isActive?'active':''}" onclick="ViewWorkout.jumpToAction(${pIdx}, ${aIdx})">
                    <span>${a.name} ${mirrorBadge}</span>
                    ${progress}
                </div>`;
            });
        });
        document.getElementById('wk-al-body').innerHTML = html;
    },

    jumpToAction: (pIdx, aIdx) => {
        const s = ViewWorkout.state;
        s.phaseIdx = pIdx;
        s.actionIdx = aIdx;
        s.setIdx = 0;
        ViewWorkout.prepareSet();
        document.getElementById('wk-action-list').classList.remove('expanded');
    }
};
