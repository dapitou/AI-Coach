package com.aeke.fitnessmirror.power.benmo
internal class PowerControlModel private constructor(
    override val m1Power:Int,
    override val m1Rate:Int,
    override val m1Distance:Int,
    override val m1LaDongCount:Int,
    override val m1ErrorCode:Int,
    override val m2Power:Int,
    override val m2Rate:Int,
    override val m2Distance:Int,
    override val m2LaDongCount:Int,
    override val controlTemp:Int,
    override val m2ErrorCode:Int,
    override val currentMode:String,
    override val m1Temp:Int,
    override val m2Temp:Int,
    override val driverPowerState:Int,
    override val m1SportTime:Int,
    override val m2SportTime:Int,
    override val m1State:Int,
    override val m2State:Int,
    override val m1SportState: Int,
    override val m2SportState: Int,
    override val m1Warn: Int,
    override val m2Warn: Int,
    override val mDriverTemp: Int,
    override val mDriverV: Int,
    override val mFanState: Int, override val m1TouchKey: Int, override val m2TouchKey: Int
): PowerControlModelInterface {
    companion object {
        fun create(hex: String): PowerControlModel? {
            try {
                val head: String = hex.substring(0, 4)
                if (head != "0164") {
                    throw IllegalArgumentException("head not 0164")
                }
                val m1Power: Int = hex.substring(4, 8).toInt(16)
                val m1Rate: Int = hex.substring(8, 12).toInt(16)
                val m1Distance: Int = hex.substring(12, 16).toInt(16)
                val m1LaDongCount: Int = hex.substring(16, 18).toInt(16)
                val m1ErrorCode: Int = hex.substring(18, 20).toInt(16)
                val m2Power: Int = hex.substring(20, 24).toInt(16)
                val m2Rate: Int = hex.substring(24, 28).toInt(16)
                val m2Distance: Int = hex.substring(28, 32).toInt(16)
                val m2LaDongCount: Int = hex.substring(32, 34).toInt(16)
                val controlTemp: Int = hex.substring(34, 36).toInt(16)
                val m2ErrorCode: Int = hex.substring(36, 38).toInt(16)
                val currentMode: String = hex.substring(38, 40)
                val m1Temp: Int = hex.substring(40, 42).toInt(16)
                val m2Temp: Int = hex.substring(42, 44).toInt(16)
                val driverPowerState: Int = hex.substring(44, 46).toInt(16)
                val m1SportTime: Int = hex.substring(46, 50).toInt(16)
                val m2SportTime: Int = hex.substring(50, 54).toInt(16)
                val m1State: Int = hex.substring(54, 56).toInt(16)
                val m2State: Int = hex.substring(56, 58).toInt(16)
                val crc8: String = hex.substring(58, 60)
                val crc8_2: String = hex.substring(0, 58).crc8()
                if (crc8 != crc8_2) {
                    throw IllegalArgumentException("crc8 error crc8:${crc8} crc8_2:${crc8_2}")
                }
                return PowerControlModel(
                    m1Power,
                    m1Rate,
                    m1Distance,
                    m1LaDongCount,
                    m1ErrorCode,
                    m2Power,
                    m2Rate,
                    m2Distance,
                    m2LaDongCount,
                    controlTemp,
                    m2ErrorCode,
                    currentMode,
                    m1Temp,
                    m2Temp,
                    driverPowerState,
                    m1SportTime,
                    m2SportTime, m1State, m2State, 0, 0, 0, 0, 0, 0, 0,-1,-1
                )
            } catch (e: Exception) {
                e.printStackTrace()
            }
            return null
        }
    }

    override fun toFormatString():String{
        return """
            ${System.currentTimeMillis()}
            驱动模组当前模式='${getModeName(currentMode)}', 
            电机1的力量值=$m1Power kg, 
            电机1的速度值=$m1Rate cm/s, 
            电机1的距离值=$m1Distance cm, 
            电机1的拉动次数=$m1LaDongCount, 
            电机1的故障码(0x00)=$m1ErrorCode, 
            电机2的力量值=$m2Power kg, 
            电机2的速度值=$m2Rate cm/s, 
            电机2的距离值=$m2Distance cm, 
            电机2的拉动次数=$m2LaDongCount, 
            控制器的温度=$controlTemp °C, 
            电机2的故障码(0x00)=$m2ErrorCode, 
            电机1的温度=$m1Temp °C, 
            电机2的温度=$m2Temp °C, 
            驱动器当前电源状态(0x03)=$driverPowerState
            电机1单次运动时间=${m1SportTime*0.01}s
            电机2单次运动时间=${m2SportTime*0.01}s
            电机1状态=${getStateName(m1State)}
            电机2状态=${getStateName(m2State)}
        """.trimIndent()
    }

    override fun toMotor1String(): String {
        return """
            力量=$m1Power kg
            速度=${formatSigned(m1Rate)} cm/s
            距离=${formatSigned(m1Distance)} cm
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
            距离=${formatSigned(m2Distance)} cm
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
    // 处理有符号数（将16位无符号数转为有符号数）
    private fun formatSigned(value: Int): String {
        // 如果最高位为1，说明是负数（补码表示）
        return if (value > 32767) {
            (value - 65536).toString()
        } else {
            value.toString()
        }
    }

    private fun getModeName(hex:String):String{
        return when(hex.toUpperCase()){
            "00" -> "标准模式"
            "03" -> "等速模式"
            "04" -> "弹力模式"
            "07" -> "划船模式"
            "08" -> "平衡模式"
            "09" -> "原点模式"
            "0A" -> "飞鸟模式"
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
                "使能慢速收绳状态"
            }
            2->{
                "上电收绳完成后的原点状态"
            }
            3->{
                "训练时拉起的状态"
            }
            4->{
                "训练时收绳的状态"
            }
            else ->"UNKNOWN ${state}"
        }
    }

    override fun toString(): String {
        return "PowerControlModel(m1Power=$m1Power, m1Rate=$m1Rate, m1Distance=$m1Distance, m1LaDongCount=$m1LaDongCount, m1ErrorCode=$m1ErrorCode, m2Power=$m2Power, m2Rate=$m2Rate, m2Distance=$m2Distance, m2LaDongCount=$m2LaDongCount, controlTemp=$controlTemp, m2ErrorCode=$m2ErrorCode, currentMode='$currentMode', m1Temp=$m1Temp, m2Temp=$m2Temp, driverPowerState=$driverPowerState, m1SportTime=$m1SportTime, m2SportTime=$m2SportTime, m1State=$m1State, m2State=$m2State)"
    }
}
