package com.aeke.fitnessmirror.power

import android.app.Application
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper

object PowerModule {

    lateinit var powerContext:Application

    fun init(app:Application){
        this.powerContext = app
        NewPowerHelper.init()
    }


}