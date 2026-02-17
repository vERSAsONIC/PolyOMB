#!/usr/bin/env python3
"""
00002 data_adapter.py - 数据适配器模块

提供 SMB 数据读取、Parquet 文件解析、数据转换功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple, List
from pathlib import Path


class SMBDataAdapter:
    """SMB 数据适配器"""
    
    def __init__(self, smb_url: str, mount_point: str = "/tmp/smb-mount"):
        """
        初始化 SMB 适配器
        
        Args:
            smb_url: SMB URL
            mount_point: 本地挂载点
        """
        self.smb_url = smb_url
        self.mount_point = mount_point
        self._is_mounted = False
        self._cache = {}
        self.cache_hits = 0
    
    def mount(self) -> bool:
        """挂载 SMB 共享"""
        # 模拟挂载成功
        self._is_mounted = True
        return True
    
    def unmount(self) -> bool:
        """卸载 SMB 共享"""
        self._is_mounted = False
        return True
    
    def is_mounted(self) -> bool:
        """检查是否已挂载"""
        return self._is_mounted
    
    def read_parquet(self, relative_path: str) -> pd.DataFrame:
        """
        读取 Parquet 文件
        
        Args:
            relative_path: 相对于挂载点的路径
        
        Returns:
            DataFrame
        """
        if not self._is_mounted:
            raise RuntimeError("SMB not mounted")
        
        full_path = Path(self.mount_point) / relative_path
        
        if not full_path.exists():
            return pd.DataFrame()
        
        return pd.read_parquet(full_path)
    
    def get_market_trades(
        self, 
        market_id: str, 
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取特定市场的交易数据
        
        Args:
            market_id: 市场 ID
            use_cache: 是否使用缓存
        
        Returns:
            交易数据 DataFrame
        """
        cache_key = f"trades_{market_id}"
        
        if use_cache and cache_key in self._cache:
            self.cache_hits += 1
            return self._cache[cache_key]
        
        # 从 trades 目录读取
        relative_path = f"polymarket/trades/{market_id}.parquet"
        df = self.read_parquet(relative_path)
        
        if use_cache:
            self._cache[cache_key] = df
        
        return df
    
    def get_market_metadata(self, market_id: str) -> Dict:
        """
        获取市场元数据
        
        Args:
            market_id: 市场 ID
        
        Returns:
            元数据字典
        """
        # 读取 markets.parquet
        markets_df = self.read_parquet("polymarket/markets.parquet")
        
        if markets_df.empty:
            return {}
        
        # 查找对应市场
        market = markets_df[markets_df['condition_id'] == market_id]
        
        if market.empty:
            return {
                "condition_id": market_id,
                "question": "Unknown",
                "category": "Unknown",
            }
        
        return market.iloc[0].to_dict()
    
    def calculate_market_volatility(
        self,
        market_id: str,
        window: str = "3h"
    ) -> float:
        """
        计算市场波动率
        
        Args:
            market_id: 市场 ID
            window: 计算窗口
        
        Returns:
            波动率值
        """
        trades = self.get_market_trades(market_id)
        
        if trades.empty or len(trades) < 2:
            return 0.0
        
        # 确保时间戳列为 datetime
        trades['timestamp'] = pd.to_datetime(trades['timestamp'])
        trades = trades.sort_values('timestamp')
        
        # 计算对数收益率
        log_returns = np.log(trades['price'] / trades['price'].shift(1)).dropna()
        
        if log_returns.empty:
            return 0.0
        
        return float(log_returns.std())
    
    def enable_cache(self):
        """启用缓存"""
        pass  # 缓存默认启用
    
    def invalidate_cache(self):
        """失效缓存"""
        self._cache = {}
        self.cache_hits = 0


class LocalDataAdapter:
    """本地数据适配器（用于测试）"""
    
    def __init__(self, data_path: str):
        """
        初始化本地适配器
        
        Args:
            data_path: 数据目录路径
        """
        self.data_path = Path(data_path)
    
    def read_parquet(self, relative_path: str) -> pd.DataFrame:
        """读取 Parquet 文件"""
        full_path = self.data_path / relative_path
        
        if not full_path.exists():
            return pd.DataFrame()
        
        return pd.read_parquet(full_path)
    
    def get_market_trades(self, market_id: str) -> pd.DataFrame:
        """获取市场交易数据"""
        relative_path = f"polymarket/trades/{market_id}.parquet"
        return self.read_parquet(relative_path)


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
        价格序列
    """
    if df.empty:
        return pd.Series(dtype=float)
    
    df_copy = df.copy()
    df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col])
    df_copy = df_copy.set_index(timestamp_col).sort_index()
    
    # 使用最后成交价
    price_series = df_copy[price_col].resample(interval).last().dropna()
    
    return price_series


def build_orderbook_snapshot(
    df: pd.DataFrame,
    timestamp: datetime,
    window: timedelta = timedelta(minutes=5)
) -> Dict:
    """
    从交易数据重建订单簿快照
    
    Args:
        df: 交易数据
        timestamp: 目标时间戳
        window: 时间窗口
    
    Returns:
        订单簿字典
    """
    if df.empty:
        return {}
    
    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    
    # 筛选时间窗口内的交易
    start_time = timestamp - window
    end_time = timestamp + window
    
    window_trades = df_copy[
        (df_copy['timestamp'] >= start_time) & 
        (df_copy['timestamp'] <= end_time)
    ]
    
    if window_trades.empty:
        return {}
    
    # 构建简化订单簿
    buys = window_trades[window_trades['side'] == 'BUY']
    sells = window_trades[window_trades['side'] == 'SELL']
    
    orderbook = {
        'timestamp': timestamp,
        'best_bid': buys['price'].max() if not buys.empty else None,
        'best_ask': sells['price'].min() if not sells.empty else None,
        'bid_volume': buys['size'].sum() if not buys.empty else 0,
        'ask_volume': sells['size'].sum() if not sells.empty else 0,
    }
    
    if orderbook['best_bid'] and orderbook['best_ask']:
        orderbook['spread'] = orderbook['best_ask'] - orderbook['best_bid']
    
    return orderbook


def convert_to_strategy_format(
    trades: pd.DataFrame,
    metadata: Dict
) -> pd.DataFrame:
    """
    转换为策略内部格式
    
    Args:
        trades: 原始交易数据
        metadata: 市场元数据
    
    Returns:
        策略格式 DataFrame
    """
    if trades.empty:
        return pd.DataFrame()
    
    df = trades.copy()
    
    # 确保时间戳列存在
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # 添加元数据列
    df['tick_size'] = metadata.get('tick_size', 0.01)
    
    return df


def get_lifecycle_date_range(df: pd.DataFrame) -> Tuple[datetime, datetime]:
    """
    获取数据的生命周期日期范围
    
    Args:
        df: 数据 DataFrame
    
    Returns:
        (开始时间, 结束时间) 元组
    """
    if df.empty or 'timestamp' not in df.columns:
        return datetime.now(), datetime.now()
    
    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    
    return df_copy['timestamp'].min(), df_copy['timestamp'].max()


def get_full_year_date_range(df: pd.DataFrame) -> Tuple[datetime, datetime]:
    """
    获取全年日期范围
    
    Args:
        df: 数据 DataFrame
    
    Returns:
        (年初, 年末) 元组
    """
    if df.empty or 'timestamp' not in df.columns:
        year = datetime.now().year
        return datetime(year, 1, 1), datetime(year, 12, 31)
    
    df_copy = df.copy()
    df_copy['timestamp'] = pd.to_datetime(df_copy['timestamp'])
    
    data_year = df_copy['timestamp'].dt.year.mode()[0]
    
    return datetime(data_year, 1, 1), datetime(data_year, 12, 31)


def filter_by_date_range(
    df: pd.DataFrame,
    start: datetime,
    end: datetime,
    timestamp_col: str = "timestamp"
) -> pd.DataFrame:
    """
    按日期范围过滤数据
    
    Args:
        df: 数据 DataFrame
        start: 开始时间
        end: 结束时间
        timestamp_col: 时间戳列名
    
    Returns:
        过滤后的 DataFrame
    """
    if df.empty or timestamp_col not in df.columns:
        return df
    
    df_copy = df.copy()
    df_copy[timestamp_col] = pd.to_datetime(df_copy[timestamp_col])
    
    mask = (df_copy[timestamp_col] >= start) & (df_copy[timestamp_col] <= end)
    return df_copy[mask]


def validate_trades_df(
    df: pd.DataFrame,
    required_columns: Optional[List[str]] = None
) -> bool:
    """
    验证交易数据 DataFrame
    
    Args:
        df: 数据 DataFrame
        required_columns: 必需列列表
    
    Returns:
        是否有效
    
    Raises:
        ValueError: 验证失败
    """
    if required_columns is None:
        required_columns = ['timestamp', 'market', 'price', 'size', 'side']
    
    if df.empty:
        raise ValueError("Empty DataFrame")
    
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    return True
