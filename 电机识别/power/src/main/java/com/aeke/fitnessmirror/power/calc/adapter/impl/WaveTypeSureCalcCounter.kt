package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

abstract class WaveTypeSureCalcCounter(override val powerType:AekePowerCoreAdapter.Power): SingleRopePowerCalcCounter(powerType) {

    private var preWaveType:IPowerRopeWaveCalc.RopeWaveData? = null

    override fun onHandlePowerCalcCount(value: IPowerRopeWaveCalc.RopeWaveData) {
        if (value.dy==0){
            preWaveType = null
            onSureRopeWaveType(arrayOf(value))
            return
        }
        preWaveType?.let {
            if (it.dy>0&&value.dy<0){
                onSureRopeWaveType(arrayOf(it,value))
                preWaveType = null
                return
            }
        }
        preWaveType = value
    }

    abstract fun onSureRopeWaveType(values: Array<IPowerRopeWaveCalc.RopeWaveData>)

}