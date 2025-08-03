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


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """在测试执行完成后输出统计信息"""
    # 获取统计信息
    stats = terminalreporter.stats
    # 原有的整体统计信息
    passed = len(stats.get("passed", []))
    failed = len(stats.get("failed", []))
    skipped = len(stats.get("skipped", []))
    xpassed = len(stats.get("xpassed", []))
    xfailed = len(stats.get("xfailed", []))
    error = len(stats.get("error", []))

    total = passed + failed + skipped + xpassed + xfailed + error

    print("\n=== 测试执行统计 ===")
    print(f"总用例数: {total}")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"跳过: {skipped}")
    print(f"预期失败但通过 (xpassed): {xpassed}")
    print(f"预期失败 (xfailed): {xfailed}")
    print(f"错误 (error): {error}")

    if total > 0:
        pass_rate = (passed / total) * 100
        print(f"通过率: {pass_rate:.2f}%")

    # 初始化按 用例函数名分组的统计字典(使用repeat插件的用例统计)
    test_case_stats = {}
    # 处理通过的用例
    for report in stats.get("passed", []):
        # test_name = report.nodeid.split("::")[-1].split("[")[0]
        test_name = report.nodeid.split("[")[0]
        print(f"{report.nodeid}, {test_name=}")
        if test_name not in test_case_stats:
            test_case_stats[test_name] = {"passed": 0, "total": 0}
        test_case_stats[test_name]["passed"] += 1
        test_case_stats[test_name]["total"] += 1

    # 处理失败的用例
    for report in stats.get("failed", []):
        # test_name = report.nodeid.split("::")[-1].split("[")[0]
        test_name = report.nodeid.split("[")[0]
        if test_name not in test_case_stats:
            test_case_stats[test_name] = {"passed": 0, "total": 0}
        test_case_stats[test_name]["total"] += 1

    # 处理其他状态的用例（可按需添加）
    print("\n=== 按用例函数名分组的测试执行统计 ===")
    for test_name, data in test_case_stats.items():
        passed = data["passed"]
        total = data["total"]
        pass_rate = (passed / total) * 100 if total > 0 else 0
        print(f"用例函数名: {test_name}")
        print(f"  总执行次数: {total}")
        print(f"  通过次数: {passed}")
        print(f"  通过率: {pass_rate:.2f}%")
