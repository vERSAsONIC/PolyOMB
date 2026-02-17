"""
00002 test_risk_management.py - 风险管理测试

测试目标:
- 验证止损/止盈逻辑
- 验证波动率风控
- 验证持仓限制
- 测试风险状态管理
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from .risk_management import (
    should_trigger_stop_loss,
    calculate_take_profit_price,
    adjust_ask_for_take_profit,
    should_pause_trading,
    can_open_new_position,
    can_close_position,
    can_increase_position,
    can_buy_no,
    is_valid_trade_size,
    is_in_risk_off_period,
    calculate_risk_off_end_time,
    is_valid_buy_price,
    is_valid_sell_price,
    check_price_deviation,
    comprehensive_risk_check,
    RiskLevel,
    RiskManager,
)


class TestStopLossLogic:
    """止损逻辑测试"""
    
    # =============================================================================
    # 基础止损触发
    # =============================================================================
    
    def test_stop_loss_triggered_by_pnl(self):
        """
        测试 PnL 触发止损
        
        条件: PnL < stop_loss_threshold AND spread <= spread_threshold
        """
        # 场景: 亏损 6%，触发 -5% 止损
        pnl = -6.0  # 亏损百分比
        spread = 0.01  # 价差
        stop_loss_threshold = -5.0
        spread_threshold = 0.02
        
        result = should_trigger_stop_loss(
            pnl, spread, 
            stop_loss_threshold, 
            spread_threshold
        )
        assert result is True
    
    def test_stop_loss_not_triggered_by_low_pnl(self):
        """测试未达阈值的亏损不触发止损"""
        pnl = -3.0  # 亏损 3%，未达到 -5% 阈值
        spread = 0.01
        stop_loss_threshold = -5.0
        spread_threshold = 0.02
        
        result = should_trigger_stop_loss(pnl, spread, stop_loss_threshold, spread_threshold)
        assert result is False
    
    def test_stop_loss_not_triggered_by_high_spread(self):
        """
        测试高价差不触发止损
        
        即使亏损严重，价差太大时也不止损（避免滑点损失）
        """
        pnl = -10.0  # 严重亏损
        spread = 0.10  # 但价差很大（10 cents）
        spread_threshold = 0.02
        
        result = should_trigger_stop_loss(pnl, spread, -5.0, spread_threshold)
        assert result is False
    
    def test_stop_loss_exact_threshold(self):
        """测试恰好在阈值边界的情况"""
        # 边界情况: PnL 恰好等于 -5%
        pnl = -5.0
        spread = 0.01
        
        # 应触发（保守策略）
        result = should_trigger_stop_loss(pnl, spread, -5.0, 0.02)
        assert result is True
    
    # =============================================================================
    # 止盈逻辑
    # =============================================================================
    
    def test_take_profit_calculation(self):
        """
        测试止盈价格计算
        
        formula: tp_price = avg_price * (1 + take_profit_threshold/100)
        """
        avg_price = 0.60
        take_profit_threshold = 3.0  # 3%
        
        tp_price = calculate_take_profit_price(avg_price, take_profit_threshold)
        expected = 0.60 * 1.03  # 0.618
        
        assert abs(tp_price - expected) < 0.001
    
    def test_take_profit_order_placement(self):
        """
        测试止盈订单放置
        
        当 ask_price < tp_price 时，应调整至 tp_price
        """
        avg_price = 0.60
        current_ask = 0.61
        tp_threshold = 3.0
        
        tp_price = 0.618
        final_ask = adjust_ask_for_take_profit(current_ask, avg_price, tp_threshold)
        
        # 应调整到止盈价格
        assert final_ask == pytest.approx(tp_price, abs=0.001)
    
    def test_take_profit_above_threshold(self):
        """测试当前价格已高于止盈线的情况"""
        avg_price = 0.60
        current_ask = 0.65  # 已高于 tp_price (0.618)
        
        # 应保持当前价格（取较高者）
        final_ask = adjust_ask_for_take_profit(current_ask, avg_price, 3.0)
        assert final_ask == 0.65


class TestVolatilityRiskControl:
    """波动率风控测试"""
    
    def test_trading_paused_by_high_volatility(self):
        """
        测试高波动率暂停交易
        
        3小时波动率 > volatility_threshold 时应暂停
        """
        volatility_3h = 0.20  # 20% 波动率
        threshold = 0.15  # 阈值 15%
        
        result = should_pause_trading(volatility_3h, threshold)
        assert result is True
    
    def test_trading_continues_with_normal_volatility(self):
        """测试正常波动率下继续交易"""
        volatility_3h = 0.10  # 10% 波动率
        threshold = 0.15
        
        result = should_pause_trading(volatility_3h, threshold)
        assert result is False
    
    def test_trading_paused_at_exact_threshold(self):
        """测试恰好在波动率阈值的情况"""
        volatility_3h = 0.15
        threshold = 0.15
        
        # 应暂停（保守策略）
        result = should_pause_trading(volatility_3h, threshold)
        assert result is True
    
    def test_volatility_spike_during_position(self):
        """
        测试持仓期间波动率飙升
        
        已有持仓时波动率飙升，应暂停新开仓，但允许平仓
        """
        has_position = True
        volatility_3h = 0.25
        threshold = 0.15
        
        # 不应开新仓
        assert can_open_new_position(volatility_3h, threshold, has_position) is False
        
        # 但应允许平仓（止损/止盈）
        assert can_close_position(volatility_3h, has_position) is True


class TestPositionLimits:
    """持仓限制测试"""
    
    def test_max_position_size_limit(self):
        """
        测试最大持仓限制
        
        当前持仓 >= max_position_size 时不应再买
        """
        current_position = 250
        max_size = 250
        
        result = can_increase_position(current_position, max_size)
        assert result is False
    
    def test_position_below_max_can_increase(self):
        """测试持仓低于限制时可以增加"""
        current_position = 200
        max_size = 250
        
        result = can_increase_position(current_position, max_size)
        assert result is True
    
    def test_opposite_position_check(self):
        """
        测试反向持仓检查
        
        持有 YES 时不应买更多 NO（应先合并或平仓）
        """
        yes_position = 100
        no_position = 5  # 少量反向持仓
        max_position_size = 250
        
        # 不应增加 NO 持仓（因为已有 YES 且 NO 持仓 > 0）
        # 函数签名: can_buy_no(yes_position, no_position, max_position_size)
        result = can_buy_no(yes_position, no_position, max_position_size)
        # 当前逻辑：如果 YES 持仓 > 10 且 NO 持仓 > 0，则不允许买入 NO
        assert result is False
    
    def test_opposite_position_can_buy_when_small(self):
        """测试小仓位时可以买入"""
        yes_position = 0
        no_position = 5
        
        result = can_buy_no(no_position, yes_position)
        assert result is True
    
    def test_min_trade_size_check(self):
        """测试最小交易数量检查"""
        proposed_size = 3
        min_size = 5
        
        # 小于最小数量不应下单
        result = is_valid_trade_size(proposed_size, min_size)
        assert result is False
        
        # 大于等于最小数量应通过
        result = is_valid_trade_size(5, 5)
        assert result is True


class TestRiskOffPeriod:
    """风险关闭期测试"""
    
    def test_risk_off_period_after_stop_loss(self):
        """
        测试止损后的风险关闭期
        
        止损后应在 sleep_period 小时内暂停交易
        """
        # 触发止损
        sleep_period = 6  # 小时
        risk_off_time = datetime.now() - timedelta(hours=3)  # 3小时前触发
        sleep_until = calculate_risk_off_end_time(risk_off_time, sleep_period)
        
        # 在关闭期内不应交易
        assert is_in_risk_off_period(sleep_until) is True
    
    def test_risk_off_period_expiration(self):
        """测试风险关闭期过期"""
        # 6小时前触发止损
        risk_off_time = datetime.now() - timedelta(hours=7)
        sleep_period = 6
        sleep_until = calculate_risk_off_end_time(risk_off_time, sleep_period)
        
        # 已过关闭期
        assert is_in_risk_off_period(sleep_until) is False


class TestPriceRangeValidation:
    """价格范围验证测试"""
    
    def test_buy_order_price_range(self):
        """
        测试买单价格范围
        
        poly-maker 限制: 0.1 <= price < 0.9
        """
        # 价格太低
        assert is_valid_buy_price(0.05) is False
        
        # 价格太高
        assert is_valid_buy_price(0.95) is False
        
        # 有效价格
        assert is_valid_buy_price(0.50) is True
        assert is_valid_buy_price(0.10) is True  # 边界包含
        assert is_valid_buy_price(0.89) is True  # 边界不包含 0.9
    
    def test_sell_order_price_range(self):
        """测试卖单价格范围"""
        # 价格太低
        assert is_valid_sell_price(0.05) is False
        
        # 价格太高
        assert is_valid_sell_price(0.95) is False
        
        # 有效价格
        assert is_valid_sell_price(0.50) is True
        assert is_valid_sell_price(0.11) is True
        assert is_valid_sell_price(0.90) is True  # 边界包含
    
    def test_price_change_threshold(self):
        """
        测试价格变化阈值
        
        价格偏离参考价超过阈值时暂停交易
        """
        reference_price = 0.50
        current_price = 0.60  # 偏离 10 cents
        threshold = 0.05  # 阈值 5 cents
        
        # 应检测到偏离
        result = check_price_deviation(current_price, reference_price, threshold)
        assert result is True
        
        # 未偏离
        result = check_price_deviation(0.52, reference_price, 0.05)
        assert result is False


class TestRiskManagementIntegration:
    """风险管理集成测试"""
    
    def test_comprehensive_risk_check_low_risk(self):
        """
        综合风险检查 - 低风险场景
        
        所有条件都在安全范围内
        """
        result = comprehensive_risk_check(
            pnl=-2.0,
            spread=0.015,
            volatility_3h=0.10,
            position_size=150,
            max_position=250,
            in_risk_off_period=False,
            stop_loss_threshold=-5.0,
            spread_threshold=0.02,
            volatility_threshold=0.15,
        )
        
        # 此场景: 亏损但未达止损，波动率正常，持仓未超限
        assert result.can_trade is True
        assert result.risk_level == RiskLevel.LOW
    
    def test_comprehensive_risk_check_stop_loss(self):
        """综合风险检查 - 止损场景"""
        result = comprehensive_risk_check(
            pnl=-6.0,  # 触发止损
            spread=0.01,
            volatility_3h=0.10,
            position_size=150,
            max_position=250,
            in_risk_off_period=False,
        )
        
        assert result.can_trade is False
        assert result.risk_level == RiskLevel.CRITICAL
    
    def test_comprehensive_risk_check_high_volatility(self):
        """综合风险检查 - 高波动率场景"""
        result = comprehensive_risk_check(
            pnl=-2.0,
            spread=0.01,
            volatility_3h=0.20,  # 高波动率
            position_size=150,
            max_position=250,
            in_risk_off_period=False,
        )
        
        # 高波动率仍允许交易，但标记为中风险
        assert result.can_trade is True
        assert result.risk_level == RiskLevel.MEDIUM
    
    def test_comprehensive_risk_check_risk_off(self):
        """综合风险检查 - 风险关闭期场景"""
        result = comprehensive_risk_check(
            pnl=-2.0,
            spread=0.01,
            volatility_3h=0.10,
            position_size=150,
            max_position=250,
            in_risk_off_period=True,  # 在风险关闭期
        )
        
        assert result.can_trade is False
        assert result.risk_level == RiskLevel.HIGH


class TestRiskManager:
    """风险管理器类测试"""
    
    def test_risk_manager_initialization(self, default_skill_config):
        """测试风险管理器初始化"""
        manager = RiskManager(default_skill_config)
        
        assert manager.config == default_skill_config
        assert manager.risk_off_until is None
    
    def test_risk_manager_stop_loss_trigger(self, default_skill_config):
        """测试风险管理器触发止损"""
        manager = RiskManager(default_skill_config)
        
        # 初始不在风险关闭期
        assert manager.is_in_risk_off_period() is False
        
        # 触发止损
        manager.trigger_stop_loss()
        
        # 现在在风险关闭期
        assert manager.is_in_risk_off_period() is True
    
    def test_risk_manager_clear_risk_off(self, default_skill_config):
        """测试清除风险关闭期"""
        manager = RiskManager(default_skill_config)
        
        # 触发止损
        manager.trigger_stop_loss()
        assert manager.is_in_risk_off_period() is True
        
        # 清除
        manager.clear_risk_off_period()
        assert manager.is_in_risk_off_period() is False
    
    def test_risk_manager_check_risk(self, default_skill_config):
        """测试风险管理器风险检查"""
        manager = RiskManager(default_skill_config)
        
        result = manager.check_risk(
            pnl=-2.0,
            spread=0.01,
            volatility_3h=0.10,
            position_size=150
        )
        
        assert isinstance(result.can_trade, bool)
        assert isinstance(result.risk_level, RiskLevel)
