import pytest

def pytest_addoption(parser):
    # pytest 添加自定义命令行参数
    parser.addoption("--index_device", type=int,action="store", default=0,help="配置项中设备序列索引")
    parser.addoption("--serial", type=str, action="store", default='', help="指定设备号")
    parser.addoption("--recording", type=int, action="store", default=0, help="设置是否录屏")
    # parser.addoption(
    #     "--env", action="store", default="dev", help="env：表示命令行参数内容，不填写默认输出default的值内容"
    # )

@pytest.fixture(scope='session')
def index_device(request):
    # 定义index_device fixture 用于接收命令行参数的值
    return request.config.getoption("--index_device")

# run: python -m pytest -vs testcases\test_milogin_pages.py --index_device 1

@pytest.fixture(scope='session')
def serial(request):
    # 定义fixture 用于接收命令行参数的值
    return request.config.getoption("--serial")

@pytest.fixture(scope='session')
def recording(request):
    # 定义fixture 用于接收命令行参数的值
    return request.config.getoption("--recording")

# run: python -m pytest -vs testcases\test_login_account_ui2.py --serial xxxx --recording 1