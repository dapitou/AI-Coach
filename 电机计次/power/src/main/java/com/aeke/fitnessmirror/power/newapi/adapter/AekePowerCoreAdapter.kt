package com.aeke.fitnessmirror.power.newapi.adapter

import java.util.function.Consumer

/**
 * 重量都是kg
 * 长度都是mm
 * 此接口所有的回调除特殊说明都不能在主线程回调
 * 数据方向都是 电机->app
 * 数据方向 app->电机 主要作用于UI的表现的在上面一层封装实现
 * 作用:隔离不同电机差异,尽量减少方法实现
 */
interface AekePowerCoreAdapter{

    fun init()

    /**
     * 获得当前时刻电机信息,包括版本、重量、模式等
     */
    fun getPowerInfo(): PowerInfo

    fun setPowerInfoTickCallback(callback: Consumer<AekePowerCoreAdapter.PowerInfo>)

    /**
     * 设置电机重量和模式
     * kg
     */
    fun setPower(mode: PowerMode)

    /**
     * 获得电机版本,内部发送获取电机版本的指令,两秒后必须回调callback,不管电机版本是否正确获取
     */
    fun getPowerVersion(callback:Consumer<Long>?)

    /**
     * 重启电机芯片程序
     */
    fun rebootPowerChip()

    /**
     * 电机错误码回调
     * 错误码只有在变化时回调一次,相同错误码只回调一次,不重复回调
     * value==0时,说明电机恢复正常
     * 数据方向:电机->app
     */
    fun setPowerErrorCodeListener(callback: ((Int)->Unit)?)

    fun isSupportPowerSmooth():Boolean

    fun isSupportHandOffProtect():Boolean

    fun setHandsOffProtect(enable: Boolean)

    fun setBalanceMode(isOpen:Boolean)

    fun setResetMode()

    data class PowerInfo(
        //版本
        var version:Long,
        //左边绳子实时长度 mm
        var ropeLeftLength:Int = 0,
        //右边绳子实时长度 mm
        var ropeRightLength:Int = 0,
        //电机的实时重量,单位0.01kg
        var ropeLeftWeight:Float = 200f,
        //电机的实时重量,单位0.01kg
        var ropeRightWeight: Float = 200f,
        //左电机速度单位cm/s 向心为正，离心为负
        var leftSpeed: Int = 0,
        //右电机速度单位cm/s 向心为正，离心为负
        var rightSpeed: Int = 0,
        var m1TouchKey: Int = 0,
        var m2TouchKey: Int = 0,
    )

    interface PowerMode{
        var weight:Float
        var isSmooth:Boolean
        var smoothRate:Int
        //卸力
        data class UNLOAD(override var weight: Float = 2f,override var isSmooth:Boolean = false,override var smoothRate:Int = 0) : PowerMode
        //标准模式
        data class STANDARD(override var weight: Float,override var isSmooth:Boolean = false,override var smoothRate:Int = 0) : PowerMode
        //向心
        data class XiangXin(override var weight: Float,override var isSmooth:Boolean = false,override var smoothRate:Int = 0) : PowerMode
        //离心
        data class LiXin(override var weight: Float,override var isSmooth:Boolean = false,override var smoothRate:Int = 0) : PowerMode
        //划船
        data class HuaChuan(override var weight: Float,override var isSmooth:Boolean = false,override var smoothRate:Int = 0) : PowerMode
        //划船
        data class TanLi(override var weight: Float,override var isSmooth:Boolean = false,override var smoothRate:Int = 0) : PowerMode

    }

    /**
     * 左右电机
     */
    enum class Power{
        LEFT,
        RIGHT,
    }

}

