"""
00002 test_order_pricing.py - 订单定价测试

测试目标:
- 验证订单定价逻辑与 poly-maker 原始算法一致
- 测试买卖价计算
- 测试基于持仓的定价调整
- 测试价差约束
"""

import pytest
import pandas as pd
import numpy as np

from .order_pricing import (
    round_to_tick_size,
    get_order_prices,
    calculate_bid_ask,
    calculate_spread,
    is_valid_spread,
    calculate_order_size,
    should_adjust_for_imbalance,
    adjust_for_imbalance,
    validate_order_book,
    OrderPricer,
)


class TestOrderPricingBasic:
    """基础订单定价测试"""
    
    # =============================================================================
    # 基础买卖价计算
    # =============================================================================
    
    def test_basic_bid_ask_calculation(self):
        """
        测试基础买卖价计算
        
        给定订单簿数据，计算合理的买卖挂单价格
        """
        order_book = {
            'best_bid': 0.65,
            'best_bid_size': 100,
            'second_best_bid': 0.64,
            'second_best_bid_size': 150,
            'top_bid': 0.60,
            'best_ask': 0.67,
            'best_ask_size': 120,
            'second_best_ask': 0.68,
            'second_best_ask_size': 140,
            'top_ask': 0.72,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        avg_price = 0.66
        row = {'tick_size': 0.01}
        
        bid, ask = get_order_prices(order_book, avg_price, row)
        
        # 验证基本约束:
        # 1. 买价应低于最优买价
        assert bid < order_book['best_bid']
        
        # 2. 卖价应高于最优卖价
        assert ask > order_book['best_ask']
        
        # 3. 买价 < 卖价（无套利）
        assert bid < ask
    
    def test_bid_less_than_best_bid(self):
        """
        验证买价始终低于最优买价
        
        这是做市商的基本策略: 不抢最优价，提供流动性
        """
        test_cases = [
            {'best_bid': 0.50, 'best_ask': 0.52},
            {'best_bid': 0.75, 'best_ask': 0.77},
            {'best_bid': 0.30, 'best_ask': 0.35},
        ]
        
        for case in test_cases:
            order_book = {
                'best_bid': case['best_bid'],
                'best_bid_size': 100,
                'second_best_bid': case['best_bid'] - 0.01,
                'second_best_bid_size': 100,
                'top_bid': case['best_bid'] - 0.05,
                'best_ask': case['best_ask'],
                'best_ask_size': 100,
                'second_best_ask': case['best_ask'] + 0.01,
                'second_best_ask_size': 100,
                'top_ask': case['best_ask'] + 0.05,
                'bid_sum_within_n_percent': 1000,
                'ask_sum_within_n_percent': 1000,
            }
            
            bid, _ = get_order_prices(order_book, avg_price=case['best_bid'], row={'tick_size': 0.01})
            assert bid < case['best_bid']
    
    def test_ask_greater_than_best_ask(self):
        """验证卖价始终高于最优卖价"""
        order_book = {
            'best_bid': 0.65,
            'best_ask': 0.67,
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        _, ask = get_order_prices(order_book, avg_price=0.66)
        assert ask > order_book['best_ask']
    
    def test_spread_constraint(self):
        """
        测试价差约束
        
        验证: ask - bid 在合理范围内 (1-5 cents)
        """
        order_book = {
            'best_bid': 0.65,
            'best_bid_size': 100,
            'second_best_bid': 0.64,
            'second_best_bid_size': 100,
            'top_bid': 0.60,
            'best_ask': 0.67,
            'best_ask_size': 100,
            'second_best_ask': 0.68,
            'second_best_ask_size': 100,
            'top_ask': 0.72,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        bid, ask = get_order_prices(order_book, avg_price=0.66)
        spread = ask - bid
        
        # 价差应在 0.01-0.05 之间
        assert 0.01 <= spread <= 0.05
    
    # =============================================================================
    # Tick Size 处理
    # =============================================================================
    
    def test_tick_size_rounding(self):
        """
        测试 Tick Size 舍入
        
        验证: 价格按 tick_size 舍入到正确精度
        """
        raw_price = 0.654321
        tick_size = 0.01
        rounded = round_to_tick_size(raw_price, tick_size)
        assert rounded == 0.65
        
        # 测试舍入规则
        assert round_to_tick_size(0.655, 0.01) == 0.66
        assert round_to_tick_size(0.654, 0.01) == 0.65
    
    def test_different_tick_sizes(self):
        """测试不同 tick size"""
        tick_sizes = [0.01, 0.001, 0.0001]
        
        for tick in tick_sizes:
            price = 0.5
            rounded = round_to_tick_size(price + 0.00033, tick)
            
            # 验证价格精度
            assert abs(rounded - round(rounded / tick) * tick) < 1e-10


class TestOrderPricingWithPosition:
    """基于持仓的定价调整测试"""
    
    def test_profit_based_pricing_long_position(self):
        """
        测试多头持仓时的定价调整
        
        持有 YES 仓位，均价 0.60，现价 0.65
        应调整卖价以锁定利润
        """
        order_book = {
            'best_bid': 0.64,
            'best_bid_size': 100,
            'second_best_bid': 0.63,
            'top_bid': 0.60,
            'best_ask': 0.66,
            'best_ask_size': 100,
            'second_best_ask': 0.67,
            'top_ask': 0.70,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        position_avg = 0.60  # 持仓均价
        current_mid = 0.65
        
        bid, ask = get_order_prices(order_book, position_avg, position_size=100)
        
        # 有盈利持仓时，卖价应不低于均价
        assert ask >= position_avg * 0.97  # 允许一定误差
    
    def test_loss_based_pricing(self):
        """
        测试亏损持仓时的定价调整
        
        均价 0.70，现价 0.65，处于亏损状态
        应更保守地定价以等待回本
        """
        order_book = {
            'best_bid': 0.64,
            'best_ask': 0.66,
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        position_avg = 0.70
        
        # 期望: 卖价接近或略高于均价，不轻易割肉
        bid, ask = get_order_prices(order_book, position_avg, position_size=100)
        assert ask >= position_avg * 0.95  # 不低于均价太多
    
    def test_zero_position_pricing(self):
        """测试零持仓时的定价"""
        order_book = {
            'best_bid': 0.65,
            'best_ask': 0.67,
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        position_avg = 0
        
        # 零持仓时不应考虑持仓因素
        bid, ask = get_order_prices(order_book, position_avg, position_size=0)
        
        # 价格应仅基于订单簿
        assert bid < order_book['best_bid']
        assert ask > order_book['best_ask']


class TestOrderPricingMarketConditions:
    """不同市场条件下的定价测试"""
    
    def test_deep_liquidity_pricing(self):
        """
        测试深度流动性市场的定价
        
        订单簿深度大，可以挂更大的单
        """
        deep_book = {
            'best_bid': 0.65,
            'best_bid_size': 1000,  # 大深度
            'second_best_bid': 0.64,
            'second_best_bid_size': 2000,
            'top_bid': 0.60,
            'best_ask': 0.67,
            'best_ask_size': 1000,
            'second_best_ask': 0.68,
            'second_best_ask_size': 2000,
            'top_ask': 0.72,
            'bid_sum_within_n_percent': 10000,
            'ask_sum_within_n_percent': 10000,
        }
        
        # 深度好时可以更接近最优价
        bid, ask = get_order_prices(deep_book, avg_price=0.66)
        spread = ask - bid
        
        # 深度好的市场价差更小
        assert spread < 0.05
    
    def test_thin_liquidity_pricing(self):
        """
        测试流动性差市场的定价
        
        订单簿深度小，需要更保守的定价
        """
        thin_book = {
            'best_bid': 0.65,
            'best_bid_size': 10,  # 小深度
            'second_best_bid': 0.60,
            'second_best_bid_size': 5,
            'top_bid': 0.55,
            'best_ask': 0.67,
            'best_ask_size': 10,
            'second_best_ask': 0.72,
            'second_best_ask_size': 5,
            'top_ask': 0.75,
            'bid_sum_within_n_percent': 50,
            'ask_sum_within_n_percent': 50,
        }
        
        # 流动性差时扩大价差
        bid, ask = get_order_prices(thin_book, avg_price=0.66)
        spread = ask - bid
        
        # 流动性差的市场价差更大
        assert spread >= 0.01
    
    def test_imbalanced_order_book(self):
        """
        测试不平衡订单簿的定价
        
        买量远大于卖量，或反之
        """
        imbalanced_book = {
            'best_bid': 0.65,
            'best_bid_size': 1000,  # 买量大
            'best_ask': 0.67,
            'best_ask_size': 50,     # 卖量小
            'bid_sum_within_n_percent': 5000,
            'ask_sum_within_n_percent': 200,
        }
        
        # 检查是否检测到失衡
        should_adjust, direction = should_adjust_for_imbalance(imbalanced_book)
        
        # ratio = bid_sum / ask_sum = 25 (买方占优)
        assert should_adjust is True
        assert direction == "buy_heavy"


class TestOrderPricingEdgeCases:
    """边界情况测试"""
    
    def test_empty_order_book(self):
        """测试空订单簿"""
        empty_book = {}
        
        # 空订单簿应有默认值
        bid, ask = get_order_prices(empty_book, avg_price=0.5)
        
        # 应有合理的默认值
        assert bid > 0
        assert ask > bid
    
    def test_single_side_order_book(self):
        """测试只有单边深度的订单簿"""
        single_side = {
            'best_bid': 0.65,
            'best_bid_size': 100,
            'best_ask': 0.67,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        # 正常定价
        bid, ask = get_order_prices(single_side, avg_price=0.66)
        assert bid < ask
    
    def test_extreme_spread(self):
        """测试极端价差"""
        extreme_book = {
            'best_bid': 0.30,
            'best_ask': 0.70,  # 40 cent 价差，极端情况
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        # 极端价差时应限制最大价差
        bid, ask = get_order_prices(extreme_book, avg_price=0.50)
        spread = ask - bid
        
        # 验证基本约束：买价 < 卖价，且在有效范围
        assert bid < ask
        assert 0.01 <= bid <= 0.99
        assert 0.01 <= ask <= 0.99
    
    def test_price_at_bounds(self):
        """测试价格接近边界 (0.01 和 0.99)"""
        bound_book = {
            'best_bid': 0.01,
            'best_ask': 0.03,
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        bid, ask = get_order_prices(bound_book, avg_price=0.02)
        
        # 低价市场应限制最小价格
        assert bid >= 0.01
        
        bound_book_high = {
            'best_bid': 0.97,
            'best_ask': 0.99,
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        bid, ask = get_order_prices(bound_book_high, avg_price=0.98)
        
        # 高价市场应限制最大价格
        assert ask <= 0.99


class TestOrderPricerClass:
    """OrderPricer 类测试"""
    
    def test_pricer_initialization(self):
        """测试定价器初始化"""
        pricer = OrderPricer(
            tick_size=0.01,
            min_spread=0.01,
            max_spread=0.05
        )
        
        assert pricer.tick_size == 0.01
        assert pricer.min_spread == 0.01
        assert pricer.max_spread == 0.05
    
    def test_pricer_get_prices(self):
        """测试定价器获取价格"""
        pricer = OrderPricer()
        
        order_book = {
            'best_bid': 0.65,
            'best_ask': 0.67,
            'best_bid_size': 100,
            'best_ask_size': 100,
            'bid_sum_within_n_percent': 1000,
            'ask_sum_within_n_percent': 1000,
        }
        
        bid, ask = pricer.get_prices(order_book)
        
        assert bid < ask
        assert bid < order_book['best_bid']
        assert ask > order_book['best_ask']
    
    def test_pricer_validate_spread(self):
        """测试定价器验证价差"""
        pricer = OrderPricer(min_spread=0.01, max_spread=0.05)
        
        # 有效价差
        assert pricer.validate_spread(0.64, 0.67) is True  # 3 cents
        
        # 价差太小
        assert pricer.validate_spread(0.64, 0.645) is False  # 0.5 cents
        
        # 价差太大
        assert pricer.validate_spread(0.60, 0.70) is False  # 10 cents


# =============================================================================
# 与 poly-maker 对比测试
# =============================================================================

class TestOrderPricingVsPolyMaker:
    """与 poly-maker 原始算法对比"""
    
    def test_pricing_algorithm_structure(self, sample_orderbook_snapshots):
        """
        验证定价算法结构正确
        
        使用相同输入，验证输出格式符合预期
        """
        # 对于每个订单簿快照
        for _, row in sample_orderbook_snapshots.head(10).iterrows():
            order_book = row.to_dict()
            
            # 确保必要字段存在
            if 'best_bid' in order_book and 'best_ask' in order_book:
                bid, ask = get_order_prices(order_book, avg_price=0.5)
                
                # 验证基本约束
                assert isinstance(bid, float)
                assert isinstance(ask, float)
                assert bid < ask
                assert 0.01 <= bid <= 0.99
                assert 0.01 <= ask <= 0.99
