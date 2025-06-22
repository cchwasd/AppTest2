import platform


class AppConfig:
    """Ӧ�������࣬���ڴ洢Ӧ�õĸ��������"""
    system_type = None # ��ʼ�������ԣ����ڴ洢ϵͳ����

    def __init__(self, custom_config=None):
        self.custom_config = custom_config
        AppConfig.system_type = AppConfig.get_system_type()
    @classmethod
    def get_system_type(cls):
        # �ж�ϵͳ�����Ƿ��ѻ�ȡ
        if cls.system_type is None:
            # ��δ��ȡ������ platform.system() ��ȡ���洢
            cls.system_type = platform.system()
        return cls.system_type


app_config = AppConfig()

