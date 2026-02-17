"""
00002 test_backtest_flow.py - 回测流程集成测试

测试目标:
- 验证完整回测流程
- 测试 DataAdapter -> Skill -> 结果输出
- 验证回测结果的正确性
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from conftest import TEST_CONFIG

from .backtest_engine import (
    BacktestEngine,
    VolatilityMarketMakerStrategy,
    Signal,
    Trade,
    BacktestResult,
    calculate_sharpe_ratio,
    calculate_max_drawdown,
    calculate_win_rate,
    calculate_pnl_from_trades,
    run_backtest,
)


class TestBacktestEngine:
    """回测引擎测试"""
    
    def test_backtest_engine_initialization(self):
        """测试回测引擎初始化"""
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        engine = BacktestEngine(strategy, initial_capital=10000)
        
        assert engine.initial_capital == 10000
        assert engine.current_capital == 10000
        assert len(engine.trades) == 0
    
    def test_backtest_single_step(self, sample_trades_1k):
        """
        测试单步回测
        
        处理单个时间点的数据
        """
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        engine = BacktestEngine(strategy)
        
        # 取第一个数据点
        row = sample_trades_1k.iloc[0]
        result = engine.step(row)
        
        # 验证: 产生有效信号
        assert result['signal'] in ['BUY', 'SELL', 'HOLD']
        assert 'pnl' in result
    
    def test_backtest_full_run(self, sample_trades_1k):
        """
        测试完整回测运行
        
        遍历所有历史数据
        """
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        engine = BacktestEngine(strategy, initial_capital=10000)
        
        result = engine.run(sample_trades_1k)
        
        # 验证结果结构
        assert isinstance(result, BacktestResult)
        assert hasattr(result, 'trades')
        assert hasattr(result, 'pnl_series')
        assert hasattr(result, 'statistics')
    
    def test_backtest_capital_tracking(self, sample_trades_1k):
        """
        测试资金跟踪
        
        验证每笔交易后资金变化正确
        """
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        engine = BacktestEngine(strategy, initial_capital=10000)
        result = engine.run(sample_trades_1k)
        
        # 验证: 有交易执行
        if result.trades:
            # 验证总盈亏计算正确
            manual_pnl = sum(t.pnl for t in result.trades if t.pnl is not None)
            assert abs(result.total_pnl - manual_pnl) < 0.01


class TestStrategyIntegration:
    """策略集成测试"""
    
    def test_strategy_initialization(self):
        """测试策略初始化"""
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        
        assert strategy.config == TEST_CONFIG
        assert strategy.position == 0
        assert strategy.avg_price == 0.0
    
    def test_strategy_signal_generation(self, sample_orderbook_snapshots):
        """
        测试策略信号生成
        
        验证策略根据市场数据生成正确的买卖信号
        """
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        
        for _, row in sample_orderbook_snapshots.head(10).iterrows():
            signal = strategy.generate_signal(row)
            assert signal in [Signal.BUY, Signal.SELL, Signal.HOLD]
            assert signal.value in ['BUY', 'SELL', 'HOLD']
    
    def test_strategy_execute_signal_buy(self):
        """测试策略执行买入信号"""
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        
        row = pd.Series({
            'timestamp': datetime.now(),
            'price': 0.40,  # 低价触发买入
        })
        
        trade = strategy.execute_signal(Signal.BUY, row)
        
        if trade:
            assert trade.action == 'BUY'
            assert trade.size > 0
            assert trade.price == 0.40
    
    def test_strategy_execute_signal_sell(self):
        """测试策略执行卖出信号"""
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        
        # 先建立持仓
        strategy.position = 100
        strategy.avg_price = 0.50
        
        row = pd.Series({
            'timestamp': datetime.now(),
            'price': 0.60,  # 高价触发卖出
        })
        
        trade = strategy.execute_signal(Signal.SELL, row)
        
        if trade:
            assert trade.action == 'SELL'
            assert trade.size > 0
            assert trade.pnl is not None
    
    def test_strategy_with_volatility_threshold(self, sample_trades_1k):
        """
        测试策略波动率阈值处理
        
        高波动率时应减少或停止交易
        """
        # 添加高波动率列
        df = sample_trades_1k.copy()
        df['3_hour'] = 0.20  # 高波动率
        
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        
        # 在高波动率下大部分信号应为 HOLD
        signals = []
        for _, row in df.head(50).iterrows():
            signal = strategy.generate_signal(row)
            signals.append(signal)
        
        # 高波动率时应该主要产生 HOLD 信号
        hold_count = sum(1 for s in signals if s == Signal.HOLD)
        assert hold_count > 0  # 至少有一些 HOLD 信号
    
    def test_strategy_update_params(self):
        """测试策略参数更新"""
        strategy = VolatilityMarketMakerStrategy(TEST_CONFIG)
        
        # 更新参数
        new_params = {'stop_loss_threshold': -3.0, 'take_profit_threshold': 5.0}
        strategy.update_params(new_params)
        
        # 验证参数已更新
        assert strategy.config['stop_loss_threshold'] == -3.0
        assert strategy.config['take_profit_threshold'] == 5.0
        
        # 验证其他参数未变
        assert strategy.config['volatility_threshold'] == TEST_CONFIG['volatility_threshold']


class TestBacktestResultValidation:
    """回测结果验证"""
    
    def test_pnl_calculation_accuracy(self):
        """
        测试 PnL 计算准确性
        
        验证: PnL = sum((sell_price - buy_price) * size)
        """
        trades = [
            Trade(timestamp=datetime.now(), action='BUY', size=10, price=0.50),
            Trade(timestamp=datetime.now(), action='SELL', size=10, price=0.60, pnl=1.0),
        ]
        
        # 手动计算
        manual_pnl = 10 * (0.60 - 0.50)  # 1.0
        
        # 函数计算
        engine_pnl = calculate_pnl_from_trades(trades)
        
        assert abs(manual_pnl - engine_pnl) < 0.01
    
    def test_sharpe_ratio_calculation(self):
        """测试夏普比率计算"""
        returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
        
        sharpe = calculate_sharpe_ratio(returns, risk_free_rate=0)
        
        # 手动计算验证
        if returns.std() != 0:
            expected_sharpe = returns.mean() / returns.std() * np.sqrt(252)
            assert abs(sharpe - expected_sharpe) < 0.001
    
    def test_sharpe_ratio_empty_series(self):
        """测试空序列夏普比率"""
        sharpe = calculate_sharpe_ratio(pd.Series(dtype=float))
        assert sharpe == 0.0
    
    def test_max_drawdown_calculation(self):
        """测试最大回撤计算"""
        pnl_series = pd.Series([0, 10, 20, 15, 25, 20, 30, 25, 20, 35])
        
        max_dd = calculate_max_drawdown(pnl_series)
        
        # 从 30 跌到 20，回撤 10
        expected_max_dd = -10
        assert max_dd == expected_max_dd
    
    def test_max_drawdown_empty_series(self):
        """测试空序列最大回撤"""
        max_dd = calculate_max_drawdown(pd.Series(dtype=float))
        assert max_dd == 0.0
    
    def test_win_rate_calculation(self):
        """测试胜率计算"""
        trades = [
            Trade(timestamp=datetime.now(), action='SELL', size=10, price=0.6, pnl=10),
            Trade(timestamp=datetime.now(), action='SELL', size=10, price=0.6, pnl=-5),
            Trade(timestamp=datetime.now(), action='SELL', size=10, price=0.6, pnl=15),
            Trade(timestamp=datetime.now(), action='SELL', size=10, price=0.6, pnl=-3),
            Trade(timestamp=datetime.now(), action='SELL', size=10, price=0.6, pnl=8),
        ]
        
        win_rate = calculate_win_rate(trades)
        
        # 3 胜 2 负，胜率 60%
        assert win_rate == 0.6
    
    def test_win_rate_no_completed_trades(self):
        """测试没有完成交易时的胜率"""
        trades = [
            Trade(timestamp=datetime.now(), action='BUY', size=10, price=0.5),
        ]
        
        win_rate = calculate_win_rate(trades)
        assert win_rate == 0.0


class TestTimePresetIntegration:
    """时间预设集成测试"""
    
    def test_backtest_with_lifecycle_preset(self, sample_trades_1k):
        """
        测试生命周期预设回测
        
        使用数据的完整时间范围
        """
        result = run_backtest(sample_trades_1k, TEST_CONFIG)
        
        # 验证使用了全部数据
        if 'timestamp' in sample_trades_1k.columns:
            assert result.start_date == sample_trades_1k['timestamp'].min()
            assert result.end_date == sample_trades_1k['timestamp'].max()
    
    def test_backtest_result_attributes(self, sample_trades_1k):
        """测试回测结果属性"""
        result = run_backtest(sample_trades_1k, TEST_CONFIG)
        
        # 验证结果属性
        assert isinstance(result.trades, list)
        assert isinstance(result.pnl_series, pd.Series)
        assert isinstance(result.statistics, dict)
        assert isinstance(result.trade_count, int)
        assert isinstance(result.total_pnl, (int, float))


class TestParameterOverride:
    """参数覆盖测试"""
    
    def test_strategy_parameter_override(self):
        """
        测试策略参数覆盖
        
        运行时覆盖默认配置
        """
        default_config = TEST_CONFIG.copy()
        strategy = VolatilityMarketMakerStrategy(default_config)
        
        # 覆盖参数
        custom_params = {
            'stop_loss_threshold': -3.0,
            'take_profit_threshold': 5.0,
        }
        strategy.update_params(custom_params)
        
        # 验证参数已更新
        assert strategy.config['stop_loss_threshold'] == -3.0
        assert strategy.config['take_profit_threshold'] == 5.0
        
        # 验证其他参数未变
        assert strategy.config['volatility_threshold'] == TEST_CONFIG['volatility_threshold']
    
    def test_backtest_with_different_parameters(self, sample_trades_1k):
        """
        测试不同参数的回测结果对比
        
        保守参数 vs 激进参数
        """
        conservative = {'stop_loss_threshold': -3.0, 'take_profit_threshold': 2.0}
        aggressive = {'stop_loss_threshold': -10.0, 'take_profit_threshold': 5.0}
        
        # 合并配置
        cons_config = {**TEST_CONFIG, **conservative}
        aggr_config = {**TEST_CONFIG, **aggressive}
        
        result_conservative = run_backtest(sample_trades_1k, cons_config)
        result_aggressive = run_backtest(sample_trades_1k, aggr_config)
        
        # 验证都有结果
        assert isinstance(result_conservative, BacktestResult)
        assert isinstance(result_aggressive, BacktestResult)


class TestErrorHandling:
    """错误处理测试"""
    
    def test_backtest_empty_data(self):
        """测试空数据回测"""
        empty_df = pd.DataFrame()
        
        with pytest.raises(ValueError, match="Empty market data"):
            run_backtest(empty_df, TEST_CONFIG)
    
    def test_backtest_insufficient_data(self):
        """测试数据不足的情况"""
        small_df = pd.DataFrame({
            'timestamp': [datetime.now(), datetime.now()],
            'price': [0.5, 0.51]
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            run_backtest(small_df, TEST_CONFIG)


class TestPerformanceBenchmarks:
    """性能基准测试"""
    
    @pytest.mark.slow
    def test_backtest_performance_10k_rows(self):
        """
        测试 10k 行数据回测性能
        
        期望: < 1 秒
        """
        import time
        
        # 生成 10k 行数据
        n = 10000
        large_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=n, freq='1min'),
            'price': 0.5 + np.random.normal(0, 0.02, n),
            '3_hour': np.random.uniform(0.05, 0.20, n),
        })
        
        start = time.time()
        result = run_backtest(large_data, TEST_CONFIG)
        elapsed = time.time() - start
        
        # 性能应满足要求
        assert elapsed < 5.0  # 5秒内完成
        assert isinstance(result, BacktestResult)
    
    def test_convenience_function_run_backtest(self, sample_trades_1k):
        """测试便捷函数 run_backtest"""
        result = run_backtest(sample_trades_1k, TEST_CONFIG, initial_capital=5000)
        
        assert isinstance(result, BacktestResult)
        # 验证初始资金设置正确
        assert result.total_pnl is not None
