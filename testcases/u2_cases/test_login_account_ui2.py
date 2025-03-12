import time

import pytest
from common.Uiauto2Bar import UiAuto2Bar
from common.utils import u2_screen

@pytest.fixture(scope='session')
def u2_start(serial, recording):
    app = UiAuto2Bar(serial, recording)
    time.sleep(2)
    app.start_preset()
    yield app
    app.stop_service()


@u2_screen
def test_login_account(u2_start):
    app = u2_start
    app.device.app_current()
    app.device.swipe_ext("up")
    unlock_points =[
        (245, 1880), (532, 1590), (532, 1880), (830, 1590), (830, 1300), (532, 1300), (245, 1590),
    ]
    app.device.swipe_points(unlock_points, duration=0.4)
    # app.device.adb_device.switch_wifi(True)
    app.device.app_stop("com.android.settings")
    app.device.app_start("com.android.settings")
    app.device(resourceId="android:id/title", text="WLAN").click_exists(2)
    app.switch_checkbox(text_before="WLAN", checkbox_name="android.widget.CheckBox",enabled=True)
    app.device(description="返回").click(2)
    logout_check = app.device(resourceId="android:id/title", text="登录小米帐号").click_exists(2)
    assert logout_check==True, "请检查登录状态！"
    app.device(text="账号密码登录").click(2)
    account = "18735992867"
    password = "cch123456"
    app.device(resourceId="com.xiaomi.account:id/et_account_name").clear_text()
    app.device(resourceId="com.xiaomi.account:id/et_account_name").send_keys(account)
    app.device(resourceId="com.xiaomi.account:id/password_layout").click()
    app.device(description="删除").long_click(1)
    # # 会弹出小米安全键盘，只能一个个点击输入密码
    # for i in password:
    #     app.device(description=i).click()
    app.device.shell(f"input text {password}")
    app.device(description="完成").click()
    agree_box = app.device(className="android.widget.CheckBox",resourceId="com.xiaomi.account:id/license")
    if agree_box.info["checked"] == False:
        agree_box.click()

    app.device(text="登录").click(1)
    app.device(text="小米云服务").wait(timeout=5)
    app.device(text="同意并继续").click()
    app.device(text="取消").click(2)
    if app.device(text="自动保存账号密码").wait(timeout=5):
        app.device(text="取消").click()
    # 默认开启，点击关闭
    # app.device(resourceId="android:id/title", text="开启小米云服务").click(timeout=20)
    # app.device(resourceId="android:id/title", text="开启查找手机").click()
    # app.device(resourceId="com.miui.cloudservice:id/btn_next").click()
    logout_check = app.device(resourceId="com.xiaomi.account:id/action_bar_title_expand", text="小米账号").click_exists(2)
    assert logout_check==True, "登录失败，请检查！"

    app.device.press("home")
    app.device.app_stop("com.android.settings")
    app.device.adb_device.switch_wifi(False)

