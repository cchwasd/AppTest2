from appium.webdriver.common.appiumby import AppiumBy


class SettingsPage:
    package = "com.android.settings"
    activity = "com.android.settings/com.android.settings.MainSettings"

    ## 通用元素
    common_ele_text = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("${var}")')

    # 启动页同意
    agree_btn = (AppiumBy.ID, "com.xkw.client:id/agree_yes")

    # 登录页操作
    account_text = (AppiumBy.XPATH, '//android.widget.TextView[@text="管理帐号、云服务等"]')
    logout_btn = (AppiumBy.ID, 'com.xiaomi.account:id/logout_btn')
    mine_btn = (AppiumBy.ID, "com.xkw.client:id/mine_text")
    login_btn = (AppiumBy.ID, "com.xkw.client:id/mine_username")
    password_login_btn = (AppiumBy.ID, "com.xkw.client:id/login_mobile_use_password")
    username_input = (AppiumBy.ID, "com.xkw.client:id/login_password_username")
    password_input = (AppiumBy.ID, "com.xkw.client:id/login_password_password")
    login_submit_btn = (AppiumBy.ID, "com.xkw.client:id/login_password_login")
    discover_search_box = (AppiumBy.ID, "com.xkw.client:id/discover_search_box")

    # 发现页面
    discovery_btn = (AppiumBy.ID, "com.xkw.client:id/discover_text")
    ## 推荐页面
    recommend_btn = (AppiumBy.ID, "com.xkw.client:id/recommend_text")
    ## 分类页面
    category_btn = (AppiumBy.ID, "com.xkw.client:id/category_text")
    course_synchronization_resources_btn = (AppiumBy.ID, "com.xkw.client:id/category_entrance_left")
    knowledge_point_resources_btn = (AppiumBy.ID, "com.xkw.client:id/category_entrance_right")



if __name__ == "__main__":
    # from common.utils import replace_text
    # ele_text = replace_text(SettingsPage.common_ele_text, "安全")
    # print(ele_text)
    pass

