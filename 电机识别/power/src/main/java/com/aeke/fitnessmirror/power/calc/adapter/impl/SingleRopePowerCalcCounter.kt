package com.aeke.fitnessmirror.power.calc.adapter.impl

import android.os.Handler
import android.os.Looper
import android.util.Log
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import java.util.Deque
import java.util.LinkedList
import kotlin.math.min

abstract class SingleRopePowerCalcCounter(open val powerType:AekePowerCoreAdapter.Power): IPowerCalcCounter {
    private lateinit var powerCalc: IPowerRopeWaveCalc

    //平均做功绳子长度
    private val doWorkAvgRopeLengthObservable: AekeObservable<Pair<Int,Int>> = AekeObservable()
    //做功计次增量
    private val doWorkCalcCountObservable: AekeObservable<Int> = AekeObservable()
    //做功w
    private val doWorkCalcDataObservable: AekeObservable<IPowerCalcCounter.DoWokeData> = AekeObservable()

    //起点
    var initStartPoint:Int = 0
    //行程
    var initDistance:Int = Int.MAX_VALUE

    private var initDistanceRopeData:Deque<IPowerRopeWaveCalc.RopeWaveData> = LinkedList()

    private var isStartCalc:Boolean = false

    private lateinit var config: PowerCalcConfig

    private val mMainHandler:Handler = Handler(Looper.getMainLooper())

    /*
    * 1.没有初始行程时计算初始行程 -计次加2
    * 2.有初始行程时，进行初始/起点 重置逻辑判断,重新定义初始行程 -计次加3
    * 3.暂停时触发起点重置
    * */
    private val calcInitDistance:java.util.function.Function<IPowerRopeWaveCalc.RopeWaveData,Boolean> = object :java.util.function.Function<IPowerRopeWaveCalc.RopeWaveData,Boolean>{

        /*
        * return true:通过  false:不通过
        * */
        override fun apply(value: IPowerRopeWaveCalc.RopeWaveData): Boolean {
            if (value.dy<0){
                return true
            }
            //出现暂停
            if (value.dy==0){
                initStartPoint = value.endLength
                initDistanceRopeData.clear()
            }else{
                //没有设置初始行程,走1逻辑
                if (initDistance ==Int.MAX_VALUE){
                    initDistanceRopeData.add(value)
                    if (initDistanceRopeData.size==2){
                        val first = initDistanceRopeData.pop()
                        val second = initDistanceRopeData.pop()
                        //20% TODO 起点差值偏差
                        if (withinTolerance(first.startLength,second.startLength,config.START_POINT_THRESHOLD)){
                            if (withinTolerance(first.dy,second.dy,config.DISTANCE_THRESHOLD)){
                                //符合初始行程定义
                                initDistance = (second.dy+first.dy)/2
                                initStartPoint = (second.startLength+first.startLength)/2
                                //TODO 转发初始计次
                                /*postRopeCalcEvent(2)
                                postDoWorkEvent(arrayOf(first,second))
                                postAvgRopeLengthEvent(initDistance)*/
                                onConfirmInitDistanceAndStartPoint(first,second)
                                return false
                            }
                        }
                        initDistanceRopeData.add(value)
                    }
                    return false
                }
                //已经计算了初始行程
                else{
                    initDistanceRopeData.add(value)
                    if (initDistanceRopeData.size==2){
                        val first = initDistanceRopeData.pop()
                        val second = initDistanceRopeData.pop()
                        //first second向心离心起点都符合要求,third仅仅向心符合要求

                        /*
                        * TODO 产品只对初始行程进行定义,不对起点进行定义
                        *  两侧绳子行程的定义
                        *  初始行程的定义和两边绳子判断的冲突
                        * */
                        if (withinTolerance(first.startLength,second.startLength,config.START_POINT_THRESHOLD)){
                            if (withinTolerance(first.dy,second.dy,config.DISTANCE_THRESHOLD)){
                                if (allBelowThreshold(first.dy,second.dy,initDistance* initDistance*config.DISTANCE_EFFECTIVE_THRESHOLD)|| min(first.dy,second.dy) > initDistance*config.DISTANCE_RESET_THRESHOLD){
                                    initStartPoint = (first.startLength+second.startLength)/2
                                    initDistance = ((first.dy+second.dy)/2)
                                    //TODO 转发初始计次
                                    /*postRopeCalcEvent(3)
                                    postDoWorkEvent(arrayOf(first,second,third))
                                    postAvgRopeLengthEvent(initDistance)
                                    return false*/
                                }
                            }
                        }
                        initDistanceRopeData.add(second)
                        //initDistanceRopeData.add(third)
                    }
                }
            }
            return true
        }
    }

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        this.config = config
        this.powerCalc = powerRopeWaveCalc
        this.powerCalc.init(config, ropeGetter)
        powerCalc.observeRopeLength(object :AekeObserver<Long>{
            override fun update(value: Long) {
                onFps(value)
            }
        })
        //TODO 实现观察激活点
        powerCalc.observeRopeWaveType(object :AekeObserver<IPowerRopeWaveCalc.RopeWaveData>{
            override fun update(value: IPowerRopeWaveCalc.RopeWaveData) {
                /*if (!isStartCalc){
                    return
                }*/
                if (value.type!=powerType){
                    return
                }
                /*
                * TODO 产品定义:两根绳子行程如何判断产品定义不清晰
                * */
                /*if (value.dy < 0) {
                    //不处理离心行程
                    return
                }*/
                //val distance = initDistance
                /*if (!calcInitDistance.apply(value)||initDistance==Int.MAX_VALUE){
                    return
                }*/
                onHandlePowerCalcCount(value)
            }
        })
    }

    protected open fun onFps(value: Long) {

    }

    protected fun onConfirmInitDistanceAndStartPoint(first: IPowerRopeWaveCalc.RopeWaveData,second: IPowerRopeWaveCalc.RopeWaveData,){

    }

    protected abstract fun onHandlePowerCalcCount(value: IPowerRopeWaveCalc.RopeWaveData)

    override fun observeRopeLength(callback: AekeObserver<Long>): () -> Unit {
        return powerCalc.observeRopeLength(callback)
    }

    override fun stopCalcCount() {
        isStartCalc = false
        powerCalc.postTask{
            initDistanceRopeData = LinkedList()
            initStartPoint = 0
            initDistance = Int.MAX_VALUE
        }
    }

    override fun startCalcCount() {
        isStartCalc = true
        powerCalc.postTask{
            //TODO 产品定义:双侧绳子取那个?产品未定义
            initDistanceRopeData = LinkedList()
            initStartPoint = 0
            initDistance = Int.MAX_VALUE
        }
    }

    override fun observeDoWorkAvgRopeLength(callback: AekeObserver<Pair<Int,Int>>): () -> Unit {
        doWorkAvgRopeLengthObservable.addObserver(callback)
        return {
            doWorkAvgRopeLengthObservable.deleteObserver(callback)
        }
    }

    override fun observeDoWorkCalcCountData(callback: AekeObserver<Int>): () -> Unit {
        doWorkCalcCountObservable.addObserver(callback)
        return {
            doWorkCalcCountObservable.deleteObserver(callback)
        }
    }

    override fun observeDoWorkCalcDataData(callback: AekeObserver<IPowerCalcCounter.DoWokeData>): () -> Unit {
        doWorkCalcDataObservable.addObserver(callback)
        return {
            doWorkCalcDataObservable.deleteObserver(callback)
        }
    }

    protected fun log(msg:String){
        Log.d("SimplePowerCalcCounter",msg)
    }

    protected fun withinTolerance(a: Int, b: Int, tolerance: Float): Boolean {
        val max = maxOf(a, b)
        val min = minOf(a, b)
        // 防止除以零异常
        if (min == 0) return false
        // 最大相对差值是否在容忍范围内
        return (max - min).toDouble() / min < tolerance
    }

    protected fun allBelowThreshold(a: Int, b: Int, base: Float): Boolean {
        return a<base&&b<base
    }

    override fun release() {
        doWorkAvgRopeLengthObservable.deleteObservers()
        doWorkCalcCountObservable.deleteObservers()
        doWorkCalcDataObservable.deleteObservers()
        powerCalc.release()
    }

    override fun switchHandShankMode(isImmediatelyStartCalc: Boolean) {
        TODO("Not yet implemented")
    }

    override fun switchCrossBarMode(isImmediatelyStartCalc: Boolean) {
        TODO("Not yet implemented")
    }

    override fun observeDoWorkCalcCountTypeData(callback: AekeObserver<Pair<AekePowerCoreAdapter.Power?,IPowerCalcCounter.CountType>>): () -> Unit {
        TODO("Not yet implemented")
    }

    override fun observeConfirmInitDistanceAndStartPoint(callback: AekeObserver<Pair<Int,Int>>): () -> Unit {
        TODO("暂不实现")
    }
}