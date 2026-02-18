"""
00002 market_data_loader.py - 高效市场数据加载器

提供带本地缓存的市场数据加载功能，支持：
- 本地缓存避免重复读取 SMB
- 市场-区块索引快速定位数据
- 按市场 ID 查询交易数据
"""

import pandas as pd
import numpy as np
import json
import os
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import hashlib
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MarketDataLoader:
    """
    高效市场数据加载器
    
    特性：
    1. 本地缓存机制 - 避免重复读取 SMB
    2. 智能索引 - 快速定位市场对应的区块范围
    3. 增量更新 - 只读取新数据
    """
    
    # SMB 默认路径
    DEFAULT_SMB_PATH = "/Volumes/liuqiong/prediction-market-analysis/data"
    
    def __init__(
        self,
        data_path: Optional[str] = None,
        cache_dir: str = "~/.cache/polymarket",
        use_cache: bool = True
    ):
        """
        初始化数据加载器
        
        Args:
            data_path: 数据源路径 (默认使用 SMB 挂载点)
            cache_dir: 本地缓存目录
            use_cache: 是否使用缓存
        """
        self.data_path = Path(data_path or self.DEFAULT_SMB_PATH)
        self.cache_dir = Path(cache_dir).expanduser()
        self.use_cache = use_cache
        
        # 创建缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.trades_cache_dir = self.cache_dir / "trades"
        self.trades_cache_dir.mkdir(exist_ok=True)
        
        # 索引文件路径
        self.index_file = self.cache_dir / "market_block_index.pkl"
        self.markets_cache = self.cache_dir / "markets.parquet"
        
        # 内存缓存
        self._markets_df: Optional[pd.DataFrame] = None
        self._market_index: Optional[Dict[str, List[Tuple[int, int]]]] = None
        self._loaded_trades_files: Set[str] = set()
        
        logger.info(f"MarketDataLoader 初始化完成")
        logger.info(f"  数据源: {self.data_path}")
        logger.info(f"  缓存目录: {self.cache_dir}")
    
    def _get_cache_key(self, market_id: str) -> str:
        """生成缓存键"""
        return hashlib.md5(market_id.encode()).hexdigest()[:16]
    
    def _get_market_cache_path(self, market_id: str) -> Path:
        """获取市场缓存文件路径"""
        cache_key = self._get_cache_key(market_id)
        return self.trades_cache_dir / f"{cache_key}.parquet"
    
    def _load_markets(self, force_reload: bool = False) -> pd.DataFrame:
        """
        加载市场元数据
        
        Args:
            force_reload: 强制重新加载
            
        Returns:
            市场元数据 DataFrame
        """
        if self._markets_df is not None and not force_reload:
            return self._markets_df
        
        # 检查本地缓存
        if self.use_cache and self.markets_cache.exists() and not force_reload:
            logger.info("从本地缓存加载 markets 数据...")
            self._markets_df = pd.read_parquet(self.markets_cache)
            return self._markets_df
        
        # 从 SMB 加载
        markets_file = self.data_path / "polymarket" / "markets" / "markets_0_10000.parquet"
        
        if not markets_file.exists():
            logger.warning(f"Markets 文件不存在: {markets_file}")
            return pd.DataFrame()
        
        logger.info("从 SMB 加载 markets 数据...")
        self._markets_df = pd.read_parquet(markets_file)
        
        # 保存到本地缓存
        if self.use_cache:
            self._markets_df.to_parquet(self.markets_cache)
            logger.info(f"已缓存 {len(self._markets_df)} 条市场记录")
        
        return self._markets_df
    
    def get_market_info(self, market_id: str) -> Optional[Dict]:
        """
        获取市场详细信息
        
        Args:
            market_id: 市场 condition_id
            
        Returns:
            市场信息字典，如果不存在返回 None
        """
        markets_df = self._load_markets()
        
        if 'condition_id' not in markets_df.columns:
            return None
        
        market_row = markets_df[markets_df['condition_id'] == market_id]
        
        if len(market_row) == 0:
            return None
        
        info = market_row.iloc[0].to_dict()
        
        # 解析 JSON 字段
        for field in ['outcomes', 'outcome_prices', 'clob_token_ids']:
            if field in info and isinstance(info[field], str):
                try:
                    info[field] = json.loads(info[field])
                except:
                    pass
        
        return info
    
    def _get_token_ids_for_market(self, market_id: str) -> List[str]:
        """获取市场的 token IDs"""
        info = self.get_market_info(market_id)
        
        if not info:
            return []
        
        token_ids = info.get('clob_token_ids', [])
        
        # 确保是列表
        if isinstance(token_ids, str):
            try:
                token_ids = json.loads(token_ids)
            except:
                token_ids = []
        
        # 转为字符串
        return [str(tid) for tid in token_ids]
    
    def _scan_trades_files(self) -> List[Tuple[int, int, Path]]:
        """
        扫描可用的交易文件
        
        Returns:
            列表，每项为 (start_block, end_block, file_path)
        """
        trades_dir = self.data_path / "polymarket" / "trades"
        
        if not trades_dir.exists():
            logger.warning(f"Trades 目录不存在: {trades_dir}")
            return []
        
        files = []
        
        # 只读取少量文件避免超时
        try:
            for entry in os.scandir(trades_dir):
                if entry.is_file() and entry.name.startswith('trades_') and entry.name.endswith('.parquet'):
                    # 解析文件名: trades_{start}_{end}.parquet
                    try:
                        parts = entry.name.replace('trades_', '').replace('.parquet', '').split('_')
                        start_block = int(parts[0])
                        end_block = int(parts[1])
                        files.append((start_block, end_block, Path(entry.path)))
                    except:
                        continue
        except Exception as e:
            logger.error(f"扫描 trades 文件失败: {e}")
        
        # 按区块号排序
        files.sort()
        return files
    
    def _build_market_index(self, force_rebuild: bool = False) -> Dict[str, List[Tuple[int, int]]]:
        """
        构建市场-区块索引
        
        Args:
            force_rebuild: 强制重建索引
            
        Returns:
            索引字典 {market_id: [(start_block, end_block), ...]}
        """
        if self._market_index is not None and not force_rebuild:
            return self._market_index
        
        # 检查缓存的索引
        if self.use_cache and self.index_file.exists() and not force_rebuild:
            logger.info("从缓存加载市场索引...")
            with open(self.index_file, 'rb') as f:
                self._market_index = pickle.load(f)
            return self._market_index
        
        logger.info("构建市场-区块索引...")
        
        # 获取所有市场
        markets_df = self._load_markets()
        
        # 初始化索引
        index: Dict[str, List[Tuple[int, int]]] = {}
        
        # 扫描交易文件
        trades_files = self._scan_trades_files()
        
        if not trades_files:
            logger.warning("未找到交易文件")
            return {}
        
        logger.info(f"扫描到 {len(trades_files)} 个交易文件")
        
        # 为每个市场建立索引（只处理少量样本避免太慢）
        sample_size = min(100, len(markets_df))
        sample_markets = markets_df.head(sample_size)
        
        for _, market in sample_markets.iterrows():
            market_id = market['condition_id']
            token_ids = self._get_token_ids_for_market(market_id)
            
            if not token_ids:
                continue
            
            # 检查哪些文件包含该市场的交易
            relevant_blocks = []
            
            for start_block, end_block, file_path in trades_files[:20]:  # 只检查前20个文件
                try:
                    # 快速检查：只读取前几行
                    df = pd.read_parquet(file_path, columns=['taker_asset_id'])
                    
                    # 检查是否有交集
                    file_tokens = set(df['taker_asset_id'].astype(str).unique())
                    
                    if any(str(tid) in file_tokens for tid in token_ids):
                        relevant_blocks.append((start_block, end_block))
                        
                except Exception as e:
                    continue
            
            if relevant_blocks:
                index[market_id] = relevant_blocks
        
        self._market_index = index
        
        # 保存索引
        if self.use_cache:
            with open(self.index_file, 'wb') as f:
                pickle.dump(index, f)
            logger.info(f"已缓存 {len(index)} 个市场的索引")
        
        return index
    
    def get_market_trades(
        self,
        market_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        获取市场交易数据
        
        Args:
            market_id: 市场 condition_id
            start_time: 开始时间（可选）
            end_time: 结束时间（可选）
            use_cache: 是否使用本地缓存
            
        Returns:
            交易数据 DataFrame
        """
        # 检查本地缓存
        cache_path = self._get_market_cache_path(market_id)
        
        if use_cache and self.use_cache and cache_path.exists():
            logger.info(f"从本地缓存加载 {market_id[:20]}... 的交易数据")
            df = pd.read_parquet(cache_path)
            
            # 应用时间过滤
            if start_time or end_time:
                df = self._filter_by_time(df, start_time, end_time)
            
            return df
        
        # 获取市场 token IDs
        token_ids = self._get_token_ids_for_market(market_id)
        
        if not token_ids:
            logger.warning(f"无法获取市场 {market_id[:20]}... 的 token IDs")
            return pd.DataFrame()
        
        logger.info(f"加载市场 {market_id[:20]}... 的交易数据")
        logger.info(f"Token IDs: {[tid[:20] + '...' for tid in token_ids]}")
        
        # 获取相关区块范围
        index = self._build_market_index()
        block_ranges = index.get(market_id, [])
        
        if not block_ranges:
            logger.info(f"未找到市场的索引，尝试扫描所有文件...")
            # 扫描所有文件
            block_ranges = self._scan_trades_files()
            block_ranges = [(s, e) for s, e, _ in block_ranges]
        
        # 读取并合并交易数据
        all_trades = []
        
        for start_block, end_block in block_ranges:
            file_path = self.data_path / "polymarket" / "trades" / f"trades_{start_block}_{end_block}.parquet"
            
            if not file_path.exists():
                continue
            
            try:
                logger.debug(f"读取 {file_path.name}...")
                df = pd.read_parquet(file_path)
                
                # 过滤该市场的交易
                mask = (
                    df['taker_asset_id'].astype(str).isin(token_ids) |
                    df['maker_asset_id'].astype(str).isin(token_ids)
                )
                market_trades = df[mask].copy()
                
                if len(market_trades) > 0:
                    # 添加市场 ID 列
                    market_trades['market_id'] = market_id
                    all_trades.append(market_trades)
                    
            except Exception as e:
                logger.error(f"读取文件失败 {file_path}: {e}")
                continue
        
        if not all_trades:
            logger.warning(f"未找到市场 {market_id[:20]}... 的交易数据")
            return pd.DataFrame()
        
        # 合并数据
        result = pd.concat(all_trades, ignore_index=True)
        
        # 排序
        if 'block_number' in result.columns:
            result = result.sort_values('block_number')
        
        logger.info(f"加载完成: {len(result)} 条交易记录")
        
        # 保存到缓存
        if self.use_cache and use_cache:
            result.to_parquet(cache_path)
            logger.info(f"已缓存到 {cache_path}")
        
        # 应用时间过滤
        if start_time or end_time:
            result = self._filter_by_time(result, start_time, end_time)
        
        return result
    
    def _filter_by_time(
        self,
        df: pd.DataFrame,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> pd.DataFrame:
        """按时间过滤数据"""
        if df.empty:
            return df
        
        # 尝试解析时间戳
        time_col = None
        for col in ['timestamp', '_fetched_at', 'block_number']:
            if col in df.columns:
                time_col = col
                break
        
        if not time_col:
            return df
        
        if time_col == 'timestamp' or time_col == '_fetched_at':
            df[time_col] = pd.to_datetime(df[time_col])
        
        if start_time:
            df = df[df[time_col] >= start_time]
        
        if end_time:
            df = df[df[time_col] <= end_time]
        
        return df
    
    def clear_cache(self):
        """清除所有本地缓存"""
        logger.info("清除本地缓存...")
        
        # 清除交易缓存
        if self.trades_cache_dir.exists():
            for f in self.trades_cache_dir.glob("*.parquet"):
                f.unlink()
        
        # 清除索引
        if self.index_file.exists():
            self.index_file.unlink()
        
        # 清除 markets 缓存
        if self.markets_cache.exists():
            self.markets_cache.unlink()
        
        # 重置内存缓存
        self._markets_df = None
        self._market_index = None
        self._loaded_trades_files.clear()
        
        logger.info("缓存已清除")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计信息"""
        stats = {
            'cache_dir': str(self.cache_dir),
            'markets_cached': self.markets_cache.exists(),
            'index_exists': self.index_file.exists(),
            'trades_cached': 0,
            'total_cache_size_mb': 0
        }
        
        # 统计交易缓存
        if self.trades_cache_dir.exists():
            trades_files = list(self.trades_cache_dir.glob("*.parquet"))
            stats['trades_cached'] = len(trades_files)
            
            total_size = sum(f.stat().st_size for f in trades_files)
            stats['total_cache_size_mb'] = round(total_size / (1024 * 1024), 2)
        
        # 计算 markets 缓存大小
        if self.markets_cache.exists():
            stats['markets_cache_size_mb'] = round(
                self.markets_cache.stat().st_size / (1024 * 1024), 2
            )
        
        return stats


def convert_raw_trades_to_market_format(df: pd.DataFrame) -> pd.DataFrame:
    """
    将原始交易数据转换为策略可用的市场格式
    
    原始格式 (from blockchain):
    - block_number, transaction_hash, maker_asset_id, taker_asset_id, maker_amount, taker_amount
    
    目标格式:
    - timestamp, market, price, size, side
    """
    if df.empty:
        return pd.DataFrame(columns=['timestamp', 'market', 'price', 'size', 'side'])
    
    result = pd.DataFrame()
    
    # 使用 block_number 作为时间索引（或尝试解析 timestamp）
    if 'timestamp' in df.columns and df['timestamp'].notna().any():
        result['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        # 使用 block_number 作为伪时间戳
        result['timestamp'] = pd.to_datetime(df['block_number'], unit='s')
    
    # 计算价格 (taker_amount / maker_amount，假设是二元市场)
    # 注意：这是简化计算，实际应根据 token 类型确定
    result['price'] = df['taker_amount'] / (df['maker_amount'] + df['taker_amount'])
    result['price'] = result['price'].clip(0.01, 0.99)
    
    # 交易数量
    result['size'] = df['maker_amount'] + df['taker_amount']
    
    # 买卖方向（简化判断）
    # 如果 maker_asset_id 为 0，通常是买入
    result['side'] = df['maker_asset_id'].apply(lambda x: 'BUY' if x == 0 else 'SELL')
    
    # 市场 ID
    result['market'] = df.get('market_id', 'unknown')
    
    return result


# 便捷函数
def create_default_loader(cache_dir: Optional[str] = None) -> MarketDataLoader:
    """创建默认的数据加载器"""
    return MarketDataLoader(cache_dir=cache_dir or "~/.cache/polymarket")
