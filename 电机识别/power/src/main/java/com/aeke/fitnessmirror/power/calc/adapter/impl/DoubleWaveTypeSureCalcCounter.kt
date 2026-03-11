package com.aeke.fitnessmirror.power.calc.adapter.impl

import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.calc.PowerCalcConfig
import com.aeke.fitnessmirror.power.calc.adapter.BasePowerCalcCounter
import com.aeke.fitnessmirror.power.calc.adapter.IPowerRopeWaveCalc
import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

/**
 * 专门计算向心离心时间的类
 */
open class DoubleWaveTypeSureCalcCounter(): BasePowerCalcCounter() {

    private var firstXxWaveType:IPowerRopeWaveCalc.RopeWaveData? = null
    private var secondXxWaveType:IPowerRopeWaveCalc.RopeWaveData? = null
    private var waitXxFrameCount:Int = 0
    private var xxEndFrameCount:Int = 0


    private var firstLxWaveType:IPowerRopeWaveCalc.RopeWaveData? = null
    private var secondLxWaveType:IPowerRopeWaveCalc.RopeWaveData? = null
    private var waitLxFrameCount:Int = 0

    override fun init(
        config: PowerCalcConfig,
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        ropeGetter: IRopeGetter
    ) {
        super.init(config, powerRopeWaveCalc, ropeGetter)
        powerRopeWaveCalc.observeRopeWaveType(object :AekeObserver<IPowerRopeWaveCalc.RopeWaveData>{
            override fun update(value: IPowerRopeWaveCalc.RopeWaveData) {
                onHandlePowerCalcCount(value)
            }
        })
    }

    override fun onFps(value: Long) {
        super.onFps(value)
        //向心相关
        if (firstXxWaveType!=null&&secondXxWaveType!=null){
            onSureXxRopeWaveType(arrayOf(firstXxWaveType!!,secondXxWaveType!!))
            resetXxData()
        }else if (firstXxWaveType!=null){
            waitXxFrameCount++
            if (waitXxFrameCount>2){
                onSureXxRopeWaveType(arrayOf(firstXxWaveType!!))
                resetXxData()
            }
        }

        //离心相关
        if (firstLxWaveType!=null&&secondLxWaveType!=null){
            onSureLxRopeWaveTypeInternal(arrayOf(firstLxWaveType!!,secondLxWaveType!!))
            resetLxData()
        }else if (firstLxWaveType!=null){
            waitLxFrameCount++
            if (waitLxFrameCount>2){
                onSureLxRopeWaveTypeInternal(arrayOf(firstLxWaveType!!))
                resetLxData()
            }
        }

    }

    private fun onHandlePowerCalcCount(value: IPowerRopeWaveCalc.RopeWaveData) {
        if (value.dy==0){
            return
        }
        if (value.type==AekePowerCoreAdapter.Power.LEFT){
            if (value.dy>0){
                onXxLeft(value)
            }else{
                onLxLeft(value)
            }
        }else{
            if (value.dy>0){
                onXxRight(value)
            }else{
                onLxRight(value)
            }
        }
    }

    private fun onLxLeft(value: IPowerRopeWaveCalc.RopeWaveData){
        if (firstLxWaveType==null){
            firstLxWaveType = value
        }else if (secondLxWaveType==null){
            secondLxWaveType = value
        }
    }

    private fun onLxRight(value: IPowerRopeWaveCalc.RopeWaveData){
        if (firstLxWaveType==null){
            firstLxWaveType = value
        }else if (secondLxWaveType==null){
            secondLxWaveType = value
        }
    }

    private fun onXxLeft(value: IPowerRopeWaveCalc.RopeWaveData){
        if (firstXxWaveType==null){
            firstXxWaveType = value
        }else if (secondXxWaveType==null){
            secondXxWaveType = value
        }
    }

    private fun onXxRight(value: IPowerRopeWaveCalc.RopeWaveData){
        if (firstXxWaveType==null){
            firstXxWaveType = value
        }else if (secondXxWaveType==null){
            secondXxWaveType = value
        }
    }

    open fun onSureXxRopeWaveType(values: Array<IPowerRopeWaveCalc.RopeWaveData>){
        xxEndFrameCount = values.minOf { it.end }
        resetLxData()
    }

    private fun onSureLxRopeWaveTypeInternal(values: Array<IPowerRopeWaveCalc.RopeWaveData>){
        val lxStartFrame = values.maxOf { it.start }
        if (xxEndFrameCount<=lxStartFrame){
            onSureLxRopeWaveType(values)
        }
    }

    open fun onSureLxRopeWaveType(values: Array<IPowerRopeWaveCalc.RopeWaveData>){

    }

    private fun resetXxData(){
        firstXxWaveType = null
        secondXxWaveType = null
        waitXxFrameCount = 0
    }

    private fun resetLxData(){
        firstLxWaveType = null
        secondLxWaveType = null
        waitLxFrameCount = 0
        xxEndFrameCount = 0
    }

    override fun stopCalcCount() {
        super.stopCalcCount()
        resetLxData()
        resetXxData()
    }

}