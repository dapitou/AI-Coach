package com.aeke.fitnessmirror.power.calc.adapter.impl

import android.util.Log
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.IPowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.calc.adapter.PowerRopeUtils
import com.aeke.fitnessmirror.power.constance.HardwareMode
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

/**
 * 包含离心做功等计算功能的
 * TODO(离心做功未完成,等后续产品需求)
 */
open class LxDoubleRopePowerCalcCounter:DoubleRopePowerCalcCounter() {

    private val doWorkLxCalcCount2Observable: AekeObservable<Pair<AekePowerCoreAdapter.Power?, IPowerCalcCounter.CountType>> = AekeObservable()
    //做功w
    private val doWorkLxCalcDataObservable: AekeObservable<IPowerCalcCounter.DoWokeData> = AekeObservable()
    //做功计次增量
    private val doWorkLxCalcCountObservable: AekeObservable<Int> = AekeObservable()
    //离心行程
    protected val lxDistanceObservable: AekeObservable<Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>> = AekeObservable()
    protected val xxDistanceObservable: AekeObservable<Array<Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>>> = AekeObservable()
    private var frameCount:Int = Int.MAX_VALUE
    private var firstPower:AekePowerCoreAdapter.Power? = null
    private var leftStartFrame:Int = Int.MAX_VALUE
    private var rightStartFrame:Int = Int.MAX_VALUE
    private var leftEndFrame:Int = Int.MAX_VALUE
    private var rightEndFrame:Int = Int.MAX_VALUE
    private var lockLeftCalc:Boolean = true
    private var lockRightCalc:Boolean = true

    private var currentWaitLxDistance:Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>? = null
    private var currentWaitLxCount:Int = 0

    private var currentWaitXxDistance:Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>? = null
    private var currentWaitXxCount:Int = 0

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter, true)
        //向心单双边判断
        observeFromRopeStartPointDy(object :AekeObserver<Pair<Long,Long>>{

            private fun resetSingleDoubleCalcVar(countType: IPowerCalcCounter.CountType){
                if (countType== IPowerCalcCounter.CountType.Single){
                    if (firstPower== AekePowerCoreAdapter.Power.LEFT){
                        lockLeftCalc = true
                    }else if (firstPower== AekePowerCoreAdapter.Power.RIGHT){
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
                onCalc(value)
                onDistanceThreshold(value)
            }

            private fun onCalc(value: Pair<Long, Long>) {
                if (firstPower!=null){
                    if (frameCount!=Int.MAX_VALUE){
                        frameCount++
                        if (frameCount>=3){
                            //TODO 发出单边事件
                            val dy:Long
                            val data:Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>
                            if (firstPower== AekePowerCoreAdapter.Power.LEFT){
                                dy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(leftEndFrame))-multiInitStartPoint
                                data = firstPower!! to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,dy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            }else{
                                dy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(rightEndFrame))-multiInitStartPoint
                                data = firstPower!! to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,rightStartFrame,rightEndFrame,dy.toInt(),powerWaveCalc.ropeData.get(rightStartFrame),powerWaveCalc.ropeData.get(rightEndFrame))
                            }
                            postLxDoWorkEvent(
                                IPowerCalcCounter.DoWokeData(
                                    IPowerCalcCounter.CountType.Single,
                                    NewPowerHelper.currentPowerSetWeight,data,null))
                            postLxRopeCalcEvent(firstPower, IPowerCalcCounter.CountType.Single)
                            this.resetSingleDoubleCalcVar(IPowerCalcCounter.CountType.Single)
                        }
                    }
                }
                val leftDy = value.first
                val rightDy = value.second
                if (firstPower!= AekePowerCoreAdapter.Power.LEFT){
                    if (!lockLeftCalc&&leftDy<=multiInitDistance*config.DISTANCE_THRESHOLD){
                        leftEndFrame = powerWaveCalc.currentFrameNumber.toInt()
                        if (firstPower==null){
                            firstPower= AekePowerCoreAdapter.Power.LEFT
                            frameCount = 0
                        }else{
                            //TODO 发出双边事件
                            val rightDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(rightEndFrame))-multiInitStartPoint
                            val rightData = AekePowerCoreAdapter.Power.RIGHT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,rightDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            val leftDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(leftEndFrame))-multiInitStartPoint
                            val leftData = AekePowerCoreAdapter.Power.LEFT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,leftDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            postLxDoWorkEvent(
                                IPowerCalcCounter.DoWokeData(
                                    IPowerCalcCounter.CountType.Double,
                                    NewPowerHelper.currentPowerSetWeight,rightData,leftData))
                            postLxRopeCalcEvent(null, IPowerCalcCounter.CountType.Double)
                            this.resetSingleDoubleCalcVar(IPowerCalcCounter.CountType.Double)
                        }
                    }
                }
                if (firstPower!= AekePowerCoreAdapter.Power.RIGHT){
                    if (!lockRightCalc&&rightDy<=multiInitDistance*config.DISTANCE_THRESHOLD){
                        rightEndFrame = powerWaveCalc.currentFrameNumber.toInt()
                        if (firstPower==null){
                            firstPower= AekePowerCoreAdapter.Power.RIGHT
                            frameCount = 0
                        }else{
                            //TODO 发出双边事件
                            val rightDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(rightEndFrame))-multiInitStartPoint
                            val rightData = AekePowerCoreAdapter.Power.RIGHT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,rightDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            val leftDy = PowerRopeUtils.getLeftRopeLength(powerWaveCalc.ropeData.get(leftEndFrame))-multiInitStartPoint
                            val leftData = AekePowerCoreAdapter.Power.LEFT to IPowerRopeWaveCalc.RopeWaveData(firstPower!!,leftStartFrame,leftEndFrame,leftDy.toInt(),powerWaveCalc.ropeData.get(leftStartFrame),powerWaveCalc.ropeData.get(leftEndFrame))
                            postLxDoWorkEvent(
                                IPowerCalcCounter.DoWokeData(
                                    IPowerCalcCounter.CountType.Double,
                                    NewPowerHelper.currentPowerSetWeight,rightData,leftData))
                            postLxRopeCalcEvent(null, IPowerCalcCounter.CountType.Double)
                            this.resetSingleDoubleCalcVar(IPowerCalcCounter.CountType.Double)
                        }
                    }
                }
            }


            private fun onDistanceThreshold(value: Pair<Long, Long>) {
                if (value.first>=multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD){
                    lockLeftCalc = false
                    leftStartFrame = powerWaveCalc.currentFrameNumber.toInt()
                }
                if (value.second>=multiInitDistance*config.DISTANCE_EFFECTIVE_THRESHOLD){
                    lockRightCalc = false
                    rightStartFrame = powerWaveCalc.currentFrameNumber.toInt()
                }
            }
        })

        observeLxDoWorkCalcCountTypeData(object :AekeObserver<Pair<AekePowerCoreAdapter.Power?, IPowerCalcCounter.CountType>>{
            override fun update(value: Pair<AekePowerCoreAdapter.Power?, IPowerCalcCounter.CountType>) {
                if (currentMode== HardwareMode.HandShankMode){
                    if (value.second==IPowerCalcCounter.CountType.Double){
                        postLxRopeCalcEvent(1)
                    }else if (value.second==IPowerCalcCounter.CountType.Single){
                        postLxRopeCalcEvent(1)
                    }
                }else{
                    if (value.second==IPowerCalcCounter.CountType.Double){
                        postLxRopeCalcEvent(1)
                    }else if (value.second==IPowerCalcCounter.CountType.Single){
                        //return
                    }
                }
            }

        })

        observeRopeXxLxPauseEvent(object :AekeObserver<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>{
            override fun update(value: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>) {
                val datas = value.second
                val type = value
                if (datas.dy>=0){
                    return
                }
                val value1 = currentWaitLxDistance
                if (value1!=null){
                    //TODO 离心双边
                    val value2 = value
                    lxDistanceObservable.setChanged()
                    lxDistanceObservable.postChanged(arrayOf(value1,value2))
                    currentWaitLxCount = 0
                    currentWaitLxDistance = null
                }else{
                    currentWaitLxDistance = value
                }
            }

        })
        observeRopeXxLxPauseEvent(object :AekeObserver<Pair<AekePowerCoreAdapter.Power,IPowerRopeWaveCalc.RopeWaveData>>{
            override fun update(value: Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>) {
                val datas = value.second
                val type = value
                if (datas.dy<=0){
                    return
                }
                val value1 = currentWaitXxDistance
                if (value1!=null){
                    //TODO 离心双边
                    val value2 = value
                    xxDistanceObservable.setChanged()
                    xxDistanceObservable.postChanged(arrayOf(value1,value2))
                    currentWaitXxCount = 0
                    currentWaitXxDistance = null
                }else{
                    currentWaitXxDistance = value
                }
            }

        })

    }

    override fun onFps(value: Long) {
        super.onFps(value)
        if (currentWaitLxDistance!=null){
            currentWaitLxCount++
            if (currentWaitLxCount>=3){
                //TODO 离心单边
                lxDistanceObservable.setChanged()
                lxDistanceObservable.postChanged(arrayOf(currentWaitLxDistance!!))
                currentWaitLxCount = 0
                currentWaitLxDistance = null
            }
        }else{
            currentWaitLxCount = 0
        }


        if (currentWaitXxDistance!=null){
            currentWaitXxCount++
            if (currentWaitXxCount>=3){
                //TODO 离心单边
                xxDistanceObservable.setChanged()
                xxDistanceObservable.postChanged(arrayOf(currentWaitXxDistance!!))
                currentWaitXxCount = 0
                currentWaitXxDistance = null
            }
        }else{
            currentWaitXxCount = 0
        }

    }

    protected fun postLxDoWorkEvent(value:IPowerCalcCounter.DoWokeData){
        //TODO 未实现
        log("postLxDoWorkEvent")
        doWorkLxCalcDataObservable.setChanged()
        doWorkLxCalcDataObservable.notifyObservers(value)
    }

    protected fun postLxRopeCalcEvent(power:AekePowerCoreAdapter.Power?,countType:IPowerCalcCounter.CountType){
        log("postLxRopeCalcEvent")
        doWorkLxCalcCount2Observable.setChanged()
        doWorkLxCalcCount2Observable.notifyObservers(power to countType)
    }

    protected fun postLxRopeCalcEvent(addCount:Int){
        log("postLxRopeCalcEvent")
        doWorkLxCalcCountObservable.setChanged()
        doWorkLxCalcCountObservable.notifyObservers(addCount)
    }

    fun observeLxDoWorkCalcCountData(callback: AekeObserver<Int>): () -> Unit {
        doWorkLxCalcCountObservable.addObserver(callback)
        return {
            doWorkLxCalcCountObservable.deleteObserver(callback)
        }
    }

    fun observeLxDoWorkCalcDataData(callback: AekeObserver<IPowerCalcCounter.DoWokeData>): () -> Unit {
        doWorkLxCalcDataObservable.addObserver(callback)
        return {
            doWorkLxCalcDataObservable.deleteObserver(callback)
        }
    }

    fun observeLxDoWorkCalcCountTypeData(callback: AekeObserver<Pair<AekePowerCoreAdapter.Power?,IPowerCalcCounter.CountType>>): () -> Unit {
        doWorkLxCalcCount2Observable.addObserver(callback)
        return {
            doWorkLxCalcCount2Observable.deleteObserver(callback)
        }
    }

    private fun log(msg:String){
        Log.i("LxDoubleRopePowerCalcCounter",msg)
    }

}

