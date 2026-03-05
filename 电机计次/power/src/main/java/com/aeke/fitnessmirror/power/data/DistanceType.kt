package com.aeke.fitnessmirror.power.data

enum class DistanceType(
    val range: IntRange
) {
    LONG(85 until 10000),
    MEDIUM(60 until 85),
    SHORT(35 until 60),
    ULTRA_SHORT(20 until 35);

    companion object {
        fun getDistanceType(distance: Int): DistanceType {
            return when (distance) {
                in LONG.range -> LONG
                in MEDIUM.range -> MEDIUM
                in SHORT.range -> SHORT
                else -> ULTRA_SHORT
            }
        }
    }
}