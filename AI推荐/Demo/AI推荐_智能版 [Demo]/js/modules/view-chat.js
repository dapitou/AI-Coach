window.ViewChat = {
    prevStep: () => {
        if (window.store.step > 0) {
            window.store.step--;
            const history = document.getElementById('chat-history');
            if(history.lastElementChild && !history.lastElementChild.classList.contains('chat-bubble')) history.removeChild(history.lastElementChild);
            if(history.lastElementChild && history.lastElementChild.classList.contains('chat-ai')) history.removeChild(history.lastElementChild);
            if(history.lastElementChild && history.lastElementChild.classList.contains('chat-user')) history.removeChild(history.lastElementChild);
            if(history.lastElementChild && history.lastElementChild.classList.contains('chat-ai')) history.removeChild(history.lastElementChild);
            
            App.updateSummary();
            App.nextStep();
        } else {
            App.reset();
        }
    },

    nextStep: () => {
        const flow = window.store.flow;
        const step = window.store.step;
        const chatHistory = document.getElementById('chat-history');

        const bubbles = chatHistory.querySelectorAll('.chat-bubble');
        bubbles.forEach(b => b.classList.add('chat-history-dim'));
        
        const flows = CONFIG.FLOWS;

        if (flow === 'course' && step === 1) {
             const type = window.store.inputs['type'];
             const lockTypes = ['HIIT', '有氧', '搏击'];
             if (lockTypes.includes(type)) {
                 window.store.inputs['targets'] = ['全身'];
                 window.store.step++;
                 App.nextStep();
                 return;
             }
        }

        const currentFlow = flows[flow];
        
        if (step >= currentFlow.length) {
            // 5. Completion Feedback
            App.showTyping();
            setTimeout(() => {
                App.hideTyping();
                const confirmText = TEXT_VARIANTS.analysisStart[Math.floor(Math.random() * TEXT_VARIANTS.analysisStart.length)];
                const bubble = document.createElement('div');
                bubble.className = 'chat-bubble chat-ai';
                
                // 布局防抖优化：预计算高度
                bubble.style.opacity = '0';
                bubble.innerText = confirmText;
                chatHistory.appendChild(bubble);
                const h = bubble.offsetHeight;
                bubble.style.height = h + 'px';
                bubble.style.opacity = '1';
                bubble.innerText = '';
                
                App.typeWriter(bubble, confirmText, 30, () => { bubble.style.height = 'auto'; });
                Voice.speak(confirmText);
                
                // Scroll to align
                ViewChat.alignBubble(bubble);

                setTimeout(() => App.startReasoning(), 2000);
            }, 600);
            return;
        }

        const config = currentFlow[step];
        if (config.key === 'duration') config.default = window.store.user.duration;

        // Data-driven variant selection
        const variants = (config.variant && TEXT_VARIANTS[config.variant]) ? TEXT_VARIANTS[config.variant] : [config.q];
        const qText = variants[Math.floor(Math.random() * variants.length)];
        
        App.showTyping();

        setTimeout(() => {
            App.hideTyping();
            const bubble = document.createElement('div');
            bubble.className = 'chat-bubble chat-ai';
            
            // 布局防抖优化：预计算高度，防止文字换行导致选项跳动
            bubble.style.opacity = '0';
            bubble.innerText = qText;
            chatHistory.appendChild(bubble);
            const h = bubble.offsetHeight;
            bubble.style.height = h + 'px';
            bubble.style.opacity = '1';
            bubble.innerText = '';

            let optionsHtml = '';
            if (config.type === 'slider') {
                optionsHtml = `
                    <div class="chat-slider-box">
                        <div style="display:flex;justify-content:space-between;margin-bottom:10px;color:#fff;font-weight:700;">
                            <span>时长</span><span id="slider-val">${config.default || config.min} ${config.unit}</span>
                        </div>
                        <input type="range" min="${config.min}" max="${config.max}" step="${config.step}" value="${config.default || config.min}" style="width:100%" oninput="document.getElementById('slider-val').innerText = this.value + ' ${config.unit}'">
                        <div style="display:flex; justify-content:center; margin-top:15px;"><div class="opt-chip confirm" onclick="App.handleInput('${config.key}', this.parentElement.previousElementSibling.value, false)">确认</div></div>
                    </div>`;
            } else {
                const gridClass = (config.key === 'targets') ? 'options-grid cols-4' : 'options-grid';
                optionsHtml = `<div class="${gridClass}">` + config.opts.map(o => {
                    const isActive = (config.key === 'days' && window.store.user.days && window.store.user.days.includes(o)) ? 'active' : '';
                    let subText = '';
                    if (config.key === 'days') subText = `<span class="chat-sub-text">${isActive ? '训练' : '休息'}</span>`; 
                    return `<div class="opt-chip ${isActive}" onclick="App.handleInput('${config.key}', '${o}', ${config.multi}, this); App.toggleDayText(this)"><span>${o}</span>${subText}</div>`;
                }).join('') + `</div>`;
            }

            if(config.multi) {
                optionsHtml += `<div class="options-grid" style="margin-top:10px; justify-content:center;"><div class="opt-chip confirm" onclick="App.confirmMulti('${config.key}', this)">确认</div></div>`;
            }
            
            if (step > 0) {
                optionsHtml += `<div style="margin-top:15px; text-align:center;"><span onclick="App.prevStep()" style="font-size:12px; color:#666; cursor:pointer; padding:5px 10px;">↩ 上一步</span></div>`;
            }
            
            const optContainer = document.createElement('div');
            optContainer.innerHTML = optionsHtml;
            chatHistory.appendChild(optContainer);

            App.typeWriter(bubble, qText, 30, () => { bubble.style.height = 'auto'; }); 
            Voice.speak(qText);

            ViewChat.alignBubble(bubble);
        }, 500);
    },

    alignBubble: (bubble) => {
        // 1. Align Top Logic
        requestAnimationFrame(() => {
            const container = document.getElementById('chat-history');
            
            // Capture anchor from the first bubble (step 0)
            if (window.store.step === 0 || window.store.chatAnchorY == null) {
                window.store.chatAnchorY = bubble.offsetTop;
            }
            
            // Scroll to align current bubble to anchor
            const target = bubble.offsetTop - window.store.chatAnchorY;
            App.scrollTo(container, target, 800);
        });
    },
    
    toggleDayText: (el) => {
        const sub = el.querySelector('.chat-sub-text');
        if(sub) sub.innerText = el.classList.contains('active') ? '训练' : '休息';
    },

    handleDaysVoiceInput: (text, container) => {
        const dayMap = { '一': '周一', '二': '周二', '三': '周三', '四': '周四', '五': '周五', '六': '周六', '日': '周日', '天': '周日', '七': '周日', '1': '周一', '2': '周二', '3': '周三', '4': '周四', '5': '周五', '6': '周六', '7': '周日' };
        const segments = text.split(/[，。,.;；\s]+/);
        const chips = Array.from(container.querySelectorAll('.opt-chip')).filter(c => !c.getAttribute('onclick').includes('confirmMulti'));
        
        segments.forEach(seg => {
            if (!seg.trim()) return;
            let targets = [];
            const regex = /[一二三四五六日天七1-7]/g;
            let match;
            while ((match = regex.exec(seg)) !== null) { if (dayMap[match[0]]) targets.push(dayMap[match[0]]); }
            if (seg.includes('周末')) targets.push('周六', '周日');
            if (seg.includes('工作日')) targets.push('周一', '周二', '周三', '周四', '周五');
            if (seg.includes('每天') || seg.includes('天天') || seg.includes('全选')) targets = ['周一','周二','周三','周四','周五','周六','周日'];
            targets = [...new Set(targets)];
            if (targets.length === 0) return;

            const negKeywords = ['不练', '取消', '休息', '去掉', '删除', '不用', '排除', '关掉'];
            const modKeywords = ['改成', '换成', '修改为', '只有', '只要', '重选', '变更为', '全部取消', '只练'];
            const isNeg = negKeywords.some(k => seg.includes(k));
            const isMod = modKeywords.some(k => seg.includes(k));
            
            if (isMod) {
                chips.forEach(c => { if(c.classList.contains('active')) { c.classList.remove('active'); App.toggleDayText(c); } });
                targets.forEach(t => { const chip = chips.find(c => c.innerText.includes(t)); if(chip) { chip.classList.add('active'); App.toggleDayText(chip); } });
            } else if (isNeg) {
                targets.forEach(t => { const chip = chips.find(c => c.innerText.includes(t)); if(chip && chip.classList.contains('active')) { chip.classList.remove('active'); App.toggleDayText(chip); } });
            } else {
                targets.forEach(t => { const chip = chips.find(c => c.innerText.includes(t)); if(chip && !chip.classList.contains('active')) { chip.classList.add('active'); App.toggleDayText(chip); } });
            }
        });
        
        if (text.includes('全部取消') || text.includes('全不选') || text.includes('清空')) {
            chips.forEach(c => { c.classList.remove('active'); App.toggleDayText(c); });
        }
        
        if (['确认', '好了', '完成', '下一步', '是的', 'OK'].some(k => text.toLowerCase().includes(k.toLowerCase()))) {
            if (container.id === 'schedule-days-list') App.confirmSchedule();
            else App.confirmMulti('days', null);
        }
    },

    showTyping: () => {
        const history = document.getElementById('chat-history');
        if (document.getElementById('typing-indicator')) return;
        const typing = document.createElement('div');
        typing.id = 'typing-indicator';
        typing.className = 'chat-typing';
        typing.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
        history.appendChild(typing);
        history.scrollTop = history.scrollHeight;
    },

    hideTyping: () => {
        const typing = document.getElementById('typing-indicator');
        if (typing) typing.remove();
    },

    handleVoiceInput: (text, isFinal) => {
        const flow = window.store.flow;
        
        if (document.getElementById('modal-schedule').classList.contains('active')) {
            App.handleDaysVoiceInput(text, document.getElementById('schedule-days-list'));
            return;
        }

        if (!flow) {
            const subtitle = document.getElementById('home-subtitle');
            if (subtitle) {
                subtitle.innerText = text;
                subtitle.style.opacity = 1;
            }

            const keywords = {
                'course': ['一节课', '课程', '单课', '练一练', '客程', '刻成', '一杰克'],
                'plan': ['计划', '周期', '长线', '激化', '急化', '极化', '集画', '济化', '规划']
            };
            
            let matchedType = null;
            for (const [type, words] of Object.entries(keywords)) {
                if (words.some(w => text.includes(w))) {
                    matchedType = type;
                    break;
                }
            }

            if (matchedType) {
                if (subtitle) subtitle.innerText = '';
                const chatHistory = document.getElementById('chat-history');
                const bubble = document.createElement('div');
                bubble.className = 'chat-bubble chat-user';
                bubble.innerText = text;
                chatHistory.appendChild(bubble);
                
                App.startFlow(matchedType);
                return; 
            }
            return;
        }

        let userBubble = document.getElementById('temp-user-bubble');
        if (!userBubble && document.getElementById('view-chat').classList.contains('active')) {
            userBubble = document.createElement('div');
            userBubble.id = 'temp-user-bubble';
            userBubble.className = 'chat-bubble chat-user interim';
            document.getElementById('chat-history').appendChild(userBubble);
        }
        
        if (isFinal) {
            if (['退出', '结束', '返回首页', '取消'].some(k => text.includes(k))) {
                Voice.speak("好的，已退出。");
                App.reset();
                return;
            }
            if (['上一步', '返回', '重选', '不对', '修改'].some(k => text.includes(k))) {
                if (document.getElementById('view-chat').classList.contains('active')) {
                    Voice.speak("好的，重新选择。");
                    if (userBubble) userBubble.remove();
                    App.prevStep();
                    return;
                }
            }
        }

        const step = window.store.step;
        const flows = {
            'course': [{key:'type', opts:CONSTANTS.ENUMS.COURSE_TYPES}, {key:'targets', opts:CONSTANTS.PARTS}, {key:'duration', type:'slider', min:20, max:90}],
            'plan': [{key:'cycle', type:'slider', min:1, max:12}, {key:'days', opts:['周一','周二','周三','周四','周五','周六','周日'], multi:true}, {key:'duration', opts:['30','45','60']}]
        };

        let currentOpts = [];
        if (!flow) {
            currentOpts = ['一节课', '课程', '计划', '周期'];
        } else {
            if (flows[flow] && flows[flow][step]) {
                currentOpts = flows[flow][step].opts || [];
            }
            if (window.store.pendingFatigue) {
                const p = window.store.pendingFatigue;
                currentOpts = ['切换', '不切换', '确认', '取消', '是', '否'];
                if (p.recommended && p.recommended.length) currentOpts.push(p.recommended[0]);
                if (p.hit) currentOpts.push(p.hit);
            }
        }
        
        let html = text;
        let matched = null;
        
        let allowNumber = false;
        if (flow && flows[flow] && flows[flow][step]) {
            const cfg = flows[flow][step];
            if (cfg.type === 'slider' || ['duration', 'cycle', 'freq'].includes(cfg.key)) allowNumber = true;
        }
        
        const numVal = allowNumber ? App.cnToInt(text) : null;
        
        if (numVal !== null) {
            matched = numVal.toString();
            const matchStr = text.match(/[0-9]+|[一二两三四五六七八九十]+/);
            if(matchStr) html = html.replace(matchStr[0], `<span class="keyword-highlight">${matched}</span>`);
        } else {
            if (currentOpts.length) {
                if (flow && flows[flow][step].multi) {
                    const matches = [];
                    currentOpts.forEach(opt => {
                        if (text.includes(opt)) matches.push(opt);
                    });
                    if (matches.length > 0) {
                        matches.forEach(m => {
                            html = html.replace(m, `<span class="keyword-highlight">${m}</span>`);
                        });
                    }
                }
                
                currentOpts.forEach(opt => {
                    if (text.includes(opt) || (opt.length > 1 && text.includes(opt[0]))) {
                        html = html.replace(opt, `<span class="keyword-highlight">${opt}</span>`);
                        matched = opt;
                    }
                });
            }
        }
        
        if (userBubble) {
            userBubble.innerHTML = html;
            document.getElementById('chat-history').scrollTop = document.getElementById('chat-history').scrollHeight;
        }

        if (isFinal) {
            if (userBubble) {
                userBubble.removeAttribute('id');
                userBubble.classList.remove('interim');
            }
            
            if (matched) {
                if (flow) {
                    const config = flows[flow][step];
                    if(config) {
                        if (config.multi) {
                            if (config.key === 'days') {
                                const history = document.getElementById('chat-history');
                                let optContainer = null;
                                for (let i = history.children.length - 1; i >= 0; i--) {
                                    if (history.children[i].querySelector('.options-grid')) {
                                        optContainer = history.children[i];
                                        break;
                                    }
                                }
                                if (optContainer) {
                                    App.handleDaysVoiceInput(text, optContainer);
                                }
                                return;
                            }

                            const matches = currentOpts.filter(opt => {
                                if (text.includes(opt)) return true;
                                if (config.key === 'targets' && opt.length > 1 && text.includes(opt[0])) return true;
                                return false;
                            });
                            
                            const modKeywords = ['改成', '换成', '修改为', '只有', '只要', '重选', '变更为', '全部取消'];
                            const isMod = modKeywords.some(k => text.includes(k));

                            if (matches.length > 0) {
                                if (isMod) {
                                    const allChips = Array.from(document.querySelectorAll('.opt-chip'));
                                    allChips.forEach(chip => {
                                        const chipText = chip.querySelector('span') ? chip.querySelector('span').innerText : chip.innerText;
                                        if (currentOpts.includes(chipText) && chip.classList.contains('active')) {
                                            chip.classList.remove('active');
                                            App.toggleDayText(chip);
                                        }
                                    });
                                }

                                matches.forEach(m => {
                                    const chips = Array.from(document.querySelectorAll('.opt-chip'));
                                    const target = chips.find(c => (c.querySelector('span') ? c.querySelector('span').innerText : c.innerText) === m);
                                    if (target && !target.classList.contains('active')) {
                                        target.classList.add('active');
                                        App.toggleDayText(target);
                                    }
                                });
                            }
                            if (['确认', '好了', '完成', '下一步', '是的', 'OK'].some(k => text.toLowerCase().includes(k.toLowerCase()))) {
                                App.confirmMulti(config.key, null);
                            }
                            return;
                        }

                        if (window.store.pendingFatigue) {
                            const p = window.store.pendingFatigue;
                            if (['切换', '确认', '是'].some(k => matched.includes(k)) || text.includes(p.recommended[0]) || text.includes(p.recommended[0][0])) App.handleInput('fatigue_resolution', 'switch', false);
                            else if (['不切换', '取消', '否'].some(k => matched.includes(k)) || text.includes(p.hit) || text.includes(p.hit[0])) App.handleInput('fatigue_resolution', 'keep', false);
                            return;
                        }

                        if (config.type === 'slider') {
                            let targetVal = parseInt(matched);
                            const slider = document.querySelector('.chat-slider-box input[type=range]');
                            if (slider && !isNaN(targetVal)) {
                                App.animateSlider(slider, targetVal, () => {
                                     App.handleInput(config.key, targetVal, false);
                                });
                                return;
                            }
                        } else if (config.key === 'duration' || config.key === 'cycle' || config.key === 'freq') {
                            matched = parseInt(matched);
                        }
                        App.handleInput(config.key, matched, false);
                    }
                }
            } else {
                if (flow) {
                    const errText = TEXT_VARIANTS.error[Math.floor(Math.random() * TEXT_VARIANTS.error.length)];
                    Voice.speak(errText);
                    if (userBubble) userBubble.style.opacity = '0.5';
                }

                const clickables = Array.from(document.querySelectorAll('.opt-chip, .btn-full, .chat-back, .big-btn, .edit-btn, .ae-btn, .mic-btn, .unit-toggle, .result-header div[onclick]'));
                const visibleClickables = clickables.filter(el => el.offsetParent !== null);
                
                const matchedBtn = visibleClickables.find(el => {
                    let btnText = el.innerText.replace(/\s/g, '').replace(/[><←✕↺⚙]/g, '');
                    const voiceText = text.replace(/\s/g, '');
                    if (!btnText) return false;
                    return (voiceText.includes(btnText) && btnText.length >= 2) || (btnText.includes(voiceText) && voiceText.length >= 2);
                });

                if (matchedBtn) {
                    matchedBtn.click();
                    matchedBtn.classList.add('active-voice-click');
                    setTimeout(() => matchedBtn.classList.remove('active-voice-click'), 300);
                    return;
                }
            }
        }
    },

    handleInput: (key, val, isMulti, el) => {
        if (isMulti) {
            if (el) el.classList.toggle('active');
            else {
                const chips = Array.from(document.querySelectorAll('.opt-chip'));
                const target = chips.find(c => c.innerText.includes(val));
                if(target) { target.classList.toggle('active'); App.toggleDayText(target); }
            }
            return;
        }
        
        if (key === 'targets' && !window.store.pendingFatigue) {
            const fatigued = window.store.user.fatiguedParts;
            const selected = Array.isArray(val) ? val : [val];
            const hit = selected.find(p => fatigued.includes(p));
            
            if (hit) {
                const rec = '背部';
                window.store.pendingFatigue = { original: val, recommended: [rec], hit: hit };
                const template = TEXT_VARIANTS.fatigueWarn[Math.floor(Math.random() * TEXT_VARIANTS.fatigueWarn.length)];
                const text = template.replace('{part}', hit).replace('{rec}', rec);
                
                App.showTyping();
                document.getElementById('chat-history').querySelectorAll('.chat-bubble').forEach(b => b.classList.add('chat-history-dim'));

                setTimeout(() => {
                    App.hideTyping();
                    const chatHistory = document.getElementById('chat-history');
                    const bubble = document.createElement('div');
                    bubble.className = 'chat-bubble chat-ai';
                    
                    // 布局防抖优化
                    bubble.style.opacity = '0';
                    bubble.innerText = text;
                    chatHistory.appendChild(bubble);
                    const h = bubble.offsetHeight;
                    bubble.style.height = h + 'px';
                    bubble.style.opacity = '1';
                    bubble.innerText = '';
                    
                    App.typeWriter(bubble, text, 30, () => { bubble.style.height = 'auto'; });
                    const optContainer = document.createElement('div');
                    optContainer.innerHTML = `<div class="options-grid">
                        <div class="opt-chip recommend" onclick="App.handleInput('fatigue_resolution', 'switch', false)">切换为${rec}</div>
                        <div class="opt-chip secondary" onclick="App.handleInput('fatigue_resolution', 'keep', false)">坚持练${hit}</div>
                    </div>`;
                    chatHistory.appendChild(optContainer);
                    chatHistory.scrollTop = chatHistory.scrollHeight;
                    Voice.speak(text);
                }, 600);
                return;
            }
        }
        
        if (key === 'fatigue_resolution') {
            const pending = window.store.pendingFatigue;
            window.store.pendingFatigue = null;
            App.recordInput('targets', val === 'switch' ? pending.recommended : pending.original);
            return;
        }

        App.recordInput(key, val);
    },

    confirmMulti: (key, el) => {
        let optContainer;
        if (el) {
            optContainer = el.closest('.options-grid').parentElement;
        } else {
            const history = document.getElementById('chat-history');
            for (let i = history.children.length - 1; i >= 0; i--) {
                if (history.children[i].querySelector('.options-grid')) {
                    optContainer = history.children[i];
                    break;
                }
            }
        }
        if (!optContainer) return;
        
        const activeChips = Array.from(optContainer.querySelectorAll('.opt-chip.active')).filter(c => !c.getAttribute('onclick').includes('confirmMulti'));
        
        let active = activeChips.map(e => e.querySelector('span') ? e.querySelector('span').innerText : e.innerText);
        if(!active.length) return App.showToast("请至少选择一项");
        
        App.handleInput(key, active, false);
    },

    recordInput: (key, val) => {
        const flow = window.store.flow;
        const step = window.store.step;
        
        const unitsMap = {
            'course': { 2: '分钟' },
            'plan': { 0: '周', 2: '分钟' }
        };
        const unit = (unitsMap[flow] && unitsMap[flow][step]) ? unitsMap[flow][step] : '';

        let displayVal = val;
        let storedVal = val;

        if (unit && !Array.isArray(val)) {
            displayVal = val + unit;
            storedVal = val + unit;
        } else if (Array.isArray(val)) {
            displayVal = val.join('、');
        }

        window.store.inputs[key] = storedVal;
        
        const chatHistory = document.getElementById('chat-history');
        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble chat-user';
        chatHistory.appendChild(bubble);
        
        // 用户回答也使用打字机效果，完成后再滚动和跳转
        App.typeWriter(bubble, displayVal, 30, () => {
            chatHistory.scrollTop = chatHistory.scrollHeight;
            App.updateSummary();
            window.store.step++;
            setTimeout(() => App.nextStep(), 600);
        });
    },
    
    updateSummary: () => {
        const inputs = window.store.inputs;
        const summary = document.getElementById('chat-summary');
        summary.innerHTML = '';
        Object.values(inputs).forEach(val => {
            const txt = Array.isArray(val) ? val.join('+') : val;
            summary.innerHTML += `<div class="summary-tag">${txt}</div>`;
        });
    }
};