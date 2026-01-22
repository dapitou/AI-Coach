window.PhaseEngine = {
    generateSchedule: (totalWeeks) => {
        const phases = [];
        const P = CONFIG.PHASES;
        
        if (totalWeeks < 4) {
            if(totalWeeks === 1) phases.push({...P['进阶期'], weeks:1});
            else if(totalWeeks === 2) { phases.push({...P['适应期'], weeks:1}); phases.push({...P['进阶期'], weeks:1}); }
            else { phases.push({...P['适应期'], weeks:1}); phases.push({...P['进阶期'], weeks:1}); phases.push({...P['突破期'], weeks:1}); }
        } else {
            const w1 = Math.max(1, Math.round(totalWeeks * 0.25));
            const w2 = Math.max(1, Math.round(totalWeeks * 0.40));
            const w4 = Math.max(1, Math.round(totalWeeks * 0.10));
            const w3 = totalWeeks - w1 - w2 - w4;
            phases.push({...P['适应期'], weeks:w1});
            phases.push({...P['进阶期'], weeks:w2});
            phases.push({...P['突破期'], weeks:w3});
            phases.push({...P['减载期'], weeks:w4});
        }
        
        let schedule = [];
        phases.forEach(p => {
            for(let i=0; i<p.weeks; i++) schedule.push(p);
        });
        return schedule.slice(0, totalWeeks);
    }
};