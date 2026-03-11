package com.aeke.fitnessmirror.power.calc.adapter.impl

import android.os.Handler
import android.os.Looper
import android.util.Log
import androidx.lifecycle.Lifecycle
import androidx.lifecycle.LifecycleOwner
import androidx.lifecycle.LifecycleRegistry
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.aekeLifeScope
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.calc.adapter.SimplePowerRopeWaveCalc
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlin.coroutines.resume
import kotlin.math.abs

/**
 * 运动测评力量测试相关
 */
class StrengthTestRopePowerCalcCounter(val threshold:Float = 0.9f): OldDoubleRopePowerCalcCounter(),LifecycleOwner {

    companion object {
        const val TAG = "StrengthTestRopePowerCalcCounter"
    }

    private var life:LifecycleRegistry = LifecycleRegistry(this)

    //--------------力量测评初始界面逻辑函数
    //确定第一个向心行程
    //UI:展示第一个柱子
    //只有在初始界面确定了行程后才会回调一次,后面不会再回调
    var callbackInitConfirmFirstXiangXinEvent:((Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>)->Unit)? = null

    var callbackCompareRopeErrorEvent:(()->Unit)? = null

    //确定初始行程
    //跳转力量测评界面
    //只有在初始界面确定了行程后才会回调一次,后面不会再回调
    var callbackInitConfirmDistanceAndStartPointEvent:((Pair<Int, Int>)->Unit)? = null
    //绳子返回了起点
    //只有在初始界面确定了行程后才会回调一次,后面不会再回调
    var callbackInitRopeReturnStartPoint:(()->Unit)? = null
    //--------------力量测评初始界面逻辑函数

    //初始结束后,上面的函数都不会回调

    //--------------力量测评开始界面逻辑函数
    var callbackUICountDownShow:(()->Unit)? = null
    var callbackTestActionResult:((StrengthTestActionStatusBean)->Unit)? = null

    var callbackTestActionEndReturnStartPoint:((actionIsSuccess:Boolean)->Unit)? = null

    /**
     * 动作失败后会回调
     * true:回到原点以下,用于隐藏警告
     * false:回到原点以上,用于触发回到超出原点警告
     */
    var callbackTestActionFailRopeStartPointState:((Boolean)->Unit)? = null
    //--------------力量测评开始界面逻辑函数
    private val xxDistanceEventObservable: AekeObservable<Pair<Long, Long>> = AekeObservable()

    private var isStartAutoManage:Boolean = false

    private var job:Job? = null

    private var initCallbackDestroy:(()->Unit)? =  null

    private var lastRopeLength = -1L
    private var xxStartPoint = -1L
    private var xxStartTime = 0L
    private var ropeDecreasing = false
    private var startDecreasingPoint = -1L
    private var destroyCallback: (() -> Unit)? = null
    private var ropeEventDestroyCallback: (() -> Unit)? = null
    var isInCountDown = false
    var isCountSuccess = false
    var isResting = false

    /**
     * 单位 m/s
     */
    var currentXxSpeed: Float = 0f

    override fun init(config: PowerCalcConfig, powerRopeWaveCalc: IPowerRopeWaveCalc, ropeGetter: IRopeGetter) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        life.handleLifecycleEvent(Lifecycle.Event.ON_RESUME)
        ropeEventDestroyCallback = super.observeRopeEvent(object : AekeObserver<Pair<Long, Long>> {
            override fun update(value: Pair<Long, Long>) {
                val avgDistance = (value.first + value.second) / 2
                if (multiInitDistance == Int.MAX_VALUE) {
                    lastRopeLength = avgDistance
                    return
                }
                if (lastRopeLength in 1 until avgDistance && ropeDecreasing) {
                    xxStartPoint = lastRopeLength
                    ropeDecreasing = false
                } else if (lastRopeLength > avgDistance && startDecreasingPoint < 0) {
                    startDecreasingPoint = avgDistance
                }
                if (avgDistance > lastRopeLength) {
                    startDecreasingPoint = -1
                }
                if (startDecreasingPoint > 0) {
                    val decreasingDistance = abs(avgDistance - startDecreasingPoint)
                    if (decreasingDistance > 10) {
                        ropeDecreasing = true
                    }
                }
                if (xxStartPoint > 0L && xxStartTime > 0L && !ropeDecreasing) {
                    val xxDistance = avgDistance - xxStartPoint
                    currentXxSpeed = (1f * xxDistance / (System.currentTimeMillis() - xxStartTime))*10
                }
                lastRopeLength = avgDistance
                if (xxStartPoint > 0L) {
                    xxDistanceEventObservable.setChanged()
                    xxDistanceEventObservable.notifyObservers(Pair(value.first - xxStartPoint, value.second - xxStartPoint))
                }
            }
        })
    }

    private fun initStrengthTestOption(){
        if (multiInitDistance==Int.MAX_VALUE){
            val callback1 = this.observeRopeXxLxPauseEvent(object : AekeObserver<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>> {
                override fun update(value: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>) {
                    if (value.second.dy>0){
                        this@StrengthTestRopePowerCalcCounter.deleteObserver(this)
                        log("确定第一个向心行程")
                        callbackInitConfirmFirstXiangXinEvent?.invoke(value)
                    }
                }
            })
            val callback2 = this.observeConfirmInitDistanceAndStartPoint(object : AekeObserver<Pair<Int, Int>> {
                override fun update(value: Pair<Int, Int>) {
                    log("确定行程和起点")
                    this@StrengthTestRopePowerCalcCounter.deleteObserver(this)
                    callbackInitConfirmDistanceAndStartPointEvent?.invoke(value)
                    Handler(Looper.getMainLooper()).post {
                        onHandleStrengthTest()
                    }
                }
            })
            initCallbackDestroy = {
                callback1()
                callback2()
            }
        }else{
            Handler(Looper.getMainLooper()).post {
                onHandleStrengthTest()
            }
        }
    }

    fun countDownStart() {
        isInCountDown = true
        isCountSuccess = false
        currentXxSpeed  = 0f
        xxStartTime = System.currentTimeMillis()
    }

    fun countDownEnd() {
        isInCountDown = false
        xxStartTime = 0
        if (!isCountSuccess) {
            callbackTestActionResult?.invoke(StrengthTestActionStatusBean(false, null))
            NewPowerHelper.triggerUnloadProtect()
        }
    }

    fun resetCountDown() {
        isInCountDown = false
        isCountSuccess = false
        xxStartTime = 0
    }

    fun initializeStartPoint() {
        xxStartPoint = lastRopeLength
    }

    private fun onHandleStrengthTest() {
        job = aekeLifeScope.launch({
            log("开始停止")
            SimplePowerRopeWaveCalc.isPause = true
            while (!isStartAutoManage) {
                delay(200)
            }
            log("结束停止")
            SimplePowerRopeWaveCalc.isPause = false
            //做了一组
            val callback = this@StrengthTestRopePowerCalcCounter.observeRopeXxDistance(object :
                AekeObserver<Pair<Long, Long>> {
                override fun update(value: Pair<Long, Long>) {
                    if (!isInCountDown || isResting) {
                        return
                    }
                    if (value.first >= threshold * multiInitDistance && value.second >= threshold * multiInitDistance) {
                        log("动作回调111")
                        isCountSuccess = true
                    }
                }

            })

           val callback2 = this@StrengthTestRopePowerCalcCounter.observeDoWorkCalcDataData(object :
                AekeObserver<IPowerCalcCounter.DoWokeData> {
                override fun update(value: IPowerCalcCounter.DoWokeData) {
                    if (isResting) {
                        return
                    }
                    if (value.value2 != null) {
                        if (isCountSuccess) {
                            log("动作回调222")
                            callbackTestActionResult?.invoke(
                                StrengthTestActionStatusBean(
                                    true,
                                    value
                                )
                            )
                        } else {
                            log("动作回调333")
                            callbackTestActionResult?.invoke(
                                StrengthTestActionStatusBean(
                                    false,
                                    value
                                )
                            )
                            NewPowerHelper.triggerUnloadProtect()
                        }
                        isInCountDown = false
                    }
                }
            })
            destroyCallback = {
                callback.invoke()
                callback2.invoke()
            }
        }, onFinally = {

        })
    }

    fun startStrengthTestAutoManage(){
        isStartAutoManage = true
    }

    override fun onCompareRopeWaveDataError() {
        super.onCompareRopeWaveDataError()
        callbackCompareRopeErrorEvent?.invoke()
    }


    override fun isSupportResetDistance(): Boolean {
        return false
    }

    override fun isSupportResetPoint(): Boolean {
        return false
    }

    override fun isSatisfyCalc(value: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>): Boolean {
        val dy = value.second.dy
        val initDistance: Int = multiInitDistance
        return abs(dy) > initDistance * 0.6
    }

    override fun release() {
        super.release()
        log("release")
        callbackTestActionResult  = null
        callbackTestActionEndReturnStartPoint  = null
        callbackTestActionFailRopeStartPointState  = null
        callbackInitRopeReturnStartPoint  = null
        callbackInitConfirmFirstXiangXinEvent  = null
        callbackInitConfirmDistanceAndStartPointEvent  = null
        callbackCompareRopeErrorEvent = null
        callbackUICountDownShow = null
        destroyCallback?.invoke()
        ropeEventDestroyCallback?.invoke()
        life.handleLifecycleEvent(Lifecycle.Event.ON_DESTROY)
    }

    override fun getLifecycle(): Lifecycle {
        return life
    }

    override fun stopCalcCount() {
        val isStart = isStartCalc
        super.stopCalcCount()
        if (isStart){
            job?.cancel()
            initCallbackDestroy?.invoke()
        }
    }

    override fun startCalcCount() {
        val isStart = isStartCalc
        super.startCalcCount()
        if (!isStart){
            initStrengthTestOption()
        }
    }

    override fun observeFromRopeStartPointDy(callback: AekeObserver<Pair<Long, Long>>): () -> Unit {
        return super.observeFromRopeStartPointDy(object : AekeObserver<Pair<Long, Long>> {
            override fun update(value: Pair<Long, Long>) {
                callback.update(value)
            }
        })
    }

    fun observeRopeXxDistance(callback: AekeObserver<Pair<Long, Long>>): () -> Unit {
        xxDistanceEventObservable.addObserver(callback)
        return {
            xxDistanceEventObservable.deleteObserver(callback)
        }
    }

    /**
     * 设置重量,单位kg
     * 内部自动缓速逻辑
     */
    fun setPower(weight: Float) {
        log("setPower weight = $weight")
        val EPSILON = 0.001f
        if (abs(weight - NewPowerHelper.currentPowerSetWeight) < EPSILON) {
            log("setPower weight = $weight, considered same as current: ${NewPowerHelper.currentPowerSetWeight}")
            return
        }
        NewPowerHelper.setPowerSmooth(AekePowerCoreAdapter.PowerMode.STANDARD(weight), 28, 5f)
    }

    data class StrengthTestActionStatusBean(val state:Boolean, val doWrokData:IPowerCalcCounter.DoWokeData?){
        //力量测评阶段此次状态向心时间,单位秒
        val timeXiangXin:Float by lazy {
            if (doWrokData==null){
                0f
            }else{
                val xiangXin1:Float = doWrokData.value1.second.let {
                    (it.end-it.start)/10f
                }
                val xiangXin2:Float = doWrokData.value2?.second?.let {
                    (it.end-it.start)/10f
                }?:0f
                (xiangXin1+xiangXin2)/2
            }
        }

        //未完成原因
        //超时未完成
        val isTimeoutNoComplete:Boolean = doWrokData==null
        //行程未达到阈值
        val isDistanceNoComplete:Boolean = !state&&!isTimeoutNoComplete

    }

    override fun isSupportHandsOffProtect(): Boolean {
        return false
    }

    private fun log(msg:String){
        Log.i(TAG,msg)
    }

}