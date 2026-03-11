package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import kotlin.math.abs

//纠错
class ActionAdjustErrorPowerCalcCounter(override val type:ActionType):ActionPointPowerCalcCounter(type,true) {

    private val pointMaps:MutableMap<Int,MutableList<ActionPoint>> = mutableMapOf()
    private var wait5Point1:ActionPoint? = null
    private var wait5Point2:ActionPoint? = null
    private var waitCount:Int = 0

    var actionAdjustErrorCallback:(()->Unit)? = null


    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        repeat(6){
            pointMaps.put(it, mutableListOf())
        }

    }

    override fun onConfirmActionPoint(actionPoint: ActionPoint) {
        super.onConfirmActionPoint(actionPoint)
        pointMaps[actionPoint.pointType]?.add(actionPoint)
        if (actionPoint.pointType==5){
            if (wait5Point1==null){
                wait5Point1 = actionPoint
            }else{
                wait5Point2 = actionPoint
            }
        }
    }

    override fun onFps(value: Long) {
        super.onFps(value)
        if (wait5Point1!=null){
            waitCount++
            if (waitCount>3){
                calc(wait5Point1!!,wait5Point2)
            }
        }
    }

    private fun calc(action5Point1:ActionPoint,action5Point2: ActionPoint?){
        val action5IsSingle = if (wait5Point2==null){
            //5是单边
            true
        }else{
            //5是双边
            false
        }
        //TODO 触发回溯纠错判断

        pointMaps.filter { it.key!=0&&it.key!=3 }.values.filter {
            if (it.isEmpty()){
                false
            }else{
                if (type==ActionType.Single){
                    it.maxOf { it.frame }-it.minOf { it.frame }<=2
                }else{
                    it.maxOf { it.frame }-it.minOf { it.frame }>2
                }
            }
        }.also {
            if (it.size==4){
                actionAdjustErrorCallback?.invoke()
            }
        }
        pointMaps.forEach {
            it.value.clear()
        }
        wait5Point1 = null
        wait5Point2 = null
        waitCount = 0
    }

    override fun startCalcCount() {
        super.startCalcCount()
    }

    override fun stopCalcCount() {
        super.stopCalcCount()
    }

    override fun release() {
        super.release()
    }

}