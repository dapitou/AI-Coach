package com.aeke.fitnessmirror.power.calc.adapter

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import java.util.LinkedList
import kotlin.math.abs

/**
 * 电机绳子长度波峰波谷变化抽象接口
 * 内部处理波峰波谷判断误差偏移
 */
interface IPowerRopeWaveCalc{

    val ropeData: LinkedList<Long>
    /*
    * 左边重量:(FF FF FF)
    * 右边重量:(FF FF FF)
    * 其它保留位
    * */
    val weightData: LinkedList<Long>

    val currentFrameNumber:Long
    /**
     * 一秒回调次数
     * 默认fps=10
     */
    fun init(config: PowerCalcConfig,ropeGetter: IRopeGetter)

    fun postTask(task:Runnable)

    fun pause()

    fun resume()

    fun observeRopeWaveType(callback: AekeObserver<RopeWaveData>):()->Unit

    fun observeRopeLength(callback: AekeObserver<Long>):()->Unit

    /**
     * 释放资源
     */
    fun release()


    data class RopeTriple(var start:Int,var end:Int,var dy:Int){
        internal var childrens:List<RopeTriple>? = null
    }
    /**
     * 电机左右类型
     * type->true:左边电机
     * type->false:右边电机
     */
    data class RopeWaveData(val type: AekePowerCoreAdapter.Power, val start:Int, val end:Int, var dy:Int,internal val startRope:Long, internal val endRope:Long){
        internal var childrens:List<RopeWaveData>? = null

        val startLength by lazy<Int> {
            if (type== AekePowerCoreAdapter.Power.LEFT){
                PowerRopeUtils.getLeftRopeLength(startRope).toInt()
            }else{
                PowerRopeUtils.getRightRopeLength(startRope).toInt()
            }
        }
        val endLength by lazy<Int> {
            if (type== AekePowerCoreAdapter.Power.LEFT){
                PowerRopeUtils.getLeftRopeLength(endRope).toInt()
            }else{
                PowerRopeUtils.getRightRopeLength(endRope).toInt()
            }
        }

        val startFrame by lazy<Int> {
            if (type== AekePowerCoreAdapter.Power.LEFT){
                PowerRopeUtils.getLeftFrameIndex(startRope).toInt()
            }else{
                PowerRopeUtils.getRightFrameIndex(startRope).toInt()
            }
        }
        val endFrame by lazy<Int> {
            if (type== AekePowerCoreAdapter.Power.LEFT){
                PowerRopeUtils.getLeftFrameIndex(endRope).toInt()
            }else{
                PowerRopeUtils.getRightFrameIndex(endRope).toInt()
            }
        }
        //向心时间
        val timeXiangXin:Float by lazy {
            (end-start)/10f
        }

    }

}

//以下是电机计次类相关接口定义

/**
 * 电机计次类接口
 * 单次计次,复合计次等实现这个接口
 */
interface IPowerCalcCounter {

    fun init(config: PowerCalcConfig,powerRopeWaveCalc: IPowerRopeWaveCalc, ropeGetter: IRopeGetter)

    /**
     * 数据类型Long 8个字节,十六进制字符串16个长度
     *      保留位:(F) 左边电机绳长(F FF)
     *      保留位:(F) 右边电机绳长(F FF) (保留位)F
     *      帧号:(F FF FF FF)
     *      获得当前所有的绳子数据
     */
    fun observeRopeLength(callback: AekeObserver<Long>):()->Unit

    /**
     * 停止计次
     */
    fun stopCalcCount()

    /**
     * 开始计次
     */
    fun startCalcCount()

    /**
     * 做功绳子平均长度变化
     */
    fun observeDoWorkAvgRopeLength(callback:AekeObserver<Pair<Int,Int>>): () -> Unit

    /**
     * 计次
     */
    fun observeDoWorkCalcCountData(callback:AekeObserver<Int>): () -> Unit

    /**
     * 做功
     */
    fun observeDoWorkCalcDataData(callback:AekeObserver<DoWokeData>): () -> Unit

    fun observeDoWorkCalcCountTypeData(callback:AekeObserver<Pair<AekePowerCoreAdapter.Power?,CountType>>): () -> Unit

    /*
    * 确定了初始行程和起点回调,只会在第一次确定了行程和起点回调一次,后面行程发生变化不再回调
    * */
    fun observeConfirmInitDistanceAndStartPoint(callback:AekeObserver<Pair<Int,Int>>): () -> Unit

    /*
    * 监听绳子到达起点阈值边界状态
    * */
    fun observeRopeArriveStartPoint(callback: AekeObserver<Pair<IPowerCalcCounter.RopeArriveStartPointState, IPowerRopeWaveCalc.RopeWaveData>>): () -> Unit{
        TODO()
    }

    /**
     * first:左边距离起点dy
     * second:右边距离起点dy
     * 此监听根据fps频率进行回调,10fps,一秒回调10次
     * 监听距离起点dy的变化
     * <0:在起点下方
     * >0:在起点上方
     */
    fun observeFromRopeStartPointDy(callback: AekeObserver<Pair<Long,Long>>): () -> Unit{
        TODO()
    }

    /*
    * 监听绳子到达行程阈值边界状态
    * */
    /*fun observeRopeArriveDistance(callback: AekeObserver<Pair<IPowerCalcCounter.RopeArriveDistanceState, IPowerRopeWaveCalc.RopeWaveData>>){

    }*/

    /**
     * 绳子向心离心暂停类型监听
     * dy<0:离心
     * dy>0:向心
     * dy=0:暂停
     */
    fun observeRopeXxLxPauseEvent(callback: AekeObserver<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>):()->Unit{
        TODO()
    }

    fun observeRopeXxLxTimeDataEvent(callback:AekeObserver<IPowerCalcCounter.XxLxTimeData>):()->Unit{
        TODO()
    }

    /**
     * 释放资源
     */
    fun release()

    fun switchHandShankMode(isImmediatelyStartCalc:Boolean)
    fun switchCrossBarMode(isImmediatelyStartCalc:Boolean)

    fun deleteObserver(callback:Any){
        TODO()
    }

    //绳子进入起点阈值状态
    enum class RopeArriveStartPointState{
        Enter_StartPoint_Threshold_UpToDown,//进入阈值上限
        Enter_StartPoint_Threshold_DownToUp,//进入阈值下限

        Exit_StartPoint_Threshold_UpToDown,//退出阈值下限
        Exit_StartPoint_Threshold_DownToUp,//退出阈值上限
    }

    //绳子进入行程阈值状态
    /*enum class RopeArriveDistanceState{
        Enter_StartPoint_Threshold_UpToDown,//进入阈值上限
        Enter_StartPoint_Threshold_DownToUp,//进入阈值下限

        Exit_StartPoint_Threshold_UpToDown,//退出阈值下限
        Exit_StartPoint_Threshold_DownToUp,//退出阈值上限
    }*/

    data class DoWokeData(
        val countType: CountType,
        val weight:Float,
        val value1: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>,
        var value2: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>?
    ){

        var sn:Int = -1
            internal set
        var leftXiangXinDoWork:Float = 0.0f
            internal set
        var rightXiangXinDoWork:Float = 0.0f
            internal set
    }

    data class XxLxTimeData(
        val sn:Int,
        val xxValue:Array<IPowerRopeWaveCalc.RopeWaveData>,
        var lxValue:Array<IPowerRopeWaveCalc.RopeWaveData>?
    ){

        fun getHighRopeType():AekePowerCoreAdapter.Power{
            return if (xxValue.size>=2){
                if (xxValue[0].startLength>xxValue[1].startLength){
                    return xxValue[0].type
                }else{
                    return xxValue[1].type
                }
            }else if (xxValue.size==1){
                xxValue[0].type
            }else{
                return AekePowerCoreAdapter.Power.LEFT
            }
        }

        fun xxTime(): Float {
            if (xxValue.size == 1) {
                return (xxValue[0].end - xxValue[0].start) * 0.1f
            } else if (xxValue.size == 2) {
                return ((xxValue[0].end - xxValue[0].start) + (xxValue[1].end - xxValue[1].start)) * 0.05f
            }
            return 0f
        }

        fun xxSpeed(): Float {
            if (lxValue != null) {
                return 0f
            }
            return abs(xxDistance()) / xxTime()
        }

        private fun xxDistance(): Float {
            if (xxValue.size == 1) {
                return (xxValue[0].endLength - xxValue[0].startLength).toFloat()
            } else if (xxValue.size == 2) {
                return ((xxValue[0].endLength - xxValue[0].startLength) + (xxValue[1].endLength - xxValue[1].startLength)) * 0.5f
            }
            return 0f
        }

        fun lxTime():Float?{
            val value = lxValue
            if (value==null){
                return null
            }
            if (value.size==1){
                return (value[0].end-value[0].start)*0.1f
            }else if (value.size==2){
                return ((value[0].end-value[0].start)+(value[1].end-value[1].start))*0.05f
            }
            return 0f
        }

        fun getShowFrameNumber():Int{
            val lx = lxValue
            val xxFrameSum = xxValue.sumBy { it.end }
            if (lx != null) {
                val lxFrameSum = lx.sumBy { it.start }
                return (lxFrameSum+xxFrameSum)/(lx.size+xxValue.size)
            }else{
                return xxFrameSum/xxValue.size
            }

        }

    }


    enum class CountType{
        Init,ResetLow,Single,Double
    }
}

interface IRopeGetter {
    fun getLeftRopeLength():Long
    fun getRightRopeLength():Long

}
