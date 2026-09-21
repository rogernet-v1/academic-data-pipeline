# config/logging_config.py
import sys
from loguru import logger
from config.settings import LOG_FILE

# 清除默认配置
logger.remove()

# 控制台彩色输出
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)

# 文件日志输出（按大小切割）
logger.add(
    LOG_FILE,
    rotation="10 MB",
    retention="7 days",
    level="DEBUG",
    encoding="utf-8"
)