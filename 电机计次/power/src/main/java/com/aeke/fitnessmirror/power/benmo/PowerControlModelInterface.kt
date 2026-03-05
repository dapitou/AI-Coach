package com.aeke.fitnessmirror.power.benmo

interface PowerControlModelInterface {
    val m1Power: Int
    val m1Rate: Int
    val m1Distance: Int
    val m1LaDongCount: Int
    val m1ErrorCode: Int
    val m2Power: Int
    val m2Rate: Int
    val m2Distance: Int
    val m2LaDongCount: Int
    val m2ErrorCode: Int
    val currentMode: String
    val m1Temp: Int
    val m2Temp: Int
    val m1SportTime: Int
    val m2SportTime: Int
    val m1State: Int
    val m2State: Int
    val controlTemp:Int
    val driverPowerState:Int
    fun toFormatString():String

    //AK21
    val m1SportState:Int
    val m2SportState:Int
    val m1Warn:Int
    val m2Warn:Int
    val mDriverTemp:Int
    val mDriverV:Int
    val mFanState:Int
    val m1TouchKey:Int //0:无按键,踏板未准备好； 1：有按键，踏板已准备好；数据来源m1State第一个字节
    val m2TouchKey:Int //0:无按键,踏板未准备好； 1：有按键，踏板已准备好；数据来源m2State第一个字节

    // 分区格式化方法
    fun toMotor1String():String
    fun toMotor2String():String
}