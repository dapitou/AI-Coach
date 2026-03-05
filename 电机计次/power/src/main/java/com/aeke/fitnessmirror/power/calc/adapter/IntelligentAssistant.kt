package com.aeke.fitnessmirror.power.calc.adapter

import android.os.Handler
import android.os.Looper
import android.os.Message
import android.util.Log
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import com.aeke.baseliabrary.utils.data.GlobalPropManage
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.adapter.impl.DoubleRopePowerCalcCounter
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import java.math.BigDecimal
import java.math.RoundingMode
import kotlin.math.round


class IntelligentAssistant(val counter: DoubleRopePowerCalcCounter) : LifecycleOwner {
    private val lifecycleRegistry = LifecycleRegistry(this)
    private var leftDy = 0
    private var rightDy = 0
    private var currentSide: Side? = null
    private var isEnable = true
    private var isAssistantRunning = false
    var onAssistantRunning: ((Boolean) -> Unit)? = null
    companion object {
        const val MSG_START_ASSISTANT = 1
        const val MSG_STOP_ASSISTANT = 2
        const val MSG_ASSISTANT_RUNNING = 3

        //速度的单位为cm/s，所以将临界速度也进行转化，0.2m/s和0.4m/s即20cm/s，40cm/s
        const val START_CRITICAL_SPEED = 25
        const val STOP_CRITICAL_SPEED = 40

        //临界速度的持续时间，单位为ms
        const val CRITICAL_DURATION = 2000L
        const val ASSISTANT_INTERVAL_TIME = 1200L

        const val MIN_WEIGHT = 2f
        const val MIN_SMOOTH_RATE = 4

        //如果当前重量小于等于这个重量，则不进行智能助力
        const val ASSISTANT_CRITICAL_WEIGHT = 5f
    }


    private val mainHandler: Handler = object : Handler(Looper.getMainLooper()) {
        override fun handleMessage(msg: Message) {

            when (msg.what) {
                MSG_START_ASSISTANT -> {
                    Log.d("IntelligentAssistant", "start assistant")
                    isAssistantRunning = true
                    startAssistant()
                }

                MSG_STOP_ASSISTANT -> {
                    Log.d("IntelligentAssistant", "stop assistant")
                    isAssistantRunning = false
                }

                MSG_ASSISTANT_RUNNING -> {
                    val step = msg.obj as Float
                    val currentWeight = NewPowerHelper.currentPowerSetWeight
                    Log.d(
                        "IntelligentAssistant",
                        "assistant running step = $step, currentWeight = $currentWeight"
                    )
                    val currentModeType = NewPowerHelper.getPowerModeType()
                    val targetWeight = currentWeight - step
                    var smoothRate = (step * 2).toInt()
                    currentModeType.weight = targetWeight
                    if (currentWeight <= MIN_WEIGHT || targetWeight <= MIN_WEIGHT || step <= 0.6) {
                        isAssistantRunning = false
                        NewPowerHelper.setPower(MIN_WEIGHT)
                    } else {
                        if (smoothRate < MIN_SMOOTH_RATE) {
                            smoothRate = MIN_SMOOTH_RATE
                        }
                        NewPowerHelper.setPowerSmooth(currentModeType, smoothRate)
                    }
                    onAssistantRunning?.invoke(isAssistantRunning)
                    if (isAssistantRunning) {
                        val newMsg = Message.obtain()
                        newMsg.what = MSG_ASSISTANT_RUNNING
                        newMsg.obj = step
                        this.sendMessageDelayed(newMsg, ASSISTANT_INTERVAL_TIME)
                    }
                }
            }
        }
    }

    init {
        init(counter)
    }

    private fun init(counter: DoubleRopePowerCalcCounter) {
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_CREATE)
        NewPowerHelper.observePowerInfoTickCallback(
            this,
            object : AekeObserver<AekePowerCoreAdapter.PowerInfo> {
                override fun update(value: AekePowerCoreAdapter.PowerInfo) {
                    if (!isEnable) {
                        return
                    }
                    if (counter.multiInitDistance == Int.MAX_VALUE) {
                        return
                    }
                    speedDetect(value.leftSpeed, value.rightSpeed)
                }
            })
        counter.observeFromRopeStartPointDy(object : AekeObserver<Pair<Long, Long>> {
            override fun update(value: Pair<Long, Long>) {
                leftDy = value.first.toInt()
                rightDy = value.second.toInt()
            }

        })
        isEnable = GlobalPropManage.isSupportAssistant
    }

    fun release() {
        lifecycleRegistry.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY)
        onAssistantRunning = null
    }

    private fun speedDetect(leftSpeed: Int, rightSpeed: Int) {
        Log.d("speedDetect", "speedDetect leftSpeed = $leftSpeed, rightSpeed = $rightSpeed")
        if (!isAssistantRunning && (leftSpeed < 0 && rightSpeed < 0)) {
            currentSide = null
            mainHandler.removeMessages(MSG_START_ASSISTANT)
            return
        }
        val (maxSpeed, side) =
            when {
                leftSpeed > rightSpeed -> leftSpeed to Side.LEFT
                leftSpeed < rightSpeed -> rightSpeed to Side.RIGHT
                else -> leftSpeed to currentSide
            }

        if (currentSide != side) {
            currentSide = side
            if (!(leftSpeed > 0 && rightSpeed > 0)) {
                mainHandler.removeMessages(MSG_START_ASSISTANT)
                return
            }
        }
        val dy = if (side == Side.LEFT) leftDy else rightDy
        if (isAssistantRunning) {
            if (dy < 5 || maxSpeed == 0 || NewPowerHelper.isUnload) {
                mainHandler.removeMessages(MSG_STOP_ASSISTANT)
                mainHandler.sendEmptyMessage(MSG_STOP_ASSISTANT)
                return
            }
            if (maxSpeed >= STOP_CRITICAL_SPEED) {
                if (!mainHandler.hasMessages(MSG_STOP_ASSISTANT)) {
                    mainHandler.sendEmptyMessageDelayed(MSG_STOP_ASSISTANT, CRITICAL_DURATION)
                }
            } else {
                mainHandler.removeMessages(MSG_STOP_ASSISTANT)
            }
            return
        }
        if (isNoNeedAssistant()) {
            return
        }
        if (maxSpeed in 1 until START_CRITICAL_SPEED && dy < counter.multiInitDistance * 0.8) {
            if (!mainHandler.hasMessages(MSG_START_ASSISTANT)) {
                mainHandler.sendEmptyMessageDelayed(MSG_START_ASSISTANT, CRITICAL_DURATION)
            }
        } else if (maxSpeed == 0) {
            //do nothing
        } else {
            mainHandler.removeMessages(MSG_START_ASSISTANT)
        }
    }

    private fun startAssistant() {
        val currentWeight = NewPowerHelper.currentPowerSetWeight
        val step = ((currentWeight - 2) / 4).roundToHalfStep().toFloat()
        val message = Message.obtain()
        message.what = MSG_ASSISTANT_RUNNING
        message.obj = step
        mainHandler.sendMessage(message)
    }

    private fun isNoNeedAssistant(): Boolean {
        return (NewPowerHelper.currentPowerSetWeight <= ASSISTANT_CRITICAL_WEIGHT
                || NewPowerHelper.isUnload)
    }

    fun enableAssistant() {
        isEnable = true
    }

    fun disableAssistant() {
        isEnable = false
        isAssistantRunning = false
        mainHandler.removeMessages(MSG_START_ASSISTANT)
        mainHandler.removeMessages(MSG_STOP_ASSISTANT)
    }

    override fun getLifecycle(): Lifecycle {
        return lifecycleRegistry
    }

    private fun Number.roundToHalfStep(): Double {
        val value = this.toDouble()
        val halfStepped = round(value * 2) / 2.0
        return BigDecimal.valueOf(halfStepped)
            .setScale(1, RoundingMode.HALF_UP)
            .toDouble()
    }

    enum class Side {
        LEFT,
        RIGHT
    }
}