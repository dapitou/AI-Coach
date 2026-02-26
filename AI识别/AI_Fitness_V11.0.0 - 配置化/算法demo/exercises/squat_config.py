from exercises.generic import GenericExercise

class SquatExerciseConfig(GenericExercise):
    """
    深蹲 (配置版)
    逻辑已完全解耦至 GenericExercise，此处仅指定配置文件。
    """
    def __init__(self, sound_mgr):
        # 核心：只需指定配置文件名，所有逻辑由父类 GenericExercise 接管
        super().__init__(sound_mgr, config_file="深蹲.json")