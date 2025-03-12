import cv2
import numpy as np


def get_pos_by_one_match(source_img, target_img, similar=0.95):
    """
        在当前页面上匹配出最相似的目标图片，并计算出中心坐标
        :param source_img:
        :param target_img: 例：../img/test.png
        :return: (x,y)
    """
    source_image = cv2.imread(source_img)
    target_image = cv2.imread(target_img)
    h, w = target_image.shape[:2]  # 获取模板高和宽
    # 匹配模板
    res = cv2.matchTemplate(source_image, target_image, cv2.TM_CCOEFF_NORMED)
    # 获取匹配结果中的最小值、最大值、最小值坐标和最大值坐标
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    if max_val < similar:
        return None
    # 计算矩形左边
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    center_pos = int(top_left[0] + (w // 2)), int(top_left[1] + (h // 2))
    return center_pos

    # # 画矩形
    # cv2.rectangle(source_image, top_left, bottom_right, (0, 0, 255), 5)
    # # 展示结果
    # cv2.namedWindow("source_image", cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
    # cv2.imshow('source_image', source_image)
    # cv2.waitKey(0)


def get_npos_by_more_match(source_img, target_img, similar=0.95):
    """
    在当前页面上匹配目标图片，计算出多个匹配度较高的中心坐标，
    :param source_img:
    :param target_img: 例：../img/test.png
    :return: [(x,y),]
    """
    source_image = cv2.imread(source_img)
    target_image = cv2.imread(target_img)

    result = cv2.matchTemplate(source_image, target_image, cv2.TM_SQDIFF_NORMED)  # 进行模板匹配
    h, w = target_image.shape[:2]  # 获取模板高和宽

    threshold = 1-similar    # 定义阈值，因为TM_SQDIFF_NORMED越接近0越匹配，所以设置阈值为0.01

    loc = np.where(result <= threshold)  # 匹配结果小于阈值的位置

    temp_list = []
    for pt in zip(*loc[::-1]):  # 遍历位置，zip把两个列表依次参数打包
        right_bottom = (pt[0] + w, pt[1] + h)  # 右下角位置
        centor_pos = int(pt[0]+(w//2)), int(pt[1]+(h//2))
        temp_list.append(centor_pos)
        #
        # temp_x = pt[0] + (w // 2)
        cv2.rectangle(source_image, pt, right_bottom, (0, 0, 255), 2)  # 绘制匹配到的矩阵

    result_list = sorted(temp_list)
    temp_list.clear()
    # print(result_list)
    temp_x = 0
    for item in result_list:
        if abs(item[0]-temp_x)>2:
            temp_list.append(item)
        temp_x = item[0]
    # print(f"---中心点坐标：{temp_list}, type:{type(temp_list[0][0])}")

    return temp_list
    # cv2.namedWindow("source_image", cv2.WINDOW_NORMAL | cv2.WINDOW_FREERATIO)
    # cv2.imshow("source_image",source_image)
    # # cv2.imshow("template",template)
    # cv2.waitKey(0)  #获取按键的ASCLL码
    # cv2.destroyAllWindows()  #释放所有的窗口


if __name__ == '__main__':
    target_img = "./mode_imgs/ball_g.png"
    source_img = "./mode_imgs/ant_forest.png"
    # source_img = "mode_imgs/screenshot_page.png"
    # pos = get_pos_by_one_match(source_img, target_img)
    pos = get_npos_by_more_match(source_img, target_img)
    print(f'---pos:{pos}')