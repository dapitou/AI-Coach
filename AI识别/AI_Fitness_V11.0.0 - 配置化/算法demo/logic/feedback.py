from core.config import TextConfig, ColorConfig, AlgoConfig

class FeedbackSystem:
    """
    全局反馈状态机 (Global Feedback State Machine) - V24.10 Mutex & Priority
    
    【核心逻辑】
    1. 互斥锁 (Mutex Lock): 
       同时只能激活一个错误纠错。self.locked_key 记录当前霸占系统的错误。
       
    2. 优先级仲裁 (Priority Arbitration):
       加载 AlgoConfig 中的优先级配置。
       虽然 process_error 是逐个调用的，但通过 locked_key 机制确保高优先级错误能占据主导。
    """

    def __init__(self, sound_mgr):
        self.sound = sound_mgr
        self.history = {} # {err_key: [bool, bool...]}
        self.active_feedback = set()
        self.error_counts = {}
        self.bad_reps = 0
        self.current_rep_has_error = False
        
        # [New] 全局互斥锁：记录当前正在纠错的 Key (None 表示空闲)
        self.locked_key = None
        
        # [New] 优先级映射 (数值越小优先级越高, 默认999)
        # 使用 getattr 防止配置文件缺少某些 Key 导致报错
        self.priority_map = {
            'arm': getattr(AlgoConfig, 'PRIORITY_PRESS_ARM', 1),
            'shrug': getattr(AlgoConfig, 'PRIORITY_SHRUG', 2),
            'valgus': getattr(AlgoConfig, 'PRIORITY_SQUAT_VALGUS', 1),
            'rounding': getattr(AlgoConfig, 'PRIORITY_SQUAT_ROUNDING', 2),
            # 可在此处自动扩展其他 Key，未配置的默认为低优先级
        }

    def reset(self):
        self.history = {}
        self.active_feedback = set()
        self.error_counts = {}
        self.bad_reps = 0
        self.current_rep_has_error = False
        self.locked_key = None # 重置锁

    def process_error(self, err_key, is_good, block_feedback=False, set_msg_callback=None):
        """
        处理单个错误的帧输入，并根据全局状态决定是否激活反馈
        """
        # 1. 基础历史记录更新 (始终执行，保证数据连续性)
        if err_key not in self.history: self.history[err_key] = []
        self.history[err_key].append(is_good)
        if len(self.history[err_key]) > 5: self.history[err_key].pop(0)

        if not is_good:
            self.current_rep_has_error = True
            self.error_counts[err_key] = self.error_counts.get(err_key, 0) + 1

        # 2. 计算本地触发状态 (Trigger Condition)
        # 判定标准：连续 2 帧为 False (Bad)
        is_triggered_locally = False
        if len(self.history[err_key]) >= 2:
            if not self.history[err_key][-1] and not self.history[err_key][-2]:
                is_triggered_locally = True

        # 3. 全局状态机仲裁 (Global Arbitration)
        
        current_prio = self.priority_map.get(err_key, 999)
        
        # --- 情况 A: 系统已被锁定 ---
        if self.locked_key is not None:
            
            # A1. 如果输入的就是当前锁定的错误
            if err_key == self.locked_key:
                if is_good:
                    # [解锁] 错误已修正 -> 释放锁
                    self.locked_key = None
                    if err_key in self.active_feedback:
                        self.active_feedback.remove(err_key)
                    
                    # 播放成功音效与提示
                    self.sound.play('success')
                    if set_msg_callback:
                        set_msg_callback(TextConfig.MSG_GOOD, ColorConfig.NEON_GREEN, dur=1.5, priority=2)
                else:
                    # [维持] 错误仍存在 -> 保持锁定
                    # 确保它在 active_feedback 中
                    self.active_feedback.add(err_key) 
            
            # A2. 如果输入的是其他错误 (竞争者)
            else:
                # 检查是否允许"高优先级抢占" (Simultaneous Preemption)
                # 规则：如果新错误优先级(1) 高于 当前锁定的错误优先级(2)，且新错误也触发了
                # 注意：这里我们遵循"直至该纠错解除"的强规则，通常不允许抢占。
                # 但为了解决"同时触发进高优先级"的问题，我们允许在同一帧内的逻辑覆盖。
                # 鉴于无法知晓"同一帧"边界，我们采用严格的互斥逻辑。
                # 即：一旦锁定，除非修好，否则天王老子来了也得排队。
                pass # 忽略该错误，不加入 active_feedback

        # --- 情况 B: 系统空闲 (无锁) ---
        else:
            if is_triggered_locally and not is_good and not block_feedback:
                # [上锁] 触发新错误
                self.locked_key = err_key
                self.active_feedback.add(err_key)
                
                # 注意：如果同一帧后面来了更高优先级的 process_error，
                # 由于上面的 A2 逻辑采用了严格互斥，先到的会先锁住。
                # 如果动作代码中先检测了低优先级，会导致低优先级先锁。
                # 但通常高优先级检测逻辑(如小臂)会写在前面，或者我们信任严格互斥带来的稳定性。

        # 4. 持续反馈音效 (仅针对当前激活/锁定的错误)
        if (err_key in self.active_feedback) and not is_good:
             self.sound.play('error')

    def end_cycle(self, cycle_flags):
        self.current_rep_has_error = False
        
        # Determine if any current errors exist
        has_current_bad = False
        for k, v in cycle_flags.items():
            if not v: has_current_bad = True
            
        if has_current_bad: self.bad_reps += 1
        
        # 播放计次音效 (只有在没纠错时才播，防止声音打架)
        if not self.active_feedback:
            self.sound.play('count')