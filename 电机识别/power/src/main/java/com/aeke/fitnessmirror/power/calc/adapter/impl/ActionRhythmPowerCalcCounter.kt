package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import kotlin.math.abs

//动作节奏
class ActionRhythmPowerCalcCounter(override val type:ActionType):ActionPointPowerCalcCounter(type,true) {

    //动作节奏向心时间回调
    var actionRhythmXxCallback:((Float)->Unit)? = null

    //动作节奏离心时间回调
    var actionRhythmLxCallback:((Float)->Unit)? = null



    private var leftActionXxTime:ActionXxTime = ActionXxTime(AekePowerCoreAdapter.Power.LEFT)
    private var rightActionXxTime:ActionXxTime = ActionXxTime(AekePowerCoreAdapter.Power.RIGHT)

    private var leftTempActionXxTime:ActionXxTime? = null
    private var rightTempActionXxTime:ActionXxTime? = null
    private var currentTempActionXxTime:ActionXxTime? = null

    private var waitXxFrameCount:Int = 0



    private var leftActionLxTime:ActionLxTime = ActionLxTime(AekePowerCoreAdapter.Power.LEFT)
    private var rightActionLxTime:ActionLxTime = ActionLxTime(AekePowerCoreAdapter.Power.RIGHT)

    private var leftTempActionLxTime:ActionLxTime? = null
    private var rightTempActionLxTime:ActionLxTime? = null
    private var currentTempActionLxTime:ActionLxTime? = null

    private var waitLxFrameCount:Int = 0

    private val oldDoubleRopePowerCalcCounter:OldDoubleRopePowerCalcCounter = OldDoubleRopePowerCalcCounter()

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        oldDoubleRopePowerCalcCounter.init(config, powerRopeWaveCalc, ropeGetter,true)
    }

    override fun onFps(value: Long) {
        super.onFps(value)
        if (waitXxFrameCount>=3){
            onConfirmActionXxTime(currentTempActionXxTime!!,null)
            currentTempActionXxTime = null
            waitXxFrameCount=0
            leftTempActionXxTime = null
            rightTempActionXxTime = null
        }
        if (leftTempActionXxTime!=null&&rightTempActionXxTime!=null){
            //判断双边
            onConfirmActionXxTime(leftTempActionXxTime!!,rightTempActionXxTime!!)
            leftTempActionXxTime = null
            rightTempActionXxTime = null
        }else if (leftTempActionXxTime!=null){
            currentTempActionXxTime = leftTempActionXxTime
            waitXxFrameCount++
        }else if (rightTempActionXxTime!=null){
            currentTempActionXxTime = rightTempActionXxTime
            waitXxFrameCount++
        }else{
            waitXxFrameCount=0
        }


        if (waitLxFrameCount>=3){
            onConfirmActionLxTime(currentTempActionLxTime!!,null)
            currentTempActionLxTime = null
            waitLxFrameCount=0
            leftTempActionLxTime = null
            rightTempActionLxTime = null
        }
        if (leftTempActionLxTime!=null&&rightTempActionLxTime!=null){
            //判断双边
            onConfirmActionLxTime(leftTempActionLxTime!!,rightTempActionLxTime!!)
            leftTempActionLxTime = null
            rightTempActionLxTime = null
        }else if (leftTempActionLxTime!=null){
            currentTempActionLxTime = leftTempActionLxTime
            waitLxFrameCount++
        }else if (rightTempActionLxTime!=null){
            currentTempActionLxTime = rightTempActionLxTime
            waitLxFrameCount++
        }else{
            waitLxFrameCount=0
        }
    }

    override fun onConfirmActionPoint(actionPoint: ActionPoint) {
        super.onConfirmActionPoint(actionPoint)
        if (actionPoint.power == AekePowerCoreAdapter.Power.LEFT){
            onLeftActionPoint(actionPoint)
        }else{
            onRightActionPoint(actionPoint)
        }
    }

    private fun onLeftActionPoint(actionPoint: ActionPoint){
        if (actionPoint.pointType == 1){
            leftActionXxTime.point1Frame = actionPoint.frame
            leftActionXxTime.point2Frame = Long.MIN_VALUE
        }else if (actionPoint.pointType == 2){
            leftActionXxTime.point2Frame = actionPoint.frame
        }
        if (leftActionXxTime.point1Frame!=Long.MIN_VALUE && leftActionXxTime.point2Frame!=Long.MIN_VALUE){
            leftTempActionXxTime = ActionXxTime(AekePowerCoreAdapter.Power.LEFT,leftActionXxTime.point1Frame,leftActionXxTime.point2Frame)
            leftActionXxTime.point1Frame = Long.MIN_VALUE
            leftActionXxTime.point2Frame = Long.MIN_VALUE
        }


        if (actionPoint.pointType == 4){
            leftActionLxTime.point1Frame = actionPoint.frame
            leftActionLxTime.point2Frame = Long.MIN_VALUE
        }else if (actionPoint.pointType == 5){
            leftActionLxTime.point2Frame = actionPoint.frame
        }
        if (leftActionLxTime.point1Frame!=Long.MIN_VALUE && leftActionLxTime.point2Frame!=Long.MIN_VALUE){
            leftTempActionLxTime = ActionLxTime(AekePowerCoreAdapter.Power.LEFT,leftActionLxTime.point1Frame,leftActionLxTime.point2Frame)
            leftActionLxTime.point1Frame = Long.MIN_VALUE
            leftActionLxTime.point2Frame = Long.MIN_VALUE
        }

    }

    private fun onRightActionPoint(actionPoint: ActionPoint){
        if (actionPoint.pointType == 1){
            rightActionXxTime.point1Frame = actionPoint.frame
            rightActionXxTime.point2Frame = Long.MIN_VALUE
        }else if (actionPoint.pointType == 2){
            rightActionXxTime.point2Frame = actionPoint.frame
        }
        if (rightActionXxTime.point1Frame!=Long.MIN_VALUE && rightActionXxTime.point2Frame!=Long.MIN_VALUE){
            rightTempActionXxTime = ActionXxTime(AekePowerCoreAdapter.Power.LEFT,rightActionXxTime.point1Frame,rightActionXxTime.point2Frame)
            rightActionXxTime.point1Frame = Long.MIN_VALUE
            rightActionXxTime.point2Frame = Long.MIN_VALUE
        }



        if (actionPoint.pointType == 4){
            rightActionLxTime.point1Frame = actionPoint.frame
            rightActionLxTime.point2Frame = Long.MIN_VALUE
        }else if (actionPoint.pointType == 5){
            rightActionLxTime.point2Frame = actionPoint.frame
        }
        if (rightActionLxTime.point1Frame!=Long.MIN_VALUE && rightActionLxTime.point2Frame!=Long.MIN_VALUE){
            rightTempActionLxTime = ActionLxTime(AekePowerCoreAdapter.Power.LEFT,rightActionLxTime.point1Frame,rightActionLxTime.point2Frame)
            rightActionLxTime.point1Frame = Long.MIN_VALUE
            rightActionLxTime.point2Frame = Long.MIN_VALUE
        }
    }

    private fun onConfirmActionXxTime(actionXxTime1: ActionXxTime,actionXxTime2: ActionXxTime?){
        if (actionXxTime2!=null){
            //TODO 双
            val xxTime1 = (actionXxTime1.point2Frame-actionXxTime1.point1Frame).toFloat()
            val xxTime2 = (actionXxTime2.point2Frame-actionXxTime2.point1Frame).toFloat()
            actionRhythmXxCallback?.invoke((xxTime1+xxTime2)/20)
        }else {
            //TODO 单
            val xxTime1 = (actionXxTime1.point2Frame-actionXxTime1.point1Frame).toFloat()
            actionRhythmXxCallback?.invoke(xxTime1/10)
        }

    }

    private fun onConfirmActionLxTime(actionLxTime1: ActionLxTime,actionLxTime2: ActionLxTime?){
        if (actionLxTime2!=null){
            //TODO 双
            val lxTime1 = (actionLxTime1.point2Frame-actionLxTime1.point1Frame).toFloat()
            val lxTime2 = (actionLxTime2.point2Frame-actionLxTime2.point1Frame).toFloat()
            actionRhythmLxCallback?.invoke(abs((lxTime1+lxTime2)/20))
        }else {
            //TODO 单
            val lxTime1 = (actionLxTime1.point2Frame-actionLxTime1.point1Frame).toFloat()
            actionRhythmLxCallback?.invoke(abs(lxTime1/10))
        }
    }

    override fun startCalcCount() {
        super.startCalcCount()
        oldDoubleRopePowerCalcCounter.startCalcCount()
    }

    override fun stopCalcCount() {
        super.stopCalcCount()
        oldDoubleRopePowerCalcCounter.stopCalcCount()
    }

    override fun release() {
        super.release()
        oldDoubleRopePowerCalcCounter.release()
    }


    data class ActionXxTime(val power:AekePowerCoreAdapter.Power,var point1Frame:Long = Long.MIN_VALUE,var point2Frame:Long = Long.MIN_VALUE)
    data class ActionLxTime(val power:AekePowerCoreAdapter.Power,var point2Frame:Long = Long.MIN_VALUE,var point1Frame:Long = Long.MIN_VALUE)

}