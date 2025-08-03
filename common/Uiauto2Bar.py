
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
        self.device.wait_timeout = 3  # 设置默认元素等待超时（秒）
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
        # 保持屏幕常亮
        self.device.shell("svc power stayon true")
    def stop_week(self):
        # 关闭屏幕常亮
        self.device.shell("svc power stayon false")
    def get_info(self):
        print("-"*20)
        print(self.device.info,
              self.device.device_info,
              self.device.app_current(),  # 获取当前应用包名，Activity名称
              sep="\n")
        # self.device.dump_hierarchy()    # 界面信息树

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

class Uiauto2Watcher:
    def __init__(self, device: u2.Device):
        self.device = device
        self.watchers = {}
        self.ctx = self.device.watch_context()

    def add_watcher(self, name: str, xpath: str, callback: callable = None):
        """
        添加一个 watcher

        :param name: watcher 的名称
        :param selector: 匹配元素的选择器，例如 {"text": "安全"}
        :param callback: 匹配成功时执行的回调函数
        """
        watcher = self.ctx.when(xpath=xpath)
        if callback:
            watcher.click(callback=callback)
        else:
            watcher.click()
        self.watchers[name] = watcher
        return self

    def remove_watcher(self, name: str):
        """
        移除指定名称的 watcher

        :param name: watcher 的名称
        """
        if name in self.watchers:
            # 虽然 watch_context 没有直接的移除方法，但可以重新创建上下文来清除
            del self.watchers[name]
            self.ctx = self.device.watch_context()
            for watcher_name, watcher in self.watchers.items():
                self.ctx.when(**watcher.selector).click()
            logger.info(f"Removed watcher: {name}")
        else:
            logger.warning(f"Watcher {name} not found")

    def start_watchers(self):
        """
        启动所有 watcher
        """
        self.ctx.start()
        logger.info("Started all watchers")

    def stop_watchers(self):
        """
        停止所有 watcher
        """
        self.ctx.stop()
        logger.info("Stopped all watchers")

    def list_watchers(self) -> list:
        """
        列出所有 watcher 的名称

        :return: 包含所有 watcher 名称的列表
        """
        return list(self.watchers.keys())

    def wait_stable(self, timeout: float = None):
        """
        等待界面稳定，直到没有弹窗

        :param timeout: 超时时间，单位为秒
        """
        self.ctx.wait_stable(timeout=timeout)
        logger.info("Interface is stable")



def mtest_uiauto2_bar():
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


if __name__ == "__main__":
    # ui2 = UiAuto2Bar()
    # ui2.get_info()
    # mtest_uiauto2_bar()
    # run_cmd()

    driver = u2.connect("A86UUT1B26000479")

    # driver.swipe_ext("left", scale=0.9)  # 屏幕右滑，滑动距离为屏幕宽度的90%
    # driver.swipe_ext("right")  # 整个屏幕右滑动
    #
    # ctx = driver.watch_context()
    # ctx.when("安全").click()
    # ctx.wait_stable()  # 等待界面不再有弹窗
    # # 查看所有注册的Watcher：
    # ctx.start()
    # time.sleep(20)
    # ctx.stop()

    wa = Uiauto2Watcher(driver)
    wa.add_watcher("应用watcher", xpath="//*[@resource-id='android:id/title' and @text='应用']")
    wa.add_watcher("蓝牙watcher", xpath="//*[@resource-id='android:id/title' and @text='蓝牙']")
    wa.start_watchers()
    time.sleep(20)
    wa.stop_watchers()


