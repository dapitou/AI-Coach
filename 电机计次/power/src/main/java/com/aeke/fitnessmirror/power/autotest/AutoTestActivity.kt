package com.aeke.fitnessmirror.power.autotest

import android.content.res.Resources
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.os.Message
import android.util.Log
import android.view.View
import android.widget.AdapterView
import android.widget.ArrayAdapter
import android.widget.Button
import android.widget.ImageView
import android.widget.Spinner
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.widget.AppCompatTextView
import com.aeke.fitnessmirror.foldboard.AekeObserver
import com.aeke.fitnessmirror.power.R
import com.aeke.fitnessmirror.power.aekeLifeScope
import com.aeke.fitnessmirror.power.benmo.BenMoPowerHelper
import com.aeke.fitnessmirror.power.newapi.NewPowerHelper
import com.aeke.fitnessmirror.power.newapi.adapter.AekePowerCoreAdapter
import com.tencent.mmkv.MMKV
import kotlinx.coroutines.Job
import kotlinx.coroutines.delay
import me.jessyan.autosize.AutoSizeCompat
import me.jessyan.autosize.AutoSizeConfig

class AutoTestActivity : AppCompatActivity() {

    companion object {
        @JvmStatic
        var isDEBUG = false
        const val INDEX_OTA = 1
        const val INDEX_USER_SIMULATION = 2
        const val MMKV_AUTO_TESTING = "auto_testing"
        const val MSG_SECOND_TICK = 1
        const val MSG_MOTOR_DEAD = 2
    }

    private val items = listOf(
        INDEX_OTA to "OTA升级",
        INDEX_USER_SIMULATION to "用户模拟测试"
    )

    private val counts = listOf(
        1 to "100",
        2 to "300",
        3 to "500",
        4 to "1000"
    )

    private var currentItem: Int = INDEX_OTA
    private var currentCount: Int = 100

    private var isSimulateDeath = false
    private var isMotorDead = false
    private var currentJob: Job? = null
    private var testedCount = 0
    private var successCount = 0
    private var failCount = 0
    private var currentFileName: String? = null
    private var testDuration: Int = 0 //已测试时长，单位秒
    private var mainHandler: Handler = object : Handler(Looper.getMainLooper()) {
        override fun handleMessage(msg: Message) {
            when (msg.what) {
                MSG_SECOND_TICK -> {
                    testDuration++
                    val time = testDuration.toTimeFormat()
                    timeTv.text = "已测试时长：$time"
                    if (isDestroyed) {
                        return
                    }
                    sendEmptyMessageDelayed(MSG_SECOND_TICK, 1000)
                }

                MSG_MOTOR_DEAD -> {
                    removeCallbacksAndMessages(null)
                    isMotorDead = true
                    onTestFinished()
                }

            }
        }
    }

    private var hexObserver = object : AekeObserver<String> {
        override fun update(value: String) {
            if (isSimulateDeath){
                return
            }
            Log.i("AutoTestActivity", "hexData: $value")
            mainHandler.removeMessages(MSG_MOTOR_DEAD)
            mainHandler.sendEmptyMessageDelayed(MSG_MOTOR_DEAD, 1000 * 60 * 5)
        }
    }

    private lateinit var startTestButton: Button
    private lateinit var itemSpinner: Spinner
    private lateinit var countSpinner: Spinner
    private lateinit var testingName: AppCompatTextView
    private lateinit var testingInfo: AppCompatTextView
    private lateinit var tip: AppCompatTextView
    private lateinit var timeTv: AppCompatTextView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        isDEBUG = true
        setDesignWidthInDp()
        setContentView(R.layout.activity_auto_test)
        initView()
    }

    private fun initView() {
        startTestButton = findViewById(R.id.startButton)
        itemSpinner = findViewById(R.id.itemSpinner)
        countSpinner = findViewById(R.id.countSpinner)
        testingName = findViewById(R.id.test_name)
        testingInfo = findViewById(R.id.info_content)
        tip = findViewById(R.id.test_tip)
        timeTv = findViewById(R.id.time_tv)
        timeTv.setOnClickListener {
            isSimulateDeath = true
        }
        findViewById<ImageView>(R.id.back_img).setOnClickListener {
            onBackPressed()
        }
        startTestButton.setOnClickListener(IntervalClickListener({
            startTest()
        }))
        setupItemSpinner()
        setupCountSpinner()
    }

    override fun getResources(): Resources? {
        val resources = super.getResources()
        setDesignWidthInDp()
        if (Looper.myLooper() == Looper.getMainLooper()) {
            //需要升级到 v1.1.2 及以上版本才能使用 AutoSizeCompat
            AutoSizeCompat.autoConvertDensityOfGlobal(resources) //如果没有自定义需求用这个方法
        }
        return resources
    }

    override fun onBackPressed() {
        if (startTestButton.text != "开始测试") {
            Toast.makeText(this, "请等待测试完成", Toast.LENGTH_SHORT).show()
            return
        }
        super.onBackPressed()
    }

    private fun startTest() {
        if (startTestButton.text == "开始测试") {
            startTestButton.text = "停止测试"
            MMKV.defaultMMKV().encode(MMKV_AUTO_TESTING, true)
            when (currentItem) {
                INDEX_OTA -> {
                    startOtaTest()
                }

                INDEX_USER_SIMULATION -> {
                    mainHandler.sendEmptyMessageDelayed(MSG_SECOND_TICK, 1000)
                    mainHandler.removeMessages(MSG_MOTOR_DEAD)
                    mainHandler.sendEmptyMessageDelayed(MSG_MOTOR_DEAD, 1000 * 60 * 5)
                    BenMoPowerHelper.hexDataReceiveObserver.addObserver(this, hexObserver)
                    startUserSimulationTest()
                }
            }
        } else {
            startTestButton.text = "停止中，请等待"
            MMKV.defaultMMKV().encode(MMKV_AUTO_TESTING, false)
            mainHandler.removeMessages(MSG_SECOND_TICK)
            if (currentItem == INDEX_USER_SIMULATION) {
                currentJob?.cancel()
                onTestFinished()
            }
        }
    }

    private fun startOtaTest() {
        if (!isTesting()) {
            onTestFinished()
            return
        }
        tip.visibility = View.VISIBLE
        testingName.text = "OTA升级测试"
        val fileName = getOTAFileName()
        currentFileName = fileName
        testingInfo.text =
            "目标测试次数：$currentCount\n已完成测试次数：$testedCount\n成功次数：$successCount\n失败次数：$failCount\n本次升级固件名称：$fileName"
        val data = assets.open(fileName)
            .readBytes()
        BenMoPowerHelper.startOta(data) {
            testedCount++
            if (it) {
                successCount++
            } else {
                failCount++
            }
            if (testedCount < currentCount) {
                lifecycle.aekeLifeScope.launch {
                    delay(5000)
                    startOtaTest()
                }
            } else {
                onTestFinished()
            }
        }
    }

    private fun startUserSimulationTest() {
        if (!isTesting()) {
            onTestFinished()
            return
        }
        testingName.text = "用户模拟测试"
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n"
        currentJob = lifecycle.aekeLifeScope.launch {
            realUserSimulationTest {
                testedCount++
                if (testedCount < currentCount) {
                    startUserSimulationTest()
                } else {
                    onTestFinished()
                }
            }
        }

    }

    /**
     * 用户模拟测试，30分钟为1组
     * 1组测试步骤如下：
     * 1. 开启脱手保护
     * 2.设置恒力模式，重量15kg，训练5分钟
     * 3.设置离心模式，重量10kg，训练5分钟
     * 4.设置向心模式，重量8kg，训练5分钟
     * 5.设置弹力模式，重量10kg，训练5分钟
     * 6.设置划船模式，重量8kg，训练5分钟
     * 7.卸力休息5分钟
     */
    private suspend fun realUserSimulationTest(onFinish: () -> Unit) {
        NewPowerHelper.setHandsOffProtect(true)
        delay(5000)
        NewPowerHelper.setActivate()
        delay(3000)
        NewPowerHelper.setPower(AekePowerCoreAdapter.PowerMode.STANDARD(NewPowerHelper.currentPowerSetWeight))
        delay(5000)
        NewPowerHelper.setPower(15f, true)
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n当前电机状态：标准模式，重量：${NewPowerHelper.currentPowerSetWeight}kg"
        delay(5 * 60 * 1000)

        NewPowerHelper.setPower(AekePowerCoreAdapter.PowerMode.LiXin(NewPowerHelper.currentPowerSetWeight))
        delay(5000)
        NewPowerHelper.setPower(10f, true)
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n当前电机状态：离心模式，重量：${NewPowerHelper.currentPowerSetWeight}kg"
        delay(5 * 60 * 1000)

        NewPowerHelper.setPower(AekePowerCoreAdapter.PowerMode.XiangXin(NewPowerHelper.currentPowerSetWeight))
        delay(5000)
        NewPowerHelper.setPower(8f, true)
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n当前电机状态：向心模式，重量：${NewPowerHelper.currentPowerSetWeight}kg"
        delay(5 * 60 * 1000)

        NewPowerHelper.setPower(AekePowerCoreAdapter.PowerMode.TanLi(NewPowerHelper.currentPowerSetWeight))
        delay(5000)
        NewPowerHelper.setPower(10f, true)
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n当前电机状态：弹力模式，重量：${NewPowerHelper.currentPowerSetWeight}kg"
        delay(5 * 60 * 1000)

        NewPowerHelper.setPower(AekePowerCoreAdapter.PowerMode.HuaChuan(NewPowerHelper.currentPowerSetWeight))
        delay(5000)
        NewPowerHelper.setPower(8f, true)
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n当前电机状态：划船模式，重量：${NewPowerHelper.currentPowerSetWeight}kg"
        delay(5 * 60 * 1000)

        NewPowerHelper.setUnload()
        testingInfo.text =
            "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n当前电机状态：卸力状态"
        delay(5 * 60 * 1000)

        NewPowerHelper.setHandsOffProtect(false)
        delay(5000)

        onFinish()
    }

    private fun onTestFinished() {
        startTestButton.text = "开始测试"
        tip.visibility = View.GONE
        currentJob?.cancel()
        NewPowerHelper.setPower(AekePowerCoreAdapter.PowerMode.STANDARD(2f, true))
        BenMoPowerHelper.hexDataReceiveObserver.deleteObserver(hexObserver)
        if (currentItem == INDEX_OTA) {
            testingInfo.text =
                "目标测试次数：$currentCount\n已完成测试次数：$testedCount\n成功次数：$successCount\n失败次数：$failCount\n本次升级固件名称：$currentFileName"
        } else if (currentItem == INDEX_USER_SIMULATION) {
            testingInfo.text = if (isMotorDead) "电机死机！！！" else
                "目标测试组数：$currentCount\n已完成测试组数：$testedCount\n"
        }
    }

    private fun getOTAFileName(): String {
        if (currentFileName == "HVG11_AEKE_PFC_2025-07-02-11-341.bin") {
            return "HVG11_AEKE_PFC_2026-01-09-13-477.bin"
        } else {
            return "HVG11_AEKE_PFC_2025-07-02-11-341.bin"
        }
    }

    private fun isTesting(): Boolean {
        return MMKV.defaultMMKV().decodeBool(MMKV_AUTO_TESTING, false)
    }

    private fun setDesignWidthInDp() {
        AutoSizeConfig.getInstance().designWidthInDp = 540
    }

    private fun setupItemSpinner() {
        val itemOptions = mutableSetOf<String>()

        for (item in items) {
            itemOptions.add(item.second)
        }

        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_item,
            itemOptions.toList()
        )
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        itemSpinner.adapter = adapter
        itemSpinner.setSelection(0)
        itemSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: AdapterView<*>,
                view: android.view.View?,
                position: Int,
                id: Long
            ) {
                val selectedItem = parent.getItemAtPosition(position) as String
                currentItem = items.first { it.second == selectedItem }.first
            }

            override fun onNothingSelected(parent: AdapterView<*>) {}
        }
    }

    private fun setupCountSpinner() {
        val countOptions = mutableSetOf<String>()

        for (item in counts) {
            countOptions.add(item.second)
        }
        val adapter = ArrayAdapter(
            this,
            android.R.layout.simple_spinner_item,
            countOptions.toList()
        )
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item)
        countSpinner.adapter = adapter

        countSpinner.setSelection(0)
        countSpinner.onItemSelectedListener = object : AdapterView.OnItemSelectedListener {
            override fun onItemSelected(
                parent: AdapterView<*>,
                view: android.view.View?,
                position: Int,
                id: Long
            ) {
                val selectedItem = parent.getItemAtPosition(position) as String
                currentCount = counts.first { it.second == selectedItem }.second.toInt()
            }

            override fun onNothingSelected(parent: AdapterView<*>) {}
        }
    }

    fun Int.toTimeFormat(): String {
        val hours = this / 3600
        val minutes = (this % 3600) / 60
        val seconds = this % 60
        return String.format("%02d:%02d:%02d", hours, minutes, seconds)
    }

    override fun onDestroy() {
        super.onDestroy()
        isDEBUG = false
        mainHandler.removeCallbacksAndMessages(null)
    }
}