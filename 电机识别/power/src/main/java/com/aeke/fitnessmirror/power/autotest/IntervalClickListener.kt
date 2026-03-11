package com.aeke.fitnessmirror.power.autotest

import android.view.View

class IntervalClickListener(
    private val originalListener: View.OnClickListener,
    private val throttleInterval: Long = 3000
) : View.OnClickListener {
    private var lastClickTime = 0L

    override fun onClick(v: View?) {
        val currentTime = System.currentTimeMillis()
        if (currentTime - lastClickTime >= throttleInterval) {
            lastClickTime = currentTime
            originalListener.onClick(v)
        } else {
            //do nothing
        }
    }
}