package com.aeke.fitnessmirror.power.calc

import com.aeke.fitnessmirror.power.calc.adapter.IRopeGetter
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper

class PowerRopeGetter: IRopeGetter {
    override fun getLeftRopeLength(): Long {
        return NewPowerHelper.getPowerInfo().ropeLeftLength.toLong()/10
    }

    override fun getRightRopeLength(): Long {
        return NewPowerHelper.getPowerInfo().ropeRightLength.toLong()/10
    }
}