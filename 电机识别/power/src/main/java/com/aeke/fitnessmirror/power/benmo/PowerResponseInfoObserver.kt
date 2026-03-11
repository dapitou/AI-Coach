package com.aeke.fitnessmirror.power.benmo

// 用于PowerHelperInterface的通用响应信息观察者
interface PowerResponseInfoObserver {
    fun addObserver(observer: (PowerControlModelInterface) -> Unit)
    fun removeObserver(observer: (PowerControlModelInterface) -> Unit)
}