const { useState, useEffect } = React;

const App = () => {
    const [currentSlide, setCurrentSlide] = useState(0);
    const slides = window.PPT_DATA.slides;

    const nextSlide = () => {
        if (currentSlide < slides.length - 1) setCurrentSlide(curr => curr + 1);
    };

    const prevSlide = () => {
        if (currentSlide > 0) setCurrentSlide(curr => curr - 1);
    };

    useEffect(() => {
        const handleKeyDown = (e) => {
            if (e.key === 'ArrowRight' || e.key === ' ') nextSlide();
            if (e.key === 'ArrowLeft') prevSlide();
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [currentSlide]);

    const renderSlideContent = () => {
        const slide = slides[currentSlide];
        switch (slide.type) {
            case 'cover': return <window.SlideCover slide={slide} />;
            case 'timeline': return <window.SlideTimeline slide={slide} />;
            case 'comparison': return <window.SlideComparison slide={slide} />;
            case 'grid': return <window.SlideGrid slide={slide} />;
            case 'showcase': return <window.SlideShowcase slide={slide} />;
            case 'summary': return <window.SlideSummary slide={slide} />;
            default: return <div className="flex items-center justify-center h-full">Slide content missing</div>;
        }
    };

    return (
        <div className="relative w-screen h-screen overflow-hidden selection:bg-primary selection:text-white">
            <main className="relative z-10 w-full h-full p-4 md:p-8 flex flex-col">
                <div className="flex-1 w-full h-full relative flex items-center justify-center">
                    <div key={currentSlide} className="w-full h-full slide-enter-active">
                        {renderSlideContent()}
                    </div>
                </div>
                <div className="h-16 flex items-center justify-between px-8 max-w-[95vw] mx-auto w-full fixed bottom-4 left-0 right-0 z-40 pointer-events-none">
                    <div className="text-slate-400 text-sm font-mono pointer-events-auto bg-white/80 backdrop-blur px-4 py-2 rounded-full shadow-sm border border-slate-200">
                        {currentSlide + 1} / {slides.length}
                    </div>
                    <div className="flex gap-4 pointer-events-auto">
                        <button onClick={prevSlide} disabled={currentSlide === 0} className="p-3 rounded-full bg-white text-slate-600 shadow-lg border border-slate-100 hover:bg-slate-50 disabled:opacity-50 disabled:shadow-none transition-all hover:-translate-y-1">
                            <window.Icon name="ChevronLeft" />
                        </button>
                        <button onClick={nextSlide} disabled={currentSlide === slides.length - 1} className="p-3 rounded-full bg-primary text-white shadow-lg shadow-primary/30 hover:bg-primary-dark disabled:opacity-50 disabled:shadow-none transition-all hover:-translate-y-1">
                            <window.Icon name="ChevronRight" />
                        </button>
                    </div>
                </div>
            </main>
        </div>
    );
};

const root = ReactDOM.createRoot(document.getElementById('root'));
root.render(<App />);