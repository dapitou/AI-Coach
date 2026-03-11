package com.aeke.fitnessmirror.power.calc.adapter

import android.util.Log
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import java.util.ArrayList
import java.util.LinkedList
import java.util.Queue
import java.util.concurrent.LinkedBlockingDeque
import java.util.function.BiConsumer
import kotlin.math.abs
import kotlin.math.sign

class SimplePowerRopeWaveCalc() : IPowerRopeWaveCalc {

    companion object{
        var isPause:Boolean = false
    }

    //常量配置-------------------------------------------------------
    private var loopTime: Long = 100
    //常量配置-------------------------------------------------------

    private var isInit:Boolean = false

    val ropeWaveObservable: AekeObservable<IPowerRopeWaveCalc.RopeWaveData> = AekeObservable()

    val ropeObservable: AekeObservable<Long> = AekeObservable()

    private val endTask:Queue<Runnable> = LinkedBlockingDeque<Runnable>()

    //从零开始
    private var frame:Long = -1
    //存储绳子长度实时变化数据
    override val ropeData: LinkedList<Long> = LinkedList()
    override val weightData: LinkedList<Long> = LinkedList()
    override val currentFrameNumber: Long
        get(){
            return frame
        }

    @Volatile
    private var isStop:Boolean = false
    private lateinit var ropeGetter: IRopeGetter

    private lateinit var config: PowerCalcConfig

    private lateinit var left0PointCalc: Rope0PointCalcer

    private lateinit var right0PointCalc: Rope0PointCalcer

    private val loopRopeThread: Thread = object : Thread() {

        override fun run() {
            var rope:Long
            var weight:Long
            var frameNumber:Long
            var leftLength:Long
            var rightLength:Long
            var leftWeight:Long
            var rightWeight:Long
            while (!isStop) {
                if (isPause){
                    Thread.sleep(loopTime)
                    continue
                }
                leftLength = ropeGetter.getLeftRopeLength()
                rightLength = ropeGetter.getRightRopeLength()
                leftWeight = NewPowerHelper.getPowerInfo().ropeLeftWeight.toLong()
                rightWeight = NewPowerHelper.getPowerInfo().ropeRightWeight.toLong()
                frameNumber = getFrameNumber()
                //未确定波峰波谷类型
                rope = PowerRopeUtils.createRopeLongData(leftLength, rightLength, frameNumber)
                weight = PowerRopeUtils.createWeightLongData(leftWeight,rightWeight)
                ropeData.add(rope)
                weightData.add(weight)
                ropeObservable.setChanged()
                ropeObservable.notifyObservers(rope)
                //log("rope frameNumber:${frameNumber} leftLength:${leftLength} rightLength:${rightLength}")
                left0PointCalc.calc(leftLength,frameNumber,rope)
                right0PointCalc.calc(rightLength,frameNumber,rope)
                while (endTask.isNotEmpty()){
                    endTask.poll()?.run()
                }
                sleep(loopTime)
            }
            ropeData.clear()
            weightData.clear()
        }
    }

    override fun init(config: PowerCalcConfig, ropeGetter: IRopeGetter) {
        if (isInit){
            return
        }
        isInit = true
        this.config = config
        this.ropeGetter = ropeGetter

        left0PointCalc = Rope0PointCalcer(config) {
            postWaveTypeEvent(AekePowerCoreAdapter.Power.LEFT,it)
        }
        right0PointCalc = Rope0PointCalcer(config) {
            postWaveTypeEvent(AekePowerCoreAdapter.Power.RIGHT,it)
        }

        loopTime = 1000L / config.fps
        if (!loopRopeThread.isAlive) {
            loopRopeThread.start()
        }
    }

    override fun postTask(task: Runnable) {
        endTask.add(task)
    }

    override fun pause() {
        isPause = true
        postTask{
            left0PointCalc.reset()
            right0PointCalc.reset()
        }
    }

    override fun resume() {
        isPause = false
        postTask{
            left0PointCalc.reset()
            right0PointCalc.reset()
        }

    }

    override fun observeRopeWaveType(callback: AekeObserver<IPowerRopeWaveCalc.RopeWaveData>): () -> Unit {
        ropeWaveObservable.addObserver(callback)
        return {
            ropeWaveObservable.deleteObserver(callback)
        }
    }

    override fun observeRopeLength(callback: AekeObserver<Long>): () -> Unit {
        ropeObservable.addObserver(callback)
        return {
            ropeObservable.deleteObserver(callback)
        }
    }

    override fun release() {
        isStop = true
        ropeWaveObservable.deleteObservers()
        ropeObservable.deleteObservers()
    }

    private fun getFrameNumber():Long{
        return frame++
    }

    /**
     * type true:左电机  false:右电机
     */
    private fun postWaveTypeEvent(type: AekePowerCoreAdapter.Power, rope: IPowerRopeWaveCalc.RopeTriple){
        ropeWaveObservable.setChanged()
        ropeWaveObservable.notifyObservers(
            IPowerRopeWaveCalc.RopeWaveData(
                type,
                rope.start,
                rope.end,
                rope.dy,
                ropeData[rope.start],
                ropeData[rope.end]
            ).apply {
                this.childrens = rope.childrens?.map {
                    IPowerRopeWaveCalc.RopeWaveData(type, it.start, it.end, it.dy,ropeData[it.start],ropeData[it.end])
                }
            }
        )
    }

}

private fun log(msg:String){
    Log.d("SimplePowerRopeWaveCalc",msg)
}

private class Rope0PointCalcer(val config:PowerCalcConfig,val point0Callback:(IPowerRopeWaveCalc.RopeTriple)->Unit){
    //偏差抖动阈值 cm
    private val OFFSET:Long = config.OFFSET
    //判断暂停阈值 以帧为单位,若2s为阈值,10fps,则是20帧
    private var PAUSE_FRAME_THRESHOLD:Int = config.PAUSE_FRAME_THRESHOLD
    //极点阈值
    private var POINT_0_FRAME_THRESHOLD:Int = config.POINT_0_FRAME_THRESHOLD
    private var currentSum = 0  // 累计dy
    private var currentType: Int? = null  // 记录当前dy趋势（1: 正，-1: 负，0: 暂停）
    private var startFrame = -1  // 累加开始帧

    private var prevLength:Long = Long.MAX_VALUE

    val leftIncrementData: ArrayList<IPowerRopeWaveCalc.RopeTriple> = ArrayList()  // (startFrame, endFrame, dySum)

    private var currentRopeTriple: IPowerRopeWaveCalc.RopeTriple? = null

    fun reset(){
        currentSum = 0
        currentType = null
        startFrame = -1
        prevLength = Long.MAX_VALUE
        leftIncrementData.clear()
        currentRopeTriple = null
    }

    /*
    合并增减量,确定有效波峰波谷暂停
    逻辑如下:
    出现暂停帧数小于FRAME_VALUE,则将前面的同向数据(同向数据中出现不同向的数据,或者出现暂停帧数大于或等于FRAME_VALUE,则中止合并同向数据)包括小于FRAME_VALUE的暂停的帧数合并,视为一直同向
    */
    private val compressPoint0CalcRunnable: BiConsumer<ArrayList<IPowerRopeWaveCalc.RopeTriple>, IPowerRopeWaveCalc.RopeTriple> =
        object : BiConsumer<ArrayList<IPowerRopeWaveCalc.RopeTriple>, IPowerRopeWaveCalc.RopeTriple> {

            private var lastMaxDistanceRopeTriple: IPowerRopeWaveCalc.RopeTriple? = null

            override fun accept(incrementData: ArrayList<IPowerRopeWaveCalc.RopeTriple>, currentRopeTriple: IPowerRopeWaveCalc.RopeTriple) {
                //如果当前是零点,并且leftIncrementData最后一个也是零点,判断是否暂停
                val last = incrementData.lastOrNull()?:return
                if (currentRopeTriple.dy==0){
                    if (last.dy==0){
                        if (currentRopeTriple.end - last.start + 1 == POINT_0_FRAME_THRESHOLD) {
                            calcWaveHighLow(incrementData,currentRopeTriple)
                        }else{
                            calcPauseFrame(incrementData,currentRopeTriple)
                        }
                    }else{
                        if (currentRopeTriple.end - currentRopeTriple.start + 1 == PAUSE_FRAME_THRESHOLD){
                            calcPauseFrame(incrementData,currentRopeTriple)
                        } else if (currentRopeTriple.end - currentRopeTriple.start + 1 == POINT_0_FRAME_THRESHOLD) {
                            calcWaveHighLow(incrementData,currentRopeTriple)
                        }
                    }
                }
                //如果当前abs(dy)是>=OFFSET
                else if (abs(currentRopeTriple.dy)>=OFFSET){
                    calcWaveHighLow(incrementData,currentRopeTriple)
                }

            }

            private fun calcPauseFrame(leftIncrementData: ArrayList<IPowerRopeWaveCalc.RopeTriple>, currentRopeTriple: IPowerRopeWaveCalc.RopeTriple) {
                val last = leftIncrementData.lastOrNull()?:return
                if (currentRopeTriple.end-last.start+1>=PAUSE_FRAME_THRESHOLD){
                    //log("可判定暂停")
                    //判断暂停之前发出波峰波谷为判断事件
                    //TODO 看产品需不需要这个逻辑,不需要注释这段就行
                    //calcWaveHighLow(leftIncrementData,currentRopeTriple)
                    point0Callback(
                        IPowerRopeWaveCalc.RopeTriple(
                            last.end,
                            currentRopeTriple.end,
                            0
                        )
                    )
                    leftIncrementData.clear()
                    lastMaxDistanceRopeTriple = null
                }else{
                    //log("不判定暂停")
                }
            }

            private fun calcWaveHighLow(leftIncrementData: ArrayList<IPowerRopeWaveCalc.RopeTriple>, currentRopeTriple: IPowerRopeWaveCalc.RopeTriple){
                val maxDistanceRopeTriple = getRecentlyMaxDistance(leftIncrementData,PAUSE_FRAME_THRESHOLD)
                
                // 添加诊断日志：记录波峰波谷判定过程
                log("calcWaveHighLow - maxDy:${maxDistanceRopeTriple.dy} currentDy:${currentRopeTriple.dy} maxStart:${maxDistanceRopeTriple.start} maxEnd:${maxDistanceRopeTriple.end} incrementDataSize:${leftIncrementData.size}")
                
                if (lastMaxDistanceRopeTriple?.end!=maxDistanceRopeTriple.end){
                    /*
                    * TODO 出现达到暂停阈值时确定波谷目前有问题,后续要改应该着重改这里
                    * */
                    if (maxDistanceRopeTriple.dy!=0&&maxDistanceRopeTriple.dy.sign!=currentRopeTriple.dy.sign){
                        //波峰波谷数据
                        val rope = maxDistanceRopeTriple.copy()
                        if (maxDistanceRopeTriple.dy<0){
                            //TODO 波谷目前判断不精确,看后面需求变化,目前不需要离心功率
                            log("判定波谷 start:${rope.start} end:${rope.end} dy:${rope.dy} frameCount:${rope.end-rope.start}")
                            //getRecentlyMaxDistance(leftIncrementData,PAUSE_FRAME_THRESHOLD)
                        }else{
                            log("判定波峰 start:${rope.start} end:${rope.end} dy:${rope.dy} frameCount:${rope.end-rope.start}")
                        }
                        val childStart = leftIncrementData.indexOfFirst { it.start==rope.start }
                        val childEnd = leftIncrementData.indexOfLast { it.end==rope.end }
                        val childrens = mutableListOf<IPowerRopeWaveCalc.RopeTriple>()
                        for (i in childStart..childEnd){
                            childrens.add(leftIncrementData[i])
                        }
                        
                        // 添加诊断日志：记录子段信息
                        log("  子段数量:${childrens.size} 详情:${childrens.joinToString { "(${it.start}-${it.end},dy=${it.dy})" }}")
                        
                        rope.childrens = childrens
                        point0Callback(rope)
                        lastMaxDistanceRopeTriple = maxDistanceRopeTriple
                    } else {
                        log("  跳过判定 - maxDy符号:${maxDistanceRopeTriple.dy.sign} currentDy符号:${currentRopeTriple.dy.sign}")
                    }
                } else {
                    log("  跳过判定 - lastMaxEnd:${lastMaxDistanceRopeTriple?.end} == maxEnd:${maxDistanceRopeTriple.end}")
                }
            }

            /*
            * TODO 处理这个值的正确
            * 倒序获得一个值
            * 向前遍历一个同方向的数据一直累加,直到遇到不同方向的数据(不包括暂停)或者遇到连续暂停达到阈值的数据,如果遇到暂停,则判定为结束遍历,返回开始帧和结束帧,和累加值
            * */
            private fun getRecentlyMaxDistance(leftIncrementData: ArrayList<IPowerRopeWaveCalc.RopeTriple>, frameThreshold: Int): IPowerRopeWaveCalc.RopeTriple {
                var (start,end,dy) = leftIncrementData.last().copy()
                
                // 添加诊断日志：记录初始状态
                log("  getRecentlyMaxDistance开始 - lastData:(${start}-${end},dy=${dy}) dataSize:${leftIncrementData.size}")
                
                //达到判断暂停帧,直接返回
                if (dy==0&&(end-start+1)>=frameThreshold){
                    log("  达到暂停帧阈值,直接返回")
                    return IPowerRopeWaveCalc.RopeTriple(start, end, dy)
                }
                var dySign = dy.sign
                var mergedCount = 1
                for (i in leftIncrementData.size - 2 downTo 0) {
                    val (startFrame,endFrame,currentDy) = leftIncrementData[i]
                    if (currentDy==0){
                        //达到判断暂停帧,直接返回
                        if ((endFrame-startFrame+1)>=frameThreshold){
                            log("  遇到暂停帧阈值,停止合并 at index:$i")
                            break
                        }else{
                            log("  跳过小暂停 at index:$i frames:${endFrame-startFrame+1}")
                            continue
                        }
                    }
                    //初始为0时,一直找到上升和下降态,然后设置
                    if (dySign==0){
                        dySign = currentDy.sign
                        end = endFrame
                        log("  初始dySign设置为:${dySign}")
                    }
                    //同向累加
                    if (currentDy.sign==dySign){
                        dy+=currentDy
                        start = startFrame
                        mergedCount++
                        log("  合并同向数据 index:$i (${startFrame}-${endFrame},dy=${currentDy}) 累计dy:${dy}")
                    }
                    //非同向直接返回
                    else{
                        log("  遇到反向数据,停止合并 at index:$i currentDySign:${currentDy.sign} vs dySign:${dySign}")
                        break
                    }
                }
                log("  getRecentlyMaxDistance结束 - 合并了${mergedCount}段 最终:(${start}-${end},dy=${dy}) frameCount:${end-start}")
                return IPowerRopeWaveCalc.RopeTriple(start, end, dy)
            }



        }


    /*
    * 数据格式:[x,y,z]
    * x:开始帧索引(闭合包含)
    * y:结束帧索引(闭合包含)
    * z:增量 >0:增长态 <0:下降态 =0:暂停态
    *
    * 逻辑原则:不能连续出现两个同类型数据
    *
    * 实现斜率曲线并且去除抖动后组合曲线上升下降暂停态
    * */
    fun calc(length: Long, frameNumber: Long, rope: Long){
        if (prevLength==Long.MAX_VALUE){
            prevLength = length
            return
        }
        val dy = (length - prevLength).toInt()
        val dyType = dy.sign

        if (currentType == null) {
            //初始化第一笔数据
            currentType = dyType
            currentSum = dy
            startFrame = frameNumber.toInt()
            currentRopeTriple =
                IPowerRopeWaveCalc.RopeTriple(startFrame, frameNumber.toInt() - 1, currentSum)
        } else if (currentType == dyType) {
            //同一趋势，继续累加
            currentSum += dy
            if (currentRopeTriple==null){
                currentRopeTriple =
                    IPowerRopeWaveCalc.RopeTriple(startFrame, frameNumber.toInt() - 1, currentSum)
            }else{
                currentRopeTriple?.also {
                    it.end = frameNumber.toInt() - 1
                    it.dy = currentSum
                }
            }
        } else {
            //发生趋势变化，存储上一次累加的数据
            val endFrame = frameNumber.toInt() - 1
            
            // 添加诊断日志：记录趋势变化时的数据段添加
            log("趋势变化 - 添加数据段 start:${startFrame} end:${endFrame} currentSum:${currentSum} abs:${abs(currentSum)} OFFSET:${OFFSET} 新趋势dyType:${dyType}")
            
            if (abs(currentSum) <OFFSET){
                leftIncrementData.lastOrNull().also {
                    //直接合并暂停同类型
                    if (it!=null&&it.dy==0){
                        it.end = endFrame
                        log("  合并到上一个暂停段 新end:${endFrame}")
                    }else{
                        leftIncrementData.add(
                            IPowerRopeWaveCalc.RopeTriple(
                                startFrame,
                                endFrame,
                                0
                            )
                        )
                        log("  添加新暂停段 (${startFrame}-${endFrame},dy=0)")
                    }
                }
            }else{
                leftIncrementData.add(
                    IPowerRopeWaveCalc.RopeTriple(
                        startFrame,
                        endFrame,
                        currentSum
                    )
                )
                log("  添加新数据段 (${startFrame}-${endFrame},dy=${currentSum}) 当前总段数:${leftIncrementData.size}")
            }
            currentRopeTriple = null
            // 重新开始新的累加
            currentType = dyType
            currentSum = dy
            startFrame = frameNumber.toInt()
        }

        prevLength = length

        //有中间态数据(处于上升态,暂停态,下降态未确定状态)
        if (currentRopeTriple != null) {
            compressPoint0CalcRunnable.accept(leftIncrementData,currentRopeTriple!!)
        }

    }

}
