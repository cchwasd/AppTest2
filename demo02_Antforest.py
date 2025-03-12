import time

import uiautomator2 as u2
from match_image import get_npos_by_more_match


def ant_forest():
    device = u2.connect('f800062f')
    print("screen_size:", device.window_size())

    # device.shell("adb shell settings put system screen_off_timeout %d" % 600000)
    device.app_start(package_name="com.eg.android.AlipayGphone", wait=True)
    device.sleep(1.0)
    # app_current = device.app_current()
    # print(f'---app_current:{app_current}')
    txt_btn = device(text='使用密码验证')
    if txt_btn.exists():
        device(text='使用密码验证').click()
        # device(text='使用指纹验证').wait()
        # 九宫格解锁
        wipe_points = {
            'points': [
                (250, 2060), (250, 1770), (250, 1482), (540, 1768),
                (828, 1482), (828, 1770), (828, 2060)
            ]
        }
        device.swipe_points(wipe_points.get('points'), 0.1)
    device.sleep(1)
    device(resourceId="com.alipay.android.phone.openplatform:id/app_text", text="蚂蚁森林").click(timeout=3)
    device(text='去保护').wait()
    source_img = './mode_imgs/ant_forest.png'
    target_img = './mode_imgs/ball_g.png'
    target_img2 = './mode_imgs/energy_font.png'
    source_img2 = './mode_imgs/screenshot_page.png'
    device.screenshot(source_img)
    pos_list = get_npos_by_more_match(source_img, target_img)
    if pos_list:
        for item in pos_list:
            print(f'---坐标点：{item}')
            device.click(x=item[0], y=item[1])
            time.sleep(0.5)
    while True:
        device.click(x=960, y=1600)     # 点击找能量
        device(textMatches=".+的蚂蚁森林").wait()

        device.screenshot(source_img2)
        pos_list = get_npos_by_more_match(source_img2, target_img)

        if pos_list:
            for item in pos_list:
                print(f'---坐标点：{item}')
                device.click(x=item[0], y=item[1])
                time.sleep(0.5)
        pos_list2 = get_npos_by_more_match(source_img2, target_img2)
        if pos_list2:
            for item in pos_list2:
                print(f'---坐标点：{item}')
                device.click(x=item[0], y=item[1])
                time.sleep(0.5)
        if device(text="共找到能量").exists():
            device(text="返回我的森林").click_gone()
            break
    time.sleep(1)
    device.press("home")


if __name__ == '__main__':
    ant_forest()
    # device = u2.connect('f800062f')
    # # device.screenshot('./mode_imgs/energy_ball.png')
    # print(device(text="可收取").exists())