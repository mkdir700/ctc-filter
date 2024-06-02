from pandas import DataFrame

from ._okx import OKXAdapter


class Downloader:
    def __init__(self, inst_id: str, exchange: str) -> None:
        """初始化下载器

        Args:
            inst_id: 交易对
            exchange: 交易所, 目前支持 okx
        """
        if not isinstance(inst_id, str):
            raise TypeError("instId must be a string")
        self.inst_id = inst_id
        if exchange.lower() == "okx":
            self._adapter = OKXAdapter()
        else:
            raise ValueError("Unsupported exchange")

    def get_current_candlestick(self, bar: str = "1H") -> DataFrame:
        """获取当前 K 线数据"""
        return self._adapter.get_current_candlestick(self.inst_id, bar=bar)

    def get_candlesticks(self, bar: str = "1H", limit: str = "100") -> DataFrame:
        return self._adapter.get_candlesticks(self.inst_id, bar=bar, limit=limit)
