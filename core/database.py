import os
import sys

# 确保项目根目录在搜索路径中
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "academic_data.db")
DATABASE_URL = f"sqlite+aiosqlite:///{DB_PATH}"

# 创建异步引擎与 Session 工厂
engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ORM 基类
Base = declarative_base()