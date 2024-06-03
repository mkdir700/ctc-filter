import pandas as pd
import talib as ta
from typing_extensions import override

from ctc_filter.filter import Filter


def is_kdj_bullish(df: pd.DataFrame, n: int = 1) -> bool:
    """判断是否存在 KDJ 看涨信号(K 大于 D).

    Args:
        instId: 交易对
        n: 最近 n 根 K 线，默认为 1，即最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
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


def middleband_inside_candle(df: pd.DataFrame, n: int = 1) -> bool:
    """判断中轨是否在 K 线内部

    Args:
        instId: 交易对
        n: 时间范围, 默认为 1, 表示最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
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


def is_boll_bullish(df: pd.DataFrame, n: int = 1) -> bool:
    """判断是否存在 Boll 看涨信号(收盘价大于中轨且小于上轨).

    Args:
        instId: 交易对
        n: 时间范围, 默认为 1, 表示最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
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


def is_zero_axis_golden_cross(df: pd.DataFrame, n: int = 1) -> bool:
    """判断是否存在零轴金叉信号(MACD 柱状图由负变正).

    Args:
        instId: 交易对
        n: 默认为 1, 表示最近 1 个 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取
    """
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


def is_golden_cross_macd(
    df: pd.DataFrame,
    n: int = 1,
) -> bool:
    """判断是否存在 MACD 看涨信号(DIF 大于 DEA 且 MACD 柱状图大于 0).

    Args:
        instId: 交易对
        n: 最近 n 根 K 线，默认为 1，即最近 1 根 K 线
        default_df: K 线数据, 默认为 None, 由调用者传入, 避免重复获取

    Returns:
        bool: 是否满足规则
    """
    # 计算 MACD
    assert hasattr(ta, "MACD"), "MACD not found in talib"
    dif, dea, macd = ta.MACD(df["close"], fastperiod=12, slowperiod=26, signalperiod=9)  # type: ignore
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


class SampleFilter(Filter):
    name = "Sample Filter"
    description = """
    需要同时满足以下条件：
    1. n 根 K 线内部存在 macd 金叉信号
    2. n 根 K 线内部中轨在 K 线内部
    3. n 根 K 线内部存在 KDJ 看涨信号
    """

    @override
    def filter(self) -> bool:
        n = 5
        cond1 = is_golden_cross_macd(self.df, n)
        cond2 = middleband_inside_candle(self.df, n)
        cond3 = is_kdj_bullish(self.df, n)
        return cond1 and cond2 and cond3
