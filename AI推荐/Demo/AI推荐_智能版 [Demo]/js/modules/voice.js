const Voice = {
    synth: window.speechSynthesis,
    rec: null,
    isListening: false,
    selfSpeaking: false,
    voice: null,
    init: () => {
        if (Voice.rec) return; // Prevent multiple inits
        if (window.SpeechRecognition || window.webkitSpeechRecognition) {
            try { Voice.rec = new (window.SpeechRecognition || window.webkitSpeechRecognition)(); } catch(e) { console.error("Voice Init Failed:", e); return; }
            Voice.rec.lang = 'zh-CN';
            Voice.rec.continuous = true; // Continuous Mode for better sensitivity
            Voice.rec.interimResults = true; // Real-time
            
            Voice.rec.onresult = (event) => {
                if (Voice.selfSpeaking) return; // Ignore self
                let interim = '';
                let final = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) final += event.results[i][0].transcript;
                    else interim += event.results[i][0].transcript;
                }
                if (final) App.handleVoiceInput(final, true);
                else if (interim) App.handleVoiceInput(interim, false);
            };
            
            Voice.rec.onerror = (event) => {
                console.log('Voice Error:', event.error);
                if (event.error === 'no-speech' || event.error === 'aborted') {
                    // Silent ignore, onend will handle restart
                } else {
                    App.showToast("语音识别异常: " + event.error);
                    App.setListeningUI(false);
                }
            };

            // Sound detection for immediate feedback
            Voice.rec.onsoundstart = () => {
                document.querySelector('.siri-container').classList.add('listening');
            };
            
            Voice.rec.onend = () => { 
                if (Voice.isListening && !Voice.selfSpeaking) {
                    try { Voice.rec.start(); } catch(e){} // Auto-restart
                } else if (!Voice.selfSpeaking) {
                    App.setListeningUI(false);
                }
            };
            
            // Load voices
            window.speechSynthesis.onvoiceschanged = () => {
                const voices = window.speechSynthesis.getVoices();
                // Try to find a natural sounding voice
                Voice.voice = voices.find(v => v.lang === 'zh-CN' && (v.name.includes('Google') || v.name.includes('Microsoft') || v.name.includes('Apple'))) || voices.find(v => v.lang === 'zh-CN');
            };
        }
    },
    
    speak: (text) => {
        if (!window.SpeechSynthesisUtterance || !Voice.synth) return;
        Voice.selfSpeaking = true;
        if (Voice.rec) try { Voice.rec.abort(); } catch(e) {} // Use abort to discard current buffer
        App.setListeningUI(false);
        
        if (Voice.synth && Voice.synth.speaking) Voice.synth.cancel();
        const utter = new SpeechSynthesisUtterance(text);
        document.querySelector('.siri-container').classList.add('speaking');
        utter.lang = 'zh-CN';
        utter.rate = 1.1;
        if (Voice.voice) utter.voice = Voice.voice;
        
        utter.onend = () => {
            // Add safety delay to prevent self-hearing echo
            setTimeout(() => {
                document.querySelector('.siri-container').classList.remove('speaking');
                Voice.selfSpeaking = false;
                Voice.startListening(); // Always listen (Home or Chat)
            }, 1500); // Increased safety delay for anti-self-hearing
        };
        if (Voice.synth) Voice.synth.speak(utter);
    },
    
    startListening: () => {
        const activeView = document.querySelector('.view.active');
        if (activeView && activeView.id !== 'view-home' && activeView.id !== 'view-chat') return;

        if (!Voice.rec || Voice.selfSpeaking) return;
        try {
            Voice.isListening = true; 
            Voice.rec.start();
            App.setListeningUI(true);
            document.querySelector('.siri-container').classList.add('listening');
        } catch(e) { console.error("Start Listening Failed:", e); }
    },
    
    stopListening: () => {
        if (!Voice.rec) return;
        Voice.isListening = false;
        Voice.rec.stop();
        App.setListeningUI(false);
        document.querySelector('.siri-container').classList.remove('listening');
    }
};