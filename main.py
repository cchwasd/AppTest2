import time
from appium import webdriver
from appium.options.common.base import AppiumOptions
from appium.options.android import UiAutomator2Options  # 继承自 AppiumOptions 针对 Android 平台的特定选项类
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.webdriver import By  # 导入appium 定位的方法包
from appium.webdriver.extensions.android.nativekey import AndroidKey

"""
{
  "appium:automationName": "uiautomator2",
  "platformName": "Android",
  "appium:platformVersion": "12",
  "appium:deviceName": "f800062f",
  "appium:appPackage": "com.android.settings",
  "appium:appActivity": ".MainSettings",
  "appium:ignoreHiddenApiPolicyError": "true"
}

# 环境：Appium-Python-Client==3.1.1, selenium==4.18.1, node:v20.11.1,
"""


def create_driver():
    """
    AppiumOptions():
        用于配置 Appium 测试的通用选项，可用于 Android 和 iOS 平台
        可以设置通用的测试选项，如平台名称、版本、自动化引擎等
    """
    # 创建 AppiumOptions 对象
    options = AppiumOptions()  # UiAutomator2Options()
    # 加载测试的配置选项和参数(Capabilities配置)
    options.load_capabilities({
        "automationName": "uiautomator2",  # 自动化测试的引擎
        "platformName": "Android",  # 系统平台
        "platformVersion": "12",  # 系统版本
        "deviceName": "f800062f",  # 设备的名称
        "udid": "f800062f",
        "appPackage": "com.android.settings",  # 待测试应用的包名(启动APP)
        "appActivity": ".MainSettings",  # 待测试应用的活动（Activity）名称
        "unicodeKeyboard": "true",  # 设置使用 Unicode 编码方式发送字符串到设备的键盘
        "restKeyboard": "true",  # 设置重置设备的软键盘状态并隐藏键盘
        "skipServerInstallation": "false",
        "noReset": "true",  # 不重置App，是否保留 session 信息，可以避免重新登录
        "ignoreHiddenApiPolicyError": "true"
    })

    # Appium服务器地址端口，本地用http://127.0.0.1:4723
    # 连接AppiumServer，初始化自动化环境，并启动应用
    appium_host = 'http://127.0.0.1:4723/wd/hub'
    driver = webdriver.Remote(appium_host, options=options)

    print(driver.current_activity)
    return driver


def close_driver(driver):
    """关闭驱动"""
    if driver:
        driver.quit()


def test_driver():
    driver = create_driver()
    # 设置隐式等待时间为10秒
    driver.implicitly_wait(10)

    size_dict = driver.get_window_size()
    x, y = size_dict['width'], size_dict['height']

    # 根据id定位搜索位置框，点击
    driver.find_element(by=AppiumBy.ID, value="android:id/inputArea").click()

    # 根据id定位搜索输入框，点击
    sbox = driver.find_element(by=AppiumBy.ID, value="android:id/input")
    sbox.send_keys("锁屏")
    # 输入回车，确定搜索
    driver.press_keycode(AndroidKey.ENTER)
    # 选择（定位）所有标题
    eles = driver.find_elements(by=AppiumBy.ID, value="com.android.settings:id/settings_search_item_name")
    result_list = [ele.text for ele in eles]

    # 滑动 直到页面底部
    page = driver.page_source
    len_page = len(page)
    while True:
        temp_page = page[:-len_page // 4]
        driver.swipe(x // 2, y // 2, x // 2, y // 6, duration=800)
        time.sleep(2)
        page = driver.page_source
        len_page = len(driver.page_source)

        eles = driver.find_elements(by=AppiumBy.ID, value="com.android.settings:id/settings_search_item_name")
        for ele in eles:
            context = ele.text
            if context not in result_list:
                result_list.append(context)

        if temp_page == driver.page_source[:-len_page // 4]:
            break
        temp_page = page[:-len_page // 4]

    # print(page,size_dict)
    print(result_list, len(result_list))

    # 关闭驱动
    close_driver(driver)


if __name__ == "__main__":
    test_driver()

