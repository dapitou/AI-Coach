/**
 * PRD Dynamic Annotation Module
 * Automatically draws connection lines and explanatory text based on PRD specs.
 */
window.PRD = {
    layer: null,
    svg: null,
    notesContainer: null,
    resizeTimeout: null,
    enabled: false,
    
    // PRD Specification Mapping
    specs: {
        'view-home': [
            { sel: '.siri-container', title: '虚拟形象', text: 'Siri-like 动效常驻。状态映射：待机(呼吸)、聆听(扩散)、思考(闪烁)、表达(波形)。', side: 'left' },
            { sel: '#home-start-btn', title: '启动触发', text: '中心化按钮。展示麦克风图标、引导文案及版本号(V27.0)。点击请求权限并进入对话。', side: 'right' },
            { sel: '.action-buttons .big-btn:nth-child(1)', title: '快捷入口(课)', text: '“给我一节课”入口，直接触发单课生成流程。', side: 'left' },
            { sel: '.action-buttons .big-btn:nth-child(2)', title: '快捷入口(计划)', text: '“给我一份计划”入口，触发周期计划生成流程。', side: 'right' },
            { sel: '#profile-card .info-item:nth-child(1)', title: '档案-目标', text: '展示主要目标(增肌/减脂/健康)。数据源：用户档案。', side: 'left' },
            { sel: '#profile-card .info-item:nth-child(2)', title: '档案-等级', text: '展示运动等级(L1-L5)。影响推荐强度与容量系数。', side: 'right' },
            { sel: '#profile-card .info-item:nth-child(3)', title: '档案-体重', text: '展示当前体重。用于计算BMI及卡路里消耗。', side: 'left' },
            { sel: '#profile-card .info-item:nth-child(4)', title: '疲劳度模型', text: '1-10分映射：1-2超量恢复；3-4完全恢复；5-6功能性；7-8非功能性；9-10过度训练。', side: 'right' }
        ],
        'view-chat': [
            { sel: '.chat-header', title: '沉浸式导航', text: '顶部展示 AI 状态指示灯与当前会话情境，支持随时退出。', side: 'left' },
            { sel: '.chat-container', title: '课程生成流程', text: '模拟真人教练问询流程。步骤：类型->部位(疲劳拦截)->时长(20-90min)。支持模糊意图识别。', side: 'right' },
            { sel: '.input-area .mic-btn', title: '语音交互', text: '点击唤醒/停止。支持实时语音转文字(STT)与波形反馈。', side: 'left' },
            { sel: '.input-area', title: '多模态输入', text: '支持点击芯片选择，也支持语音模糊匹配(如“练胸”=“胸部”)。', side: 'right' }
        ],
        'view-reasoning': [
            { sel: '.reasoning-center', title: '推理展示', text: '透明化 AI 决策过程：读取档案 -> 解析需求 -> 风控扫描(避开伤病) -> 策略匹配(加载范式) -> 构建课程。', side: 'right' }
        ],
        'view-result': (el) => {
            if (el.classList.contains('plan-mode')) {
                return [
                    { sel: '.plan-hero-title', title: '计划标题', text: '规则：{等级}{目标}计划。如“中级增肌计划”。', side: 'left' },
                    { sel: '.plan-hero-tags', title: '核心标签', text: '展示：等级 | 周期(周) | 频率(天/周)。', side: 'right' },
                    { sel: '.plan-hero-intro', title: '计划介绍', text: '展示适应人群、解决痛点及预期效果。', side: 'left' },
                    { sel: '#plan-weight-chart-container', title: '体重预测', text: 'SVG折线图。节点基于阶段权重插值(突破期变化大)。点击Tab联动高亮。', side: 'right' },
                    { sel: '.plan-flow-container', title: '阶段流程', text: 'Tab切换阶段(适应/进阶/突破/减载)。显示周数与强度系数。', side: 'left' },
                    { sel: '.plan-week-row', title: '周视图', text: '展示当前选中阶段的每日安排(训练/休息)。', side: 'right' },
                    { sel: '.plan-day-cell.training', title: '训练日卡片', text: '标题：{部位}{阶段后缀}。点击下钻进入课程详情页。', side: 'left' }
                ];
            } else {
                return [
                    { sel: '#res-title', title: '课程标题', text: '规则：{类型}训练 或 W{周}|{部位}训练。', side: 'left' },
                    { sel: '#res-sub', title: '副标题', text: '展示：时长 | 部位 | 难度。', side: 'right' },
                    { sel: '#unit-switch', title: '单位切换', text: '切换 KG/LBS。全局数值自动换算。', side: 'left' },
                    { sel: '#st-time', title: '统计-时长', text: '所有动作(单组耗时+休息)总和。', side: 'right' },
                    { sel: '#st-count', title: '统计-动作', text: '当前课程包含的动作总数。', side: 'left' },
                    { sel: '#st-vol', title: '统计-容量', text: '所有动作的组数之和。', side: 'right' },
                    { sel: '#st-cal', title: '统计-消耗', text: '公式：0.075 * 体重 * 时长。', side: 'left' },
                    { sel: '#res-phase-tabs', title: '环节导航', text: '吸附式Tab。切换[热身]/[主训]/[放松]。默认选中主训。', side: 'right' },
                    { sel: '.smart-switch', title: '智能推荐', text: '开关。开启: AI接管策略(置灰)。关闭: 允许自定义。点击置灰区域触发提示。', side: 'left' },
                    { sel: '.phase-controls-row .control-group:nth-child(2)', title: '负荷策略', text: '下拉选择(恒定/递增/递减)。修改触发全环节重算。', side: 'right' },
                    { sel: '.phase-controls-row .control-group:nth-child(3)', title: '循环模式', text: '下拉选择(常规/循环/超级组)。', side: 'left' },
                    { sel: '.phase-controls-row .control-group:nth-child(4)', title: '组间休息', text: '修改后影响课程总时长计算。', side: 'right' },
                    { sel: '.action-card-pro .ac-header', title: '卡片折叠态', text: '展示缩略图、名称、部位标签、摘要(组x次 重量)。', side: 'left' },
                    { sel: '.action-card-pro .ae-tools', title: '工具栏', text: '支持上移、下移、替换(打开动作库)、展开/折叠。', side: 'right' },
                    { sel: '.action-card-pro .set-list', title: '组详情', text: '展示每一组的序号、步进器、删除按钮。', side: 'left' },
                    { sel: '.action-card-pro .stepper', title: '智能策略联动', text: '当智能推荐关闭时，手动修改某组重量，系统自动检测趋势(如递增)并更新全局策略。', side: 'right' },
                    { sel: '.action-card-pro .ac-footer', title: '底部信息', text: '展示强度百分比(%1RM)、RPE、组间休息。', side: 'left' }
                ];
            }
        },
        'view-library': [
            { sel: '.lib-filters', title: '筛选器', text: '支持按部位、器械、难度等多维度快速过滤动作库。', side: 'left' },
            { sel: '.lib-body', title: '智能排序', text: '基于匹配度(Match Score)降序：新鲜度(+60)、收藏(+50)、难度匹配(+30)。', side: 'right' },
            { sel: '.lib-item', title: '动作列表', text: '展示动作详情与标签。支持多选添加或单选替换。', side: 'left' }
        ],
        'modal-action-detail': [
            { sel: '#detail-tabs', title: '多维展示', text: 'Tab切换：简介、教学、历史。', side: 'right' },
            { sel: '.ad-video', title: '演示视频', text: '自动循环播放动作演示。', side: 'left' },
            { sel: '.muscle-map', title: '肌群映射', text: '展示主动肌、拮抗肌、辅助肌、稳定肌。', side: 'right' },
            { sel: '.ad-section:last-child', title: '历史数据', text: '展示预估 1RM 趋势图及近期训练记录。', side: 'left' }
        ],
        'modal-profile': [
            { sel: '#in-gender', title: '基础数据-性别', text: '影响模版匹配(如男/女分化)及卡路里计算系数。', side: 'left' },
            { sel: '#in-dob', title: '基础数据-生日', text: '用于计算年龄，进而推算最大心率(MHR = 208 - 0.7*Age)。', side: 'right' },
            { sel: '#in-height', title: '基础数据-身高', text: '结合体重计算BMI，评估身体形态。', side: 'left' },
            { sel: '#in-weight', title: '基础数据-体重', text: '计算BMI及运动卡路里消耗的基础参数。', side: 'right' },
            { sel: '#d-bmi', title: '自动计算-BMI', text: 'BMI>28时触发大体重风控，自动剔除高冲击动作。', side: 'left' },
            { sel: '#in-rhr', title: '基础数据-静息心率', text: '评估心肺耐力水平，影响有氧训练强度推荐。', side: 'right' },
            { sel: '#in-fatigue', title: '疲劳度模型', text: '主观评分(1-10)。映射为身体状态值(0-100)。<55分触发降级保护。', side: 'left' },
            
            { sel: '#in-level', title: '偏好-运动等级', text: 'L1-L5。决定推荐强度系数、容量系数及动作难度筛选。', side: 'right' },
            { sel: '#in-duration', title: '偏好-时间预算', text: '每日可用训练时长，作为单课生成的默认时长。', side: 'left' },
            { sel: '#pref-pain', title: '风控-疼痛部位', text: '硬过滤条件。生成课程时强制剔除涉及该部位的动作。', side: 'right' },
            { sel: '#pref-missing', title: '风控-缺失器械', text: '环境约束。筛选动作时自动过滤无法执行的动作。', side: 'left' },
            { sel: '#pref-days', title: '偏好-日程安排', text: '每周训练日。用于周期计划的排课逻辑(如三分化/五分化)。', side: 'right' },
            
            { sel: '#in-goal', title: '目标-主要目标', text: '增肌/减重/健康。决定核心策略矩阵(组数/间歇/强度)。', side: 'left' },
            { sel: '#in-func-goal', title: '目标-功能目标', text: '细化主训内容(如力量/耐力/爆发)。', side: 'right' },
            { sel: '#in-target-weight', title: '目标-目标体重', text: '用于生成体重预测曲线的终点数据。', side: 'left' }
        ],
        'modal-schedule': [
            { sel: '#schedule-days-list', title: '日程安排', text: '设置每周训练日。影响周期计划的周频和每日安排。', side: 'left' }
        ],
        'view-schedule': [
            { sel: '.result-body', title: '加入日程', text: '确认后将生成的计划写入用户日历，并设置提醒。', side: 'right' }
        ]
    },

    init: () => {
        // Create Layer
        const layer = document.createElement('div');
        layer.id = 'prd-layer';
        layer.style.display = 'none';
        layer.innerHTML = `
            <svg class="prd-svg-container"></svg>
            <div class="prd-notes-container"></div>
        `;
        document.body.appendChild(layer);
        
        PRD.layer = layer;
        PRD.svg = layer.querySelector('svg');
        PRD.notesContainer = layer.querySelector('.prd-notes-container');

        // Observe View Changes
        const observer = new MutationObserver(() => {
            if (!PRD.enabled) return;
            // Debounce render
            if (PRD.renderTimeout) clearTimeout(PRD.renderTimeout);
            PRD.renderTimeout = setTimeout(PRD.render, 300); // Increased debounce to reduce flickering
        });

        const app = document.getElementById('app');
        observer.observe(app, { attributes: true, subtree: true, attributeFilter: ['class', 'style'] });
        
        // Initial Render
        // setTimeout(PRD.render, 500);
        
        // Window Resize
        window.addEventListener('resize', () => {
            if (!PRD.enabled) return;
            if (PRD.resizeTimeout) clearTimeout(PRD.resizeTimeout);
            PRD.resizeTimeout = setTimeout(PRD.render, 200);
        });
    },

    toggle: () => {
        PRD.enabled = !PRD.enabled;
        const btn = document.getElementById('prd-toggle-btn');
        if (btn) {
            btn.innerText = `PRD 引注: ${PRD.enabled ? 'ON' : 'OFF'}`;
            if (PRD.enabled) btn.classList.add('active');
            else btn.classList.remove('active');
        }
        if (PRD.layer) PRD.layer.style.display = PRD.enabled ? 'block' : 'none';
        if (PRD.enabled) PRD.render();
    },

    render: () => {
        if (!PRD.enabled) return;
        // Clear previous
        PRD.notesContainer.innerHTML = '';
        PRD.svg.innerHTML = '';

        // Find active view
        let activeView = document.querySelector('.view.active');
        let viewId = activeView ? activeView.id : null;

        // Check for active modal which overlays the view
        const activeModal = document.querySelector('.modal.active');
        if (activeModal) {
            viewId = activeModal.id;
            // activeView remains as background context, but we will target inside modal
        }

        if (!viewId) return;

        let specs = PRD.specs[viewId];
        
        if (typeof specs === 'function') {
            specs = specs(activeView);
        }

        if (!specs) return;

        const appRect = document.getElementById('app').getBoundingClientRect();
        const marginX = 20;

        // Track occupied vertical space to prevent overlap (Simple collision avoidance)
        let leftY = 20;
        let rightY = 20;
        const gap = 15;
        
        // Reset Y if view changed significantly or just keep accumulating? 
        // Better to sort by target Y position first to stack them nicely.
        
        // Collect all items first
        const items = [];

        specs.forEach((spec, index) => {
            // If in modal mode, search within modal first, fallback to document
            const target = activeModal ? activeModal.querySelector(spec.sel) : activeView.querySelector(spec.sel);
            if (!target || target.offsetParent === null || target.getBoundingClientRect().height === 0) return; // Skip if not visible
            const targetRect = target.getBoundingClientRect();
            
            // Create Note
            const note = document.createElement('div');
            note.className = 'prd-note';
            note.innerHTML = `<h4>${spec.title}</h4>${spec.text}`;
            PRD.notesContainer.appendChild(note);
            
            items.push({ spec, target, targetRect, note });
        });

        // Sort items by target vertical position
        items.sort((a, b) => a.targetRect.top - b.targetRect.top);

        items.forEach(item => {
            const { spec, targetRect, note } = item;
            const noteHeight = note.offsetHeight;
            
            // Calculate Position
            let noteX, noteY;
            const noteWidth = 260;

            if (spec.side === 'left') {
                noteX = appRect.left - noteWidth - marginX;
                // Ideal Y is centered on target, but must be below previous note
                let idealY = targetRect.top + (targetRect.height / 2) - (noteHeight / 2);
                noteY = Math.max(idealY, leftY);
                leftY = noteY + noteHeight + gap;
            } else {
                noteX = appRect.right + marginX;
                let idealY = targetRect.top + (targetRect.height / 2) - (noteHeight / 2);
                noteY = Math.max(idealY, rightY);
                rightY = noteY + noteHeight + gap;
            }
            
            // Clamp to screen top
            noteY = Math.max(10, noteY);

            // Apply position
            
            note.style.left = `${noteX}px`;
            note.style.top = `${noteY}px`;

            // Draw Polyline (Elbow Connector) - 折线
            // Start: Note edge closest to app
            // End: Target edge closest to note
            const startX = spec.side === 'left' ? (noteX + noteWidth) : noteX;
            const startY = noteY + 40; // Approx middle of note header
            
            const endX = spec.side === 'left' ? targetRect.left : targetRect.right;
            const endY = targetRect.top + (targetRect.height / 2);

            // Elbow points
            const midX = (startX + endX) / 2;

            const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
            // M start -> L midX,startY -> L midX,endY -> L end
            path.setAttribute("d", `M ${startX} ${startY} L ${midX} ${startY} L ${midX} ${endY} L ${endX} ${endY}`);
            path.setAttribute("class", "prd-line");
            PRD.svg.appendChild(path);

            // Add Dot at target
            const dot = document.createElementNS("http://www.w3.org/2000/svg", "circle");
            dot.setAttribute("cx", endX);
            dot.setAttribute("cy", endY);
            dot.setAttribute("r", "3");
            dot.setAttribute("class", "prd-dot");
            PRD.svg.appendChild(dot);

            // Trigger animation
            requestAnimationFrame(() => note.classList.add('visible'));
        });
    }
};

// Auto-init
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', PRD.init);
} else {
    PRD.init();
}
