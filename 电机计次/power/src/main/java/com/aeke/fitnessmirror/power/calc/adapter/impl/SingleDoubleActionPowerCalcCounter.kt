package com.aeke.fitnessmirror.power.calc.adapter.impl

import android.util.Log
import com.aeke.baseliabrary.utils.log.ALog
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.data.ActionRhythmHelper

class SingleDoubleActionPowerCalcCounter(override val type:ActionType): ActionPointPowerCalcCounter(type,true) {

    val actionBalance:ActionBalancePowerCalcCounter = ActionBalancePowerCalcCounter(type)
    val actionRangeOffset:ActionRangeOffsetPowerCalcCounter = ActionRangeOffsetPowerCalcCounter(type)
    val actionRange:ActionRangePowerCalcCounter = ActionRangePowerCalcCounter(type)
    val actionRhythm:ActionRhythmPowerCalcCounter = ActionRhythmPowerCalcCounter(type)
    val actionAdjustError:ActionAdjustErrorPowerCalcCounter = ActionAdjustErrorPowerCalcCounter(type)

    //动作平衡功率差 0
    //动作平衡行程差 1
    //幅度一致性 2
    //动作幅度 3
    //动作节奏 向心 4
    //动作节奏 离心 5
    /*
    * 类型 to 评分(ABCDE)
    * */
    var actionCallback:((ActionScore)->Unit)? = null
    var adjustErrorCallback:(()->Unit)? = null

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        actionBalance.init(config, powerRopeWaveCalc, ropeGetter)
        actionRangeOffset.init(config, powerRopeWaveCalc, ropeGetter)
        actionRange.init(config, powerRopeWaveCalc, ropeGetter)
        actionRhythm.init(config, powerRopeWaveCalc, ropeGetter)
        actionAdjustError.init(config, powerRopeWaveCalc, ropeGetter)

        //纠错
        actionAdjustError.actionAdjustErrorCallback = {
            ALog.d("纠错回调")
            adjustErrorCallback?.invoke()
        }

        //动作平衡功率差
        actionBalance.actionBalanceWorkCallback = {
            if (it<=0.1f){
                actionCallback?.invoke(ActionScore(0,"A",it))
            }else if(it<=0.15f){
                actionCallback?.invoke(ActionScore(0,"B",it))
            }else if (it<=0.20f){
                actionCallback?.invoke(ActionScore(0,"C",it))
            }else if (it<=0.25f){
                actionCallback?.invoke(ActionScore(0,"D",it))
            }else{
                actionCallback?.invoke(ActionScore(0,"E",it))
            }
        }
//        //动作平衡行程差
//        actionBalance.actionBalanceDistanceCallback = {
//            if (it<=0.05f){
//                actionCallback?.invoke(ActionScore(1,"A",it))
//            }else if(it<=0.08f){
//                actionCallback?.invoke(ActionScore(1,"B",it))
//            }else if (it<=0.11f){
//                actionCallback?.invoke(ActionScore(1,"C",it))
//            }else if (it<=0.13f){
//                actionCallback?.invoke(ActionScore(1,"D",it))
//            }else{
//                actionCallback?.invoke(ActionScore(1,"E",it))
//            }
//        }
        //幅度一致性
//        actionRangeOffset.actionRangeOffsetDistanceCallback = {
//            if (it<=0.05f){
//                actionCallback?.invoke(ActionScore(2,"A",it))
//            }else if(it<=0.08f){
//                actionCallback?.invoke(ActionScore(2,"B",it))
//            }else if (it<=0.11f){
//                actionCallback?.invoke(ActionScore(2,"C",it))
//            }else if (it<=0.13f){
//                actionCallback?.invoke(ActionScore(2,"D",it))
//            }else{
//                actionCallback?.invoke(ActionScore(2,"E",it))
//            }
//        }
        //动作幅度
        actionRange.actionRangePowerCallback = {
            if (it<0.8f){
                actionCallback?.invoke(ActionScore(3,"E",it))
            }else if(it<0.9f){
                actionCallback?.invoke(ActionScore(3,"D",it))
            }else if (it<0.95f){
                actionCallback?.invoke(ActionScore(3,"C",it))
            }else if (it<1.0f){
                actionCallback?.invoke(ActionScore(3,"B",it))
            }else{
                actionCallback?.invoke(ActionScore(3,"A",it))
            }
        }
        //动作节奏 向心
//        actionRhythm.actionRhythmXxCallback = {
//            if (it<1f){
//                actionCallback?.invoke(ActionScore(4,"E",it))
//            }else if(it<1.2f){
//                actionCallback?.invoke(ActionScore(4,"D",it))
//            }else if (it<1.6f){
//                actionCallback?.invoke(ActionScore(4,"C",it))
//            }else if (it<1.8f){
//                actionCallback?.invoke(ActionScore(4,"B",it))
//            }else{
//                actionCallback?.invoke(ActionScore(4,"A",it))
//            }
//        }
        //动作节奏 离心
        actionRhythm.actionRhythmLxCallback = {
            val durations = ActionRhythmHelper.getActionRhythmDuration(distanceType)
            when (it) {
                in durations.rangeA -> {
                    actionCallback?.invoke(ActionScore(5, "A", it))
                }

                in durations.rangeB -> {
                    actionCallback?.invoke(ActionScore(5, "B", it))
                }

                in durations.rangeC -> {
                    actionCallback?.invoke(ActionScore(5, "C", it))
                }

                in durations.rangeD -> {
                    actionCallback?.invoke(ActionScore(5, "D", it))
                }

                in durations.rangeE -> {
                    actionCallback?.invoke(ActionScore(5, "E", it))
                }
            }
        }
    }

    override fun release() {
        super.release()
        actionCallback = null
        actionBalance.release()
        actionRangeOffset.release()
        actionRange.release()
        actionRhythm.release()
        actionAdjustError.release()
    }

    override fun startCalcCount() {
        super.startCalcCount()
        actionBalance.startCalcCount()
        actionRangeOffset.startCalcCount()
        actionRange.startCalcCount()
        actionRhythm.startCalcCount()
        actionAdjustError.startCalcCount()
    }

    override fun stopCalcCount() {
        super.stopCalcCount()
        actionBalance.stopCalcCount()
        actionRangeOffset.stopCalcCount()
        actionRange.stopCalcCount()
        actionRhythm.stopCalcCount()
        actionAdjustError.stopCalcCount()
    }

    data class ActionScore(
        //动作平衡功率差 0
        //动作平衡行程差 1
        //幅度一致性 2
        //动作幅度 3
        //动作节奏 向心 4
        //动作节奏 离心 5
        val type:Int,
        //ABCDE
        val level:String,
        //分数
        val score:Float)

}

enum class ActionType{
    Single,Double
}