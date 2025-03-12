
from common.AppiumBar import AppiumApi


#定义一个类：描述每个页面相同的属性及行为
class BasePage:
    package: str = ""
    activity: str = ""
    appiumApi: AppiumApi = None

    # 行为：输入，点击
    def locator(self, loc: tuple):
        # loc=(MobileBy.ID,"resourceid值")
        return self.appiumApi.driver.find_element(*loc)

    def input(self, loc, value):
        return self.locator(loc).send_keys(value)

    def click(self, loc):
        return self.locator(loc).click()