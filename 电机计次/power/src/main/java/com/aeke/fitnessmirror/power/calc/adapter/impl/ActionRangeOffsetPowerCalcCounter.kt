package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min
import kotlin.math.sqrt

//幅度一致性
class ActionRangeOffsetPowerCalcCounter(override val type:ActionType):ActionPointPowerCalcCounter(type,true) {

    var actionRangeOffsetDistanceCallback:((Float)->Unit)? = null

    private var prevValue: IPowerCalcCounter.DoWokeData? = null
    private var sumQ:Float = 0f
    private var totalDistance:Float = Float.MIN_VALUE
    private var prevAvgDistance:Float = Float.MIN_VALUE
    private var calcCount:Int = 0

    private val oldDoubleRopePowerCalcCounter:OldDoubleRopePowerCalcCounter = OldDoubleRopePowerCalcCounter()

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        oldDoubleRopePowerCalcCounter.init(config, powerRopeWaveCalc, ropeGetter,true)
        oldDoubleRopePowerCalcCounter.observeDoWorkCalcDataData(object : AekeObserver<IPowerCalcCounter.DoWokeData> {
            override fun update(value: IPowerCalcCounter.DoWokeData) {
                val resultD:Float
                if (value.value2!=null){
                    var a = value.value1.second.dy.toFloat()
                    var b = value.value2!!.second.dy.toFloat()
                    resultD = (a+b)/2
                }else{
                    return
                }

                calcCount++
                if (prevAvgDistance==Float.MIN_VALUE){
                    prevAvgDistance=resultD
                    totalDistance = resultD
                }else{
                    prevAvgDistance = (prevAvgDistance+resultD)/2
                    totalDistance+=resultD
                    val a = resultD-prevAvgDistance
                    sumQ+=((a*a)/calcCount)
                    val b = sqrt(sumQ)/prevAvgDistance
                    actionRangeOffsetDistanceCallback?.invoke(b)
                }
            }
        })
    }

    override fun release() {
        super.release()
        oldDoubleRopePowerCalcCounter.release()
    }

    override fun startCalcCount() {
        super.startCalcCount()
        oldDoubleRopePowerCalcCounter.startCalcCount()
    }

    override fun stopCalcCount() {
        super.stopCalcCount()
        oldDoubleRopePowerCalcCounter.stopCalcCount()
    }

}