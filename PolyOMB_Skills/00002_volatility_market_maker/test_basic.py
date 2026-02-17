#!/usr/bin/env python3
"""
基础功能验证测试
（不需要 pytest）
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys

def test_volatility_calc():
    """测试波动率计算"""
    from volatility_calc import calculate_volatility, should_pause_trading
    
    print("\n[1] 测试波动率计算...")
    
    # 测试基础计算
    prices = pd.Series([0.50, 0.52, 0.48, 0.51, 0.53, 0.49])
    vol = calculate_volatility(prices)
    assert vol > 0, "波动率应大于0"
    assert vol <= 1, "波动率应在[0,1]范围"
    print(f"  ✓ 波动率计算: {vol:.4f}")
    
    # 测试恒定价格
    constant = pd.Series([0.5] * 10)
    vol_const = calculate_volatility(constant)
    assert vol_const == 0, "恒定价格波动率应为0"
    print(f"  ✓ 恒定价格波动率: {vol_const}")
    
    # 测试波动率阈值
    assert should_pause_trading(0.20, 0.15) == True, "高波动率应暂停"
    assert should_pause_trading(0.10, 0.15) == False, "低波动率不应暂停"
    print(f"  ✓ 波动率阈值检查")
    
    return True

def test_order_pricing():
    """测试订单定价"""
    from order_pricing import get_order_prices, round_to_tick_size, is_valid_spread
    
    print("\n[2] 测试订单定价...")
    
    # 测试 tick size 舍入
    assert round_to_tick_size(0.654, 0.01) == 0.65
    assert round_to_tick_size(0.655, 0.01) == 0.66
    print(f"  ✓ tick size 舍入")
    
    # 测试定价
    order_book = {
        'best_bid': 0.65,
        'best_ask': 0.67,
        'best_bid_size': 100,
        'best_ask_size': 100,
    }
    bid, ask = get_order_prices(order_book, avg_price=0.66, row={'tick_size': 0.01})
    assert bid < ask, "买价应小于卖价"
    assert bid < order_book['best_bid'], "买价应低于最优买价"
    assert ask > order_book['best_ask'], "卖价应高于最优卖价"
    print(f"  ✓ 订单定价: bid={bid:.2f}, ask={ask:.2f}")
    
    # 测试价差验证
    assert is_valid_spread(0.64, 0.67, 0.01, 0.05) == True
    assert is_valid_spread(0.64, 0.70, 0.01, 0.05) == False
    print(f"  ✓ 价差验证")
    
    return True

def test_risk_management():
    """测试风险管理"""
    from risk_management import (
        should_trigger_stop_loss,
        calculate_take_profit_price,
        can_increase_position,
        RiskLevel
    )
    
    print("\n[3] 测试风险管理...")
    
    # 测试止损
    assert should_trigger_stop_loss(-6, 0.01, -5, 0.02) == True
    assert should_trigger_stop_loss(-3, 0.01, -5, 0.02) == False
    print(f"  ✓ 止损触发检查")
    
    # 测试止盈价格
    tp = calculate_take_profit_price(0.60, 3.0)
    assert abs(tp - 0.618) < 0.001, f"止盈价格计算错误: {tp}"
    print(f"  ✓ 止盈价格计算: {tp:.4f}")
    
    # 测试持仓限制
    assert can_increase_position(200, 250) == True
    assert can_increase_position(250, 250) == False
    print(f"  ✓ 持仓限制检查")
    
    return True

def test_data_adapter():
    """测试数据适配器"""
    from data_adapter import SMBDataAdapter, validate_trades_df
    
    print("\n[4] 测试数据适配器...")
    
    # 测试适配器初始化
    adapter = SMBDataAdapter("smb://test", "/tmp/test")
    assert adapter.mount() == True
    assert adapter._is_mounted == True
    print(f"  ✓ SMB 适配器初始化")
    
    # 测试数据验证
    valid_df = pd.DataFrame({
        'timestamp': [datetime.now()],
        'market': ['0x123'],
        'price': [0.5],
        'size': [100],
        'side': ['BUY']
    })
    assert validate_trades_df(valid_df) == True
    print(f"  ✓ 数据验证")
    
    return True

def test_backtest_engine():
    """测试回测引擎"""
    from backtest_engine import (
        VolatilityMarketMakerStrategy,
        BacktestEngine,
        Signal,
        calculate_sharpe_ratio,
        calculate_max_drawdown
    )
    
    print("\n[5] 测试回测引擎...")
    
    # 测试策略初始化
    config = {
        'stop_loss_threshold': -5.0,
        'take_profit_threshold': 3.0,
        'volatility_threshold': 0.15,
    }
    strategy = VolatilityMarketMakerStrategy(config)
    assert strategy.config['stop_loss_threshold'] == -5.0
    print(f"  ✓ 策略初始化")
    
    # 测试引擎初始化
    engine = BacktestEngine(strategy, initial_capital=10000)
    assert engine.initial_capital == 10000
    print(f"  ✓ 回测引擎初始化")
    
    # 测试夏普比率
    returns = pd.Series([0.01, -0.005, 0.02, -0.01, 0.015])
    sharpe = calculate_sharpe_ratio(returns)
    assert sharpe != 0 or len(returns) < 2
    print(f"  ✓ 夏普比率计算: {sharpe:.4f}")
    
    return True

def test_with_mock_data():
    """使用 Mock 数据测试完整流程"""
    from data_adapter import SMBDataAdapter
    from volatility_calc import calculate_volatility
    
    print("\n[6] 使用 Mock 数据测试...")
    
    # 加载 Mock 数据
    mock_path = "tests/mock_data/polymarket/trades/0x218919622a6132646d149021008659d834927b2b81005a92a54b38d781b0a56f.csv"
    df = pd.read_csv(mock_path)
    
    assert len(df) == 1000, f"数据行数错误: {len(df)}"
    print(f"  ✓ 加载 Mock 数据: {len(df)} 行")
    
    # 测试波动率计算
    vol = calculate_volatility(df['price'])
    assert vol >= 0, "波动率应非负"
    print(f"  ✓ Mock 数据波动率: {vol:.4f}")
    
    return True

def main():
    """运行所有测试"""
    print("=" * 60)
    print("🧪 基础功能验证测试")
    print("=" * 60)
    
    tests = [
        ("波动率计算", test_volatility_calc),
        ("订单定价", test_order_pricing),
        ("风险管理", test_risk_management),
        ("数据适配器", test_data_adapter),
        ("回测引擎", test_backtest_engine),
        ("Mock 数据测试", test_with_mock_data),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"  ✗ 测试失败: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 测试结果: {passed} 通过, {failed} 失败")
    print("=" * 60)
    
    if failed == 0:
        print("✅ 所有测试通过!")
    else:
        print("❌ 部分测试失败")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
