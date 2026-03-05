package com.aeke.fitnessmirror.power.calc.adapter

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

open class BasePowerCalcCounter:IPowerCalcCounter {
    private lateinit var powerCalc: IPowerRopeWaveCalc
    private lateinit var config: PowerCalcConfig

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        this.powerCalc = powerRopeWaveCalc
        powerRopeWaveCalc.init(config,ropeGetter)
        this.config =  config
        powerCalc.observeRopeLength(object :AekeObserver<Long>{
            override fun update(value: Long) {
                onFps(value)
            }
        })
    }

    open fun onFps(value: Long){

    }

    override fun observeRopeLength(callback: AekeObserver<Long>): () -> Unit {
        return powerCalc.observeRopeLength(callback)
    }

    override fun stopCalcCount() {

    }

    override fun startCalcCount() {

    }

    override fun observeDoWorkAvgRopeLength(callback: AekeObserver<Pair<Int, Int>>): () -> Unit {
        //TODO
        return {}
    }

    override fun observeDoWorkCalcCountData(callback: AekeObserver<Int>): () -> Unit {
        //TODO
        return {}
    }

    override fun observeDoWorkCalcDataData(callback: AekeObserver<IPowerCalcCounter.DoWokeData>): () -> Unit {
        //TODO
        return {}
    }

    override fun observeDoWorkCalcCountTypeData(callback: AekeObserver<Pair<AekePowerCoreAdapter.Power?, IPowerCalcCounter.CountType>>): () -> Unit {
        //TODO
        return {}
    }

    override fun observeConfirmInitDistanceAndStartPoint(callback: AekeObserver<Pair<Int, Int>>): () -> Unit {
        //TODO
        return {}
    }

    override fun release() {
        powerCalc.release()
    }

    override fun switchHandShankMode(isImmediatelyStartCalc: Boolean) {

    }

    override fun switchCrossBarMode(isImmediatelyStartCalc: Boolean) {

    }
}