from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import httpx
from models.paper import StandardPaper


class BaseSpider(ABC):
    """
    学术数据源爬虫抽象基类
    """
    source_name: str = "base"

    def __init__(self, timeout: float = 15.0):
        self.timeout = timeout

    @abstractmethod
    async def fetch_papers(self, search_query: str, max_results: int = 10) -> List[StandardPaper]:
        """
        根据检索词拉取论文并统一清洗返回 StandardPaper 列表
        """
        pass

    @abstractmethod
    def parse(self, raw_data: Any) -> List[StandardPaper]:
        """
        将数据源特有的原始响应数据清洗为 StandardPaper 结构
        """
        pass