

class SettingsPage:
    package = "com.android.settings"
    activity = "com.android.settings/com.android.settings.MainSettings"

    class agree_btn:
        resourceId = "com.xkw.client:id/agree_yes"
        text = "同意"

    class logout_btn:
        resourceId = "com.xiaomi.account:id/logout_btn"
        text = "退出登录"

    class discover_search_box:
        resourceId = "com.xkw.client:id/discover_search_box"
        text = "搜索"


if __name__ == "__main__":

    from common.utils import class_to_dict, dict_to_class
    settings_dict = class_to_dict(SettingsPage)
    print(settings_dict)
    print(settings_dict["agree_btn"])

    settings_class = dict_to_class(settings_dict)
    print(settings_class.agree_btn.resourceId)

    def prase_data(resourceId, text):
        print(resourceId, text)

    data = {'resourceId': 'com.xkw.client:id/agree_yes', 'text': '同意'}
    prase_data(**data)
    pass

