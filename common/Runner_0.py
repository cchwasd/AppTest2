# https://blog.csdn.net/2401_83014899/article/details/142579224
import time
from concurrent.futures import ThreadPoolExecutor, as_completed, wait, ALL_COMPLETED
import os
from multiprocessing import Pool
import random
import pytest

from common.AdbBar import AdbBar


def divide_groups(data_list:list=None, devices:list=None,shuffle=False):
    """ 数据分组 """
    if not data_list or not devices:
        return None
    # data_list = list(range(0,27)) # 10000000
    # devices = ['server1', 'server2', 'server3', 'server4']
    if shuffle:
        random.shuffle(data_list)
    group_dict = {f'{device}': list() for device in devices}    # 初始化字典值
    nums_device = len(devices)
    nums_group, remainder = divmod(len(data_list), nums_device)
    # print(f"{nums_device=}，{nums_group=}")
    # # 1.均分数据，顺序遍历写入
    # for i, value in enumerate(data_list):
    #     group = i % len(devices)
    #     group_dict[devices[group]].append(value)

    # # 2.切片分组写入
    # device_index=0
    # for i in range(0, len(data_list)-remainder,nums_group):
    #     group_dict[devices[device_index]]=data_list[i:i+nums_group]
    #     device_index+=1
    # device_index = 0
    # for item in data_list[-remainder:]:
    #     group_dict[devices[device_index]].append(item)
    #     device_index += 1

    # # 3.切片分组写入
    for i in range(nums_device):
        group_dict[devices[i]] = data_list[i*nums_group: (i+1)* nums_group]
    if remainder != 0:
        for index, value in enumerate(data_list[-remainder:]):
            group_dict[devices[index]].append(value)
    return group_dict

def pytest_run(test_cases: list, index_device:int=0):
    """ apply_async，submit提交任务执行  """
    result_lst = []
    for case in test_cases:
        result=pytest.main(['-vs', case, '--index_device', f'{index_device}'])
        # result=os.popen(f"python -m pytest -vs {case} --index_device {index_device}").read().strip()
        result_lst.append(result)
    return result_lst

def pytest_run2(args: tuple):
    """ map方式提交任务执行 获取参数组合，拆分 """
    test_cases, index_device = args
    result_lst = []
    for case in test_cases:
        result=pytest.main(['-vs', case, '--index_device', f'{index_device}'])
        # result=os.popen(f"python -m pytest -vs {case} --index_device {index_device}").read().strip()
        result_lst.append(result)
    return result_lst

def pytest_run_u2(args: tuple):
    """ map方式提交任务执行 获取参数组合，拆分 """
    device, test_cases, recording = args
    result_lst = []
    for case in test_cases:
        result=pytest.main(['-vs', case, '--serial', f'{device}', '--recording', f'{recording}'])
        # result=os.popen(f"python -m pytest -vs {case} --index_device {index_device}").read().strip()
        result_lst.append(result)
    return result_lst

def case_runner_by_thread():
    """
    testcases = [
        r'C:\MCodes\PyCodes\AppPro\testcases\test_milogin_pages.py',
        r'C:\MCodes\PyCodes\AppPro\testcases\test_switch_pages.py'
    ]
    devices = AdbBar.get_connected_devices()


    # 执行方式1 
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        # 使用submit提交执行的函数到线程池中
        futures = {executor.submit(pytest_run, testcases, i): i for i in range(len(devices))}

        # wait(testcases, return_when=ALL_COMPLETED)   # 主线程等待所有子线程完成

        # as_completed: 每返回一个子线程就立刻处理，先完成的任务会先返回给主线程，直到所有的任务结束。
        for future in as_completed(futures):
            number = futures[future]
            try:
                result = future.result()    # 通过result来获取返回值
            except Exception as exc:
                print(f"{number} generated an exception: {exc}")
            else:
                print(f"The factorial of {number} is {result}")

    # 执行方式2
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        task_lst = [ (testcases,i) for i in range(len(devices))]
        print(task_lst)
        # map 方法是对序列中每一个元素都执行，返回结果的顺序和元素的顺序相同，即使子线程先返回也不会获取结果
        for result in executor.map(pytest_run2, task_lst):
            print(f"{result} 返回")
    """

    testcases = [
        r'C:\MCodes\PyCodes\AppPro\testcases\test_login_account2_ui2.py',
        r'C:\MCodes\PyCodes\AppPro\testcases\test_login_account_ui2.py'
    ]
    devices = AdbBar.get_connected_devices()
    data_dict = divide_groups(testcases,devices)
    print(data_dict)
    recording= 1
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        task_lst = [ (k,v,recording) for k,v in data_dict.items()]
        print(task_lst)
        # map 方法是对序列中每一个元素都执行，返回结果的顺序和元素的顺序相同，即使子线程先返回也不会获取结果
        for result in executor.map(pytest_run_u2, task_lst):
            print(f"{result} 返回")


def case_runner_by_process():
    """
    testcases = [
        r'C:\MCodes\PyCodes\AppPro\testcases\test_milogin_pages.py',
        r'C:\MCodes\PyCodes\AppPro\testcases\test_switch_pages.py'
    ]
    devices = AdbBar.get_connected_devices()
    # 执行方式1
    processes = Pool(processes=len(devices))
    results = [processes.apply_async(pytest_run, args=(testcases, i)) for i in range(len(devices))]
    processes.close()
    processes.join()

    for res in results:
        print("---: ",res.get())

    # 执行方式2
    with Pool(processes=len(devices)) as pool:
        task_lst = [(testcases, i) for i in range(len(devices))]
        print(task_lst)
        # map 方法是对序列中每一个元素都执行，返回结果的顺序和元素的顺序相同，即使子线程先返回也不会获取结果
        for result in pool.map(pytest_run2, task_lst):
            print(f"{result} 返回")
    """

    testcases = [
        r'C:\MCodes\PyCodes\AppPro\testcases\test_login_account2_ui2.py',
        r'C:\MCodes\PyCodes\AppPro\testcases\test_login_account_ui2.py'
    ]
    devices = AdbBar.get_connected_devices()
    data_dict = divide_groups(testcases,devices)
    print(data_dict)
    recording= 1
    # 执行方式2
    with Pool(processes=len(devices)) as pool:
        task_lst = [ (k,v,recording) for k,v in data_dict.items()]
        print(task_lst)
        # map 方法是对序列中每一个元素都执行，返回结果的顺序和元素的顺序相同，即使子线程先返回也不会获取结果
        for result in pool.map(pytest_run_u2, task_lst):
            print(f"{result} 返回")



if __name__ == "__main__":
    # data=divide_groups()
    # print(data)
    # case_runner_by_thread()
    case_runner_by_process()