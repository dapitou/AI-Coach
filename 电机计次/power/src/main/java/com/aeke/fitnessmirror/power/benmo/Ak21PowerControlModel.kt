package com.aeke.fitnessmirror.power.benmo

internal class Ak21PowerControlModel private constructor(
    override val m1Power:Int,
    override val m1Rate:Int,
    override val m1Distance:Int,
    override val m1LaDongCount:Int,
    override val m1ErrorCode:Int,
    override val m2Power:Int,
    override val m2Rate:Int,
    override val m2Distance:Int,
    override val m2LaDongCount:Int,
    override val m2ErrorCode:Int,
    override val currentMode:String,
    override val m1Temp:Int,
    override val m2Temp:Int,
    override val m1SportTime:Int,
    override val m2SportTime:Int,
    override val m1State:Int,
    override val m2State:Int,
    override val controlTemp:Int,
    override val driverPowerState:Int,
    override val m1SportState:Int,
    override val m2SportState:Int,
    override val m1Warn:Int,
    override val m2Warn:Int,
    override val mDriverTemp:Int,
    override val mDriverV:Int,
    override val mFanState:Int, override val m1TouchKey: Int, override val m2TouchKey: Int,

    ): PowerControlModelInterface {
    companion object{
        fun create(hex:String): Ak21PowerControlModel?{
            try {
                val head:String = hex.substring(0,4)
                if (head!="6402"){
                    throw IllegalArgumentException("head not 6402")
                }
                val currentMode:String = hex.substring(4,6)
                val m1Power:Int = hex.substring(6,10).toInt(16) / 100
                val m1Rate:Int = hex.substring(10,14).toInt(16)
                val m1Distance:Int = formatSigned(hex.substring(14,18).toInt(16))
                val m1LaDongCount:Int = hex.substring(18,22).toInt(16)
                //电机1训练状态
                val m1SportState:Int = hex.substring(22,24).toInt(16)
                val m1SportTime:Int = hex.substring(24,28).toInt(16)

                val m2Power:Int = hex.substring(28,32).toInt(16) / 100
                val m2Rate:Int = hex.substring(32,36).toInt(16)
                val m2Distance:Int = formatSigned(hex.substring(36,40).toInt(16))
                val m2LaDongCount:Int = hex.substring(40,44).toInt(16)
                //电机2训练状态
                val m2SportState:Int = hex.substring(44,46).toInt(16)
                val m2SportTime:Int = hex.substring(46,50).toInt(16)

                val m1ErrorCode:Int = hex.substring(50,52).toInt(16)
                val m2ErrorCode:Int = hex.substring(52,54).toInt(16)
                val m1State:Int = hex.substring(54,56).toInt(16)
                val m2State:Int = hex.substring(56,58).toInt(16)
                val m1Warn:Int = hex.substring(58,60).toInt(16)
                val m2Warn:Int = hex.substring(60,62).toInt(16)
                val m1Temp:Int = hex.substring(62,64).toInt(16)
                val m2Temp:Int = hex.substring(64,66).toInt(16)
                val mDriverTemp:Int = hex.substring(66,68).toInt(16)
                val mDriverV:Int = hex.substring(68,72).toInt(16)
                val mFanState:Int = hex.substring(72,74).toInt(16)
                val crc8:String = hex.substring(74,76)
                val crc8_2:String = hex.substring(0,74).crc8()
                val m1TouchKey:Int = m1State and 0x01
                val m2TouchKey:Int = m2State and 0x01
                if (crc8!=crc8_2){
                    throw IllegalArgumentException("crc8 error crc8:${crc8} crc8_2:${crc8_2}")
                }
                return Ak21PowerControlModel(
                    m1Power,
                    m1Rate,
                    m1Distance,
                    m1LaDongCount,
                    m1ErrorCode,
                    m2Power,
                    m2Rate,
                    m2Distance,
                    m2LaDongCount,
                    m2ErrorCode,
                    currentMode,
                    m1Temp,
                    m2Temp,
                    m1SportTime,
                    m2SportTime,
                    m1State,
                    m2State,-1, -1, m1SportState,m2SportState,m1Warn,m2Warn,mDriverTemp,mDriverV,mFanState,m1TouchKey,m2TouchKey)
            }catch (e:Exception){
                e.printStackTrace()
            }
            return null
        }
    }



    override fun toFormatString():String{
        return """
            ${System.currentTimeMillis()}
            模式=${getModeName(currentMode)}, 
            电机1的力量值=$m1Power kg, 
            电机1的速度值=${formatSigned(m1Rate)} cm/s, 
            电机1的距离值=$m1Distance cm, 
            电机1的拉动次数=$m1LaDongCount, 
            电机1训练状态=${getStateName(m1SportState)}
            电机1单次运动时间=${m1SportTime * 0.01}s
            电机2的力量值=$m2Power kg, 
            电机2的速度值=${formatSigned(m2Rate)} cm/s, 
            电机2的距离值=$m2Distance cm, 
            电机2的拉动次数=$m2LaDongCount, 
            电机2训练状态=${getStateName(m2SportState)}
            电机2单次运动时间=${m2SportTime * 0.01}s
            电机1的故障码(0x00)=$m1ErrorCode, 
            电机2的故障码(0x00)=$m2ErrorCode, 
            电机1状态=$m1State
            电机2状态=$m2State
            电机1的报警码=$m1Warn, 
            电机2的报警码=$m2Warn
            电机1的温度=$m1Temp °C, 
            电机2的温度=$m2Temp °C, 
            驱动模组温度=$mDriverTemp °C, 
            驱动模组母线电压=$mDriverV, 
            电机风扇状态=$mFanState,
            电机1踏板按键=$m1TouchKey,
            电机2踏板按键=$m2TouchKey
        """.trimIndent()
    }

    override fun toMotor1String(): String {
        return """
            力量=$m1Power kg
            速度=${formatSigned(m1Rate)} cm/s
            距离=$m1Distance cm
            拉动次数=$m1LaDongCount
            训练状态=${getStateName(m1SportState)}
            单次运动时间=${m1SportTime * 0.01}s
            故障码(0x00)=$m1ErrorCode
            状态=$m1State
            报警码=$m1Warn
            温度=$m1Temp °C
            踏板按键=$m1TouchKey
        """.trimIndent()
    }

    override fun toMotor2String(): String {
        return """
            力量=$m2Power kg
            速度=${formatSigned(m2Rate)} cm/s
            距离=$m2Distance cm
            拉动次数=$m2LaDongCount
            训练状态=${getStateName(m2SportState)}
            单次运动时间=${m2SportTime * 0.01}s
            故障码(0x00)=$m2ErrorCode
            状态=$m2State
            报警码=$m2Warn
            温度=$m2Temp °C
            踏板按键=$m2TouchKey
        """.trimIndent()
    }

    private fun getModeName(hex:String):String{
        return when(hex.toUpperCase()){
            "00" -> "标准模式"
            "01" -> "等速模式"
            "02" -> "弹力模式"
            "03" -> "划船模式"
            "04" -> "平衡模式"
            "05" -> "重力模式"
            "FA" -> "开始运动"
            "FB" -> "暂停运动"
            "FC" -> "起点重置"
            "55" -> "失能模式"
            "AA" -> "使能模式"
            "EE" -> "收绳中"
            else->"UNKNOWN ${hex}"
        }
    }

    private fun getStateName(state:Int):String{
        return when(state){
            0->{
                "失能"
            }
            1->{
                "使能慢速"
            }
            2->{
                "原点状态"
            }
            3->{
                "训练拉起"
            }
            4->{
                "训练收绳"
            }
            5->{
                "训练暂停"
            }
            else ->"UNKNOWN ${state}"
        }
    }

    override fun toString(): String {
        return "Ak21PowerControlModel(currentMode='$currentMode', m1Power=$m1Power, m1Rate=$m1Rate, m1Distance=$m1Distance, m1LaDongCount=$m1LaDongCount, m1ErrorCode=$m1ErrorCode, m2Power=$m2Power, m2Rate=$m2Rate, m2Distance=$m2Distance, m2LaDongCount=$m2LaDongCount, m2ErrorCode=$m2ErrorCode, m1Temp=$m1Temp, m2Temp=$m2Temp, m1SportTime=$m1SportTime, m2SportTime=$m2SportTime, m1State=$m1State, m2State=$m2State, m1SportState=$m1SportState, m2SportState=$m2SportState, m1Warn=$m1Warn, m2Warn=$m2Warn, mDriverTemp=$mDriverTemp, mDriverV=$mDriverV, mFanState=$mFanState)， m1TouchKey=$m1TouchKey, m2TouchKey=$m2TouchKey)"
    }

}
// 处理有符号数（将16位无符号数转为有符号数）
fun formatSigned(value: Int): Int {
    // 如果最高位为1，说明是负数（补码表示）
    return if (value > 32767) {
        (value - 65536)
    } else {
        value
    }
}