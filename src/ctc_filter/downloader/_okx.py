import json
import os

import pandas as pd
from pandas import DataFrame


class OKXAdapter:
    """OKX 交易所适配器"""

    def __init__(self):
        try:
            from okx.MarketData import MarketAPI
        except ImportError:
            raise ImportError("Please install the okx package")

        KEY = os.getenv("OKX_API_KEY")
        SECRET = os.getenv("OKX_API_SECRET")
        assert KEY and SECRET, "API key and secret are required"
        self._market = MarketAPI(KEY, SECRET, flag="0")

    def to_candles(self, data: list) -> DataFrame:
        """将数据转换为用于绘制 K 线图的 DataFrame

        Args:
            data: JSON 数据

        Returns:
            DataFrame: 一组 K 线数据帧
        """
        df = pd.DataFrame(
            data,
            columns=[
                "ts",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "volCcy",
                "volCcyQuote",
                "_",
            ],
        )
        return df

    def get_current_candlestick(self, inst_id: str, bar: str = "1H") -> DataFrame:
        """获取当前 K 线数据"""
        if not isinstance(inst_id, str):
            raise TypeError("instId must be a string")

        # 获取最近 3 个小时级别的 K 线数据
        resp = self._market.get_candlesticks(inst_id, bar=bar, limit="2")
        data = resp["data"]
        df = self.to_candles(data)
        return df

    def get_candlesticks(
        self,
        inst_id: str,
        bar: str = "1H",
        limit: str = "100",
    ) -> DataFrame:
        """获取 K 线数据, 包含历史数据和最新数据"""
        if not isinstance(inst_id, str):
            raise TypeError("instId must be a string")
        if not isinstance(inst_id, str):
            raise TypeError("instId must be a string")
        if not (isinstance(limit, str) and limit.isdigit()):
            raise TypeError("limit must be a number")

        dst_dir = f"./data/{inst_id}/{bar}"
        file_path = f"./data/{inst_id}/{bar}/{inst_id}.json"

        # 获取最新的 K 线数据
        latest_df = self.get_current_candlestick(inst_id, bar)

        resp = self._market.get_history_candlesticks(inst_id, bar=bar, limit=limit)
        history_data = resp["data"]
        history_df = self.to_candles(history_data)
        df = self.merge_candlesticks(history_df, latest_df)
        data = df.to_dict(orient="records")
        os.makedirs(dst_dir, exist_ok=True)
        with open(file_path, "w") as f:
            f.write(json.dumps(data, indent=4))
        return df

    def merge_candlesticks(self, df1: DataFrame, df2: DataFrame) -> DataFrame:
        """合并两个 K 线数据帧

        Args:
            df1: K 线数据帧 1
            df2: K 线数据帧 2

        Returns:
            DataFrame: 合并后的 K 线数据帧
        """
        # 合并历史数据和最新数据，按时间戳去重，保留 '_' 为 1 的数据，即收盘数据
        df = pd.concat([df1, df2], ignore_index=True)
        df.drop_duplicates("ts", keep="last", inplace=True)
        df.sort_values("ts", ascending=True, inplace=True)
        return df
