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
            { sel: '.siri-container', title: 'P1.1 启动触发 (Start Trigger)', text: '状态机：待机(呼吸) -> 监听(扩散) -> 思考(闪烁) -> 表达(波形)。\n交互：点击或语音唤醒。', side: 'left' },
            { sel: '#home-start-btn', title: 'P1.1 启动按钮 (Central Trigger)', text: 'UI：麦克风图标 + 引导文案 + 版本号(V27.0)。\n交互：点击请求权限 -> 视图切换 -> 语音初始化。', side: 'right' },
            { sel: '.action-buttons .big-btn:nth-child(1)', title: 'P1.2 快捷入口 (Quick Actions)', text: '功能：给我一节课。\n逻辑：初始化单课流程 -> 跳转对话页。\n前置：校验功能目标。', side: 'left' },
            { sel: '.action-buttons .big-btn:nth-child(2)', title: 'P1.2 快捷入口 (Quick Actions)', text: '功能：给我一份计划。\n逻辑：初始化计划流程 -> 跳转对话页。\n前置：校验功能目标。', side: 'right' },
            { sel: '.custom-template-link', title: 'P1.2 自定义入口', text: '功能：自定义课程模板。\n逻辑：跳过问询 -> 进入结果页(预置空模板)。', side: 'left' },
            { sel: '#profile-card', title: 'P1.3 运动档案卡片 (Profile Card)', text: '展示：目标、等级、体重、疲劳度。\n状态映射：疲劳度(1-10) -> 状态标签/颜色。\n交互：点击更新唤起模态框。', side: 'right' },
            { sel: '.edit-btn', title: 'P1.3 更新档案 (Update)', text: '交互：点击唤起档案编辑模态框。', side: 'left' }
        ],
        'view-chat': [
            { sel: '.chat-header', title: 'P2.1 顶部导航 (Chat Header)', text: '功能：退出交互、状态指示(呼吸灯)。\n逻辑：点击退出中断会话。', side: 'left' },
            { sel: '.chat-back', title: 'P2.1 退出 (Exit)', text: '交互：点击中断会话返回首页。', side: 'right' },
            { sel: '.chat-container', title: 'P2.1 对话流容器 (Chat Stream)', text: '交互：历史记录滚动、自动对齐(Auto-Align)。\n内容：AI提问(打字机效) + 用户回答(气泡)。', side: 'right' },
            { sel: '.chat-summary', title: 'P2.1 意图摘要 (Summary)', text: '数据：实时展示已确认的参数标签。', side: 'left' },
            { sel: '.input-area .mic-btn', title: 'P2.2 语音输入 (Voice Input)', text: '交互：点击切换 监听/停止。\n反馈：高亮光环 + 脉冲动效。', side: 'left' },
            { sel: '.input-area', title: 'P2.2 多模态输入 (Multimodal Input)', text: '组件：智能芯片(单选/多选)、数值滑块(拖动)。\n逻辑：语音优先，触控兜底，实时互通。', side: 'right' }
        ],
        'view-reasoning': [
            { sel: '.reasoning-center', title: 'P2.3 推理可视化 (Reasoning)', text: '逻辑：读取档案 -> 解析需求 -> 风控扫描 -> 策略匹配 -> 构建课程。\n表现：逐行展示决策日志。', side: 'right' }
        ],
        'view-result': (el) => {
            // Fix: Check visibility of plan list container to distinguish modes
            const isPlanMode = el.querySelector('#res-plan-list') && el.querySelector('#res-plan-list').style.display !== 'none';
            
            if (isPlanMode) {
                return [
                    { sel: '#btn-close-result', title: 'P3.2 关闭 (Close)', text: '交互：点击返回首页。', side: 'left' },
                    { sel: '.plan-hero', title: 'P3.2 计划概览 (Plan Hero)', text: '数据：标题({等级}{目标}计划)、标签(周期/频率)、介绍文案。\n来源：计划生成逻辑。', side: 'left' },
                    { sel: '#plan-weight-chart-container', title: 'P3.2 体重预测图 (Weight Chart)', text: '可视化：SVG折线图。\n逻辑：基于阶段权重插值，点击Tab联动高亮。', side: 'right' },
                    { sel: '.plan-flow-container', title: 'P3.2 阶段导航 (Phase Flow)', text: '结构：适应期 -> 进阶期 -> 突破期 -> 减载期。\n信息：名称、周数、强度系数。', side: 'left' },
                    { sel: '.plan-week-row', title: 'P3.2 训练周历 (Weekly Calendar)', text: '展示：每日安排(训练/休息)。\n交互：点击训练日下钻至课程详情。', side: 'right' },
                    { sel: '#btn-main-action', title: 'P3.2 加入日程 (Join)', text: '交互：点击将计划写入用户日程。', side: 'right' }
                ];
            } else {
                return [
                    { sel: '#btn-close-result', title: 'P3.1 关闭 (Close)', text: '交互：点击返回首页。', side: 'left' },
                    { sel: '#btn-back-plan', title: 'P3.1 返回计划 (Back)', text: '交互：返回计划详情页。', side: 'left' },
                    { sel: '.plan-hero-title', title: 'P3.1 课程概览 (Course Hero)', text: '数据：课程名称、难度、时长、部位。\n来源：课程生成逻辑。', side: 'left' },
                    { sel: '#unit-switch', title: 'P3.1 单位切换', text: '交互：KG/LBS 切换。\n逻辑：全局数值实时换算 (1kg ≈ 2.2lbs)。', side: 'right' },
                    { sel: '#res-stats', title: 'P3.1 数据统计 (Stats Bar)', text: '指标：时长(min)、动作(个)、容量(组)、消耗(kcal)。\n公式：消耗 = 0.075 * 体重 * 时长。', side: 'left' },
                    { sel: '#res-phase-tabs', title: 'P3.1 环节导航 (Phase Nav)', text: '结构：热身 | 主训 | 放松。\n交互：吸附式Tab，点击切换动作列表。', side: 'right' },
                    { sel: '#course-phase-controls', title: 'P3.1 微调控制台 (Fine-Tuning)', text: '参数：负荷策略(推荐/恒定/递增/递减)、循环模式(常规/循环)、休息时间。\n逻辑：修改触发全环节重算。', side: 'left' },
                    { sel: '.ad-add-btn', title: 'P3.1 添加动作 (Add Action)', text: '交互：点击打开动作库添加新动作。', side: 'right' },
                    { sel: '.action-card-pro', title: 'P3.1 动作卡片 (Action Card)', text: '信息：缩略图、名称、部位、组数x负荷。\n交互：展开/折叠、排序、替换、删除。', side: 'right' },
                    { sel: '.stepper', title: 'P3.1 负荷微调 (Stepper)', text: '交互：点击+/-或输入数值调整负荷。', side: 'left' },
                    { sel: '.add-set-btn', title: 'P3.1 增加组 (Add Set)', text: '交互：点击为当前动作增加一组。', side: 'right' },
                    { sel: '#btn-main-action', title: 'P3.1 开始训练 (Start)', text: '交互：点击进入训练执行页面。', side: 'right' }
                ];
            }
        },
        'view-library': [
            { sel: '.chat-back', title: 'P5.1 取消 (Cancel)', text: '交互：点击返回上一页。', side: 'left' },
            { sel: '.result-header div[onclick*="confirmReplace"]', title: 'P5.1 确认 (Confirm)', text: '交互：点击将选中动作回填至课程。', side: 'right' },
            { sel: '.lib-filters', title: 'P5.1 筛选与检索 (Filter & Search)', text: '维度：部位(快捷Tab)、器械、难度、冲击(高级筛选)。\n逻辑：维度间AND，维度内OR。', side: 'left' },
            { sel: '.lib-filter-toggle', title: 'P5.1 高级筛选 (Advanced)', text: '交互：展开/收起更多筛选维度。', side: 'right' },
            { sel: '.lib-body', title: 'P5.1 动作列表 (Action List)', text: '排序：匹配度降序(新鲜度/收藏/难度匹配)。\n展示：分组聚合(按功能)。', side: 'right' },
            { sel: '.lib-group-title', title: 'P5.1 分组 (Grouping)', text: '逻辑：按动作功能(如增肌/力量)聚合展示。', side: 'left' },
            { sel: '.lib-item', title: 'P5.1 动作单元 (Action Item)', text: '信息：缩略图、名称、部位、肌群、器械、难度。\n交互：点击查看详情。', side: 'left' },
            { sel: '.lib-check-area', title: 'P5.1 选择 (Select)', text: '交互：多选添加 / 单选替换。', side: 'right' }
        ],
        'modal-action-detail': [
            { sel: '.modal-header div[onclick*="closeActionDetail"]', title: 'P5.2 关闭 (Close)', text: '交互：点击关闭详情弹窗。', side: 'left' },
            { sel: '.ad-add-btn', title: 'P5.2 添加动作 (Add)', text: '交互：将当前动作加入课程。', side: 'right' },
            { sel: '#detail-tabs', title: 'P5.2 详情Tab', text: '结构：简介、教学、历史。\n交互：切换内容视图。', side: 'right' },
            { sel: '.ad-video', title: 'P5.2 视频演示', text: '内容：标准动作循环播放。\n覆盖：教学Tab播放详细讲解。', side: 'left' },
            { sel: '.ad-tags', title: 'P5.2 标签 (Tags)', text: '数据：部位、构造、难度、镜像属性。', side: 'right' },
            
            // Intro Tab
            { sel: '#ad-sec-basic', title: 'P5.2 基础属性 (Attributes)', text: '数据：器械、冲击等级、训练范式。', side: 'left' },
            { sel: '#ad-sec-muscle', title: 'P5.2 肌群映射 (Muscle Map)', text: '数据：主动肌(高亮)、拮抗肌、辅助肌、稳定肌。\n来源：动作属性定义。', side: 'right' },
            { sel: '#ad-sec-desc', title: 'P5.2 动作说明 (Description)', text: '数据：动作要领与功效描述。', side: 'left' },
            
            // Teach Tab
            { sel: '#ad-sec-points', title: 'P5.2 动作要点 (Points)', text: '数据：关键动作步骤与注意事项。', side: 'left' },
            { sel: '#ad-sec-errors', title: 'P5.2 常见错误 (Errors)', text: '数据：易错点与纠正建议。', side: 'right' },
            
            // History Tab
            { sel: '#ad-sec-1rm', title: 'P5.2 1RM趋势 (Trend)', text: '可视化：预估1RM变化曲线。', side: 'left' },
            { sel: '#ad-sec-recent', title: 'P5.2 近期变化 (Changes)', text: '数据：近1周/1月/3月的能力涨跌幅。', side: 'right' },
            { sel: '#ad-sec-records', title: 'P5.2 训练记录 (Records)', text: '列表：历史训练日期与负荷记录。', side: 'left' }
        ],
        'modal-profile': [
            { sel: '.modal-header div[onclick*="saveProfile"]', title: '档案: 保存 (Save)', text: '交互：点击保存修改并重新计算推荐。', side: 'right' },
            { sel: '.tabs', title: '档案: 分类Tab', text: '结构：基础、偏好、目标。\n交互：切换表单内容。', side: 'left' },
            { sel: '#in-gender', title: '档案: 性别', text: '属性：男/女 (单选)。\n用途：计算基础代谢、推荐算法修正。', side: 'left' },
            { sel: '#in-dob', title: '档案: 生日', text: '属性：YYYY-MM-DD。\n用途：计算年龄 -> 最大心率(MHR)。', side: 'right' },
            { sel: '#in-height', title: '档案: 身高', text: '属性：100-250cm (滑动)。\n用途：计算BMI。', side: 'left' },
            { sel: '#in-weight', title: '档案: 体重', text: '属性：30-150kg (滑动)。\n用途：计算BMI、卡路里消耗。', side: 'right' },
            { sel: '#d-bmi', title: '档案: BMI', text: '属性：自动计算。\n逻辑：体重/身高²。>28触发高冲击规避。', side: 'left' },
            { sel: '#in-rhr', title: '档案: 静息心率', text: '属性：自动更新/手动。\n用途：评估心肺能力。', side: 'right' },
            { sel: '#d-mhr', title: '档案: 最大心率', text: '属性：自动计算。\n公式：208 - 0.7*年龄。用于定义强度区间。', side: 'left' },
            { sel: '#in-fatigue', title: '档案: 主观疲劳度', text: '属性：1-10 (滑动)。\n用途：修正当日训练负荷。<55分触发降级。', side: 'left' },
            
            { sel: '#in-level', title: '档案: 运动等级', text: '属性：L1-L5 (单选)。\n用途：决定推荐强度、容量系数、动作难度。', side: 'right' },
            { sel: '#in-duration', title: '档案: 每日运动时长', text: '属性：20-60min (滑动)。\n用途：生成课程的默认时长。', side: 'left' },
            { sel: '#pref-pain', title: '档案: 疼痛部位', text: '属性：多选。\n用途：动作硬性剔除。', side: 'right' },
            { sel: '#pref-missing', title: '档案: 缺失配件', text: '属性：多选。\n用途：动作硬性剔除。', side: 'left' },
            { sel: '#pref-days', title: '档案: 每周训练日', text: '属性：周一至周日 (多选)。\n用途：计划日程配置。', side: 'right' },
            { sel: '#in-style', title: '档案: 训练风格', text: '属性：传统/多变/激进 (单选)。\n用途：影响课程编排风格。', side: 'left' },
            
            { sel: '#in-goal', title: '档案: 主要目标', text: '属性：增肌/减重/健康 (单选)。\n用途：宏观策略矩阵匹配。', side: 'left' },
            { sel: '#in-func-goal', title: '档案: 功能目标', text: '属性：力量/耐力/爆发... (单选)。\n用途：微观生理目标匹配。', side: 'right' },
            { sel: '#in-body-type', title: '档案: 目标体型', text: '属性：单选。\n用途：计划推荐参考。', side: 'left' },
            { sel: '#in-target-weight', title: '档案: 目标体重', text: '属性：30-150kg (滑动)。\n用途：生成体重预测曲线。', side: 'right' }
        ],
        'modal-schedule': [
            { sel: '.modal-header div[onclick*="confirmSchedule"]', title: '计划: 确认 (Confirm)', text: '交互：确认训练日选择。', side: 'right' },
            { sel: '#schedule-days-list', title: '计划: 训练日确认', text: '交互：点击切换 训练/休息。\n逻辑：至少选择1天。', side: 'left' }
        ],
        'view-schedule': [
            { sel: '.chat-back', title: '计划: 关闭 (Close)', text: '交互：点击返回首页。', side: 'left' },
            { sel: '.result-body', title: '计划: 日程写入', text: '结果：将生成的计划写入用户日历。\n反馈：设置提醒。', side: 'right' }
        ],
        'view-workout': [
            { sel: '.wk-close-btn', title: 'P4.1 结束 (End)', text: '交互：点击弹出确认框结束训练。', side: 'left' },
            { sel: '.wk-progress-container', title: 'P4.1 进度 (Progress)', text: '数据：展示当前训练进度百分比。', side: 'right' },
            { sel: '.wk-dashboard', title: 'P4.1 仪表盘 (Dashboard)', text: '可视化：实时功率(W)、行程曲线(cm)、重量表盘(kg)。\n交互：拖动表盘调整重量。', side: 'left' },
            { sel: '.wk-dial-wrapper', title: 'P4.1 重量表盘 (Dial)', text: '交互：拖动圆环快速调节重量。', side: 'left' },
            { sel: '.wk-dial-controls', title: 'P4.1 重量调节 (Weight)', text: '交互：点击+/-微调当前组重量。', side: 'right' },
            { sel: '.wk-video-area', title: 'P4.2 视频区 (Video Area)', text: '内容：动作演示循环播放。\n覆盖层：倒计时、休息中、暂停。', side: 'right' },
            { sel: '.wk-action-list-overlay', title: 'P4.3 动作列表 (Action List)', text: '功能：查看进度、快速跳转、替换动作。\n交互：点击展开/收起。', side: 'left' },
            { sel: '.sim-controls', title: 'P4.4 模拟控制 (Sim)', text: '交互：开发调试用，模拟硬件数据输入。', side: 'right' }
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
        const appCenterX = appRect.left + appRect.width / 2;
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

            // Dynamic Side Calculation: Nearest Side
            const targetCenterX = targetRect.left + targetRect.width / 2;
            const side = targetCenterX < appCenterX ? 'left' : 'right';

            if (side === 'left') {
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
            const startX = side === 'left' ? (noteX + noteWidth) : noteX;
            const startY = noteY + 40; // Approx middle of note header
            
            const endX = side === 'left' ? targetRect.left : targetRect.right;
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
