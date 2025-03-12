import time

import pytest
from common.Uiauto2Bar import UiAuto2Bar
from common.utils import u2_screen

@pytest.fixture(scope='session')
def u2_start(serial="ALNYGL3911000015", recording=1): # serial="ALNYGL3911000015", recording=1
    app = UiAuto2Bar(serial, recording)
    app.start_preset()
    time.sleep(1.5)
    yield app
    app.stop_service()


@u2_screen
def test_login_account2(u2_start):
    app = u2_start
    app.device.swipe_ext("up")
    unlock_points =[
        (400, 1630), (600, 1430), (600, 1630), (800, 1430), (800, 1236), (600, 1236), (400, 1430),
    ]
    app.device.swipe_points(unlock_points, duration=0.4)
    app.device.adb_device.switch_wifi(True)
    app.device.app_stop("com.android.settings")

    app.device.app_start("com.android.settings")
    # app.device(resourceId="android:id/title", text="WLAN").click_exists(2)
    # app.switch_checkbox(text_before="WLAN",id_before="com.android.settings:id/switch_text",checkbox_name="android.widget.Switch",enabled=True)
    time.sleep(3)
    logout_check = app.device(resourceId="android:id/title", text="登录荣耀账号").click_exists(3)
    assert logout_check==True, "请检查登录状态！"
    account = "18735992867"
    password = "Ljjz@123"
    if app.device(resourceId="com.hihonor.id:id/welcome_header_text", text="荣耀账号").wait(timeout=3):
        app.device(resourceId="com.hihonor.id:id/check_user_name").clear_text()
        app.device(resourceId="com.hihonor.id:id/check_user_name").send_keys(account)
        app.device(resourceId="com.hihonor.id:id/btn_check_account",text="下一步").click()
        app.device(packageName="com.hihonor.id",text="荣耀账号").wait(timeout=2)
        app.device(resourceId="com.hihonor.id:id/login_by_pwd_txt", text="密码登录").click()
        app.device(resourceId="com.hihonor.id:id/password_display_layout").click()
        # app.device(resourceId="com.hihonor.id:id/password_display_layout").send_keys(password)
        app.device.shell(f"input text {password}")
        app.device(resourceId="com.hihonor.secime:id/keyboard_hide_btn").click()
        if app.device(resourceId="com.hihonor.id:id/agreement_checkbox").info["checked"] == False:
            app.device(resourceId="com.hihonor.id:id/agreement_checkbox").click()
        app.device(resourceId="com.hihonor.id:id/btn_login", text="登录").click()

    res_check = app.device(resourceId="android:id/action_bar_title", text="账号中心").wait(timeout=6)
    assert res_check == True, "登录失败，请检查！"

    app.device.press("home")
    app.device.app_stop("com.android.settings")
    app.device.adb_device.switch_wifi(False)



