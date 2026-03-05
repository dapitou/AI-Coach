package com.aeke.fitnessmirror.power.calc.adapter.impl

import android.util.Log
import com.aeke.baseliabrary.utils.data.GlobalPropManage
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.benmo.BenMoPowerHelper
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.HandsOffProtectionHelper
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.calc.adapter.IntelligentAssistant
import com.aeke.fitnessmirror.power.calc.adapter.PowerRopeUtils
import com.aeke.fitnessmirror.power.constance.HardwareMode
import com.aeke.fitnessmirror.power.data.DistanceType
import com.aeke.fitnessmirror.power.event.HandsOffProtectEvent
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import org.greenrobot.eventbus.EventBus
import java.lang.IllegalArgumentException
import java.util.Deque
import java.util.LinkedList
import kotlin.math.abs
import kotlin.math.max
import kotlin.math.min

/**
 * 可用于随心练等场景
 */
open class DoubleRopePowerCalcCounter :IPowerCalcCounter{

    //0:手柄模式
    //1:横杆模式

    private val logTag = this::class.simpleName
    var currentMode:Int = HardwareMode.HandShankMode
        private set

    protected lateinit var powerWaveCalc: IPowerRopeWaveCalc
    //平均做功绳子长度
    private val doWorkAvgRopeLengthObservable: AekeObservable<Pair<Int,Int>> = AekeObservable()
    //做功计次增量
    private val doWorkCalcCountObservable: AekeObservable<Int> = AekeObservable()
    //做功计次增量
    private val doWorkCalcCount2Observable: AekeObservable<Pair<AekePowerCoreAdapter.Power?,IPowerCalcCounter.CountType>> = AekeObservable()
    //做功w
    private val doWorkCalcDataObservable: AekeObservable<IPowerCalcCounter.DoWokeData> = AekeObservable()
    //确定了初始行程和起点
    private val confirmInitDistanceAndStartPointObservable:AekeObservable<Pair<Int,Int>> = AekeObservable()
    //向心离心暂停监听
    private val ropeXxLxPauseStateObservable:AekeObservable<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>> = AekeObservable()

    private val ropeArriveStartPointObservable:AekeObservable<Pair<IPowerCalcCounter.RopeArriveStartPointState,IPowerRopeWaveCalc.RopeWaveData>> = AekeObservable()

    private val fromRopeStartPointDyEventObservable:AekeObservable<Pair<Long,Long>> = AekeObservable()
    //绳子向心离心事件
    val ropeXxLxTimeObservable:AekeObservable<IPowerCalcCounter.XxLxTimeData> = AekeObservable()

    private var prevAvgDistance:Int = Int.MAX_VALUE

    private var prevAvgStartPoint:Int = Int.MAX_VALUE

    private var isStartCalc:Boolean = false

    var onAssistantRunning: ((Boolean) -> Unit)? = null
        set(value) {
            field = value
            intelligentAssistant?.onAssistantRunning = onAssistantRunning
        }

    var multiInitDistance:Int = Int.MAX_VALUE
        private set
    var multiInitStartPoint:Int = 0
        private set

    lateinit var config: PowerCalcConfig

    private val waveQueue:Deque<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>> = LinkedList()

    private var initWaveQueue:Deque<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>> = LinkedList()
    //脱手保护类
    private var handsOffProtectionHelper: HandsOffProtectionHelper? = null
    private var intelligentAssistant: IntelligentAssistant? = null

    private var useForCorrect:Boolean = false

    val leftCounter:SingleRopePowerCalcCounter = object : SingleRopePowerCalcCounter(AekePowerCoreAdapter.Power.LEFT) {
        override fun onHandlePowerCalcCount(values: IPowerRopeWaveCalc.RopeWaveData) {
            if (!isStartCalc){
                return
            }
            if (values.dy<=0){
                postXxLxWaveEvent(AekePowerCoreAdapter.Power.RIGHT,values)
            }
            if (values.dy<0){
                return
            }
            if (values.dy==0){
                /*if (isSupportResetPoint()){
                    if (this@DoubleRopePowerCalcCounter.multiInitDistance!=Int.MAX_VALUE&&isPauseOtherSide(AekePowerCoreAdapter.Power.LEFT, values)) {
                        resetStartPoint(values.startLength)
                    }
                }*/
                return
            }
            onSureRopeWaveType(AekePowerCoreAdapter.Power.LEFT,values)
        }
    }

    val rightCounter:SingleRopePowerCalcCounter = object : SingleRopePowerCalcCounter(AekePowerCoreAdapter.Power.RIGHT) {
        override fun onHandlePowerCalcCount(values: IPowerRopeWaveCalc.RopeWaveData) {
            if (!isStartCalc){
                return
            }
            if (values.dy<=0){
                postXxLxWaveEvent(AekePowerCoreAdapter.Power.LEFT,values)
            }
            if (values.dy<0){
                return
            }
            if (values.dy==0){
                /*if (isSupportResetPoint()){
                    if (this@DoubleRopePowerCalcCounter.multiInitDistance!=Int.MAX_VALUE&&isPauseOtherSide(AekePowerCoreAdapter.Power.RIGHT, values)) {
                        resetStartPoint(values.startLength)
                    }
                }*/
                return
            }
            onSureRopeWaveType(AekePowerCoreAdapter.Power.RIGHT,values)
        }
    }

    private var currentInitXxLxTimeRopeData:Array<IPowerRopeWaveCalc.RopeWaveData>? = null
    private var currentXxLxTimeRecord:Triple<Int,Array<IPowerRopeWaveCalc.RopeWaveData>,Array<IPowerRopeWaveCalc.RopeWaveData>?>? = null

    val doubleWaveTypeCounter:DoubleWaveTypeSureCalcCounter = object :DoubleWaveTypeSureCalcCounter(){
        private var xxlxSn:Int = 0
        override fun onSureLxRopeWaveType(values: Array<IPowerRopeWaveCalc.RopeWaveData>) {
            super.onSureLxRopeWaveType(values)
            val xxLxTimeRecord = currentXxLxTimeRecord
            if (xxLxTimeRecord==null){
                return
            }
            val xxEndMax:Int = xxLxTimeRecord.second.maxOf { it.end }
            val lxStartMax:Int = values.maxOf { it.start }
            if (xxEndMax>lxStartMax){
                return
            }
            //向心双边
            if (xxLxTimeRecord.second.size==2){
                //离心双边
                if (values.size==2){
                    val record = Triple(xxlxSn,xxLxTimeRecord.second,values)
                    postRopeXxLxTimeObservableEvent(record)
                }
                //离心单边
                else{
                    //忽略
                }
            }
            //向心单边
            else if (xxLxTimeRecord.second.size==1){
                //离心双边
                if (values.size==2){
                    val value = if (xxLxTimeRecord.second[0].type==values[0].type){
                        values[0]
                    }else{
                        values[1]
                    }
                    val record = Triple(xxlxSn,xxLxTimeRecord.second, arrayOf(value))
                    postRopeXxLxTimeObservableEvent(record)
                }
                //离心单边
                else{
                    if (xxLxTimeRecord.second[0].type==values[0].type){
                        val record = Triple(xxlxSn,xxLxTimeRecord.second, arrayOf(values[0]))
                        postRopeXxLxTimeObservableEvent(record)
                    }
                }
            }
        }

        override fun onSureXxRopeWaveType(values: Array<IPowerRopeWaveCalc.RopeWaveData>) {
            super.onSureXxRopeWaveType(values)
            if (multiInitDistance==Int.MAX_VALUE){
                currentInitXxLxTimeRopeData = values
                return
            }
            currentXxLxTimeRecord = null
            var result = values
            if (values.size==2){
                val value1 = values[0]
                val value2 = values[1]
                val copyList = mutableListOf<IPowerRopeWaveCalc.RopeWaveData>()
                if ((value1.dy.toFloat()/multiInitDistance)>=config.DISTANCE_EFFECTIVE_THRESHOLD){
                    copyList.add(value1)
                }
                if ((value2.dy.toFloat()/multiInitDistance)>=config.DISTANCE_EFFECTIVE_THRESHOLD){
                    copyList.add(value2)
                }
                if (copyList.size>0){
                    result = copyList.toTypedArray()
                }else{
                    return
                }
            }else{
                val avgLength = values[0].dy
                if ((avgLength.toFloat()/multiInitDistance)<config.DISTANCE_EFFECTIVE_THRESHOLD){
                    return
                }
            }
            xxlxSn++
            val record = Triple(xxlxSn,result,null)
            currentXxLxTimeRecord = record
            postRopeXxLxTimeObservableEvent(record)
        }

    }

    private var prevDoWorkData: IPowerCalcCounter.DoWokeData? = null

    private var doWorkSn:Int = 0

    private var calcTypeFlag:Int = 0

    private var initBuffer:Deque<Array<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>> = LinkedList()

    private val resetBuffer:Deque<Array<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>> = LinkedList()

    private var lockLeftCalc:Boolean = true
    private var lockRightCalc:Boolean = true
    protected var distanceType: DistanceType = DistanceType.LONG

    private var frameCount:Int = Int.MAX_VALUE
    private var firstPower:AekePowerCoreAdapter.Power? = null
    private var leftStartFrame:Int = Int.MAX_VALUE
    private var rightStartFrame:Int = Int.MAX_VALUE
    private var leftEndFrame:Int = Int.MAX_VALUE
    private var rightEndFrame:Int = Int.MAX_VALUE

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        init(config, powerRopeWaveCalc, ropeGetter, false)
    }

    fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter,
        useForCorrect: Boolean
    ) {
        this.config = config
        this.powerWaveCalc = powerRopeWaveCalc
        this.useForCorrect = useForCorrect
        powerWaveCalc.init(config, ropeGetter)
        powerWaveCalc.observeRopeLength(object :AekeObserver<Long>{
            override fun update(value: Long) {
                onFps(value)
                onHandleFromRopeStartPointDyEvent(value)
            }
        })
        leftCounter.init(config, powerRopeWaveCalc, ropeGetter)
        rightCounter.init(config, powerRopeWaveCalc, ropeGetter)
        doubleWaveTypeCounter.init(config, powerRopeWaveCalc, ropeGetter)
        initSingleDoubleCalc()
        if (!useForCorrect) {
            if (isSupportHandsOffProtect()) {
                handsOffProtectionHelper = HandsOffProtectionHelper(protectCallback = {
                    EventBus.getDefault().post(HandsOffProtectEvent(it))
                }).apply {
                    this.attach(powerRopeWaveCalc)
                }
            }
            switchHandShankMode(false)
            intelligentAssistant = IntelligentAssistant(this)
        }
    }

    private fun initSingleDoubleCalc() {
        //向心单双边判断
        observeFromRopeStartPointDy(object :AekeObserver<Pair<Long,Long>>{

            private fun resetSingleDoubleCalcVar(countType: IPowerCalcCounter.CountType){
                if (countType==IPowerCalcCounter.CountType.Single){
                    if (firstPower==AekePowerCoreAdapter.Power.LEFT){
                        lockLeftCalc = true
                    }else if (firstPower==AekePowerCoreAdapter.Power.RIGHT){
                        lockRightCalc = true
                    }
                }else{
                    lockLeftCalc = true
                    lockRightCalc = true
                }
                frameCount = Int.MAX_VALUE
                firstPower = null
            }

            override fun update(value: Pair<Long, Long>) {
                onDistanceThreshold(value)
                onStartPointThreshold(value)
            }

            private fun onDistanceThreshold(value: Pair<Long, Long>) {
                if (firstPower!=null){
                    if (frameCount!=Int.MAX_VALUE){
                        frameCount++
                        if (frameCount>=3){
                            //TODO 发出单边事件
                            val dy:Long
                            val data:Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>
                            if (firstPower==AekePowerCoreAdapter.Power.LEFT){
                                dy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(leftEndFrame))-multiInitStartPoint
                                data = firstPower!! to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,dy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            }else{
                                dy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(rightEndFrame))-multiInitStartPoint
                                data = firstPower!! to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,rightStartFrame,rightEndFrame,dy.toInt(),powerWaveCalc.ropeData.get(rightStartFrame),powerWaveCalc.ropeData.get(rightEndFrame))
                            }
                            postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,NewPowerHelper.currentPowerSetWeight,data,null))
                            postRopeCalcEvent(firstPower,IPowerCalcCounter.CountType.Single)
                            val side = firstPower?.name ?: "null "
                            log("$side 发出单边事件")
                            this.resetSingleDoubleCalcVar(IPowerCalcCounter.CountType.Single)
                        }
                    }
                }
                val leftDy = value.first
                val rightDy = value.second
                log("leftDy = $leftDy, rightDy = $rightDy, multiInitDistance = $multiInitDistance, multiInitStartPoint = $multiInitStartPoint")
                if (firstPower!=AekePowerCoreAdapter.Power.LEFT){
                    if (!lockLeftCalc&&leftDy>=multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD){
                        log("LEFT 达到计次阈值, multiInitDistance = $multiInitDistance")
                        leftEndFrame = powerWaveCalc.currentFrameNumber.toInt()
                        if (firstPower==null){
                            firstPower=AekePowerCoreAdapter.Power.LEFT
                            frameCount = 0
                        }else{
                            //TODO 发出双边事件
                            val rightDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(rightEndFrame))-multiInitStartPoint
                            val rightData = AekePowerCoreAdapter.Power.RIGHT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,rightDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            val leftDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(leftEndFrame))-multiInitStartPoint
                            val leftData = AekePowerCoreAdapter.Power.LEFT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,leftDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Double,NewPowerHelper.currentPowerSetWeight,rightData,leftData))
                            postRopeCalcEvent(null,IPowerCalcCounter.CountType.Double)
                            log("Power.LEFT 发出双边事件")
                            this.resetSingleDoubleCalcVar(IPowerCalcCounter.CountType.Double)
                        }
                    }
                }
                if (firstPower!=AekePowerCoreAdapter.Power.RIGHT){
                    if (!lockRightCalc&&rightDy>=multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD){
                        log("RIGHT 达到计次阈值, multiInitDistance = $multiInitDistance")
                        rightEndFrame = powerWaveCalc.currentFrameNumber.toInt()
                        if (firstPower==null){
                            firstPower=AekePowerCoreAdapter.Power.RIGHT
                            frameCount = 0
                        }else{
                            //TODO 发出双边事件
                            val rightDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(rightEndFrame))-multiInitStartPoint
                            val rightData = AekePowerCoreAdapter.Power.RIGHT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,rightDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            val leftDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(leftEndFrame))-multiInitStartPoint
                            val leftData = AekePowerCoreAdapter.Power.LEFT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,leftDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Double,NewPowerHelper.currentPowerSetWeight,rightData,leftData))
                            postRopeCalcEvent(null,IPowerCalcCounter.CountType.Double)
                            log("Power.RIGHT 发出双边事件")
                            this.resetSingleDoubleCalcVar(IPowerCalcCounter.CountType.Double)
                        }
                    }
                }
            }

            private fun onStartPointThreshold(value: Pair<Long, Long>){
                if (value.first<=multiInitDistance*config.DISTANCE_THRESHOLD){
                    lockLeftCalc = false
                    leftStartFrame = powerWaveCalc.currentFrameNumber.toInt()
                }
                if (value.second<=multiInitDistance*config.DISTANCE_THRESHOLD){
                    lockRightCalc = false
                    rightStartFrame = powerWaveCalc.currentFrameNumber.toInt()
                }
            }
        })

        observeDoWorkCalcCountTypeData(object :AekeObserver<Pair<AekePowerCoreAdapter.Power?, IPowerCalcCounter.CountType>>{
            override fun update(value: Pair<AekePowerCoreAdapter.Power?, IPowerCalcCounter.CountType>) {
                if (currentMode==HardwareMode.HandShankMode){
                    if (value.second==IPowerCalcCounter.CountType.Double){
                        postRopeCalcEvent(1)
                    }else if (value.second==IPowerCalcCounter.CountType.Single){
                        postRopeCalcEvent(1)
                    }
                }else{
                    if (value.second==IPowerCalcCounter.CountType.Double){
                        postRopeCalcEvent(1)
                    }else if (value.second==IPowerCalcCounter.CountType.Single){
                        postRopeCalcEvent(1)
                    }
                }
            }

        })

    }

    protected fun onHandleFromRopeStartPointDyEvent(value:Long){
        if (multiInitDistance==Int.MAX_VALUE){
            return
        }
        val leftRope = PowerRopeUtils.getLeftRopeLength(value)
        val rightRope = PowerRopeUtils.getRightRopeLength(value)
        postFromRopeStartPointDyEvent(leftRope-multiInitStartPoint,rightRope-multiInitStartPoint)
    }

    protected open fun onSureRopeWaveType(power:AekePowerCoreAdapter.Power,values: IPowerRopeWaveCalc.RopeWaveData){
        if (waveQueue.size>0){
            val first = waveQueue.pop()
            if (first.first!=power){
                waveQueue.add(first)
            }
        }
        var data = values
        if (multiInitStartPoint==0){
            val childrens = data.childrens
            val index = childrens?.indexOfLast { it.end-it.start>=config.START_PAUSE_FRAME_THRESHOLD }?:-1
            if (childrens!=null&&index>=0){
                data = childrens[index]
                var dy = 0
                for (i in index until childrens.size) {
                    dy+=childrens[i].dy
                }
                data = IPowerRopeWaveCalc.RopeWaveData(power,data.start,values.end,dy,data.startRope,values.endRope)
            }
        }
        waveQueue.add(power to data)
        postXxLxWaveEvent(power, data)
    }

    protected open fun onFps(value: Long) {
        if (multiInitDistance==Int.MAX_VALUE){
            if (waveQueue.size==1){
                if (calcTypeFlag==config.RIGHT_LEFT_OFFSET_FRAME_COUNT_THRESHOLD){
                    calcTypeFlag = 0
                    //确定单侧
                    val first = waveQueue.pop()
                    if (initBuffer.size>=2){
                        initBuffer.pop()
                    }
                    initBuffer.add(arrayOf(first))
                    initWaveQueue.add(first)
                }else{
                    calcTypeFlag++
                }
            }else if (waveQueue.size==2){
                val first = waveQueue.pop()
                val second = waveQueue.pop()
                calcTypeFlag = 0
                //双侧
                val dy = (first.second.dy+second.second.dy)/2
                val leftStartLength = PowerRopeUtils.createRopeLongData(((first.second.startLength+second.second.startLength)/2).toLong(),0,second.second.startFrame.toLong())
                val leftEndLength = PowerRopeUtils.createRopeLongData(((first.second.endLength+second.second.endLength)/2).toLong(),0,second.second.endFrame.toLong())
                val da = IPowerRopeWaveCalc.RopeWaveData(AekePowerCoreAdapter.Power.LEFT,second.second.start,second.second.end,dy,leftStartLength,leftEndLength)

                if (initBuffer.size>=2){
                    initBuffer.pop()
                }
                initBuffer.add(arrayOf(first,second))
                initWaveQueue.add(AekePowerCoreAdapter.Power.LEFT to da)
            }


            if (initWaveQueue.size==2){
                val first = initWaveQueue.pop()
                val second = initWaveQueue.pop()
                if (!onConfirmInitDistanceAndStartPoint(first,second)){
                    initWaveQueue.add(second)
                }
            }
            return
        }
        if (waveQueue.size==1){
            if (calcTypeFlag==config.RIGHT_LEFT_OFFSET_FRAME_COUNT_THRESHOLD){
                calcTypeFlag = 0
                //确定单侧
                val first = waveQueue.pop()
                if (resetBuffer.size>=2){
                    resetBuffer.pop()
                }
                resetBuffer.add(arrayOf(first))
                onSureSingleDoubleType2(first,null)
            }else{
                calcTypeFlag++
            }
        }else if (waveQueue.size==2){
            val first = waveQueue.pop()
            val second = waveQueue.pop()
            calcTypeFlag = 0
            //确定双侧
            if (resetBuffer.size>=2){
                resetBuffer.pop()
            }
            resetBuffer.add(arrayOf(first,second))
            onSureSingleDoubleType2(first,second)
        }
    }

    private fun resetStartPoint(startPoint:Int){
        multiInitStartPoint = startPoint
        prevAvgStartPoint = Int.MAX_VALUE
        waveQueue.clear()
        postAvgRopeLengthEvent()
    }

    open fun onConfirmInitDistanceAndStartPoint(
        first: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>,
        second: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>):Boolean{
        log("first dy = ${first.second.dy}, second dy = ${second.second.dy}, first startLength = ${first.second.startLength}, second startLength = ${second.second.startLength}")
        if (withinTolerance(first.second.dy,second.second.dy,config.DISTANCE_THRESHOLD)){
            if (withinToleranceStartPoint(first.second.startLength,second.second.startLength,config.START_POINT_THRESHOLD)){
                multiInitDistance = (first.second.dy+second.second.dy)/2
                multiInitStartPoint = (first.second.startLength+second.second.startLength)/2
                distanceType = DistanceType.getDistanceType(multiInitDistance)
                prevAvgDistance = multiInitDistance
                prevAvgStartPoint = multiInitStartPoint
                confirmInitDistanceAndStartPointObservable.setChanged()
                confirmInitDistanceAndStartPointObservable.notifyObservers(multiInitDistance to multiInitStartPoint)
                postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Init,NewPowerHelper.currentPowerSetWeight,first,second))
                postAvgRopeLengthEvent()
                //显示初始行程确定后的向心时间
                currentInitXxLxTimeRopeData?.let {
                    doubleWaveTypeCounter.onSureXxRopeWaveType(it)
                }
                return true
            }
        }
        return false
    }

    open fun onSureSingleDoubleType2(
        first: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>,
        second: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>?
    ) {
        var dy = Int.MAX_VALUE
        var startPoint = Int.MAX_VALUE
        if (second == null) {
            if (first.second.dy > 0) {
                dy = first.second.dy
                startPoint = first.second.startLength
                /*val isSatisfyCalc = isSatisfyCalc(first)
                if (isSatisfyCalc){
                    postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,NewPowerHelper.currentPowerSetWeight,first,null))
                }*/
            }
        } else if (first.second.dy > 0 && second.second.dy > 0) {
            dy = (first.second.dy+second.second.dy)/2
            startPoint = (first.second.startLength+second.second.startLength)/2
            /*val isSatisfyCalc1 = isSatisfyCalc(first)
            val isSatisfyCalc2 = isSatisfyCalc(second)
            if (isSatisfyCalc1&&isSatisfyCalc2){
                postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Double,NewPowerHelper.currentPowerSetWeight,first,second))
            }else if (isSatisfyCalc2){
                postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,NewPowerHelper.currentPowerSetWeight,second,null))
            }else if (isSatisfyCalc1){
                postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,NewPowerHelper.currentPowerSetWeight,first,null))
            }*/
        }else if (first.second.dy == 0 && second.second.dy > 0) {
            dy = second.second.dy
            startPoint = second.second.startLength
            /*val isSatisfyCalc = isSatisfyCalc(second)
            if (isSatisfyCalc){
                postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,NewPowerHelper.currentPowerSetWeight,second,null))
            }*/
        }else if (second.second.dy == 0 && first.second.dy > 0) {
            dy = second.second.dy
            startPoint = second.second.startLength
            /*val isSatisfyCalc = isSatisfyCalc(first)
            if (isSatisfyCalc){
                postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,NewPowerHelper.currentPowerSetWeight,first,null))
            }*/
        }
        if (dy==Int.MAX_VALUE||startPoint== Int.MAX_VALUE){
            return
        }
        var isReset:Boolean = false
        var isPostDoWork = false
        if (prevAvgStartPoint!=Int.MAX_VALUE){
            if (abs(prevAvgStartPoint-multiInitStartPoint) >multiInitStartPoint*config.START_POINT_THRESHOLD&& abs(startPoint-multiInitStartPoint) >multiInitStartPoint*config.START_POINT_THRESHOLD){
                if (withinTolerance(prevAvgStartPoint,startPoint,config.START_POINT_THRESHOLD)){
                    isReset = true
                    if (dy < multiInitDistance * config.DISTANCE_EFFECTIVE_THRESHOLD && prevAvgDistance < multiInitDistance * config.DISTANCE_EFFECTIVE_THRESHOLD) {
                        isPostDoWork = true
                    }
                }
            }
        }
        if (prevAvgDistance!= Int.MAX_VALUE){
            if (prevAvgDistance<multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD&&dy<multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD){
                if (withinTolerance(prevAvgDistance,dy,config.DISTANCE_THRESHOLD)){
                    isReset = true
                    isPostDoWork = true
                }
            }
        }
        if (isReset){
            multiInitDistance = (prevAvgDistance+dy)/2
            multiInitStartPoint = (prevAvgStartPoint+startPoint)/2
            lockLeftCalc = true
            lockRightCalc = true
            if (isPostDoWork) {
            //TODO 发出做功事件
            postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.ResetLow,NewPowerHelper.currentPowerSetWeight, first, second))
            }
        }


        prevAvgDistance = dy
        prevAvgStartPoint = startPoint
        /*if (isSupportResetDistance()){
            if (dy != Int.MAX_VALUE){
                if (withinTolerance(dy,prevAvgDistance,config.DISTANCE_THRESHOLD)){
                    if ((prevAvgDistance>multiInitDistance*config.DISTANCE_RESET_THRESHOLD&&dy>multiInitDistance&&dy>multiInitDistance*config.DISTANCE_RESET_THRESHOLD)){
                        multiInitDistance = (prevAvgDistance+dy)/2
                    }else if ((prevAvgDistance<multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD&&dy<multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD)){
                        multiInitDistance = (prevAvgDistance+dy)/2
                        postDoWorkEvent(IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.ResetLow,NewPowerHelper.currentPowerSetWeight, first, second))
                    }
                }
            }
        }
        if (isSupportResetPoint()){
            if (startPoint != Int.MAX_VALUE) {
                if (prevAvgStartPoint!=Int.MAX_VALUE){
                    if (prevAvgStartPoint-startPoint>multiInitStartPoint*config.START_POINT_THRESHOLD){
                        if (withinTolerance(prevAvgStartPoint,startPoint,config.START_POINT_THRESHOLD)){
                            multiInitStartPoint = (prevAvgStartPoint+startPoint)/2
                        }
                    }
                }
            }
        }*/
        postAvgRopeLengthEvent()

    }

    open fun isSupportResetPoint():Boolean{
        return true
    }

    open fun isSupportResetDistance():Boolean{
        return true
    }

    open fun isSupportHandsOffProtect():Boolean{
        return GlobalPropManage.isSupportWeightProtect
    }

    fun enableAssistant() {
        intelligentAssistant?.enableAssistant()
    }

    fun disableAssistant() {
        intelligentAssistant?.disableAssistant()
    }

    protected fun isPauseType(values: Array<IPowerRopeWaveCalc.RopeWaveData>):Boolean{
        return values.size==1
    }

    protected fun isPauseOtherSide(power:AekePowerCoreAdapter.Power,value:IPowerRopeWaveCalc.RopeWaveData):Boolean{
        val power = if (power==AekePowerCoreAdapter.Power.LEFT){
            AekePowerCoreAdapter.Power.RIGHT
        }else{
            AekePowerCoreAdapter.Power.LEFT
        }
        val start = value.start
        val end = value.end
        return isPause(power, start, end)
    }

    protected fun isPause(power:AekePowerCoreAdapter.Power,start:Int,end:Int):Boolean{
        try {
            val ropeData = powerWaveCalc.ropeData
            var max:Long = Long.MIN_VALUE
            var min:Long = Long.MAX_VALUE
            for (i in start until end){
                if (power==AekePowerCoreAdapter.Power.LEFT){
                    PowerRopeUtils.getLeftRopeLength(ropeData[i])
                }else{
                    PowerRopeUtils.getRightRopeLength(ropeData[i])
                }.let {
                    max = max(max,it)
                    min = min(min,it)
                }
            }
            return max-min<10
        }catch (e:Exception){
            throw IllegalArgumentException()
        }
    }

    protected fun isPause(value:Pair<AekePowerCoreAdapter.Power,Array<IPowerRopeWaveCalc.RopeWaveData>>):Boolean{
        val power = value.first
        val start = value.second[0].start
        val end = value.second[value.second.size-1].end
        return isPause(power, start, end)
    }

    protected fun withinTolerance(a: Int, b: Int, tolerance: Float): Boolean {
        val max = maxOf(a, b)
        val min = minOf(a, b)
        // 防止除以零异常
        if (min == 0) return false
        // 最大相对差值是否在容忍范围内
        return (max - min).toDouble() / min < tolerance
    }

    protected fun withinToleranceStartPoint(a: Int, b: Int, tolerance: Float): Boolean {
        if (abs(a-b)<=15){
            return true
        }else{
            return false
        }
        /*val max = maxOf(a, b)
        val min = minOf(a, b)
        // 防止除以零异常
        if (min == 0) return false
        // 最大相对差值是否在容忍范围内
        return (max - min).toDouble() / min < tolerance*/
    }

    protected fun isSatisfyCalc(value:Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>):Boolean{
        val initDistance:Int
        val initStartPoint:Int
        val startLength = value.second.startLength
        val dy = value.second.dy
        initDistance = multiInitDistance
        initStartPoint = multiInitStartPoint
        if (startLength<initStartPoint+config.OFFSET&& abs(dy) > initDistance*config.DISTANCE_EFFECTIVE_THRESHOLD){
            return true
        }else{
            return false
        }
    }

    override fun observeRopeLength(callback: AekeObserver<Long>): () -> Unit {
        return powerWaveCalc.observeRopeLength(callback)
    }

    override fun stopCalcCount() {
        if (!isStartCalc){
            return
        }
        isStartCalc = false
        powerWaveCalc.pause()
        powerWaveCalc.postTask{
            resetData()
            doubleWaveTypeCounter.stopCalcCount()
            leftCounter.stopCalcCount()
            rightCounter.stopCalcCount()
        }
    }

    override fun observeRopeArriveStartPoint(callback: AekeObserver<Pair<IPowerCalcCounter.RopeArriveStartPointState, IPowerRopeWaveCalc.RopeWaveData>>): () -> Unit {
        ropeArriveStartPointObservable.addObserver(callback)
        return {
            ropeArriveStartPointObservable.deleteObserver(callback)
        }
    }

    override fun startCalcCount() {
        if (isStartCalc){
            return
        }
        isStartCalc = true
        powerWaveCalc.resume()
        powerWaveCalc.postTask{
            resetData()
            doubleWaveTypeCounter.startCalcCount()
            leftCounter.startCalcCount()
            rightCounter.startCalcCount()
        }
    }

    private fun resetData(){
        initWaveQueue.clear()
        waveQueue.clear()
        prevAvgStartPoint = Int.MAX_VALUE
        prevAvgDistance = Int.MAX_VALUE
        if (isSupportResetDistance()){
            multiInitDistance = Int.MAX_VALUE
        }
        if (isSupportResetPoint()){
            multiInitStartPoint = 0
        }
        initBuffer.clear()
        resetBuffer.clear()
        prevDoWorkData = null
        lockLeftCalc = true
        lockRightCalc = true


        frameCount = Int.MAX_VALUE
        firstPower = null
        leftStartFrame = Int.MAX_VALUE
        rightStartFrame = Int.MAX_VALUE
        leftEndFrame = Int.MAX_VALUE
        rightEndFrame = Int.MAX_VALUE

        currentXxLxTimeRecord = null
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

    override fun observeDoWorkCalcCountTypeData(callback: AekeObserver<Pair<AekePowerCoreAdapter.Power?,IPowerCalcCounter.CountType>>): () -> Unit {
        doWorkCalcCount2Observable.addObserver(callback)
        return {
            doWorkCalcCount2Observable.deleteObserver(callback)
        }
    }

    override fun observeConfirmInitDistanceAndStartPoint(callback: AekeObserver<Pair<Int,Int>>): () -> Unit {
        confirmInitDistanceAndStartPointObservable.addObserver(callback)
        return {
            confirmInitDistanceAndStartPointObservable.deleteObserver(callback)
        }
    }

    override fun release() {
        powerWaveCalc.release()
        leftCounter.release()
        rightCounter.release()
        intelligentAssistant?.release()
        handsOffProtectionHelper?.detach()
        NewPowerHelper.setBalanceMode(false)
    }

    protected fun postRopeCalcEvent(addCount:Int){
        log("postRopeCalcEvent:${addCount}")
        doWorkCalcCountObservable.setChanged()
        doWorkCalcCountObservable.notifyObservers(addCount)
    }

    protected fun postRopeCalcEvent(power:AekePowerCoreAdapter.Power?,countType:IPowerCalcCounter.CountType){
        log("postRopeCalcEvent")
        doWorkCalcCount2Observable.setChanged()
        doWorkCalcCount2Observable.notifyObservers(power to countType)
    }

    protected fun postDoWorkEvent(value:IPowerCalcCounter.DoWokeData){
        log("postDoWorkEvent CountType = ${value.countType.name}")
        var data = value
        if (value.countType==IPowerCalcCounter.CountType.Double|| value.countType==IPowerCalcCounter.CountType.Single){
            calcRopeDoWork(value)
            if (value.value2!=null){
                doWorkSn++
                //双边发出value
                prevDoWorkData = null
            }else {
                val prev = prevDoWorkData
                //等待出结果,之前有一组数据在等待下一组,
                if (prev != null) {
                    //同一边,分别为一组
                    if (data.value1.first==prev.value1.first){
                        doWorkSn++
                        prevDoWorkData = data
                    }
                    //不同边,为一组
                    else{
                        prev.value2 = data.value1
                        prev.leftXiangXinDoWork+=data.leftXiangXinDoWork
                        prev.rightXiangXinDoWork+=data.rightXiangXinDoWork
                        data = prev
                        prevDoWorkData = null
                    }
                }else{
                    doWorkSn++
                    prevDoWorkData = data
                }
            }
        }else {
            if (value.countType==IPowerCalcCounter.CountType.Init||value.countType==IPowerCalcCounter.CountType.ResetLow){
                val first: Array<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>
                val second:Array<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>
                if (value.countType == IPowerCalcCounter.CountType.Init) {
                    if (initBuffer.isNotEmpty()) {
                        first = initBuffer.pop()
                    } else {
                        return
                    }
                    if (initBuffer.isNotEmpty()) {
                        second = initBuffer.pop()
                    } else {
                        return
                    }
                } else {
                    if (resetBuffer.isNotEmpty()) {
                        first = resetBuffer.pop()
                    } else {
                        return
                    }
                    if (resetBuffer.isNotEmpty()) {
                        second = resetBuffer.pop()
                    } else {
                        return
                    }
                }
                if (first.size>=2){
                    postRopeCalcEvent(null,IPowerCalcCounter.CountType.Double)
                    data = IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Double,value.weight,first[0],first[1])
                    postDoWorkEvent(data)
                }else if (first.size>=1){
                    postRopeCalcEvent(first[0].first,IPowerCalcCounter.CountType.Single)
                    data = IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,value.weight,first[0],null)
                    postDoWorkEvent(data)
                }

                if (second.size>=2){
                    postRopeCalcEvent(null,IPowerCalcCounter.CountType.Double)
                    data = IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Double,value.weight,second[0],second[1])
                    postDoWorkEvent(data)
                }else if (second.size>=1){
                    postRopeCalcEvent(second[0].first,IPowerCalcCounter.CountType.Single)
                    data = IPowerCalcCounter.DoWokeData(IPowerCalcCounter.CountType.Single,value.weight,second[0],null)
                    postDoWorkEvent(data)
                }
            }
            return
        }

        /*if (currentMode==HardwareMode.HandShankMode){
            if (value.countType==IPowerCalcCounter.CountType.Double){
                postRopeCalcEvent(1)
            }else if (value.countType==IPowerCalcCounter.CountType.Single){
                postRopeCalcEvent(1)
            }
        }else{
            if (value.countType==IPowerCalcCounter.CountType.Double){
                postRopeCalcEvent(1)
            }else if (value.countType==IPowerCalcCounter.CountType.Single){
                //return
            }
        }*/

        data.sn = doWorkSn
        data.leftXiangXinDoWork = round2NumerPoint(data.leftXiangXinDoWork)
        data.rightXiangXinDoWork = round2NumerPoint(data.rightXiangXinDoWork)
        log("postDoWorkEvent leftXiangXinDoWork = ${data.leftXiangXinDoWork} rightXiangXinDoWork = ${data.rightXiangXinDoWork}")
        doWorkCalcDataObservable.setChanged()
        doWorkCalcDataObservable.notifyObservers(data)
    }

    protected fun calcRopeDoWork(value:IPowerCalcCounter.DoWokeData){
        var work = PowerRopeUtils.getDoWork(powerWaveCalc,value.value1,NewPowerHelper.currentPowerSetWeight)
        log("calcRopeDoWork - value1: power=${value.value1.first} dy=${value.value1.second.dy} start=${value.value1.second.start} end=${value.value1.second.end} work=$work weight=${NewPowerHelper.currentPowerSetWeight}")
        if (value.value1.first==AekePowerCoreAdapter.Power.LEFT){
            value.leftXiangXinDoWork+=work
        }else{
            value.rightXiangXinDoWork+=work
        }
        if (value.value2!=null){
            work = PowerRopeUtils.getDoWork(powerWaveCalc,value.value2!!,NewPowerHelper.currentPowerSetWeight)
            log("calcRopeDoWork - value2: power=${value.value2!!.first} dy=${value.value2!!.second.dy} start=${value.value2!!.second.start} end=${value.value2!!.second.end} work=$work weight=${NewPowerHelper.currentPowerSetWeight}")
            if (value.value2!!.first==AekePowerCoreAdapter.Power.LEFT){
                value.leftXiangXinDoWork+=work
            }else{
                value.rightXiangXinDoWork+=work
            }
        }
    }

    protected fun postAvgRopeLengthEvent(){
        log("postAvgRopeLengthEvent")
        doWorkAvgRopeLengthObservable.setChanged()
        doWorkAvgRopeLengthObservable.notifyObservers(multiInitStartPoint to multiInitDistance)
    }

    protected fun postXxLxWaveEvent(power:AekePowerCoreAdapter.Power,data:IPowerRopeWaveCalc.RopeWaveData){
        ropeXxLxPauseStateObservable.setChanged()
        ropeXxLxPauseStateObservable.notifyObservers(power to data)
    }

    protected fun postFromRopeStartPointDyEvent(leftDy:Long,rightDy:Long){
        fromRopeStartPointDyEventObservable.setChanged()
        fromRopeStartPointDyEventObservable.notifyObservers(leftDy to rightDy)
    }

    protected fun postRopeXxLxTimeObservableEvent(value:Triple<Int,Array<IPowerRopeWaveCalc.RopeWaveData>,Array<IPowerRopeWaveCalc.RopeWaveData>?>){
        ropeXxLxTimeObservable.setChanged()
        ropeXxLxTimeObservable.notifyObservers(IPowerCalcCounter.XxLxTimeData(value.first,value.second,value.third))
    }

    protected fun round2NumerPoint(value:Float):Float{
        return (value * 100).toInt() / 100.0f
    }

    /**
     * 切换手柄模式
     */
    override fun switchHandShankMode(isImmediatelyStartCalc:Boolean){
        log("switchHandShankMode")
        currentMode = HardwareMode.HandShankMode
        NewPowerHelper.setBalanceMode(false)
        if (isImmediatelyStartCalc){
            startCalcCount()
        }
    }

    /**
     * 切换横杠模式
     */
    override fun switchCrossBarMode(isImmediatelyStartCalc:Boolean){
        log("switchCrossBarMode")
        currentMode = HardwareMode.CrossBarMode
        NewPowerHelper.setBalanceMode(true)
        if (isImmediatelyStartCalc){
            startCalcCount()
        }
    }

    private fun log(msg: String) {
        Log.d("DoubleRopePowerCalcCounter_$logTag", msg)
    }

    override fun observeRopeXxLxPauseEvent(callback: AekeObserver<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>): () -> Unit {
        ropeXxLxPauseStateObservable.addObserver(callback)
        return {
            ropeXxLxPauseStateObservable.deleteObserver(callback)
        }
    }

    override fun observeFromRopeStartPointDy(callback: AekeObserver<Pair<Long, Long>>): () -> Unit {
        fromRopeStartPointDyEventObservable.addObserver(callback)
        return {
            fromRopeStartPointDyEventObservable.deleteObserver(callback)
        }
    }

    override fun observeRopeXxLxTimeDataEvent(callback: AekeObserver<IPowerCalcCounter.XxLxTimeData>): () -> Unit {
        ropeXxLxTimeObservable.addObserver(callback)
        return {
            ropeXxLxTimeObservable.deleteObserver(callback)
        }
    }

    override fun deleteObserver(callback: Any) {
        doWorkAvgRopeLengthObservable.deleteObserver(callback)
        doWorkCalcCountObservable.deleteObserver(callback)
        doWorkCalcCount2Observable.deleteObserver(callback)
        doWorkCalcDataObservable.deleteObserver(callback)
        confirmInitDistanceAndStartPointObservable.deleteObserver(callback)
        ropeXxLxPauseStateObservable.deleteObserver(callback)
        ropeArriveStartPointObservable.deleteObserver(callback)
        fromRopeStartPointDyEventObservable.deleteObserver(callback)
    }

}