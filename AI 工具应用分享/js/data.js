// PPT 内容数据配置
// 图片资源请放入 assets 文件夹，并在此处引用路径

window.PPT_DATA = {
    config: {
        // 全局配置
        version: '2.6',
        assetsBase: 'assets/', // 资源根目录
        defaultPlaceholder: 'https://placehold.co/600x400/f1f5f9/94a3b8?text=Image+Asset',
        logo: 'AEKE.png'
    },
    slides: [
        {
            id: 'intro',
            type: 'cover',
            title: '2025 AI工具应用分享',
            subtitle: '从“提效”到“创造”：产品经理的 AI 进化之路',
            presenter: '卢凯晨（产品经理）',
            date: '2025.01.16'
        },
        {
            id: 'timeline',
            type: 'timeline',
            title: '时代背景 - AI的进化',
            subtitle: '从“技术爆发”到“智能助手”落地',
            events: [
                { year: '2021 Q1', title: 'DALL-E 诞生', desc: 'AI 第一次学会了“听话画图”，虽然画得还很粗糙，但创意不再受画笔限制。', icon: 'Image' },
                { year: '2021 Q2', title: 'Copilot 预览', desc: '程序员有了个“AI 徒弟”，它能自动补全代码，写代码像打字联想一样快。', icon: 'Code2' },
                { year: '2021 Q3', title: 'AlphaFold 2', desc: 'AI 破解了生物学的“达芬奇密码”（蛋白质结构），帮科学家省了几十年的实验时间。', icon: 'Zap' },
                { year: '2021 Q4', title: '大模型基石', desc: '科学家发现“大力出奇迹”：只要模型做得足够大，喂的数据足够多，AI 就会变聪明。', icon: 'BarChart3' },
                { year: '2022 Q1', title: 'InstructGPT', desc: 'AI 终于能“听懂人话”了，不再是胡言乱语，而是按照你的指令去办事。', icon: 'MessageSquare' },
                { year: '2022 Q2', title: 'DALL-E 2', desc: 'AI 画图达到了照片级逼真，设计师惊呼“饭碗不保”，生成式 AI 火了。', icon: 'Image' },
                { year: '2022 Q3', title: 'Stable Diffusion', desc: 'AI 绘画技术免费公开，普通人用家里电脑也能画出大师级作品。', icon: 'Layout' },
                { year: '2022 Q4', title: 'ChatGPT', desc: 'AI 的“iPhone 时刻”！人人都能和一个博学的大脑自由聊天，AI 从实验室走进了千家万户。', icon: 'MessageSquare', highlight: true },
                { year: '2023 Q1', title: 'GPT-4', desc: 'AI 智商大爆发，考律师、考医生都能拿高分，逻辑推理能力接近人类专家。', icon: 'Brain', highlight: true },
                { year: '2023 Q2', title: 'AutoGPT', desc: 'AI 开始尝试“自己给自己派活”，你给个目标，它自己拆解步骤去执行。', icon: 'Rocket' },
                { year: '2023 Q3', title: 'Llama 2', desc: '大模型界的“安卓”来了，企业可以免费用开源模型，造自己的专属 AI。', icon: 'Users' },
                { year: '2023 Q4', title: 'Gemini 1.0', desc: 'AI 进化成“全能战士”，能同时看视频、听录音、读文章，像人一样感知世界。', icon: 'Zap' },
                { year: '2024 Q1', title: 'Sora 震撼', desc: 'AI 懂了物理规律，能生成 60 秒电影级视频，虽然还没公测，但震撼了整个影视圈。', icon: 'MonitorPlay', highlight: true },
                { year: '2024 Q2', title: 'GPT-4o', desc: 'AI 变得像电影《Her》里的萨曼莎，能听出你的情绪，毫秒级回应，聊天更有“人味”。', icon: 'MessageSquare' },
                { year: '2024 Q3', title: 'o1-preview', desc: 'AI 学会了“深思熟虑”，遇到难题不急着回答，先打草稿思考，数学代码能力暴涨。', icon: 'Brain' },
                { year: '2024 Q4', title: 'Computer Use', desc: 'AI 接管了鼠标键盘，能像员工一样操作电脑软件，帮你订票、填表、发邮件。', icon: 'Code2' },
                { year: '2025 Q1', title: 'DeepSeek-R1', desc: '国产之光！推理成本打成“白菜价”，高性能 AI 变得像水电一样便宜，应用爆发的前夜。', icon: 'Brain', active: true, highlight: true },
                { year: '2025 Q2', title: 'GPT-5 预览', desc: '模型智力再次跃迁，多模态理解能力全面超越人类，解决复杂问题的能力大幅提升。', icon: 'Zap' },
                { year: '2025 Q3', title: '具身智能', desc: 'AI 拥有了身体，通用人形机器人开始走出实验室，尝试进入家庭处理家务。', icon: 'Users' },
                { year: '2025 Q4', title: 'AI OS', desc: '操作系统被 AI 重构，不再需要打开一个个 APP，AI 直接调用系统底层能力帮你搞定一切。', icon: 'Layout' },
                { year: '2025 Future', title: '主动智能', desc: 'AI 不再傻等指令，而是像贴心秘书一样，主动预测你的需求并把事办了。', icon: 'Rocket' }
            ]
        },
        {
            id: 'comparison',
            type: 'comparison',
            title: '产品工作流变革',
            subtitle: '从“单打独斗”到“人机协作”：AI 重塑产品全生命周期',
            steps: [
                { 
                    title: '1. 需求挖掘 (Discovery)', 
                    icon: 'Search',
                    subSteps: ['舆情监控', '竞品差异', '机会评估'],
                    traditional: [
                        '依赖滞后的研报，信息源单一',
                        '主观判断易陷入“伪需求”陷阱',
                        '缺乏量化数据支撑决策'
                    ], 
                    ai: [
                        'AI 助手全网监控竞品/舆情',
                        '基于数据量化用户痛点',
                        '自动生成机会点评估报告'
                    ]
                },
                { 
                    title: '2. 用户分析 (Empathy)', 
                    icon: 'Users',
                    subSteps: ['深度访谈', '问卷分析', '画像构建'],
                    traditional: [
                        '用户访谈样本少、周期长',
                        '定性分析受限于个人经验',
                        '难以覆盖目标用户场景'
                    ], 
                    ai: [
                        '合成海量虚拟用户角色',
                        '批量并行访谈快速验证',
                        '消除主观偏见，挖掘深层需求'
                    ]
                },
                { 
                    title: '3. 需求定义 (Definition)', 
                    icon: 'GitBranch',
                    subSteps: ['业务流程', '异常分支', '接口定义'],
                    traditional: [
                        '需求文档纯文字晦涩难懂',
                        '特殊异常情况靠脑补',
                        '开发漏看细节导致返工'
                    ], 
                    ai: [
                        '智能生成业务流程图',
                        '穷举异常流程规避风险',
                        '结构化文档确保逻辑自洽'
                    ]
                },
                { 
                    title: '4. 原型验证 (Prototyping)', 
                    icon: 'Layout',
                    subSteps: ['低保真', '高保真', '交互动效'],
                    traditional: [
                        '线框图交互性差，难体验',
                        '高保真依赖设计排期',
                        '验证想法的“试错成本”极高'
                    ], 
                    ai: [
                        '一句话生成界面',
                        '可交互演示 Demo 即时体验',
                        '独立完成原型验证'
                    ]
                },
                { 
                    title: '5. 开发跟进 (Delivery)', 
                    icon: 'Code2',
                    subSteps: ['技术评审', '冒烟测试', '视觉验收'],
                    traditional: [
                        '需求传递损耗大，理解偏差',
                        '验收往往滞后于开发完成',
                        'Bug 修复挤占迭代时间'
                    ], 
                    ai: [
                        '辅助生成测试计划与脚本',
                        '直接验收核心逻辑',
                        '前置质量卡点，减少返工'
                    ]
                },
                { 
                    title: '6. 交付迭代 (Iteration)', 
                    icon: 'RefreshCw',
                    subSteps: ['漏斗分析', '留存归因', 'A/B测试'],
                    traditional: [
                        '埋点漏埋，取数排期长',
                        '归因分析靠猜，缺乏依据',
                        '难以形成有效的数据闭环'
                    ], 
                    ai: [
                        '用大白话查数据',
                        '自动归因异常指标',
                        '基于数据生成迭代建议'
                    ]
                }
            ]
        },
        {
            id: 'my-journey',
            type: 'grid',
            title: '卢凯晨的 AI 进化实录',
            subtitle: '点击卡片查看具体案例与产出',
            items: [
                { 
                    category: '1. 需求挖掘', icon: 'Search', title: '竞品洞察', 
                    desc: '全网竞品分析',
                    detailDesc: 'AI 抓取同类健身计划 App 用户评论，发现市面普遍计划过于死板，缺乏个性化运动推荐。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '1. 需求挖掘', icon: 'MessageSquare', title: '反馈统计', 
                    desc: '海量反馈量化',
                    detailDesc: 'AI统计竞品用户反馈的需求，并自动根据频次排出优先级。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '2. 用户分析', icon: 'Users', title: '虚拟用户访谈', 
                    desc: 'AI 找茬',
                    detailDesc: 'AI模拟访谈目标用户“有运动习惯拥抱科技的商务精英”，输出所有可能的访谈对话。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '2. 用户分析', icon: 'Zap', title: '旅程模拟', 
                    desc: '情绪预测',
                    detailDesc: 'AI模拟目标用户从“填写档案” → “获取计划” → “开始运动” → “结束运动”的全流程用户故事，感受用户行为。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '3. 需求定义', icon: 'FileText', title: '需求极致优化', 
                    desc: '极速多轮迭代',
                    detailDesc: '写好需求框架输入AI，它自动补充产品逻辑细节和异常场景。单日内完成100次需求迭代，完成过去写几个月文档也达不到的需求深度和表达优化程度。',
                    detailImage: '555.mp4'
                },
                { 
                    category: '3. 需求定义', icon: 'MonitorPlay', title: '流程可视化', 
                    desc: '自动生成流程图',
                    detailDesc: '完善后的需求描述给AI，自动提炼业务核心流程，助力初步评审。',
                    detailImage: '888.mp4'
                },
                { 
                    category: '4. 原型验证', icon: 'Code2', title: '零成本验证', 
                    desc: '独立开发 Demo',
                    detailDesc: '利用AI生成Demo程序，一键验证需求是否可行，决策开始工程化还是回退优化，节约开发成本。',
                    detailImage: '222.mp4'
                },
                { 
                    category: '4. 原型验证', icon: 'Layout', title: '不画原型图', 
                    desc: '文字生成界面',
                    detailDesc: '描述原型需求，一键生成原型图，任意跳转，且自带详细注解。开发更高效，且把时间留给需求思考。',
                    detailImage: '111.mp4'
                },
                { 
                    category: '5. 开发跟进', icon: 'Brain', title: '逻辑排雷', 
                    desc: '极端场景测试',
                    detailDesc: '让 AI 扮演测试员，基于demo穷举极端场景。发现逻辑漏洞，及时补全。',
                    detailImage: '444.mp4'
                },
                { 
                    category: '5. 开发跟进', icon: 'CheckCircle', title: '用例生成', 
                    desc: '自动化脚本',
                    detailDesc: '基于最终版需求文档，输出标准测试用例，助力测试更清晰全面。',
                    detailImage: '666.mp4'
                },
                { 
                    category: '6. 交付迭代', icon: 'BarChart3', title: '数据自由', 
                    desc: '用人话问数据',
                    detailDesc: '提供原始数据，AI助力各种数据统计，不用花时间计算。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '6. 交付迭代', icon: 'BarChart3', title: '智能归因', 
                    desc: '异常指标诊断',
                    detailDesc: '需求突发出现问题，帮助排查问题，定位根因。',
                    detailImage: '',
                    detailImageText: '待补充'
                }
            ]
        },
        {
            id: 'case-study',
            type: 'showcase',
            title: '实战案例：做一个简单人脸跟踪小游戏',
            subtitle: '学习如何使用结构化提示词描述需求，完成你的第一个Demo程序',
            mainImage: '鼻子跟踪_7.0.html', // 对应 assets/鼻子跟踪_7.0.html
            steps: [
                { 
                    title: '1. 定义角色', 
                    desc: '你是一个高级web程序员，专注前端视觉，帮我制作网页版娱乐小程序。'
                },
                { 
                    title: '2. 核心需求', 
                    desc: '跟踪我的鼻子。'
                },
                { 
                    title: '3. 功能描述', 
                    desc: '默认不开启摄像头，打开摄像头后开始跟踪我的鼻子。' 
                },
                { 
                    title: '4. 页面布局', 
                    desc: '左下角开关“开始捕捉”；右上角“Score 得分”，摄像头未开启时：屏幕中间显示“请开启摄像头”' 
                },
                { 
                    title: '5. 视觉交互', 
                    desc: '摄像头开启后：鼻子显示红点（实时跟踪）；小红点随着鼻子运动，不停释放红色粒子，带来彗星尾巴的特效；天空不停落下绿色小球，鼻子碰到就会爆炸（彩色粒子），发出音效，并得分，球越大分数越高，同时弹出加分特效 “+分数”。' 
                },
                { 
                    title: '6. 技术要求', 
                    desc: 'html + css + javascript，html单文件' 
                },
                { 
                    title: '7. 运行程序', 
                    desc: '复制代码txt文本保存，后缀改成html，一键运行' 
                }
            ]
        },
        {
            id: 'other-scenarios',
            type: 'grid',
            title: 'AEKE 办公助手',
            subtitle: '探索更多 AI 赋能的可能性',
            items: [
                { 
                    category: '1. 知识赋能', icon: 'Book', title: 'AI 运动科学知识库', 
                    desc: '整合内部文档与专业教材，构建垂直领域的知识库。员工可以用自然语言快速检索复杂的运动生理学知识，辅助课程设计，解决“知识孤岛”问题。',
                    detailDesc: '整合内部文档与专业教材，构建垂直领域的知识库。员工可以用自然语言快速检索复杂的运动生理学知识，辅助课程设计，解决“知识孤岛”问题。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '2. 体验创新', icon: 'Music', title: 'AI 运动音乐生成', 
                    desc: '利用 AI 音乐模型，根据运动类型（如瑜伽、HIIT）快速生成匹配 BGM，解决版权问题并降低选曲成本，为用户提供个性化的听觉体验。',
                    detailDesc: '利用 AI 音乐模型，根据运动类型（如瑜伽、HIIT）快速生成匹配 BGM，解决版权问题并降低选曲成本，为用户提供个性化的听觉体验。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '3. 效率提升', icon: 'FileText', title: 'AI 需求预评审', 
                    desc: '产品需求AI先评（按公司级要求），降低反复评审会议的低效。',
                    detailDesc: '产品需求AI先评（按公司级要求），降低反复评审会议的低效。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '4. 决策辅助', icon: 'BarChart3', title: 'AI 竞品研报生成', 
                    desc: '输入竞品名称，AI 自动全网搜集其最新功能更新、定价策略与用户评价，生成结构化的对比分析表格，辅助产品决策。',
                    detailDesc: '输入竞品名称，AI 自动全网搜集其最新功能更新、定价策略与用户评价，生成结构化的对比分析表格，辅助产品决策。',
                    detailImage: '',
                    detailImageText: '待补充'
                },
                { 
                    category: '5. 客户服务', icon: 'MessageSquare', title: 'AI 售后助手', 
                    desc: '帮助内部售后人员解决常见问题的窗口，不用反复咨询相同产品问题。',
                    detailDesc: '帮助内部售后人员解决常见问题的窗口，不用反复咨询相同产品问题。',
                    detailImage: '',
                    detailImageText: '待补充'
                }
            ]
        },
        {
            id: 'team-empowerment',
            type: 'summary',
            title: 'AI 如何助力团队',
            subtitle: '从单点提效到全链路赋能',
            points: [
                '不再凭空猜想：用 AI 挖掘海量数据，精准定位用户痛点。',
                '不再纠结文档：用 AI 生成标准 PRD 与流程图，确保逻辑自洽。',
                '不再等待排期：用 AI 快速生成原型 Demo，即时验证想法。',
                '不再人肉测试：用 AI 穷举极端场景与编写用例，守住质量底线。'
            ],
            quote: '当你在思考需要写什么输出给AI时，为何不让AI直接输出给AI。'
        },
        {
            id: 'outro',
            type: 'cover',
            title: '拥抱变化',
            subtitle: '不要问 AI 能为你做什么，要问你想用 AI 创造什么。',
            presenter: '谢谢观看',
            date: ''
        }
    ]
};