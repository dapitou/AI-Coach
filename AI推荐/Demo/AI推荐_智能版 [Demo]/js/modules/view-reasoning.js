window.ViewReasoning = {
    startReasoning: () => {
        App.switchView('view-reasoning');
        document.getElementById('app').classList.add('state-reasoning');
        document.querySelector('.siri-container').classList.add('thinking');
        
        const user = window.store.user;
        const inputs = window.store.inputs;
        const flow = window.store.flow;
        
        const logs = [];
        logs.push(`读取档案: ${user.gender} / ${user.level} / ${user.goal}`);
        
        if (flow === 'course') {
            const targets = Array.isArray(inputs.targets) ? inputs.targets.join(',') : inputs.targets;
            logs.push(`解析需求: ${inputs.type} / ${targets}`);
        } else {
            const daysCount = (inputs.days || []).length;
            logs.push(`解析计划: ${inputs.cycle}周 / ${daysCount}天频次`);
        }
        
        if (user.pain && user.pain.length) logs.push(`风控过滤: 避开${user.pain.join('、')}`);
        else logs.push(`风控扫描: 无禁忌部位`);
        
        logs.push(`匹配策略: ${CONFIG.STRATEGY[user.goal]?.strategy || '智能推荐'}模型`);
        logs.push(`构建课程: 动作库 Top-K 筛选`);
        logs.push(`生成方案: 计算容量与负荷...`);

        const logContainer = document.getElementById('reasoning-log');
        logContainer.innerHTML = '';
        
        let i = 0; 
        function nextLog() {
            if (i >= logs.length) {
                setTimeout(() => {
                    document.getElementById('app').classList.remove('state-reasoning');
                    document.querySelector('.siri-container').classList.remove('thinking');
                    App.showResult();
                }, 800);
                return;
            }
            const div = document.createElement('div');
            div.className = 'log-item';
            div.innerHTML = `<div class="log-icon"><div class="typing-dot" style="width:4px;height:4px;background:#fff;animation:none;opacity:0.5;"></div></div><span>${logs[i]}</span>`;
            logContainer.appendChild(div);
            if (i > 0) {
                const prev = logContainer.children[i-1];
                prev.classList.remove('active');
                prev.classList.add('done');
                prev.querySelector('.log-icon').innerHTML = '✓';
            }
            div.classList.add('active');
            i++;
            setTimeout(nextLog, 800);
        }
        nextLog();
    }
};