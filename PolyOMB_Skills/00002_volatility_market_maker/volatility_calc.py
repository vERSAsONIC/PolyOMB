"""
00002 volatility_calc.py - 波动率计算模块

提供波动率计算功能，包括:
- 对数收益率波动率
- 滚动窗口波动率
- 波动率阈值检查
"""

import numpy as np
import pandas as pd
from typing import Union


def calculate_volatility(prices: Union[pd.Series, np.ndarray]) -> float:
    """
    计算价格序列的波动率（对数收益率标准差）
    
    公式: std(log(price[i] / price[i-1]))
    
    Args:
        prices: 价格序列
        
    Returns:
        波动率值（标准差）
        
    Raises:
        ValueError: 空序列或数据不足
    """
    prices = pd.Series(prices)
    
    # 检查空序列
    if len(prices) == 0:
        raise ValueError("Empty price series")
    
    # 检查数据点不足
    if len(prices) < 2:
        raise ValueError("Insufficient data points: need at least 2 prices")
    
    # 移除 NaN 和无效值
    prices = prices.dropna()
    prices = prices[prices > 0]  # 价格必须为正
    
    if len(prices) < 2:
        return 0.0
    
    # 计算对数收益率
    # log_return[i] = log(price[i] / price[i-1])
    log_returns = np.log(prices / prices.shift(1)).dropna()
    
    if len(log_returns) == 0:
        return 0.0
    
    # 返回样本标准差 (ddof=1)
    return float(log_returns.std(ddof=1))


def calculate_rolling_volatility(
    df: pd.DataFrame,
    price_col: str = "price",
    timestamp_col: str = "timestamp",
    window: str = "3h",
    min_periods: int = 10
) -> pd.Series:
    """
    计算滚动窗口波动率
    
    基于时间窗口的滚动对数收益率标准差
    
    Args:
        df: 包含价格和时间戳的 DataFrame
        price_col: 价格列名
        timestamp_col: 时间戳列名
        window: 滚动窗口大小 (如 "3h", "1h", "30min")
        min_periods: 最小周期数
        
    Returns:
        滚动波动率序列 (与输入相同长度)
    """
    df = df.copy()
    
    # 确保时间戳格式正确
    df[timestamp_col] = pd.to_datetime(df[timestamp_col])
    
    # 按时间排序
    df = df.sort_values(timestamp_col)
    
    # 设置时间索引
    df_indexed = df.set_index(timestamp_col)
    
    # 计算对数收益率
    df_indexed['log_return'] = np.log(
        df_indexed[price_col] / df_indexed[price_col].shift(1)
    )
    
    # 滚动标准差 (时间窗口)
    rolling_vol = df_indexed['log_return'].rolling(
        window=window,
        min_periods=min_periods
    ).std(ddof=1)
    
    # 重置索引，保持与原 DataFrame 相同的顺序
    df_indexed['volatility'] = rolling_vol
    
    # 按照原始索引排序并返回
    result = df_indexed.reset_index()
    result = result.sort_index()
    
    return result['volatility']


def should_pause_trading(volatility: float, threshold: float = 0.15) -> bool:
    """
    检查是否应该因高波动率暂停交易
    
    保守策略: volatility >= threshold 时暂停
    
    Args:
        volatility: 当前波动率
        threshold: 波动率阈值
        
    Returns:
        True 如果应暂停交易
    """
    # 处理 NaN 值
    if pd.isna(volatility):
        return False
    
    return volatility >= threshold


def extract_price_series(
    df: pd.DataFrame,
    interval: str = "1min"
) -> pd.Series:
    """
    从交易数据提取价格序列
    
    将不规则时间序列重采样为规则时间序列
    
    Args:
        df: 交易数据 DataFrame
        interval: 重采样间隔 (如 "1min", "5min", "1h")
        
    Returns:
        价格时间序列
    """
    df = df.copy()
    
    # 确保时间戳格式正确
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 按时间排序
    df = df.sort_values('timestamp')
    
    # 设置时间索引
    df = df.set_index('timestamp')
    
    # 重采样: 取每个区间的最后价格
    price_series = df['price'].resample(interval).last()
    
    # 前向填充缺失值 (使用上一个已知价格)
    price_series = price_series.ffill()
    
    # 移除任何剩余的 NaN
    price_series = price_series.dropna()
    
    return price_series


def calculate_hourly_volatility(df: pd.DataFrame) -> pd.Series:
    """
    按小时计算波动率
    
    返回每小时的波动率序列
    
    Args:
        df: 交易数据
        
    Returns:
        每小时波动率序列 (索引为小时)
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df.set_index('timestamp', inplace=True)
    
    # 按小时重采样，计算每小时的标准差
    hourly_vol = df['price'].resample('1h').apply(
        lambda x: calculate_volatility(x) if len(x) >= 2 else np.nan
    )
    
    # 移除 NaN
    hourly_vol = hourly_vol.dropna()
    
    return hourly_vol


def add_volatility_column(
    df: pd.DataFrame,
    window: str = "3h",
    min_periods: int = 10,
    output_col: str = "3_hour"
) -> pd.DataFrame:
    """
    为 DataFrame 添加波动率列
    
    模拟 poly-maker 中的 row['3_hour'] 字段
    
    Args:
        df: 输入数据
        window: 滚动窗口
        min_periods: 最小周期
        output_col: 输出列名
        
    Returns:
        添加波动率列后的 DataFrame
    """
    df = df.copy()
    
    # 计算滚动波动率
    vol_series = calculate_rolling_volatility(
        df, 
        window=window, 
        min_periods=min_periods
    )
    
    # 添加为新列
    df[output_col] = vol_series.values
    
    return df
