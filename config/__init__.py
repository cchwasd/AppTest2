import platform


class AppConfig:
    """应用配置类，用于存储应用的各种配置项。"""
    system_type = None # 初始化类属性，用于存储系统类型

    def __init__(self, custom_config=None):
        self.custom_config = custom_config
        AppConfig.system_type = AppConfig.get_system_type()
    @classmethod
    def get_system_type(cls):
        # 判断系统类型是否已获取
        if cls.system_type is None:
            # 若未获取，调用 platform.system() 获取并存储
            cls.system_type = platform.system()
        return cls.system_type


app_config = AppConfig()

