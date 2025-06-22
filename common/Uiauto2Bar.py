
import argparse
import base64
import logging
import signal
import subprocess
from datetime import datetime
from typing import Union, Optional
import uiautomator2 as u2
import time
import os

from common import the_paths, AdbBar
from common.utils import exec_subprocess, os_type

# import cv2
# import numpy as np

logger = logging.getLogger("Uiauto2Bar")

class UiAuto2Bar:
    def __init__(self, serial:str="", recording:bool=False):
        if not serial:
            if not AdbBar.devices:
                logger.error("No devices connected.")
                raise Exception("No devices connected.")
            self.serial = AdbBar.devices[0]
        else:
            self.serial = serial
        self.device = u2.connect(serial)
        self.device.wait_timeout=3  # 设置默认元素等待超时（秒）
        self.option_dict: dict = {"recording":recording}

    def start_preset(self):
        logger.info("Starting preset...")
        if not self.is_screen_on():
            self.device.press("power")
            self.device.screen_on()
        if "recording" in self.option_dict and self.option_dict["recording"]:
            self.start_recording()
        self.keep_week()
    def stop_service(self):
        logger.info("stopping service...")
        if "recording" in self.option_dict and self.option_dict["recording"]:
            self.stop_recording()
        self.device.screen_off()
        self.stop_week()
        self.device.stop_uiautomator()
    def is_screen_on(self):
        return self.device.info["screenOn"]
    def keep_week(self):
        self.device.shell("svc power stayon true")
    def stop_week(self):
        self.device.shell("svc power stayon false")
    def get_info(self):
        print("-"*20)
        print(self.device.info,
              self.device.device_info,
              self.device.app_current(),  # 获取当前应用包名，Activity名称
              sep="\n")
        self.device.dump_hierarchy()    # 界面信息树

        print("-" * 20)

    def connect_wifi(self, ssid: str="", password: str=""):
        if not ssid:
            return False
        self.device.shell(cmdargs=f"adb shell cmd wifi connect-network {ssid} wpa2 {password}")
        logger.info("connecting to wifi")
    def swipe(self, direct:str="bottom", duration: float = 0.5):
        swipe_direct = {
            'bottom': (0.5, 0.6, 0.5, 0.3),
            'top': (0.5, 0.6, 0.5, 0.9),
            'left': (0.2, 0.5, 0.9, 0.5),
            'right': (0.9, 0.5, 0.2, 0.5),
        }
        self.device.swipe(*swipe_direct[direct],duration=duration)
        logger.info(f"{direct} swipe.")

    def dock_swipe(self, direction:str="right"):
        # w, h = self.device.window_size()
        logger.info(f"dock_swipe")
        if direction == "right":
            self.device.swipe(0.98, 0.5, 0.6, 0.5, duration=0.8)
        elif direction == "left":
            self.device.swipe(0.02, 0.5, 0.5, 0.5, duration=0.8)

    def check_element(self, **kwargs):
        # 超时检查元素是否存在
        timeout = kwargs["timeout"] if "timeout" in kwargs.keys() else 0
        logger.info(f"check_element")
        if "timeout" in kwargs.keys():
            del kwargs["timeout"]
        if "xpath" in kwargs.keys():
            return self.device.xpath(xpath=kwargs["xpath"]).wait(timeout=timeout)
        return self.device(**kwargs).wait(timeout=timeout)

    def wait_element_gone(self, **kwargs):
        timeout = kwargs["timeout"] if "timeout" in kwargs.keys() else 0
        if "timeout" in kwargs.keys():
            del kwargs["timeout"]
        if "xpath" in kwargs.keys():
            return self.device.xpath(xpath=kwargs["xpath"]).wait_gone(timeout=timeout)
        return self.device(**kwargs).wait_gone(timeout=timeout)

    def find_elements(self, **kwargs):
        if "xpath" in kwargs.keys():
            if "index" in kwargs.keys():
                self.device.xpath(xpath=kwargs["xpath"]).all()[kwargs["index"]]
            return self.device.xpath(xpath=kwargs["xpath"]).all()
        else:
            return self.device(**kwargs)

    def get_attribs(self, **kwargs):
        if ("instance" or "index") in kwargs.keys():
            return self.device(**kwargs).info
        if "xpath" in kwargs.keys():
            elements = self.device.xpath(kwargs["xpath"]).all()
            return [ele.attrib for ele in elements]
        else:
            # return [self.device(**kwargs, instance=i).info for i in self.device(**kwargs).count]
            return [ele.info for ele in self.device(**kwargs)]

    def check_switch_checkbox(self, text_before:str="", id_before="android:id/title",checkbox_name="android.widget.CheckBox"):
        old_wait = self.device.wait_timeout
        self.device.wait_timeout = 0.1
        status_dict = {
            'true': True,
            'false': False
        }
        xpath1 = f'//*[@text="{text_before}" and @resource-id="{id_before}"]/../..//{checkbox_name}'
        xpath2 = f'//*[@text="{text_before}" and @resource-id="{id_before}"]/../../..//{checkbox_name}'

        if text_before and not id_before:
            xpath1 = f'//*[@text="{text_before}"]/../..//{checkbox_name}'
            xpath2 = f'//*[@text="{text_before}"]/../../..//{checkbox_name}'
        element = self.device.xpath(xpath1)
        if element.exists:
            self.device.wait_timeout = old_wait
            logger.info(f"The checkbox element is existing, {element.attrib['checked']}")
            return status_dict.get(element.attrib['checked']), element
        else:
            element = self.device.xpath(xpath2)
            if element.exists:
                self.device.wait_timeout = old_wait
                logger.info(f"The checkbox element is existing, {element.attrib['checked']}")
                return status_dict.get(element.attrib['checked']), element
        self.device.wait_timeout = old_wait
        logger.error("The checkbox element is nonexistent")
        return False, None

    def switch_checkbox(self, text_before:str="", id_before="android:id/title",checkbox_name="android.widget.CheckBox", enabled=True):
        status, element = self.check_switch_checkbox(text_before, id_before, checkbox_name=checkbox_name)
        if not element:
            return False
        if status != enabled:
            logger.info(f"The checkbox element is being {enabled}")
            element.click()
            return enabled
        elif status == enabled:
            logger.info(f"The checkbox element has been {enabled}")
            return enabled

    def check_with_scroll(self,sx:Union[int,float]=0.5,sy:Union[int,float]=0.5,distance=800,direct="bottom",maxslipes: int=30, slipe_to_top:bool=False, **kwargs):
        w, h = self.device.window_size()
        swipe_direct = {
            'bottom': (sx * w, sy * h, sx * w, sy * h - distance),
            'top': (sx * w, sy * h, sx * w, sy * h + distance),
            'left': (sx * w, sy * h, sx * w - distance, sy * h),
            'right': (sx * w, sy * h, sx * w + distance, sy * h),
        }
        if "xpath" in kwargs.keys():
            element = self.device.xpath(kwargs["xpath"])
        else:
            element = self.device(**kwargs)
        if element.exists:
            logger.info("Slide to check that the element is present")
            return element
        if slipe_to_top:
            self.device(scrollable=True).scroll.toBeginning(steps=50)

        length = len(self.device.dump_hierarchy())
        dump_data = self.device.dump_hierarchy()[-length // 6:]
        for _ in range(maxslipes):
            self.device.swipe(*swipe_direct[direct],duration=0.5)
            if element.exists:
                logger.info("Slide to check that the element is present")
                return element
            new_dump_data = self.device.dump_hierarchy()[-length // 6:]
            if new_dump_data==dump_data:
                break
            dump_data = new_dump_data
        logger.info("Slide check that the element does not exist")
        return None

    def click_with_scroll(self,sx:Union[int,float]=0.5,sy:Union[int,float]=0.5,distance=800,direct="bottom",maxslipes: int=30, slipe_to_top:bool=False, **kwargs):
        element = self.check_with_scroll(sx=sx,sy=sy,distance=distance,direct=direct,maxslipes=maxslipes,slipe_to_top=slipe_to_top, **kwargs)
        logger.info("Swipe to find and click the element")
        if element is not None:
            element.click()

            return True
        return False

    def screen_shot(self, serial:str="",filename: Optional[str] = None, format="pillow", display_id: Optional[int] = None):
        if not serial:
            serial = self.device.serial
        if filename is None:
            now_time = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{serial}_{now_time}.png"
        self.device.screenshot(filename=filename, format=format, display_id=display_id)
        logger.info(f"Screenshot savePath: {filename} ")

    def start_recording(self):
        logger.info("Start recording...")
        scrcpy_app = r"C:\MPrograms\Android\scrcpy-win64-v2.7\scrcpy.exe"
        cur_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        save_path = the_paths.get("logs") / f"{self.device.serial}-{cur_time}.mp4"
        try:
            self.option_dict["scrcpy_process"] = subprocess.Popen(
            f"{scrcpy_app} -s {self.device.serial} --max-size=1920 --max-fps=20 --video-bit-rate 6M --record={save_path}",
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) # --no-display
            self.option_dict["recording"] = True
            logger.info(f"option_dict: {self.option_dict}")
            logger.info(f"recording savepath: {save_path}")
            return True
        except Exception as e:
            logger.error(f"start_recording error: {e}")
            self.option_dict["recording"] = False
        return False

    def stop_recording(self):
        logger.info("Stopping recording...")
        if self.option_dict["recording"] and "scrcpy_process" in self.option_dict:
            try:
                if os_type() == "linux":
                    # Linux 上，可以通过发送 SIGINT 信号（通常由 Ctrl+C 触发）来终止进程
                    os.kill(self.option_dict["scrcpy_process"].pid, signal.SIGINT)
                elif os_type() == "windows":
                    # 在 Windows 上，可以通过发送 CTRL_C_EVENT 信号( Ctrl+C)来终止进程
                    os.kill(self.option_dict["scrcpy_process"].pid, signal.CTRL_C_EVENT)
                    # os.killpg(self.scrcpy_process.pid, signal.CTRL_C_EVENT)
                    # ctypes.windll.kernel32.GenerateConsoleCtrlEvent(0, self.scrcpy_process.pid)
            except Exception as e:
                logger.error(f"stop_recording error: {e}")
            self.option_dict["recording"] = False
            del self.option_dict["scrcpy_process"]

def run_cmd():
    parser = argparse.ArgumentParser()
    # 给这个解析对象添加命令行参数
    parser.add_argument('-s', '--serial', type=str, metavar='', default='',
                        required=False, help='Device index in the configuration file')
    parser.add_argument('-r', '--recording', type=int, default=0,metavar='',
                        required=False,  help='An integer flag (0 or 1) to enable screen recording')
    args = parser.parse_args()  # 获取所有参数
    serial = args.serial
    recording = bool(args.recording)

    u2 = UiAuto2Bar(serial=serial, recording=recording)
    u2.device.app_start("com.android.settings")
    u2.check_with_scroll(text="特色功能")
    u2.device.press("home")
    u2.device.app_stop("com.android.settings")


def test_uiauto2_bar():
    ui2device = UiAuto2Bar()
    device = ui2device.device
    ui2device.device.open_notification()    #  打开下拉通知栏
    ui2device.device.press("home")
    ui2device.device.open_quick_settings()  # 打开下拉菜单
    ui2device.get_info()
    ui2device.swipe("bottom",0.5)
    ui2device.dock_swipe()
    ui2device.device.open_url('http://www.baidu.com')  # 打开默认浏览器访问百度网页
    ui2device.device(resourceId="android:id/input").click()
    ui2device.start_recording()
    ui2device.stop_recording()
    # ui2device.screen_shot()
    # ui2device.device.clipboard="应用锁"
    ui2device.device(resourceId="android:id/input").set_text("应用锁") # 输入文本
    ui2device.device(resourceId="android:id/input").send_keys("安全")
    ui2device.device.shell("input keyevent 279")
    ui2device.device.press("power") # 模拟按键
    ui2device.device.press("home")
    device.swipe_ext('up')  # up, down, left, right
    ui2device.device().pinch_in()
    ui2device.device().pinch_out()
    device().gesture((300,1000),(600,1000),(300,1500),(600,1500))   # 双指滑动
    device(description="描述内容").click_exists(timeout=5)
    ui2device.device(scrollable=True).scroll.toEnd()
    ui2device.device(scrollable=True).scroll.toBeginning(steps=50)
    ui2device.device(scrollable=True).scroll.to(text="安全")
    device.app_start(package_name="com.android.settings")
    device.app_stop(package_name="com.android.settings")
    device.set_input_ime(True)  # 输入法启用
    device.set_input_ime(False)
    device(resourceId="android:id/title").exists(timeout=3)
    device(resourceId="android:id/title").wait(exists=True,timeout=3)
    device.exists(scrollable=True, text="安全")

    xpath1 = f'//*[@text="自动切换"]/../../..//*[@resource-id="android:id/widget_frame"]'
    xpath1 = f'//*[@text="自动切换"]/../../..//android.widget.Switch'

    ui2device.check_switch_checkbox(text_before="抬起亮屏",checkbox_name="android.widget.CheckBox")
    ui2device.switch_checkbox(text_before="抬起亮屏",checkbox_name="android.widget.CheckBox", enabled=True)

    points =[
        (250, 2060), (250, 1770), (250, 1482), (540, 1768),
        (828, 1482), (828, 1770), (828, 2060)
    ]
    device.swipe_points(points)
    device()

    ui2device.device.app_info("com.android.settings")

    ui2device.device(resourceId="android:id/title",instance=0).get_text()
    eles = ui2device.device.xpath("//*[@resource-id='android:id/title']").all()


    ui2device.find_elements(resourceId="android:id/title")
    ui2device.find_elements(xpath="//*[@resource-id='android:id/title']")
    ui2device.find_elements(resourceId="android:id/title")
    ui2device.get_attribs(xpath="//*[@resource-id='android:id/title']")
    ui2device.get_attribs(xpath=xpath1)
    ui2device.get_attribs(resourceId="android:id/title")
    ui2device.check_with_scroll(text="特色功能")
    ui2device.check_with_scroll(direct="top",text="特色功能")


# https://blog.csdn.net/zh6526157/article/details/129659343
'''
class UiImageAutomator(object):
    """
    基于图像识别操作的封装类
    """

    def __init__(self, device_sn):
        """
        初始化函数
        :param device_sn: 设备序列号
        """
        self.d = u2.connect(device_sn)
        self.width, self.height = self.d.window_size()

    def click_image(self, image_path, timeout=10):
        """
        点击指定图片
        :param image_path: 图片路径
        :param timeout: 超时时间（秒），默认为10秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            try:
                img = cv2.imread(image_path, 0)
                img_width, img_height = img.shape[::-1]
                screen = self.d.screenshot(format='opencv')
                result = cv2.matchTemplate(screen, img, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                if max_val > 0.8:
                    x, y = max_loc[0] + img_width / 2, max_loc[1] + img_height / 2
                    self.d.click(x / self.width, y / self.height)
                    return True
            except Exception as e:
                print(e)

            time.sleep(1)

    def click_image_until(self, image_path, until_image_path, timeout=30):
        """
        点击指定图片，直到出现目标图片
        :param image_path: 图片路径
        :param until_image_path: 目标图片路径
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if self.is_image_exist(until_image_path):
                return True

            self.click_image(image_path, 1)

    def click_image_times(self, image_path, times=1):
        """
        点击指定图片，指定次数
        :param image_path: 图片路径
        :param times: 点击次数，默认为1次
        :return: True/False
        """
        for i in range(times):
            if not self.click_image(image_path):
                return False

        return True

    def click_image_until_gone(self, image_path, timeout=30):
        """
        点击指定图片，直到该图片消失
        :param image_path: 图片路径
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if not self.is_image_exist(image_path):
                return True

            self.click_image(image_path, 1)

    def click_image_until_color(self, image_path, color, threshold=10, timeout=30):
        """
        点击指定图片，直到该图片上某一像素点的颜色与指定颜色相似
        :param image_path: 图片路径
        :param color: 指定颜色，格式为(B, G, R)
        :param threshold: 相似度阈值，默认为10
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            try:
                img = cv2.imread(image_path)
                h, w, _ = img.shape
                center_color = img[h // 2, w // 2]
                if abs(center_color[0] - color[0]) <= threshold and abs(
                        center_color[1] - color[1]) <= threshold and abs(center_color[2] - color[2]) <= threshold:
                    self.click_image(image_path, 1)
                    return True
            except Exception as e:
                print(e)

            time.sleep(1)

    def click_image_until_color_gone(self, image_path, color, threshold=10, timeout=30):
        """
        点击指定图片，直到该图片上某一像素点的颜色与指定颜色不再相似
        :param image_path: 图片路径
        :param color: 指定颜色，格式为(B, G, R)
        :param threshold: 相似度阈值，默认为10
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            try:
                img = cv2.imread(image_path)
                h, w, _ = img.shape
                center_color = img[h // 2, w // 2]
                if abs(center_color[0] - color[0]) > threshold or abs(center_color[1] - color[1]) > threshold or abs(
                        center_color[2] - color[2]) > threshold:
                    return True
            except Exception as e:
                print(e)

            self.click_image(image_path, 1)

    def click_image_until_text(self, image_path, text, threshold=0.7, timeout=30):
        """
        点击指定图片，直到该图片上出现指定文本
        :param image_path: 图片路径
        :param text: 指定文本
        :param threshold: 相似度阈值，默认为0.7
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if self.is_text_exist(image_path, text, threshold):
                self.click_image(image_path, 1)
                return True

            time.sleep(1)

    def click_image_until_text_gone(self, image_path, text, threshold=0.7, timeout=30):
        """
        点击指定图片，直到该图片上不再出现指定文本
        :param image_path: 图片路径
        :param text: 指定文本
        :param threshold: 相似度阈值，默认为0.7
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if not self.is_text_exist(image_path, text, threshold):
                return True

            self.click_image(image_path, 1)

    def click_text(self, text, timeout=10):
        """
        点击指定文本
        :param text: 指定文本
        :param timeout: 超时时间（秒），默认为10秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            try:
                self.d(text=text).click()
                return True
            except Exception as e:
                print(e)

            time.sleep(1)

    def click_text_until(self, text, until_image_path, timeout=30):
        """
        点击指定文本，直到出现目标图片
        :param text: 指定文本
        :param until_image_path: 目标图片路径
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if self.is_image_exist(until_image_path):
                return True

            self.click_text(text, 1)

    def click_text_times(self, text, times=1):
        """
        点击指定文本，指定次数
        :param text: 指定文本
        :param times: 点击次数，默认为1次
        :return: True/False
        """
        for i in range(times):
            if not self.click_text(text):
                return False

        return True

    def click_text_until_gone(self, text, timeout=30):
        """
        点击指定文本，直到该文本消失
        :param text: 指定文本
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if not self.is_text_exist(text):
                return True

            self.click_text(text, 1)

    def click_text_until_color(self, text, color, threshold=10, timeout=30):
        """
        点击指定文本，直到该文本上某一像素点的颜色与指定颜色相似
        :param text: 指定文本
        :param color: 指定颜色，格式为(B, G, R)
        :param threshold: 相似度阈值，默认为10
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            try:
                center_color = self.get_text_center_color(text)
                if abs(center_color[0] - color[0]) <= threshold and abs(
                        center_color[1] - color[1]) <= threshold and abs(center_color[2] - color[2]) <= threshold:
                    self.click_text(text, 1)
                    return True
            except Exception as e:
                print(e)

            time.sleep(1)

    def click_text_until_color_gone(self, text, color, threshold=10, timeout=30):
        """
        点击指定文本，直到该文本上某一像素点的颜色与指定颜色不再相似
        :param text: 指定文本
        :param color: 指定颜色，格式为(B, G, R)
        :param threshold: 相似度阈值，默认为10
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            try:
                center_color = self.get_text_center_color(text)
                if abs(center_color[0] - color[0]) > threshold or abs(center_color[1] - color[1]) > threshold or abs(
                        center_color[2] - color[2]) > threshold:
                    return True
            except Exception as e:
                print(e)

            self.click_text(text, 1)

    def click_text_until_text(self, text, until_text, threshold=0.7, timeout=30):
        """
        点击指定文本，直到该文本下出现指定文本
        :param text: 指定文本
        :param until_text: 目标文本
        :param threshold: 相似度阈值，默认为0.7
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if self.is_text_exist(text) and self.is_text_exist(text, until_text, threshold):
                self.click_text(text, 1)
                return True

            time.sleep(1)

    def click_text_until_text_gone(self, text, until_text, threshold=0.7, timeout=30):
        """
        点击指定文本，直到该文本下不再出现指定文本
        :param text: 指定文本
        :param until_text: 目标文本
        :param threshold: 相似度阈值，默认为0.7
        :param timeout: 超时时间（秒），默认为30秒
        :return: True/False
        """
        start_time = time.time()

        while True:
            current_time = time.time()
            if current_time - start_time > timeout:
                print("Timeout")
                return False

            if not self.is_text_exist(text, until_text, threshold):
                return True

            self.click_text(text, 1)

    def get_text_center_color(self, text):
        """
        获取指定文本中心像素点颜色
        :param text: 指定文本
        :return: 颜色，格式为(B, G, R)
        """
        bounds = self.d(text=text).info['bounds']
        x = (bounds['left'] + bounds['right']) / 2
        y = (bounds['top'] + bounds['bottom']) / 2
        screen = self.d.screenshot(format='opencv')
        return screen[int(y), int(x)]

    def is_image_exist(self, image_path, threshold=0.8):
        """
        判断指定图片是否存在
        :param image_path: 图片路径
        :param threshold: 相似度阈值，默认为0.8
        :return: True/False
        """
        try:
            img = cv2.imread(image_path, 0)
            img_width, img_height = img.shape[::-1]
            screen = self.d.screenshot(format='opencv')
            result = cv2.matchTemplate(screen, img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > threshold:
                return True
        except Exception as e:
            print(e)

        return False

    def is_text_exist(self, text, other_text=None, threshold=0.7):
        """
        判断指定文本是否存在
        :param text: 指定文本
        :param other_text: 其他文本，用于判断指定文本下是否出现了目标文本，默认为None
        :param threshold: 相似度阈值，默认为0.7
        :return: True/False
        """
        try:
            if other_text is None:
                self.d(text=text)
                return True
            else:
                self.d(text=text).down(text=other_text)
                return True
        except Exception as e:
            print(e)

        return False

    def long_click_image(self, image_path, duration=1):
        """
        长按指定图片
        :param image_path: 图片路径
        :param duration: 长按时间（秒），默认为1秒
        :return: True/False
        """
        try:
            img = cv2.imread(image_path, 0)
            img_width, img_height = img.shape[::-1]
            screen = self.d.screenshot(format='opencv')
            result = cv2.matchTemplate(screen, img, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            if max_val > 0.8:
                x, y = max_loc[0] + img_width / 2, max_loc[1] + img_height / 2
                self.d.long_click(x / self.width, y / self.height, duration)
                return True
        except Exception as e:
            print(e)

        return False

    def long_click_text(self, text, duration=1):
        """
        长按指定文本
        :param text: 指定文本
        :param duration: 长按时间（秒），默认为1秒
        :return: True/False
        """
        try:
            self.d(text=text).long_click(duration=duration)
            return True
        except Exception as e:
            print(e)

        return False
'''

if __name__ == "__main__":
    # ui2 = UiAuto2Bar()
    # ui2.get_info()
    # test_uiauto2_bar()
    run_cmd()


