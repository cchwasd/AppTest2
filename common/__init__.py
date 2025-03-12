
from common.utils import define_paths, load_logger, init_logging
import datetime

today = datetime.datetime.utcnow()
the_paths = define_paths()

# 加载日志配置文件
# load_logger(the_paths["config"]/"log_config.yml")
init_logging(filename=the_paths["logs"]/f"app_run{today:%Y-%m-%d_%H%M%S}.log")
# logger.info(f"{the_paths=}")