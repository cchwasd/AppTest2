# -*- coding: utf-8 -*-
"""
----------------------------------------
# @File         : AppConfig.py
# @Time         : 2025/7/20 0:57
# @Author       : cch
# @Description  : 
----------------------------------------
"""
import platform
# 通过元类实现线程锁的单例模式
import threading

# 定义线程锁单例元类
class ThreadSafeSingletonMeta(type):
    _instances = {}
    _lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        # 使用双重检查锁定，先在不加锁的情况下检查实例是否已创建，如果未创建再进入同步块进行二次检查。这样可以减少不必要的锁竞争，提高性能。
        if cls not in cls._instances:
            with cls._lock:     # 使用线程锁保证线程安全
                if cls not in cls._instances:
                    cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

# 使用元类创建单例类
class AppConfig(metaclass=ThreadSafeSingletonMeta):
    """应用配置类，用于存储应用的各种配置项。"""
    _system_type = None   # 类属性，用于存储系统类型
    case_data: dict = {}

    def __init__(self, custom_config=None):
        # 初始化操作
        self._custom_config = custom_config
        # 初始化系统类型
        if AppConfig._system_type is None:
            AppConfig._system_type = AppConfig._get_system_type()
        self.system_type = AppConfig._system_type


    @classmethod
    def _get_system_type(cls):
        try:
            # 调用 platform.system() 获取系统类型
            # print("_get_system_type run")
            system_type = platform.system()
        except Exception as e:
            # 异常处理，记录日志或设置默认值
            print(f"Failed to get system type: {e}")
            system_type = "Unknown"
        return system_type

    @property
    def custom_config(self):
        return self._custom_config
    @custom_config.setter
    def custom_config(self, new_config):
        self._custom_config = new_config


app_config = AppConfig()


if __name__ == "__main__":

    appconfig = AppConfig(custom_config="my_custom_config")
    print(id(appconfig), appconfig.system_type, appconfig.custom_config)
    print(appconfig.case_data)
    AppConfig.case_data = {"k1": "v1"}
    appconfig = AppConfig()
    print(id(appconfig), appconfig.system_type, appconfig.custom_config)
    print(appconfig.case_data)

