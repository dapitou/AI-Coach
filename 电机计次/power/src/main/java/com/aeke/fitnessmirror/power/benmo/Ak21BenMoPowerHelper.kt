package com.aeke.fitnessmirror.power.benmo

import MessageDigestUtils
import android.util.Log
import com.aeke.fitnessmirror.SerialPortJNIAdapter
import com.aeke.fitnessmirror.foldboard.AekeObservable
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.foldboard.Utils
import com.aeke.fitnessmirror.power.PowerLifeScope
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

internal object Ak21BenMoPowerHelper : PowerHelperInterface {


    @Volatile
    private var isCancelReadThread: Boolean = false
    private const val readMaxSize: Int = 280
    private const val baudRate: Int = 57600
    private const val devicePath: String = "/dev/ttyS9"
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
    private val sendSemaphore = Semaphore(1)
    var currentInfo: Ak21PowerControlModel? = null
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

    private var portAddr: Long = 0L
        private set

    private var sn:Int = 20

    override val logObserver:AekeObservable<String> = AekeObservable()

    override val hexDataReceiveObserver: AekeObservable<String> = AekeObservable()

    override val versionObserver:AekeObservable<String> = AekeObservable()

    private val _powerResponseInfoObserver:AekeObservable<Ak21PowerControlModel> = AekeObservable()
    
    override val powerResponseInfoObserver: PowerResponseInfoObserver = object : PowerResponseInfoObserver {
        override fun addObserver(observer: (PowerControlModelInterface) -> Unit) {
            _powerResponseInfoObserver.addObserver(object : AekeObserver<Ak21PowerControlModel> {
                override fun update(value: Ak21PowerControlModel) {
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

    override fun init(){
        if (isInit){
            return
        }
        isInit = true
        lifeScope.launch {
            withContext(Dispatchers.IO){
                portAddr = SerialPortJNIAdapter.openPort(devicePath, baudRate, 8, 1, 'n')
                if (portAddr !=0L){
                    log("SerialPort open success portAddr:$portAddr")
                    initControlParser()
                    readThread.start()
                    delay(100)
                    getPowerVersion()
                    //delay(100)
                    setEnablePowerMode()
                    repeat(3){
                        if (currentInfo !=null){
                            return@repeat
                        }
                        delay(1000)
                    }
                    log("is can get power info:${currentInfo?.toString()}")
                }else{
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
                if (value.length == 80 && value.substring(0,4) == "6402") {
                    val model = Ak21PowerControlModel.create(value) ?:return
                    _powerResponseInfoObserver.setChanged()
                    _powerResponseInfoObserver.notifyObservers(model)
                    currentInfo = model
                }else{
                    log("package:${value}")
                }
            }
        })

        hexDataReceiveObserver.addObserver(object :AekeObserver<String>{
            override fun update(value: String) {
                try {
                    if (value.length == 14 &&value.substring(0,4)=="0264") {
                        val data:String = value.substring(0,12)
                        val version:Int = value.substring(4,9).toInt(16)
                        val crc:String = value.substring(12,14)
                        val dataCrc8:String = data.crc8()
                        if (dataCrc8.equals(crc,true)){
                            versionObserver.setChanged()
                            versionObserver.notifyObservers(version.toString())
                        }else{
                            log("new version crc8 error:${value} , crc:${crc}, dataCrc8:${dataCrc8}")
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
                    log("ota receive:${value}")
                    powerOtaObserver.setChanged()
                    powerOtaObserver.notifyObservers(PowerOtaModel.create(value))
                }
            }
        })
    }
//64020100000000000000000000000000000000000000000000000000005e0D0A
    //0xAA	使能模式
    override fun setEnablePowerMode(){
        writeCmd(order = "02", mcMode = "AA")
    }

    //0x55	失能模式
    override fun setUnEnablePowerMode(){
        writeCmd(order = "02", mcMode = "55")
    }

    //0x00	标准模式	操作参数：拉力和回力设置
    override fun setStandardMode(huiLiSet:String,laLiSet:String){
        writeCmd(mcMode = "00", huiLiSet = huiLiSet.expandHexString(2), laLiSet = laLiSet.expandHexString(2))
    }
    //0x01	等速模式	操作参数：等速模式系数
    override fun setDengSuMode(denSuXishu:String){
        writeCmd(mcMode = "01", denSuXishu = denSuXishu)
    }

    //0x02	弹力模式	操作参数：回力设置和弹簧系数
    override fun setTanLiMode(huiLiSet:String,tanHuangXishu:String){
        writeCmd(mcMode = "02", huiLiSet = huiLiSet.expandHexString(2), tanHuangXishu = tanHuangXishu)
    }

    //0x03	划船模式	操作参数：回力设置
    override fun setHuaChuanMode(huiLiSet:String){
        writeCmd(mcMode = "03", huiLiSet = huiLiSet.expandHexString(2))
    }

    //0x04	平衡模式	操作参数：拉力和回力设置
    override fun setPingHengMode(huiLiSet:String,laLiSet:String){
        writeCmd(mcMode = "04", huiLiSet = huiLiSet.expandHexString(2), laLiSet = laLiSet.expandHexString(2))
    }

    //0x06	飞鸟模式	操作参数：回力值和飞鸟位置参数
    fun setFeiNiaoMode(huiLiSet:String,feiNiaoSet:String){
        writeCmd(mcMode = "06", huiLiSet = huiLiSet.expandHexString(2), feiNiaoSet = feiNiaoSet)
    }

    //0xFC	起点重置	操作参数：仅发送模式位即可
    override fun setResetMode(){
        writeCmd(mcMode = "FC")
    }

    //0xFE	FE模式，芯片软启动功能，会重新运行程序
    override fun rebootPowerChip(){
        writeCmd(order = "FF", mcMode = "FF")
    }

    override fun getPowerVersion(){
        if (!isInit){
            log("power not init")
            return
        }
        lifeScope.launch {
            writeCmd(order = "F1")
        }
    }

    //6402010005dc05dc0000000000000000000000000000000000000000003d0D0A
    //6402010005dc05dc0000000000000000000000000000000000000000003d0d0a   //15公斤发送指令
    fun writeCmd(order:String = "01",/*1b*/
                       mcMode:String = "00",/*1b*/
                       huiLiSet:String = "0000",/*2b*/
                       laLiSet:String = "0000",/*2b*/
                       denSuXishu:String = "00",/*1b*/
                       yuanDianSet:String = "00",/*1b*/
                       feiNiaoSet:String = "00",/*1b*/
                       tanHuangXishu:String = "00",/*1b*/
                       laLiCountClear:String = "00"/*1b*/){
        val smooth = if (isSmooth) "01" else "00"
        val hexData =  "6402${order}${mcMode}${huiLiSet}${laLiSet}${denSuXishu}${tanHuangXishu}${feiNiaoSet}${laLiCountClear}${smooth}${smoothRate.toString(16).expandHexString()}000000000000000000000000000000"
        val sendData = "${hexData}${hexData.crc8()}0D0A"
        log("order:${order} mcMode:${mcMode} huiLiSet:${huiLiSet} laLiSet:${laLiSet} denSuXishu:${denSuXishu} yuanDianSet:${yuanDianSet}")

        if (!(order.length==2&&
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

    private fun getSn():Int{
        if (sn > 99) {
            sn = 10
        } else {
            sn++
        }
        return sn
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
        sendSemaphore.withPermit {
            withContext(Dispatchers.IO) {
                SerialPortJNIAdapter.writePort(hexData, portAddr)
            }
        }
    }

    private suspend fun sendOtaData(hexData: String){
        if (!isInit){
            log("power not init")
            return
        }
        log("send ota data:${hexData}")
        sendSemaphore.withPermit {
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

                delay(200)
                sendOtaData(enterOtaCmd)


                var result:Pair<Boolean, PowerOtaModel?> = awaitOtaCmdResult("0A00")
                if (!result.first){
                    log("enterOtaCmd await ota result error ${result.second}")
                    failReason = "enterOtaCmd error"
                    return@withContext
                }

                log("enterOtaCmd success")
                delay(50)

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
            if (updateResult) {
                stopOta()
            }
            onMotorOTAResult(updateResult, failReason, fileName)
	    log("ota end failReason:${failReason} updateResult:${updateResult}")
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

    override fun isSupportPowerSmooth(): Boolean = true
    override fun isSupportHandOffProtect(): Boolean = true

    override fun setHandsOffProtect(enable: Boolean, handOffSpeed: Int, handOffTime: Int) {
        log("send data setHandsOffProtect $enable ${handOffSpeed} ${handOffTime}")
        val enableHex:String = if (enable){
            "01"
        }else{
            "00"
        }
        val hexData = "6402A0${enableHex}${handOffSpeed.toString(16).expandHexString()}${handOffTime.toString(16).expandHexString()}0000000000000000000000000000000000000000000000"
        val sendData = "${hexData}${hexData.crc8()}0D0A"
        lifeScope.launch {
            log("setHandsOffProtect $sendData, length = ${sendData.length}")
            sendData(sendData.hexToBytes())
        }
    }

    override fun setBalanceMode(isOpen: Boolean) {
        val enableHex:String = if (isOpen){
            "01"
        }else{
            "00"
        }
        val hexData = "6402A2${enableHex}00000000000000000000000000000000000000000000000000"
        val sendData = "${hexData}${hexData.crc8()}0D0A"
        lifeScope.launch {
            log("setBalanceMode $sendData, length = ${sendData.length}")
            sendData(sendData.hexToBytes())
        }
    }

    fun log(msg:String, save:Boolean = false){
        logObserver.setChanged()
        logObserver.notifyObservers(msg)
        if(save) {
            Log.w("NewPowerHelper",msg)
        } else {
            Log.d("NewPowerHelper",msg)
        }
    }
}
