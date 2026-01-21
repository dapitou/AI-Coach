window.UserAbility = {
    oneRM: {}, 
    init: () => {
        const level = window.store.user.level || 'L3';
        const coeff = CONFIG.LEVEL_COEFF[level] || 1.0;
        for(let k in CONSTANTS.ENUMS.ONE_RM) {
            window.UserAbility.oneRM[k] = Math.round(CONSTANTS.ENUMS.ONE_RM[k] * coeff);
        }
        // Ensure '全身' exists for fallback
        window.UserAbility.oneRM['全身'] = Math.round(50 * coeff);
    },
    update: (part, load, reps) => {
        // Epley Formula: 1RM = Weight * (1 + Reps/30)
        const est1RM = Math.round(load * (1 + reps/30));
        if (est1RM > (window.UserAbility.oneRM[part] || 0)) {
            window.UserAbility.oneRM[part] = est1RM;
            console.log(`[Feedback] New PR for ${part}: ${est1RM}kg`);
            return true;
        }
        return false;
    }
};