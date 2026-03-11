package com.aeke.fitnessmirror.power.data

object ActionRhythmHelper {

    fun getActionRhythmDuration(type: DistanceType): ActionRhythmDurations {
        val actionRhythmDurations = when (type) {
            DistanceType.LONG -> ActionRhythmDurations.LONG
            DistanceType.MEDIUM -> ActionRhythmDurations.MEDIUM
            DistanceType.SHORT -> ActionRhythmDurations.SHORT
            DistanceType.ULTRA_SHORT -> ActionRhythmDurations.ULTRA_SHORT
        }
        return actionRhythmDurations
    }
}