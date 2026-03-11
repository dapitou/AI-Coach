package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

//动作平衡
class ActionBalancePowerCalcCounter(val type:ActionType):DoubleRopePowerCalcCounter() {

    var actionBalanceWorkCallback:((Float)->Unit)? = null
    var actionBalanceDistanceCallback:((Float)->Unit)? = null

    private var prevValue: IPowerCalcCounter.DoWokeData? = null

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter,true)
        observeDoWorkCalcDataData(object : AekeObserver<IPowerCalcCounter.DoWokeData> {
            override fun update(value: IPowerCalcCounter.DoWokeData) {
                if (value.value2!=null){
                    //双
                    var a = value.leftXiangXinDoWork
                    var b = value.rightXiangXinDoWork
                    //TODO 双侧功率差
                    val resultW = abs(a-b)/ min(a,b)
                    actionBalanceWorkCallback?.invoke(resultW)
                    //TODO 双侧行程差
                    a = value.value1.second.dy.toFloat()
                    b = value.value2!!.second.dy.toFloat()
                    val resultD = abs(a-b)/ min(a,b)
                    actionBalanceDistanceCallback?.invoke(resultD)
                }
            }
        })
    }

}