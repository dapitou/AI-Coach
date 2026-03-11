package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.calc.adapter.PowerRopeUtils
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import java.util.LinkedList

open class ActionPointPowerCalcCounter(open val type: ActionType, private val useForCorrect: Boolean) :
    DoubleRopePowerCalcCounter() {

    var actionPointCallback:((ActionPoint)->Unit)? = null

    protected val internalActionPointCallback:((ActionPoint)->Unit)= {
        actionPointCallback?.invoke(it)
        onConfirmActionPoint(it)
    }

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter, useForCorrect)
        observeRopeLength(object :AekeObserver<Long>{
            override fun update(value: Long) {
                val leftRope = PowerRopeUtils.getLeftRopeLength(value)
                val rightRope = PowerRopeUtils.getRightRopeLength(value)
                onLeftRopeDy(leftRope)
                onRightRopeDy(rightRope)
            }
        })

        observeRopeXxLxTimeDataEvent(object :AekeObserver<IPowerCalcCounter.XxLxTimeData>{
            override fun update(value: IPowerCalcCounter.XxLxTimeData) {

            }

        })

    }

    private var rightLock:Boolean = false
    private var rightState3Temp:ActionPoint? = null
    private var rightQueue:LinkedList<ActionPoint> = LinkedList()
    private var prevRightRope:Long = Long.MIN_VALUE
    private fun onRightRopeDy(rightRope: Long) {
        if (prevRightRope==Long.MIN_VALUE){
            prevRightRope = rightRope
            return
        }
        val frame = powerWaveCalc.currentFrameNumber
        val start = multiInitStartPoint
        val distance = multiInitDistance
        if (distance==Int.MAX_VALUE){
            prevRightRope = rightRope
            return
        }
        if (prevRightRope<=getStartPointThr()&&rightRope>getStartPointThr()){
            //输出0 1
            var fr = powerWaveCalc.currentFrameNumber-1
            var minValue = Long.MAX_VALUE
            while (fr>0){
                val rope = powerWaveCalc.ropeData[fr.toInt()]
                val left = PowerRopeUtils.getLeftRopeLength(rope)
                val right = PowerRopeUtils.getRightRopeLength(rope)
                if (right-minValue<0){
                    minValue = right
                    fr--
                }else{
                    fr++
                    break
                }
            }
            val action1 = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,fr,0,System.currentTimeMillis()-(frame-fr)*100)
            internalActionPointCallback.invoke(action1)
            val action = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,frame,1,System.currentTimeMillis())
            rightQueue.push(action)
            internalActionPointCallback.invoke(action)

        }
        if (prevRightRope<=getDistanceRopeLengthThr()&&rightRope>getDistanceRopeLengthThr()){
            //输出2
            rightLock = true
            val action = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,frame,2,System.currentTimeMillis())
            rightQueue.push(action)
            internalActionPointCallback.invoke(action)
        }
        if (prevRightRope>getDistanceRopeLengthThr()&&rightRope<=getDistanceRopeLengthThr()){
            //输出3 4
            rightLock = false
            val temp = rightState3Temp
            if (temp != null) {
                if (temp.frame!=Long.MIN_VALUE){
                    val action2 = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,temp.frame,3,temp.pointTime)
                    internalActionPointCallback.invoke(action2)
                }
            }
            val action = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,frame,4,System.currentTimeMillis())
            rightQueue.push(action)
            internalActionPointCallback.invoke(action)
        }
        if (prevRightRope>getStartPointThr()&&rightRope<=getStartPointThr()){
            //输出5
            val action = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,frame,5,System.currentTimeMillis())
            rightQueue.push(action)
            internalActionPointCallback.invoke(action)
        }
        if (rightLock){
            if (rightRope>prevRightRope){
                rightState3Temp = ActionPoint(AekePowerCoreAdapter.Power.RIGHT,powerWaveCalc.currentFrameNumber,3,System.currentTimeMillis())
            }
        }else {
            rightState3Temp = null
        }
        prevRightRope = rightRope
    }

    private var leftLock:Boolean = false
    private var leftState3Temp:ActionPoint? = null
    private var leftQueue:LinkedList<ActionPoint> = LinkedList()
    private var prevLeftRope:Long = Long.MIN_VALUE
    private fun onLeftRopeDy(leftRope: Long) {
        if (prevLeftRope==Long.MIN_VALUE){
            prevLeftRope = leftRope
            return
        }
        val frame = powerWaveCalc.currentFrameNumber
        val start = multiInitStartPoint
        val distance = multiInitDistance
        if (distance==Int.MAX_VALUE){
            prevLeftRope = leftRope
            return
        }
        if (prevLeftRope<=getStartPointThr()&&leftRope>getStartPointThr()){
            //输出0 1
            var fr = powerWaveCalc.currentFrameNumber-1
            var minValue = Long.MAX_VALUE
            while (fr>0){
                val rope = powerWaveCalc.ropeData[fr.toInt()]
                val left = PowerRopeUtils.getLeftRopeLength(rope)
                val right = PowerRopeUtils.getRightRopeLength(rope)
                if (left-minValue<0){
                    minValue = left
                    fr--
                }else{
                    fr++
                    break
                }
            }
            val action1 = ActionPoint(AekePowerCoreAdapter.Power.LEFT,fr,0,System.currentTimeMillis()-(frame-fr)*100)
            internalActionPointCallback.invoke(action1)
            val action = ActionPoint(AekePowerCoreAdapter.Power.LEFT,frame,1,System.currentTimeMillis())
            leftQueue.push(action)
            internalActionPointCallback.invoke(action)

        }
        if (prevLeftRope<=getDistanceRopeLengthThr()&&leftRope>getDistanceRopeLengthThr()){
            //输出2
            leftLock = true
            val action = ActionPoint(AekePowerCoreAdapter.Power.LEFT,frame,2,System.currentTimeMillis())
            leftQueue.push(action)
            internalActionPointCallback.invoke(action)
        }
        if (prevLeftRope>getDistanceRopeLengthThr()&&leftRope<=getDistanceRopeLengthThr()){
            //输出3 4
            leftLock = false
            val temp = leftState3Temp
            if (temp != null) {
                if (temp.frame!=Long.MIN_VALUE){
                    val action2 = ActionPoint(AekePowerCoreAdapter.Power.LEFT,temp.frame,3,temp.pointTime)
                    internalActionPointCallback.invoke(action2)
                }
            }
            val action = ActionPoint(AekePowerCoreAdapter.Power.LEFT,frame,4,System.currentTimeMillis())
            leftQueue.push(action)
            internalActionPointCallback.invoke(action)
        }
        if (prevLeftRope>getStartPointThr()&&leftRope<=getStartPointThr()){
            //输出5
            val action = ActionPoint(AekePowerCoreAdapter.Power.LEFT,frame,5,System.currentTimeMillis())
            leftQueue.push(action)
            internalActionPointCallback.invoke(action)
        }
        if (leftLock){
            if (leftRope>prevLeftRope){
                leftState3Temp = ActionPoint(AekePowerCoreAdapter.Power.LEFT,powerWaveCalc.currentFrameNumber,3,System.currentTimeMillis())
            }
        }else {
            leftState3Temp = null
        }
        prevLeftRope = leftRope
    }

    protected open fun onConfirmActionPoint(actionPoint: ActionPoint){

    }

    private fun getDistanceRopeLengthThr():Int{
        return ((multiInitStartPoint+multiInitDistance*0.8f)).toInt()
    }

    private fun getStartPointThr():Int{
        return (multiInitStartPoint+multiInitDistance*0.2f).toInt()
    }

    data class ActionPoint(
        //左右电机
        val power:AekePowerCoreAdapter.Power,
        val frame:Long,
        //动作点类型:0-5
        val pointType:Int,
        //动作点时间戳
        val pointTime:Long)

}