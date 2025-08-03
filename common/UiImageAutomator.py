# -*- coding: utf-8 -*-
import time
import cv2
import numpy as np
import uiautomator2 as u2



# https://blog.csdn.net/zh6526157/article/details/129659343

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

