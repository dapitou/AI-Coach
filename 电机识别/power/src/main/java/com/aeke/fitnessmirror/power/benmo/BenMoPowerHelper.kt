package com.aeke.fitnessmirror.power.benmo

import MessageDigestUtils
import android.util.Log
import cn.hutool.core.io.checksum.crc16.CRC16IBM
import com.aeke.baseliabrary.utils.ProductHelper
import com.aeke.baseliabrary.utils.log.ALog
import com.aeke.fitnessmirror.SerialPortJNIAdapter
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.foldboard.CRC8Util
import com.aeke.fitnessmirror.foldboard.Utils
import com.aeke.fitnessmirror.power.PowerLifeScope
import com.aeke.fitnessmirror.power.benmo.BenMoPowerHelper.logObserver
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.hardwaredevicediagnostic.utils.DeviceDiagnostics
import com.aeke.sensor.SensorAekeApi
import com.aeke.sensor.SensorTrackEvent
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.suspendCancellableCoroutine
import kotlinx.coroutines.sync.Semaphore
import kotlinx.coroutines.sync.withPermit
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeoutOrNull
import org.json.JSONObject
import kotlin.coroutines.resume

/*
* 本末伺服电机
* */
internal object BenMoPowerHelper : PowerHelperInterface {

    @Volatile
    private var isCancelReadThread: Boolean = false
    private const val readMaxSize: Int = 280
    private const val baudRate: Int = 57600
    private val devicePath: String = ProductHelper.findAvailablePowerDevice()
    //private const val devicePath: String = "/dev/ttyS4"

    override var isSmooth:Boolean = false

    override var smoothRate:Int = 0
        set(value) {
            if (value in 0 until 256){
                field = value
            }
        }
    private var isInit:Boolean = false

    override val lifeScope = PowerLifeScope()

    override var isOtaing: Boolean = false
    var currentInfo: PowerControlModel? = null
        private set(value) {
            value?.let {
                if (!"ee".equals(it.currentMode,true)){
                    lastReportMode = it.currentMode
                }
            }
            field = value
        }

    var lastReportMode:String? = null
        private set
    var isOpenSuccess = false
        private set

    var isSerialDelay = false

    private var portAddr: Long = 0L
        set

    override val logObserver:AekeObservable<String> = AekeObservable()

    override val hexDataReceiveObserver: AekeObservable<String> = AekeObservable()

    override val versionObserver:AekeObservable<String> = AekeObservable()

    private val _powerResponseInfoObserver:AekeObservable<PowerControlModel> = AekeObservable()

    override val powerResponseInfoObserver: PowerResponseInfoObserver = object : PowerResponseInfoObserver {
        override fun addObserver(observer: (PowerControlModelInterface) -> Unit) {
            _powerResponseInfoObserver.addObserver(object : AekeObserver<PowerControlModel> {
                override fun update(value: PowerControlModel) {
                    observer(value as PowerControlModelInterface)
                }
            })
        }

        override fun removeObserver(observer: (PowerControlModelInterface) -> Unit) {
            // 在这种简化实现中，我们不实现移除功能
            // 在实际应用中，可能需要更复杂的映射机制
        }
    }

    private val powerOtaObserver:AekeObservable<PowerOtaModel> = AekeObservable()

    private val readThread: Thread = object : Thread("BenMoPowerReadThread") {
        override fun run() {
            var result: ByteArray
            var hexData: String
            while (!isCancelReadThread) {
                try {
                    
                    result = SerialPortJNIAdapter.readPort(readMaxSize, portAddr)
                    hexData = Utils.bytesToHexStr(result)
                    DeviceDiagnostics.logHardwareTrace("motor", hexData, false)
                    //Log.d("-----","${System.currentTimeMillis()} package:${hexData}")
                    hexDataReceiveObserver.setChanged()
                    hexDataReceiveObserver.notifyObservers(hexData)
                } catch (e: Exception) {
                    sleep(200)
                    e.printStackTrace()
                }
            }
        }
    }

    private var powerVersionNumber:Int = -1
    private val sendSemaphore = Semaphore(1)

    @Deprecated("仅供调试使用", level = DeprecationLevel.WARNING)
    fun getPowerVersionImmediately(): Int = powerVersionNumber

    override fun init(){
        if (isInit){
            return
        }
        isInit = true
        lifeScope.launch {
            withContext(Dispatchers.IO){
                portAddr = SerialPortJNIAdapter.openPort(devicePath, baudRate, 8, 1, 'n')
                if (portAddr !=0L){
                    log("SerialPort open success portAddr:$portAddr, devicePath:$devicePath")
                    isOpenSuccess = true
                    initControlParser()
                    readThread.start()
                    delay(100)
                    getPowerVersion()
                    //delay(100)
                    //setEnablePowerMode()
                    repeat(3){
                        if (currentInfo !=null){
                            return@repeat
                        }
                        delay(1000)
                    }
                    if (powerVersionNumber<=0){
                        getPowerVersion()
                    }
                    log("is can get power info:${currentInfo?.toString()}")
                } else {
                    isInit = false
                    isOpenSuccess = false
                    log("SerialPort open fail")
                }
            }
        }
    }

    private fun initControlParser(){
        hexDataReceiveObserver.addObserver(object :AekeObserver<String>{
            override fun update(value: String) {
                if (isOtaing){
                    return
                }
                if (value.length>4&&value.substring(0,4)=="0164"){
                    val model = PowerControlModel.create(value) ?:return
                    _powerResponseInfoObserver.setChanged()
                    _powerResponseInfoObserver.notifyObservers(model)
                    currentInfo = model
                }else{
                    log("package:${value}")
                }
            }
        })
        //老版本协议适配
        hexDataReceiveObserver.addObserver(object :AekeObserver<String>{
            override fun update(value: String) {
                //464143
                try {
                    if (value.length>6&&value.substring(0,4)=="0264"){
                        val data:String = value.substring(0,12)
                        val ver1:Int = value.substring(4,9).toInt(16)
                        val ver2:String = value.substring(9,12).toInt(16).toString(8)
                        val crc:String = value.substring(12,14)
                        val dataCrc8:String = data.crc8()
                        if (dataCrc8.equals(crc,true)){
                            versionObserver.setChanged()
                            versionObserver.notifyObservers("${ver1}${ver2}")
                        }else{
                            log("version crc8 error:${value} crc:${crc} dataCrc8:${dataCrc8}")
                        }
                    }
                }catch (e:Exception){
                    log("old version crc8 error:${e.message}")
                }
            }
        })

        //新版本协议适配
        hexDataReceiveObserver.addObserver(object :AekeObserver<String>{
            override fun update(value: String) {
                //464143
                try {
                    if (value.length>6&&value.substring(0,4)=="0264"){
                        val data:String = value.substring(0,14)
                        val ver1:Int = value.substring(4,9).toInt(16)
                        val ver2:String = value.substring(9,12).toInt(16).toString(8)
                        //1 存在ota固件 0 不存在
                        val isHaveOta:Int = value.substring(12,14).toInt()
                        val crc:String = value.substring(14,16)
                        val dataCrc8:String = data.crc8()
                        log("power version ver1:${ver1} ver2:${ver2} isHaveOta:${isHaveOta}")
                        if (dataCrc8.equals(crc,true)){
                            versionObserver.setChanged()
                            versionObserver.notifyObservers("${ver1}${ver2}${isHaveOta}")
                            powerVersionNumber = ver1
                        }else{
                            log("new version crc8 error:${value} crc:${crc} dataCrc8:${dataCrc8}")
                        }
                    }
                }catch (e:Exception){
                    log("new version crc8 error:${e.message}")
                }
            }
        })

        hexDataReceiveObserver.addObserver(object :AekeObserver<String>{
            override fun update(value: String) {
                if (!isOtaing){
                    return
                }
                if (value.length>2&&value.substring(0,2)=="64"){
                    //log("ota receive:${value}")
                    powerOtaObserver.setChanged()
                    powerOtaObserver.notifyObservers(PowerOtaModel.create(value))
                }
            }
        })
    }

    //0xAA	使能模式
    override fun setEnablePowerMode(){
        writeCmd_0_1kg(mcMode = "AA")
    }

    //0x55	失能模式
    override fun setUnEnablePowerMode(){
        writeCmd_0_1kg(mcMode = "55")
    }

    //0x00	标准模式	操作参数：拉力和回力设置
    override fun setStandardMode(huiLiSet:String,laLiSet:String){
        writeCmd_0_1kg(mcMode = "00", huiLiSet = huiLiSet.expandHexString(2), laLiSet = laLiSet.expandHexString(2))
    }
    //0x03	等速模式	操作参数：等速模式系数
    override fun setDengSuMode(denSuXishu:String){
        writeCmd_0_1kg(mcMode = "03", denSuXishu = denSuXishu)
    }

    //0x04	弹力模式	操作参数：回力设置和弹簧系数
    override fun setTanLiMode(huiLiSet:String,tanHuangXishu:String){
        writeCmd_0_1kg(mcMode = "04", huiLiSet = huiLiSet.expandHexString(2), tanHuangXishu = tanHuangXishu)
    }

    //0x07	划船模式	操作参数：回力设置
    override fun setHuaChuanMode(huiLiSet:String){
        writeCmd_0_1kg(mcMode = "07", huiLiSet = huiLiSet.expandHexString(2))
    }

    //0x08	平衡模式	操作参数：拉力和回力设置
    override fun setPingHengMode(huiLiSet:String,laLiSet:String){
        writeCmd_0_1kg(mcMode = "08", huiLiSet = huiLiSet.expandHexString(2), laLiSet = laLiSet.expandHexString(2))
    }

    //0x09	原点模式	操作参数：回力值和原点位置参数
    fun setYuanDianMode(huiLiSet:String,yuanDianSet:String){
        writeCmd_0_1kg(mcMode = "09", huiLiSet = huiLiSet.expandHexString(2), yuanDianSet = yuanDianSet)
    }

    //0x0A	飞鸟模式	操作参数：回力值和飞鸟位置参数
    fun setFeiNiaoMode(huiLiSet:String,feiNiaoSet:String){
        writeCmd_0_1kg(mcMode = "0A", huiLiSet = huiLiSet.expandHexString(2), feiNiaoSet = feiNiaoSet)
    }

    //0xFA	开始运动	操作参数：仅发送模式位即可
    fun setStartSportMode(){
        writeCmd_0_1kg(mcMode = "FA")
    }

    //0xFB	暂停运动	操作参数：仅发送模式位即可
    fun setPauseSportMode(){
        writeCmd_0_1kg(mcMode = "FB")
    }

    //0xFC	起点重置	操作参数：仅发送模式位即可
    override fun setResetMode(){
        writeCmd_0_1kg(mcMode = "FC")
    }

    //0xFD	FD模式为消除错误，强恢复模组工作
    private fun rebootPowerClearError(){
        writeCmd_0_1kg(mcMode = "FD")
    }

    //0xFE	FE模式，芯片软启动功能，会重新运行程序
    override fun rebootPowerChip(){
        writeCmd_0_1kg(mcMode = "FE")
    }

    //0xB1	平衡模式
    override fun setBalanceMode(isOpen: Boolean) {
        if (!isSupportHandOffProtect()) {
            log("not support motor hands off protect and BalanceMode")
            return
        }
        val state = if (isOpen){
            "01"
        }else{
            "00"
        }
        val data = "0363B1${state}0000000000"
        lifeScope.launch {
            sendData("${data}${data.crc8()}".hexToBytes())
        }
    }

    override fun getPowerVersion(){
        if (!isInit){
            log("power not init")
            return
        }
        lifeScope.launch {
            sendData("46414300200000008B14017E".hexToBytes())
            delay(500)
            sendData("4641430020000000A900B618F503B5019900D007DB".hexToBytes())
        }
    }

    fun writeCmd_0_1kg(mid:String = "03",/*1b*/
                       mcMode:String,/*1b*/
                       huiLiSet:String = "0000",/*2b*/
                       laLiSet:String = "0000",/*2b*/
                       denSuXishu:String = "00",/*1b*/
                       yuanDianSet:String = "00",/*1b*/
                       feiNiaoSet:String = "00",/*1b*/
                       tanHuangXishu:String = "00",/*1b*/
                       laLiCountClear:String = "00"/*1b*/){
        if (isSmooth){
            writeCmd_0_1kg_smooth(
                mid = mid,
                mcMode = mcMode,
                huiLiSet = huiLiSet,
                laLiSet = laLiSet,
                denSuXishu = denSuXishu,
                yuanDianSet = yuanDianSet,
                feiNiaoSet = feiNiaoSet,
                tanHuangXishu = tanHuangXishu,
                laLiCountClear = laLiCountClear,
                smooth = "01",
                smoothRate = smoothRate.toString(16).expandHexString()
            )
            return
        }
        val hexData:String =  "${mid}64${mcMode}${huiLiSet.reserveByByte()}${laLiSet.reserveByByte()}${denSuXishu}${yuanDianSet}${feiNiaoSet}${tanHuangXishu}${laLiCountClear}"
        val sendData:String = "${hexData}${hexData.crc8()}"
        if (!(mid.length==2&&
                    mcMode.length==2&&
                    huiLiSet.length==4&&
                    laLiSet.length==4&&
                    denSuXishu.length==2&&
                    tanHuangXishu.length==2&&
                    laLiCountClear.length==2&&
                    feiNiaoSet.length==2&&
                    yuanDianSet.length==2)){
            log("params length error $hexData")
            return
        }
        log("send data 0_1kg $sendData")
        lifeScope.launch {
            sendData(sendData.hexToBytes())
        }
    }

    private fun writeCmd_0_1kg_smooth(mid:String = "03",/*1b*/
                       mcMode:String,/*1b*/
                       huiLiSet:String = "0000",/*2b*/
                       laLiSet:String = "0000",/*2b*/
                       denSuXishu:String = "00",/*1b*/
                       yuanDianSet:String = "00",/*1b*/
                       feiNiaoSet:String = "00",/*1b*/
                       tanHuangXishu:String = "00",/*1b*/
                       smooth:String = "00",
                       smoothRate:String = "00",
                       laLiCountClear:String = "00"/*1b*/){
        val hexData:String =  "${mid}65${mcMode}${huiLiSet}${laLiSet}${denSuXishu}${yuanDianSet}${feiNiaoSet}${tanHuangXishu}${smooth}${smoothRate}${laLiCountClear}"
        val sendData:String = "${hexData}${hexData.crc8()}"
        if (!(mid.length==2&&
                    mcMode.length==2&&
                    huiLiSet.length==4&&
                    laLiSet.length==4&&
                    denSuXishu.length==2&&
                    tanHuangXishu.length==2&&
                    laLiCountClear.length==2&&
                    feiNiaoSet.length==2&&
                    yuanDianSet.length==2)){
            log("params length error $hexData")
            return
        }
        log("send data writeCmd_0_1kg_smooth $sendData")
        lifeScope.launch {
            sendData(sendData.hexToBytes())
        }
    }

    override fun setHandsOffProtect(enable:Boolean, handOffSpeed:Int, handOffTime:Int){
        log("send data setHandsOffProtect $enable ${handOffSpeed} ${handOffTime}")
        val enableHex:String = if (enable){
            "01"
        }else{
            "00"
        }
        val sendData:String = "0363bb00${enableHex}${handOffSpeed.toString(16).expandHexString()}${handOffTime.toString(16).expandHexString()}0000"
        lifeScope.launch {
            log("setHandsOffProtect $sendData")
            sendData("${sendData}${sendData.crc8()}".hexToBytes())
        }
    }

    private fun writeCmd_0_5kg(
        mid: String = "03",/*1b*/
        mcMode: String,/*1b*/
        huiLiSet: String = "00",/*1b*/
        laLiSet: String = "00",/*1b*/
        denSuXishu: String = "00",/*1b*/
        yuanDianSet: String = "00",/*1b*/
        feiNiaoSet: String = "00",/*1b*/
        tanHuangXishu: String = "00",/*1b*/
    ){
        val hexData:String =  "${mid}64${mcMode}${huiLiSet}${laLiSet}${denSuXishu}${yuanDianSet}${feiNiaoSet}${tanHuangXishu}"
        val sendData:String = "${hexData}${hexData.crc8()}"
        if (!(mid.length==2&&
                    mcMode.length==2&&
                    huiLiSet.length==2&&
                    laLiSet.length==2&&
                    denSuXishu.length==2&&
                    tanHuangXishu.length==2&&
                    yuanDianSet.length==2&&
                    feiNiaoSet.length==2)){
            log("params length error $hexData")
            return
        }
        log("send data 0_5kg $sendData")
        lifeScope.launch {
            sendData(sendData.hexToBytes())
        }
    }

    override suspend fun sendData(hexData:ByteArray){
        if (portAddr==0L){
            log("power portAddr not init")
            return
        }
        if (!isInit){
            log("power not init")
            return
        }
        if (isOtaing){
            log("otaing not send data")
            return
        }
        DeviceDiagnostics.logHardwareTrace("motor", Utils.bytesToHexStr(hexData), true)
        sendSemaphore.withPermit {
            withContext(Dispatchers.IO) {
                SerialPortJNIAdapter.writePort(hexData, portAddr)
            }
        }
    }

    private suspend fun sendOtaData(hexData: String) {
        if (!isInit) {
            log("power not init")
            return
        }
        sendSemaphore.withPermit {
            log("send ota data:${hexData}")
            withContext(Dispatchers.IO) {
                SerialPortJNIAdapter.writePort(hexData.hexToBytes(), portAddr)
            }
        }
    }

    private suspend fun awaitOtaCmdResult(cmdId: String,timeout: Long = 10000):Pair<Boolean, PowerOtaModel?>{
        var observer: AekeObserver<PowerOtaModel>? = null
        var result:Pair<Boolean, PowerOtaModel?> = false to null
        try {
            withTimeoutOrNull(timeout) {
                result = suspendCancellableCoroutine<Pair<Boolean, PowerOtaModel?>> { cancel ->
                    observer = object : AekeObserver<PowerOtaModel> {
                        override fun update(value: PowerOtaModel) {
                            //log("awaitCmdResult accept:${value}")
                            if (value.cmdId.equals(cmdId, ignoreCase = true)){
                                cancel.resume(true to value)
                            }
                        }
                    }
                    powerOtaObserver.addObserver(observer as AekeObserver<PowerOtaModel>)
                }
            }
        }catch (e:Exception){
            e.printStackTrace()
        }finally {
            powerOtaObserver.deleteObserver(observer)
        }
        return result
    }

    /**
     *  ota升级流程：
     *  1、发送进入ota指令，等待回复，超时时间为10秒
     *  2、收到正确回复后，等待1秒，发送开始ota指令，等待回复，超时为10秒
     *  3、收到正确回复后，发送ota数据，收到正确回复后，继续发送，直到数据发送完毕
     *  4、数据发送完毕，等待500ms，发送结束ota指令
     *  5、收到正确回复后，等待5秒，通知升级成功
     */

    @Synchronized
    override fun startOta(datas: ByteArray, fileName: String?, callback: (Boolean) -> Unit) {
        /*if (!file.exists()){
            log("file not exist ${file}")
            return
        }*/
        if (isOtaing){
            log("otaing,not can to update")
            return
        }
        isOtaing = true
        var updateResult:Boolean = false
        var failReason:String? = null
        lifeScope.launch({
            withContext(Dispatchers.IO){
                val otaDatas:ByteArray = datas//Files.readAllBytes(file.toPath())
                log("calc file sign ...")
                val fileMd5:String = MessageDigestUtils.getMd5(otaDatas)?: return@withContext
                val fileSha256:String = MessageDigestUtils.getSha256(otaDatas)?:return@withContext
                val fileCrc16:String = otaDatas.crc16()
                log("file sign: fileCrc16:${fileCrc16} fileMd5:${fileMd5} fileSha256:${fileSha256}")
                if (fileMd5.length!=32||fileSha256.length!=64||fileCrc16.length!=4){
                    failReason = "file sign error"
                    throw IllegalArgumentException("file sign error fileCrc16:${fileCrc16} fileMd5:${fileMd5} fileSha256:${fileSha256}")
                }

                //进入ota
                //val enterOtaCmd = "6410104A0A000000000A010400000000000000000067EF"
                val enterOtaCmd = "641710240A000000000A0104000000000000000000AEAD"
                sendOtaData(enterOtaCmd)
                var result:Pair<Boolean, PowerOtaModel?> = awaitOtaCmdResult("0A00")
                if (!result.first){
                    log("enterOtaCmd await ota result error ${result.second}")
                    failReason = "enterOtaCmd error"
                    return@withContext
                }

                log("enterOtaCmd success")
                delay(1000)

                //开始ota
                val fileSize:Long = datas.size.toLong()
                val fileSizeHexStr:String = fileSize.toString(16).expandHexString(4).reserveByByte()
                if (fileSizeHexStr.length>8){
                    failReason = "file length too big"
                    throw IllegalArgumentException("file length too big")
                }
                val all0Str = "000000000000000000000000"
                var startOtaCmd = "642B10440C000000000A010400${all0Str}${fileSizeHexStr}${all0Str}"
                startOtaCmd = "${startOtaCmd}${startOtaCmd.crc16()}"
                sendOtaData(startOtaCmd)
                result = awaitOtaCmdResult("0C00")
                val sendMtu:Int
                if (!result.first){
                    log("startOtaCmd await ota result error ${result.second}")
                    failReason = "startOtaCmd error"
                    return@withContext
                }else {
                    val data = result.second!!.data
                    val dataResult:String = data.substring(0,2)
                    if (dataResult!="00"){
                        log("startOtaCmd return result error ${dataResult}")
                        failReason = "startOtaCmd result error"
                        return@withContext
                    }
                    sendMtu = data.substring(2,6).reserveByByte().toInt(16)
                }

                log("startOtaCmd success sendMtu:${sendMtu}")

                //数据包发送
                var seq:Int = 0
                var dataSeq:Int = 0
                val otaFileDatas:ByteArray = otaDatas
                for (index in 0 until fileSize step sendMtu.toLong()){
                    val sendDataLen:Long
                    val dataLength: Long = if (index+sendMtu>fileSize){
                        sendDataLen = fileSize-index
                        fileSize
                    }else{
                        sendDataLen = sendMtu.toLong()
                        index+sendMtu
                    }
                    log("ota data index:${index} endIndex:${dataLength}")
                    val sendBytes = otaFileDatas.copyOfRange(index.toInt(),dataLength.toInt())
                    val sendBytesHexStr = Utils.bytesToHexStr(sendBytes)//.reserveByByte()
                    //val dataLengthHexStr:String = dataLength.toString(16).expandHexString(4).reserveByByte()
                    val verAndLen:Long = (sendDataLen+24 and 0b0000_111111111111) xor 0b0001_000000000000
                    val verAndLenHexStr:String = verAndLen.toString(16).expandHexString().reserveByByte()
                    val data1 = "64${verAndLenHexStr}"
                    val seqHexData:String = seq.toString(16).expandHexString(2).reserveByByte()
                    val dataDomain:String = "00${dataSeq.toString(16).expandHexString(4).reserveByByte()}${sendDataLen.toString(16).expandHexString(4).reserveByByte()}${sendBytesHexStr}"
                    val sendDataCmdNoCrc16:String = "${data1}${data1.crc8()}0E00${seqHexData}000A010400${dataDomain}"
                    sendOtaData("${sendDataCmdNoCrc16}${sendDataCmdNoCrc16.crc16()}")
                    val sendResult = awaitOtaCmdResult("0E00")
                    if (!sendResult.first){
                        failReason = "ota data error"
                        throw IllegalStateException("ota data error")
                    }else{
                        val data = sendResult.second!!
                        if (data.data.substring(0,2)!="00"){
                            failReason = "ota data result error"
                            throw IllegalArgumentException("ota data error")
                        }
                        val returnSeq:Int = data.data.substring(2).reserveByByte().toInt(16)
                        if (returnSeq!=dataSeq){
                            failReason = "ota return seq error"
                            throw IllegalArgumentException("ota return seq error returnSeq:${returnSeq} dataSeq:${dataSeq}")
                        }
                    }
                    seq++
                    dataSeq++
                }

                log("send ota datas end")
                delay(500)

                //结束ota
                val seqHexData:String = seq.toString(16).expandHexString(2).reserveByByte()
                val cmdHexNoCrc16 = "644310681000${seqHexData}000A0104000000${fileCrc16.reserveByByte()}${fileMd5.reserveByByte()}${fileSha256.reserveByByte()}"
                val cmdHex:String = "${cmdHexNoCrc16}${cmdHexNoCrc16.crc16()}"
                sendOtaData(cmdHex)
                result = awaitOtaCmdResult("1000", timeout = 20000)
                if (result.first){
                    if (result.second!!.data=="00"){
                        updateResult = true
                        log("ota success :${result.second}")
                    }else{
                        log("ota fail :${result.second}")
                        failReason = "end cmd result fail"
                    }
                }else{
                    log("end cmd receive error:${result.second}")
                    failReason = "end cmd fail"
                }

                delay(5000)

            }
        }, onError = {
            log("onError:"+it.message)
            it.printStackTrace()
        }, onFinally = {
            isOtaing = false
            if (!updateResult) {
                stopOta()
            }
            onMotorOTAResult(updateResult, failReason, fileName)
            callback(updateResult)
        })
    }

    private fun onMotorOTAResult(isSuccess: Boolean, failReason: String?, fileName: String?) {
        var jsonObj = JSONObject()
        jsonObj.put("motor_issuccess", isSuccess)
        jsonObj.put("motor_failreason", failReason)
        jsonObj.put("motor_filename", fileName)
        SensorAekeApi.addTrack(SensorTrackEvent.Motor_OTA_Result, jsonObj)
    }

    override fun stopOta(){
        //0000
        //0000000000000000000000000000000000000000000000000000000000000000
        //00000000000000000000000000000000
        lifeScope.launch {
            log("结束ota")
            val sendData:String = "6443106810000000000A0104000000FFFF00000000000000000000000000000000000000000000000000000000000000000000000000"
            sendOtaData("${sendData}${sendData.crc16()}")
        }
    }

    override fun isSupportPowerSmooth():Boolean{
        return powerVersionNumber>250800
    }

    override fun isSupportHandOffProtect(): Boolean {
        return powerVersionNumber > 251000
    }

}

@Synchronized
internal fun String.crc8(): String {
    //crc8.reset()
    //crc8.update(hexToBytes())
    //return String.format("%02x", crc8.value xor 0x00)
    val crc8 = CRC8Util.getCRC8_X8_X5_X4_1(this)
    if (crc8.length%2 == 0){
        return crc8
    }else{
        return "0${crc8}"
    }
}


private val crc16IBM: CRC16IBM by lazy { CRC16IBM() }

@Synchronized
internal fun String.crc16():String{
    return hexToBytes().crc16().reserveByByte()
}

@Synchronized
internal fun ByteArray.crc16():String{
    crc16IBM.reset()
    crc16IBM.update(this)
    return crc16IBM.getHexValue(true)
}

fun String.expandHexString(
    byteCount:Int = if (this.length%2==0)this.length/2 else (this.length/2)+1,
    prefix:Boolean = true,
    fill:String = "00"
):String{
    var value = if (this.length%2==0){
        this
    }else{
        "0$this"
    }
    val repeatCount = byteCount-(value.length/2)
    if (repeatCount>0){
        repeat(repeatCount){
            if (prefix){
                value="${fill}${value}"
            }else{
                value="${value}${fill}"
            }
        }
    }
    return value
    //return Utils.bytesToHexStr(Utils.expandBytes(value.hexToBytes(), 0, byteCount))
}

internal fun String.hexToBytes():ByteArray{
    return Utils.hexStrToBytes(this)
}

internal fun String.reserveByByte():String{
    val thiz = this.expandHexString()
    var result:String = ""
    for (index in this.length downTo 2 step 2){
        result="${result}${thiz.substring(index-2,index)}"
    }
    return result
}

fun log(msg:String, save:Boolean = false){
    logObserver.setChanged()
    logObserver.notifyObservers(msg)
    if(save) {
        ALog.w("NewPowerHelper",msg)
    } else {
        ALog.d("NewPowerHelper",msg)
    }
}

class PowerOtaModel private constructor(
    val ver: Int,
    val len: Int,
    val crc8: String,
    val cmdId: String,
    val seq: Int,
    val sender: String,
    val receiver: String,
    val attr: String,
    val data: String,
    val crc16: String,
){
    companion object{
        fun create(hex:String): PowerOtaModel?{
            try {
                val sof:String = hex.substring(0,2)
                if (sof!="64"){
                    throw IllegalArgumentException("head not is 64")
                }
                val lenAndVer:Int = hex.substring(2,6).reserveByByte().toInt(16)
                val ver:Int = lenAndVer shr 12
                val len:Int = lenAndVer and 0b0000_1111_1111_1111
                val crc8:String = hex.substring(6,8)
                val cmdId:String = hex.substring(8,12)
                val seq:Int = hex.substring(12,16).toInt(16)
                val sender:String = hex.substring(16,20)
                val receiver:String = hex.substring(20,24)
                val attr:String = hex.substring(24,26)
                val endIndex:Int = len*2-4
                val data:String = hex.substring(endIndex-(len-15)*2,endIndex)
                val crc16:String = hex.substring(len*2-4,len*2)
                val caleCrc16:String = hex.substring(0,endIndex).crc16()
                if (!crc16.equals(caleCrc16,true)){
                    throw IllegalStateException("crc compare error crc16:${crc16} caleCrc16:${caleCrc16}")
                }
                return PowerOtaModel(ver,len,crc8,cmdId,seq,sender, receiver, attr, data, crc16)
            }catch (e:Exception){
                e.printStackTrace()
            }
            return null
        }
    }

    override fun toString(): String {
        return "PowerOtaModel(ver=$ver, len=$len, crc8='$crc8', cmdId='$cmdId', seq=$seq, sender='$sender', receiver='$receiver', attr='$attr', data='$data', crc16='$crc16')"
    }
}







