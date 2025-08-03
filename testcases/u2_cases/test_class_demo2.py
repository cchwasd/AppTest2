# -*- coding: utf-8 -*-

"""
----------------------------------------
# @File         : test_class_demo2.py
# @Time         : 2025/7/19 21:55
# @Author       : cch
# @Description  : 
----------------------------------------
"""
import pytest
import os

from common.UiTestBase import UiTestBase

class TestDemo2(UiTestBase):

    @pytest.mark.smoke
    @pytest.mark.repeat(3)
    def test_003(self):
        print(self.device_lst)
        print(self.current_class_file)
        print(self.current_function_name)

        assert self.__class__.__name__ == os.path.basename(__file__).split('.')[0]
        assert self.current_class_file == __file__
        assert self.current_function_name == "test_001"

    @pytest.mark.smoke
    def test_004(self):
        print(self.device_lst)
        print(self.current_class_file)
        print(self.current_function_name)

        assert self.__class__.__name__ == os.path.basename(__file__).split('.')[0]
        assert self.current_class_file == __file__
        assert self.current_function_name == "test_002"


if __name__ == "__main__":
    pytest.main(["-vs", __file__])  # 模拟命令行行为
