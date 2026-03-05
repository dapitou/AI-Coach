package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

class PowerParamCalcCounter(override val powerType: AekePowerCoreAdapter.Power): WaveTypeSureCalcCounter(powerType) {
    override fun onSureRopeWaveType(values: Array<IPowerRopeWaveCalc.RopeWaveData>) {

    }

}