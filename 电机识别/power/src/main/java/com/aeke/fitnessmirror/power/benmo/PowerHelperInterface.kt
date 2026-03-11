package com.aeke.fitnessmirror.power.benmo
import com.aeke.baseliabrary.utils.ProductHelper
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.power.BuildConfig

interface PowerHelperInterface {
    var isOtaing: Boolean
    val lifeScope: com.aeke.fitnessmirror.power.PowerLifeScope
    val logObserver: AekeObservable<String>
    val hexDataReceiveObserver: AekeObservable<String>
    val versionObserver: AekeObservable<String>
    val powerResponseInfoObserver: PowerResponseInfoObserver
    var isSmooth:Boolean
    var smoothRate:Int

    fun init()
    fun setEnablePowerMode()
    fun setUnEnablePowerMode()
    fun setStandardMode(huiLiSet: String, laLiSet: String)
    fun setDengSuMode(denSuXishu: String)
    fun setTanLiMode(huiLiSet: String, tanHuangXishu: String)
    fun setHuaChuanMode(huiLiSet: String)
    fun setPingHengMode(huiLiSet: String, laLiSet: String)
    fun setResetMode()
    fun rebootPowerChip()
    fun getPowerVersion()
    suspend fun sendData(hexData: ByteArray)
    fun startOta(datas: ByteArray, fileName: String? = null, callback: (Boolean) -> Unit)
    fun stopOta()
    fun isSupportPowerSmooth() : Boolean
    fun isSupportHandOffProtect() : Boolean
    fun setHandsOffProtect(enable: Boolean, handOffSpeed: Int = 0x13, handOffTime: Int = 0x04)
    fun setBalanceMode(isOpen: Boolean)
}

object PowerHelperCreator {
    @Volatile
    private var instance: PowerHelperInterface? = null

    @JvmStatic
    fun create(): PowerHelperInterface {
        val cachedInstance = instance
        if (cachedInstance != null) {
            return cachedInstance
        }

        return synchronized(this) {
            val localInstance = instance
            if (localInstance == null) {
                val newInstance = if(ProductHelper.isS1Pro()) {
                    Ak21BenMoPowerHelper
                } else {
                    BenMoPowerHelper
                }
                instance = newInstance
                newInstance
            } else {
                localInstance
            }
        }
    }
}