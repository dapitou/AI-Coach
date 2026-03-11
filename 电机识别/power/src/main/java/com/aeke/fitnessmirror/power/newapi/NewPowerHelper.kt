package com.aeke.fitnessmirror.power.newapi

import android.os.Handler
import android.os.Looper
import android.media.MediaPlayer
import android.util.Log
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleEventObserver
import androidx.lifecycle.LifecycleOwner
import com.aeke.baseliabrary.event.BleDeviceButtonPressEvent
import com.aeke.baseliabrary.event.PinUnloaderBatteryEvent
import com.aeke.baseliabrary.utils.ProductHelper
import com.aeke.baseliabrary.utils.log.ALog
import com.aeke.baseliabrary.utils.log.logD
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.PowerAdjustProtectDialog
import com.aeke.fitnessmirror.power.PowerModule
import com.aeke.fitnessmirror.power.R
import com.aeke.fitnessmirror.power.benmo.PowerControlModelInterface
import com.aeke.fitnessmirror.power.event.AdjustWeightProtectResultEvent
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import com.aeke.fitnessmirror.power.newapi.adapter.impl.BenMoPowerCoreAdapterImpl
import org.greenrobot.eventbus.EventBus
import org.greenrobot.eventbus.Subscribe
import org.greenrobot.eventbus.ThreadMode
import java.util.function.Consumer
import kotlin.math.abs
import kotlin.math.roundToInt

object NewPowerHelper {

    private lateinit var powerCore: AekePowerCoreAdapter
    const val SMOOTH_STEP = 3f
    const val SMOOTH_PERIOD = 500L
    private val weightChanged: AekeObservable<Pair<String, Float>> = AekeObservable()
    private val modeChanged: AekeObservable<Pair<String, AekePowerCoreAdapter.PowerMode>> = AekeObservable()
    private val errorCodeChanged: AekeObservable<Int> = AekeObservable()
    private val unloadChanged: AekeObservable<Boolean> = AekeObservable()
    private val powerInfoChanged: AekeObservable<AekePowerCoreAdapter.PowerInfo> = AekeObservable()
    private val footBoardChanged: AekeObservable<Boolean> = AekeObservable()

    var isUnload: Boolean = false
        private set
    var isPinUnload: Boolean = false
        private set

    var currentPowerMode: AekePowerCoreAdapter.PowerMode = AekePowerCoreAdapter.PowerMode.STANDARD(2f)
        private set

    var currentPowerSetWeight: Float = 2f
        private set

    var isFootboardLocked = false
        private set

    private var expectWeightAndMode: AekePowerCoreAdapter.PowerMode? = null
    private var smoothingWeightAndMode: AekePowerCoreAdapter.PowerMode? = null

    private lateinit var mainHandler: Handler

    private var smoothStep: Float = SMOOTH_STEP

    private var powerProtectDialog: PowerAdjustProtectDialog? = null

    private var isLoadAutoManage = false

    private var mediaPlayer: MediaPlayer? = null

    private val smoothSetWeightAndMode: Runnable = Runnable {
        expectWeightAndMode?.let { expect ->
            smoothingWeightAndMode?.let { smoothing ->
                val offset = expect.weight - smoothing.weight
                if (smoothing.weight >= 2f && abs(offset) > smoothStep) {
                    if (offset > 0) {
                        smoothing.weight += smoothStep
                    } else {
                        smoothing.weight -= smoothStep
                    }
                    powerCore.setPower(smoothing)
                    mainHandler.removeCallbacksAndMessages("smoothSetWeigthAndMode")
                    handleSmoothingWeightAndMode()
                } else {
                    powerCore.setPower(expect)
                    smoothStep = SMOOTH_STEP
                }
            }
        }
    }
    private var isFirstLaunched = true

    fun init() {
        EventBus.getDefault().register(this)
        mainHandler = Handler(Looper.getMainLooper())
        powerCore = BenMoPowerCoreAdapterImpl()
        powerCore.init()
        powerCore.setPowerInfoTickCallback(callback = object : Consumer<AekePowerCoreAdapter.PowerInfo> {
            override fun accept(info: AekePowerCoreAdapter.PowerInfo) {
                val isNowLocked = info.m1TouchKey == 1 && info.m2TouchKey == 1
                if (isFootboardLocked != isNowLocked) {
                    isFootboardLocked = isNowLocked
                    footBoardChanged.setChanged()
                    footBoardChanged.notifyObservers(isNowLocked)
                    // 播放相应的音效
                    if (isFirstLaunched) {
                        logD("首次运行不需要播放踏板锁定提示音")
                        isFirstLaunched = false
                        return
                    }
                    playFoldboardSound(isNowLocked)
                }
                powerInfoChanged.setChanged()
                powerInfoChanged.notifyObservers(info)
            }
        })
        powerCore.setPowerErrorCodeListener {
            errorCodeChanged.setChanged()
            errorCodeChanged.notifyObservers(it)
        }
        /*observePowerModeChange(callback = object :AekeObserver<Pair<String,AekePowerCoreAdapter.PowerMode>>{
            private var prevMode:AekePowerCoreAdapter.PowerMode? = null
            override fun update(va lue: Pair<String,AekePowerCoreAdapter.PowerMode>) {
                if (value.second is AekePowerCoreAdapter.PowerMode.UNLOAD&&prevMode !is AekePowerCoreAdapter.PowerMode.UNLOAD){
                    unloadChanged.setChanged()
                    unloadChanged.notifyObservers(true)
                }else if(value.second !is AekePowerCoreAdapter.PowerMode.UNLOAD&&prevMode is AekePowerCoreAdapter.PowerMode.UNLOAD){
                    unloadChanged.setChanged()
                    unloadChanged.notifyObservers(false)
                }
                prevMode = value.second
            }
        })*/
    }

    fun setLoadAutoManage(auto: Boolean) {
        isLoadAutoManage = auto
    }

    fun getPowerInfo(): AekePowerCoreAdapter.PowerInfo {
        return powerCore.getPowerInfo()
    }

    /**
     * 获取 PowerControlModel 数据
     * 用于调试和显示详细的电机信息
     */
    fun getPowerControlModel(): PowerControlModelInterface? {
        return if (powerCore is BenMoPowerCoreAdapterImpl) {
            (powerCore as BenMoPowerCoreAdapterImpl).getPowerControlModel()
        } else {
            null
        }
    }

    fun setUnload(isSmooth: Boolean = true) {
        if (isUnload) {
            Log.i("NewPowerHelper", "setUnload skip")
            return
        }
        if (!isUnload) {
            unloadChanged.setChanged()
            unloadChanged.notifyObservers(true)
        }
        isUnload = true
        smoothingWeightAndMode = AekePowerCoreAdapter.PowerMode.STANDARD(currentPowerMode.weight)
        expectWeightAndMode = AekePowerCoreAdapter.PowerMode.UNLOAD(2.0f)
        if (isSmooth && powerCore.isSupportPowerSmooth()) {
            val smoothRate: Int = Math.round(currentPowerSetWeight / 0.5f)
            val mode = AekePowerCoreAdapter.PowerMode.STANDARD(2f, true, smoothRate)
            powerCore.setPower(mode)
        } else if (isSmooth && currentPowerMode.weight > 12) {
            smoothingWeightAndMode = AekePowerCoreAdapter.PowerMode.STANDARD(currentPowerMode.weight)
            expectWeightAndMode = AekePowerCoreAdapter.PowerMode.UNLOAD(2.0f)
            handleSmoothingWeightAndMode()
        } else {
            powerCore.setPower(AekePowerCoreAdapter.PowerMode.UNLOAD(2.0f))
        }
    }

    fun setUnload() {
        setUnload(true)
    }

    fun setActivate() {
        setActivate(true)
    }

    fun setActivate(isSmooth: Boolean = true) {
        Log.i("NewPowerHelper", "setActivate isSmooth:$isSmooth , isUnload:$isUnload , isPinUnload:$isPinUnload")
        if (!isUnload) {
            Log.i("NewPowerHelper", "setActivate skip")
            return
        }
        if (isUnload) {
            unloadChanged.setChanged()
            unloadChanged.notifyObservers(false)
        }
        isUnload = false
        if(isPinUnload){
            isPinUnload = false
            powerCore.setResetMode()
//            ToastHelper.showToast("原点已重置", 3000)
            Log.i("NewPowerHelper", "setActivate 原点重置")
        }
        smoothingWeightAndMode = AekePowerCoreAdapter.PowerMode.STANDARD(2.0f)
        expectWeightAndMode = currentPowerMode
        smoothStep = SMOOTH_STEP
        if (isSmooth && powerCore.isSupportPowerSmooth()) {
            handleSmoothingWeightAndMode()
        } else if (isSmooth && currentPowerMode.weight > 12) {
            smoothingWeightAndMode = AekePowerCoreAdapter.PowerMode.STANDARD(2.0f)
            expectWeightAndMode = currentPowerMode
            handleSmoothingWeightAndMode()
        } else {
            powerCore.setPower(currentPowerMode)
        }
    }

    internal fun setPowerInternal(
        powerMode: AekePowerCoreAdapter.PowerMode,
        isSmooth: Boolean = false,
        tag: String = "unknown",
        weightStep: Float = SMOOTH_STEP
    ) {
        Log.i("NewPowerHelper", "setPowerInternal: weight = ${powerMode}，isSmooth = $isSmooth")
        val powerMax: Float = if (ProductHelper.isSupportPowerOf50KG()) {
            50f
        } else {
            30f
        }
        if (powerMode.weight > powerMax) {
            powerMode.weight = powerMax
        } else if (powerMode.weight < 2f) {
            powerMode.weight = 2f
        }

        if (!isUnload) {
            if (isSmooth) {
                smoothingWeightAndMode = AekePowerCoreAdapter.PowerMode.STANDARD(currentPowerMode.weight)
            } else {
                mainHandler.removeCallbacksAndMessages("smoothSetWeigthAndMode")
            }
        }
        if (powerMode::class.java != currentPowerMode::class.java) {
            modeChanged.setChanged()
            modeChanged.notifyObservers(tag to powerMode)
        }
        currentPowerMode = powerMode
        powerMode.weight.let {
            //保留两位判断精度
            if (abs(it - currentPowerSetWeight) > 0.01) {
                currentPowerSetWeight = it
                weightChanged.setChanged()
                weightChanged.notifyObservers(tag to it)
            }
        }

        if (!isUnload) {
            if (isSmooth) {
                smoothStep = weightStep
                expectWeightAndMode = powerMode
                handleSmoothingWeightAndMode()
            } else {
                powerCore.setPower(powerMode)
            }
        }
    }

    /**
     * 设置电机重量和模式
     * kg
     * TODO 设置滑动设置重量
     */
    fun setPower(powerMode: AekePowerCoreAdapter.PowerMode, isSmooth: Boolean = false, tag: String = "unknown") {
        var internalSmooth: Boolean = isSmooth
        //减力
        if (currentPowerMode.weight > powerMode.weight) {
            if (currentPowerMode.weight <= 12) {
                internalSmooth = false
            }
        }
        //增力
        else {
            if (powerMode.weight <= 12) {
                internalSmooth = false
            }
        }

        if (!internalSmooth) {
            if (powerMode.weight - currentPowerMode.weight >= 20f) {
                if (powerProtectDialog?.isShowing != true) {
                    powerProtectDialog = PowerAdjustProtectDialog(
                        PowerModule.powerContext,
                        leftCallback = {
                            EventBus.getDefault().post(
                                AdjustWeightProtectResultEvent(
                                    currentPowerMode
                                )
                            )
                        }, rightCallback = {
                            EventBus.getDefault().post(
                                AdjustWeightProtectResultEvent(
                                    powerMode
                                )
                            )
                            setPowerInternal(powerMode, internalSmooth, tag)
                        })
                    powerProtectDialog?.show()
                }
                return
            }
        }
        setPowerInternal(powerMode, internalSmooth, tag)
    }

    fun setPower(weight: Float, isSmooth: Boolean = false, tag: String = "unknown") {
        Log.i("NewPowerHelper", "setPower: weight = ${weight}")
        val mode = currentPowerMode
        when (mode) {
            is AekePowerCoreAdapter.PowerMode.UNLOAD -> {

            }

            is AekePowerCoreAdapter.PowerMode.LiXin -> {
                setPower(AekePowerCoreAdapter.PowerMode.LiXin(weight), isSmooth, tag)
            }

            is AekePowerCoreAdapter.PowerMode.HuaChuan -> {
                setPower(AekePowerCoreAdapter.PowerMode.HuaChuan(weight), isSmooth, tag)
            }

            is AekePowerCoreAdapter.PowerMode.TanLi -> {
                setPower(AekePowerCoreAdapter.PowerMode.TanLi(weight), isSmooth, tag)
            }

            is AekePowerCoreAdapter.PowerMode.XiangXin -> {
                setPower(AekePowerCoreAdapter.PowerMode.XiangXin(weight), isSmooth, tag)
            }

            is AekePowerCoreAdapter.PowerMode.STANDARD -> {
                setPower(AekePowerCoreAdapter.PowerMode.STANDARD(weight), isSmooth, tag)
            }
        }
    }

    fun triggerUnloadProtect() {
        if (powerCore.isSupportPowerSmooth()) {
            val smoothRate: Int = (currentPowerSetWeight / 0.5f).roundToInt()
            val mode = AekePowerCoreAdapter.PowerMode.STANDARD(2f, true, smoothRate)
            currentPowerSetWeight = 2f
            powerCore.setPower(mode)
        } else {
            setPower(AekePowerCoreAdapter.PowerMode.STANDARD(2.0f), true)
        }
    }

    fun setPowerSmooth(
        powerMode: AekePowerCoreAdapter.PowerMode,
        smoothRate: Int,
        weightStep: Float = SMOOTH_STEP
    ) {
        if (powerCore.isSupportPowerSmooth()) {
            powerMode.weight.let {
                if (abs(it - currentPowerSetWeight) > 0.01) {
                    currentPowerSetWeight = it
                    weightChanged.setChanged()
                    weightChanged.notifyObservers("setPowerSmooth" to it)
                }
            }
            powerMode.isSmooth = true
            powerMode.smoothRate = smoothRate
            powerCore.setPower(powerMode)
        } else {
            setPowerInternal(
                powerMode,
                true,
                "setPowerSmooth",
                weightStep
            )
        }
    }

    fun getPowerModeType(): AekePowerCoreAdapter.PowerMode {
        return when (currentPowerMode) {
            is AekePowerCoreAdapter.PowerMode.UNLOAD -> {
                AekePowerCoreAdapter.PowerMode.STANDARD(2f)
            }

            is AekePowerCoreAdapter.PowerMode.LiXin -> {
                AekePowerCoreAdapter.PowerMode.LiXin(2f)
            }

            is AekePowerCoreAdapter.PowerMode.HuaChuan -> {
                AekePowerCoreAdapter.PowerMode.HuaChuan(2f)
            }

            is AekePowerCoreAdapter.PowerMode.TanLi -> {
                AekePowerCoreAdapter.PowerMode.TanLi(2f)
            }

            is AekePowerCoreAdapter.PowerMode.XiangXin -> {
                AekePowerCoreAdapter.PowerMode.XiangXin(2f)
            }

            is AekePowerCoreAdapter.PowerMode.STANDARD -> {
                AekePowerCoreAdapter.PowerMode.STANDARD(2f)
            }

            else -> {
                AekePowerCoreAdapter.PowerMode.STANDARD(2f)
            }
        }
    }

    private fun handleSmoothingWeightAndMode() {
        if (powerCore.isSupportPowerSmooth()) {
            val mode = expectWeightAndMode ?: return
            mode.isSmooth = true
            mode.smoothRate = 14
            powerCore.setPower(mode)
        } else {
            mainHandler.postDelayed(smoothSetWeightAndMode, "smoothSetWeigthAndMode", SMOOTH_PERIOD)
        }
    }

    /**
     * 获得电机版本,内部发送获取电机版本的指令,两秒后必须回调callback,不管电机版本是否正确获取
     */
    fun getPowerVersion(callback: Consumer<Long>) {
        powerCore.getPowerVersion(callback)
    }

    /**
     * 重启电机芯片程序
     */
    fun rebootPowerChip() {
        powerCore.rebootPowerChip()
    }

    /**
     * 移除电机的监听,callback为具体的观察者对象
     */
    fun removePowerObserver(callback: Any) {
        weightChanged.deleteObserver(callback)
        modeChanged.deleteObserver(callback)
        errorCodeChanged.deleteObserver(callback)
    }

    fun observeFootboardChange(owner: LifecycleOwner? = null, callback: AekeObserver<Boolean>) {
        owner?.lifecycle?.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(p0: LifecycleOwner, p1: Lifecycle.Event) {
                if (p1 == Lifecycle.Event.ON_DESTROY) {
                    footBoardChanged.deleteObserver(callback)
                }
            }
        })
        footBoardChanged.addObserver(callback)
    }


    fun observePowerInfoTickCallback(owner: LifecycleOwner? = null, callback: AekeObserver<AekePowerCoreAdapter.PowerInfo>) {
        owner?.lifecycle?.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(p0: LifecycleOwner, p1: Lifecycle.Event) {
                if (p1 == Lifecycle.Event.ON_DESTROY) {
                    powerInfoChanged.deleteObserver(callback)
                }
            }
        })
        powerInfoChanged.addObserver(callback)
    }

    /**
     * 电机模式变化回调,里面回调模式只有改变的时候才回调,相同模式的改变不回调
     * 数据方向 app->电机
     */
    fun observePowerModeChange(owner: LifecycleOwner? = null, callback: AekeObserver<Pair<String, AekePowerCoreAdapter.PowerMode>>) {
        owner?.lifecycle?.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(p0: LifecycleOwner, p1: Lifecycle.Event) {
                if (p1 == Lifecycle.Event.ON_DESTROY) {
                    modeChanged.deleteObserver(callback)
                }
            }
        })
        modeChanged.addObserver(callback)
    }

    /**
     * 电机重量变化回调,相同重量只回调一次
     * 数据方向 app->电机
     */
    fun observePowerWeightChange(owner: LifecycleOwner? = null, callback: AekeObserver<Pair<String, Float>>) {
        owner?.lifecycle?.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(p0: LifecycleOwner, p1: Lifecycle.Event) {
                if (p1 == Lifecycle.Event.ON_DESTROY) {
                    weightChanged.deleteObserver(callback)
                }
            }
        })
        weightChanged.addObserver(callback)
    }

    /**
     * 电机错误码回调
     * 错误码只有在变化时回调一次,相同错误码只回调一次,不重复回调
     * value==0时,说明电机恢复正常
     * 数据方向:电机->app
     */
    fun observerPowerErrorCode(owner: LifecycleOwner? = null, callback: AekeObserver<Int>) {
        owner?.lifecycle?.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(p0: LifecycleOwner, p1: Lifecycle.Event) {
                if (p1 == Lifecycle.Event.ON_DESTROY) {
                    errorCodeChanged.deleteObserver(callback)
                }
            }
        })
        errorCodeChanged.addObserver(callback)
    }

    /**
     * 电机卸力状态回调
     */
    fun observerPowerUnload(owner: LifecycleOwner? = null, callback: AekeObserver<Boolean>) {
        owner?.lifecycle?.addObserver(object : LifecycleEventObserver {
            override fun onStateChanged(p0: LifecycleOwner, p1: Lifecycle.Event) {
                if (p1 == Lifecycle.Event.ON_DESTROY) {
                    unloadChanged.deleteObserver(callback)
                }
            }
        })
        unloadChanged.addObserver(callback)
    }

    @Subscribe(threadMode = ThreadMode.MAIN)
    fun onBleDeviceButtonPressEvent(event: BleDeviceButtonPressEvent) {
        if (!isLoadAutoManage) {
            Log.w("NewPowerHelper", "load not auto manage")
            return
        }
        logD("NewPowerHelper", "onBleDeviceButtonPressEvent is isPinUnloader:${event.isPinUnloader}")
        if (event.isPinUnloader) {
            // 插销卸力器只处理卸力场景
            logD("NewPowerHelper", "插销卸力器 按键卸力, isUnload:${isUnload}")

            setUnload(true)
            isPinUnload = true
            return
        }
        if (ProductHelper.isS1Pro() && (!event.isLeftPinUnloaderOnline || !event.isRightPinUnloaderOnline)) {
            logD("NewPowerHelper", "S1Pro 插销卸力器 按键卸力, 左侧卸力器在线:${event.isLeftPinUnloaderOnline}, 右侧卸力器在线:${event.isRightPinUnloaderOnline} ，按键卸力拦截！")
            // toast 在 PowerSettingView 中处理
            return
        }
        logD("NewPowerHelper", "卸力按键激活, isUnload:${isUnload}")
        if (isUnload) {
            setActivate()
        } else {
            setUnload()
        }
    }

    @Subscribe(threadMode = ThreadMode.MAIN)
    fun onPinUnloaderBatteryEvent(event: PinUnloaderBatteryEvent) {
        // 电量变化不处理卸力激活力量，只在用户主动触发激活力量时判断低电量，拦截激活操作
        /*if (event.battery <= 10) {
            if (!isUnload) {
                logD("NewPowerHelper", "插销卸力器处理卸力")
                setUnload()
            }
        } else {
            if (isUnload) {
                setActivate()
            }
        }*/
    }

    internal fun stopSmoothingWeightAndMode() {
        mainHandler.removeCallbacksAndMessages("smoothSetWeigthAndMode")
    }

    fun isSupportPowerSmooth(): Boolean {
        return powerCore.isSupportPowerSmooth()
    }

    fun isSupportHandOffProtect(): Boolean {
        return powerCore.isSupportHandOffProtect()
    }

    fun setHandsOffProtect(enable: Boolean) {
        if (!powerCore.isSupportHandOffProtect()) {
            Log.w("NewPowerHelper", "not support motor hands off protect")
            return
        }
        powerCore.setHandsOffProtect(enable)
    }
    fun setBalanceMode(isOpen: Boolean) {
        powerCore.setBalanceMode(isOpen)
    }

    /**
     * 播放踏板音效
     * @param isLocked true: 锁定音效，false: 解锁音效
     */
    private fun playFoldboardSound(isLocked: Boolean) {
        try {
            // 停止当前播放
            mediaPlayer?.reset()
            mediaPlayer?.release()
            mediaPlayer = null

            // 根据锁定状态选择音效资源
            val soundResId = if (isLocked) {
                // 锁定音效
                R.raw.foldboard_locked
            } else {
                // 解锁音效
                R.raw.foldboard_unlock
            }

            // 创建并播放 MediaPlayer
            mediaPlayer = MediaPlayer.create(PowerModule.powerContext, soundResId)
            mediaPlayer?.setOnCompletionListener {
                it?.release()
                mediaPlayer = null
            }
            mediaPlayer?.start()

            ALog.d("NewPowerHelper", "playFoldboardSound: isLocked=$isLocked, resId=$soundResId")
        } catch (e: Exception) {
            ALog.e("NewPowerHelper", "playFoldboardSound error: ${e.message}")
        }
    }

}