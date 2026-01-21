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

    typeWriter: (element, text, speed = 30) => {
        element.textContent = '';
        let i = 0;
        function type() {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
                setTimeout(type, speed);
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
    }
};