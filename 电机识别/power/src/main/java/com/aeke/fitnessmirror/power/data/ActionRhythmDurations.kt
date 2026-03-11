package com.aeke.fitnessmirror.power.data

import com.aeke.baseliabrary.data.FloatRange

data class ActionRhythmDurations(
    val rangeA: FloatRange,
    val rangeB: FloatRange,
    val rangeC: FloatRange,
    val rangeD: FloatRange,
    val rangeE: FloatRange,
) {
    companion object {
        val LONG = ActionRhythmDurations(
            rangeA = FloatRange(1.6f, 500f),
            rangeB = FloatRange(1.5f, 1.6f),
            rangeC = FloatRange(1.4f, 1.5f),
            rangeD = FloatRange(1.2f, 1.4f),
            rangeE = FloatRange(0f, 1.2f),
        )
        val MEDIUM = ActionRhythmDurations(
            rangeA = FloatRange(1.4f, 500f),
            rangeB = FloatRange(1.3f, 1.4f),
            rangeC = FloatRange(1.2f, 1.3f),
            rangeD = FloatRange(1.05f, 1.2f),
            rangeE = FloatRange(0f, 1.05f),
        )
        val SHORT = ActionRhythmDurations(
            rangeA = FloatRange(1.2f, 500f),
            rangeB = FloatRange(1.1f, 1.2f),
            rangeC = FloatRange(1.0f, 1.1f),
            rangeD = FloatRange(0.9f, 1.0f),
            rangeE = FloatRange(0f, 0.9f),
        )
        val ULTRA_SHORT = ActionRhythmDurations(
            rangeA = FloatRange(1.0f, 500f),
            rangeB = FloatRange(0.9f, 1.0f),
            rangeC = FloatRange(0.85f, 0.9f),
            rangeD = FloatRange(0.8f, 0.85f),
            rangeE = FloatRange(0f, 0.8f),
        )
    }
}
