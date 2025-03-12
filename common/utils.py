import functools
import logging
import os
import platform
import logging.config
import subprocess
import time
from configparser import ConfigParser
from pathlib import Path
import yaml
from string import Template
import pprint

# 定义一个装饰器函数，用于记录函数执行时间
def time_exec(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        params_str = args.__str__().lstrip('(').rstrip(')')
        if not params_str.endswith(','):
            params_str += ', '
        params_str += kwargs.__str__().replace(': ','=').lstrip('{').rstrip('}')
        print(f"start function: {fn.__name__}, params: {params_str} ")
        start = time.perf_counter()
        ret = fn(*args, **kwargs)
        end = time.perf_counter()
        print(f"{fn.__name__} elapsed time: {end - start:.3f}s")
        return ret
    return wrapper

def u2_screen(fn):
    """ 实现一个传参 装饰器来获取执行类函数的对象 """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):   # self, 类内函数使用
        try:
            return fn(*args, **kwargs)  # self, 类内函数使用
        except Exception as e:
            kwargs.get("u2_start",None).screen_shot()
            raise Exception(f"Error in function {fn.__name__}, error: {e}")

    return wrapper

def yaml_load(config_file):
    """
      读取YAML配置文件并返回Appium的desired capabilities列表。

      :param config_file_path: YAML配置文件的路径
      :return: 包含多个desired capabilities字典的列表
    """
    with open(config_file, mode='r', encoding="utf-8") as file:
        config = yaml.safe_load(file)
        return config

def yaml_save(config_file_path, config_data):
    """
    保存YAML配置文件。

    :param config_file_path: YAML配置文件的路径
    :param config_data: 要保存的配置数据
    """
    with open(config_file_path, 'w', encoding='utf-8') as file:
        yaml.dump(config_data, file, allow_unicode=True, default_flow_style=False)

@time_exec
def yaml_update(config_file_path, device_index, is_save=True, **kwargs):
    """
    修改YAML配置文件中的参数。

    :param config_file_path: YAML配置文件的路径
    :param device_index: 要修改的设备配置索引（从0开始）
    :param kwargs: 要修改的参数和值
    """
    # 加载配置文件
    config_data = yaml_load(config_file_path)

    # 检查索引是否有效
    if device_index < 0 or device_index >= len(config_data):
        raise IndexError("设备索引超出范围")

    # 修改指定索引的设备配置
    for key, value in kwargs.items():
        config_data[device_index]['desired_caps'][key] = value
    if is_save:
        # 保存修改后的配置文件
        yaml_save(config_file_path, config_data)
    return config_data

# 定义和检查关键目录的路径
def define_paths():
    base_path = Path(__file__).resolve().parent.parent
    conf = ConfigParser()
    # 先加载 ini项目配置
    conf.read(base_path/'config'/'project.ini', encoding='utf-8')
    conf_dict = {
        'report': conf['Paths'].get('report_dir'),
        'logs': conf['Paths'].get('log_dir'),
        'resources': conf['Paths'].get('resources_dir')
    }
    all_keys = list(conf_dict.keys())
    for k in all_keys:
        if not conf_dict[k]:
            del conf_dict[k]

    paths = {
        'config': base_path / 'config',
        'report': Path(conf_dict.get('report', base_path / 'report')),
        'logs': Path(conf_dict.get('logs', base_path / 'report' / 'logs')),
        'resources': Path(conf_dict.get('resources', base_path / 'resources'))
    }

    # 确保所有需要的目录都存在
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

    return paths

def find_files(pattern, path='.'):
    """
    按照文件名查找文件
    :param pattern:文件名模式，例如 "*vft*.pdf,文件名包含vft的pdf文件"
    :param path: 文件路径
    :return:
    """
    return [p.__str__() for p in Path(path).rglob(f'**/{pattern}')]

def rename_file(old_path, new_path):
    Path(new_path).rename(old_path)
def os_type():
    """获取操作系统类型，返回 'windows'、'linux' 之类的"""
    return platform.system().lower()

def exec_cmd(cmd):
    """执行命令行并返回内容"""
    result = os.popen(cmd).read()
    return result

def exec_subprocess(command: str=""):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)
    # 获取输出和错误
    stdout, stderr = process.communicate()
    # 打印输出和错误
    # print(stdout.decode())    #  text=True和 std.decode() 效果一样
    # if stderr:
    #     print("error:",stderr)
        # raise Exception(stderr.decode())
    return stdout.strip(), stderr.strip()

def class_to_dict(cls):
    # 创建一个空字典来存储转换后的数据
    result_dict = {}
    # 遍历类的属性
    for key, value in cls.__dict__.items():
        if not (key.startswith('_')):    # 排除内置属性和魔法方法
            # 如果属性是类，则递归调用class_to_dict函数
            if isinstance(value, type):
                result_dict[key] = class_to_dict(value)
            else:
                result_dict[key] = value
    return result_dict

def dict_to_class(d, cls):
    # 实例化一个类对象
    obj = cls()
    for key, value in d.items():
        # 如果字典的值是另一个字典，递归调用dict_to_class
        if isinstance(value, dict):
            # 动态创建类
            TempClass = type(key.capitalize(), (object,), {})
            setattr(obj, key, dict_to_class(value, TempClass))
        else:
            setattr(obj, key, value)
    return obj


def load_logger(path="logging.yml", level=logging.INFO):
    """加载日志配置文件（分级别多文件多模块），"""
    if os.path.exists(path):
        with open(path, "r") as rf:
            log_config = rf.read()
            if "${" in log_config:
                # 使用string.Template 将外部变量插入到YAML配置中
                log_config_template = Template(log_config)
                log_config_with_variables = log_config_template.safe_substitute(logs=define_paths()['logs'])
                conf = yaml.safe_load(log_config_with_variables)
            else:
                conf = yaml.safe_load(rf)
        logging.config.dictConfig(conf)
    else:
        logging.basicConfig(level=level)


def parse_var(ele_text: tuple, text:str):
    # 解析，替换text文本中指定变量内容
    by, val = ele_text[0], ele_text[1]
    val = Template(val).safe_substitute(var=text)
    return by, val


def init_logging(level=logging.DEBUG,filename=""):
    logging.basicConfig(level=level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',filename=filename)




# the_paths = define_paths()
# load_logger(the_paths["config"]/"log_config.yml")
# logger = logging.getLogger("AppiumApi")

if __name__ == '__main__':
    yal_context = yaml_load("../config/appium_config.yml")
    pprint.pprint(yal_context)
    res = yaml_update("../config/appium_config.yml",0,is_save=False, deviceName="Shenqi",platformVersion='15')
    pprint.pprint(res)
    # paths = define_paths()
    # pprint.pprint(paths)
    # pprint.pprint(os_type())

    # load_logger("../config/log_config.yml")
    # logging.debug("debug msg")
    # logging.info("info msg")
    # logging.warning("warning msg")
    # logging.error("error msg")
    # logging.critical("critical msg")
    # ###设置完毕###
    # # 获取根记录器：配置信息从yaml文件中获取
    # root = logging.getLogger()
    # # 子记录器的名字与配置文件中loggers字段内的保持一致
    # server = logging.getLogger("AppiumApi")
    # server.info("rootlogger: %s", str(root.handlers))
    # server.info("serverlogger: %s", str(server.handlers))
    # server.info("子记录器与根记录器的handler是否相同：%s", str(root.handlers[0] == server.handlers[0]))

    # out,_ = exec_subprocess("adb devices")
    # print(out)
