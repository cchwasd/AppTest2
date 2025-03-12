import json
import random
import time
import uiautomator2 as u2
import requests
import base64

def umi_ocr(file=""):
    url = 'http://127.0.0.1:1224/api/ocr'
    headers = {"Content-Type": "application/json",
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
               }
    with open(file, "rb") as rf:
        img_context = rf.read()
    img_data = base64.b64encode(s=img_context).decode("utf-8")
    # print("img_data: ", img_data)
    dict_data = {
        'base64': img_data
    }
    result = {}
    # print("json_data: ", json_data)
    post_data = requests.post(url=url, data=json.dumps(dict_data), headers=headers)
    res_dict = post_data.json()
    if post_data.status_code == 200 and res_dict["code"]==100:
        # print("res_data: ", res_dict["data"])
        for item in res_dict["data"]:
            # print(item["text"], item["box"][0])
            if item["text"] not in result.keys():
                center_pos = 0.5 * (item["box"][0][0]+item["box"][1][0]), 0.5 * (item["box"][0][1]+item["box"][2][1])
                result[item["text"]]=center_pos
    # print(result)
    return result
class BrushDevice:
    def __init__(self, app_pkg, run_hour):
        self.app_pkg=app_pkg
        self.run_hour=run_hour
        self.device = u2.connect()  # 'f800062f'
        self.swipe_count = 0
        self.start_time = time.time()  # 获取当前时间
        self.stop_time = self.start_time + self.run_hour * 3600

    def app_run(self):
        app_pkg=self.app_pkg
        run_hour=self.run_hour
        device=self.device
        print("--start info:",device.info)
        print("--start device_info:",device.device_info)
        print("--start app_current:",device.app_current())
        # 设定循环持续时间为2小时，即7200秒

        device.implicitly_wait(3)   # 设置元素查找等待时间
        w, h =device.window_size()

        app_events = {
            'com.kuaishou.nebula': self.kuaishou_start,
            'com.ss.android.ugc.aweme.lite': self.douyin_start,
        }
        app_event = app_events[app_pkg]
        app_event()

        if time.time() > self.stop_time:
            print(f"---{app_pkg} 刷视频 {run_hour}h 完成")
            print(f"---共滑动 {self.swipe_count} 次")

        #     device.swipe(0.5, 0.7, 0.5, 0.3, duration=0.3)
        #     time.sleep(random_second)
        #     self.swipe_count+=1

    def restart_app(self):
        device=self.device
        device.press("home")
        device.app_stop(self.app_pkg)
        device.app_start(self.app_pkg)

    def kuaishou_start(self):
        start_pkg_name="com.kuaishou.nebula"
        device=self.device

        flag_flush = False
        if device.app_current().get('package', 'None') != start_pkg_name:
            device.app_start(package_name=start_pkg_name)
            time.sleep(3)
        if device.xpath('//*[@text="我知道了"]').exists:
            device.xpath('//*[@text="我知道了"]').click()
        if device.xpath('//*[@text="取消"]').exists:
            device.xpath('//*[@text="取消"]').click()
        if device.xpath('//*[@text="拒绝"]').exists:
            device.xpath('//*[@text="拒绝"]').click()
        if device(text="立即领取").exists:
            device(text="立即领取").click()
            device.xpath('//*[@text="立即签到"]').click()
            device.xpath('/hierarchy/android.widget.FrameLayout[3]/android.widget.FrameLayout[1]/android.widget.LinearLayout[1]/android.widget.FrameLayout[1]/android.widget.FrameLayout[1]/android.widget.RelativeLayout[1]/android.widget.FrameLayout[1]/android.webkit.WebView[1]/android.webkit.WebView[1]/android.view.View[1]/android.view.View[5]/android.view.View[5]/android.view.View[1]/android.view.View[1]').click()
            device.press("back")
        if device.xpath('//*[@text="去赚钱"]').wait(4):
            device.xpath('//*[@text="去赚钱"]').click()


        # if device.xpath('//*[contains(@text,"看视频额外得")]').exists:
        #     device.xpath('//*[contains(@text,"看视频额外得")]').click()
        # if device.xpath('//*[starts-with(@text,"看视频额外得")]').exists:
        #     device.xpath('//*[starts-with(@text,"看视频额外得")]').click()
        # if device.xpath("//*[re:match(@text, '^看视频额外得')]").exists:
        #     device.xpath("//*[re:match(@text, '^看视频额外得')]").click()

        # 2. 日常任务，看 6 次直播
        print("看 6 次直播")
        for i in range(6):
            if device.xpath('//*[@text="放弃奖励"]').exists:
                device.xpath('//*[@text="放弃奖励"]').click()
                device.press("back")
            if device.xpath('//*[@text="去赚钱"]').wait(6):
                device.xpath('//*[@text="去赚钱"]').click()
                time.sleep(3)
            device.swipe(0.5, 0.8, 0.5, 0.2)
            time.sleep(2)
            if device.xpath('//*[@text="规则"]').exists:
                device.xpath('//*[@text="规则"]').click()
            # if device.xpath("//*[re:match(@text, '直播领金币$')]").exists:
            #     device.xpath("//*[re:match(@text, '直播领金币$')]").click()
                time.sleep(3)
                device.swipe(0.5, 0.2, 0.5, 0.8)
                time.sleep(2)
                device.click(0.2, 0.4)
                time.sleep(66)
                device.press("back")
                if device.xpath('//*[@text="退出直播间"]').wait(2):
                    device.xpath('//*[@text="退出直播间"]').click()
                if device.xpath('//*[@content-desc="返回"]').wait(2):
                    device.xpath('//*[@content-desc="返回"]').click()
                time.sleep(1)
            self.swipe_count += 1
        self.restart_app()

        # 搜索
        print("搜索")
        for i in range(2):
            if device.xpath('//android.widget.CheckedTextView[@text="去赚钱"]').exists:
                device.xpath('//android.widget.CheckedTextView[@text="去赚钱"]').click()
                time.sleep(3)
                device.swipe(0.5, 0.8, 0.5, 0.2)
                time.sleep(2)
            try:
                if not device.xpath('//*[re:match(@text, "搜索“.*”赚金币")]').exists:
                    break
                node = device.xpath('//*[re:match(@text, "搜索“.*”赚金币")]')
                search_text = node.text.split("“")[-1].split("”")[0]
                node.click()
                time.sleep(2)
                device.send_keys(text=search_text)
                time.sleep(1)
                device.xpath('//*[@text="搜索"]').click()
                time.sleep(2)
                device.press("back")
                device.press("back")

            except Exception as e:
                print(e)

        # 看广告
        print("看广告")
        for _ in range(10):
            if device.xpath('//*[@text="去赚钱"]').wait(4):
                device.xpath('//*[@text="去赚钱"]').click()
                time.sleep(3)
                device.swipe(0.5, 0.8, 0.5, 0.2)
                time.sleep(2)
                for _ in range(3):
                    if device.xpath('//*[contains(@text,"看广告得")]').exists:
                        break
                    device.swipe(0.5, 0.8, 0.5, 0.2)
                if not device.xpath('//*[contains(@text,"看广告得")]').exists:
                    break
            time.sleep(1)
            if device.xpath('//*[@text="放弃奖励"]').exists:
                device.xpath('//*[@text="放弃奖励"]').click()
            if device.xpath('//*[contains(@text,"看广告得")]').exists:
                device.xpath('//*[contains(@text,"看广告得")]').click()
                time.sleep(30)
                if device.xpath('//*[@text="已成功领取奖励"]').exists:
                    device.press("back")
                if device.xpath('//*[@text="坚持退出"]').wait(2):
                    device.xpath('//*[@text="坚持退出"]').click()
            time.sleep(1)
        # 1.最后 n 分钟 刷视频
        while time.time() < self.stop_time:
            random_second = random.randint(5, 15)
            if device.xpath('看视频额外得%').exists:
                device.xpath('看视频额外得%').click()
                time.sleep(2)
            device.swipe(0.5, 0.7, 0.5, 0.3, duration=0.3)
            time.sleep(random_second)
            self.swipe_count+=1
    def douyin_start(self):
        start_pkg_name="com.ss.android.ugc.aweme.lite"
        save_img_path='./mode_imgs/douyin_img.png'
        device=self.device
        if device.app_current().get('package', 'None') != start_pkg_name:
            device.app_start(package_name=start_pkg_name)
            time.sleep(3)
        if device.xpath('//*[@text="关闭"]').exists:
            device.xpath('//*[@text="关闭"]').click()
        if device.xpath('//*[@text="忽略提醒"]').exists:
            device.xpath('//*[@text="忽略提醒"]').click()
        if device.xpath('//*[@text="我知道了"]').exists:
            device.xpath('//*[@text="我知道了"]').click()
        # if self.swipe_count % 50 == 0:
        if device.xpath('//*[@resource-id="com.ss.android.ugc.aweme.lite:id/dc9"]').wait(3):
            device.xpath('//*[@resource-id="com.ss.android.ugc.aweme.lite:id/dc9"]').click()
            time.sleep(3)
        device.screenshot(save_img_path)
        time.sleep(2)
        res_data = umi_ocr(save_img_path)
        time.sleep(1)
        print("---res_data:", res_data)

        # 逛街赚钱
        print("逛街赚钱")
        for _ in range(15):
            event = "逛街赚钱"
            if "逛街赚钱" in res_data.keys():
                print("---click: ",res_data[event])
                device.click(res_data[event][0], res_data[event][1])
                time.sleep(3)
                for j in range(6):
                    time.sleep(5)
                    device.swipe(0.5, 0.7, 0.5, 0.3, duration=0.3)
                if device.xpath('//com.lynx.tasm.ui.image.FlattenUIImage').wait(2):
                    device.xpath('//com.lynx.tasm.ui.image.FlattenUIImage').click()
                    time.sleep(1)
                    device.press("back")
                    time.sleep(2)
                print("---wait ")

            event = "看广告赚金币"
            print("看广告赚金币")
            if "逛街赚钱" in res_data.keys():
                if device.xpath('//*[@text="评价并收下金币"]').exists:
                    device.xpath('//com.lynx.tasm.ui.image.FlattenUIImage').click()
                if device.xpath('//*[contains(@text,"领取成功")]').exists:
                    device.press("back")
                print("---click: ",res_data[event])
                device.click(res_data[event][0], res_data[event][1])
                time.sleep(25)
                if device.xpath('//*[contains(@text,"领取成功")]').exists:
                    device.press("back")

            event = "看小说赚金币"
            print("看小说赚金币")
            if "逛街赚钱" in res_data.keys():
                device.watcher("name1").when('//*[@text="立即领取"]').click('//*[@text="立即领取"]')
                device.watcher.watched = True
                print("---click: ", res_data[event])
                device.click(res_data[event][0], res_data[event][1])
                if device.xpath('//*[@text="继续阅读"]').exists:
                    device.xpath('//*[@text="继续阅读"]').click()
                else:
                    if device.xpath('//*[@text="书架"]').exists:
                        device.xpath('//*[@text="书架"]').click()
                        device.click(200, 700)
                for _ in range(30):

                    device.swipe(0.5, 0.7, 0.5, 0.3, duration=0.3)
                    time.sleep(3)
                if device.xpath('//*[contains(@text,"领取成功")]').exists:
                    device.press("back")
                device.watcher.watched = False
            self.restart_app()
            time.sleep(3)
            for _ in range(30):
                device.swipe(0.5, 0.7, 0.5, 0.3)
                time.sleep(5)





def main():
    # app_pkg="com.kuaishou.nebula"
    app_pkg="com.ss.android.ugc.aweme.lite"
    run_hour=2

    brushdevice = BrushDevice(app_pkg,run_hour)
    brushdevice.app_run()

if __name__ == '__main__':
    # umi_ocr()
    try:
        st = time.time()
        main()
    except Exception as e:
         print(e)
    finally:
        et = time.time()
        str_st = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(st))
        str_et = time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(et))
        print(f"开始时间：{str_st}\n结束时间：{str_et}")
