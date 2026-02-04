from exercises.generic import GenericExercise

class PressExerciseConfig(GenericExercise):
    """
    推举 (配置版)
    完全复用 GenericExercise 引擎，逻辑定义在 '推举.json' 中。
    """
    def __init__(self, sound_mgr):
        # 指定配置文件名为 '推举.json'
        super().__init__(sound_mgr, config_file="推举.json")