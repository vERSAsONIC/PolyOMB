"""
00002 order_pricing.py - 订单定价模块

提供订单定价功能，参考 poly-maker 核心算法
"""

import numpy as np
from typing import Dict, Tuple, Optional


def round_to_tick_size(price: float, tick_size: float) -> float:
    """
    将价格按 tick size 舍入
    
    使用四舍五入规则
    
    Args:
        price: 原始价格
        tick_size: 最小价格变动单位
        
    Returns:
        舍入后的价格
    """
    if tick_size <= 0:
        return price
    return round(price / tick_size) * tick_size


def get_order_prices(
    order_book: Dict,
    avg_price: float,
    row: Optional[Dict] = None,
    position_size: float = 0
) -> Tuple[float, float]:
    """
    计算订单买卖价格
    
    基于 poly-maker 算法的简化实现:
    1. 计算中间价
    2. 根据订单簿深度调整价差
    3. 考虑持仓情况调整卖价
    4. 确保价格在合理范围内
    
    Args:
        order_book: 订单簿数据，包含 best_bid, best_ask, 等
        avg_price: 持仓均价 (0 表示无持仓)
        row: 市场参数行，包含 tick_size 等
        position_size: 持仓数量
        
    Returns:
        (bid_price, ask_price)
    """
    # 获取参数
    tick_size = row.get('tick_size', 0.01) if row else 0.01
    
    # 获取订单簿数据
    best_bid = order_book.get('best_bid', 0.0) or 0.0
    best_ask = order_book.get('best_ask', 0.0) or 0.0
    best_bid_size = order_book.get('best_bid_size', 0) or 0
    best_ask_size = order_book.get('best_ask_size', 0) or 0
    
    # 如果没有订单簿数据，使用默认值
    if best_bid == 0 and best_ask == 0:
        best_bid = 0.49
        best_ask = 0.51
    elif best_bid == 0:
        best_bid = best_ask - 0.02
    elif best_ask == 0:
        best_ask = best_bid + 0.02
    
    # 计算中间价
    mid_price = (best_bid + best_ask) / 2
    
    # 基础价差 (2 cents)
    base_spread = 0.02
    
    # 根据订单簿深度调整价差
    # 深度好 -> 价差小，深度差 -> 价差大
    bid_sum = order_book.get('bid_sum_within_n_percent', 1000) or 1000
    ask_sum = order_book.get('ask_sum_within_n_percent', 1000) or 1000
    
    # 平均深度
    avg_depth = (bid_sum + ask_sum) / 2
    
    # 深度调整因子 (深度越大，价差越小)
    if avg_depth > 5000:
        depth_factor = 0.8  # 深度很好，缩小价差
    elif avg_depth > 2000:
        depth_factor = 0.9
    elif avg_depth > 500:
        depth_factor = 1.0  # 正常深度
    else:
        depth_factor = 1.2  # 深度不足，扩大价差
    
    spread = base_spread * depth_factor
    
    # 确保价差在合理范围内 [0.01, 0.05]
    spread = max(0.01, min(spread, 0.05))
    
    # 计算基础买卖价
    bid = mid_price - spread / 2
    ask = mid_price + spread / 2
    
    # 确保买价低于最优买价，卖价高于最优卖价
    # 但我们提供更好的流动性（更接近中间价）
    bid = min(bid, best_bid - tick_size)
    ask = max(ask, best_ask + tick_size)
    
    # 根据持仓调整卖价 (止盈考虑)
    if position_size > 0 and avg_price > 0:
        # 有持仓时，确保卖价不低于成本价的 97%
        # 同时考虑止盈 (+3%)
        min_ask_for_profit = avg_price * 1.03  # 止盈价格
        min_ask_for_cost = avg_price * 0.97    # 成本保护
        
        # 取较高者，但不要太激进
        min_ask = max(min_ask_for_cost, min(best_ask, min_ask_for_profit))
        ask = max(ask, min_ask)
    
    # 如果持有空头 (position_size < 0)，调整买价
    if position_size < 0 and avg_price > 0:
        # 空头时，确保买价不高于成本价的 103%
        max_bid_for_profit = avg_price * 0.97  # 空头止盈
        max_bid_for_cost = avg_price * 1.03    # 成本保护
        
        max_bid = min(max_bid_for_cost, max(best_bid, max_bid_for_profit))
        bid = min(bid, max_bid)
    
    # 舍入到 tick size
    bid = round_to_tick_size(bid, tick_size)
    ask = round_to_tick_size(ask, tick_size)
    
    # 最终检查: 确保买价 < 卖价
    if bid >= ask:
        # 如果冲突，以中间价为准，强制设置价差
        ask = round_to_tick_size(mid_price + spread / 2, tick_size)
        bid = round_to_tick_size(ask - spread, tick_size)
    
    # 确保价格在有效范围 [0.01, 0.99]
    bid = max(0.01, min(bid, 0.99))
    ask = max(0.01, min(ask, 0.99))
    
    return bid, ask


def calculate_bid_ask(order_book: Dict) -> Tuple[float, float]:
    """
    计算基础买卖价格
    
    Args:
        order_book: 订单簿数据
        
    Returns:
        (bid, ask)
    """
    return get_order_prices(order_book, avg_price=0.0)


def calculate_spread(bid: float, ask: float) -> float:
    """
    计算价差
    
    Args:
        bid: 买价
        ask: 卖价
        
    Returns:
        价差 (ask - bid)
    """
    return ask - bid


def is_valid_spread(
    bid: float,
    ask: float,
    min_spread: float = 0.01,
    max_spread: float = 0.05
) -> bool:
    """
    检查价差是否在有效范围内
    
    Args:
        bid: 买价
        ask: 卖价
        min_spread: 最小价差
        max_spread: 最大价差
        
    Returns:
        True 如果价差有效
    """
    if bid <= 0 or ask <= 0 or bid >= ask:
        return False
    
    spread = calculate_spread(bid, ask)
    return min_spread <= spread <= max_spread


def calculate_order_size(
    position: float,
    bid_price: float,
    row: Dict,
    other_position: float
) -> Tuple[float, float]:
    """
    计算买卖订单数量
    
    Args:
        position: 当前持仓
        bid_price: 买价 (用于计算)
        row: 市场参数，包含 trade_size, max_size, min_size
        other_position: 反向持仓数量
        
    Returns:
        (buy_amount, sell_amount)
    """
    trade_size = row.get('trade_size', 50)
    max_size = row.get('max_size', 250)
    min_size = row.get('min_size', 5)
    
    # 计算可买入数量
    # 限制: 不超过 max_size，考虑现有持仓
    room_for_buy = max(0, max_size - position)
    buy_amount = min(trade_size, room_for_buy)
    
    # 如果反向持仓较大，减少买入 (避免对冲)
    if other_position > min_size:
        buy_amount = 0
    
    # 买入数量必须 >= min_size 才有效
    if buy_amount < min_size:
        buy_amount = 0
    
    # 计算可卖出数量
    # 限制: 不超过现有持仓
    sell_amount = min(trade_size, position)
    
    # 卖出数量必须 >= min_size 才有效
    if sell_amount < min_size:
        sell_amount = 0
    
    return buy_amount, sell_amount


def should_adjust_for_imbalance(order_book: Dict) -> Tuple[bool, str]:
    """
    检查是否应该因订单簿失衡调整定价
    
    Args:
        order_book: 订单簿数据
        
    Returns:
        (should_adjust, direction)
        direction: "buy_heavy" | "sell_heavy" | "balanced"
    """
    bid_sum = order_book.get('bid_sum_within_n_percent', 1000) or 1000
    ask_sum = order_book.get('ask_sum_within_n_percent', 1000) or 1000
    
    if ask_sum == 0:
        return True, "buy_heavy"
    
    ratio = bid_sum / ask_sum
    
    # ratio > 2: 买方远大于卖方
    if ratio > 2:
        return True, "buy_heavy"
    
    # ratio < 0.5: 卖方远大于买方
    if ratio < 0.5:
        return True, "sell_heavy"
    
    return False, "balanced"


def adjust_for_imbalance(
    bid: float,
    ask: float,
    direction: str,
    adjustment_factor: float = 0.01
) -> Tuple[float, float]:
    """
    根据失衡方向调整价格
    
    Args:
        bid: 原买价
        ask: 原卖价
        direction: 失衡方向 ("buy_heavy" | "sell_heavy")
        adjustment_factor: 调整因子
        
    Returns:
        调整后的 (bid, ask)
    """
    if direction == "buy_heavy":
        # 买方占优，市场倾向于上涨
        # 提高卖价以获取更高利润，稍微提高买价以确保成交
        ask += adjustment_factor
        bid += adjustment_factor * 0.5
    elif direction == "sell_heavy":
        # 卖方占优，市场倾向于下跌
        # 降低买价以获取更低成本，稍微降低卖价以确保成交
        bid -= adjustment_factor
        ask -= adjustment_factor * 0.5
    
    return bid, ask


def validate_order_book(order_book: Dict) -> bool:
    """
    验证订单簿数据有效性
    
    Args:
        order_book: 订单簿数据
        
    Returns:
        True 如果有效
    """
    # 至少要有买价或卖价
    has_bid = 'best_bid' in order_book and order_book['best_bid'] is not None
    has_ask = 'best_ask' in order_book and order_book['best_ask'] is not None
    
    return has_bid or has_ask


class OrderPricer:
    """
    订单定价器类
    
    封装定价逻辑，便于配置和复用
    """
    
    def __init__(
        self,
        tick_size: float = 0.01,
        min_spread: float = 0.01,
        max_spread: float = 0.05,
        base_spread: float = 0.02
    ):
        """
        初始化定价器
        
        Args:
            tick_size: 最小价格变动
            min_spread: 最小价差
            max_spread: 最大价差
            base_spread: 基础价差
        """
        self.tick_size = tick_size
        self.min_spread = min_spread
        self.max_spread = max_spread
        self.base_spread = base_spread
    
    def get_prices(self, order_book: Dict, avg_price: float = 0.0) -> Tuple[float, float]:
        """
        获取定价
        
        Args:
            order_book: 订单簿数据
            avg_price: 持仓均价
            
        Returns:
            (bid, ask)
        """
        return get_order_prices(
            order_book,
            avg_price=avg_price,
            row={'tick_size': self.tick_size}
        )
    
    def validate_spread(self, bid: float, ask: float) -> bool:
        """
        验证价差
        
        Args:
            bid: 买价
            ask: 卖价
            
        Returns:
            True 如果价差有效
        """
        return is_valid_spread(bid, ask, self.min_spread, self.max_spread)
