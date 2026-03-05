package com.aeke.fitnessmirror.power.calc.adapter

import android.util.Log
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter

object PowerRopeUtils {

    fun createRopeLongData(leftRope: Long, rightRope: Long, frameNumber: Long): Long {
        val leftWaveType = (leftRope shr 12) and 0xF // 取左边波峰波谷类型 (高4位)
        val leftRopeLength = leftRope and 0xFFF // 取左边绳长 (低12位)

        val rightWaveType = (rightRope shr 12) and 0xF // 取右边波峰波谷类型 (高4位)
        val rightRopeLength = rightRope and 0xFFF // 取右边绳长 (低12位)

        val reserved = 0xFL // 保留位 (默认填充 0xF)

        return (leftWaveType shl 60) or
                (leftRopeLength shl 48) or
                (rightWaveType shl 44) or
                (rightRopeLength shl 32) or
                (reserved shl 28) or
                (frameNumber and 0xFFFFFFF) // 取帧号的低 28 位
    }

    fun getLeftRopeLength(rope: Long): Long {
        // 提取左边绳长（48-59bit）
        return ((rope shr 48) and 0xFFF)
    }

    fun getRightRopeLength(rope: Long): Long {
        // 提取右边绳长（32-43bit）
        return ((rope shr 32) and 0xFFF)
    }

    fun getLeftFrameIndex(rope: Long): Long {
        // 提取左边波峰波谷对应的帧号（0-27bit）
        return rope and 0xFFFFFFF
    }

    fun getRightFrameIndex(rope: Long): Long {
        // 右边波峰波谷共用相同帧号
        return rope and 0xFFFFFFF
    }

    fun getFrameIndex(rope: Long): Long {
        // 右边波峰波谷共用相同帧号
        return rope and 0xFFFFFFF
    }

    //重量解析相关
    fun createWeightLongData(leftWeight: Long, rightWeight: Long): Long {
        val left = (leftWeight and 0xFFFFFF) shl 40   // 左重量，占高24位
        val right = (rightWeight and 0xFFFFFF) shl 16 // 右重量，占中24位
        val reserved = 0xFFFFL                                // 保留位，默认填满(0xFFFF)，可以改

        return left or right or reserved
    }

    fun getLeftWeight(data: Long): Long {
        return ((data shr 40) and 0xFFFFFF)
    }

    fun getRightWeight(data: Long): Long {
        return ((data shr 16) and 0xFFFFFF)
    }

    //重量解析相关


    /*
    * W = (m*g+ma)*L
    * */
    internal fun getDoWork(
        powerRopeWaveCalc: IPowerRopeWaveCalc,
        doWorkData:Pair<AekePowerCoreAdapter.Power, IPowerRopeWaveCalc.RopeWaveData>,
        //kg
        weight: Float
    ): Float {
        val data = powerRopeWaveCalc.ropeData
        val weightData = powerRopeWaveCalc.weightData
        if (data.size<=3){
            return 0.0f
        }
        val getRopeLength: (Long) -> Long = when (doWorkData.first) {
            AekePowerCoreAdapter.Power.LEFT -> this::getLeftRopeLength
            AekePowerCoreAdapter.Power.RIGHT -> this::getRightRopeLength
        }

        val getRopeWeight: (Long) -> Long = when (doWorkData.first) {
            AekePowerCoreAdapter.Power.LEFT -> this::getLeftWeight
            AekePowerCoreAdapter.Power.RIGHT -> this::getRightWeight
        }

        val side = if (doWorkData.first == AekePowerCoreAdapter.Power.LEFT) "LEFT" else "RIGHT"
        val frameCount = doWorkData.second.end - doWorkData.second.start
        
        Log.d("PowerRopeUtils", "========== getDoWork 开始 ==========")
        Log.d("PowerRopeUtils", "侧边: $side, 重量: ${weight}kg")
        Log.d("PowerRopeUtils", "数据范围: start=${doWorkData.second.start}, end=${doWorkData.second.end}, frameCount=$frameCount")
        
        val g = 9.8f
        val dt = 0.1f
        var totalWork = 0.0f
        var positiveWorkCount = 0
        
        // 方案2: 计算平均绳长用于归一化
        var totalRopeLength = 0f
        var ropeLengthCount = 0
        
        for (i in (doWorkData.second.start + 1) until doWorkData.second.end) {
            val mps1 = getRopeLength(data[i - 1]) / 100.0f
            val mps2 = getRopeLength(data[i]) / 100.0f
            val mps3 = getRopeLength(data[i + 1]) / 100.0f

            //val w1 = getRopeWeight(weightData[i - 1]) / 100.0f
            //val w2 = getRopeWeight(weightData[i]) / 100.0f
            //val w3 = getRopeWeight(weightData[i + 1]) / 100.0f

            //加速度
            val a = (mps3 - 2 * mps2 + mps1) / (dt * dt)
            //牛顿
            //val f = ((w1+w2+w3)/3) * (g + a)
            val f = weight * (g + a)
            //dy (波峰波谷差值)
            val d = mps3 - mps2
            //做功
            val work = f * d
            
            Log.d("PowerRopeUtils", "  帧[$i] 绳长: mps1=$mps1, mps2=$mps2, mps3=$mps3")
            Log.d("PowerRopeUtils", "  帧[$i] 加速度: a=$a, 力: f=$f, 位移dy: d=$d")
            Log.d("PowerRopeUtils", "  帧[$i] 做功: work=$work ${if (work > 0) "(计入)" else "(忽略)"}")
            
            if (work > 0) {
                totalWork += work
                positiveWorkCount++
            }
            
            // 累计绳长用于计算平均值
            totalRopeLength += mps2
            ropeLengthCount++
        }

        // 使用实际参与计算的帧数
        val avgPower = if (positiveWorkCount > 0) {
            totalWork / (positiveWorkCount / 10f)
        } else {
            0f
        }
        
        // 方案2: 绳长归一化处理
        val STANDARD_ROPE_LENGTH = 0.20f  // 标准绳长20cm
        val avgRopeLength = if (ropeLengthCount > 0) totalRopeLength / ropeLengthCount else STANDARD_ROPE_LENGTH
        val normalizedPower = if (avgRopeLength > 0) {
            avgPower * (avgRopeLength / STANDARD_ROPE_LENGTH)
        } else {
            avgPower
        }
        
        Log.d("PowerRopeUtils", "总做功: totalWork=$totalWork (有效帧数: $positiveWorkCount, 总帧数: $frameCount)")
        Log.d("PowerRopeUtils", "平均功率计算: $totalWork / ($positiveWorkCount / 10) = $avgPower")
        Log.d("PowerRopeUtils", "归一化处理: 平均绳长=${avgRopeLength}m, 标准绳长=${STANDARD_ROPE_LENGTH}m")
        Log.d("PowerRopeUtils", "归一化功率: $avgPower * ($avgRopeLength / $STANDARD_ROPE_LENGTH) = $normalizedPower")
        Log.d("PowerRopeUtils", "========== getDoWork 结束 ==========")
        
        return normalizedPower
    }


}