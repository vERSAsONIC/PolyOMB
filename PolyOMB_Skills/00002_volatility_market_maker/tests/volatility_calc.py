#!/usr/bin/env python3
"""
00002 volatility_calc.py - 波动率计算模块

提供波动率计算的核心函数，用于预测市场做市策略
"""

import pandas as pd
import numpy as np
from typing import Optional, Tuple


def calculate_volatility(
    prices: pd.Series,
    window: Optional[int] = None,
    min_periods: int = 2
) -> float:
    """
    计算价格序列的波动率（对数收益率标准差）
    
    Args:
        prices: 价格序列
        window: 滚动窗口大小（None表示使用全部数据）
        min_periods: 最小有效数据点数量
    
    Returns:
        波动率值（对数收益率标准差）
    
    Raises:
        ValueError: 空序列或数据不足
    """
    if prices is None or len(prices) == 0:
        raise ValueError("Empty price series")
    
    if len(prices) < min_periods:
        raise ValueError(f"Insufficient data points: {len(prices)} < {min_periods}")
    
    # 处理 NaN 值
    clean_prices = prices.dropna()
    if len(clean_prices) < min_periods:
        raise ValueError("Too many NaN values in price series")
    
    # 计算对数收益率
    log_returns = np.log(clean_prices / clean_prices.shift(1)).dropna()
    
    if len(log_returns) == 0:
        return 0.0
    
    if window is not None and len(log_returns) >= window:
        log_returns = log_returns.iloc[-window:]
    
    # 计算标准差（使用样本标准差 ddof=1）
    volatility = log_returns.std(ddof=1)
    
    # 处理 NaN 和无穷值
    if pd.isna(volatility) or np.isinf(volatility):
        return 0.0
    
    return float(volatility)


def calculate_rolling_volatility(
    df: pd.DataFrame,
    price_col: str = "price",
    timestamp_col: str = "timestamp",
    window: str = "3h",
    min_periods: int = 10
) -> pd.Series:
    """
    计算滚动波动率
    
    Args:
        df: 包含交易数据的 DataFrame
        price_col: 价格列名
        timestamp_col: 时间戳列名
        window: 滚动窗口（如 '3h', '1D'）
        min_periods: 最小有效数据点数量
    
    Returns:
        滚动波动率序列
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    # 确保时间戳列为索引
    df_copy = df.copy()
    if timestamp_col in df_copy.columns:
        df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col])
        df_copy = df_copy.set_index(timestamp_col).sort_index()
    
    # 计算对数收益率
    log_returns = np.log(df_copy[price_col] / df_copy[price_col].shift(1))
    
    # 计算滚动标准差
    rolling_vol = log_returns.rolling(window=window, min_periods=min_periods).std()
    
    # 重新对齐到原始索引
    if timestamp_col in df.columns:
        rolling_vol = rolling_vol.reindex(df[timestamp_col]).reset_index(drop=True)
    
    return rolling_vol


def should_pause_trading(volatility: float, threshold: float) -> bool:
    """
    根据波动率判断是否暂停交易
    
    Args:
        volatility: 当前波动率
        threshold: 波动率阈值
    
    Returns:
        是否应暂停交易
    """
    # 保守策略：达到阈值即暂停
    return volatility >= threshold


def extract_price_series(
    df: pd.DataFrame,
    interval: str = "1min",
    price_col: str = "price",
    timestamp_col: str = "timestamp"
) -> pd.Series:
    """
    从交易数据提取价格时间序列
    
    Args:
        df: 交易数据 DataFrame
        interval: 重采样间隔
        price_col: 价格列名
        timestamp_col: 时间戳列名
    
    Returns:
        重采样后的价格序列
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    df_copy = df.copy()
    df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col])
    df_copy = df_copy.set_index(timestamp_col).sort_index()
    
    # 使用最后成交价作为该间隔的价格
    price_series = df_copy[price_col].resample(interval).last().dropna()
    
    return price_series


def calculate_hourly_volatility(
    df: pd.DataFrame,
    price_col: str = "price",
    timestamp_col: str = "timestamp"
) -> pd.Series:
    """
    按小时计算波动率
    
    Args:
        df: 交易数据 DataFrame
        price_col: 价格列名
        timestamp_col: 时间戳列名
    
    Returns:
        每小时波动率序列
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    df_copy = df.copy()
    df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col])
    df_copy = df_copy.set_index(timestamp_col).sort_index()
    
    # 计算对数收益率
    log_returns = np.log(df_copy[price_col] / df_copy[price_col].shift(1))
    
    # 按小时聚合计算标准差
    hourly_vol = log_returns.resample("1h").std()
    
    return hourly_vol


def add_volatility_column(
    df: pd.DataFrame,
    window: str = "3h",
    min_periods: int = 10,
    price_col: str = "price",
    timestamp_col: str = "timestamp",
    output_col: str = "3_hour"
) -> pd.DataFrame:
    """
    向 DataFrame 添加波动率列
    
    Args:
        df: 输入 DataFrame
        window: 滚动窗口
        min_periods: 最小数据点
        price_col: 价格列名
        timestamp_col: 时间戳列名
        output_col: 输出列名
    
    Returns:
        添加了波动率列的 DataFrame
    """
    df_copy = df.copy()
    df_copy[output_col] = calculate_rolling_volatility(
        df_copy,
        price_col=price_col,
        timestamp_col=timestamp_col,
        window=window,
        min_periods=min_periods
    )
    return df_copy
