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
        side: null // 'L' | 'R' | null
    },

    start: (ctx) => {
        // Init State
        const s = ViewWorkout.state;
        s.ctx = ctx;
        s.phaseIdx = 0;
        s.actionIdx = 0;
        s.setIdx = 0;
        s.totalTime = 0;
        s.powerHistory = new Array(50).fill(0);
        s.strokeHistory = new Array(100).fill(0);
        s.isPaused = false;
        
        App.switchView('view-workout');
        
        // Start Global Timer
        if (s.interval) clearInterval(s.interval);
        s.interval = setInterval(ViewWorkout.tick, 100); // 100ms tick for smooth UI

        ViewWorkout.initDial();
        ViewWorkout.prepareSet();
    },

    prepareSet: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const set = action.setDetails[s.setIdx];

        s.status = 'countdown';
        s.timer = 3; // 3s countdown
        s.setTimer = 0;
        s.currentReps = 0;
        s.targetReps = set.reps;
        s.currentPower = 0;
        s.currentStroke = 0;
        s.side = action.mirror ? 'L' : null;
        
        // Auto-set Weight
        s.currentLoad = set.load || 20;
        ViewWorkout.updateDialUI();

        ViewWorkout.render();
        ViewWorkout.renderActionList();
        ViewWorkout.renderCountdown();
    },

    tick: () => {
        const s = ViewWorkout.state;
        if (s.isPaused) return;

        // Global Stats
        if (s.status !== 'finished') s.totalTime += 0.1;

        // State Machine
        if (s.status === 'countdown') {
            s.timer -= 0.1;
            if (s.timer <= 0) {
                s.status = 'working';
                s.timer = 0;
                ViewWorkout.render(); // Remove overlay
            } else {
                ViewWorkout.updateCountdownUI();
            }
        } else if (s.status === 'working') {
            s.setTimer += 0.1;
            
            // Auto-finish time-based sets
            const phase = s.ctx.phases[s.phaseIdx];
            const action = phase.actions[s.actionIdx];
            const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式';
            
            if (isTimeBased && s.setTimer >= s.targetReps) { // targetReps stores seconds for time-based
                ViewWorkout.finishSet();
            }
            
            ViewWorkout.updateDashboard();
            ViewWorkout.drawPowerChart();
            ViewWorkout.drawStrokeChart();
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

        // Check if last set of last action of last phase
        const isLastSet = s.setIdx >= action.sets - 1;
        const isLastAction = s.actionIdx >= phase.actions.length - 1;
        const isLastPhase = s.phaseIdx >= s.ctx.phases.length - 1;

        if (isLastSet && isLastAction && isLastPhase) {
            ViewWorkout.finishWorkout();
            return;
        }

        // Determine Rest Time
        let restTime = 0;
        if (isLastSet) {
            // Action/Phase Switch
            restTime = (phase.strategy.restRound !== undefined) ? phase.strategy.restRound : 30; 
        } else {
            // Set Switch
            restTime = (phase.strategy.rest !== undefined) ? phase.strategy.rest : 30;
        }

        if (restTime > 0) {
            s.status = 'resting';
            s.timer = restTime;
            ViewWorkout.renderRest();
        } else {
            ViewWorkout.nextSet();
        }
    },

    nextSet: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
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
        ViewWorkout.prepareSet();
    },

    finishWorkout: () => {
        const s = ViewWorkout.state;
        s.status = 'finished';
        clearInterval(s.interval);
        
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
    
    togglePause: () => {
        const s = ViewWorkout.state;
        s.isPaused = !s.isPaused;
        const btn = document.getElementById('wk-pause-btn');
        if(btn) btn.innerText = s.isPaused ? '▶' : 'II';
    },

    simRep: () => {
        const s = ViewWorkout.state;
        if (s.status !== 'working') return;
        
        s.currentReps++;
        s.currentPower = Math.floor(Math.random() * 50 + 150); // Spike power
        s.currentStroke = 100; // Spike stroke
        
        // Visual Feedback
        const repEl = document.getElementById('wk-rep-val');
        if(repEl) {
            repEl.style.transform = 'scale(1.5)';
            repEl.style.color = '#fff';
            setTimeout(() => {
                repEl.style.transform = 'scale(1)';
                repEl.style.color = 'var(--primary)';
            }, 200);
        }

        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式';

        if (!isTimeBased && s.currentReps >= s.targetReps) {
            ViewWorkout.finishSet();
        }
    },

    simTime: () => {
        const s = ViewWorkout.state;
        if (s.status === 'working') s.setTimer += 5;
        if (s.status === 'resting') s.timer = Math.max(1, s.timer - 5);
    },

    simPower: () => {
        const s = ViewWorkout.state;
        s.currentPower = Math.floor(Math.random() * 100 + 200);
        s.currentStroke = 80;
    },

    // --- Rendering ---

    render: () => {
        const s = ViewWorkout.state;
        const phase = s.ctx.phases[s.phaseIdx];
        const action = phase.actions[s.actionIdx];
        const set = action.setDetails[s.setIdx];
        const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式';

        // Header
        document.getElementById('wk-phase-name').innerText = phase.type;        
        
        let nameSuffix = '';
        if (s.side === 'L') nameSuffix = ' (左侧)';
        if (s.side === 'R') nameSuffix = ' (右侧)';
        
        document.getElementById('wk-al-name').innerText = action.name + nameSuffix;
        document.getElementById('wk-al-set').innerText = `Set ${s.setIdx + 1}/${action.sets} · ${set.load}kg x ${set.reps}${action.mirror ? '/侧' : ''}`;
        
        // Hide overlays
        document.getElementById('wk-overlay-cnt').style.display = 'none';
        document.getElementById('wk-overlay-rest').style.display = 'none';
    },

    renderCountdown: () => {
        const el = document.getElementById('wk-overlay-cnt');
        el.style.display = 'flex';
        ViewWorkout.updateCountdownUI();
    },

    updateCountdownUI: () => {
        const s = ViewWorkout.state;
        document.getElementById('wk-cnt-num').innerText = Math.ceil(s.timer);
    },

    renderRest: () => {
        const el = document.getElementById('wk-overlay-rest');
        el.style.display = 'flex';
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
        const isTimeBased = action.paradigm === '间歇范式' || action.paradigm === '流式范式';

        // Power Decay
        if (s.currentPower > 0) s.currentPower *= 0.95;
        
        // Stroke Simulation (Sine wave if working)
        if (s.status === 'working') {
            s.currentStroke = 50 + Math.sin(Date.now() / 500) * 40;
        } else {
            s.currentStroke = 0;
        }
        
        // Total Time
        const m = Math.floor(s.totalTime / 60);
        const sec = Math.floor(s.totalTime % 60);
        document.getElementById('wk-total-time').innerText = `${m < 10 ? '0'+m : m}:${sec < 10 ? '0'+sec : sec}`;
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

        // Update History
        s.powerHistory.push(s.currentPower);
        s.powerHistory.shift();

        ctx.clearRect(0, 0, w, h);
        
        const barWidth = w / s.powerHistory.length;
        ctx.fillStyle = '#269e70';

        for (let i = 0; i < s.powerHistory.length; i++) {
            const val = s.powerHistory[i];
            const barH = (val / 300) * h;
            const x = i * barWidth;
            const y = h - barH;
            ctx.fillRect(x, y, barWidth - 1, barH);
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

        s.strokeHistory.push(s.currentStroke);
        s.strokeHistory.shift();

        ctx.clearRect(0, 0, w, h);
        ctx.beginPath();
        for (let i = 0; i < s.strokeHistory.length; i++) {
            const val = s.strokeHistory[i];
            const x = (i / (s.strokeHistory.length - 1)) * w;
            const y = h - (val / 100) * h;
            if(i===0) ctx.moveTo(x,y);
            else ctx.lineTo(x,y);
        }
        ctx.strokeStyle = '#2979ff';
        ctx.lineWidth = 2;
        ctx.stroke();
    },

    // --- Dial Logic ---
    initDial: () => {
        const wrapper = document.getElementById('wk-dial-wrapper');
        if(!wrapper) return;
        
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
            // Normalize angle to 0-360 starting from 9 o'clock clockwise
            // Our dial starts at 150deg (bottom left) and goes 240deg to 390deg (bottom right)
            // atan2 returns -180 to 180.
            // Map to 0-240 range.
            
            // Shift angle so start (150deg) is 0.
            // 150deg is roughly 5 o'clock position in standard math? No, 0 is 3 o'clock.
            // 150 is bottom right. Wait.
            // CSS rotate(150deg) rotates the whole SVG.
            // Let's simplify: Map Y position or just use simple distance for now, or proper angle.
            // Proper angle:
            let deg = angle + 90; // 0 at 12 o'clock
            if (deg < 0) deg += 360;
            
            // Map to value 2-50
            // This is complex to get right without visual feedback loop.
            // Let's use a simpler approach: Dragging up/down changes value.
            
            const dy = (ViewWorkout.state.lastY - clientY);
            ViewWorkout.adjustWeight(dy * 0.1);
            ViewWorkout.state.lastY = clientY;
        };

        wrapper.addEventListener('mousedown', (e) => {
            ViewWorkout.state.isDialDragging = true;
            ViewWorkout.state.lastY = e.clientY;
            document.addEventListener('mousemove', handleMove);
            document.addEventListener('mouseup', () => {
                ViewWorkout.state.isDialDragging = false;
                document.removeEventListener('mousemove', handleMove);
            }, {once:true});
        });
        
        wrapper.addEventListener('touchstart', (e) => {
            ViewWorkout.state.isDialDragging = true;
            ViewWorkout.state.lastY = e.touches[0].clientY;
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
        // Total arc length for r=40 is 2*PI*40 = 251.
        // We show 240 degrees of it, so max stroke is 251 * (240/360) = 167.
        // Let's assume full circle for simplicity of CSS, but masked.
        // Actually, CSS stroke-dasharray="200" is set.
        // Map 2-50 to 0-200 offset.
        const pct = (val - 2) / (50 - 2);
        const offset = 200 - (pct * 200);
        document.getElementById('wk-dial-progress').style.strokeDashoffset = offset;
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
                html += `
                <div class="wk-al-item ${isActive?'active':''}" onclick="ViewWorkout.jumpToAction(${pIdx}, ${aIdx})">
                    <span>${a.name} ${mirrorBadge}</span>
                    <span>${a.sets}组</span>
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
