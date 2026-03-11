package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import kotlin.math.abs

//动作幅度
class ActionRangePowerCalcCounter(val type:ActionType):LxDoubleRopePowerCalcCounter() {

    var actionRangePowerCallback:((Float)->Unit)? = null

    private var leftPrevXx:IPowerRopeWaveCalc.RopeWaveData? = null
    private var rightPrevXx:IPowerRopeWaveCalc.RopeWaveData? = null

    private var dPrevXx:Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>? = null



    private var isSingle:Boolean = type==ActionType.Single

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        lxDistanceObservable.addObserver(object :AekeObserver<Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>>{
            override fun update(value: Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>) {
                if (isSingle){
                    if (value.size==1){
                        if (value[0].first==AekePowerCoreAdapter.Power.LEFT){
                            val prev = leftPrevXx?:return
                            //TODO 单左
                            val leftXx = prev.dy.toFloat()
//                            val leftLx = value[0].second.dy.toFloat()
                            actionRangePowerCallback?.invoke(abs(leftXx / multiInitDistance))
                        }else{
                            //TODO 单右
                            val prev = rightPrevXx?:return
                            val rightXx = prev.dy.toFloat()
//                            val rightLx = value[0].second.dy.toFloat()
                            actionRangePowerCallback?.invoke(abs(rightXx / multiInitDistance))

                        }
                    }
                }else{
                    if (value.size==2){
                        //TODO 双
                        val prev = dPrevXx?:return
                        val xxDis = (prev[0].second.dy+prev[1].second.dy)/2f
//                        val lxDis = (value[0].second.dy+value[1].second.dy)/2f
                        actionRangePowerCallback?.invoke(abs(xxDis / multiInitDistance))
                    }
                }
            }
        })
        xxDistanceObservable.addObserver(object :AekeObserver<Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>>{
            override fun update(value: Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>) {
                if (multiInitDistance==Int.MAX_VALUE){
                    return
                }
                if (isSingle){
                    if (value.size==1){
                        if (value[0].first==AekePowerCoreAdapter.Power.LEFT){
                            leftPrevXx = value[0].second
                        }else{
                            rightPrevXx = value[0].second
                        }
                    }
                }else{
                    if (value.size==2){
                        dPrevXx = value
                    }
                }
            }
        })
    }

}