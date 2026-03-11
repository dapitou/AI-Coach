package com.aeke.fitnessmirror.power.event

import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter.Power

class HandsOffProtectEvent(val power: Power)

class AdjustWeightProtectResultEvent(val mode:AekePowerCoreAdapter.PowerMode)
