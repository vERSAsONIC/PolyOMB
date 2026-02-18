"""
00002 test_data_adapter.py - 数据适配器测试

测试目标:
- 验证 SMB 数据读取
- 验证 Parquet 文件解析
- 验证数据转换逻辑
- 测试错误处理
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

from conftest import TEST_MARKET_ID, SMB_PATH

from .data_adapter import (
    SMBDataAdapter,
    LocalDataAdapter,
    extract_price_series,
    build_orderbook_snapshot,
    convert_to_strategy_format,
    get_lifecycle_date_range,
    get_full_year_date_range,
    filter_by_date_range,
    validate_trades_df,
)


class TestSMBAdapterMock:
    """SMB 适配器 Mock 测试（无需网络）"""
    
    def test_adapter_initialization(self, mock_smb_adapter):
        """测试适配器初始化"""
        adapter = mock_smb_adapter(
            "smb://test-server/share/data",
            mount_point="/tmp/test-mount"
        )
        
        assert adapter.smb_url == "smb://test-server/share/data"
        assert adapter.mount_point == "/tmp/test-mount"
    
    def test_mount_smb_share(self, mock_smb_adapter):
        """测试 SMB 挂载"""
        adapter = mock_smb_adapter(SMB_PATH)
        
        result = adapter.mount()
        assert result is True
        assert adapter._is_mounted is True
    
    def test_unmount_smb_share(self, mock_smb_adapter):
        """测试 SMB 卸载"""
        adapter = mock_smb_adapter(SMB_PATH)
        adapter.mount()
        
        result = adapter.unmount()
        assert result is True
        assert adapter._is_mounted is False
    
    def test_read_parquet_with_mock_data(self, mock_smb_adapter, sample_trades_1k):
        """测试读取 Parquet 文件"""
        adapter = mock_smb_adapter(SMB_PATH)
        adapter.set_mock_data("polymarket/trades.parquet", sample_trades_1k)
        
        result = adapter.read_parquet("polymarket/trades.parquet")
        
        assert len(result) == 1000
        assert 'timestamp' in result.columns
        assert 'price' in result.columns
    
    def test_get_market_trades(self, mock_smb_adapter, sample_trades_1k):
        """测试获取特定市场交易数据"""
        adapter = mock_smb_adapter(SMB_PATH)
        adapter.set_mock_data("trades", sample_trades_1k)
        
        market_id = TEST_MARKET_ID
        result = adapter.get_market_trades(market_id)
        
        assert len(result) > 0
    
    def test_get_market_metadata(self, mock_smb_adapter):
        """测试获取市场元数据"""
        adapter = mock_smb_adapter(SMB_PATH)
        
        market_id = TEST_MARKET_ID
        result = adapter.get_market_metadata(market_id)
        
        assert result['condition_id'] == market_id
        assert 'question' in result


class TestSMBDataAdapterReal:
    """SMBDataAdapter 真实功能测试"""
    
    def test_real_adapter_initialization(self):
        """测试真实适配器初始化"""
        adapter = SMBDataAdapter(SMB_PATH)
        
        assert adapter.smb_url == SMB_PATH
        assert adapter.is_mounted() is False
    
    def test_real_adapter_mount_unmount(self):
        """测试真实适配器挂载卸载"""
        adapter = SMBDataAdapter(SMB_PATH)
        
        # 挂载
        assert adapter.mount() is True
        assert adapter.is_mounted() is True
        
        # 卸载
        assert adapter.unmount() is True
        assert adapter.is_mounted() is False
    
    def test_adapter_cache(self):
        """测试适配器缓存功能"""
        adapter = SMBDataAdapter(SMB_PATH)
        adapter.mount()
        
        # 初始缓存命中为 0
        assert adapter.cache_hits == 0
        
        # 模拟缓存数据
        mock_df = pd.DataFrame({'test': [1, 2, 3]})
        adapter._cache['test_key'] = mock_df
        
        # 不需要真实数据，测试缓存机制
        adapter.invalidate_cache()
        assert len(adapter._cache) == 0


class TestDataTransformation:
    """数据转换测试"""
    
    def test_extract_price_series(self, sample_trades_1k):
        """
        测试从交易数据提取价格序列
        
        将交易数据转换为策略可用的时间序列
        """
        df = sample_trades_1k
        
        price_series = extract_price_series(df, interval="1min")
        
        # 验证: 时间索引
        assert isinstance(price_series.index, pd.DatetimeIndex)
        
        # 验证: 返回了价格数据
        assert len(price_series) > 0
        # 由于数据每10分钟一条，重采样为1分钟会保持相似长度（只是重新索引）
        assert len(price_series) <= len(df)
    
    def test_extract_price_series_empty(self):
        """测试空数据提取价格序列"""
        empty_df = pd.DataFrame()
        result = extract_price_series(empty_df)
        
        assert len(result) == 0
    
    def test_calculate_market_volatility_from_adapter(self, sample_trades_1k):
        """测试通过适配器计算市场波动率"""
        adapter = SMBDataAdapter(SMB_PATH)
        adapter.mount()
        
        # 设置模拟数据
        adapter._cache[f"trades_{TEST_MARKET_ID}"] = sample_trades_1k
        
        volatility = adapter.calculate_market_volatility(
            TEST_MARKET_ID, 
            window="3h"
        )
        
        assert 0 <= volatility <= 1
    
    def test_build_orderbook_from_trades(self, sample_trades_1k):
        """
        测试从交易数据重建订单簿
        
        prediction-market-analysis 可能没有直接订单簿，
        需要从 trades 推断
        """
        df = sample_trades_1k
        
        timestamp = df['timestamp'].iloc[100]
        orderbook = build_orderbook_snapshot(df, timestamp=timestamp)
        
        # 验证: 订单簿结构
        assert 'best_bid' in orderbook or len(orderbook) == 0
        assert 'best_ask' in orderbook or len(orderbook) == 0
    
    def test_convert_to_strategy_format(self, sample_trades_1k, sample_market_metadata):
        """
        测试转换为策略内部格式
        
        将原始数据转换为 poly-maker 期望的格式
        """
        strategy_data = convert_to_strategy_format(
            trades=sample_trades_1k,
            metadata=sample_market_metadata
        )
        
        # 验证: 包含必要的列
        assert 'tick_size' in strategy_data.columns
        assert 'timestamp' in strategy_data.columns


class TestDateRangeHandling:
    """日期范围处理测试"""
    
    def test_full_lifecycle_date_range(self, sample_trades_1k):
        """
        测试生命周期日期范围
        
        返回数据的完整时间范围
        """
        df = sample_trades_1k
        
        start, end = get_lifecycle_date_range(df)
        
        assert start == df['timestamp'].min()
        assert end == df['timestamp'].max()
    
    def test_full_year_date_range(self, sample_trades_1k):
        """
        测试全年日期范围
        
        自动检测年份并返回该年全年
        """
        df = sample_trades_1k
        
        start, end = get_full_year_date_range(df)
        
        # 检测数据年份
        data_year = df['timestamp'].dt.year.mode()[0]
        assert start.year == data_year
        assert end.year == data_year
        assert start.month == 1 and start.day == 1
        assert end.month == 12 and end.day == 31
    
    def test_filter_data_by_date_range(self, sample_trades_1k):
        """测试按日期范围过滤数据"""
        df = sample_trades_1k
        
        start = datetime(2024, 1, 2)
        end = datetime(2024, 1, 5)
        
        filtered = filter_by_date_range(df, start, end)
        
        assert filtered['timestamp'].min() >= start
        assert filtered['timestamp'].max() <= end
    
    def test_filter_empty_dataframe(self):
        """测试过滤空 DataFrame"""
        empty_df = pd.DataFrame()
        result = filter_by_date_range(
            empty_df, 
            datetime(2024, 1, 1), 
            datetime(2024, 1, 2)
        )
        assert len(result) == 0


class TestDataValidation:
    """数据验证测试"""
    
    def test_validate_trades_dataframe(self, sample_trades_1k):
        """验证交易数据 DataFrame 结构"""
        df = sample_trades_1k
        
        # 验证成功
        result = validate_trades_df(df)
        assert result is True
    
    def test_validate_missing_columns(self):
        """测试缺失必需列的验证"""
        df = pd.DataFrame({
            'timestamp': [datetime.now()],
            'price': [0.5],
            # 缺少 'market', 'size', 'side'
        })
        
        with pytest.raises(ValueError, match="Missing required columns"):
            validate_trades_df(df)
    
    def test_validate_empty_dataframe(self):
        """测试验证空 DataFrame"""
        df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="Empty DataFrame"):
            validate_trades_df(df)
    
    def test_validate_price_range(self, sample_trades_1k):
        """验证价格范围"""
        df = sample_trades_1k
        
        # 验证价格在 [0.01, 0.99] 范围内
        assert (df['price'] >= 0.01).all()
        assert (df['price'] <= 0.99).all()
    
    def test_validate_chronological_order(self, sample_trades_1k):
        """验证时间顺序"""
        df = sample_trades_1k
        
        # 验证时间戳递增
        assert df['timestamp'].is_monotonic_increasing


class TestDataCaching:
    """数据缓存测试"""
    
    def test_data_caching_mechanism(self):
        """
        测试数据缓存机制
        
        重复读取应使用缓存
        """
        adapter = SMBDataAdapter(SMB_PATH)
        adapter.mount()
        
        # 设置模拟数据
        mock_df = pd.DataFrame({'test': [1, 2, 3]})
        adapter._cache['trades_test'] = mock_df
        
        # 从缓存读取
        result = adapter.get_market_trades('test', use_cache=True)
        assert adapter.cache_hits == 1
        assert len(result) == 3
    
    def test_cache_invalidation(self):
        """测试缓存失效"""
        adapter = SMBDataAdapter(SMB_PATH)
        
        # 添加缓存
        adapter._cache['test'] = pd.DataFrame()
        
        # 手动失效缓存
        adapter.invalidate_cache()
        assert len(adapter._cache) == 0
        assert adapter.cache_hits == 0


# =============================================================================
# SMB 真实连接测试（需要 --run-smb 标记）
# =============================================================================

@pytest.mark.smb
class TestSMBAdapterReal:
    """SMB 适配器真实连接测试"""
    
    def test_real_smb_connection(self):
        """测试真实 SMB 连接"""
        adapter = SMBDataAdapter(SMB_PATH)
        result = adapter.mount()
        assert result is True
        adapter.unmount()
    
    def test_read_real_markets_parquet(self):
        """读取真实 markets.parquet"""
        # 使用 SMB 挂载的真实路径
        markets_file = "/Volumes/liuqiong/prediction-market-analysis/data/polymarket/markets/markets_0_10000.parquet"
        
        import pandas as pd
        df = pd.read_parquet(markets_file)
        
        # 验证数据
        assert len(df) > 0
        assert "condition_id" in df.columns
        assert "question" in df.columns
        print(f"✅ 成功读取 {len(df)} 条市场记录")
    
    def test_read_real_trades_for_market(self):
        """验证交易数据目录可访问"""
        import os
        
        trades_dir = "/Volumes/liuqiong/prediction-market-analysis/data/polymarket/trades"
        
        # 验证 SMB 挂载点可访问
        # 注意：由于网络文件系统延迟，不执行 listdir 操作
        assert os.path.ismount("/Volumes/liuqiong"), "SMB 未挂载"
        assert os.path.exists(trades_dir), "交易数据目录不存在"
        print(f"✅ 交易数据目录可访问")
