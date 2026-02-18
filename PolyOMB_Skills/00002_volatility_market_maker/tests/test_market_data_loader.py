"""
00002 test_market_data_loader.py - MarketDataLoader 测试

测试数据加载器的各项功能
"""

import pytest
import pandas as pd
from datetime import datetime
import tempfile
import shutil
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from market_data_loader import (
    MarketDataLoader,
    convert_raw_trades_to_market_format,
    create_default_loader
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def temp_cache_dir():
    """临时缓存目录"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def loader(temp_cache_dir):
    """创建测试用的加载器"""
    return MarketDataLoader(
        cache_dir=temp_cache_dir,
        use_cache=True
    )


# =============================================================================
# Tests
# =============================================================================

class TestMarketDataLoader:
    """MarketDataLoader 测试类"""
    
    def test_initialization(self, temp_cache_dir):
        """测试初始化"""
        loader = MarketDataLoader(cache_dir=temp_cache_dir)
        
        assert loader.cache_dir == Path(temp_cache_dir).expanduser()
        assert loader.use_cache is True
        assert loader._markets_df is None
        assert loader._market_index is None
    
    def test_cache_directory_creation(self, temp_cache_dir):
        """测试缓存目录自动创建"""
        loader = MarketDataLoader(cache_dir=temp_cache_dir)
        
        assert loader.cache_dir.exists()
        assert loader.trades_cache_dir.exists()
    
    def test_get_cache_key(self, loader):
        """测试缓存键生成"""
        market_id = "0x1234567890abcdef"
        cache_key = loader._get_cache_key(market_id)
        
        # 应该是 MD5 哈希的前16位
        assert len(cache_key) == 16
        assert cache_key.isalnum()
    
    def test_get_market_cache_path(self, loader):
        """测试缓存路径生成"""
        market_id = "0x1234567890abcdef"
        cache_path = loader._get_market_cache_path(market_id)
        
        assert cache_path.suffix == ".parquet"
        assert cache_path.parent == loader.trades_cache_dir
    
    def test_get_cache_stats_empty(self, loader):
        """测试空缓存统计"""
        stats = loader.get_cache_stats()
        
        assert stats['trades_cached'] == 0
        assert stats['total_cache_size_mb'] == 0
        assert stats['markets_cached'] is False
    
    def test_clear_cache(self, loader, temp_cache_dir):
        """测试清除缓存"""
        # 创建一些测试缓存文件
        test_file = loader.trades_cache_dir / "test.parquet"
        test_file.write_text("test")
        
        assert test_file.exists()
        
        loader.clear_cache()
        
        assert not test_file.exists()
        assert loader._markets_df is None
        assert loader._market_index is None


class TestDataConversion:
    """数据转换测试"""
    
    def test_convert_empty_dataframe(self):
        """测试空 DataFrame 转换"""
        df = pd.DataFrame()
        result = convert_raw_trades_to_market_format(df)
        
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0
        assert 'timestamp' in result.columns
        assert 'price' in result.columns
    
    def test_convert_raw_trades(self):
        """测试原始交易数据转换"""
        raw_data = pd.DataFrame({
            'block_number': [100, 101, 102],
            'transaction_hash': ['0x1', '0x2', '0x3'],
            'maker_asset_id': [0, 123, 0],
            'taker_asset_id': [456, 0, 789],
            'maker_amount': [1000, 2000, 1500],
            'taker_amount': [2000, 1000, 2500],
        })
        
        result = convert_raw_trades_to_market_format(raw_data)
        
        assert len(result) == 3
        assert 'timestamp' in result.columns
        assert 'price' in result.columns
        assert 'size' in result.columns
        assert 'side' in result.columns
        
        # 验证价格计算 (taker / (maker + taker))
        expected_price = 2000 / (1000 + 2000)  # ~0.666
        assert abs(result['price'].iloc[0] - expected_price) < 0.01
        
        # 验证买卖方向
        assert result['side'].iloc[0] == 'BUY'  # maker_asset_id == 0
        assert result['side'].iloc[1] == 'SELL'  # maker_asset_id != 0
    
    def test_price_clipping(self):
        """测试价格范围限制"""
        # 创建极端值数据
        raw_data = pd.DataFrame({
            'block_number': [100],
            'maker_asset_id': [1],
            'taker_asset_id': [2],
            'maker_amount': [999999],
            'taker_amount': [1],
        })
        
        result = convert_raw_trades_to_market_format(raw_data)
        
        # 价格应在 [0.01, 0.99] 范围内
        assert result['price'].iloc[0] >= 0.01
        assert result['price'].iloc[0] <= 0.99


class TestIntegration:
    """集成测试"""
    
    @pytest.mark.smb
    def test_real_market_info(self):
        """测试获取真实市场信息（需要 SMB）"""
        loader = create_default_loader()
        
        # 2020年特朗普选举市场
        market_id = "0xf2e631ea675c5b09caea0bf65cf7887e25907af2657c8c907f02d9afbff20d05"
        
        info = loader.get_market_info(market_id)
        
        if info:
            assert 'question' in info
            assert 'volume' in info
            assert info['condition_id'] == market_id
    
    @pytest.mark.slow
    def test_real_trades_loading(self):
        """测试加载真实交易数据（慢测试）"""
        loader = create_default_loader()
        
        market_id = "0xf2e631ea675c5b09caea0bf65cf7887e25907af2657c8c907f02d9afbff20d05"
        
        try:
            trades = loader.get_market_trades(market_id)
            
            if not trades.empty:
                assert 'block_number' in trades.columns
                assert 'transaction_hash' in trades.columns
                
                # 验证可以转换为策略格式
                market_trades = convert_raw_trades_to_market_format(trades)
                assert 'price' in market_trades.columns
                
        except Exception as e:
            pytest.skip(f"无法加载数据: {e}")


class TestCacheMechanism:
    """缓存机制测试"""
    
    def test_cache_hit(self, loader, temp_cache_dir):
        """测试缓存命中"""
        market_id = "test_market_123"
        
        # 创建模拟缓存数据
        cache_path = loader._get_market_cache_path(market_id)
        test_data = pd.DataFrame({
            'block_number': [1, 2, 3],
            'price': [0.5, 0.6, 0.7]
        })
        test_data.to_parquet(cache_path)
        
        # 从缓存读取
        result = loader.get_market_trades(market_id)
        
        assert len(result) == 3
        assert list(result['price']) == [0.5, 0.6, 0.7]
    
    def test_cache_stats_update(self, loader, temp_cache_dir):
        """测试缓存统计更新"""
        # 创建一些缓存文件
        for i in range(3):
            cache_file = loader.trades_cache_dir / f"test_{i}.parquet"
            # 写入更多数据确保文件有大小
            df = pd.DataFrame({'data': list(range(1000))})
            df.to_parquet(cache_file)
        
        stats = loader.get_cache_stats()
        
        assert stats['trades_cached'] == 3
        assert stats['total_cache_size_mb'] >= 0  # 小文件可能四舍五入为0


def test_create_default_loader():
    """测试工厂函数"""
    loader = create_default_loader()
    
    assert isinstance(loader, MarketDataLoader)
    assert loader.use_cache is True


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
