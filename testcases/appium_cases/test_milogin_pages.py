
import pytest
from data_pages.settings_page import SettingsPage
from common.AppiumBar import AppiumBar
from common.utils import parse_var


@pytest.fixture(scope='session')
def appium_start(index_device):
    app = AppiumBar()
    app.init_works(index_device)
    yield app
    app.clean_works()

def test_android_click(appium_start):
    # Usage of the context manager ensures the driver session is closed properly
    # after the test completes. Otherwise, make sure to call `driver.quit()` on teardown.
    app = appium_start
    app.driver.terminate_app('com.android.settings')
    app.driver.activate_app('com.android.settings')
    app.driver.implicitly_wait(3)
    # app.driver.find_element(*SettingsPage.account_text).click()
    # app.driver.find_element(*SettingsPage.logout_btn).click()

    text_lst = ['我的设备','WLAN',] # '显示','声音与振动','桌面','安全','照片','应用设置','我的服务']
    for text in text_lst:
        temp_ele = parse_var(SettingsPage.common_ele_text, text)
        print(temp_ele)
        if app.check_with_scroll(*temp_ele):
            app.driver.find_element(*temp_ele).click()
            app.press_key("back")


    assert app.check_element_exist(*parse_var(SettingsPage.common_ele_text, "我的服务"))== True, f"界面元素断言失败！"

