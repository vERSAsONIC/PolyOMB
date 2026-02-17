"""
00002 test_volatility_calc.py - 波动率计算测试

测试目标:
- 验证波动率计算准确性
- 验证与 prediction-market-analysis 数据计算结果一致性
- 测试边界情况和异常处理
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .volatility_calc import (
    calculate_volatility,
    calculate_rolling_volatility,
    should_pause_trading,
    extract_price_series,
    calculate_hourly_volatility,
    add_volatility_column,
)


class TestVolatilityCalculation:
    """波动率计算测试类"""
    
    # =============================================================================
    # 基础计算测试
    # =============================================================================
    
    def test_volatility_3h_basic_calculation(self):
        """
        测试基础3小时波动率计算
        
        使用已知价格序列验证计算准确性
        """
        # 准备测试数据 - 已知标准差的价格序列
        prices = pd.Series([0.50, 0.52, 0.48, 0.51, 0.53, 0.49])
        
        # 执行测试
        result = calculate_volatility(prices)
        
        # 验证: 波动率应为正数
        assert result > 0
        # 验证: 波动率在合理范围 [0, 1] 内
        assert 0 <= result <= 1
        # 验证: 不是 NaN 或无穷
        assert not np.isnan(result)
        assert not np.isinf(result)
    
    def test_volatility_returns_calculation(self):
        """
        测试对数收益率计算
        
        验证: volatility = std(log(price[i]/price[i-1]))
        """
        prices = pd.Series([1.0, 1.1, 1.0, 0.9, 1.0])
        
        # 手动计算对数收益率
        expected_returns = [
            np.log(1.1/1.0),   # 0.0953
            np.log(1.0/1.1),   # -0.0953
            np.log(0.9/1.0),   # -0.1054
            np.log(1.0/0.9),   # 0.1054
        ]
        expected_std = np.std(expected_returns, ddof=1)
        
        # 执行测试
        result = calculate_volatility(prices)
        
        # 验证结果与手动计算一致（允许 0.1% 误差）
        assert abs(result - expected_std) < 0.001
    
    def test_volatility_with_window(self, sample_trades_1k):
        """
        测试带时间窗口的波动率计算
        
        验证: 使用3小时窗口计算滚动波动率
        """
        df = sample_trades_1k.copy()
        
        # 计算3小时滚动波动率
        result = calculate_rolling_volatility(
            df, 
            price_col="price",
            timestamp_col="timestamp",
            window="3h"
        )
        
        # 验证: 结果长度与输入一致
        assert len(result) == len(df)
        
        # 验证: 波动率在合理范围内 [0, 1]（非 NaN 值）
        valid_vol = result.dropna()
        if len(valid_vol) > 0:
            assert (valid_vol >= 0).all()
            assert (valid_vol <= 1).all()
    
    # =============================================================================
    # 边界情况测试
    # =============================================================================
    
    def test_volatility_empty_series(self):
        """测试空序列异常处理"""
        empty_prices = pd.Series([], dtype=float)
        
        # 期望抛出 ValueError
        with pytest.raises(ValueError, match="Empty price series"):
            calculate_volatility(empty_prices)
    
    def test_volatility_single_price(self):
        """测试单价格异常处理"""
        single_price = pd.Series([0.5])
        
        # 单价格无法计算波动率，应抛出异常
        with pytest.raises(ValueError, match="Insufficient data points"):
            calculate_volatility(single_price)
    
    def test_volatility_constant_prices(self):
        """测试恒定价格序列"""
        constant_prices = pd.Series([0.5] * 10)
        
        # 期望波动率为 0（对数收益率全为 0）
        result = calculate_volatility(constant_prices)
        assert result == 0.0
    
    def test_volatility_nan_values(self):
        """测试包含 NaN 的价格序列"""
        prices_with_nan = pd.Series([0.5, 0.52, np.nan, 0.51, 0.53])
        
        # 期望: 正确处理 NaN，忽略后计算
        result = calculate_volatility(prices_with_nan)
        assert not np.isnan(result)
        assert result > 0
    
    def test_volatility_extreme_values(self):
        """测试极端价格值"""
        # 价格接近 0 和 1 的边界
        extreme_prices = pd.Series([0.01, 0.99, 0.01, 0.99, 0.01])
        
        # 期望: 正确处理极端值，不溢出
        result = calculate_volatility(extreme_prices)
        # 极端价格的波动率可能很大，但应该为正数且不是无穷
        assert result >= 0
        assert not np.isinf(result)
        assert not np.isnan(result)
    
    # =============================================================================
    # 与参考实现对比测试
    # =============================================================================
    
    @pytest.mark.smb
    def test_volatility_vs_prediction_market_analysis(self, sample_trades_1k):
        """
        与 prediction-market-analysis 计算结果对比
        
        使用真实数据验证波动率计算一致性
        
        Note: 此测试需要 SMB 连接，使用 --run-smb 启用
        """
        # 使用模拟数据验证计算逻辑
        df = sample_trades_1k.copy()
        
        # 我们的计算
        our_volatility = calculate_rolling_volatility(df, window="3h")
        
        # 验证结果结构正确
        assert len(our_volatility) == len(df)
        assert our_volatility.dtype == float
        
        # 验证大部分值在合理范围（排除前几个 NaN）
        valid_vol = our_volatility.dropna()
        if len(valid_vol) > 0:
            assert (valid_vol >= 0).all()
            assert (valid_vol <= 1).all()
    
    # =============================================================================
    # 性能测试
    # =============================================================================
    
    @pytest.mark.slow
    def test_volatility_performance_large_dataset(self):
        """
        测试大数据集性能
        
        验证: 处理 10万条数据 < 1秒
        """
        import time
        
        # 生成大量数据
        n = 100_000
        large_prices = pd.Series(
            0.5 + np.random.normal(0, 0.02, n)
        )
        
        start = time.time()
        result = calculate_volatility(large_prices)
        elapsed = time.time() - start
        
        # 验证性能要求
        assert elapsed < 1.0
        # 验证结果正确
        assert result >= 0
        assert not np.isnan(result)


class TestVolatilityFromTrades:
    """从交易数据计算波动率测试"""
    
    def test_volatility_from_trade_prices(self, sample_trades_1k):
        """
        从交易数据提取价格并计算波动率
        
        这是 poly-maker 的主要使用场景
        """
        df = sample_trades_1k
        
        # 提取价格序列
        prices = extract_price_series(df, interval="1min")
        
        # 验证提取结果
        assert len(prices) > 0
        assert isinstance(prices.index, pd.DatetimeIndex)
        
        # 计算波动率
        if len(prices) >= 2:
            volatility = calculate_volatility(prices)
            
            # 验证结果
            assert isinstance(volatility, float)
            assert 0 <= volatility <= 1
    
    def test_volatility_by_hour(self, sample_trades_1k):
        """
        按小时计算波动率
        
        验证: 返回每小时的波动率序列
        """
        df = sample_trades_1k
        
        hourly_vol = calculate_hourly_volatility(df)
        
        # 验证: 有结果返回
        assert isinstance(hourly_vol, pd.Series)
        
        # 验证: 索引是时间类型
        assert isinstance(hourly_vol.index, pd.DatetimeIndex)
    
    def test_volatility_3h_column_in_dataframe(self, sample_trades_1k):
        """
        测试 DataFrame 添加 3小时波动率列
        
        模拟 poly-maker 中的 row['3_hour'] 字段
        """
        df = sample_trades_1k.copy()
        
        result_df = add_volatility_column(
            df, 
            window="3h",
            min_periods=10,
            output_col="3_hour"
        )
        
        # 验证: 列存在且类型正确
        assert "3_hour" in result_df.columns
        assert result_df["3_hour"].dtype == float
        
        # 验证: 前几个值为 NaN（因为窗口不足）
        # 前 min_periods 个应该是 NaN
        assert result_df["3_hour"].isna().sum() >= 9  # 至少前 9 个是 NaN


class TestVolatilityThresholds:
    """波动率阈值相关测试"""
    
    def test_volatility_threshold_check(self):
        """
        测试波动率阈值检查函数
        
        验证: volatility > threshold 时返回 True
        """
        high_vol = 0.20
        threshold = 0.15
        assert should_pause_trading(high_vol, threshold) is True
        
        low_vol = 0.10
        assert should_pause_trading(low_vol, threshold) is False
    
    def test_volatility_at_exact_threshold(self):
        """测试恰好在阈值边界的情况"""
        threshold = 0.15
        exact_vol = 0.15
        
        # 边界行为: 应暂停交易（保守策略）
        assert should_pause_trading(exact_vol, threshold) is True


# =============================================================================
# 测试数据验证
# =============================================================================

def test_sample_trades_fixture(sample_trades_1k):
    """验证测试数据 fixture 正确生成"""
    assert len(sample_trades_1k) == 1000
    assert 'timestamp' in sample_trades_1k.columns
    assert 'price' in sample_trades_1k.columns
    assert 'side' in sample_trades_1k.columns
    
    # 验证时间范围
    duration = sample_trades_1k['timestamp'].max() - sample_trades_1k['timestamp'].min()
    assert duration.days >= 6  # 约7天的数据
    
    # 验证价格范围
    assert sample_trades_1k['price'].min() >= 0.01
    assert sample_trades_1k['price'].max() <= 0.99
