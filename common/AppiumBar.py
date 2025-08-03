
import os
import sys
import signal
import socket
import subprocess
import base64
import ctypes
import logging
import argparse
from selenium.webdriver.remote.client_config import ClientConfig
import time
import threading
from typing import Optional
from adbutils import adb
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.options.ios import XCUITestOptions
from appium.webdriver import WebElement
from appium.webdriver.appium_service import AppiumService
from appium.webdriver.common.appiumby import AppiumBy
from appium.webdriver.connectiontype import ConnectionType
# from appium.webdriver.common.touch_action import TouchAction # 2.x,3.x
from appium.webdriver.extensions.android.nativekey import AndroidKey
from appium.webdriver.webdriver import WebDriver
from selenium.common import TimeoutException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.actions import interaction
from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.mouse_button import MouseButton
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.support.abstract_event_listener import AbstractEventListener
from selenium.webdriver.support.event_firing_webdriver import EventFiringWebDriver
from selenium.webdriver.support.expected_conditions import presence_of_element_located, \
    presence_of_all_elements_located, invisibility_of_element_located
from selenium.webdriver.support.wait import WebDriverWait
from typing_extensions import List, Dict

# 命令行执行，将当前文件的上上级目录，及项目目录加入Python解释器在搜索模块时的路径列表当中
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if base_path not in sys.path:
    sys.path.append(base_path)
from common import the_paths
from common.AdbBar import AdbBar
from common.utils import exec_cmd, os_type, yaml_load, exec_subprocess

"""
运行环境：Appium v2.12.1; uiautomator2@3.8.1; Appium-Python-Client 4.2.1; selenium 4.25.0;
"""

# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

logger = logging.getLogger("AppiumBar")

class ServiceController:
    service_lst = []
    @classmethod
    def start_service(cls, serial):
        service = AppiumService()
        start_args = ["-a", "127.0.0.1", "-p", "4723", "--allow-inscure=adb_shell", "--base-path=/wd/hub"]
        # --use-plugins 加载对应的插件,指定设备类型
        # wincmd: appium server -a 127.0.0.1 -p 4723 --default-capabilities "{\"platformName\": \"Android\",\"udid\": \"\"}"
        service.start(args=start_args)
        cls.service_lst.append(service)
        return service

    @classmethod
    def stop_service(cls, service: AppiumService):
        service.stop()
        cls.service_lst.remove(service)

    @classmethod
    def stop_all_service(cls):
        for service in cls.service_lst:
            service.stop()
        cls.service_lst.clear()

class AppiumBar:
    config_data = None

    def __init__(self):
        self.service: AppiumService = None  # Appium Service 可以单独拎出来
        self.driver: WebDriver = None
        self.event_listener = None
        self.serial = None
        self.option_dict = dict()

    @classmethod
    def load_config(cls):
        config_data = yaml_load(config_file=the_paths.get("config") / "appium_config.yml")
        AppiumBar.config_data = config_data
        return config_data

    def init_works(self, device_index=0, appium_opts: dict = None, driver_opts: dict = None):
        self.service = self.__start_service(device_index, custom_opts=appium_opts)
        self.driver = self.__create_driver(device_index, custom_opts=driver_opts)

        self.judge_device()
        # 截屏和录屏判断 启用
        if self.option_dict["screenshot"]:
            self.enable_event_listener(ExceptListener())
        if self.option_dict["recording"]:
            self.start_recording(use_scrcpy=False)

    def clean_works(self):
        #
        if "screenshot" in self.option_dict and self.option_dict["screenshot"]:
            self.disable_event_listener()
            self.option_dict["screenshot"] = False
        if "recording" in self.option_dict and self.option_dict["recording"]:
            self.stop_recording()
            self.option_dict["recording"] = False

        self.__close_driver()
        self.__stop_service()

    def __start_service(self, index: int=0, custom_opts: dict = None) -> AppiumService:
        """
        启动Appium服务器，并返回进程对象。
        :param index: appium_config.yml 配置中的 设备序列
        :param desc: appium_config.yml 配置中的 备注描述
        :param cust_opts: 自定 appium 启动项
        :return:
        """
        config_data = AppiumBar.config_data if AppiumBar.config_data else AppiumBar.load_config()
        if len(config_data) <= index:
            logger.error("The device index is out of range.")
        host = config_data[index]['host']
        port = config_data[index]['port']
        base_path = config_data[index]['base_path']
        log_path = config_data[index]['log_path']
        # serial = config_data[index]['desired_caps']['udid']
        devices = AdbBar.get_connected_devices()
        logger.info(f"The devices is currently connected: {devices}")
        try:
            args_str = f'-a {host} -p {port} --relaxed-security'    # --allow-insecure=adb_shell: 仅会开启adb shell的功能
            if base_path:
                args_str += f' -pa {base_path}'
            if log_path:
                args_str += f' -g {log_path}'
            if custom_opts:
                for k, v in custom_opts.items():
                    args_str += f' -{k} {v}'
            # print(f"启动参数：{args_str}")
            logger.info(f"Appium服务启动中，启动参数：{args_str}")
            self.service = AppiumService()

            # 线程间的通信方式，创建一个事件对象，用于通知子线程停止
            event = threading.Event()
            # 创建并启动子线程
            thread = threading.Thread(target=self.__waitting_service, args=(event, 3.5))
            thread.start()

            self.service.start(
                # Check the output of `appium server --help` for the complete list of
                # server command line arguments
                args=args_str.split(),
                timeout_ms=20000,
            )
            event.wait()  # 等待事件被设置
            thread.join()   # 等待子线程结束

            return self.service
        except Exception as e:
            logger.error(f"启动Appium服务器时出错：{e}")
        return None

    def __waitting_service(self, event, timeout=3.5):
        start_time = time.time()
        while True:
            # 检查是否应该停止线程
            if event.is_set():
                logger.info(f"{time.time() - start_time:.2f}s 内 Appium Service 已正常启动。。。")
                break
            # 检查是否超时
            if time.time() - start_time > timeout:
                logger.error(f"{timeout}s 内 Appium Service 未正常启动，终止运行！")
                break
            # 这里添加你的检查逻辑，检查某个条件是否满足
            if self.service.is_running:
                event.set()  # 设置事件，通知子线程停止
            # 休眠一会儿再进行下一次检查
            logger.info(f"{self.service.is_running=}")
            time.sleep(0.5)
    def __stop_service(self):
        """
        终止指定的Appium后台进程。
        :param service: 要终止的service对象
        """
        if self.service is not None:
            self.service.stop()
        # kill_cmd = {"windows": "taskkill /f /im node.exe", "linux": "pkill node"}
        # exec_cmd(kill_cmd[os_type()])
        logger.info("Appium 服务终止运行。。。")

    def judge_device(self):
        devices = AdbBar.devices
        self.serial = self.driver.caps.get('udid', '')
        if not self.serial and len(devices) > 0:
            self.serial = devices[0]
        logger.info(f"The device in use is {self.serial}")

    def is_port_available(self, host, port):
        """检测端口是否可用"""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:  # Port is open
                return False
        return True

    def release_port(self, port):
        """释放给定的TCP端口"""
        check_cmd = {"windows": f"netstat -ano| findstr {port}", "linux": f"netstat -anp| grep :{port}"}
        result = exec_cmd(check_cmd[os_type()])
        if str(port) in result:
            pid = result.strip().split(" ")[-1]
            kill_cmd = {"windows": f"taskkill -f -pid {pid}", "linux": f"kill -9 {pid}"}
            exec_cmd(kill_cmd[os_type()])
            return True
        return True

    def get_info(self):
        # 获取应用信息
        logger.info(f"设置配置项：{self.driver.caps}")
        # logger.info(self.driver.get_settings())
        # print(self.driver.page_source)


    def __create_driver(self, index: int=0, custom_opts: dict=None, setting: dict=None):
        config_data = AppiumBar.config_data if AppiumBar.config_data else AppiumBar.load_config()
        if len(config_data)<=0:
            raise Exception("配置项内容为空！")
        if len(config_data)<index:
            raise Exception("该索引 配置项不存在！")
        desired_caps = config_data[index]['desired_caps']
        host = config_data[index]['host']
        port = config_data[index]['port']
        base_path = config_data[index]['base_path']
        self.option_dict["screenshot"] = config_data[index]['screenshot']
        self.option_dict["recording"] = config_data[index]['recording']
        platform_name = desired_caps.get("platformName", "Android")
        options = None
        if platform_name == "Android":
            # options = AppiumOptions()
            options = UiAutomator2Options()  # UiAutomator2Options()
        elif platform_name == "iOS":
            options = XCUITestOptions()
        if custom_opts is not None:
            desired_caps.update(custom_opts)
        logger.info(f"{config_data=}")
        logger.info(f"{desired_caps=}")
        dev_name = adb.device(serial=self.serial).shell("getprop ro.config.marketing_name") # getprop ro.product.marketname
        and_version = adb.device(serial=self.serial).shell("getprop ro.build.version.release")
        # 加载测试的配置选项和参数(Capabilities配置)
        options.load_capabilities(desired_caps)
        command_executor = f"http://{host}:{port}"
        if base_path:
            command_executor += f"{base_path}"
        from appium import version as appium_version
        if appium_version.version >= '4.3.0':
            client_config = ClientConfig(remote_server_addr=command_executor,ignore_certificates=True)
            self.driver = webdriver.Remote(command_executor=command_executor, options=options,
                                           client_config=client_config)
        else:
            self.driver = webdriver.Remote(command_executor=command_executor, options=options)
        if setting:
            # self.driver.update_settings({"waitForIdleTimeout": 2,"enableMultipleWindows": True})
            self.driver.update_settings(setting)
        return self.driver

    def __close_driver(self):
        if self.driver:
            self.driver.quit()

    def start_activity(self, activity: str=""):
        """ adb shell am start -n com.android.settings/.HWSettings """
        exec_subprocess(f"adb -s {self.serial} shell am start -n {activity}")

    def shell(self, command: str):
        """
        运行移动端的shell指令
        :param command: 比如：wm size

        """
        if "shell" not in command:
            mobile_val = "shell"
        result = self.driver.execute_script(f'mobile: {mobile_val}', {
            'command': command.split()[0],
            'args': command.split()[1:],
            'includeStderr': False,
            'timeout': 5000
        })
        return result

    def get_attributes(self, by: str, value: str, index:int=0) -> dict:
        # 获取元素的所有属性信息
        attrs = ['resource-id', 'text', 'name', 'class', 'package', 'content-desc', 'enabled', 'checkable', 'checked',
                 'clickable', 'enabled', 'focusable', 'focused', 'scrollable', 'long-clickable', 'password', 'selected',
                 'bounds']
        elements = self.driver.find_elements(by,value)
        if len(elements) == 0:
            logger.error(f"No element: {value}")
        attributes = {attr: elements[index].get_attribute(attr) for attr in attrs}
        return attributes

    def continuous_drag(self, sx, sy, mx, my, ex, ey, pause_time=1.5, duration: int = 250):
        # 连续2次不间断拖拽
        actions = ActionChains(self.driver)

        actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, 'touch'), duration=duration)
        # actions.w3c_actions = ActionBuilder(driver, mouse= PointerInput(interaction.POINTER_MOUSE, "mouse"))

        actions.w3c_actions.pointer_action.move_to_location(x=sx, y=sy)
        actions.w3c_actions.pointer_action.pointer_down()
        # 使用pause方法代替time.sleep来实现长按
        actions.w3c_actions.pointer_action.pause(duration=pause_time)  # 暂停 1.5s
        actions.w3c_actions.pointer_action.move_to_location(x=mx, y=my)
        actions.w3c_actions.pointer_action.pause(duration=pause_time)
        actions.w3c_actions.pointer_action.move_to_location(x=ex, y=ey)
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def three_finger_slide(self, duration: int = 250):
        # 三指下滑
        distance = 300
        x1, y1 = 300, 500
        x2, y2 = 500, 600
        x3, y3 = 700, 700
        # 创建两个指针输入，代表两个手指
        pointer1 = PointerInput(interaction.POINTER_TOUCH, "touch1")
        pointer2 = PointerInput(interaction.POINTER_TOUCH, "touch2")
        pointer3 = PointerInput(interaction.POINTER_TOUCH, "touch3")

        # 创建动作链
        actions = ActionChains(self.driver)
        # 开始动作链
        actions.w3c_actions = ActionBuilder(self.driver, duration=duration)
        actions.w3c_actions._add_input(pointer1)
        actions.w3c_actions._add_input(pointer2)
        actions.w3c_actions._add_input(pointer3)

        # 第一个手指按下
        pointer1.create_pointer_move(x=x1, y=y1)
        pointer1.create_pointer_down(button=MouseButton.LEFT)
        pointer1.create_pause(pause_duration=1)
        # 第二个手指按下
        pointer2.create_pointer_move(x=x2, y=y2)
        pointer2.create_pointer_down(button=MouseButton.LEFT)
        pointer2.create_pause(pause_duration=1)
        # 第三个手指按下
        pointer3.create_pointer_move(x=x3, y=y3)
        pointer3.create_pointer_down(button=MouseButton.LEFT)
        pointer3.create_pause(pause_duration=1)
        # 两个手指同时移动
        pointer1.create_pointer_move(duration=180, x=x1, y=y1+distance)
        pointer2.create_pointer_move(duration=180, x=x2, y=y2+distance)
        pointer3.create_pointer_move(duration=180, x=x3, y=y3+distance)

        # 两个手指同时释放
        pointer1.create_pointer_up(button=MouseButton.LEFT)
        pointer2.create_pointer_up(button=MouseButton.LEFT)
        pointer3.create_pointer_up(button=MouseButton.LEFT)
        # 执行动作链
        actions.perform()

    def three_finger_tap(self):
        # 三指长按
        self.driver.tap(positions=[(300,500),(500,400),(700,500)], duration=2000)

    def drag_dock(self, duration: int=1000):
        # 模拟手动侧边栏滑动，从屏幕边缘开始的滑动操作
        screen_size = self.driver.get_window_size()
        # 定义滑动起始位置（左侧边缘）和结束位置（屏幕中心）
        start_x = screen_size['width']*0.998
        start_y = screen_size['height']*0.5
        end_x = screen_size['width']*0.5
        end_y = screen_size['height']*0.5

        pointer1 = PointerInput(interaction.POINTER_TOUCH, "touch1")
        # 创建动作链
        actions = ActionChains(self.driver)
        # 开始动作链
        actions.w3c_actions = ActionBuilder(self.driver)
        actions.w3c_actions._add_input(pointer1)
        # 第一个手指按下
        pointer1.create_pointer_move(x=start_x, y=start_y, duration=duration)
        pointer1.create_pointer_down(button=MouseButton.LEFT)

        pointer1.create_pointer_move(x=end_x, y=end_y, duration=duration)
        pointer1.create_pointer_up(button=MouseButton.LEFT)

        # 执行动作链
        actions.perform()

    def double_click(self, x=400, y=500, ele: WebElement=None):
        actions = ActionChains(self.driver)
        if ele:
            actions.double_click(ele)
        else:
            self.driver.tap(positions=[(x,y)])
            self.driver.tap(positions=[(x,y)])

    def multiple_swipe(self, positions:tuple, duration: int = 250):
        nums = len(positions)
        if nums==0:
            return
        actions = ActionChains(self.driver)
        actions.w3c_actions = ActionBuilder(self.driver, mouse=PointerInput(interaction.POINTER_TOUCH, 'touch'), duration=duration)

        actions.w3c_actions.pointer_action.move_to_location(x=positions[0][0],y=positions[0][1])
        actions.w3c_actions.pointer_action.pointer_down()
        if nums > 1:
            for i in range(1, nums):
                actions.w3c_actions.pointer_action.move_to_location(x=positions[i][0], y=positions[i][1])
        actions.w3c_actions.pointer_action.release()
        actions.perform()

    def press_key(self, key: str=""):
        key_dict = {
            "home": AndroidKey.HOME, "back": AndroidKey.BACK, "power": AndroidKey.POWER,
            "volume_up": AndroidKey.VOLUME_UP, "volume_down": AndroidKey.VOLUME_DOWN
        }
        self.driver.press_keycode(key_dict[key])

    def wait_element(self,by:str=AppiumBy.ID, value: Optional[str] = None, expect: bool = True, timeout: float=3):
        # 等待元素出现或消失
        locator = (by, value)
        try:
            if expect:  # 等待出现
                WebDriverWait(self.driver, timeout=timeout).until(presence_of_element_located(locator))
            else:     # 等待消失
                WebDriverWait(self.driver, timeout=timeout).until(invisibility_of_element_located(locator))
            return True
        except TimeoutException:
            logger.error(f"{value}元素不存在或不可见")
            return False

    def check_toast(self, toast_message="", fuzzy=False,timeout=3):
        try:
            # 等待Toast出现，这里假设Toast内容是“Toast message”，需要根据实际情况修改
            if fuzzy:
                toast_locator = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().textContains("{}")'.format(toast_message))
            else:
                toast_locator = (AppiumBy.ANDROID_UIAUTOMATOR, 'new UiSelector().text("{}")'.format(toast_message))
            # 隐式等待，presence_of_element_located，presence_of_all_elements_located
            toast_element = WebDriverWait(self.driver, timeout=timeout).until(presence_of_element_located(toast_locator))
            logger.info(f"检测到Toast弹窗内容：{toast_element.text}")
            return True
        except Exception as e:
            logger.error(f"未检测到Toast弹窗或发生错误：{e}")
            return False

    def check_element_exist(self, by:str=AppiumBy.ID, value: Optional[str] = None, timeout: float=3):
        try:
            locator = (by,value)
            if timeout <= 0:
                self.driver.find_element(*locator)
            else:
                WebDriverWait(self.driver, timeout=timeout).until(presence_of_element_located(locator))
            logger.info(f"元素{value}存在且可见")
            return True
        except TimeoutException:
            logger.error(f"{value}元素不存在或不可见")
            return False
        except NoSuchElementException:
            logger.error(f"{value}元素不存在或不可见")
            return False

    def click_element(self, by: str = AppiumBy.ID, value: Optional[str] = None, timeout: float = 3, instance: int=0):
        try:
            locator = (by, value)
            elements = WebDriverWait(self.driver, timeout=timeout).until(presence_of_all_elements_located(locator))
            if elements and len(elements) > instance:
                elements[instance].click()
            logger.info(f"发现元素{value}，并点击")

            return True
        except TimeoutException:
            logger.error("等待超时，元素不存在或不可见")
            return False

    def pinch(self, percent:float=0.5, element=None):
        # 桌面 双指捏合
        if element:
            size = element.size  # 获取元素的尺寸信息
            position = element.location # 获取元素的坐标
        else:
            size = self.driver.get_window_size()
            position = {'x': size['width']*0.2, 'y': size['height']*0.2}
        x_insrance = int(size['width'] * (1-0.2) * percent)  # 计算缩放中心的横坐标
        y_instance = int(size['height'] * (1-0.2) * percent)  # 计算缩放中心的纵坐标

        start_x1, start_y1 = position['x'], position['y']
        end_x1, end_y1 = start_x1 + x_insrance, start_y1 + y_instance

        start_x2, start_y2 = size['width']-position['x'], size['height']-position['y']
        end_x2, end_y2 = start_x2 - x_insrance, start_y2 - y_instance
        logger.info(f"{size=}, {position=}")
        logger.info(f"{start_x1=}, {start_y1=}, {end_x1=}, {end_y1=}")
        logger.info(f"{start_x2=}, {start_y2=}, {end_x2=}, {end_y2=}")

        pointer1 = PointerInput(interaction.POINTER_TOUCH, "touch1")
        pointer2 = PointerInput(interaction.POINTER_TOUCH, "touch2")

        actions = ActionChains(self.driver)
        # 开始动作链
        actions.w3c_actions = ActionBuilder(self.driver)
        actions.w3c_actions._add_input(pointer1)
        # 第一个手指按下
        pointer1.create_pointer_move(x=start_x1, y=start_y1)
        pointer1.create_pointer_down(button=MouseButton.LEFT)
        pointer1.create_pointer_move(x=end_x1, y=end_y1)
        pointer1.create_pointer_up(button=MouseButton.LEFT)

        actions.w3c_actions._add_input(pointer2)
        pointer2.create_pointer_move(x=start_x2, y=start_y2)
        pointer2.create_pointer_down(button=MouseButton.LEFT)
        pointer2.create_pointer_move(x=end_x2, y=end_y2)
        pointer2.create_pointer_up(button=MouseButton.LEFT)

        actions.perform()

    def pinout(self, percent:float=0.5, element=None):
        # 桌面 双指放大
        if element:
            size = element.size  # 获取元素的尺寸信息
            position = element.location # 获取元素的坐标
        else:
            size = self.driver.get_window_size()
            position = {'x': size['width']*0.2, 'y': size['height']*0.2}
        x_insrance = int(size['width'] * (1-0.2) * percent)  # 计算缩放中心的横坐标
        y_instance = int(size['height'] * (1-0.2) * percent)  # 计算缩放中心的纵坐标

        end_x1, end_y1 = position['x'], position['y']
        start_x1, start_y1 = end_x1 + x_insrance, end_y1 + y_instance

        end_x2, end_y2 = size['width']-position['x'], size['height']-position['y']
        start_x2, start_y2 = end_x2 - x_insrance, end_y2 - y_instance
        logger.debug(f"{size=}, {position=}")
        logger.debug(f"{start_x1=}, {start_y1=}, {end_x1=}, {end_y1=}")
        logger.debug(f"{start_x2=}, {start_y2=}, {end_x2=}, {end_y2=}")

        pointer1 = PointerInput(interaction.POINTER_TOUCH, "touch1")
        pointer2 = PointerInput(interaction.POINTER_TOUCH, "touch2")

        actions = ActionChains(self.driver)
        # 开始动作链
        actions.w3c_actions = ActionBuilder(self.driver)
        actions.w3c_actions._add_input(pointer1)
        # 第一个手指按下
        pointer1.create_pointer_move(x=start_x1, y=start_y1)
        pointer1.create_pointer_down(button=MouseButton.LEFT)
        pointer1.create_pointer_move(x=end_x1, y=end_y1)
        pointer1.create_pointer_up(button=MouseButton.LEFT)

        actions.w3c_actions._add_input(pointer2)
        pointer2.create_pointer_move(x=start_x2, y=start_y2)
        pointer2.create_pointer_down(button=MouseButton.LEFT)
        pointer2.create_pointer_move(x=end_x2, y=end_y2)
        pointer2.create_pointer_up(button=MouseButton.LEFT)

        actions.perform()

    def get_screen_size(self):
        screen_size = self.driver.get_window_size()
        return screen_size['width'], screen_size['height']
    def is_edge(self, direct: str="bottom"):
        """
        :param direct: bottom, top, left, right
        :return:
        """

        x, y = self.get_screen_size()
        length = len(self.driver.page_source)
        page_data = self.driver.page_source[-length//4:]
        swipe_direct = {
            'bottom': (0.5*x,0.6*y,0.5*x,0.3*y),
            'top': (0.5*x,0.6*y,0.5*x,0.9*y),
            'left': (0.2*x,0.5*y,0.9*x,0.5*y),
            'right': (0.9*x,0.5*y,0.2*x,0.5*y),
        }
        self.driver.swipe(*swipe_direct[direct], duration=800)
        time.sleep(1)
        new_page_data = self.driver.page_source[-length // 4:]
        if new_page_data == page_data:
            return True
        return False


    def check_with_scroll(self, by: str = AppiumBy.ID, value: Optional[str] = None, direct:str="bottom",maxslipes: int=30, reverse_slip:bool=False):
        x, y = self.get_screen_size()
        swipe_direct = {
            'bottom': (0.5 * x, 0.6 * y, 0.5 * x, 0.3 * y),
            'top': (0.5 * x, 0.6 * y, 0.5 * x, 0.9 * y),
            'left': (0.2 * x, 0.5 * y, 0.9 * x, 0.5 * y),
            'right': (0.9 * x, 0.5 * y, 0.2 * x, 0.5 * y),
        }
        neg_direct = "top"
        if direct=="top":
            neg_direct = "bottom"
        elif direct=="left":
            neg_direct = "right"
        elif direct=="right":
            neg_direct = "left"
        if self.check_element_exist(by, value, timeout=0):
            return True
        if reverse_slip:
            for _ in range(3):
                self.driver.swipe(*swipe_direct[neg_direct])
                time.sleep(1)
                if self.is_edge(neg_direct):
                    break

        for _ in range(maxslipes):
            if self.check_element_exist(by, value, timeout=0):
                return True
            self.driver.swipe(*swipe_direct[direct], duration=800)
            time.sleep(1)
            if self.check_element_exist(by, value, timeout=0):
                return True
            if self.is_edge(direct):
                break

        return False

    def enable_event_listener(self, listener=None):
        logger.info(f"正在启动事件监听。。。")
        # listener = CustomListener()
        # listener = ExceptListener()
        self.event_driver = EventFiringWebDriver(self.driver, listener)
        self.driver = self.event_driver
        # 现在使用event_driver来执行操作，MyListener将会监听事件

    def disable_event_listener(self):
        logger.info(f"正在关闭事件监听。。。")
        self.driver = self.event_driver.wrapped_driver
        self.event_driver = None

    def start_thread_func(self, name=None, target: callable=None, args=(), kwargs=None):
        logger.info(f"正在启动后台线程处理。。。")
        thread = ApThread(name=name, target=target, args=args, kwargs=kwargs, daemon=True)
        # daemon = True  # 设置为守护线程
        thread.start()
        return thread

    def check_switch_checkbox(self, text_before="蓝牙", id_before="android:id/title", checkbox_id="android:id/checkbox"):
        # 检查 横切 按钮的 状态
        # check_switch_checkbox("蓝牙", checkbox_classname="android.widget.Switch")
        status_dict = {
            'true': True,
            'false': False
        }
        locator1 = (AppiumBy.XPATH, f'//*[@text="{text_before}" and @resource-id="{id_before}"]/../..//*[@resource-id="{checkbox_id}"]')
        locator2 = (AppiumBy.XPATH, f'//*[@text="{text_before}" and @resource-id="{id_before}"]/../../..//*[@resource-id="{checkbox_id}"]')
        if text_before and not id_before:
            locator1 = (AppiumBy.XPATH, f'//*[@text="{text_before}"]/../..//*[@resource-id="{checkbox_id}"]')
            locator2 = (AppiumBy.XPATH, f'//*[@text="{text_before}"]/../../..//*[@resource-id="{checkbox_id}"]')
        elements = self.driver.find_elements(*locator1)
        index = 0
        if len(elements) == 0:
            elements = self.driver.find_elements(*locator2)
            if len(elements) == 0:
                logger.error("The checkbox element not found")
                return False, None
            else:
                return status_dict.get(elements[index].get_attribute('checked'), ''), elements[index]
        else:
            return status_dict.get(elements[index].get_attribute('checked'), ''), elements[index]

    def switch_checkbox_status(self, text_before="蓝牙",id_before="android:id/title",checkbox_id="android:id/checkbox",enabled=True):
        # 启动或关闭 横切 按钮
        status, ele = self.check_switch_checkbox(text_before=text_before, id_before=id_before,checkbox_id=checkbox_id)
        if not ele:
            return False
        if status != enabled:
            logger.info(f"The checkbox element is being {enabled}")
            ele.click()
            return enabled
        elif status == enabled:
            logger.info(f"The checkbox element has been {enabled}")
            return enabled

    def start_recording(self, use_scrcpy=False):
        logger.info("Start recording...")
        scrcpy_app = r"C:\MPrograms\Android\scrcpy-win64-v2.7\scrcpy.exe"
        out = exec_subprocess(f"adb -s {self.serial} shell which screenrecord")
        cur_time = self.driver.get_device_time("YYYY-MM-DD_HH-mm-ss")
        save_path = the_paths.get("logs") / f"{self.serial}-{cur_time}.mp4"
        try:
            if out and not use_scrcpy:
                self.driver.start_recording_screen()
                self.option_dict["record_video"] = save_path
                self.option_dict["recording"] = True
                return True
            else:
                self.option_dict["scrcpy_process"] = subprocess.Popen(
                f"{scrcpy_app} -s {self.serial} --max-size=1920 --max-fps=20 --video-bit-rate 6M --record={save_path}",
                                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True) # --no-display
                logger.info(f"recording savepath: {save_path}")
                self.option_dict["recording"] = True
                return True
        except Exception as e:
            logger.error(f"start_recording error: {e}")
        self.option_dict["recording"]=False
        return False

    def stop_recording(self):
        logger.info("Stopping recording...")
        if self.option_dict["recording"] and "scrcpy_process" not in self.option_dict:
            video_base64 = self.driver.stop_recording_screen()
            # 将base64编码的视频内容解码为二进制数据
            video_data = base64.b64decode(video_base64)
            video_file_name = self.option_dict["record_video"]
            with open(video_file_name, 'wb') as video_file:
                video_file.write(video_data)
            self.option_dict["recording"] = False
            return True
        if self.option_dict["recording"] and "scrcpy_process"  in self.option_dict:
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

class ApThread(threading.Thread):
    def run(self):
        try:
            if self._target:
                self.result = self._target(*self._args, **self._kwargs)
        finally:
            # Avoid a refcycle if the thread is running a function with
            # an argument that has a member that points to the thread.
            del self._target, self._args, self._kwargs

    def get_result(self):
        threading.Thread.join(self)  # 等待线程执行完毕
        try:
            return self.result
        except Exception:
            return None

class ExceptListener(AbstractEventListener):
    def __init__(self):
        self.exception_handled = False  # 设置标志

    def on_exception(self, exception, driver) -> None:
        if not self.exception_handled:
            self.exception_handled = True
            cur_time = driver.get_device_time("YYYY-MM-DD_HH-mm-ss")
            serial = driver.caps.get('udid', '')
            save_path = the_paths.get("logs") / f"{serial}_{cur_time}.png"
            driver.save_screenshot(save_path)
            logger.info(f"执行异常，当时截图路径: {save_path}")
            # 设置标志，避免重复处理

        # 重置标志，以便下次异常可以处理
        threading.Timer(1.5, self.reset_exception_flag).start()

    def reset_exception_flag(self):
        self.exception_handled = False

class CustomListener(AbstractEventListener):
    def before_find(self, by, value, driver) -> None:
        logger.info(f"正在查找元素: {by}={value}")

    def after_find(self, by, value, driver) -> None:
        logger.info(f"发现监听元素: {value}, 处理弹窗")
        elements = driver.find_elements(by, value)
        if len(elements) != 0:
            elements[0].click()


def cmd_run():

    parser = argparse.ArgumentParser()
    # 给这个解析对象添加命令行参数
    parser.add_argument('-i', '--index_device', type=int, metavar='', default=0,
                        required=False, help='Device index in the configuration file')
    args = parser.parse_args()  # 获取所有参数
    index_device = args.index_device
    app = AppiumBar()
    app.init_works(index_device)
    driver = app.driver
    driver.implicitly_wait(3)
    driver.swipe(300, 600, 300, 1800)
    app.clean_works()

class PopupWatcher(threading.Thread):
    def __init__(self, driver: WebDriver, check_interval: float = 2.0, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.driver = driver
        self.check_interval = check_interval
        self.running = True

        self.watch_rules = []

    def add_watch_rule(self, locator: tuple, action = None):
        """
        添加弹窗监听规则
        :param locator: 弹窗元素定位器
        :param action: 弹窗元素操作
        """
        self.watch_rules.append((locator, action))

    def run(self):
        while self.running:
            for locator, action in self.watch_rules:
                try:
                    # 显式等待弹窗元素可见
                    element = WebDriverWait(self.driver, 0.5).until(presence_of_element_located(locator))
                    # elements = self.driver.find_elements(*locator)
                    # element.click()
                    action(element)
                except:
                    pass
            time.sleep(self.check_interval)

    def stop(self):
        self.running = False


def watch_popup():
    app = AppiumBar()
    app.init_works()
    driver = app.driver
    watcher = PopupWatcher(driver=driver, check_interval=2)

    watcher.add_watch_rule(locator=(AppiumBy.XPATH,'//*[@text="更多连接"]'), action=lambda element: element.click())
    watcher.add_watch_rule(locator=(AppiumBy.XPATH,'//*[@text="智慧助手"]'), action=lambda element: element.click())

    watcher.start()

    time.sleep(20)

    watcher.stop()

if __name__ == '__main__':
    watch_popup()
    exit()
    # cmd_run()
    app = AppiumBar()
    app.init_works(1)
    driver = app.driver
    driver.implicitly_wait(1)
    # window_handles = driver.window_handles
    # print("活动窗口句柄列表:", window_handles)
    # 平板左侧栏定位失败
    # 切换上下文，切换到webview

    # #也可以通过名称来切换
    # #driver.switch_to.context("WEBVIEW_com.baidu.yuedu")
    # driver.switch_to.context(contexts[-1])
    # #获取web内容
    # source=driver.page_source
    # # 切回native
    # driver.switch_to.context(contexts[0])
    # driver.switch_to.context("NATIVE_APP") # 这样也是可以的

    driver.activate_app('com.android.settings')
    driver.activate_app('com.android.settings/.HWSettings')
    app.start_activity("com.android.settings/.HWSettings")
    locator = (AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().text("更多连接")')
    locator = (AppiumBy.XPATH,"//android.widget.TextView[contains(@text, '更多连接')]")
    locator = (AppiumBy.XPATH,'//*[@text="移动网络"]')

    eles = driver.find_elements(*locator)
    eles[0].click()
    app.check_switch_checkbox("抬起亮屏",checkbox_id="android:id/checkbox")
    app.switch_checkbox_status("勿扰模式",checkbox_id="android:id/checkbox")
    app.check_switch_checkbox("自动切换",checkbox_id="android:id/switch_widget")
    app.switch_checkbox_status("自动切换",checkbox_id="android:id/switch_widget",enabled=True)
    app.get_attributes(*locator)

    app.shell("ime list -s")
    app.pinch(percent=0.2)
    app.pinout(percent=0.2)

    app.wait_element(AppiumBy.XPATH, '//android.widget.Button[contains(@text,"手机登录")]', timeout=5)
    app.wait_element(AppiumBy.XPATH, '//android.widget.Button[contains(@text,"手机登录")]', expect=False,timeout=5)

    locator1 = (AppiumBy.XPATH, f'//*[@text="勿扰模式"]/../..//android.widget.CheckBox')
    locator2 = (AppiumBy.XPATH, f'//android.widget.TextView[@text="抬起亮屏"]/../../../android.widget.LinearLayout/android.widget.CheckBox[@resource-id="android:id/checkbox"]')
    driver.find_element(*locator1).click()
    # 定位相对于这个元素的其他控件，例如一个按钮
    button_element = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().resourceId("android:id/checkbox").instance(0)')  # .fromParent(UiSelector().text("静音模式"))
    # 父子定位
    button_element = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().className("android.widget.LinearLayout").instance(5).childSelector(description("悬浮通知"))')  #

    # 兄弟定位
    button_element = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().description("锁屏通知").fromParent(description("悬浮通知"))')

    button_element = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().className("android.widget.LinearLayout").instance(10).childSelector(resourceId("android:id/checkbox"))')  #
    button_element = driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().className("android.widget.LinearLayout").instance(10).childSelector(className("android.widget.RelativeLayout"))')  #

    """
    app = AppiumBar()
    app.init_works(0)
    driver = app.driver
    driver.implicitly_wait(3)
    driver.swipe(300, 600, 300, 1800)
    app.is_edge()

    driver.find_element(AppiumBy.ID, "android:id/inputArea").click()
    ele = driver.find_element(AppiumBy.ID, "android:id/input")
    ele.send_keys("锁屏")

    
    app.start_recording(use_scrcpy=True)
    app.stop_recording()

    driver.start_recording_screen() # 开始屏幕录制 timeLimit=180,videoSize=f"{int(0.7*w)}x{int(0.7*h)}",bitRate=3
    time.sleep(1)
    driver.terminate_app('com.android.settings')
    driver.activate_app('com.android.settings')
    locator = (AppiumBy.ANDROID_UIAUTOMATOR,'new UiSelector().text("我的服务")')
    res = app.check_with_scroll(*locator, direct="bottom", maxslipes=10)
    print(res)

    video_base64 = driver.stop_recording_screen()  # 停止屏幕录制
    # 将base64编码的视频内容解码为二进制数据
    video_data = base64.b64decode(video_base64)
    video_file_name = f'screen_record_{int(time.time())}.mp4'
    with open(video_file_name, 'wb') as video_file:
        video_file.write(video_data)


    locator = (AppiumBy.ID, "android:id/title2")

    element = WebDriverWait(driver, timeout=2).until(presence_of_element_located(locator))
    elements = WebDriverWait(driver, timeout=2).until(presence_of_all_elements_located(locator))

    app.check_toast("无法连接网络", fuzzy=True)
    app.check_toast("未检测到sim卡", fuzzy=True)
    if app.check_toast("跳过", fuzzy=True):
        app.check_toast("刷新失败", fuzzy=True)
    app.check_switch_checkbox("抬起亮屏")
    app.switch_checkbox_status("抬起亮屏",enabled=False)

    app.check_element_exist(AppiumBy.XPATH, '//android.widget.Button[contains(@text,"微信登录")]')

    driver.set_network_connection(ConnectionType.ALL_NETWORK_ON)



    app.enable_event_listener(ExceptListener())
    app.driver.find_element(AppiumBy.XPATH, '//android.widget.Button[contains(@text,"微信登录")]')
    app.disable_event_listener()

    th1 = app.start_thread_func(target=app.check_element_exist, args=(AppiumBy.XPATH, '//android.widget.Button[contains(@text,"微信登录")]', 10))
    driver.swipe(300, 600, 300, 1800)
    time.sleep(2)
    driver.swipe(300, 600, 300, 1800)
    time.sleep(2)
    driver.swipe(300, 600, 300, 1800)
    res = th1.get_result()
    print(f"{res=}")

    # print(driver.get_credentials, driver.battery_info, driver.get_window_size(), sep="\n")
    # print(driver.current_package,driver.current_activity, driver.network_connection,driver.page_source,sep="\n")
    # driver.swipe(300,600, 300,1800)
    # driver.flick(300,1800,300,600)

    # driver.activate_app('com.miui.weather2')
    # driver.press_keycode(AndroidKey.HOME)
    # driver.activate_app('com.android.settings')
    # driver.swipe(300,600, 300,1800)
    # ele = driver.find_element(by=AppiumBy.ID, value="android:id/inputArea")
    # print(ele.location, ele.id,ele.text, ele.size,sep="\n")
    #
    # # action = TouchAction(driver)
    # # action.press(x=150, y=800).wait(5000).move_to(x=500,y=600).wait(5000).move_to(x=300,y=400).release().perform()
    #
    # app.continuous_drag(150,800,600,500,150,400,2, 100)
    #
    # app.three_finger_slide()
    # app.three_finger_tap()
    # driver.press_keycode(AndroidKey.BACK)
    # driver.press_keycode(AndroidKey.HOME)
    # app.drag_dock()
    # # app.double_click()
    # driver.lock()
    # driver.unlock()
    # driver.flick(300, 1800, 300, 600)
    # pos_list = [(260,2164),(618,1810),(618,2164),(970,1810),(970,1451),(618,1451),(260,1810)]
    # app.multiple_swipe(positions=pos_list)
    # print("-"*20)
    """
    # app.clean_works()

