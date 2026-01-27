window.UIUtils = {
    switchView: (viewId) => {
        document.querySelectorAll('.view').forEach(v => {
            v.classList.remove('active');
            if(v.id === viewId) v.classList.add('active');
        });

        // Auto-start listening if returning to interactive views
        if (viewId === 'view-home' || viewId === 'view-chat') {
            if (!Voice.selfSpeaking) Voice.startListening();
        } else {
            Voice.stopListening();
        }
        
        // Handle Home Background
        const bg = document.getElementById('home-bg-layer');
        if (bg) {
            if (viewId === 'view-home') bg.classList.remove('hidden');
            else bg.classList.add('hidden');
        }
    },

    showToast: (msg) => {
        const t = document.getElementById('toast');
        t.innerText = msg;
        t.style.opacity = 1;
        setTimeout(() => t.style.opacity = 0, 3000);
    },

    openConfirmModal: (msg, onConfirm) => {
        document.getElementById('dialog-msg').innerText = msg;
        document.getElementById('dialog-confirm-btn').onclick = onConfirm;
        document.getElementById('dialog-confirm').classList.add('active');
    },

    closeConfirmModal: () => {
        document.getElementById('dialog-confirm').classList.remove('active');
    },

    typeWriter: (element, text, speed = 30, callback) => {
        element.textContent = '';
        let i = 0;
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
            } else {
                if (callback) callback();
            }
        }
        type();
    },

    cnToInt: (text) => {
        const map = { '一':1, '二':2, '两':2, '三':3, '四':4, '五':5, '六':6, '七':7, '八':8, '九':9, '十':10, '0':0, '1':1, '2':2, '3':3, '4':4, '5':5, '6':6, '7':7, '8':8, '9':9 };
        let numStr = text.match(/[0-9]+|[一二两三四五六七八九十]+/);
        if (!numStr) return null;
        let str = numStr[0];
        if (/\d/.test(str)) return parseInt(str);
        
        if (str.length === 1) return map[str];
        if (str.length === 2) {
            if (str[0] === '十') return 10 + map[str[1]];
            if (str[1] === '十') return map[str[0]] * 10;
        }
        if (str.length === 3) {
            if (str[1] === '十') return map[str[0]] * 10 + map[str[2]];
        }
        return null;
    },

    animateSlider: (slider, targetVal, callback) => {
        let current = parseInt(slider.value);
        const step = (targetVal - current) / 10;
        let count = 0;
        const interval = setInterval(() => {
            current += step;
            slider.value = current;
            const display = document.getElementById('slider-val');
            if(display) {
                 const unit = display.innerText.replace(/[0-9\.]+/g, '').trim();
                 display.innerText = Math.round(current) + ' ' + unit;
            }
            count++;
            if (count >= 10) {
                clearInterval(interval);
                slider.value = targetVal;
                if(callback) callback();
            }
        }, 30);
    },

    toggleMicState: () => {
        if (Voice.isListening) Voice.stopListening();
        else Voice.startListening();
    },

    setListeningUI: (state) => {
        const btn = document.getElementById('mic-btn');
        if(state) btn.classList.add('listening');
        else btn.classList.remove('listening');
    },

    initChatScroll: () => {
        const el = document.getElementById('chat-history');
        if(!el) return;
        let timer;
        el.addEventListener('scroll', () => {
            el.classList.add('scrolling');
            clearTimeout(timer);
            timer = setTimeout(() => {
                el.classList.remove('scrolling');
            }, 1000);
        });
    },

    scrollTo: (element, to, duration = 600) => {
        if (!element) return;
        const start = element.scrollTop;
        const change = to - start;
        const startTime = performance.now();
        
        function animateScroll(currentTime) {
            const timeElapsed = currentTime - startTime;
            const progress = Math.min(timeElapsed / duration, 1);
            const ease = 1 - Math.pow(1 - progress, 3); // Cubic ease-out
            
            element.scrollTop = start + change * ease;
            
            if (timeElapsed < duration) requestAnimationFrame(animateScroll);
        }
        requestAnimationFrame(animateScroll);
    },

    captureScreenshot: () => {
        const h2c = window.html2canvas;
        if (!h2c) {
            window.UIUtils.showToast('截图插件未加载');
            return;
        }

        // Calculate Capture Area
        const appEl = document.getElementById('app');
        const notes = document.querySelectorAll('.prd-note');
        
        let minX = appEl.getBoundingClientRect().left;
        let maxX = appEl.getBoundingClientRect().right;
        
        notes.forEach(note => {
            if (note.style.display !== 'none' && note.offsetParent !== null) {
                const rect = note.getBoundingClientRect();
                if (rect.left < minX) minX = rect.left;
                if (rect.right > maxX) maxX = rect.right;
            }
        });
        
        const padding = 60;
        const x = minX - padding;
        const width = (maxX + padding) - x;
        
        window.UIUtils.showToast('正在截图...');

        h2c(document.body, {
            x: x + window.scrollX,
            y: 0,
            width: width,
            height: window.innerHeight,
            backgroundColor: '#000000',
            scale: 2,
            useCORS: true,
            ignoreElements: (el) => el.classList.contains('top-right-tools') || el.id === 'toast',
            onclone: (clonedDoc) => {
                // 1. Fix Gradient Text (.ai-greeting) - Force White
                const textClipElements = clonedDoc.querySelectorAll('.ai-greeting');
                textClipElements.forEach(el => {
                    el.style.color = '#ffffff';
                    el.style.webkitTextFillColor = 'initial';
                    el.style.backgroundClip = 'border-box';
                    el.style.webkitBackgroundClip = 'border-box';
                    el.style.textShadow = '0 2px 10px rgba(0,0,0,0.5)';
                });

                // 2. Fix PRD Notes Visibility - Force Opaque Dark Grey
                const notes = clonedDoc.querySelectorAll('.prd-note');
                notes.forEach(el => {
                    el.style.backgroundColor = '#222222'; // Solid dark grey
                    el.style.backdropFilter = 'none'; // Remove blur
                    el.style.border = '1px solid #666'; // Stronger border
                    el.style.boxShadow = '0 4px 20px rgba(0,0,0,0.8)';
                    el.style.color = '#ffffff';
                });

                // 3. Fix PRD Lines Visibility - Force Opaque
                const lines = clonedDoc.querySelectorAll('.prd-line');
                lines.forEach(el => {
                    el.style.strokeOpacity = '1';
                    el.style.strokeWidth = '1.5px';
                });

                // 4. Fix Glassmorphism & Transparent Containers
                // Force solid backgrounds for better visibility on black screenshot
                const glassSelectors = [
                    '.home-bottom', 
                    '.result-header', 
                    '.wk-header', 
                    '.chat-header', 
                    '.input-area', 
                    '.wk-action-list-overlay', 
                    '.big-btn', 
                    '.opt-chip', 
                    '.summary-tag', 
                    '.plan-hero-intro',
                    '.action-card-pro',
                    '.lib-item'
                ];
                
                const glassElements = clonedDoc.querySelectorAll(glassSelectors.join(','));
                glassElements.forEach(el => {
                    // Preserve active/primary states
                    if (el.classList.contains('active') || el.classList.contains('selected')) {
                        el.style.opacity = '1';
                        return;
                    }
                    
                    // Headers & Input Area -> Solid Black
                    if (el.classList.contains('chat-header') || el.classList.contains('wk-header') || el.classList.contains('input-area')) {
                        el.style.background = '#000000';
                        el.style.backgroundImage = 'none';
                    } 
                    // Cards & Buttons -> Solid Dark Grey
                    else {
                        el.style.backgroundColor = '#1a1a1a';
                        el.style.backdropFilter = 'none';
                        el.style.backgroundImage = 'none'; // Remove gradients if any
                    }
                    el.style.opacity = '1';
                });

                // 5. Enhance Text Contrast
                const textSelectors = [
                    '.info-val', 
                    '.ac-title', 
                    '.lib-name', 
                    '.plan-hero-title',
                    '.result-title'
                ];
                const textElements = clonedDoc.querySelectorAll(textSelectors.join(','));
                textElements.forEach(el => {
                    el.style.color = '#ffffff';
                    el.style.opacity = '1';
                    el.style.textShadow = '0 1px 2px rgba(0,0,0,0.8)'; // Add shadow for readability
                });
            }
        }).then(canvas => {
            const link = document.createElement('a');
            
            let viewName = 'Screen';
            const activeView = document.querySelector('.view.active');
            if (activeView) {
                if (activeView.id === 'view-home') viewName = '首页';
                else if (activeView.id === 'view-chat') viewName = '对话';
                else if (activeView.id === 'view-result') viewName = '方案';
                else if (activeView.id === 'view-workout') viewName = '训练';
            }

            const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
            link.download = `AEKE_Coach_${viewName}_${timestamp}.png`;
            link.href = canvas.toDataURL('image/png');
            link.click();
            
            window.UIUtils.showToast('截图已下载');
        }).catch(err => {
            console.error('Screenshot failed:', err);
            window.UIUtils.showToast('截图失败');
        });
    }
};