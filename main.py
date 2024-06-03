import json
import os
from datetime import datetime
from typing import Optional

import numpy as np
import pandas as pd
import talib as ta
from dotenv import load_dotenv
from okx.MarketData import MarketAPI
from pandas import DataFrame

load_dotenv()

KEY = os.getenv("OKX_API_KEY")
SECRET = os.getenv("OKX_API_SECRET")
assert KEY and SECRET, "API key and secret are required"
market = MarketAPI(KEY, SECRET, flag="0")


def to_candles(data: list) -> DataFrame:
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


def get_current_candlestick(instId: str, bar: str = "1H") -> DataFrame:
    """获取当前 K 线数据"""
    if not isinstance(instId, str):
        raise TypeError("instId must be a string")

    # 获取最近 3 个小时级别的 K 线数据
    resp = market.get_candlesticks(instId, bar=bar, limit="2")
    data = resp["data"]
    df = to_candles(data)
    return df


def get_candlesticks(instId: str, bar: str = "1H", limit: str = "100") -> DataFrame:
    """获取 K 线数据, 包含历史数据和最新数据"""
    if not isinstance(instId, str):
        raise TypeError("instId must be a string")
    if not isinstance(instId, str):
        raise TypeError("instId must be a string")
    if not (isinstance(limit, str) and limit.isdigit()):
        raise TypeError("limit must be a number")

    dst_dir = f"./data/{instId}/{bar}"
    file_path = f"./data/{instId}/{bar}/{instId}.json"

    # 获取最新的 K 线数据
    latest_df = get_current_candlestick(instId, bar)

    def _get_history_data():
        # if os.path.exists(dst_dir):
        #     with open(file_path, "r") as f:
        #         _history_data = json.load(f)
        # else:
        resp = market.get_history_candlesticks(instId, bar=bar, limit=limit)
        _history_data = resp["data"]
        return _history_data

    history_data = _get_history_data()
    history_df = to_candles(history_data)
    df = merge_candlesticks(history_df, latest_df)
    data = df.to_dict(orient="records")
    os.makedirs(dst_dir, exist_ok=True)
    with open(file_path, "w") as f:
        f.write(json.dumps(data, indent=4))
    # print(df["close"])
    return df


# def save_candlesticks(instId: str, df: pd.DataFrame) -> None:
#     data = df.to_dict(orient="records")
#     os.makedirs("./data", exist_ok=True)
#     with open(f"./data/{instId}.json", "w") as f:
#         f.write(json.dumps(data, indent=4))


def merge_candlesticks(df1: DataFrame, df2: DataFrame) -> DataFrame:
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


def is_golden_cross_macd(
    instId: str, n: int = 1, default_df: Optional[pd.DataFrame] = None
) -> bool:
    """判断是否存在 MACD 看涨信号(DIF 大于 DEA 且 MACD 柱状图大于 0).

    Args:
        instId: 交易对
        n: 最近 n 根 K 线，默认为 1，即最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
    if default_df is None:
        # 获取最近 100 个小时级别的 K 线数据
        df = get_candlesticks(instId)
    else:
        df = default_df

    # 计算 MACD
    assert hasattr(ta, "MACD"), "MACD not found in talib"
    dif, dea, macd = ta.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)  # type: ignore
    print(dif, dea)
    # NOTE: 交易所中的 macd 的数值都是 * 2 之后的结果
    macd = macd * 2
    # 出现一次 dif < dea, 这根 K 线之后出现 dif > dea
    dif_lt_dea_flag = False
    dif_lt_dea_index = 0
    for i in range(len(dif) - 1, len(dif) - n - 1, -1):
        if dif.iloc[i] < dea.iloc[i]:
            dif_lt_dea_flag = True
            dif_lt_dea_index = i
            break

    if not dif_lt_dea_flag:
        return False

    # 从 dif_lt_dea_index 开始找到 dif > dea 的 K 线
    for j in range(dif_lt_dea_index, len(dif), 1):
        if dif.iloc[j] > dea.iloc[j]:
            return True

    return False


def is_zero_axis_golden_cross(
    instId: str, n: int = 1, default_df: Optional[pd.DataFrame] = None
) -> bool:
    """判断是否存在零轴金叉信号(MACD 柱状图由负变正).

    Args:
        instId: 交易对
        n: 默认为 1, 表示最近 1 个 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取
    """
    if default_df is None:
        df = get_candlesticks(instId)
    else:
        df = default_df

    # 计算 MACD
    assert hasattr(ta, "MACD"), "MACD not found in talib"
    dif, dea, macd = ta.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)  # type: ignore
    # NOTE: 交易所中的 macd 的数值都是 * 2 之后的结果
    macd = macd * 2

    for i in range(1, n + 1):
        if (
            macd.iloc[-i] > 0
            and macd.iloc[-i - 1] < 0
            and dif.iloc[-i] > dea.iloc[-i]
            and dif.iloc[-i - 1] < dea.iloc[-i - 1]
        ):
            return True
    return False


def is_boll_bullish(
    instId: str, n: int = 1, default_df: Optional[pd.DataFrame] = None
) -> bool:
    """判断是否存在 Boll 看涨信号(收盘价大于中轨且小于上轨).

    Args:
        instId: 交易对
        n: 时间范围, 默认为 1, 表示最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
    if default_df is None:
        # 获取最近 100 个小时级别的 K 线数据
        df = get_candlesticks(instId)
    else:
        df = default_df

    # 计算 Boll
    assert hasattr(ta, "BBANDS"), "BBANDS not found in talib"
    upperband, middleband, _ = ta.BBANDS(  # type: ignore
        df["close"], timeperiod=21, nbdevup=2, nbdevdn=2, matype=0
    )
    for i in range(1, n + 1):
        if (
            float(df["close"].iloc[-i]) > middleband.iloc[-i]
            and float(df["close"].iloc[-i]) < upperband.iloc[-i]
            and float(df["high"].iloc[-i]) > float(df["close"].iloc[-i - 1])
        ):
            return True
    return False


# boll 中轨在 K 线内部
def middleband_inside_candle(
    instId: str, n: int = 1, default_df: Optional[pd.DataFrame] = None
) -> bool:
    """判断中轨是否在 K 线内部

    Args:
        instId: 交易对
        n: 时间范围, 默认为 1, 表示最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
    if default_df is None:
        # 获取最近 100 个小时级别的 K 线数据
        df = get_candlesticks(instId)
    else:
        df = default_df

    # 计算 Boll
    assert hasattr(ta, "BBANDS"), "BBANDS not found in talib"
    _, middleband, _ = ta.BBANDS(  # type: ignore
        df["close"], timeperiod=21, nbdevup=2, nbdevdn=2, matype=0
    )
    for i in range(1, n + 1):
        if (
            float(df["low"].iloc[-i])
            <= middleband.iloc[-i]
            <= float(df["high"].iloc[-i])
        ):
            return True
    return False


def is_kdj_bullish(
    instId: str, n: int = 1, default_df: Optional[pd.DataFrame] = None
) -> bool:
    """判断是否存在 KDJ 看涨信号(K 大于 D).

    Args:
        instId: 交易对
        n: 最近 n 根 K 线，默认为 1，即最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
    if default_df is None:
        # 获取最近 100 个小时级别的 K 线数据
        df = get_candlesticks(instId)
    else:
        df = default_df

    # 计算 KDJ
    assert hasattr(ta, "STOCH"), "STOCH not found in talib"
    kdj_k, kdj_d = ta.STOCH(  # type: ignore
        df["high"],
        df["low"],
        df["close"],
        fastk_period=9,
        slowk_period=3,
        slowk_matype=0,
        slowd_period=3,
        slowd_matype=0,
    )  # type: ignore

    # 出现一次 dif < dea, 这根 K 线之后出现 dif > dea
    k_lt_d = False
    k_lt_d_index = 0
    for i in range(len(kdj_k) - 1, len(kdj_k) - n - 1, -1):
        if kdj_k.iloc[i] < kdj_d.iloc[i]:
            k_lt_d = True
            k_lt_d_index = i
            break

    if not k_lt_d:
        return False

    # 从 dif_lt_dea_index 开始找到 dif > dea 的 K 线
    for j in range(k_lt_d_index, len(kdj_k), 1):
        if kdj_k.iloc[j] > kdj_d.iloc[j]:
            return True

    return False


def is_bullish(instId: str, default_df: Optional[pd.DataFrame] = None) -> bool:
    """判断是否存在看涨信号.

    Args:
        instId: 交易对
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
    # return is_macd_bullish(instId, default_df) and is_kdj_bullish(instId, default_df)
    # return is_kdj_bullish(instId, default_df)
    # return is_macd_bullish(instId, default_df)
    return is_zero_axis_golden_cross(instId, n=1, default_df=default_df)


def strategy1(
    instId: str, n: int = 1, default_df: Optional[pd.DataFrame] = None
) -> bool:
    """策略1

    需要同时满足以下条件:

    1. MACD 金叉
    2. KDJ 金叉
    3. Boll 上穿

    这三个条件在最近 n 个 K 线内同时满足.

    Args:
        instId: 交易对
        n: 最近 n 个 K 线, 默认为 1
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取
    """
    cond1 = is_golden_cross_macd(instId, n, default_df)
    cond2 = is_kdj_bullish(instId, n, default_df)
    cond3 = middleband_inside_candle(instId, n, default_df)
    return cond1 and cond3 and cond2


if __name__ == "__main__":
    with open("swap_tickers.json", "r") as f:
        data = json.load(f)

    # instId = "TURBO-USDT-SWAP"
    # df = get_candlesticks(instId)
    # if strategy1(instId, default_df=df):
    #     print(f"{instId} is bullish")

    results = []
    for item in data:
        instId = item["instId"]
        df = get_candlesticks(instId, bar="1H")
        if strategy1(instId, 10, df):
            results.append(instId)

    print(results)
