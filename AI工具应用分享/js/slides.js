const { useState, useRef, useEffect } = React;

// 1. Cover Slide
const SlideCover = ({ slide }) => (
    <div className="flex flex-col items-center justify-center h-full text-center space-y-8 animate-fade-in px-4 md:px-12 max-w-[95vw] mx-auto w-full relative">
        <div className="absolute top-0 left-0 w-full h-full overflow-hidden -z-10 pointer-events-none">
             <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-primary/10 rounded-full blur-[100px]"></div>
             <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-blue-100 rounded-full blur-[100px]"></div>
        </div>

        <div className="mb-4 animate-fade-in transition-transform hover:scale-105" style={{animationDelay: '0.1s'}}>
            <img 
                src={window.resolveImage(window.PPT_DATA.config.logo)} 
                alt="Company Brand Logo" 
                className="h-12 md:h-16 object-contain mx-auto drop-shadow-sm cursor-pointer"
            />
        </div>

        <h1 className="text-6xl md:text-8xl font-extrabold tracking-tight mb-6">
            <span className="gradient-text-primary">{slide.title}</span>
        </h1>
        <h2 className="text-2xl md:text-3xl text-slate-500 font-normal max-w-3xl leading-relaxed mb-12">
            {slide.subtitle}
        </h2>
        
        <div className="flex flex-col items-center">
            <div className="w-16 h-1 bg-primary rounded-full mb-6"></div>
            <p className="text-xl font-semibold text-slate-800">{slide.presenter}</p>
            <p className="text-slate-400 mt-2 text-sm font-mono">{slide.date}</p>
        </div>
    </div>
);

// 2. Timeline Slide
const SlideTimeline = ({ slide }) => {
    const [activeIdx, setActiveIdx] = useState(0);
    const scrollRef = useRef(null);
    
    // 使用统一的滚动 Hook
    const dragEvents = window.useDraggableScroll(scrollRef);

    return (
        <div className="flex flex-col h-full justify-center px-4 md:px-12 animate-fade-in max-w-[95vw] mx-auto w-full">
            <div className="mb-8 text-center shrink-0">
                <h2 className="text-4xl md:text-5xl font-bold mb-4 gradient-text-primary">{slide.title}</h2>
                <p className="text-xl text-slate-500">{slide.subtitle}</p>
            </div>

            <div className="relative w-full overflow-hidden">
                {/* Timeline Line */}
                <div className="absolute top-[3.5rem] left-0 w-full h-1 bg-slate-100 -z-10"></div>
                
                {/* Scrollable Container */}
                <div 
                    ref={scrollRef} 
                    className="flex overflow-x-auto pb-12 pt-4 px-4 space-x-8 hide-scrollbar cursor-grab active:cursor-grabbing"
                    {...dragEvents}
                >
                    {slide.events.map((event, idx) => {
                        // Check for year change to add extra spacing
                        const currentYear = event.year.split(' ')[0];
                        const prevYear = idx > 0 ? slide.events[idx - 1].year.split(' ')[0] : null;
                        const isNewYear = idx > 0 && currentYear !== prevYear;
                        
                        return (
                            <React.Fragment key={idx}>
                                {isNewYear && (
                                    <div className="shrink-0 flex flex-col justify-center items-center px-4 pointer-events-none select-none opacity-40">
                                        <div className="text-4xl font-black text-slate-300 -rotate-90 origin-center transform translate-y-6">{currentYear}</div>
                                        <div className="h-24 w-0.5 bg-slate-300 mt-16"></div>
                                    </div>
                                )}
                                <div 
                                    className={`relative group cursor-pointer transition-all duration-300 shrink-0 w-[280px] flex flex-col items-center select-none ${idx === activeIdx ? 'scale-105 opacity-100' : 'opacity-80 hover:opacity-100'}`}
                                    onClick={() => setActiveIdx(idx)}
                                >
                                    {/* Dot & Icon */}
                                    <div className={`w-14 h-14 rounded-full border-4 flex items-center justify-center mb-6 transition-colors duration-300 z-10 bg-white ${
                                        idx === activeIdx 
                                            ? (event.highlight ? 'border-amber-400 shadow-lg shadow-amber-400/30' : 'border-primary shadow-lg shadow-primary/20') 
                                            : (event.highlight ? 'border-amber-200' : 'border-slate-200 group-hover:border-primary/50')
                                    }`}>
                                        <window.Icon name={event.icon} className={`w-5 h-5 ${
                                            idx === activeIdx 
                                                ? (event.highlight ? 'text-amber-500' : 'text-primary') 
                                                : (event.highlight ? 'text-amber-400' : 'text-slate-400')
                                        }`} />
                                    </div>
                                    {/* Card */}
                                    <div className={`clean-panel p-6 rounded-xl text-center w-full h-48 flex flex-col transition-all duration-300 ${
                                        idx === activeIdx 
                                            ? (event.highlight ? 'border-amber-400/50 shadow-lg shadow-amber-400/10 bg-amber-50/50' : 'border-primary/30 shadow-pearl bg-white') 
                                            : 'bg-white/60 hover:bg-white'
                                    }`}>
                                        <div className={`${event.highlight ? 'text-amber-600' : 'text-primary'} font-bold text-lg mb-1`}>{event.year}</div>
                                        <h3 className="text-xl font-bold text-slate-800 mb-2 flex items-center justify-center gap-2">
                                            {event.title}
                                            {event.highlight && <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded border border-amber-200">★</span>}
                                        </h3>
                                        <p className="text-sm text-slate-500 leading-relaxed">{event.desc}</p>
                                    </div>
                                </div>
                            </React.Fragment>
                        );
                    })}
                </div>
            </div>
        </div>
    );
};

// 3. Comparison Slide
const SlideComparison = ({ slide }) => {
    const scrollRef = useRef(null);
    const dragEvents = window.useDraggableScroll(scrollRef);

    return (
        <div className="flex flex-col h-full justify-center px-4 md:px-12 animate-fade-in max-w-[95vw] mx-auto w-full">
            <div className="mb-8 text-center shrink-0">
                <h2 className="text-4xl font-bold gradient-text-primary mb-3">{slide.title}</h2>
                <p className="text-xl text-slate-500">{slide.subtitle}</p>
            </div>
            
            {/* Flowchart Container */}
            <div 
                ref={scrollRef}
                className="flex overflow-x-auto pb-8 pt-4 px-4 space-x-6 hide-scrollbar items-center relative cursor-grab active:cursor-grabbing"
                {...dragEvents}
            >
                {/* Connecting Line Background */}
                <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-100 -z-10 hidden md:block"></div>

                {slide.steps.map((step, idx) => (
                    <React.Fragment key={idx}>
                        {/* Step Card */}
                        <div className="shrink-0 w-[360px] flex flex-col group bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all duration-300 border border-slate-100 select-none">
                            {/* Header */}
                            <div className="flex items-center space-x-3 p-4 border-b border-slate-50 bg-slate-50/50 rounded-t-2xl">
                                <div className="w-10 h-10 rounded-full bg-white border border-slate-200 flex items-center justify-center text-slate-500 group-hover:border-primary group-hover:text-primary transition-colors shadow-sm">
                                    <window.Icon name={step.icon} className="w-5 h-5" />
                                </div>
                                <h3 className="font-bold text-slate-800 text-lg flex-1">{step.title}</h3>
                                <div className="text-xs font-mono text-slate-300 group-hover:text-primary/50">0{idx + 1}</div>
                            </div>

                            {/* Sub-steps (Micro Flow) */}
                            <div className="px-5 py-3 bg-white border-b border-slate-50 flex justify-between items-center text-[10px] text-slate-400 font-medium tracking-tight">
                                {step.subSteps && step.subSteps.map((sub, i) => (
                                    <React.Fragment key={i}>
                                        <span className="hover:text-primary transition-colors cursor-default">{sub}</span>
                                        {i < step.subSteps.length - 1 && <span className="text-slate-200">→</span>}
                                    </React.Fragment>
                                ))}
                            </div>

                            {/* Comparison Box */}
                            <div className="flex flex-col h-full">
                                {/* Traditional */}
                                <div className="p-5 border-b border-slate-100 flex-1 bg-slate-50/30">
                                    <div className="text-xs uppercase tracking-wider text-slate-400 font-bold mb-3 flex items-center gap-1.5">
                                        <window.Icon name="Clock" className="w-3.5 h-3.5" /> 传统模式
                                    </div>
                                    <ul className="list-disc list-outside ml-4 text-sm text-slate-500 leading-relaxed space-y-1">
                                        {Array.isArray(step.traditional) ? step.traditional.map((t, i) => (
                                            <li key={i} className="pl-1">{t}</li>
                                        )) : <li>{step.traditional}</li>}
                                    </ul>
                                </div>
                                
                                {/* AI */}
                                <div className="bg-primary-light/30 p-5 flex-1 relative overflow-hidden rounded-b-2xl">
                                    <div className="absolute top-0 left-0 w-1 h-full bg-primary"></div>
                                    <div className="text-xs uppercase tracking-wider text-primary font-bold mb-3 flex items-center gap-1.5">
                                        <window.Icon name="Zap" className="w-3.5 h-3.5" /> AI 赋能
                                    </div>
                                    <ul className="list-disc list-outside ml-4 text-sm text-slate-800 font-medium leading-relaxed space-y-1">
                                        {Array.isArray(step.ai) ? step.ai.map((t, i) => (
                                            <li key={i} className="pl-1">{t}</li>
                                        )) : <li>{step.ai}</li>}
                                    </ul>
                                </div>
                            </div>
                        </div>

                        {/* Arrow Connector (if not last) */}
                        {idx !== slide.steps.length - 1 && (
                            <div className="shrink-0 text-slate-300 hidden md:block">
                                <window.Icon name="ArrowRight" className="w-6 h-6" />
                            </div>
                        )}
                    </React.Fragment>
                ))}
                
                {/* Loop Indicator at the end */}
                <div className="shrink-0 flex flex-col items-center justify-center text-slate-300 ml-4 opacity-50">
                    <window.Icon name="RefreshCw" className="w-8 h-8 mb-2" />
                    <span className="text-xs font-bold uppercase tracking-widest">Iterate</span>
                </div>
            </div>
        </div>
    );
};

// 4. Grid Slide
const SlideGrid = ({ slide }) => {
    const [selectedItem, setSelectedItem] = useState(null);
    const scrollRef = useRef(null);
    const dragEvents = window.useDraggableScroll(scrollRef);
    const isOtherScenarios = slide.id === 'other-scenarios';
    const [globalTrigger, setGlobalTrigger] = useState(null);
    const [stopMusicSignal, setStopMusicSignal] = useState(0);

    const handleWake = () => {
        setStopMusicSignal(Date.now());
    };

    const handleGlobalCommand = (cmd) => {
        if (!cmd) return;
        // 直接广播指令，让所有组件自行匹配（支持多任务）
        setGlobalTrigger({ text: cmd, timestamp: Date.now() });
    };

    // Group items by category (Methodology Stages)
    const groups = slide.items.reduce((acc, item) => {
        const cat = item.category;
        if (!acc[cat]) acc[cat] = [];
        acc[cat].push(item);
        return acc;
    }, {});
    
    // Sort keys to ensure order 1..6
    const groupKeys = Object.keys(groups).sort((a, b) => parseInt(a) - parseInt(b));

    return (
        <div className="flex flex-col h-full justify-center px-4 md:px-12 animate-fade-in pt-10 max-w-[95vw] mx-auto w-full">
            <div className="mb-6 text-center shrink-0">
                <h2 className="text-4xl font-bold gradient-text-primary mb-2">{slide.title}</h2>
                <p className="text-xl text-slate-500">{slide.subtitle}</p>
            </div>

            <div className="relative flex-1 min-h-0">
                {/* Background Connecting Line */}
                <div className="absolute top-[3.5rem] left-0 w-full h-0.5 bg-gradient-to-r from-primary/10 via-primary/30 to-primary/10 -z-10"></div>

                <div 
                    ref={scrollRef}
                    className="flex overflow-x-auto pb-12 pt-4 px-4 space-x-12 snap-x hide-scrollbar items-start h-full cursor-grab active:cursor-grabbing"
                    {...dragEvents}
                >
                    {groupKeys.map((key, idx) => (
                        <div key={idx} className="shrink-0 w-[280px] flex flex-col space-y-6 snap-center relative pt-8">
                            {/* Stage Node on Line */}
                            <div className="absolute top-[3.5rem] -mt-1.5 left-1/2 -ml-1.5 w-3 h-3 rounded-full bg-primary border-2 border-white shadow-sm z-0"></div>
                            
                            {/* Stage Header */}
                            <div className="text-center relative z-10">
                                <div className="inline-block bg-white px-3 py-1 rounded-full border border-primary/20 shadow-sm text-primary font-bold text-xs mb-2 uppercase tracking-wider">
                                    Step 0{idx + 1}
                                </div>
                                <h3 className="text-lg font-bold text-slate-800">{key.split(' ').slice(1).join(' ')}</h3>
                            </div>

                            {/* Cards Stack */}
                            <div className="flex flex-col space-y-4">
                                {groups[key].map((item, i) => {
                                    const imgSrc = window.resolveImage(item.detailImage);
                                    const isVideo = imgSrc && imgSrc.toLowerCase().endsWith('.mp4');
                                    
                                    return (
                                        <div 
                                            key={i} 
                                            className="clean-panel p-0 rounded-xl card-hoverable cursor-pointer border-l-4 border-l-primary group bg-white/90 hover:bg-white transition-all relative overflow-hidden flex flex-col"
                                            onClick={() => setSelectedItem(item)}
                                        >
                                            {/* Interactive Demo or Standard Image */}
                                            {isOtherScenarios ? (
                                                <ScenarioDemo 
                                                    item={item} 
                                                    externalTrigger={globalTrigger}
                                                    stopMusicSignal={stopMusicSignal}
                                                    onTriggerHandled={() => setGlobalTrigger(null)}
                                                />
                                            ) : (
                                                <div className="h-32 w-full bg-slate-100 relative overflow-hidden shrink-0 group-hover:shadow-inner transition-shadow">
                                                     {imgSrc ? (
                                                        isVideo ? (
                                                            <>
                                                                <div className="video-loader absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
                                                                    <div className="w-6 h-6 border-2 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                                                                </div>
                                                                <video 
                                                                    src={imgSrc} 
                                                                    className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity relative z-10" 
                                                                    muted loop autoPlay playsInline 
                                                                    preload="metadata"
                                                                    onLoadStart={(e) => {
                                                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                                                        if(loader) loader.style.display = 'flex';
                                                                    }}
                                                                    onWaiting={(e) => {
                                                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                                                        if(loader) loader.style.display = 'flex';
                                                                    }}
                                                                    onCanPlay={(e) => {
                                                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                                                        if(loader) loader.style.display = 'none';
                                                                    }}
                                                                    onPlaying={(e) => {
                                                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                                                        if(loader) loader.style.display = 'none';
                                                                    }}
                                                                    onError={(e) => {
                                                                        e.target.style.display = 'none';
                                                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                                                        if(loader) loader.style.display = 'none';
                                                                        e.target.parentElement.innerHTML = '<div class="w-full h-full flex flex-col items-center justify-center text-slate-300 bg-slate-50"><span class="text-xl mb-1">⚠️</span><span class="text-[10px]">加载失败</span></div>';
                                                                    }}
                                                                />
                                                            </>
                                                        ) : (
                                                            <img src={imgSrc} className="w-full h-full object-cover opacity-90 group-hover:opacity-100 transition-opacity" />
                                                        )
                                                     ) : (
                                                        <GridVisualFallback item={item} />
                                                     )}
                                                     {/* Overlay gradient */}
                                                     <div className="absolute inset-0 bg-gradient-to-t from-black/10 to-transparent pointer-events-none"></div>
                                                </div>
                                            )}

                                            {/* Content Area */}
                                            <div className="p-4 flex flex-col flex-1 relative">
                                                <div className="flex items-center space-x-2 mb-2">
                                                    <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1">
                                                        <window.Icon name={item.icon} className="w-3 h-3" /> Case Study
                                                    </span>
                                                </div>
                                                <h4 className="font-bold text-slate-800 mb-1 text-base leading-tight">{item.title}</h4>
                                                <p className="text-xs text-slate-500 leading-relaxed line-clamp-2">{item.desc}</p>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    ))}
                    
                    {/* End Spacer */}
                    <div className="shrink-0 w-12"></div>
                </div>
            </div>
            <EnhancedModal isOpen={!!selectedItem} onClose={() => setSelectedItem(null)} item={selectedItem} />
            {isOtherScenarios && <OfficeAssistant onTrigger={handleGlobalCommand} onWake={handleWake} />}
        </div>
    );
};

// 5. Showcase Slide
const SlideShowcase = ({ slide }) => {
    const imgSrc = window.resolveImage(slide.mainImage);
    const isVideo = imgSrc && imgSrc.toLowerCase().endsWith('.mp4');
    const isHtml = imgSrc && imgSrc.toLowerCase().endsWith('.html');

    return (
        <div className="flex flex-col h-full justify-center px-4 md:px-12 animate-fade-in max-w-[95vw] mx-auto w-full py-6">
            <div className="mb-6 shrink-0 text-center md:text-left">
                <h2 className="text-3xl md:text-5xl font-bold mb-2 gradient-text-primary">{slide.title}</h2>
                <p className="text-lg md:text-xl text-slate-500">{slide.subtitle}</p>
            </div>
            <div className="flex flex-col md:flex-row gap-6 md:gap-10 items-stretch flex-1 min-h-0 overflow-hidden">
                <div className="w-full md:w-5/12 clean-panel p-2 rounded-3xl relative overflow-hidden group flex flex-col shrink-0 h-48 md:h-auto">
                    <div className="w-full h-full bg-slate-50 rounded-2xl border border-slate-100 flex flex-col items-center justify-center relative overflow-hidden">
                        {isHtml ? (
                            !window.isSecureContext ? (
                                <div className="flex flex-col items-center justify-center p-8 text-center bg-amber-50 text-amber-800 w-full h-full select-none">
                                    <div className="mb-4 p-3 bg-amber-100 rounded-full">
                                        <window.Icon name="Zap" className="w-8 h-8 text-amber-600" />
                                    </div>
                                    <h3 className="text-lg font-bold mb-2">需要 HTTPS 环境</h3>
                                    <p className="text-sm text-amber-700/80 max-w-[240px] leading-relaxed">
                                        浏览器安全策略限制：摄像头仅能在 <strong>HTTPS</strong> 或 <strong>Localhost</strong> 下运行。
                                    </p>
                                </div>
                            ) : (
                                <iframe 
                                    src={imgSrc} 
                                    className="w-full h-full border-0"
                                    title="Interactive Demo"
                                    allow="camera; microphone; fullscreen"
                                />
                            )
                        ) : isVideo ? (
                            <>
                                <div className="video-loader absolute inset-0 flex items-center justify-center z-20 pointer-events-none">
                                    <div className="w-8 h-8 border-4 border-primary/20 border-t-primary rounded-full animate-spin"></div>
                                </div>
                                <video 
                                    src={imgSrc} 
                                    className="w-full h-full object-cover relative z-10" 
                                    autoPlay 
                                    loop 
                                    muted 
                                    playsInline
                                    preload="metadata"
                                    onLoadStart={(e) => {
                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                        if(loader) loader.style.display = 'flex';
                                    }}
                                    onWaiting={(e) => {
                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                        if(loader) loader.style.display = 'flex';
                                    }}
                                    onCanPlay={(e) => {
                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                        if(loader) loader.style.display = 'none';
                                    }}
                                    onPlaying={(e) => {
                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                        if(loader) loader.style.display = 'none';
                                    }}
                                    onError={(e) => {
                                        e.target.style.display = 'none';
                                        const loader = e.target.parentElement.querySelector('.video-loader');
                                        if(loader) loader.style.display = 'none';
                                        e.target.parentNode.innerHTML = '<div class="flex flex-col items-center justify-center h-full text-slate-400 bg-slate-50"><span class="text-2xl mb-2">⚠️</span><span>视频资源加载失败</span><span class="text-xs mt-1 opacity-70">请检查服务器 assets 目录</span></div>';
                                    }}
                                />
                            </>
                        ) : (
                            <img
                                src={imgSrc || window.PPT_DATA.config.defaultPlaceholder} 
                                className="w-full h-full object-cover" 
                                onError={(e) => { e.target.onerror = null; e.target.src = window.PPT_DATA.config.defaultPlaceholder; }}
                            />
                        )}
                    </div>
                </div>
                <div className="w-full md:w-7/12 flex flex-col gap-3 overflow-y-auto pr-2 hide-scrollbar pb-2">
                    {slide.steps.map((step, idx) => (
                        <div key={idx} className="flex gap-4 group shrink-0">
                            <div className="flex flex-col items-center pt-1">
                                <div className="w-8 h-8 rounded-full bg-white border-2 border-primary text-primary flex items-center justify-center font-bold text-sm shadow-sm group-hover:bg-primary group-hover:text-white transition-colors shrink-0">{idx + 1}</div>
                                {idx !== slide.steps.length - 1 && <div className="w-0.5 h-full bg-slate-100 my-1 group-hover:bg-primary/20 transition-colors"></div>}
                            </div>
                            <div className="clean-panel p-4 rounded-xl flex-1 hover:border-primary/30 transition-colors bg-white/80">
                                <h4 className="text-lg font-bold text-slate-800 mb-1">{step.title}</h4>
                                <p className="text-slate-600 text-sm leading-relaxed">{step.desc}</p>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
};

// --- Summary Visual Components ---
const SummaryVisual = ({ idx }) => {
    // 1. Data Mining: High-tech Dashboard
    if (idx === 0) {
        // 实时数据状态 (24个数据点)
        const [data, setData] = useState(() => Array.from({length: 24}, () => Math.floor(Math.random() * 40) + 30));
        
        useEffect(() => {
            const interval = setInterval(() => {
                setData(prev => prev.map(v => {
                    // 模拟随机波动
                    const noise = Math.floor(Math.random() * 20) - 10;
                    return Math.max(10, Math.min(95, v + noise));
                }));
            }, 200); // 200ms 刷新一次
            return () => clearInterval(interval);
        }, []);

        // 计算折线图路径点
        const polylinePoints = data.map((v, i) => {
            const x = (i * (100 / 24)) + (100 / 24 / 2);
            const y = 100 - v;
            return `${x},${y}`;
        }).join(' ');

        return (
            <div className="h-48 w-full bg-slate-900 rounded-lg mt-4 relative overflow-hidden flex flex-col items-center justify-end pb-0 border border-slate-800 shadow-inner group">
                {/* Grid Background */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(50,196,140,0.05)_1px,transparent_1px),linear-gradient(90deg,rgba(50,196,140,0.05)_1px,transparent_1px)] bg-[size:20px_20px]"></div>
                
                {/* Header */}
                <div className="absolute top-2 right-2 flex gap-1 z-30">
                    <div className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping"></div>
                    <span className="text-[10px] text-emerald-400 font-mono">LIVE DATA</span>
                </div>

                {/* Chart Area */}
                <div className="relative flex-1 w-full px-2 pt-6 pb-2">
                    {/* SVG Overlay for Line */}
                    <svg className="absolute inset-0 w-full h-full z-20 pointer-events-none px-2 pt-6 pb-2" preserveAspectRatio="none" viewBox="0 0 100 100">
                        <polyline 
                            points={polylinePoints} 
                            fill="none" 
                            stroke="rgba(255,255,255,0.5)" 
                            strokeWidth="0.5" 
                            strokeDasharray="2 1"
                            className="transition-all duration-200 ease-linear"
                        />
                        {data.map((v, i) => (
                            <circle 
                                key={i} 
                                cx={(i * (100 / 24)) + (100 / 24 / 2)} 
                                cy={100 - v} 
                                r="1" 
                                fill="#ffffff" 
                                className="transition-all duration-200 ease-linear"
                            />
                        ))}
                    </svg>

                    {/* Bars Container */}
                    <div className="flex items-end justify-between h-full w-full relative z-10">
                        {data.map((h, i) => {
                            // 动态颜色计算：低(0)=红 -> 高(100)=绿
                            const hue = Math.min(120, Math.max(0, h * 1.2));
                            const color = `hsl(${hue}, 80%, 60%)`;
                            
                            return (
                                <div key={i} className="flex-1 h-full px-[1px] relative group/bar">
                                    {/* Number */}
                                    <div 
                                        className="absolute w-full text-center text-[8px] text-white font-mono font-bold transition-all duration-200 ease-linear"
                                        style={{ bottom: `${h}%`, marginBottom: '4px', textShadow: '0 1px 2px rgba(0,0,0,0.8)' }}
                                    >
                                        {h}
                                    </div>
                                    {/* Bar Track */}
                                    <div className="w-full h-full bg-slate-800/50 rounded-t-sm relative overflow-hidden">
                                        {/* Bar Fill */}
                                        <div 
                                            className="absolute bottom-0 left-0 w-full transition-all duration-200 ease-linear group-hover/bar:brightness-125"
                                            style={{ 
                                                height: `${h}%`,
                                                background: `linear-gradient(to top, hsl(${hue}, 80%, 30%), ${color})`
                                            }}
                                        ></div>
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            </div>
        );
    }

    // 2. Docs: Auto-generating Flowchart
    if (idx === 1) {
        return (
            <div className="h-48 w-full bg-slate-50 rounded-lg mt-4 relative flex items-center justify-center border border-slate-200 overflow-hidden">
                <div className="absolute inset-0 bg-[radial-gradient(#cbd5e1_1px,transparent_1px)] [background-size:16px_16px] opacity-30"></div>
                
                <div className="relative flex items-center gap-6 z-10">
                    {/* Source Doc */}
                    <div className="w-12 h-14 bg-white border-2 border-slate-300 rounded-lg shadow-sm flex flex-col items-center justify-center relative">
                        <div className="w-8 h-1 bg-slate-200 mb-1 rounded-full"></div>
                        <div className="w-6 h-1 bg-slate-200 mb-1 rounded-full"></div>
                        <div className="w-8 h-1 bg-slate-200 rounded-full"></div>
                        {/* Particles emitting */}
                        <div className="absolute -right-1 top-1/2 w-2 h-2 bg-primary rounded-full animate-ping"></div>
                    </div>

                    {/* Arrow */}
                    <div className="text-slate-300">
                        <window.Icon name="ArrowRight" className="w-6 h-6 animate-pulse" />
                    </div>

                    {/* Generated Flow */}
                    <div className="flex flex-col gap-3">
                        <div className="flex gap-4 justify-center">
                            <div className="w-24 h-8 bg-white border border-primary text-primary text-[10px] font-bold flex items-center justify-center rounded shadow-sm animate-fade-in-right" style={{animationDelay: '0.2s'}}>
                                User Login
                            </div>
                        </div>
                        <div className="flex gap-4 relative">
                            {/* Connecting Lines (CSS borders) */}
                            <div className="absolute top-[-12px] left-1/2 -translate-x-1/2 w-16 h-4 border-l border-r border-t border-slate-300 rounded-t-lg"></div>
                            
                            <div className="w-24 h-8 bg-white border border-slate-300 text-slate-500 text-[10px] flex items-center justify-center rounded shadow-sm animate-fade-in-right" style={{animationDelay: '0.6s'}}>
                                Success
                            </div>
                            <div className="w-24 h-8 bg-white border border-red-200 text-red-400 text-[10px] flex items-center justify-center rounded shadow-sm animate-fade-in-right" style={{animationDelay: '0.8s'}}>
                                Error
                            </div>
                        </div>
                    </div>
                </div>
                <style>{`
                    @keyframes fade-in-right { from { opacity: 0; transform: translateX(-10px); } to { opacity: 1; transform: translateX(0); } }
                    .animate-fade-in-right { animation: fade-in-right 0.5s ease-out forwards; opacity: 0; }
                `}</style>
            </div>
        );
    }

    // 3. Demo: Wireframe to UI Transformation
    if (idx === 2) {
        return (
            <div className="h-48 w-full bg-slate-100 rounded-lg mt-4 relative border border-slate-200 overflow-hidden flex items-center justify-center">
                {/* Browser Window Frame */}
                <div className="w-3/4 h-28 bg-white rounded-lg shadow-lg border border-slate-200 relative overflow-hidden">
                    {/* Header */}
                    <div className="h-4 bg-slate-50 border-b border-slate-100 flex items-center px-2 gap-1">
                        <div className="w-2 h-2 rounded-full bg-red-400"></div>
                        <div className="w-2 h-2 rounded-full bg-amber-400"></div>
                        <div className="w-2 h-2 rounded-full bg-green-400"></div>
                    </div>

                    {/* Content Container */}
                    <div className="relative w-full h-full p-3">
                        {/* Layer 1: Wireframe (Skeleton) */}
                        <div className="absolute inset-0 p-3 flex gap-2 animate-fade-out-cycle">
                            <div className="w-1/3 h-full bg-slate-100 rounded"></div>
                            <div className="flex-1 flex flex-col gap-2">
                                <div className="w-full h-8 bg-slate-100 rounded"></div>
                                <div className="w-full h-16 bg-slate-100 rounded"></div>
                            </div>
                        </div>

                        {/* Layer 2: High Fidelity UI */}
                        <div className="absolute inset-0 p-3 flex gap-2 animate-fade-in-cycle opacity-0">
                            <div className="w-1/3 h-full bg-slate-800 rounded flex flex-col items-center justify-center gap-1">
                                <div className="w-6 h-6 rounded-full bg-slate-600"></div>
                                <div className="w-8 h-1 bg-slate-600 rounded"></div>
                            </div>
                            <div className="flex-1 flex flex-col gap-2">
                                <div className="w-full h-8 bg-primary/10 rounded flex items-center px-2">
                                    <div className="w-16 h-2 bg-primary/40 rounded"></div>
                                </div>
                                <div className="w-full h-16 bg-white border border-slate-100 rounded shadow-sm p-2 flex gap-2">
                                    <div className="w-8 h-8 bg-orange-100 rounded-full"></div>
                                    <div className="flex-1 space-y-1">
                                        <div className="w-full h-1.5 bg-slate-100 rounded"></div>
                                        <div className="w-2/3 h-1.5 bg-slate-100 rounded"></div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        {/* Cursor Animation */}
                        <div className="absolute z-20 top-1/2 left-1/2 w-4 h-4 text-slate-800 animate-cursor-move">
                            <svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 3l7.07 16.97 2.51-7.39 7.39-2.51L3 3z"/></svg>
                        </div>
                    </div>
                </div>
                <style>{`
                    @keyframes fade-out-cycle { 0%, 45% { opacity: 1; } 55%, 100% { opacity: 0; } }
                    @keyframes fade-in-cycle { 0%, 45% { opacity: 0; } 55%, 100% { opacity: 1; } }
                    .animate-fade-out-cycle { animation: fade-out-cycle 4s infinite; }
                    .animate-fade-in-cycle { animation: fade-in-cycle 4s infinite; }
                    @keyframes cursor-move { 
                        0% { transform: translate(0, 0); } 
                        40% { transform: translate(40px, 20px); } 
                        50% { transform: translate(40px, 20px) scale(0.9); } 
                        60% { transform: translate(40px, 20px) scale(1); }
                        100% { transform: translate(0, 0); } 
                    }
                    .animate-cursor-move { animation: cursor-move 4s infinite; }
                `}</style>
            </div>
        );
    }

    // 4. Testing: Terminal Runner
    if (idx === 3) {
        return (
            <div className="h-48 w-full bg-slate-900 rounded-lg mt-4 relative border border-slate-800 overflow-hidden p-4 font-mono text-[10px] leading-relaxed shadow-2xl flex flex-col">
                {/* Header */}
                <div className="flex items-center gap-1.5 mb-2 opacity-50 border-b border-slate-700 pb-2 shrink-0">
                    <div className="w-2 h-2 rounded-full bg-red-500"></div>
                    <div className="w-2 h-2 rounded-full bg-yellow-500"></div>
                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                    <span className="ml-2 text-slate-400">test_runner.sh</span>
                </div>
                
                {/* Content - Scrolling Area */}
                <div className="relative flex-1 overflow-hidden mask-gradient-bottom">
                    <div className="absolute top-0 left-0 w-full animate-terminal-scroll">
                        {/* Logs repeated for scrolling effect */}
                        {[0, 1].map(cycle => (
                            <div key={cycle} className="flex flex-col gap-1 pb-4">
                                <div className="text-slate-500">$ npm run test:e2e</div>
                                <div className="text-slate-400">Starting test suite...</div>
                                {[
                                    { file: 'AuthService.spec.ts', time: '12ms' },
                                    { file: 'PaymentGateway.spec.ts', time: '45ms' },
                                    { file: 'UserProfile.spec.ts', time: '23ms' },
                                    { file: 'OrderController.spec.ts', time: '67ms' },
                                    { file: 'Notification.spec.ts', time: '89ms' },
                                    { file: 'Database.spec.ts', time: '120ms' },
                                ].map((log, i) => (
                                    <div key={`${cycle}-${i}`} className="flex items-center gap-2 text-green-400">
                                        <span>✓</span> <span>{log.file}</span> <span className="text-slate-600 ml-auto">{log.time}</span>
                                    </div>
                                ))}
                                <div className="text-emerald-300 font-bold mt-2">Test Suites: 6 passed, 6 total</div>
                                <div className="text-slate-500 mt-4">$ waiting for changes...</div>
                            </div>
                        ))}
                    </div>
                </div>

                <style>{`
                    @keyframes terminal-scroll { 0% { transform: translateY(0); } 100% { transform: translateY(-50%); } }
                    .animate-terminal-scroll { animation: terminal-scroll 10s linear infinite; }
                    .mask-gradient-bottom { mask-image: linear-gradient(to bottom, black 80%, transparent 100%); }
                `}</style>
            </div>
        );
    }
    return null;
};

// --- Grid Visual Fallback (Advanced Dynamic Effects) ---
const GridVisualFallback = ({ item, isModal = false }) => {
    const [tick, setTick] = useState(0);
    
    useEffect(() => {
        // 加快动画频率，使交互更流畅
        const timer = setInterval(() => setTick(t => t + 1), 800); 
        return () => clearInterval(timer);
    }, []);

    const containerClass = `w-full h-full flex items-center justify-center relative overflow-hidden ${isModal ? 'bg-slate-50' : 'bg-slate-50 group-hover:bg-white transition-colors'}`;
    const scaleClass = isModal ? 'scale-125' : 'scale-100';

    // 1. 竞品洞察 - Radar Chart (雷达扫描)
    if (item.title.includes('竞品洞察')) {
        return (
            <div className={containerClass}>
                <div className="absolute inset-0 bg-[radial-gradient(#e2e8f0_1px,transparent_1px)] [background-size:16px_16px] opacity-50"></div>
                <div className={`relative w-48 h-48 flex items-center justify-center ${scaleClass} transition-transform duration-500`}>
                    {/* Radar Grid */}
                    {[1, 2, 3].map(i => (
                        <div key={i} className="absolute border border-slate-200 rounded-full" style={{ width: `${i * 30}%`, height: `${i * 30}%` }}></div>
                    ))}
                    {/* Axes */}
                    <div className="absolute w-full h-px bg-slate-200"></div>
                    <div className="absolute h-full w-px bg-slate-200"></div>
                    
                    {/* Data Shape - Animated */}
                    <svg className="absolute inset-0 w-full h-full overflow-visible" viewBox="0 0 100 100">
                        <polygon 
                            points="50,20 80,50 50,80 20,50" 
                            className="fill-primary/10 stroke-primary stroke-[0.5]"
                            style={{ transformOrigin: 'center', transform: `scale(${0.9 + Math.sin(tick * 0.5)*0.05})` }}
                        />
                        <polygon 
                            points="50,10 90,40 60,90 10,60" 
                            className="fill-blue-500/10 stroke-blue-400 stroke-[0.5] [stroke-dasharray:2,2]"
                            style={{ transformOrigin: 'center', transform: `scale(${0.8 + Math.cos(tick * 0.5)*0.05}) rotate(${Math.sin(tick * 0.5)*5}deg)` }}
                        />
                    </svg>
                    
                    {/* Labels */}
                    <div className="absolute top-6 text-[8px] bg-white/80 px-1 rounded text-slate-500 backdrop-blur-sm">Feature</div>
                    <div className="absolute bottom-6 text-[8px] bg-white/80 px-1 rounded text-slate-500 backdrop-blur-sm">Price</div>
                    <div className="absolute left-6 text-[8px] bg-white/80 px-1 rounded text-slate-500 backdrop-blur-sm">UX</div>
                    <div className="absolute right-6 text-[8px] bg-white/80 px-1 rounded text-slate-500 backdrop-blur-sm">Service</div>

                    {/* Scanning Effect */}
                    <div className="absolute inset-0 rounded-full bg-gradient-to-tr from-transparent via-primary/10 to-transparent animate-spin-slow" style={{animationDuration: '4s'}}></div>

                    {/* Modal Extra: Legend */}
                    {isModal && (
                        <div className="absolute -bottom-10 flex gap-4 text-[10px]">
                            <div className="flex items-center gap-1"><div className="w-2 h-2 bg-primary/50 rounded-full"></div> My Product</div>
                            <div className="flex items-center gap-1"><div className="w-2 h-2 bg-blue-400/50 rounded-full"></div> Competitor</div>
                        </div>
                    )}
                </div>
            </div>
        );
    }

    // 2. 反馈统计 - Live Leaderboard (实时榜单)
    if (item.title.includes('反馈统计')) {
        const allItems = [
            { label: 'Dark Mode', count: 85, trend: 'up' },
            { label: 'Offline Sync', count: 62, trend: 'same' },
            { label: 'Apple Watch', count: 45, trend: 'up' },
            { label: 'Export PDF', count: 38, trend: 'down' },
            { label: 'Calendar', count: 32, trend: 'up' },
        ];
        // 模拟动态排序
        const displayItems = isModal ? allItems : allItems.slice(0, 3);
        
        return (
            <div className={`w-full h-full bg-slate-900 p-6 flex flex-col justify-center gap-4 relative overflow-hidden ${isModal ? 'px-12' : ''}`}>
                <div className="absolute top-3 right-3 flex items-center gap-1 opacity-70">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full animate-ping"></div>
                    <span className="text-[8px] text-green-400 font-mono">LIVE</span>
                </div>
                {displayItems.map((it, i) => (
                    <div key={i} className="flex flex-col gap-1.5">
                        <div className="flex justify-between text-[10px] text-slate-400 font-medium items-center">
                            <span className="flex items-center gap-2">
                                <span className="text-slate-600 font-mono">0{i+1}</span>
                                {it.label}
                            </span>
                            <span className="font-mono text-primary flex items-center gap-1">
                                {it.count + Math.floor(Math.sin(tick + i) * 3)}
                                {it.trend === 'up' && <span className="text-[8px] text-green-500">▲</span>}
                            </span>
                        </div>
                        <div className="w-full h-1.5 bg-slate-800 rounded-full overflow-hidden">
                            <div 
                                className="h-full bg-gradient-to-r from-primary to-emerald-400 transition-all duration-1000 ease-out"
                                style={{ width: `${(it.count / 100) * 100 + Math.sin(tick + i) * 2}%` }}
                            ></div>
                        </div>
                    </div>
                ))}
            </div>
        );
    }

    // 3. 虚拟用户访谈 - Chat Simulation (对话模拟)
    if (item.title.includes('虚拟用户访谈')) {
        const messages = [
            { role: 'ai', text: '您平时健身遇到的最大痛点是什么？' },
            { role: 'u', text: '主要是没时间去健身房，在家又不知道练什么。' },
            { role: 'ai', text: '如果有一款AI教练能实时指导，您会感兴趣吗？' },
            { role: 'u', text: '那太好了，但我担心动作做不标准。' },
            { role: 'ai', text: '明白了，视觉纠错功能对您很重要。' }
        ];
        
        // 循环展示消息
        const visibleCount = isModal ? messages.length : 2;
        const currentStep = tick % (visibleCount + 2);

        return (
            <div className={`w-full h-full bg-slate-50 p-4 flex flex-col gap-3 relative overflow-hidden ${isModal ? 'px-12 py-8' : ''}`}>
                {messages.slice(0, Math.min(currentStep, visibleCount)).map((msg, i) => (
                    <div key={i} className={`flex items-start gap-2 animate-fade-in-up ${msg.role === 'u' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[8px] font-bold border ${msg.role === 'ai' ? 'bg-primary/10 text-primary border-primary/20' : 'bg-blue-100 text-blue-600 border-blue-200'}`}>
                            {msg.role === 'ai' ? 'AI' : 'U'}
                        </div>
                        <div className={`p-2 rounded-xl shadow-sm text-[9px] max-w-[85%] leading-relaxed ${msg.role === 'ai' ? 'bg-white rounded-tl-none border border-slate-100 text-slate-600' : 'bg-blue-500 text-white rounded-tr-none'}`}>
                            {msg.text}
                        </div>
                    </div>
                ))}
                {currentStep <= visibleCount && (
                    <div className="flex items-start gap-2 animate-fade-in">
                        <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-[8px] text-slate-500">...</div>
                        <div className="bg-slate-100 p-2 rounded-xl rounded-tl-none text-[9px] text-slate-400 flex gap-1 items-center">
                            <span className="w-1 h-1 bg-slate-400 rounded-full animate-bounce"></span>
                            <span className="w-1 h-1 bg-slate-400 rounded-full animate-bounce" style={{animationDelay:'0.1s'}}></span>
                            <span className="w-1 h-1 bg-slate-400 rounded-full animate-bounce" style={{animationDelay:'0.2s'}}></span>
                        </div>
                    </div>
                )}
            </div>
        );
    }

    // 4. 旅程模拟 - Emotion Map (情绪曲线)
    if (item.title.includes('旅程模拟')) {
        return (
            <div className={`w-full h-full bg-white p-5 flex flex-col justify-center relative ${isModal ? 'px-12' : ''}`}>
                {/* Path Line */}
                <div className="absolute top-1/2 left-6 right-6 h-0.5 bg-slate-100"></div>
                
                <div className="flex justify-between relative z-10">
                    {['Start', 'Plan', 'Action', 'End'].map((step, i) => (
                        <div key={i} className="flex flex-col items-center gap-2">
                            <div className={`w-3 h-3 rounded-full border-2 ${i <= (tick % 5) ? 'bg-primary border-primary scale-125 shadow-lg shadow-primary/30' : 'bg-white border-slate-200'} transition-all duration-500`}></div>
                            <span className="text-[8px] text-slate-400 uppercase font-bold tracking-wider">{step}</span>
                        </div>
                    ))}
                </div>

                {/* Emotion Curve */}
                <svg className="absolute bottom-0 left-0 w-full h-16 opacity-10 pointer-events-none" preserveAspectRatio="none">
                    <path d="M0,50 Q30,0 50,50 T100,20" fill="none" stroke="currentColor" strokeWidth="4" className="text-primary" />
                </svg>

                {/* Moving Avatar */}
                <div 
                    className="absolute top-1/2 -mt-4 w-8 h-8 bg-white rounded-full shadow-md border border-slate-100 flex items-center justify-center text-lg transition-all duration-700 ease-in-out z-20"
                    style={{ left: `${((tick % 5) / 3) * 80 + 10}%`, opacity: (tick % 5) > 3 ? 0 : 1 }}
                >
                    {['🤔', '💡', '🔥', '🎉'][tick % 4] || '🤔'}
                </div>
            </div>
        );
    }

    // 5. 数据自由 - NL to SQL (自然语言查询)
    if (item.title.includes('数据自由')) {
        const steps = [
            { t: '查询上周用户留存率...', type: 'input' },
            { t: 'SELECT retention FROM users...', type: 'code' },
            { t: 'Rendering Chart...', type: 'system' }
        ];
        const currentStep = tick % 4;

        return (
            <div className={`w-full h-full bg-slate-800 p-5 flex flex-col gap-4 font-mono ${isModal ? 'px-12 py-8' : ''}`}>
                <div className="flex items-center gap-2 text-[10px] text-slate-400 border-b border-slate-700 pb-2">
                    <span className="text-green-400 font-bold">➜</span>
                    <span className="text-slate-300">{currentStep >= 0 ? steps[0].t : ''}</span>
                    {currentStep === 0 && <span className="w-1.5 h-3 bg-slate-400 animate-pulse"></span>}
                </div>
                
                {currentStep >= 1 && (
                    <div className="text-[9px] text-blue-300 bg-slate-900/50 p-2 rounded border-l-2 border-blue-500 animate-fade-in">
                        {steps[1].t}
                    </div>
                )}

                {currentStep >= 2 && (
                    <div className="flex-1 flex items-end gap-1.5 opacity-90 animate-scale-up origin-bottom">
                        {[40, 65, 45, 80, 55, 70, 60].map((h, i) => (
                            <div key={i} className="flex-1 bg-primary hover:bg-emerald-400 transition-all duration-500 rounded-t-sm" style={{ height: `${h}%` }}></div>
                        ))}
                    </div>
                )}
            </div>
        );
    }

    // 6. 智能归因 - Network Diag (系统诊断)
    if (item.title.includes('智能归因')) {
        return (
            <div className={containerClass}>
                {/* Nodes */}
                <div className="absolute top-1/3 left-1/4 w-3 h-3 bg-slate-300 rounded-full z-10"></div>
                <div className="absolute top-1/3 right-1/4 w-3 h-3 bg-slate-300 rounded-full z-10"></div>
                <div className="absolute bottom-1/3 left-1/2 w-4 h-4 bg-red-500 rounded-full shadow-[0_0_15px_rgba(239,68,68,0.6)] animate-pulse z-10"></div>
                
                {/* Lines */}
                <svg className="absolute inset-0 w-full h-full pointer-events-none">
                    <line x1="25%" y1="33%" x2="50%" y2="66%" stroke="#cbd5e1" strokeWidth="1" />
                    <line x1="75%" y1="33%" x2="50%" y2="66%" stroke="#cbd5e1" strokeWidth="1" />
                </svg>

                {/* Alert Box */}
                {tick % 2 === 0 && (
                    <div className="absolute bottom-6 bg-white border border-red-100 shadow-lg rounded px-3 py-1.5 flex items-center gap-2 animate-bounce" style={{ animationDuration: '2s' }}>
                        <window.Icon name="AlertTriangle" className="w-4 h-4 text-red-500" />
                        <span className="text-[9px] text-slate-600 font-bold">Root Cause: API Timeout</span>
                    </div>
                )}
            </div>
        );
    }

    // Default Fallback (Original Placeholder)
    return (
        <div className="w-full h-full flex flex-col items-center justify-center text-slate-300 bg-slate-50">
            <window.Icon name={item.icon} className="w-8 h-8 opacity-50 mb-2" />
            <span className="text-xs font-medium text-slate-400">{item.detailImageText || 'No Asset'}</span>
        </div>
    );
};

// --- Enhanced Modal (Replaces window.Modal for SlideGrid) ---
const EnhancedModal = ({ isOpen, onClose, item }) => {
    if (!isOpen || !item) return null;
    const imgSrc = window.resolveImage(item.detailImage);
    const isVideo = imgSrc && imgSrc.toLowerCase().endsWith('.mp4');

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 md:p-8 animate-fade-in">
            <div className="absolute inset-0 bg-slate-900/60 backdrop-blur-sm transition-opacity" onClick={onClose}></div>
            <div className="bg-white w-full max-w-5xl max-h-[90vh] rounded-2xl shadow-2xl overflow-hidden flex flex-col md:flex-row relative z-10 animate-scale-up">
                <button className="absolute top-4 right-4 z-20 p-2 bg-black/10 hover:bg-black/20 rounded-full text-slate-600 transition-colors" onClick={onClose}>
                    <window.Icon name="X" className="w-5 h-5" />
                </button>
                
                {/* Media Section */}
                <div className="w-full md:w-2/3 bg-slate-50 relative min-h-[300px] md:min-h-full flex items-center justify-center overflow-hidden border-r border-slate-100">
                     {imgSrc ? (
                        isVideo ? (
                            <video src={imgSrc} className="w-full h-full object-contain" controls autoPlay />
                        ) : (
                            <img src={imgSrc} className="w-full h-full object-contain" />
                        )
                     ) : (
                        // Pass isModal=true to enable detailed view
                        <GridVisualFallback item={item} isModal={true} />
                     )}
                </div>

                {/* Content Section */}
                <div className="w-full md:w-1/3 p-8 overflow-y-auto bg-white flex flex-col">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="p-2 bg-primary/10 rounded-lg text-primary">
                            <window.Icon name={item.icon} className="w-6 h-6" />
                        </div>
                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">{item.category}</span>
                    </div>
                    <h3 className="text-2xl font-bold text-slate-800 mb-4">{item.title}</h3>
                    <div className="prose prose-sm text-slate-600 flex-1">
                        <p className="text-base leading-relaxed mb-6">{item.desc}</p>
                        {item.detailDesc && (
                            <div className="bg-slate-50 p-5 rounded-xl border border-slate-100 text-sm shadow-inner">
                                <h4 className="font-bold text-slate-700 mb-2 flex items-center gap-2">
                                    <window.Icon name="Info" className="w-4 h-4 text-primary" /> 
                                    详细说明
                                </h4>
                                <p className="leading-relaxed">{item.detailDesc}</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

// --- Scenario Interactive Demo ---
const ScenarioDemo = ({ item, externalTrigger, onTriggerHandled, stopMusicSignal }) => {
    const isKnowledge = item.title.includes('知识库');
    const isMusic = item.title.includes('音乐');
    const isReqReview = item.title.includes('需求预评审');
    const isReport = item.title.includes('竞品');
    const isAfterSales = item.title.includes('售后');

    const [input, setInput] = useState('');
    
    let initialMsg = '你好！';
    if (isKnowledge) initialMsg = '我了解一切运动知识，想问我什么？';
    if (isMusic) initialMsg = '你喜欢什么类型的音乐？';
    if (isReqReview) initialMsg = '请粘贴需求文档内容，我将进行预评审。';
    if (isReport) initialMsg = '请输入你想调研的竞品名称。';
    if (isAfterSales) initialMsg = '请描述用户遇到的售后问题。';

    const [messages, setMessages] = useState([
        { role: 'ai', type: 'text', content: initialMsg }
    ]);
    const [isThinking, setIsThinking] = useState(false);
    const [musicPlaying, setMusicPlaying] = useState(false);
    const messagesEndRef = useRef(null);
    const audioRef = useRef(null);

    // 监听停止音乐信号 (唤醒时暂停)
    useEffect(() => {
        if (stopMusicSignal && musicPlaying) {
            setMusicPlaying(false);
        }
    }, [stopMusicSignal]);

    // TTS 语音播报函数
    const speak = (text) => {
        // 移除 cancel()，支持多任务时的语音队列顺序播放
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'zh-CN';
        window.speechSynthesis.speak(u);
    };

    // 监听外部全局指令
    useEffect(() => {
        if (externalTrigger) {
            const cmd = externalTrigger.text;
            let shouldTrigger = false;

            // 严格匹配逻辑，确保只有能产生有效回复的指令才触发，避免无关对话框输入文字
            if (isKnowledge && cmd.includes('五分化')) shouldTrigger = true;
            else if (isMusic && cmd.includes('有氧')) shouldTrigger = true;
            else if (isReqReview && (cmd.includes('需求') || cmd.includes('登录'))) shouldTrigger = true;
            else if (isReport && (cmd.toUpperCase().includes('KEEP') || cmd.includes('竞品'))) shouldTrigger = true;
            else if (isAfterSales && (cmd.includes('开机') || cmd.includes('故障'))) shouldTrigger = true;

            if (shouldTrigger) {
                handleSend(cmd);
            }
        }
    }, [externalTrigger]);

    // 监听播放状态控制音频
    useEffect(() => {
        if (audioRef.current) {
            if (musicPlaying) {
                audioRef.current.play().catch(e => console.log("Autoplay blocked:", e));
            } else {
                audioRef.current.pause();
            }
        }
    }, [musicPlaying]);

    // 监听消息变化，自动播报 AI 回复
    useEffect(() => {
        const lastMsg = messages[messages.length - 1];
        // 仅播报 AI 的文本消息，且排除初始欢迎语（长度>1时才播报）
        if (lastMsg && lastMsg.role === 'ai' && lastMsg.type === 'text' && messages.length > 1) {
            speak(lastMsg.content);
        }
    }, [messages]);

    // 自动滚动到底部
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isThinking]);

    // 组件卸载时停止语音
    useEffect(() => () => window.speechSynthesis.cancel(), []);

    const handleSend = (textOverride) => {
        const textToSend = typeof textOverride === 'string' ? textOverride : input;
        const isExternal = typeof textOverride === 'string';
        if (!textToSend.trim()) return;
        
        // 1. 添加用户消息
        const userMsg = { role: 'user', type: 'text', content: textToSend };
        setMessages(prev => [...prev, userMsg]);
        const currentInput = textToSend;
        setInput('');
        setIsThinking(true);

        // 2. 模拟 AI 思考与处理
        setTimeout(() => {
            setIsThinking(false);
            
            // --- 知识库逻辑 ---
            if (isKnowledge) {
                if (currentInput.includes('五分化')) {
                    // 先回复文本
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '五分化训练（Bro Split）是一种经典的健美分化模式，将全身肌群拆分为5个部位，每天专注轰炸一个部位，适合追求极致局部刺激的中高阶训练者。' }]);
                    // 再弹窗展示计划
                    setTimeout(() => {
                        setMessages(prev => [...prev, { role: 'ai', type: 'visual', contentType: 'knowledge-plan' }]);
                    }, 600);
                } else if (!isExternal) { // 仅在非全局指令时回复“不知道”
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '这个知识点我还在学习中，试试问我“五分化增肌计划”？' }]);
                }
            } 
            // --- 需求预评审逻辑 ---
            else if (isReqReview) {
                if (currentInput.includes('需求') || currentInput.includes('登录')) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '正在扫描需求文档，比对公司 PRD 规范...' }]);
                    setTimeout(() => {
                        setMessages(prev => [...prev, { role: 'ai', type: 'visual', contentType: 'req-review' }]);
                    }, 600);
                } else if (!isExternal) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '请试着输入“登录模块需求”...' }]);
                }
            }
            // --- 竞品研报逻辑 ---
            else if (isReport) {
                if (currentInput.toUpperCase().includes('KEEP') || currentInput.includes('竞品')) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '正在全网扫描 Keep 的最新动态与用户评价...' }]);
                    setTimeout(() => {
                        setMessages(prev => [...prev, { role: 'ai', type: 'visual', contentType: 'competitor-table' }]);
                    }, 600);
                } else if (!isExternal) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '请试着输入“分析 Keep”...' }]);
                }
            }
            // --- 售后助手逻辑 ---
            else if (isAfterSales) {
                if (currentInput.includes('开机') || currentInput.includes('故障')) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '检索到相关解决方案，建议按以下步骤排查：' }]);
                    setTimeout(() => {
                        setMessages(prev => [...prev, { role: 'ai', type: 'visual', contentType: 'after-sales' }]);
                    }, 600);
                } else if (!isExternal) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '请描述故障现象，例如“无法开机”...' }]);
                }
            }
            // --- 音乐生成逻辑 ---
            else if (isMusic) {
                if (currentInput.includes('有氧')) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '已识别有氧训练场景，为您生成 128 BPM 的快节奏配乐，提升心率表现。' }]);
                    setTimeout(() => {
                        setMessages(prev => [...prev, { role: 'ai', type: 'visual', contentType: 'music-player' }]);
                        setMusicPlaying(true);
                    }, 600);
                } else if (!isExternal) {
                    setMessages(prev => [...prev, { role: 'ai', type: 'text', content: '没问题，试试输入“适合有氧的音乐”？' }]);
                }
            }
        }, 1500);
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSend(input);
    };

    return (
        <div className="h-64 w-full bg-slate-50 relative overflow-hidden flex flex-col border-b border-slate-100 group-hover:bg-white transition-colors"
             onClick={(e) => e.stopPropagation()}
             style={{ cursor: 'default' }}>
            {/* Chat Interface */}
            <div className="flex-1 p-4 overflow-y-auto text-xs space-y-3 font-sans hide-scrollbar">
                {messages.map((msg, idx) => (
                    <div key={idx} className={`flex gap-2 animate-fade-in ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] shrink-0 font-bold ${msg.role === 'ai' ? 'bg-primary/20 text-primary' : 'bg-slate-200 text-slate-600'}`}>
                            {msg.role === 'ai' ? 'AI' : 'Me'}
                        </div>
                        
                        {msg.type === 'text' ? (
                            <div className={`p-2.5 shadow-sm border max-w-[85%] leading-relaxed ${
                                msg.role === 'ai' 
                                    ? 'bg-white rounded-r-xl rounded-bl-xl border-slate-100 text-slate-600' 
                                    : 'bg-primary text-white rounded-l-xl rounded-br-xl border-primary'
                            }`}>
                                {msg.content}
                            </div>
                        ) : (
                            // Visual Card (Popup)
                            <div className="bg-white p-0 rounded-xl shadow-lg border border-primary/20 w-full max-w-[95%] overflow-hidden animate-fade-in-up">
                                {msg.contentType === 'knowledge-plan' && (
                                    <div className="flex flex-col">
                                        <div className="bg-primary/5 px-3 py-2 border-b border-primary/10 flex justify-between items-center">
                                            <span className="font-bold text-primary text-[10px]">📅 五分化增肌周计划</span>
                                            <span className="text-[8px] text-slate-400">AI Generated</span>
                                        </div>
                                        <div className="p-2 grid grid-cols-5 gap-1.5">
                                            {[
                                                { day: '周一', part: '胸部', action: '卧推/飞鸟', color: 'bg-red-50 text-red-600 border-red-100' },
                                                { day: '周二', part: '背部', action: '引体/划船', color: 'bg-blue-50 text-blue-600 border-blue-100' },
                                                { day: '周三', part: '肩部', action: '推举/侧平举', color: 'bg-green-50 text-green-600 border-green-100' },
                                                { day: '周四', part: '腿部', action: '深蹲/腿举', color: 'bg-amber-50 text-amber-600 border-amber-100' },
                                                { day: '周五', part: '手臂', action: '弯举/下压', color: 'bg-purple-50 text-purple-600 border-purple-100' },
                                            ].map((d, i) => (
                                                <div key={i} className={`flex flex-col items-center justify-center p-1.5 rounded border ${d.color}`}>
                                                    <div className="text-[8px] opacity-70 mb-0.5">{d.day}</div>
                                                    <div className="font-bold text-[10px] mb-0.5">{d.part}</div>
                                                    <div className="text-[6px] opacity-80 scale-90 whitespace-nowrap">{d.action}</div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {msg.contentType === 'music-player' && (
                                    <div className="bg-slate-900 text-white p-3">
                                        <audio ref={audioRef} src={window.resolveImage('冲刺节拍.mp3')} loop />
                                        <div className="flex gap-3 items-center mb-3">
                                            <div className="w-10 h-10 rounded bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center shadow-lg">
                                                <window.Icon name="Music" className="w-5 h-5 text-white" />
                                            </div>
                                            <div className="flex-1 min-w-0">
                                                <div className="font-bold text-xs truncate">Cyberpunk HIIT Protocol</div>
                                                <div className="text-[8px] text-slate-400">AI Composer • 128 BPM</div>
                                            </div>
                                            <button 
                                                onClick={() => setMusicPlaying(!musicPlaying)}
                                                className="w-8 h-8 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary-dark transition-colors"
                                            >
                                                <window.Icon name={musicPlaying ? "Pause" : "Play"} className="w-4 h-4 fill-current" />
                                            </button>
                                        </div>
                                        {/* Waveform Visualizer */}
                                        <div className="flex items-end justify-between h-6 gap-0.5 opacity-80">
                                            {Array.from({length: 30}).map((_, i) => (
                                                <div 
                                                    key={i} 
                                                    className={`w-1 bg-primary rounded-t-sm transition-all duration-100 ${musicPlaying ? 'animate-pulse' : ''}`}
                                                    style={{ 
                                                        height: musicPlaying ? `${Math.random() * 100}%` : '20%',
                                                        animationDelay: `${i * 0.05}s`
                                                    }}
                                                ></div>
                                            ))}
                                        </div>
                                        {/* Progress Bar */}
                                        <div className="w-full h-1 bg-slate-700 rounded-full mt-3 overflow-hidden">
                                            <div className={`h-full bg-white ${musicPlaying ? 'w-1/3 animate-progress' : 'w-0'}`}></div>
                                        </div>
                                    </div>
                                )}
                                {msg.contentType === 'req-review' && (
                                    <div className="bg-white p-3 border-l-4 border-blue-500">
                                        <div className="font-bold text-slate-800 text-xs mb-2">需求质量评分: 85</div>
                                        <div className="space-y-2">
                                            <div className="flex items-center gap-2 text-[10px] text-green-600">
                                                <window.Icon name="CheckCircle" className="w-3 h-3" /> <span>流程闭环检查通过</span>
                                            </div>
                                            <div className="flex items-center gap-2 text-[10px] text-red-500">
                                                <window.Icon name="X" className="w-3 h-3" /> <span>缺失异常分支定义</span>
                                            </div>
                                        </div>
                                    </div>
                                )}
                                {msg.contentType === 'competitor-table' && (
                                    <div className="bg-white p-2">
                                        <div className="text-[10px] font-bold text-slate-500 mb-1">竞品对比矩阵</div>
                                        <table className="w-full text-[9px] border-collapse">
                                            <thead>
                                                <tr className="bg-slate-50 text-slate-400">
                                                    <th className="p-1 border border-slate-100 text-left">维度</th>
                                                    <th className="p-1 border border-slate-100 text-left text-primary">我方</th>
                                                    <th className="p-1 border border-slate-100 text-left">Keep</th>
                                                </tr>
                                            </thead>
                                            <tbody>
                                                <tr>
                                                    <td className="p-1 border border-slate-100 font-medium">AI 辅导</td>
                                                    <td className="p-1 border border-slate-100 bg-primary/5 text-primary">实时纠错</td>
                                                    <td className="p-1 border border-slate-100">计次为主</td>
                                                </tr>
                                                <tr>
                                                    <td className="p-1 border border-slate-100 font-medium">个性化</td>
                                                    <td className="p-1 border border-slate-100 bg-primary/5 text-primary">动态调整</td>
                                                    <td className="p-1 border border-slate-100">固定课表</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                )}
                                {msg.contentType === 'after-sales' && (
                                    <div className="bg-white p-3 border-l-4 border-green-500">
                                        <div className="font-bold text-slate-800 text-xs mb-2">推荐解决方案</div>
                                        <div className="bg-slate-50 p-2 rounded text-[10px] text-slate-600 mb-1">
                                            1. 长按电源键 10s 强制重启
                                        </div>
                                        <div className="bg-slate-50 p-2 rounded text-[10px] text-slate-600">
                                            2. 检查充电器连接是否松动
                                        </div>
                                    </div>
                                )}
                            </div>
                        )}
                    </div>
                ))}

                {/* Thinking Indicator */}
                {isThinking && (
                    <div className="flex gap-2 animate-pulse">
                        <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-primary text-[10px] shrink-0 font-bold">AI</div>
                        <div className="bg-slate-100 p-2 rounded-r-xl rounded-bl-xl text-slate-400 text-[10px] flex items-center gap-1">
                           <span>思考中</span><span className="animate-bounce">.</span><span className="animate-bounce" style={{animationDelay:'0.1s'}}>.</span><span className="animate-bounce" style={{animationDelay:'0.2s'}}>.</span>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            {/* Input Area */}
            <div className="p-3 bg-white border-t border-slate-100 relative z-10 flex gap-2">
                {/* Placeholder Logic */}
                {(() => {
                    let ph = "请输入...";
                    if (isKnowledge) ph = "试一试：五分化...";
                    else if (isMusic) ph = "试一试：有氧...";
                    else if (isReqReview) ph = "试一试：登录模块需求...";
                    else if (isReport) ph = "试一试：分析 Keep...";
                    else if (isAfterSales) ph = "试一试：无法开机...";
                    
                    return (
                <div className="relative flex-1">
                    <input 
                        type="text" 
                        className="w-full text-xs border border-slate-200 rounded-full pl-3 pr-8 py-2 focus:outline-none focus:border-primary focus:ring-2 focus:ring-primary/20 transition-all shadow-inner bg-slate-50 focus:bg-white"
                        placeholder={ph}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                        disabled={isThinking}
                    />
                </div>
                    );
                })()}
                <button 
                    onClick={() => handleSend(input)}
                    disabled={!input.trim() || isThinking}
                    className="bg-primary text-white rounded-full w-8 h-8 flex items-center justify-center shadow-sm hover:bg-primary-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                    <window.Icon name="ArrowRight" className="w-4 h-4" />
                </button>
            </div>
        </div>
    );
};

// New Component: OfficeAssistant
const OfficeAssistant = ({ onTrigger, onWake }) => {
    const [input, setInput] = useState('');
    const [isListening, setIsListening] = useState(false);
    const recognitionRef = useRef(null);
    
    // 使用 Ref 管理唤醒状态，避免闭包陷阱
    const stateRef = useRef({
        isAwake: false,
        timer: null
    });

    const resetWakeTimer = () => {
        if (stateRef.current.timer) clearTimeout(stateRef.current.timer);
        stateRef.current.timer = setTimeout(() => {
            stateRef.current.isAwake = false;
            setInput(''); // 超时重置，清空输入框给予视觉反馈
        }, 3000);
    };

    const speak = (text) => {
        // 助手自己的语音（如“我在”）需要打断之前的
        window.speechSynthesis.cancel();
        const u = new SpeechSynthesisUtterance(text);
        u.lang = 'zh-CN';
        window.speechSynthesis.speak(u);
    };

    // Initialize Speech Recognition
    useEffect(() => {
        if ('webkitSpeechRecognition' in window) {
            const recognition = new window.webkitSpeechRecognition();
            recognition.continuous = true; // 开启连续识别
            recognition.interimResults = true;
            recognition.lang = 'zh-CN';
            
            recognition.onresult = (event) => {
                let transcript = '';
                let isFinal = false;
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    transcript += event.results[i][0].transcript;
                    if (event.results[i].isFinal) isFinal = true;
                }
                
                if (!transcript.trim()) return;
                setInput(transcript);
                
                // 归一化：去除标点和空格，转小写
                const cleanText = transcript.replace(/[.,?!。，？！\s]/g, '').toLowerCase();
                const isWakeWord = cleanText.includes('同学');

                // 1. 唤醒逻辑
                if (isWakeWord) {
                    if (!stateRef.current.isAwake) {
                        stateRef.current.isAwake = true;
                        speak("我在！");
                        if (onWake) onWake();
                    }
                    resetWakeTimer(); // 刷新超时计时
                } else if (stateRef.current.isAwake) {
                    // 已唤醒状态下，用户说话（非唤醒词），打断“我在”，并刷新计时
                    window.speechSynthesis.cancel();
                    resetWakeTimer();
                }

                // 2. 指令匹配 (仅在唤醒状态下)
                if (stateRef.current.isAwake) {
                // 关键词映射表 (只要命中 key 即可触发)
                const keywords = [
                    'keep', '竞品', '有氧', '音乐', '五分化', '训练', 
                    '需求', '评审', '开机', '售后', '故障', '分析', '生成', '助手'
                ];
                
                const hit = keywords.some(k => cleanText.includes(k));
                
                if (hit && isFinal) {
                    // 命中指令，speak() 会在 handleSend -> useEffect 中被调用，从而打断当前语音
                    onTrigger(transcript); // 传递原始文本给上层处理
                    setInput(''); // 清空输入框
                    
                    // 指令执行完毕，重置为休眠状态 (闭环)
                    stateRef.current.isAwake = false;
                    if (stateRef.current.timer) clearTimeout(stateRef.current.timer);
                }
                }
            };
            
            recognition.onend = () => {
                // 保持监听状态（除非手动停止），模拟 Always-on
                if (isListening) recognition.start();
            };
            
            recognitionRef.current = recognition;
        }
    }, [isListening]);

    const startListening = () => {
        setIsListening(true);
        setInput('');
        if (recognitionRef.current) {
            try { recognitionRef.current.start(); } catch(e) {}
        }
    };

    const stopListening = () => {
        setIsListening(false);
        if (recognitionRef.current) {
            try { recognitionRef.current.abort(); } catch(e) {}
        } else {
            // Simulation for environments without Speech API
            const demos = ['分析 Keep 竞品', '生成有氧音乐', '五分化训练计划', '登录模块需求评审', '无法开机售后'];
            const randomCmd = demos[Math.floor(Math.random() * demos.length)];
            setInput(randomCmd);
            setTimeout(() => onTrigger(randomCmd), 500);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter' && input.trim()) {
            onTrigger(input);
            setInput('');
        }
    };

    return (
        <div className="absolute bottom-8 left-1/2 -translate-x-1/2 w-full max-w-3xl z-50 animate-fade-in-up">
            <div className="bg-white/90 backdrop-blur-xl border border-primary/20 shadow-pearl rounded-full p-3 flex items-center gap-4 ring-1 ring-white/50 transition-all duration-300 hover:shadow-pearl-hover">
                {/* AI Avatar / Status */}
                <div className={`w-12 h-12 rounded-full flex items-center justify-center transition-all duration-500 relative overflow-hidden ${isListening ? 'bg-primary shadow-lg shadow-primary/30' : 'bg-slate-100 border border-slate-200'}`}>
                    {isListening ? (
                        <div className="flex gap-1 items-center h-4">
                            {[1,2,3,2,1].map((h,i) => (
                                <div key={i} className="w-1 bg-white rounded-full animate-wave" style={{height: `${h*25+20}%`, animationDelay: `${i*0.1}s`}}></div>
                            ))}
                        </div>
                    ) : (
                        <window.Icon name="Zap" className={`w-6 h-6 ${isListening ? 'text-white' : 'text-primary'}`} />
                    )}
                </div>

                {/* Input Area */}
                <div className="flex-1 relative">
                    <input 
                        type="text" 
                        className="w-full bg-transparent border-none focus:ring-0 text-slate-700 placeholder-slate-400 text-base font-medium tracking-wide"
                        placeholder={isListening ? "正在聆听... 试着说 '同学'" : "AEKE 办公助手：点击唤醒或输入指令..."}
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={handleKeyDown}
                    />
                </div>

                {/* Voice Button */}
                <button 
                    className={`p-3 rounded-full transition-all duration-300 active:scale-95 ${isListening ? 'bg-red-50 text-red-500 hover:bg-red-100' : 'hover:bg-slate-100 text-slate-400 hover:text-primary'}`}
                    onClick={() => isListening ? stopListening() : startListening()}
                    title={isListening ? "停止聆听" : "点击开启语音助手"}
                >
                    <window.Icon name="Mic" className="w-6 h-6" />
                </button>

                {/* Send Button */}
                <button 
                    className="p-3 rounded-full bg-primary text-white hover:bg-primary-dark transition-all shadow-lg shadow-primary/30 active:scale-95 disabled:opacity-50 disabled:shadow-none"
                    onClick={() => { onTrigger(input); setInput(''); }}
                    disabled={!input.trim()}
                >
                    <window.Icon name="ArrowRight" className="w-6 h-6" />
                </button>
            </div>
            <style>{`
                @keyframes wave { 0%, 100% { height: 20%; } 50% { height: 100%; } }
                .animate-wave { animation: wave 0.5s ease-in-out infinite; }
            `}</style>
        </div>
    );
};

// 6. Summary Slide
const SlideSummary = ({ slide }) => (
    <div className="flex flex-col h-full justify-center px-4 md:px-20 animate-fade-in max-w-[95vw] mx-auto w-full">
        <div className="mb-6 text-center shrink-0">
            <h2 className="text-4xl md:text-6xl font-bold mb-4 gradient-text-primary">{slide.title}</h2>
            <p className="text-xl md:text-2xl text-slate-500">{slide.subtitle}</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-10 max-w-6xl mx-auto w-full flex-1 min-h-0 overflow-y-auto hide-scrollbar pb-4">
            {slide.points.map((point, idx) => (
                <div key={idx} className="clean-panel p-5 rounded-xl flex flex-col hover:border-primary/50 transition-colors group">
                    <div className="flex items-start space-x-4 h-16 mb-2">
                        <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center text-primary shrink-0 group-hover:bg-primary group-hover:text-white transition-colors">
                            <window.Icon name="CheckCircle" className="w-6 h-6" />
                        </div>
                        <p className="text-lg text-slate-700 font-medium leading-relaxed pt-1.5">{point}</p>
                    </div>
                    <SummaryVisual idx={idx} />
                </div>
            ))}
        </div>

        <div className="text-center shrink-0 mb-6 px-4">
            <p className="text-xl md:text-2xl font-bold text-slate-800 italic relative inline-block max-w-4xl leading-normal">
                <span className="text-5xl text-primary/20 absolute -top-6 -left-6 font-serif">“</span>
                {slide.quote}
                <span className="text-5xl text-primary/20 absolute -bottom-8 -right-6 font-serif">”</span>
            </p>
        </div>
    </div>
);

window.SlideCover = SlideCover;
window.SlideTimeline = SlideTimeline;
window.SlideComparison = SlideComparison;
window.SlideGrid = SlideGrid;
window.SlideShowcase = SlideShowcase;
window.SlideSummary = SlideSummary;