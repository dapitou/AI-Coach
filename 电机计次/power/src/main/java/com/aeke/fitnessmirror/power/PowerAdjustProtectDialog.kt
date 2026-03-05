package com.aeke.fitnessmirror.power

import android.app.Dialog
import android.content.Context
import android.os.Bundle
import android.view.Gravity
import android.view.View
import android.view.WindowManager
import android.widget.TextView

class PowerAdjustProtectDialog(
    context: Context,
    private val leftCallback: () -> Unit = {},
    private val rightCallback: () -> Unit = {},
): Dialog(context,R.style.MyDialog) {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.dialog_power_adjust_protect)
        findViewById<TextView>(R.id.btn_left).setOnClickListener {
            dismiss()
            leftCallback()
        }
        findViewById<TextView>(R.id.btn_right).setOnClickListener {
            dismiss()
            rightCallback()
        }

        findViewById<View>(R.id.iv_close)?.setOnClickListener {
            dismiss()
            leftCallback()
        }

        window?.setType(WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY)
        window?.attributes?.gravity = Gravity.TOP
        window?.setDimAmount(0.8f)
        setCancelable(false)
        setCanceledOnTouchOutside(false)
    }

}