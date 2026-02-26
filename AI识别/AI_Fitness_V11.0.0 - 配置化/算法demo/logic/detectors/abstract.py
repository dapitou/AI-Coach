from abc import ABC, abstractmethod

class BaseDetector(ABC):
    def __init__(self, error_key, msg, color, priority=1):
        """
        :param error_key: 错误统计的唯一Key (如 'shrug')
        :param msg: 错误提示文本
        :param color: 提示文本/特效颜色
        :param priority: 消息优先级
        """
        self.error_key = error_key
        self.msg = msg
        self.color = color
        self.priority = priority

    @abstractmethod
    def detect(self, pts, shared_data, cycle_flags):
        """
        执行检测
        :param pts: 关键点字典
        :param shared_data: 共享数据 (如 spine_len, base_shrug_dist)
        :param cycle_flags: 当前动作循环的状态字典 (用于记录本轮动作是否达标)
        :return: visuals (list of dict) - 需要绘制的特效指令列表
        """
        pass