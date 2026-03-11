package com.aeke.fitnessmirror.power.calc.adapter

import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import com.aeke.baseliabrary.utils.data.GlobalPropManage
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

/*
* 脱手保护类
* */
class HandsOffProtectionHelper constructor(
    //m/s
    val speedThreshold:Float = -2.1f,
    val timeoutFrameCount:Long = 3,
    var protectCallback:((AekePowerCoreAdapter.Power)->Unit)? = null
):LifecycleOwner{

    private var lifecycleRegistry:LifecycleRegistry = LifecycleRegistry(this)

    private var destroyCallback:(()->Unit)? = null
    private var destroyCallback2:(()->Unit)? = null

    private var leftHandsOffOpen:Boolean = false
    private var rightHandsOffOpen:Boolean = false

    fun attach(powerRopeWaveCalc: IPowerRopeWaveCalc){
        lifecycleRegistry = LifecycleRegistry(this)
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)
        //电机层面的脱手保护
        if (NewPowerHelper.isSupportHandOffProtect()) {
            NewPowerHelper.setHandsOffProtect(GlobalPropManage.isSupportWeightProtect)
            NewPowerHelper.observerPowerErrorCode(this,object :AekeObserver<Int>{
                override fun update(value: Int) {
                    if (value==16){
                        protectCallback?.invoke(AekePowerCoreAdapter.Power.LEFT)
                    }else if (value==17){
                        protectCallback?.invoke(AekePowerCoreAdapter.Power.RIGHT)
                    }
                }
            })
        }else{
            destroyCallback = powerRopeWaveCalc.observeRopeWaveType(object :AekeObserver<IPowerRopeWaveCalc.RopeWaveData>{
                override fun update(value: IPowerRopeWaveCalc.RopeWaveData) {
                    if (value.type==AekePowerCoreAdapter.Power.LEFT){
                        leftHandsOffOpen = value.dy>0
                    }else if (value.type==AekePowerCoreAdapter.Power.RIGHT){
                        rightHandsOffOpen = value.dy>0
                    }
                }
            })
            destroyCallback2 = powerRopeWaveCalc.observeRopeLength(object :AekeObserver<Long>{
                override fun update(value: Long) {
                    val leftRope = PowerRopeUtils.getLeftRopeLength(value)
                    val rightRope = PowerRopeUtils.getRightRopeLength(value)
                    onLeftHandsOff(leftRope)
                    onRightHandsOff(rightRope)
                }

            })
        }
    }

    private var prevRightRope:Long = Long.MIN_VALUE
    private var prevRightSpeed: Float = Float.MIN_VALUE

    private var leftCount:Int = 0
    private var rightCount:Int = 0

    private var prevLeftRope:Long = Long.MIN_VALUE
    private var prevLeftSpeed: Float = Float.MIN_VALUE
    private fun onLeftHandsOff(rope:Long){
        if (!leftHandsOffOpen){
            return
        }
        if (prevLeftRope==Long.MIN_VALUE){
            prevLeftRope = rope
            return
        }
        if (prevLeftSpeed==Float.MIN_VALUE){
            prevLeftSpeed = (rope-prevLeftRope)/100f/0.1f
            if (prevLeftSpeed<=speedThreshold){
                leftCount++
            }
            return
        }
        prevLeftSpeed = (rope-prevLeftRope)/100f/0.1f
        if (prevLeftSpeed<=speedThreshold){
            leftCount++
        }
        if (leftCount>=timeoutFrameCount){
            leftHandsOffOpen = false
            protectCallback?.invoke(AekePowerCoreAdapter.Power.LEFT)
            leftCount = 0
            prevLeftRope = Long.MIN_VALUE
            prevLeftSpeed = Float.MIN_VALUE
        }
        prevLeftRope = rope
    }

    private fun onRightHandsOff(rope:Long){
        if (!rightHandsOffOpen){
            return
        }
        if (prevRightRope==Long.MIN_VALUE){
            prevRightRope = rope
            return
        }
        if (prevRightSpeed==Float.MIN_VALUE){
            prevRightSpeed = (rope-prevRightRope)/100f/0.1f
            if (prevRightSpeed<=speedThreshold){
                leftCount++
            }
            return
        }
        prevRightSpeed = (rope-prevRightRope)/100f/0.1f
        if (prevRightSpeed<=speedThreshold){
            rightCount++
        }
        if (rightCount>=timeoutFrameCount){
            rightHandsOffOpen = false
            protectCallback?.invoke(AekePowerCoreAdapter.Power.RIGHT)
            rightCount = 0
            prevRightRope = Long.MIN_VALUE
            prevRightSpeed = Float.MIN_VALUE
        }
        prevRightRope = rope
    }

    fun detach(){
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY)
        destroyCallback?.invoke()
        destroyCallback2?.invoke()
        protectCallback = null
        NewPowerHelper.setHandsOffProtect(false)
    }

    override fun getLifecycle(): Lifecycle {
        return lifecycleRegistry
    }

}