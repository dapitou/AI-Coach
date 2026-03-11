package com.aeke.fitnessmirror.power.calc

class PowerCalcConfig(val fps:Int = 10) {
    //偏差抖动阈值 cm (降低阈值让算法检测到更长的波峰波谷)
    var OFFSET:Long = 3
    //判断暂停阈值 以帧为单位,若2s为阈值,10fps,则是20帧
    var PAUSE_FRAME_THRESHOLD:Int = 3*fps
    //极点阈值
    var POINT_0_FRAME_THRESHOLD:Int = 2*fps+9
    //首次行程判断暂停阈值
    var START_PAUSE_FRAME_THRESHOLD:Int = (0.6*fps).toInt()
    //起点比较上下偏差
    var START_POINT_THRESHOLD:Float = 0.2f
    //行程比较上下偏差
    var DISTANCE_THRESHOLD:Float = 0.2f
    //判定双侧成立两哥波峰波谷之间的开始帧偏移阈值
    var RIGHT_LEFT_OFFSET_FRAME_COUNT_THRESHOLD = 2
    //行程有效阈值60%
    var DISTANCE_EFFECTIVE_THRESHOLD = 0.6f
    //行程重置阈值100%
    var DISTANCE_RESET_THRESHOLD = 1f

}