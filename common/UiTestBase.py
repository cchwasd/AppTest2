# -*- coding: utf-8 -*-

"""
----------------------------------------
# @File         : UiTestBase.py
# @Time         : 2025/7/19 21:34
# @Author       : cch
# @Description  : 
----------------------------------------
"""
import pytest
import inspect

class UiTestBase:
    device_lst = []
    current_class_file = ""
    current_function_name = ""
    class_name = "UiTestBase"

    @pytest.fixture(scope="class", autouse=True)
    def setup_class(self, request):
        """
        类级别的fixture，在每个测试类开始前执行一次。
        可以在这里执行一些类级别的初始化操作，如创建测试环境。
        """
        # 可以在这里执行一些类级别的初始化操作
        print("setup_class")
        #  # 使用 request.cls 获取当前测试类，进而获取所在文件的名称；inspect 获取当前测试用例文件的名称，子类也能获取到
        class_file = inspect.getfile(request.cls)
        print(f"Current test class file: {class_file}")

        # 获取当前测试类的名称
        class_name = request.cls.__name__
        print(f"Current test class name: {class_name}")

        self.device_lst = ["dagdfg", "regrer"]
        # 这里可以将 device_lst 传递给测试类
        request.cls.device_lst = self.device_lst
        request.cls.current_class_file = class_file
        request.cls.class_name = class_name

        yield  # 这里可以放置测试类的代码
        print("teardown_class")  # 类级别的teardown操作
        request.cls.current_class_file = ""
        request.cls.class_name = ""

    @pytest.fixture(scope="function", autouse=True)
    def setup_function(self, request):
        """
        函数级别的fixture，在每个测试函数开始前执行一次。
        可以在这里执行一些函数级别的初始化操作，如创建测试环境。
        """
        # 可以在这里执行一些函数级别的初始化操作
        # 获取当前测试用例的执行函数名称
        function_name = request.function.__name__
        print(f"Current test function name: {function_name}")
        print("setup_function")
        request.cls.current_function_name = function_name
        yield  # 这里可以放置测试函数的代码
        print("teardown_function")  # 函数级别的teardown操作
        request.cls.current_function_name = ""






