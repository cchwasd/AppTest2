import time

import cv2
import pyautogui


def get_img_pos(img_mode_path, img_screen_path):
    """
    获取窗口中模型图片匹配的 坐标点
    :param img_mode_path: 用来检测的模板图片路径
    :param img_screen_path: 来源或要匹配大图路径
    :return: x,y
    """
    # 将屏幕截图保存
    pyautogui.screenshot().save(img_screen_path)
    # 载入截图
    img = cv2.imread(img_screen_path)
    # 图像模板
    img_terminal = cv2.imread(img_mode_path)
    # 读取模板的宽度和高度
    height, width, channel = img_terminal.shape
    # 进行模板匹配， 模板匹配是在一副大图中搜寻查找模版图像位置。
    result = cv2.matchTemplate(img, img_terminal, cv2.TM_SQDIFF_NORMED)
    # 解析出匹配区域的左上角坐标
    upper_left = cv2.minMaxLoc(result)[2]
    # 计算出匹配区域的右下角坐标
    lower_right = (upper_left[0]+width, upper_left[1]+height)
    # 计算出中心区域的坐标
    center = (int((upper_left[0]+lower_right[0])/2), int((upper_left[1]+lower_right[1])/2))
    return center

def auto_click(point):
    """
    鼠标右键点击坐标点
    :param point: 坐标元组
    :return: None
    """
    pyautogui.click(point[0], point[1], button="left")
    time.sleep(1)

def routine(img_model_path, img_screen_path):
    point = get_img_pos(img_model_path, img_screen_path)
    auto_click(point)


if __name__ == '__main__':
    routine("./mode_imgs/terminal.png", "./mode_imgs/screenshot.png")

