package com.aeke.fitnessmirror.power.newapi.adapter.impl

import android.os.Handler
import android.os.Looper
import android.util.Log
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import com.aeke.fitnessmirror.power.benmo.PowerControlModelInterface
import com.aeke.fitnessmirror.power.benmo.PowerHelperCreator
import com.aeke.fitnessmirror.power.benmo.PowerHelperInterface
import java.util.function.Consumer

class BenMoPowerCoreAdapterImpl: AekePowerCoreAdapter {

    private var powerHelper: PowerHelperInterface = PowerHelperCreator.create()

    private var currentPowerInfo: AekePowerCoreAdapter.PowerInfo = AekePowerCoreAdapter.PowerInfo(0)

    private var currentPowerControlModel: PowerControlModelInterface? = null

    private var errorCallback:((Int)->Unit)? = null

    private var mainHandler:Handler = Handler(Looper.getMainLooper())

    private var powerTickCallback: Consumer<AekePowerCoreAdapter.PowerInfo>? = null

    private var currentMode:AekePowerCoreAdapter.PowerMode? = null

    override fun init() {
        powerHelper.init()

        powerHelper.powerResponseInfoObserver.addObserver { value ->
            handlePowerControlModelUpdate(value)
        }
        powerHelper.versionObserver.addObserver(object :AekeObserver<String>{
            override fun update(value: String) {
                log("versionObserver:${value}")
                currentPowerInfo.version = value.toLong()
            }
        })
    }
    private var lastPostErrorCode:Int = 0
    private fun handlePowerControlModelUpdate(value: PowerControlModelInterface) {
        // 保存当前的 PowerControlModel
        currentPowerControlModel = value
        
        if (value.m1ErrorCode!=lastPostErrorCode){
            lastPostErrorCode = value.m1ErrorCode
            errorCallback?.invoke(lastPostErrorCode)
        }else if (value.m2ErrorCode!=lastPostErrorCode){
            lastPostErrorCode = value.m2ErrorCode
            errorCallback?.invoke(lastPostErrorCode)
        }else{
            lastPostErrorCode = 0
            errorCallback?.invoke(lastPostErrorCode)
        }
        currentPowerInfo.ropeLeftLength = 0.coerceAtLeast(value.m1Distance * 10)
        currentPowerInfo.ropeRightLength = 0.coerceAtLeast(value.m2Distance * 10)
        currentPowerInfo.leftSpeed = value.m1Rate
        currentPowerInfo.rightSpeed = value.m2Rate
        if (value.currentMode=="00"){
            val weight:Float? = currentMode?.weight
            if (weight!=null&&weight<=3.5){
                currentPowerInfo.ropeLeftWeight = weight*100f
                currentPowerInfo.ropeRightWeight = weight*100f
            }else{
                currentPowerInfo.ropeLeftWeight = value.m1Power*100f
                currentPowerInfo.ropeRightWeight = value.m2Power*100f
            }
        }else{
            currentPowerInfo.ropeLeftWeight = value.m1Power*100f
            currentPowerInfo.ropeRightWeight = value.m2Power*100f
        }
        currentPowerInfo.m1TouchKey = value.m1TouchKey
        currentPowerInfo.m2TouchKey = value.m2TouchKey
        onTick()
    }

    private fun onTick(){
        powerTickCallback?.accept(currentPowerInfo)
    }

    override fun getPowerInfo(): AekePowerCoreAdapter.PowerInfo {
        return currentPowerInfo
    }

    override fun setPowerInfoTickCallback(callback: Consumer<AekePowerCoreAdapter.PowerInfo>) {
        this.powerTickCallback = callback
    }

    @Synchronized
    override fun setPower(mode: AekePowerCoreAdapter.PowerMode) {
        log("setPower:${mode}")
        this.currentMode = mode
        val weight001 = (mode.weight*100).toInt()
        val weight001_04 = (mode.weight*60).toInt()
        powerHelper.isSmooth = mode.isSmooth
        powerHelper.smoothRate = mode.smoothRate.coerceAtLeast(14)
        when (mode) {
            is AekePowerCoreAdapter.PowerMode.STANDARD -> {
                powerHelper.setStandardMode(huiLiSet = weight001.toString(16), laLiSet = weight001.toString(16))
            }

            is AekePowerCoreAdapter.PowerMode.XiangXin -> {
                powerHelper.setStandardMode(huiLiSet = weight001_04.toString(16), laLiSet = weight001.toString(16) )
            }

            is AekePowerCoreAdapter.PowerMode.LiXin -> {
                powerHelper.setStandardMode(huiLiSet = weight001.toString(16), laLiSet = weight001_04.toString(16) )
            }

            is AekePowerCoreAdapter.PowerMode.HuaChuan -> {
                powerHelper.setHuaChuanMode(huiLiSet = weight001.toString(16))
            }

            is AekePowerCoreAdapter.PowerMode.TanLi -> {
                powerHelper.setTanLiMode(huiLiSet = weight001.toString(16),"03")
            }

            is AekePowerCoreAdapter.PowerMode.UNLOAD -> {
                powerHelper.setStandardMode(huiLiSet = weight001.toString(16), laLiSet = weight001.toString(16))
            }

            else -> {
                log("not found mode:${mode}")
            }
        }
        powerHelper.isSmooth = false
    }

    override fun getPowerVersion(callback: Consumer<Long>?) {
        log("getPowerVersion")
        powerHelper.getPowerVersion()
        mainHandler.postDelayed({
          try {
              callback?.accept(currentPowerInfo.version)
          }catch (e:Exception){
              log("getPowerVersion:${e.message}")
          }
        },2000)
    }

    override fun rebootPowerChip() {
        log("rebootPowerChip",true)
        powerHelper.rebootPowerChip()
    }

    override fun setPowerErrorCodeListener(callback: ((Int) -> Unit)?) {
        this.errorCallback = callback
    }

    override fun isSupportPowerSmooth(): Boolean {
        return powerHelper.isSupportPowerSmooth()
    }

    override fun isSupportHandOffProtect(): Boolean {
        return powerHelper.isSupportHandOffProtect()
    }

    override fun setHandsOffProtect(enable: Boolean) {
        powerHelper.setHandsOffProtect(enable)
    }

    override fun setBalanceMode(isOpen: Boolean) {
        powerHelper.setBalanceMode(isOpen)
    }

    private fun log(msg:String,isSave:Boolean = true){
        if (isSave){
            Log.i("BenMoPowerCoreAdapterImpl",msg)
        }else{
            Log.d("BenMoPowerCoreAdapterImpl",msg)
        }
    }

    override fun setResetMode() {
        powerHelper.setResetMode()
    }

    /**
     * 获取当前的 PowerControlModel 数据
     */
    fun getPowerControlModel(): PowerControlModelInterface? {
        return currentPowerControlModel
    }

}