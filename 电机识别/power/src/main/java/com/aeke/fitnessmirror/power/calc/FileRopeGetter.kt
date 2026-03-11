package com.aeke.fitnessmirror.power.calc

import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import java.io.File

class FileRopeGetter: IRopeGetter {
    //private var filePath:String = "/sdcard/rope_test/绳子数据/ssssssssssssssss_left.csv"
    //private var filePath:String = "/sdcard/rope_test/绳子数据/超市_left.csv"
    //private var leftFilePath:String = "/sdcard/rope_test/随心练模拟用户循环训练.csv"
    //private var rightFilePath:String = "/sdcard/rope_test/随心练模拟用户循环训练.csv"
    private var leftFilePath:String = "/sdcard/rope_test/qqqqqqqqqqqqqqqeeee_right.csv"
    private var rightFilePath:String = "/sdcard/rope_test/qqqqqqqqqqqqqqqeeee_right.csv"
    //private var filePath:String = "/sdcard/rope_test/1111111111_left2.csv"
    //private var filePath:String = "/sdcard/rope_test/绳子数据/ETWJ+TJ_S_left000000000000.csv"
    //private var filePath:String = "/sdcard/rope_test/1111111111_left.csv"
    //private var filePath:String = "/sdcard/rope_test/绳子数据/ETWJ_S_left.csv"
    //private var filePath:String = "/sdcard/rope_test/绳子数据/ETWJ_JT_right.csv"
    private var leftRopeData:MutableList<Float> = mutableListOf()
    private var rightRopeData:MutableList<Float> = mutableListOf()
    private var flag:Int = 0

    private var leftFrame:Int = 0
    private var rightFrame:Int = 2
    init {
        try {
            var file = File(leftFilePath)
            leftRopeData = file.readLines().map {
                it.split(",")[1].toFloat()
            }.toMutableList()
            file = File(rightFilePath)
            rightRopeData = file.readLines().map {
                it.split(",")[1].toFloat()
            }.toMutableList()
        }catch (e:Exception){
            e.printStackTrace()
        }
        leftRopeData = rightRopeData

    }

    override fun getLeftRopeLength():Long{
        flag++
        if (leftRopeData.isEmpty()){
            return 0
        }
        if (leftFrame>=leftRopeData.size){
            leftFrame = 0
        }

        return leftRopeData[leftFrame++].toLong()//-45
    }

    override fun getRightRopeLength():Long{
        //return 0
        if (rightRopeData.isEmpty()){
            return 0
        }
        if (rightFrame>=rightRopeData.size){
            rightFrame = 0?:(Math.random()*200).toInt()
        }
        return rightRopeData[rightFrame++].toLong()//-45
    }

    fun reset(){
        leftFrame = 0
        rightFrame = 0
    }

}