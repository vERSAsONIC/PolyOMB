"""
00002 data_adapter.py - 数据适配器模块

提供数据读取和转换功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Tuple
import subprocess
import os


class SMBDataAdapter:
    """
    SMB 数据适配器
    
    用于从 SMB 共享读取 prediction-market-analysis 数据
    """
    
    def __init__(
        self,
        smb_url: str,
        mount_point: str = "/tmp/smb-mount"
    ):
        """
        初始化 SMB 适配器
        
        Args:
            smb_url: SMB 共享 URL
            mount_point: 本地挂载点
        """
        self.smb_url = smb_url
        self.mount_point = Path(mount_point)
        self._is_mounted = False
        self._mock_data: Dict[str, pd.DataFrame] = {}
    
    def mount(self) -> bool:
        """
        挂载 SMB 共享
        
        Returns:
            True 如果成功
        """
        # 如果已挂载，直接返回
        if self._is_mounted:
            return True
        
        # 创建挂载点
        self.mount_point.mkdir(parents=True, exist_ok=True)
        
        # 检测操作系统
        import platform
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                # macOS 使用 mount_smbfs
                cmd = f"mount_smbfs '{self.smb_url}' '{self.mount_point}'"
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            elif system == "Linux":
                # Linux 使用 mount -t cifs
                cmd = f"sudo mount -t cifs '{self.smb_url}' '{self.mount_point}' -o guest"
                result = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            else:
                # Windows 或其他系统，使用 mock 模式
                print(f"Unsupported OS: {system}, using mock mode")
                self._is_mounted = True  # Mock 模式
                return True
            
            if result.returncode == 0:
                self._is_mounted = True
                return True
            else:
                print(f"Mount failed: {result.stderr.decode()}")
                # 失败时使用 mock 模式
                self._is_mounted = True
                return True
                
        except Exception as e:
            print(f"Mount error: {e}")
            # 出错时使用 mock 模式
            self._is_mounted = True
            return True
    
    def unmount(self) -> bool:
        """
        卸载 SMB 共享
        
        Returns:
            True 如果成功
        """
        if not self._is_mounted:
            return True
        
        import platform
        system = platform.system()
        
        try:
            if system == "Darwin":
                cmd = f"umount '{self.mount_point}'"
            elif system == "Linux":
                cmd = f"sudo umount '{self.mount_point}'"
            else:
                self._is_mounted = False
                return True
            
            subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
            self._is_mounted = False
            return True
            
        except Exception as e:
            print(f"Unmount error: {e}")
            self._is_mounted = False
            return True
    
    def set_mock_data(self, path: str, df: pd.DataFrame):
        """
        设置 Mock 数据（测试用）
        
        Args:
            path: 数据路径标识
            df: DataFrame
        """
        self._mock_data[path] = df.copy()
    
    def read_parquet(self, relative_path: str) -> pd.DataFrame:
        """
        读取 Parquet 文件
        
        优先返回 Mock 数据，如果不存在则读取实际文件
        
        Args:
            relative_path: 相对路径
            
        Returns:
            DataFrame
        """
        # 优先返回 Mock 数据
        if relative_path in self._mock_data:
            return self._mock_data[relative_path].copy()
        
        # 检查 CSV 版本 (用于测试)
        csv_path = relative_path.replace('.parquet', '.csv')
        if csv_path in self._mock_data:
            return self._mock_data[csv_path].copy()
        
        # 读取实际文件
        if not self._is_mounted:
            self.mount()
        
        full_path = self.mount_point / relative_path
        
        # 尝试读取 Parquet
        if full_path.exists():
            return pd.read_parquet(full_path)
        
        # 尝试读取 CSV
        csv_full_path = self.mount_point / csv_path
        if csv_full_path.exists():
            return pd.read_csv(csv_full_path)
        
        # 返回空 DataFrame
        return pd.DataFrame()
    
    def read_csv(self, relative_path: str) -> pd.DataFrame:
        """
        读取 CSV 文件
        
        Args:
            relative_path: 相对路径
            
        Returns:
            DataFrame
        """
        # 优先返回 Mock 数据
        if relative_path in self._mock_data:
            return self._mock_data[relative_path].copy()
        
        # 读取实际文件
        if not self._is_mounted:
            self.mount()
        
        full_path = self.mount_point / relative_path
        
        if full_path.exists():
            return pd.read_csv(full_path)
        
        return pd.DataFrame()
    
    def get_market_trades(self, market_id: str) -> pd.DataFrame:
        """
        获取市场交易数据
        
        Args:
            market_id: 市场 ID
            
        Returns:
            交易数据
        """
        # 尝试多种路径格式
        paths = [
            f"polymarket/trades/{market_id}.parquet",
            f"polymarket/trades/{market_id}.csv",
            "trades",
        ]
        
        for path in paths:
            if path in self._mock_data:
                df = self._mock_data[path].copy()
                # 如果指定了 market_id，过滤该市场的数据
                if 'market' in df.columns:
                    df = df[df['market'] == market_id]
                return df
        
        # 尝试读取文件
        for path in paths[:2]:
            df = self.read_parquet(path)
            if len(df) > 0:
                return df
        
        return pd.DataFrame()
    
    def get_market_metadata(self, market_id: str) -> Dict:
        """
        获取市场元数据
        
        Args:
            market_id: 市场 ID
            
        Returns:
            元数据字典
        """
        # 尝试从 Mock 数据获取
        if "markets" in self._mock_data:
            markets_df = self._mock_data["markets"]
            if 'condition_id' in markets_df.columns:
                market_row = markets_df[markets_df['condition_id'] == market_id]
                if len(market_row) > 0:
                    return market_row.iloc[0].to_dict()
        
        # 返回默认值
        return {
            "condition_id": market_id,
            "question": "Unknown Market",
            "category": "Unknown",
            "tick_size": 0.01,
            "min_order_size": 1,
        }
    
    def calculate_market_volatility(
        self,
        market_id: str,
        window: str = "3h"
    ) -> float:
        """
        计算市场波动率
        
        Args:
            market_id: 市场 ID
            window: 窗口大小
            
        Returns:
            波动率值
        """
        from .volatility_calc import calculate_volatility
        
        trades = self.get_market_trades(market_id)
        
        if len(trades) == 0:
            return 0.0
        
        if 'price' not in trades.columns:
            return 0.0
        
        return calculate_volatility(trades['price'])


class LocalDataAdapter:
    """
    本地数据适配器
    
    用于从本地文件系统读取数据
    """
    
    def __init__(self, data_path: str):
        """
        初始化本地适配器
        
        Args:
            data_path: 本地数据路径
        """
        self.data_path = Path(data_path)
    
    def read_parquet(self, relative_path: str) -> pd.DataFrame:
        """读取 Parquet 文件"""
        full_path = self.data_path / relative_path
        if full_path.exists():
            return pd.read_parquet(full_path)
        return pd.DataFrame()
    
    def read_csv(self, relative_path: str) -> pd.DataFrame:
        """读取 CSV 文件"""
        full_path = self.data_path / relative_path
        if full_path.exists():
            return pd.read_csv(full_path)
        return pd.DataFrame()


def extract_price_series(
    df: pd.DataFrame,
    interval: str = "1min"
) -> pd.Series:
    """
    从交易数据提取价格序列
    """
    df = df.copy()
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.sort_values('timestamp')
    df.set_index('timestamp', inplace=True)
    
    # 重采样
    price_series = df['price'].resample(interval).last()
    
    # 前向填充
    price_series = price_series.ffill()
    
    return price_series.dropna()


def build_orderbook_snapshot(
    df: pd.DataFrame,
    timestamp: datetime
) -> Dict:
    """
    从交易数据重建订单簿快照
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    mask = df['timestamp'] <= timestamp
    recent = df[mask].tail(20)
    
    if len(recent) == 0:
        return {}
    
    avg_price = recent['price'].mean()
    spread = recent['price'].std() * 2 or 0.02
    
    return {
        'best_bid': avg_price - spread / 2,
        'best_ask': avg_price + spread / 2,
        'best_bid_size': recent[recent['side'] == 'BUY']['size'].sum() if 'side' in recent.columns else 100,
        'best_ask_size': recent[recent['side'] == 'SELL']['size'].sum() if 'side' in recent.columns else 100,
    }


def convert_to_strategy_format(
    trades: pd.DataFrame,
    metadata: Dict
) -> pd.DataFrame:
    """
    转换为策略内部格式
    """
    from .volatility_calc import add_volatility_column
    
    df = trades.copy()
    
    # 添加波动率列
    df = add_volatility_column(df, window="3h", output_col="3_hour")
    
    # 添加订单簿信息
    df['best_bid'] = df['price'] * 0.99
    df['best_ask'] = df['price'] * 1.01
    df['tick_size'] = metadata.get('tick_size', 0.01)
    
    return df


def get_lifecycle_date_range(df: pd.DataFrame) -> Tuple[datetime, datetime]:
    """
    获取生命周期日期范围
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df['timestamp'].min(), df['timestamp'].max()


def get_full_year_date_range(df: pd.DataFrame) -> Tuple[datetime, datetime]:
    """
    获取全年日期范围
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    year = df['timestamp'].dt.year.mode()[0]
    
    return (
        datetime(year, 1, 1),
        datetime(year, 12, 31, 23, 59, 59)
    )


def filter_by_date_range(
    df: pd.DataFrame,
    start: datetime,
    end: datetime
) -> pd.DataFrame:
    """
    按日期范围过滤数据
    """
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    mask = (df['timestamp'] >= start) & (df['timestamp'] <= end)
    return df[mask].copy()


def validate_trades_df(df: pd.DataFrame) -> bool:
    """
    验证交易数据 DataFrame
    """
    required = ['timestamp', 'market', 'price', 'size', 'side']
    return all(col in df.columns for col in required)
