const { useState, useEffect } = React;

// --- Icons ---
const SvgIcon = ({ children, className }) => (
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className={className}>
        {children}
    </svg>
);

const Icons = {
    ChevronLeft: (props) => <SvgIcon {...props}><path d="m15 18-6-6 6-6"/></SvgIcon>,
    ChevronRight: (props) => <SvgIcon {...props}><path d="m9 18 6-6-6-6"/></SvgIcon>,
    Zap: (props) => <SvgIcon {...props}><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></SvgIcon>,
    Brain: (props) => <SvgIcon {...props}><rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><path d="M9 1v3"/><path d="M15 1v3"/><path d="M9 20v3"/><path d="M15 20v3"/><path d="M20 9h3"/><path d="M20 14h3"/><path d="M1 9h3"/><path d="M1 14h3"/></SvgIcon>,
    Rocket: (props) => <SvgIcon {...props}><path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="m12 15-3-3a22 22 0 0 1 2-1 20 20 0 0 1 15-15 20 20 0 0 1-15 15 22 22 0 0 1-1 2z"/></SvgIcon>,
    BarChart3: (props) => <SvgIcon {...props}><path d="M3 3v18h18"/><path d="M18 17V9"/><path d="M13 17V5"/><path d="M8 17v-3"/></SvgIcon>,
    Users: (props) => <SvgIcon {...props}><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></SvgIcon>,
    Layout: (props) => <SvgIcon {...props}><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="3" x2="21" y1="9" y2="9"/><line x1="9" x2="9" y1="21" y2="9"/></SvgIcon>,
    Code2: (props) => <SvgIcon {...props}><path d="m18 16 4-4-4-4"/><path d="m6 8-4 4 4 4"/><path d="m14.5 4-5 16"/></SvgIcon>,
    MessageSquare: (props) => <SvgIcon {...props}><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></SvgIcon>,
    MonitorPlay: (props) => <SvgIcon {...props}><path d="m10 7 5 3-5 3z"/><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M12 17v4"/><path d="M8 21h8"/></SvgIcon>,
    FileText: (props) => <SvgIcon {...props}><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></SvgIcon>,
    Image: (props) => <SvgIcon {...props}><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><circle cx="9" cy="9" r="2"/><path d="m21 15-3.086-3.086a2 2 0 0 0-2.828 0L6 21"/></SvgIcon>,
    ArrowRight: (props) => <SvgIcon {...props}><line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/></SvgIcon>,
    X: (props) => <SvgIcon {...props}><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></SvgIcon>,
    CheckCircle: (props) => <SvgIcon {...props}><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></SvgIcon>,
    Clock: (props) => <SvgIcon {...props}><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></SvgIcon>,
    Search: (props) => <SvgIcon {...props}><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></SvgIcon>,
    GitBranch: (props) => <SvgIcon {...props}><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></SvgIcon>,
    RefreshCw: (props) => <SvgIcon {...props}><path d="M21 2v6h-6"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M3 22v-6h6"/><path d="M21 12a9 9 0 0 1-15 6.7L3 16"/></SvgIcon>,
    Book: (props) => <SvgIcon {...props}><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/></SvgIcon>,
    Music: (props) => <SvgIcon {...props}><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></SvgIcon>,
    Play: (props) => <SvgIcon {...props}><polygon points="5 3 19 12 5 21 5 3"/></SvgIcon>,
    Pause: (props) => <SvgIcon {...props}><rect x="6" y="4" width="4" height="16"/><rect x="14" y="4" width="4" height="16"/></SvgIcon>,
    Mic: (props) => <SvgIcon {...props}><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" y1="19" x2="12" y2="23"/><line x1="8" y1="23" x2="16" y2="23"/></SvgIcon>,
    Table: (props) => <SvgIcon {...props}><rect width="18" height="18" x="3" y="3" rx="2" ry="2"/><line x1="3" x2="21" y1="9" y2="9"/><line x1="3" x2="21" y1="15" y2="15"/><line x1="12" x2="12" y1="3" y2="21"/></SvgIcon>
};

const Icon = ({ name, className }) => {
    const IconComponent = Icons[name] || Icons.Zap;
    return <IconComponent className={className} />;
};

// --- Helper: Image Resolver ---
const resolveImage = (path) => {
    if (!path) return null;
    if (path.startsWith('http')) return path;
    // 假设 assets 文件夹在根目录
    return `${window.PPT_DATA.config.assetsBase}${path}`;
};

// --- Modal Component ---
const Modal = ({ isOpen, onClose, item }) => {
    if (!isOpen || !item) return null;
    
    const imgSrc = resolveImage(item.detailImage);
    const isVideo = imgSrc && imgSrc.toLowerCase().endsWith('.mp4');

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 modal-overlay animate-fade-in" onClick={onClose}>
            <div className="bg-white rounded-2xl shadow-2xl max-w-6xl w-full p-8 relative" onClick={e => e.stopPropagation()}>
                <button onClick={onClose} className="absolute top-4 right-4 text-slate-400 hover:text-slate-600">
                    <Icon name="X" className="w-6 h-6" />
                </button>
                
                <div className="flex items-center space-x-3 mb-6">
                    <div className="bg-primary-light p-3 rounded-xl">
                        <Icon name={item.icon} className="w-6 h-6 text-primary" />
                    </div>
                    <div>
                        <h3 className="text-2xl font-bold text-slate-800">{item.title}</h3>
                        <span className="text-xs font-bold uppercase tracking-wider text-primary bg-primary-light px-2 py-1 rounded-full">{item.category}</span>
                    </div>
                </div>

                {/* Detail Image Area */}
                <div className="w-full aspect-video bg-slate-50 rounded-xl mb-6 flex items-center justify-center border border-slate-100 relative overflow-hidden group">
                     {imgSrc ? (
                        isVideo ? (
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
                                        const placeholder = e.target.parentElement.querySelector('.fallback-placeholder');
                                        if(placeholder) {
                                            placeholder.style.display = 'flex';
                                            placeholder.innerHTML = '<div class="text-center"><span class="text-2xl">⚠️</span><br/><span class="text-xs text-red-500 mt-1">资源加载失败</span><br/><span class="text-[10px] text-slate-400">请检查文件名大小写</span></div>';
                                        }
                                    }}
                                />
                            </>
                        ) : (
                            <img src={imgSrc} alt={item.title} className="w-full h-full object-cover" onError={(e) => {
                                e.target.onerror = null;
                                e.target.style.display = 'none';
                                e.target.nextSibling.style.display = 'flex';
                            }}/>
                        )
                     ) : null}
                     
                     {/* Fallback Placeholder */}
                     <div className="fallback-placeholder absolute inset-0 flex-col items-center justify-center text-slate-400 text-sm font-medium" style={{display: imgSrc ? 'none' : 'flex'}}>
                        <Icon name="Image" className="w-8 h-8 mb-2 opacity-50" />
                        {item.detailImageText || 'No Image Asset'}
                     </div>
                </div>

                <p className="text-slate-600 leading-relaxed text-lg">
                    {item.detailDesc || item.desc}
                </p>
            </div>
        </div>
    );
};

// 挂载到全局
window.Icon = Icon;
window.Modal = Modal;
window.resolveImage = resolveImage;

// --- Hook: Draggable Scroll ---
const useDraggableScroll = (ref) => {
    const [isDragging, setIsDragging] = useState(false);
    const [startX, setStartX] = useState(0);
    const [scrollLeft, setScrollLeft] = useState(0);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;
        // 滚轮横向滚动映射
        const onWheel = (e) => {
            // 优先响应水平滚动 (触摸板)，如果没有则映射垂直滚动 (鼠标滚轮)
            const delta = Math.abs(e.deltaX) > Math.abs(e.deltaY) ? e.deltaX : e.deltaY;
            if (delta !== 0) {
                el.scrollLeft += delta;
                e.preventDefault();
            }
        };
        el.addEventListener('wheel', onWheel, { passive: false });
        return () => el.removeEventListener('wheel', onWheel);
    }, [ref]);

    const events = {
        onMouseDown: (e) => {
            setIsDragging(true);
            setStartX(e.pageX - ref.current.offsetLeft);
            setScrollLeft(ref.current.scrollLeft);
            ref.current.style.cursor = 'grabbing';
        },
        onMouseUp: () => { setIsDragging(false); if(ref.current) ref.current.style.cursor = 'grab'; },
        onMouseLeave: () => { setIsDragging(false); if(ref.current) ref.current.style.cursor = 'grab'; },
        onMouseMove: (e) => {
            if (!isDragging) return;
            e.preventDefault();
            const x = e.pageX - ref.current.offsetLeft;
            const walk = (x - startX) * 1.5; // 1.5倍速滑动
            ref.current.scrollLeft = scrollLeft - walk;
        }
    };
    return events;
};
window.useDraggableScroll = useDraggableScroll;