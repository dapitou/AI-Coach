@file:Suppress("DEPRECATION", "SetTextI18n", "HardcodedText", "ViewConstructor", "UNUSED_PARAMETER", "LocalVariableName", "SpellCheckingInspection")
package com.aeke.motordemo

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.Path
import android.graphics.PorterDuff
import android.graphics.PorterDuffColorFilter
import android.graphics.Typeface
import android.os.Bundle
import android.graphics.drawable.GradientDrawable
import android.util.AttributeSet
import android.util.Log
import android.view.Gravity
import android.view.MotionEvent
import android.view.SurfaceView
import android.view.View
import android.view.animation.OvershootInterpolator
import android.view.ViewGroup
import android.view.WindowManager
import android.widget.Button
import android.widget.LinearLayout
import android.widget.TextView
import android.widget.Toast
import android.widget.ImageView
import androidx.core.graphics.toColorInt
import androidx.core.view.WindowCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.WindowInsetsControllerCompat
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope // KE-ZL-202309-0
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlin.math.abs
import kotlin.math.atan2
import kotlin.math.min
import kotlin.math.cos
import kotlin.math.max
import kotlin.math.sin
import java.util.concurrent.atomic.AtomicInteger

/**
 * AEKE 智能电机真实硬件体验 Demo
 * 适配：Android 竖屏大屏设备
 * 协议：基于 Ak21BenMoPowerHelper (38字节数据帧)
 * 算法：AI识别_电机纠错配置架构 V11.2 (彻底重构版)
 */
class MotorRealExperienceActivity : AppCompatActivity() {

    // --- 硬件配置 (请根据实际设备修改) ---
    private val serialPortPath = "/dev/ttyS9" // 确认使用 ttyS9
    private val baudRate = 57600

    // --- UI 组件 ---
    private lateinit var leftMotorPanel: MotorDetailPanel
    private lateinit var rightMotorPanel: MotorDetailPanel
    private lateinit var userStatePanel: UserStatePanel
    private lateinit var chartContainer: LinearLayout
    private lateinit var consoleText: TextView
    private lateinit var tvTotalCount: TextView

    // --- 核心逻辑 ---
    private lateinit var forceCurveView: RealtimeCurveView // 实时行程/力曲线
    private lateinit var powerBarView: RealtimeBarView // 功率图
    private val algorithmEngine = V11AlgorithmEngine()
    private lateinit var circularKnobView: CircularForceKnobView // 新增环形调力盘

    // 状态标记
    private var isRunning = false
    private var targetWeight = 5.0f // 目标设定力 (kg), 浮点数支持0.5
    private var isMotorActive = false // 激活状态
    private var currentMode = "00" // 00=标准, AA=使能, 55=失能
    private var lastTotalCount = 0
    // 生产环境 Helper 引用
    private val powerHelper = LocalBenMoPowerHelper()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON)

        // Hide system bars (Immersive Mode) using modern API
        val windowInsetsController = WindowCompat.getInsetsController(window, window.decorView)
        windowInsetsController.systemBarsBehavior =
            WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
        windowInsetsController.hide(WindowInsetsCompat.Type.systemBars())

        setupProfessionalUI()
        initHardware()
    }

    override fun onDestroy() {
        super.onDestroy()
        stopHardware()
    }

    // --- 纯代码 UI 构建 (专业数据看板风格) ---
    private fun setupProfessionalUI() { // KE-ZL-202309-0
        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setBackgroundColor("#050505".toColorInt())
            layoutParams = ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT)
        }

        // 1. 顶部 Header
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(32, 24, 32, 24)
            gravity = Gravity.CENTER_VERTICAL
            background = getRoundedBg("#1A1A1A".toColorInt(), 0f, 0f, 24f, 24f) // 底部圆角
        }
        
        // [Feature] 3. 左上角退出按钮
        val btnBack = TextView(this).apply {
            text = "✕"
            textSize = 28f
            setTextColor(Color.LTGRAY)
            gravity = Gravity.CENTER
            layoutParams = LinearLayout.LayoutParams(48, 48)
            setOnClickListener { 
                // 安全退出逻辑
                lifecycleScope.launch {
                    sendCommandSetWeight(2.5f) // 强制卸力
                    delay(100)
                    finish() 
                }
            }
        }

        val tvTitle = TextView(this).apply {
            text = "AEKE 智能电机算法引擎 V11.4" // [汉化]
            textSize = 20f
            typeface = Typeface.DEFAULT_BOLD
            setTextColor(Color.WHITE)
            layoutParams = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f).apply {
                marginStart = 24
            }
        }
        
        header.addView(btnBack)
        header.addView(tvTitle)
        // header.addView(btnEnable) // 移除手动上电，改为自动
        
        root.addView(header)

        // 1.5 全局核心数据栏 (总计次)
        val globalInfoPanel = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            setPadding(32, 16, 32, 16)
            gravity = Gravity.CENTER
            background = getRoundedBg("#222222".toColorInt(), 24f)
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.WRAP_CONTENT, LinearLayout.LayoutParams.WRAP_CONTENT).apply {
                topMargin = 16
                gravity = Gravity.CENTER_HORIZONTAL
            }
        }
        tvTotalCount = TextView(this).apply { // KE-ZL-202309-0
            textSize = 64f
            setTextColor(Color.GREEN)
            typeface = Typeface.create(Typeface.DEFAULT, Typeface.BOLD)
            text = "0"
        }
        globalInfoPanel.addView(TextView(this).apply { text = "训练总次数  "; textSize = 14f; setTextColor(Color.GRAY); gravity=Gravity.BOTTOM; setPadding(0,0,0,12); typeface = Typeface.DEFAULT_BOLD })
        globalInfoPanel.addView(tvTotalCount) // 纯数字，更具冲击力
        root.addView(globalInfoPanel)

        // 2. 数据监控区 (左右分栏 + 中间用户状态)
        val motorContainer = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            weightSum = 3f
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.2f).apply { // 增加高度占比
                setMargins(16, 8, 16, 8)
            }
        }
        
        // 左电机卡片
        leftMotorPanel = MotorDetailPanel(this, "左侧电机 (M1)", "#00BCD4".toColorInt()) // [汉化] Cyan
        val paramL = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f).apply { marginEnd = 8 }
        motorContainer.addView(leftMotorPanel, paramL)

        // 中间用户行为卡片
        userStatePanel = UserStatePanel(this).apply {
             val paramCenter = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1.2f).apply { // 增加宽度占比
                 marginEnd = 8
                 marginStart = 8
             }
             layoutParams = paramCenter
        }
        motorContainer.addView(userStatePanel)

        // 右电机卡片
        rightMotorPanel = MotorDetailPanel(this, "右侧电机 (M2)", "#E040FB".toColorInt()) // [汉化] Magenta
        val paramR = LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.MATCH_PARENT, 1f).apply { marginStart = 8 }
        motorContainer.addView(rightMotorPanel, paramR)
        
        root.addView(motorContainer)
        
        // 4. 图表区 (曲线 + 功率柱状图)
        chartContainer = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f).apply {
                setMargins(16, 16, 16, 8)
            }
            background = getRoundedBg("#121212".toColorInt(), 16f)
            setPadding(16, 16, 16, 16)
        }

        // 4.1 力/行程 曲线
        val tvChartTitle = TextView(this).apply { text = "双侧发力曲线 (KG)"; setTextColor(Color.GRAY); textSize = 12f; typeface = Typeface.DEFAULT_BOLD }
        chartContainer.addView(tvChartTitle) // KE-ZL-202309-0

        forceCurveView = RealtimeCurveView(this).apply { // 使用我们自定义的高性能View
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 2f)
        }
        chartContainer.addView(forceCurveView)

        // 4.2 功率柱状图
        val tvPowerTitle = TextView(this).apply { text = "功率输出趋势 (W)"; setTextColor(Color.GRAY); textSize = 12f; setPadding(0,10,0,0); typeface = Typeface.DEFAULT_BOLD }
        chartContainer.addView(tvPowerTitle) // KE-ZL-202309-0

        powerBarView = RealtimeBarView(this).apply {
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f)
        }
        chartContainer.addView(powerBarView)
        root.addView(chartContainer)

        // 5. 控制面板 (环形调力盘 + 状态控制)
        val controlPanel = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL
            gravity = Gravity.CENTER // [UI Fix] 1. 调力盘完全居中
            background = getRoundedBg("#1A1A1A".toColorInt(), 24f, 24f, 0f, 0f) // 顶部圆角
            setPadding(32, 16, 32, 16)
            layoutParams = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1.5f) // 增加高度给调力盘
        } // KE-ZL-202309-0
        
        // 5.1 环形调力盘
        circularKnobView = CircularForceKnobView(this).apply {
            // [UI Fix] 移除权重，设置固定大小或 wrap_content 以便居中
            layoutParams = LinearLayout.LayoutParams(600, LinearLayout.LayoutParams.MATCH_PARENT) 
            // 设置回调
            setOnValueChangedListener { value ->
                targetWeight = value
                // 实时生效: 如果当前已激活，直接下发指令
                if (isMotorActive) {
                    sendCommandSetWeight(targetWeight)
                }
            }
            setOnCenterClickListener {
                toggleMotorActiveState()
            }
        }
        controlPanel.addView(circularKnobView)

        root.addView(controlPanel)

        // 6. 底部日志
        consoleText = TextView(this).apply {
            textSize = 10f
            setTextColor("#666666".toColorInt())
            maxLines = 2
            text = "系统日志: 等待串口连接..."
            setPadding(16, 8, 16, 8)
            setBackgroundColor(Color.BLACK)
        }
        root.addView(consoleText)

        setContentView(root)
    }
    
    // [UI Helper] 生成圆角背景
    private fun getRoundedBg(color: Int, vararg radii: Float): GradientDrawable {
        return GradientDrawable().apply {
            setColor(color)
            if (radii.size == 1) cornerRadius = radii[0]
            else if (radii.size == 4) cornerRadii = floatArrayOf(radii[2], radii[2], radii[3], radii[3], radii[1], radii[1], radii[0], radii[0]) // TL, TR, BR, BL order varies, using standard
            // Simple corner radius
            if (radii.size == 1) cornerRadius = radii[0]
        }
    }

    // [Logic Fix] 完整的激活/卸力 闭环逻辑
    private fun toggleMotorActiveState() {
        isMotorActive = !isMotorActive
        circularKnobView.setActiveState(isMotorActive)
        
        if (isMotorActive) {
            // [Protocol Fix] 2. 设力未生效修复：严谨的时序逻辑
            // 流程: Enable(AA) -> Delay -> Reset(FC) -> Delay -> Enable(AA) -> SetWeight(00)
            // 二次 Enable 是为了防止 Reset 过程中意外清除使能状态
            logUI("正在激活... 重置原点中")
            sendCommandEnable() // 确保上电
            lifecycleScope.launch {
                delay(200)
            sendCommandResetOrigin()
                delay(500) // [Fix] 增加延时至 500ms，确保 FC 状态结束
                sendCommandEnable() // 再次确认使能
                delay(100)
                sendCommandSetWeight(targetWeight)
                logUI("力控已生效: ${targetWeight}kg")
            }
        } else {
            // 卸力流程: 立即回到 2.5kg (3kg buffer)
            sendCommandSetWeight(2.5f)
            logUI("已卸力 (安全模式 2.5kg)")
        }
    }

    // --- 硬件与数据流 ---

    private fun initHardware() {
        lifecycleScope.launch(Dispatchers.IO) {
            try {
                // 1. 权限预检 (针对工程机环境的自动提权)
                requestRootPermission()
                
                delay(500) // [Fix] 等待 su 提权完成

                // 2. 初始化 PowerHelper (使用 power 模块的标准实现)
                powerHelper.init()
                logUI("PowerHelper 初始化中... 等待数据流")
                
                // [Fix] 初始发送 Enable，防止电机处于 55 失能状态
                delay(200)
                sendCommandEnable()

                // 3. 注册观察者 (连接算法引擎)
                // 注意: update 回调可能在 IO 线程，适合直接进行算法计算
                powerHelper.setOnDataListener listener@{ model ->
                    if (!isRunning) return@listener

                    // [Fast Track] 1. 算法解算 (零GC)
                    algorithmEngine.process(model)

                    // [Fast Track] 2. 图表直接更新
                    forceCurveView.addPoint(algorithmEngine.filteredM1Force, algorithmEngine.filteredM2Force)
                    powerBarView.addPoint(algorithmEngine.m1PowerWatts, algorithmEngine.m2PowerWatts)
                }

                isRunning = true

                // [Architecture Change] Start independent UI refresh loop (Slow Track)
                // Decouples text layout updates from high-frequency data processing
                startUiRefreshLoop()

            } catch (e: Throwable) {
                logUI("硬件异常: ${e.message}")
                e.printStackTrace()
            }
        }
    }

    private fun requestRootPermission() {
        try {
            val file = java.io.File(serialPortPath)
            if (!file.canRead() || !file.canWrite()) {
                val p = Runtime.getRuntime().exec("su")
                val os = p.outputStream
                os.write("chmod 666 $serialPortPath\n".toByteArray())
                // Ak21 需要 57600
                os.write("stty -F $serialPortPath $baudRate raw -echo\n".toByteArray())
                os.write("exit\n".toByteArray())
                os.flush()
                p.waitFor()
                logUI("ROOT 提权成功")
            }
        } catch (e: Exception) {
            logUI("ROOT 提权警告: ${e.message}")
        }
    }

    // [Core Refactor] Low-Frequency UI Loop (Slow Track - 20 FPS)
    // Solves "Layout Thrashing" and Main Thread Jitter
    private fun startUiRefreshLoop() {
        lifecycleScope.launch(Dispatchers.Main) {
            while (true) {
                if (isRunning) {
                    updateTextUI()
                }
                delay(50) // 50ms = 20 FPS. Smooth for text, easy on CPU.
            }
        }
    }

    private fun updateTextUI() {
        val engine = algorithmEngine
        
        // Update User State
        // Use the latest event stored in engine (which might be latched logic inside engine)
        userStatePanel.update(engine.userStateStr, engine.userStroke, engine.currentEvent)
        
        // Update Motor Panels with COMPLETE data (Data Recovery)
        leftMotorPanel.update(
            engine.filteredM1Force, engine.leftStroke, engine.leftStateStr, 
            engine.m1PowerWatts, engine.leftRawCount, 
            engine.m1Temp, engine.m1ErrorCode, engine.m1AbsPos, engine.m1Speed
        )
        rightMotorPanel.update(
            engine.filteredM2Force, engine.rightStroke, engine.rightStateStr, 
            engine.m2PowerWatts, engine.rightRawCount,
            engine.m2Temp, engine.m2ErrorCode, engine.m2AbsPos, engine.m2Speed
        )

        tvTotalCount.text = "${engine.totalCount}"
        
        // [Feature 5] 计次动效: 缩放回弹
        if (engine.totalCount != lastTotalCount) {
            tvTotalCount.animate().scaleX(1.5f).scaleY(1.5f).setDuration(100).withEndAction {
                tvTotalCount.animate().scaleX(1.0f).scaleY(1.0f).setInterpolator(OvershootInterpolator()).setDuration(200).start()
            }.start()
            lastTotalCount = engine.totalCount
        }
        
        
        if (engine.currentEvent.isNotEmpty()) {
            consoleText.text = "EVENT: ${engine.currentEvent}"
        }
    }
    
    // Removed old updateUI method
    
    // --- 指令发送 (全面接管 Ak21BenMoPowerHelper) ---

    private fun sendCommandEnable() {
        powerHelper.setEnablePowerMode()
        logUI("CMD: 发送使能 (AA)")
        currentMode = "AA"
    }

    private fun sendCommandSetWeight(kg: Float) {
        // Ak21BenMoPowerHelper 期望 Hex String 参数
        val valueInt = (kg * 100).toInt()
        val hexStr = String.format("%04X", valueInt) // e.g. 5.5kg -> 550 -> "0226"
        
        // 开启平滑 (isSmooth = true), 需先设置属性
        powerHelper.isSmooth = true
        powerHelper.smoothRate = 0x0A // 10
        
        // setStandardMode(huiLi, laLi)
        powerHelper.setStandardMode(hexStr, hexStr)
        
        currentMode = "00"
    }

    private fun sendCommandResetOrigin() {
        powerHelper.setResetMode()
        logUI("CMD: 重置原点 (FC)")
        currentMode = "FC"
    }

    private fun sendCommandDisable() {
        powerHelper.setUnEnablePowerMode()
        currentMode = "55"
    }

    private fun stopHardware() {
        isRunning = false
        sendCommandDisable()
        // Helper 通常不关闭，或者没有暴露 close 方法，这里仅逻辑停止
    }

    private fun safeExit() {
        stopHardware()
        finish()
        android.os.Process.killProcess(android.os.Process.myPid())
    }

    private fun logUI(msg: String) {
        runOnUiThread {
            consoleText.text = msg
            Log.d("MotorReal", msg)
            }
        }
}

// ===================================================================================
// V11.0.0 算法引擎 (User Behavior & Motor State Machine)
// ===================================================================================

class V11AlgorithmEngine {
    private val m1Processor = SingleMotorProcessor()
    private val m2Processor = SingleMotorProcessor()
    private val userProcessor = UserStateProcessor()
    
    // [产品定义修正] 文档要求: 底层强制平滑。由于协议层未下发Byte12/13平滑参数，
    // 此处必须开启软件算法滤波，Alpha调整为0.15以兼顾实时性与阻尼质感。
    private val filterAlpha = 0.15f 
    private var lastM1Force = 0f
    private var lastM2Force = 0f
    
    // [核心重构] 移除 AnalysisResult 数据类，改为可变成员变量 (Mutable Fields)
    // 目的: 实现 Zero-Allocation (零GC)，避免每秒100次的对象创建导致内存抖动
    var leftStateStr: String = ""
    var rightStateStr: String = ""
    var leftStroke: Float = 0f
    var rightStroke: Float = 0f
    var userStateStr: String = ""
    var userStroke: Float = 0f
    var totalCount: Int = 0
    var m1PowerWatts: Float = 0f
    var m2PowerWatts: Float = 0f
    var filteredM1Force: Float = 0f
    var filteredM2Force: Float = 0f
    var leftRawCount: Int = 0
    var rightRawCount: Int = 0
    
    // [Data Recovery] Storing hardware monitor states
    var m1Temp: Int = 0
    var m2Temp: Int = 0
    var m1ErrorCode: Int = 0
    var m2ErrorCode: Int = 0
    var m1AbsPos: Float = 0f
    var m2AbsPos: Float = 0f
    var m1Speed: Float = 0f
    var m2Speed: Float = 0f

    // 事件标志位 (用于锁存)
    var currentEvent: String = ""
    var hasNewEvent: Boolean = false // 标记当前帧是否产生了新事件

    fun process(model: PowerControlModelInterface) {
        hasNewEvent = false // Reset per frame
        
        // 提取数据 (PowerControlModelInterface 已经是解析好的物理值)
        // [Fix 5. 功率突变] 增加 Clamp 过滤，防止协议解析错误或硬件噪声导致的异常值
        val m1F = model.m1Power / 100f
        var m1V = model.m1Rate.toFloat()
        val m1P = model.m1Distance.toFloat()
        
        val m2F = model.m2Power / 100f
        var m2V = model.m2Rate.toFloat()
        val m2P = model.m2Distance.toFloat()
        
        // Clamp Protection
        if (abs(m1V) > 1000f) m1V = m1Speed // Ignore spike > 10m/s, use last valid
        if (abs(m2V) > 1000f) m2V = m2Speed
        
        // 3. 功率计算 (P = F * v)。注意 Ak21 速度单位 cm/s，力单位 kg。
        // P (W) = (kg * 9.8) * (cm/s / 100)
        // [Fix 5] 功率突变修复：增加 max 限制，防止计算出负功率或异常大功率
        val rawPower1 = m1F * m1V * 0.098f
        val rawPower2 = m2F * m2V * 0.098f
        val power1 = if (rawPower1 in 0f..2000f) rawPower1 else 0f // 过滤异常值
        val power2 = if (rawPower2 in 0f..2000f) rawPower2 else 0f

        // 0. 数据平滑 (Low Pass Filter)
        val sm1Force = lowPassFilter(m1F, lastM1Force)
        val sm2Force = lowPassFilter(m2F, lastM2Force)
        lastM1Force = sm1Force
        lastM2Force = sm2Force

        // 1. 物理层处理 (Motor Physics Layer)
        val p1 = m1Processor.update(sm1Force, m1P, m1V)
        val p2 = m2Processor.update(sm2Force, m2P, m2V)
        
        val mainStroke = max(p1.realStroke, p2.realStroke)
        // KE-ZL-202309-0
        // 2. 用户行为层处理 (User Behavior Layer)
        // 融合双电机数据，判定用户当前处于什么阶段
        val userStateResult = userProcessor.update(
            p1.state, p2.state, 
            p1.realStroke, p2.realStroke,
            p1.stdStroke, p2.stdStroke
        )

        // 更新公共字段 (无内存分配)
        leftStateStr = p1.state.cnName
        rightStateStr = p2.state.cnName
        leftStroke = p1.realStroke
        rightStroke = p2.realStroke
        userStateStr = userStateResult.stateName
        userStroke = mainStroke
        totalCount = userProcessor.totalCount
        m1PowerWatts = power1
        m2PowerWatts = power2
        filteredM1Force = sm1Force
        filteredM2Force = sm2Force
        leftRawCount = m1Processor.rawCount
        rightRawCount = m2Processor.rawCount
        
        // Capture hardware state for UI display
        m1Temp = model.m1Temp
        m2Temp = model.m2Temp
        m1ErrorCode = model.m1ErrorCode
        m2ErrorCode = model.m2ErrorCode
        m1AbsPos = m1P
        m2AbsPos = m2P
        m1Speed = m1V
        m2Speed = m2V

        currentEvent = userStateResult.event ?: ""
        if (userStateResult.event != null) hasNewEvent = true
    }
    
    private fun lowPassFilter(current: Float, last: Float): Float {
        if (last == 0f) return current
        return last + filterAlpha * (current - last)
    }
}

// ===================================================================================
// 本地硬件适配层 (Local Hardware Layer)
// 替代缺失的 power 模块，直接管理串口与协议，修复 Unresolved reference 问题
// ===================================================================================

interface PowerControlModelInterface {
    val m1Power: Int // Raw Value: kg * 100
    val m1Rate: Int  // Signed: cm/s
    val m1Distance: Int // Signed: cm
    val m2Power: Int // Raw Value
    val m2Rate: Int
    val m2Distance: Int
    val m1Temp: Int
    val m2Temp: Int
    val m1ErrorCode: Int
    val m2ErrorCode: Int
}

class LocalBenMoPowerHelper {
    var isSmooth: Boolean = false
    var smoothRate: Int = 0
    
    private var dataListener: ((PowerControlModelInterface) -> Unit)? = null
    private val serialManager = SerialManager()
    private val parser = ProtocolParser()
    private var isReading = false

    fun init() {
        if (serialManager.open("/dev/ttyS9")) {
            isReading = true
            Thread { readLoop() }.start()
        }
    }
    
    fun setOnDataListener(listener: (PowerControlModelInterface) -> Unit) {
        this.dataListener = listener
    }

    fun setEnablePowerMode() = sendHex("640202AA")
    fun setUnEnablePowerMode() = sendHex("64020255")
    fun setResetMode() = sendHex("640201FC")
    
    fun setStandardMode(huiLiHex: String, laLiHex: String) {
        // 构造标准模式指令: 64 02 01 00 [huiLi 2] [laLi 2] ... [smooth 1] [rate 1]
        val cmd = ByteArray(32)
        cmd[0] = 0x64; cmd[1] = 0x02; cmd[2] = 0x01; cmd[3] = 0x00
        
        val hVal = huiLiHex.toInt(16)
        val lVal = laLiHex.toInt(16)
        
        cmd[4] = ((hVal shr 8) and 0xFF).toByte()
        cmd[5] = (hVal and 0xFF).toByte()
        cmd[6] = ((lVal shr 8) and 0xFF).toByte()
        cmd[7] = (lVal and 0xFF).toByte()
        
        // 注入平滑参数
        if (isSmooth) {
            cmd[12] = 0x01
            cmd[13] = smoothRate.toByte()
        }
        
        fillCRC(cmd)
        cmd[30] = 0x0D; cmd[31] = 0x0A
        serialManager.write(cmd)
    }

    private fun sendHex(prefix: String) {
        val cmd = ByteArray(32)
        val pBytes = hexStringToBytes(prefix)
        System.arraycopy(pBytes, 0, cmd, 0, pBytes.size)
        fillCRC(cmd)
        cmd[30] = 0x0D; cmd[31] = 0x0A
        serialManager.write(cmd)
    }

    private fun readLoop() {
        val buffer = ByteArray(1024)
        while (isReading) {
            val len = serialManager.read(buffer)
            if (len > 0) {
                val frames = parser.parse(buffer, len)
                frames.forEach { dataListener?.invoke(it) }
            } else {
                Thread.sleep(5)
            }
        }
    }
    
    private fun fillCRC(cmd: ByteArray) {
        var crc = 0x00
        for (i in 0 until 29) { // Ak21 CRC range 0..28 (byte 29 is CRC)
            crc = CRC8.compute(crc, cmd[i].toInt())
        }
        cmd[29] = crc.toByte()
    }

    private fun hexStringToBytes(s: String): ByteArray {
        val len = s.length
        val data = ByteArray(len / 2)
        var i = 0
        while (i < len) {
            data[i / 2] = ((Character.digit(s[i], 16) shl 4) + Character.digit(s[i + 1], 16)).toByte()
            i += 2
        }
        return data
    }
}

data class LocalPowerData(
    override val m1Power: Int, override val m1Rate: Int, override val m1Distance: Int,
    override val m2Power: Int, override val m2Rate: Int, override val m2Distance: Int,
    override val m1Temp: Int, override val m2Temp: Int,
    override val m1ErrorCode: Int, override val m2ErrorCode: Int
) : PowerControlModelInterface

class ProtocolParser {
    private val buffer = ByteArray(2048)
    private var wIdx = 0
    
    fun parse(data: ByteArray, len: Int): List<PowerControlModelInterface> {
        if (wIdx + len > buffer.size) wIdx = 0
        System.arraycopy(data, 0, buffer, wIdx, len)
        wIdx += len
        
        val res = ArrayList<PowerControlModelInterface>()
        var ptr = 0
        // Ak21 帧长度 38 字节
        while (ptr <= wIdx - 38) {
            // Header: 64 02
            if (buffer[ptr] == 0x64.toByte() && buffer[ptr+1] == 0x02.toByte()) {
                 // [Fix Data Spikes & Logic] 
                 // 1. Force 是无符号数 (Unsigned), 且单位是 0.01kg
                 val m1Force = getUInt16(ptr + 3) 
                 // 2. Speed/Rate 是有符号数 (Signed Short), 必须处理负数! 否则回绳速度变成 65535, 导致状态机死锁
                 val m1Rate = getSInt16(ptr + 5)
                 // 3. Distance 是有符号数
                 val m1Dist = getSInt16(ptr + 7)
                 
                 val m2Force = getUInt16(ptr + 14)
                 val m2Rate = getSInt16(ptr + 16)
                 val m2Dist = getSInt16(ptr + 18)
                 
                 // Diagnostics
                 val m1E = buffer[ptr + 25].toInt()
                 val m2E = buffer[ptr + 26].toInt()
                 val m1T = buffer[ptr + 31].toInt()
                 val m2T = buffer[ptr + 32].toInt()
                 
                 res.add(LocalPowerData(m1Force, m1Rate, m1Dist, m2Force, m2Rate, m2Dist, m1T, m2T, m1E, m2E))
                 ptr += 38
            } else {
                ptr++
            }
        }
        
        if (ptr < wIdx) {
            val rem = wIdx - ptr
            System.arraycopy(buffer, ptr, buffer, 0, rem)
            wIdx = rem
        } else {
            wIdx = 0
        }
        return res
    }
    
    // 解析无符号 16位 (0 ~ 65535) -> 用于力/Raw值
    private fun getUInt16(idx: Int): Int {
        return ((buffer[idx].toInt() and 0xFF) shl 8) or (buffer[idx+1].toInt() and 0xFF)
    }

    // 解析有符号 16位 (-32768 ~ 32767) -> 用于速度/位置
    private fun getSInt16(idx: Int): Int {
        val high = buffer[idx].toInt() and 0xFF
        val low = buffer[idx+1].toInt() and 0xFF
        val raw = (high shl 8) or low
        return raw.toShort().toInt() // 关键: 转为 Short 恢复符号位
    }
}

class SerialManager {
    private var fis: java.io.FileInputStream? = null
    private var fos: java.io.FileOutputStream? = null
    
    fun open(path: String): Boolean {
        return try {
            val f = java.io.File(path)
            if (!f.canRead()) return false
            fis = java.io.FileInputStream(f)
            fos = java.io.FileOutputStream(f)
            true
        } catch(e: Exception) { false }
    }
    
    fun read(b: ByteArray): Int = fis?.read(b) ?: 0
    fun write(b: ByteArray) {
        try {
            fos?.write(b)
            fos?.flush()
        } catch (_: Exception) {}
    }
}

object CRC8 {
    fun compute(crc: Int, data: Int): Int {
        var c = crc xor data
        repeat(8) {
             c = if ((c and 0x01) != 0) (c ushr 1) xor 0x8C else (c ushr 1)
        }
        return c
    }
}

// 单电机物理状态机
class SingleMotorProcessor {
    // 严格按照文档定义: 准备 | 向心 | 顶峰 | 离心 | 复位 // KE-ZL-202309-0
    enum class MotorState(val cnName: String) {
        PREPARE("准备"),
        CONCENTRIC("向心"),
        PEAK("顶峰"),
        ECCENTRIC("离心"),
        RESET("复位")
    }
    
    // 阈值适配策略 (中/长行程默认)
    private val thresholdStatic = 4.0f // 静止区 < 4.0cm
    private val thresholdTrigger = 6.0f // 触发阈值 > 6.0cm (实测建议 4.0 增强灵敏度)
    private val thresholdReturn = 4.0f // 回程阈值 4.0cm

    data class PhysicsContext(
        var state: MotorState = MotorState.PREPARE,
        var startPos: Float = 0f,
        var realStroke: Float = 0f,
        var realVel: Float = 0f, // cm/s (注意单位统一)
        var stdStroke: Float = 50f
    ) // KE-ZL-202309-0

    private val ctx = PhysicsContext()
    val baseline = DynamicBaseline()
    var rawCount = 0
    
    // 过程变量
    private var peakPosInCycle = 0f // 当前循环的峰值位置 (文档: [峰值位置])
    // KE-ZL-202309-0
    fun update(force: Float, pos: Float, speed: Float): PhysicsContext {
        // 速度单位转换: cm/s -> m/s (文档逻辑多用 m/s)
        val speedMps = speed / 100f 
        
        // 1. 更新动态基准
        baseline.update(force, pos, speedMps, ctx.state)
        
        // 2. 计算实时物理量
        ctx.startPos = baseline.stdStartPos // KE-ZL-202309-0
        // 文档公式: 实时行程 = 当前位置 - 标准起点
        // 注意: 拉索拉出，位置增加。若未拉出，pos 可能略小于 startPos (抖动)，取 max(0)
        ctx.realStroke = max(0f, pos - ctx.startPos) 
        ctx.realVel = speed
        ctx.stdStroke = baseline.stdStroke

        // 3. 状态机流转
        when (ctx.state) {
            MotorState.PREPARE -> {
                peakPosInCycle = 0f // KE-ZL-202309-0
                // 进入向心条件: 实时行程 > 触发阈值 AND (速度 > 0.05m/s OR 连续增加)
                // 优化: 降低阈值至 2.5cm 以提升响应 (接近超短行程标准)
                if (ctx.realStroke > 2.5f && speedMps > 0.05f) {
                    transitionTo(MotorState.CONCENTRIC)
                }
            }
            MotorState.CONCENTRIC -> {
                // 更新峰值位置 // KE-ZL-202309-0
                if (ctx.realStroke > peakPosInCycle) peakPosInCycle = ctx.realStroke
                
                // 进入顶峰条件:
                // 1. 自然转折: 速度趋势由正转负 AND 行程 > 50%标准行程
                // 2. 静态保持: |速度| < 0.05m/s AND 行程 > 80%标准行程
                
                // 实战优化: 只要速度明显下降或转负，且行程足够，即视为顶峰或经过顶峰
                val isHighEnough = ctx.realStroke > (baseline.stdStroke * 0.5f) || ctx.realStroke > 10.0f // 冷启动10cm // KE-ZL-202309-0
                val isTurning = speedMps < 0.0f // 速度转负 // KE-ZL-202309-0
                val isStatic = abs(speedMps) < 0.05f && ctx.realStroke > (baseline.stdStroke * 0.8f) // KE-ZL-202309-0
                
                if (isHighEnough && (isTurning || isStatic)) { // KE-ZL-202309-0
                    transitionTo(MotorState.PEAK)
                }
                
                // [安全边界] 速度异常过快时的保护逻辑 (如失控)
                // 若速度 < -1.5m/s (极快回弹)，强制重置状态，防止算法错乱
                if (speedMps < -1.5f) transitionTo(MotorState.RESET)
            }
            MotorState.PEAK -> {
                if (ctx.realStroke > peakPosInCycle) peakPosInCycle = ctx.realStroke // 顶峰偶有更高
                
                // 退出条件1: 转离心. 实时行程 较 [峰值位置] 回落超过 回程阈值 (4.0cm)
                // 优化: 2.5cm
                if ((peakPosInCycle - ctx.realStroke) > 2.5f) {
                    transitionTo(MotorState.ECCENTRIC)
                }
                // 退出条件2: 假动作回向心
                if (speedMps > 0.05f && ctx.realStroke > peakPosInCycle) {
                    transitionTo(MotorState.CONCENTRIC)
                }
            }
            MotorState.ECCENTRIC -> {
                // 退出条件1: 复位. 行程 < 静止阈值 (4.0cm) // KE-ZL-202309-0
                if (ctx.realStroke < 4.0f) {
                    transitionTo(MotorState.RESET)
                }
                // 退出条件2: 连续动作. 速度再次转正 > 0.05m/s 且行程增加
                if (speedMps > 0.05f) {
                    transitionTo(MotorState.CONCENTRIC)
                }
            }
            MotorState.RESET -> { // KE-ZL-202309-0
                // 动作: 触发计次结算(已在PEAK/ECCENTRIC触发)，流转至 PREPARE
                // 自动流转回准备
                transitionTo(MotorState.PREPARE)
            }
        }

        return ctx
    }

    private fun transitionTo(newState: MotorState) {
        if (ctx.state == newState) return
        // KE-ZL-202309-0
        val lastState = ctx.state
        ctx.state = newState
        
        // 物理计次逻辑: 满足 [单电机计次条件] 时 +1
        // 触发时机: 向心 -> 顶峰 (或 向心 -> 离心)
        if (lastState == MotorState.CONCENTRIC && (newState == MotorState.PEAK || newState == MotorState.ECCENTRIC)) {
             // 有效性判定: 幅度达标 (>= 0.8 * stdStroke, 冷启动 > 15cm)
             // [产品定义修正] V11.2 标准：严格执行 0.8 (80%) 阈值，拒绝 0.6 的放水行为
             if (peakPosInCycle >= (baseline.stdStroke * 0.8f) || peakPosInCycle > 15.0f) { 
                 rawCount++ // KE-ZL-202309-0
             }
        }
        
        if (newState == MotorState.PEAK) {
            baseline.setPeakPos(peakPosInCycle + ctx.startPos)
        }
    }
}

// 用户行为状态机 (业务层)
class UserStateProcessor {
    // 文档定义: 准备 | 向心 | 顶峰 | 离心 | 复位 // KE-ZL-202309-0
    enum class UserState(val cnName: String) {
        PREPARE("准备"),
        CONCENTRIC("向心(拉)"),
        PEAK("顶峰(Hold)"),
        ECCENTRIC("离心(放)"),
        RESET("复位")
    }
    data class StateResult(val stateName: String, val event: String?)

    private var state = UserState.PREPARE
    var totalCount = 0 // KE-ZL-202309-0
    
    // [Fix 1] 独立计次追踪，解决漏计问题
    private var leftCount = 0
    private var rightCount = 0
    private var lastLeftState = SingleMotorProcessor.MotorState.PREPARE
    private var lastRightState = SingleMotorProcessor.MotorState.PREPARE
    
    // 同步窗口
    private var lastLeftPeakTime = 0L
    private var lastRightPeakTime = 0L
    private var lastMergedTime = 0L

    fun update(
        leftState: SingleMotorProcessor.MotorState,
        rightState: SingleMotorProcessor.MotorState,
        leftStroke: Float,
        rightStroke: Float,
        leftStdStroke: Float,
        rightStdStroke: Float
    ): StateResult {
        var event: String? = null
        val lastUserState = state
        // KE-ZL-202309-0
        // 综合行程和标准行程 (双侧协同模式: 取最大值)
        val mainStroke = max(leftStroke, rightStroke)
        val mainStdStroke = max(leftStdStroke, rightStdStroke)

        // [Fix 1] 核心计次逻辑下沉：独立检测每一侧的上升沿
        val now = System.currentTimeMillis()
        val countThreshold = if (mainStdStroke < 15f) 15f else (mainStdStroke * 0.8f)

        // 检测左侧顶峰
        if (lastLeftState == SingleMotorProcessor.MotorState.CONCENTRIC && leftState == SingleMotorProcessor.MotorState.PEAK) {
             if (leftStroke >= countThreshold) {
                 leftCount++
                 lastLeftPeakTime = now
                 event = tryMergeCount(now)
             }
        }
        
        // 检测右侧顶峰
        if (lastRightState == SingleMotorProcessor.MotorState.CONCENTRIC && rightState == SingleMotorProcessor.MotorState.PEAK) {
             if (rightStroke >= countThreshold) {
                 rightCount++
                 lastRightPeakTime = now
                 event = tryMergeCount(now)
             }
        }
        
        lastLeftState = leftState
        lastRightState = rightState

        // 状态融合逻辑
        state = when {
            leftState == SingleMotorProcessor.MotorState.PREPARE && rightState == SingleMotorProcessor.MotorState.PREPARE -> UserState.PREPARE
            leftState == SingleMotorProcessor.MotorState.RESET && rightState == SingleMotorProcessor.MotorState.RESET -> UserState.RESET
            leftState == SingleMotorProcessor.MotorState.PEAK || rightState == SingleMotorProcessor.MotorState.PEAK -> UserState.PEAK // 优先级提升
            leftState == SingleMotorProcessor.MotorState.CONCENTRIC || rightState == SingleMotorProcessor.MotorState.CONCENTRIC -> UserState.CONCENTRIC
            leftState == SingleMotorProcessor.MotorState.ECCENTRIC || rightState == SingleMotorProcessor.MotorState.ECCENTRIC -> UserState.ECCENTRIC
            else -> state // 保持当前状态
        }

        if (lastUserState != state && event == null) {
            event = "用户状态 -> ${state.cnName}"
        }

        return StateResult(state.cnName, event)
    }
    
    // [Fix 1] 尝试合并计次 (同步窗口逻辑)
    private fun tryMergeCount(now: Long): String {
        // 如果最近一次合并发生不久，说明这是同一个同步动作的第二次触发，忽略
        if (now - lastMergedTime < 400) return "同步动作(Merged)"
        
        // 检查双侧时间差
        val diff = abs(lastLeftPeakTime - lastRightPeakTime)
        if (diff < 300) { // 300ms 内先后到达 -> 视为一次双侧同步
            // 只有当这是“后到达”的一侧，且“先到达”的一侧已经触发过计次时，实际上我们已经在第一次触发时计了数
            // 但为了简单，我们在每次单侧触发时检查：
            // 策略：每次单侧触发都导致 totalCount++ ? 不行，那样同步会计2次。
            // 正确策略：
            // 如果 (now - lastOtherPeakTime < 300)，说明另一侧刚触发过。这意味着这是同步动作的第二发。
            // 此时不应该增加 totalCount (因为第一发已经加了)，或者应该合并。
            // 简化逻辑：每次单侧触发先 +1。如果是同步的第二发，则 -1 (回滚) 或者 不加。
            // 更好逻辑：
            // Trigger 1 (L): diff > 300 (R is old). Total++.
            // Trigger 2 (R, 100ms later): diff = 100 < 300. This is the partner. Don't add total.
            // 记录 lastMergedTime = now.
            lastMergedTime = now
            return "双侧同步 (Sync)"
        } else {
            // 独立动作
            totalCount++
            return "有效计次 +1"
        }
    }
}

// ===================================================================================
// 动态基准池 (严格按文档)
// ===================================================================================
class DynamicBaseline {
    var stdStartPos: Float = 0f
        private set // KE-ZL-202309-0
    var stdStroke: Float = 50f // 默认中行程
        private set
    var peakPos: Float = 0f
        private set

    private val posBuffer = ArrayDeque<Float>()
    private val strokeHistory = ArrayDeque<Float>()
    // KE-ZL-202309-0
    fun update(force: Float, pos: Float, vel: Float, currentState: SingleMotorProcessor.MotorState) {
        // 1. 更新起点 (std_start_pos)
        if (posBuffer.size >= 10) posBuffer.removeFirst() // 1s @ 10Hz
        posBuffer.add(pos)

        // 智能漂移修正: 允许在 [准备] 或 [复位] 状态下更新
        if (currentState == SingleMotorProcessor.MotorState.PREPARE || currentState == SingleMotorProcessor.MotorState.RESET) { // KE-ZL-202309-0
            val minPos = posBuffer.minOrNull() ?: pos
            val maxPos = posBuffer.maxOrNull() ?: pos
            // 条件1: 张力 > 2.0kg (文档)
            if (force > 2.0f && (maxPos - minPos) < 2.0f) {
                // 条件3: 低速确认 |平均速度| < 0.05m/s (文档)
                if (abs(vel) < 0.05f) {
                    // 更新起点 (阻尼更新简化为直接更新)
                    stdStartPos = posBuffer.average().toFloat()
                }
            }
        }

        // 2. 更新标准行程 (std_stroke) - 在复位时结算
        if (currentState == SingleMotorProcessor.MotorState.RESET) { // KE-ZL-202309-0
            val lastStroke = abs(peakPos - stdStartPos) // 确保正值
            // 动态更新: 50% - 150% 范围内入队
            if (lastStroke in (stdStroke * 0.5f)..(stdStroke * 1.5f)) {
                if (strokeHistory.size >= 5) strokeHistory.removeFirst()
                strokeHistory.add(lastStroke)
                stdStroke = strokeHistory.average().toFloat()
            }
            // 冷启动
            if (strokeHistory.isEmpty() && lastStroke > 15f) { // 文档: 第一笔 > 15cm (或50%) // KE-ZL-202309-0
                strokeHistory.add(lastStroke)
                stdStroke = lastStroke
            }
        }
    }

    fun setPeakPos(pos: Float) {
        peakPos = pos
    }
}

// ===================================================================================
// 自定义 UI 组件 (Custom Views)
// ===================================================================================

class MotorDetailPanel(context: Context, private val title: String, private val colorTheme: Int) : LinearLayout(context) {
    // [UI Polish] Use Monospace font for stable numbers
    private val valTypeface = Typeface.MONOSPACE
    private val lblTypeface = Typeface.DEFAULT_BOLD
    
    private val tvTitle = TextView(context).apply { text = title; setTextColor(colorTheme); textSize = 12f; typeface = Typeface.DEFAULT_BOLD; }
    
    // [UI Fix] 3. 布局重构: 数字在上(大)，名称在下(小)
    // Force, Stroke, Power, Speed
    private val tvForce = createValView()
    private val tvStroke = createValView()
    private val tvPower = createValView()
    private val tvSpeed = createValView()

    // State, Count -> 32sp Highlighted
    private val tvState = TextView(context).apply { textSize = 32f; setTextColor(Color.YELLOW); typeface = lblTypeface; text = "准备" }
    private val tvRawCount = TextView(context).apply { textSize = 32f; setTextColor(Color.GREEN); typeface = lblTypeface; text = "0" }
    
    // Monitor Section (Restored Data)
    private val tvMonitor = TextView(context).apply { textSize = 10f; setTextColor(Color.GRAY); text = "Temp: -- | Err: --" }

    private fun createValView() = TextView(context).apply { textSize = 24f; setTextColor(Color.WHITE); typeface = valTypeface; text = "0" }

    init {
        orientation = VERTICAL
        // [UI Polish] 6. 增加圆角背景
        background = getRoundedBg(0xAA1E1E1E.toInt(), 16f)
        setPadding(16, 16, 16, 16)
        
        addView(tvTitle)
        
        // Row 1: Primary Metrics (Force & Stroke)
        val rowMain = LinearLayout(context).apply {
            orientation = HORIZONTAL
            weightSum = 2f
            setPadding(0, 16, 0, 0)
            addView(createKVBlock("实时拉力 (KG)", tvForce), LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f))
            addView(createKVBlock("实时行程 (CM)", tvStroke), LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f))
        }
        addView(rowMain)
        
        // Row 2: Secondary Metrics (Power & Speed)
        val rowSub = LinearLayout(context).apply {
            orientation = HORIZONTAL
            setPadding(0, 16, 0, 0)
            addView(createKVBlock("爆发功率 (W)", tvPower), LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f))
            addView(createKVBlock("运动速度 (M/S)", tvSpeed), LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f))
        }
        addView(rowSub)

        // Row 3: State & Count
        val rowState = LinearLayout(context).apply {
            orientation = HORIZONTAL
            setPadding(0, 24, 0, 8)
            // 调整布局比例，让 Count 占据右侧显著位置
            addView(createKVBlock("当前状态", tvState), LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f))
            addView(createKVBlock("单侧计次", tvRawCount), LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f))
        }
        addView(rowState)
        
        // Row 4: Hardware Monitor
        addView(View(context).apply { setBackgroundColor(0xFF333333.toInt()); layoutParams = LayoutParams(-1, 1).apply { topMargin=8; bottomMargin=8 } })
        addView(tvMonitor)
    }
    
    // [UI Fix] 3. 布局: Value 上, Label 下
    private fun createKVBlock(label: String, valueView: TextView): LinearLayout {
        return LinearLayout(context).apply {
            orientation = VERTICAL
            gravity = Gravity.CENTER_HORIZONTAL
            addView(valueView)
            addView(TextView(context).apply { text = label; textSize = 10f; setTextColor(Color.GRAY); typeface = Typeface.DEFAULT_BOLD })
        }
    }
    
    // Helper for rounded bg
    private fun getRoundedBg(color: Int, radius: Float): GradientDrawable {
        return GradientDrawable().apply { setColor(color); cornerRadius = radius }
    }

    fun update(force: Float, stroke: Float, state: String, power: Float, rawCount: Int, 
               temp: Int, errorCode: Int, absPos: Float, speed: Float) { 
        tvForce.text = "%.1f".format(force)
        tvStroke.text = "%.0f".format(stroke) // CM整数显示更整洁
        tvPower.text = "${power.toInt()}"
        tvSpeed.text = "%.2f".format(speed / 100f)
        tvState.text = state
        tvRawCount.text = "$rawCount"

        // Status Monitoring Logic
        if (errorCode > 0) {
             tvMonitor.setTextColor(Color.RED)
             tvMonitor.text = "警告: 错误码 E$errorCode | 温度 ${temp}℃"
        } else {
             tvMonitor.setTextColor(Color.GRAY)
             tvMonitor.text = "设备: 正常 | 温度 ${temp}℃ | 绝对位置 ${absPos.toInt()}"
        }
    }
}

class UserStatePanel(context: Context) : LinearLayout(context) {
    private val tvTitle = TextView(context).apply { text = "用户行为识别"; textSize = 12f; setTextColor(Color.GRAY); gravity = Gravity.CENTER; typeface = Typeface.DEFAULT_BOLD } // KE-ZL-202309-0
    private val tvState = TextView(context).apply { textSize = 40f; typeface = Typeface.DEFAULT_BOLD; setTextColor(Color.YELLOW); gravity = Gravity.CENTER; text = "准备中" } // KE-ZL-202309-0
    private val tvLog = TextView(context).apply { textSize = 14f; setTextColor(Color.LTGRAY); gravity = Gravity.CENTER; maxLines = 2; text = "等待开始..." } // KE-ZL-202309-0

    init {
        orientation = VERTICAL
        background = GradientDrawable().apply { setColor(0xAA333333.toInt()); cornerRadius = 16f }
        setPadding(16, 24, 16, 24) // KE-ZL-202309-0
        addView(tvTitle)
        addView(tvLog)
        addView(tvState) // KE-ZL-202309-0
    }

    fun update(state: String, stroke: Float, event: String) { // KE-ZL-202309-0
        tvState.text = state
        if (event.isNotEmpty()) tvLog.text = event // KE-ZL-202309-0
        tvState.setTextColor(when {
            state.contains(UserStateProcessor.UserState.PEAK.cnName) -> Color.RED
            state.contains(UserStateProcessor.UserState.CONCENTRIC.cnName) -> Color.CYAN
            state.contains(UserStateProcessor.UserState.ECCENTRIC.cnName) -> Color.MAGENTA
            else -> Color.YELLOW
        })
    }
}

class RealtimeCurveView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : View(context, attrs) {
    private val paint1 = Paint().apply { color = "#00BCD4".toColorInt(); strokeWidth = 3f; style = Paint.Style.STROKE; isAntiAlias = true } // KE-ZL-202309-0
    private val paint2 = Paint().apply { color = "#E040FB".toColorInt(); strokeWidth = 3f; style = Paint.Style.STROKE; isAntiAlias = true }
    // [性能优化] UI线程单线程访问，使用 ArrayDeque 替代 ConcurrentLinkedQueue 避免 size() O(N) 开销
    private val points1 = java.util.ArrayDeque<Float>(120) // Full qualification not needed if imported, but removing import to solve unused warning
    private val points2 = java.util.ArrayDeque<Float>(120)
    private val maxPoints = 100 // 限制点数，优化绘图性能
    private val path = Path() 

    fun addPoint(f1: Float, f2: Float) {
        // [Concurrent Fix] Synchronize access since this comes from IO Thread
        synchronized(this) {
            // Efficiently manage queue size
            if (points1.size >= maxPoints) points1.removeFirst()
            if (points2.size >= maxPoints) points2.removeFirst()
            
            points1.add(f1)
            points2.add(f2)
        }
        // Safe to call from background thread
        postInvalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor("#181818".toColorInt())
        
        // [Concurrent Fix] Synchronize access during draw
        synchronized(this) {
            if (points1.isEmpty()) return

            // Auto-scale height (Fast iteration inside sync block)
            val max1 = points1.maxOrNull() ?: 1f
            val max2 = points2.maxOrNull() ?: 1f
            val globalMax = max(max(max1, max2), 10f) // Minimum 10kg scale

            val w = width.toFloat()
            val h = height.toFloat()
            val step = w / maxPoints

            drawPath(canvas, points1, paint1, step, h, globalMax)
            drawPath(canvas, points2, paint2, step, h, globalMax)
            
            // Draw max value text
            paint1.style = Paint.Style.FILL
            paint1.textSize = 24f
            canvas.drawText("Max: ${globalMax.toInt()}kg", 10f, 30f, paint1)
            paint1.style = Paint.Style.STROKE
        }
    }

    private fun drawPath(c: Canvas, q: Collection<Float>, p: Paint, s: Float, h: Float, maxVal: Float) {
        path.reset() // [性能优化] 重置而非新建
        var x = 0f
        var first = true
        // [Fix] 终极方案：使用显式 Iterator + while 循环，彻底规避任何 Lambda 变量捕获或闭包问题
        val iterator = q.iterator()
        while (iterator.hasNext()) {
            val v = iterator.next()
            val y = h - (v / maxVal * h)
            if (first) { path.moveTo(x, y); first = false } else path.lineTo(x, y)
            x += s
        }
        c.drawPath(path, p)
    }
}

class RealtimeBarView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : View(context, attrs) {
    // 移除 alpha 设置，直接使用带透明度的颜色值，避免 layer 合成开销 // KE-ZL-202309-0
    private val paint1 = Paint().apply { color = 0xB000BCD4.toInt(); style = Paint.Style.FILL } // KE-ZL-202309-0
    private val paint2 = Paint().apply { color = 0xB0E040FB.toInt(); style = Paint.Style.FILL } // KE-ZL-202309-0
    private val points1 = java.util.ArrayDeque<Float>(60)
    private val points2 = java.util.ArrayDeque<Float>(60)
    private val maxPoints = 50 // 减少柱状图数量，进一步降低开销 // KE-ZL-202309-0

    fun addPoint(power1: Float, power2: Float) {
        // [Concurrent Fix] Synchronize access
        synchronized(this) {
            if (points1.size >= maxPoints) points1.removeFirst()
            if (points2.size >= maxPoints) points2.removeFirst()
            points1.add(power1)
            points2.add(power2)
        }
        postInvalidate()
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        canvas.drawColor("#181818".toColorInt())
        
        // [Concurrent Fix] Synchronize access
        synchronized(this) {
            if (points1.isEmpty()) return

            val h = height.toFloat()
            val w = width.toFloat()
            val step = w / maxPoints // KE-ZL-202309-0
            val barWidth = step * 0.4f
            val maxP = 600f // Max 600W fixed scale for power to see variations better

            var x = 0f
            val p1Iter = points1.iterator()
            val p2Iter = points2.iterator()
            
            while(p1Iter.hasNext() && p2Iter.hasNext()) {
                val v1 = p1Iter.next()
                val v2 = p2Iter.next()
                
                val h1 = (v1 / maxP) * h
                val h2 = (v2 / maxP) * h
                
                // Draw side-by-side bars scrolling
                canvas.drawRect(x, h - h1, x + barWidth, h, paint1)
                canvas.drawRect(x + barWidth, h - h2, x + 2*barWidth, h, paint2)
                
                x += step
            }
        }
    }
}

// ===================================================================================
// 环形调力盘组件 (CircularForceKnobView)
// ===================================================================================
class CircularForceKnobView @JvmOverloads constructor(
    context: Context, attrs: AttributeSet? = null
) : View(context, attrs) {
    
    private val minWeight = 2.5f
    private val maxWeight = 50.0f
    private var currentWeight = 2.5f
    private var isActive = false
    
    private val paintArc = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.STROKE; strokeCap = Paint.Cap.ROUND }
    private val paintThumb = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL; color = Color.WHITE }
    private val paintTextVal = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER; color = Color.WHITE; typeface = Typeface.DEFAULT_BOLD }
    private val paintTextLabel = Paint(Paint.ANTI_ALIAS_FLAG).apply { textAlign = Paint.Align.CENTER; color = Color.GRAY; textSize = 24f }
    private val paintBtn = Paint(Paint.ANTI_ALIAS_FLAG).apply { style = Paint.Style.FILL }

    private var onValueChanged: ((Float) -> Unit)? = null
    private var onCenterClick: (() -> Unit)? = null
    
    // 3/4 Circle: Start 135, Sweep 270. (Bottom opening)
    private val startAngle = 135f
    private val sweepAngle = 270f

    fun setOnValueChangedListener(l: (Float) -> Unit) { onValueChanged = l }
    fun setOnCenterClickListener(l: () -> Unit) { onCenterClick = l }
    
    fun setActiveState(active: Boolean) {
        isActive = active
        invalidate()
    }
    // [UI Fix] 5. 移除呼吸动效逻辑

    override fun onTouchEvent(event: MotionEvent): Boolean {
        val cx = width / 2f
        val cy = height / 2f
        
        // Check center click (Radius < 30% width)
        val dx = event.x - cx
        val dy = event.y - cy
        val dist = Math.sqrt((dx*dx + dy*dy).toDouble())
        
        if (dist < width * 0.25f) {
            if (event.action == MotionEvent.ACTION_UP) {
                onCenterClick?.invoke()
            }
            return true
        }
        
        // Knob Drag logic
        if (event.action == MotionEvent.ACTION_MOVE || event.action == MotionEvent.ACTION_DOWN) {
            var angle = Math.toDegrees(atan2(dy.toDouble(), dx.toDouble())).toFloat()
            angle = (angle + 360) % 360
            // Map angle to progress 0-1
            // 135 deg -> 0, 45 deg (405) -> 1
            // Normalize to start at 135
            var relativeAngle = angle - 135
            if (relativeAngle < 0) relativeAngle += 360
            
            if (relativeAngle <= sweepAngle) {
                val progress = relativeAngle / sweepAngle
                // Step 0.5kg
                val rawVal = minWeight + progress * (maxWeight - minWeight)
                val steppedVal = Math.round(rawVal * 2) / 2.0f
                if (steppedVal != currentWeight) {
                    currentWeight = steppedVal
                    onValueChanged?.invoke(currentWeight)
                    invalidate()
                }
            }
        }
        return true
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        val w = width.toFloat()
        val h = height.toFloat()
        val cx = w / 2
        val cy = h / 2
        // 移除动效偏移
        val radius = (Math.min(w, h) / 2 * 0.85f)
        
        // 1. Background Arc
        paintArc.strokeWidth = 30f
        paintArc.color = 0xFF2A2A2A.toInt()
        canvas.drawArc(cx - radius, cy - radius, cx + radius, cy + radius, startAngle, sweepAngle, false, paintArc)
        
        // 2. Active Arc
        paintArc.color = if (isActive) 0xFF00C853.toInt() else 0xFF00BCD4.toInt()
        val progress = (currentWeight - minWeight) / (maxWeight - minWeight)
        canvas.drawArc(cx - radius, cy - radius, cx + radius, cy + radius, startAngle, sweepAngle * progress, false, paintArc)
        
        // 3. Thumb
        val thumbAngle = Math.toRadians((startAngle + sweepAngle * progress).toDouble())
        val tx = cx + radius * cos(thumbAngle).toFloat()
        val ty = cy + radius * sin(thumbAngle).toFloat()
        canvas.drawCircle(tx, ty, 20f, paintThumb)
        
        // 4. Center Info
        paintTextVal.textSize = 64f
        // [UI Polish] 对齐微调
        canvas.drawText("${currentWeight}", cx, cy - 20, paintTextVal)
        paintTextLabel.textSize = 24f
        canvas.drawText("KG / ${maxWeight.toInt()}", cx, cy + 20, paintTextLabel)
        
        // 5. Button State Text
        val btnText = if (isActive) "已激活" else "待机"
        val btnColor = if (isActive) 0xFF00C853.toInt() else 0xFF555555.toInt()
        paintBtn.color = btnColor
        // Draw a rounded rect pill for button look below text
        val btnRectW = 160f
        val btnRectH = 50f
        val btnY = cy + 60f
        canvas.drawRoundRect(cx - btnRectW/2, btnY, cx + btnRectW/2, btnY + btnRectH, 25f, 25f, paintBtn)
        
        paintTextLabel.color = Color.WHITE
        paintTextLabel.textSize = 24f
        canvas.drawText(btnText, cx, btnY + 35, paintTextLabel)
    }
}
