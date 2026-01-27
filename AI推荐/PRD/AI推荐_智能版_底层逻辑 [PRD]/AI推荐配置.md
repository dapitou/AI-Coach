# AI推荐配置
> **定义**：AI推荐引擎的参数化配置中心，采用分层架构设计，支持运营动态下发。
> **架构**：基础字典 -> 宏观规划 -> 中观课程 -> 微观适配 -> 推荐算法

## 目录索引
*   **0. 基础字典定义**
    *   [0.1 通用枚举字典](#01-通用枚举字典)
*   **一、 宏观规划配置 (Macro Planning)**
    *   1.1 阶段周期分配配置
    *   1.2 计划阶段模板配置
*   **二、 中观课程配置 (Meso Course Design)**
    *   2.1 训练范式配置
    *   2.2 策略矩阵配置
    *   2.3 课程环节模板配置
*   **三、 微观适配配置 (Micro Adaptation)**
    *   3.1 等级强度系数配置
    *   3.2 难度兼容策略配置
    *   3.3 状态适配配置
*   **四、 推荐算法配置 (Recommendation Algorithm)**
    *   4.1 推荐影响因子配置

## 0. 基础字典定义 (Data Dictionary)
> **作用**：定义全系统通用的枚举常量，确保配置项的关联一致性，消除魔法字符串。

### 0.1 通用枚举字典
| 字典域 (Domain) | 枚举键 (Key) | 枚举值 (Values) | 说明 |
| :--- | :--- | :--- | :--- |
| **Level (等级)** | `L1`...`L5` | 入门, 初级, 中级, 进阶, 专业 | 用户运动能力分级 |
| **Goal (目标)** | `HYP`, `STR`, `END`, `FAT`, `POW`... | 增肌, 力量, 耐力, 减脂, 爆发 | 训练生理目标 |
| **Dim (维度)** | `PART`, `MODE`, `FUNC`, `CONS` | 部位, 动作模式, 动作功能, 动作构造 | 动作筛选维度 |
| **Metric (指标)** | `LAST_TRAIN`, `IS_FAV`, `HISTORY_COUNT`, `FATIGUE` | 距今天数, 收藏状态, 历史次数, 疲劳度 | 推荐判定指标 |
| **Op (算子)** | `GT`, `LT`, `EQ`, `GTE`, `LTE` | >, <, ==, >=, <= | 逻辑比较算子 |

## 一、 宏观规划配置 (Macro Planning)
> **作用**：定义计划的时间跨度、阶段划分与周排课骨架。

### 1.1 阶段周期分配配置 [原2.2]
> **定义**：定义计划各阶段的时长比例与裁剪逻辑。
> **用途**：确保不同周期的计划（如4周 vs 12周）都能包含合理的训练阶段（适应/进阶/突破/减载）。

| 计划周期 (周) | 阶段结构 (Phase Sequence) | 分配策略 (Allocation) | 说明 |
| :--- | :--- | :--- | :--- |
| **1** | `[ADV]` | `[1.0]` | 快速体验 (进阶期) |
| **2** | `[ADP, ADV]` | `[0.5, 0.5]` | 简易周期 (适应->进阶) |
| **3** | `[ADP, ADV, BRK]` | `[0.33, 0.33, 0.33]` | 完整进阶 (适应->进阶->突破) |
| **4 (标准)** | `[ADP, ADV, BRK, DEL]` | `[0.25, 0.25, 0.25, 0.25]` | 标准线性周期 |
| **> 4** | `[ADP, ADV, BRK, DEL]` | `[0.25, 0.40, 0.25, 0.10]` | 长周期规划 |

### 1.2 计划阶段模板配置 [原1.4]
> **定义**：定义计划中每个阶段的周排课模式（如“推拉腿”、“上下肢分化”）。
> **用途**：作为计划生成的骨架，决定每周练什么。
> **关联**：`基础槽位` -> 关联 `[2.3 课程环节模板]` 的 `Template Key`。

| ID | 名称 | 目标 (Goal) | 难度 (Level) | 适用性别 | 周频 | 基础槽位 (Template Keys) | 补充策略 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TPL_001** | 一分化 (全身) | `HYP` | `All` | `All` | 1 | `[FULL_BODY]` | 循环 |
| **TPL_002** | 二分化 (上下肢) | `HYP` | `All` | `All` | 2 | `[UPPER, LOWER]` | 循环 |
| **TPL_003** | 三分化 (推拉腿) | `HYP` | `All` | `Male` | 3 | `[PUSH, PULL, LEGS]` | 循环 |
| **TPL_004** | 三分化 (臀腿侧重) | `HYP` | `All` | `Female` | 3 | `[GLUTE, UPPER, GLUTE]` | 循环 |
| **TPL_005** | 四分化 (非线性) | `HYP` | `All` | `All` | 4 | `[UPPER, LOWER, UPPER, LOWER]` | 循环 |
| **TPL_006** | 五分化 (单部位) | `HYP` | `All` | `Male` | 5 | `[CHEST, BACK, SHOULDER, LEGS, ARM]` | 循环 |
| **TPL_007** | 减脂循环 | `FAT` | `L1` | `All` | 3 | `[HIIT_FAT, FAT_BURN, CORE]` | 循环 |

## 二、 中观课程配置 (Meso Course Design)
> **作用**：定义单次课程的物理规则、基准参数与内容结构。

### 2.1 训练范式配置 [原1.5]
> **定义**：定义不同课程类型的底层逻辑范式（如力量课关注组数，瑜伽课关注流式体验）。
> **用途**：作为顶层分流逻辑，决定环节参数的默认值和动作排序逻辑。

#### A. 范式映射
| 训练范式 | 包含课程类型 (Course Types) | 目标部位约束 | 核心特征 |
| :--- | :--- | :--- | :--- |
| **抗阻范式** | `STR`, `REHAB`, `GOLF` | 可选任意部位 | 关注负荷，组间休息充分，强调动作质量 |
| **间歇范式** | `HIIT`, `CARDIO`, `BOXING` | 锁定 `[FULL]` | 关注心率/工休比，高密度循环，强调代谢压力 |
| **流式范式** | `YOGA`, `PILATES`, `STRETCH` | 可选任意部位 | 关注体位流动，无间歇/少间歇，强调呼吸与控制 |

#### B. 范式默认参数
| 训练范式 | 循环模式 | 负荷策略 | 休息配置 | 强制组数 |
| :--- | :--- | :--- | :--- | :--- |
| **抗阻范式** | 常规组 | 推荐 | True | - |
| **间歇范式** | 循环组 | 计时 | True | - |
| **流式范式** | 常规组 | 计时 | False | 1 |

### 2.2 策略矩阵配置 [原1.1]
> **定义**：定义不同目标下的基准训练参数（如组数、休息、强度）。
> **用途**：作为生成课程时的核心参数基准，后续会根据用户等级进行系数缩放。
> **映射**：`Goal` -> `[计划属性].计划功能目标`

| 目标 (Goal) | 动作组数 | 动作间歇(s) | 训练强度 | 循环模式 | 负荷策略 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **HYP (增肌)** | 4 | 90 | 0.75 | 常规组 | 递增 |
| **STR (力量)** | 5 | 120 | 0.85 | 常规组 | 恒定 |
| **FAT (减脂)** | 4 | 30 | 0.65 | 循环组 | 计时 |
| **END (耐力)** | 4 | 30 | 0.50 | 超级组 | 计时 |
| **POW (爆发)** | 4 | 150 | 0.70 | 常规组 | 递增 |
| **CARDIO (心肺)** | 4 | 20 | 0.65 | 循环组 | 计时 |
| **HIIT** | 6 | 30 | 0.75 | 循环组 | 计时 |
| **AEROBIC (有氧)** | 4 | 15 | 0.60 | 循环组 | 计时 |
| **YOGA** | 1 | 0 | 0.40 | 常规组 | 计时 |
| **PILATES** | 3 | 30 | 0.50 | 常规组 | 恒定 |
| **STRETCH (拉伸)** | 1 | 0 | 0.20 | 常规组 | 计时 |
| **RECOVERY (恢复)** | 2 | 0 | 0.30 | 常规组 | 恒定 |
| **FLEX (柔韧)** | 2 | 0 | 0.30 | 常规组 | 计时 |
| **COORD (协调)** | 3 | 60 | 0.50 | 常规组 | 恒定 |
| **POSTURE (体态)** | 3 | 45 | 0.50 | 常规组 | 计时 |
| **ACTIVATE (激活)** | 2 | 0 | 0.40 | 常规组 | 恒定 |
| **BALANCE (平衡)** | 3 | 60 | 0.50 | 常规组 | 恒定 |
| **SPEC (专项)** | 3 | 90 | 0.70 | 常规组 | 推荐 |

### 2.3 课程环节模板配置 [原1.2]
> **定义**：定义单节课的“配方”，即动作槽位的构成与比例。
> **用途**：决定课程内容的结构（如：练胸日 = 40%水平推 + 40%垂直推 + 20%三头肌）。
> **逻辑**：采用**多维向量最佳匹配**。系统根据 `Key` + `Level` + `Gender` + `Goal` 寻找得分最高的模板。
> **槽位语法**：`Dim:Target@Weight` (例如 `MODE:PUSH_H@0.4` 表示 动作模式:水平推 权重0.4)

| 模板键 (Key) | 适用等级 | 适用性别 | 适用目标 | 动作槽位配置 (Slot Schema) |
| :--- | :--- | :--- | :--- | :--- |
| **FULL_BODY** | All | All | All | `CONS:COMPOUND@0.6`, `CONS:ISOLATE@0.4` |

| **[策略维度 - 推拉腿分化]** |  |  |  |  |
| **PUSH** | All | All | All | `MODE:PUSH_H@0.4`, `MODE:PUSH_V@0.4`, `MUSCLE:TRICEPS@0.2` |
| **PULL** | All | All | All | `MODE:PULL_V@0.4`, `MODE:PULL_H@0.4`, `MUSCLE:BICEPS@0.2` |
| **LEGS** | All | All | All | `MODE:SQUAT@0.4`, `MODE:HINGE@0.4`, `MUSCLE:CALVES@0.1`, `PART:CORE@0.1` |

| **[策略维度 - 上下肢分化]** |  |  |  |  |
| **UPPER** | All | All | All | `MODE:PUSH_H@0.2`, `MODE:PUSH_V@0.2`, `MODE:PULL_H@0.2`, `MODE:PULL_V@0.2`, `PART:ARM@0.2` |
| **LOWER** | All | All | All | `MODE:SQUAT@0.4`, `MODE:HINGE@0.4`, `MODE:LUNGE@0.1`, `PART:CORE@0.1` |

| **[解剖维度 - 部位训练]** |  |  |  |  |
| **CHEST** | L1,L2 | All | All | `MUSCLE:PEC_MID@0.4`, `MUSCLE:PEC_UPPER@0.4`, `MUSCLE:PEC_LOWER@0.1`, `MUSCLE:PEC_INNER@0.1` |
| **CHEST** | L3-L5 | All | All | `MODE:PUSH_H@0.6`, `MODE:FLY@0.2`, `MUSCLE:TRICEPS@0.2` |
| **GLUTE** | All | Female | All | `MODE:HINGE@0.5`, `MODE:LUNGE@0.3`, `MUSCLE:GLUTE_MED@0.2` |
| **GLUTE** | All | Male | All | `MUSCLE:GLUTE_MAX@0.65`, `MUSCLE:GLUTE_MED@0.35` |
| **BACK** | L1,L2 | All | All | `MUSCLE:LATS@0.4`, `MUSCLE:TRAPS@0.4`, `MUSCLE:ERECTOR@0.2` |
| **BACK** | L3-L5 | All | All | `MODE:PULL_V@0.5`, `MODE:PULL_H@0.3`, `MUSCLE:BICEPS@0.2` |
| **SHOULDER** | L1,L2 | All | All | `MUSCLE:DELT_MID@0.5`, `MUSCLE:DELT_FRONT@0.3`, `MUSCLE:DELT_REAR@0.2` |
| **SHOULDER** | L3-L5 | All | All | `MODE:PUSH_V@0.4`, `MUSCLE:DELT_MID@0.4`, `MUSCLE:DELT_REAR@0.2` |
| **ARM** | L1,L2 | All | All | `CONS:ISOLATE@0.8`, `CONS:COMPOUND@0.2` |
| **ARM** | L3-L5 | All | All | `MUSCLE:TRICEPS@0.6`, `MUSCLE:BICEPS@0.4` |
| **LEGS** | L1,L2 | All | All | `CONS:MACHINE@0.5`, `MODE:SQUAT@0.3`, `MODE:HINGE@0.2` |
| **LEGS** | L3-L5 | All | All | `MUSCLE:QUADS@0.4`, `MUSCLE:HAMS@0.4`, `MUSCLE:ADDUCTOR@0.1`, `MUSCLE:CALVES@0.1` |
| **CORE** | L1,L2 | All | All | `MODE:CORE_STABLE@0.6`, `MODE:ROTATION@0.4` |
| **CORE** | L3-L5 | All | All | `MUSCLE:ABS_RECT@0.7`, `MUSCLE:ABS_OBLIQUE@0.3` |

| **[目标维度 - 功能训练]** |  |  |  |  |
| **FAT_BURN** | All | All | All | `FUNC:CARDIO@0.6`, `CONS:COMPOUND@0.2`, `MODE:CORE_STABLE@0.2` |
| **HIIT_FAT** | All | All | All | `FUNC:POWER@0.4`, `FUNC:CARDIO@0.4`, `MODE:CORE_STABLE@0.2` |
| **FLEX** | All | All | All | `FUNC:FLEX@0.8`, `FUNC:POSTURE@0.2` |
| **BALANCE** | All | All | All | `FUNC:BALANCE@0.5`, `MODE:CORE_STABLE@0.3`, `FUNC:COORD@0.2` |
| **CORE_ACT** | All | All | All | `FUNC:ACTIVATE@0.6`, `MODE:CORE_STABLE@0.4` |
| **ACTIVATE** | All | All | All | `FUNC:ACTIVATE@0.6`, `FUNC:BALANCE@0.2`, `FUNC:COORD@0.2` |
| **RECOVERY** | All | All | All | `FUNC:RECOVERY@0.5`, `FUNC:FLEX@0.3`, `FUNC:ACTIVATE@0.2` |
| **POSTURE** | All | All | All | `FUNC:POSTURE@0.6`, `FUNC:FLEX@0.2`, `MODE:CORE_STABLE@0.2` |

| **[混合维度 - 目标 + 部位]** |  |  |  |  |
| **SHOULDER** | L3,L4 | All | `STR` | `MODE:PUSH_V@0.6`, `MODE:PUSH_H@0.2`, `MUSCLE:DELT_REAR@0.2` |
| **LEGS** | L3-L5 | All | `POW` | `MODE:SQUAT@0.5`, `FUNC:POWER@0.3`, `MUSCLE:GLUTE_MAX@0.2` |

| **[通用]** |  |  |  |  |
| **FULL_BODY** | All | All | All | `CONS:COMPOUND@0.6`, `CONS:ISOLATE@0.4` | 默认全身训练 |

## 三、 微观适配配置 (Micro Adaptation)
> **作用**：根据用户个体差异（等级、状态）对基准参数进行动态修正。

### 3.1 等级强度系数配置 [原1.3]
> **定义**：根据用户运动等级设定的负荷缩放系数。
> **用途**：基于 [2.2 策略矩阵] 的基准值，针对不同等级用户进行差异化调整。
> **公式**：`最终值` = `基准值` * `系数`。

| 运动等级 | 等级系数 | 说明 |
| :--- | :--- | :--- |
| **L1 (入门)** | 0.5 | 需降低门槛，建立信心 |
| **L2 (初级)** | 0.8 | 低于标准，关注动作质量 |
| **L3 (中级)** | 1.0 | 标准负荷 |
| **L4 (进阶)** | 1.2 | 增加负荷挑战 |
| **L5 (专业)** | 1.5 | 接近极限 |

### 3.2 难度兼容策略配置 [原2.1]
> **定义**：定义动作筛选时的难度兼容范围与高斯分布概率。
> **用途**：决定不同等级用户在筛选动作时，是倾向于保守（选低难度）还是挑战（选高难度）。

| 策略名称 [键] | 范围偏移 | 概率分布 [偏移: 权重] | 说明 |
| :--- | :--- | :--- | :--- |
| **CONSERVATIVE** (L1) | `[0, 2]` | `{0: 0.6, 1: 0.3, 2: 0.1}` | 同级60%, 进阶30%, 挑战10% |
| **STANDARD** (L2/3) | `[-1, 1]` | `{0: 0.6, -1: 0.2, 1: 0.2}` | 同级60%, 降级20%, 升级20% |
| **ADVANCED** (L4) | `[-1, 1]` | `{0: 0.4, -1: 0.3, 1: 0.3}` | 同级40%, 降级30%, 升级30% |
| **CHALLENGE** (L5) | `[-2, 0]` | `{0: 0.3, -1: 0.4, -2: 0.3}` | 同级30%, 降级40%, 基础30% |

### 3.3 状态适配配置 [原4.1]
> **定义**：根据用户实时状态（如疲劳度）调整训练参数的规则。
> **用途**：防止过度训练，提供人性化的负荷调整与禁忌规避。

#### A. 疲劳干预
> **来源**：`[状态数据].综合疲劳度` (100=状态极佳, 0=力竭)

| 状态值区间 | 标签 | 强度系数 | 容量系数 | 强制约束 |
| :--- | :--- | :--- | :--- | :--- |
| **[85, 100]** | 已恢复 | 1.0 | 1.0 | - |
| **[55, 84]** | 恢复中 | 0.9 | 1.0 | - |
| **[30, 54]** | 疲劳中 | 0.8 | 0.8 | 剔除高冲击 |
| **[0, 29]** | 已力竭 | - | - | 推荐切换为“主动恢复”课程 |

## 四、 推荐算法配置 (Recommendation Algorithm)
> **作用**：定义动作筛选、打分与组装的逻辑。

### 4.1 推荐影响因子配置 [原3.1]
> **定义**：定义动作推荐的打分规则（奖惩权重）。
> **用途**：决定哪些动作优先推荐（如新鲜的、收藏的），哪些动作被降权（如厌恶的、疲劳的）。

| 分类 | 因子键 (Factor Key) | 权重 (Weight) | 判定指标 (Metric) | 算子 (Op) | 阈值 (Value) |
| :--- | :--- | :--- | :--- |
| **偏好** | `FAV_REWARD` | +50 | `IS_FAV` | `EQ` | `TRUE` |
| **行为** | `FRESH_REWARD` | +40 | `LAST_TRAIN_GAP` | `GT` | `7` (Day) |
| **行为** | `EXPLORE_REWARD` | +30 | `HISTORY_COUNT` | `EQ` | `0` |
| **行为** | `BORED_PENALTY` | -80 | `CONSECUTIVE_USE` | `GTE` | `3` |
| **行为** | `REPLACE_PENALTY` | -50 | `LAST_REPLACE_GAP` | `LTE` | `30` (Day) |
| **行为** | `DELETE_PENALTY` | -100 | `LAST_DELETE_GAP` | `LTE` | `30` (Day) |
| **激励** | `CONFIDENCE_REWARD` | +20 | `ABSENCE_DAYS` | `GT` | `7` (Day) |
| **状态** | `FATIGUE_PENALTY` | -50 | `MUSCLE_FATIGUE` | `LT` | `55` |

## 需求池
> > *业务导读：未来版本规划的配置项。*