import json

from pandas import DataFrame

from ctc_filter.config import settings


class DataSource:
    def get_tickers(self) -> list:
        data_file_path = settings.user_data_dir / "tickers.json"
        if not data_file_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_file_path}")
        with open(data_file_path) as f:
            data = json.load(f)
        return data

    def get_candlesticks(self, inst_id: str, bar: str = "1H") -> DataFrame:
        data_file_path = (
            settings.user_data_dir / "candlesticks" / inst_id / bar / "data.json"
        )
        if not data_file_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_file_path}")
        # PERF: 暂时从 JSON 文件中读取数据
        with open(data_file_path) as f:
            data = json.load(f)
        df = self.to_candles(data)
        return df

    def to_candles(self, data: list) -> DataFrame:
        """将数据转换为用于绘制 K 线图的 DataFrame

        Args:
            data: JSON 数据

        Returns:
            DataFrame: 一组 K 线数据帧
        """
        df = DataFrame(
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
