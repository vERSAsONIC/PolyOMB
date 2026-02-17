#!/usr/bin/env python3
"""
00002 order_pricing.py - 订单定价模块

提供做市商订单定价逻辑，与 poly-maker 原始算法一致
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple


def round_to_tick_size(price: float, tick_size: float) -> float:
    """
    将价格按 tick_size 舍入
    
    Args:
        price: 原始价格
        tick_size: 最小价格单位
    
    Returns:
        舍入后的价格
    """
    return round(price / tick_size) * tick_size


def get_order_prices(
    order_book: Dict,
    avg_price: float,
    row: Optional[Dict] = None,
    position_size: int = 0,
    tick_size: float = 0.01,
) -> Tuple[float, float]:
    """
    计算买卖挂单价格
    
    Args:
        order_book: 订单簿数据
        avg_price: 持仓均价（0表示无持仓）
        row: 额外数据行
        position_size: 当前持仓数量
        tick_size: 最小价格单位
    
    Returns:
        (bid_price, ask_price) 元组
    """
    best_bid = order_book.get('best_bid', 0.5)
    best_ask = order_book.get('best_ask', 0.5)
    best_bid_size = order_book.get('best_bid_size', 0)
    best_ask_size = order_book.get('best_ask_size', 0)
    
    # 计算中间价
    mid_price = (best_bid + best_ask) / 2
    spread = best_ask - best_bid
    
    # 基础定价: 买价略低于最优买价，卖价略高于最优卖价
    # 价差通常在 1-5 cents 之间
    base_spread = max(spread * 1.2, 0.01)  # 至少 1 cent
    base_spread = min(base_spread, 0.05)   # 最多 5 cents
    
    # 根据订单簿深度调整
    bid_sum = order_book.get('bid_sum_within_n_percent', 1000)
    ask_sum = order_book.get('ask_sum_within_n_percent', 1000)
    
    # 流动性好的市场可以缩小价差
    liquidity_factor = min(bid_sum, ask_sum) / 1000
    if liquidity_factor > 1:
        base_spread *= 0.8  # 深度好，价差收窄
    elif liquidity_factor < 0.5:
        base_spread *= 1.3  # 深度差，价差扩大
    
    # 计算基础买卖价
    bid = best_bid - base_spread / 2
    ask = best_ask + base_spread / 2
    
    # 确保买价低于最优买价
    bid = min(bid, best_bid - tick_size)
    
    # 确保卖价高于最优卖价
    ask = max(ask, best_ask + tick_size)
    
    # 根据持仓调整
    if position_size > 0 and avg_price > 0:
        # 有盈利持仓，调整卖价考虑止盈
        if mid_price > avg_price:
            # 盈利状态，稍微积极卖出
            ask = max(ask, avg_price * 1.01)
        else:
            # 亏损状态，不轻易割肉
            ask = max(ask, avg_price * 0.98)
    
    # 按 tick_size 舍入
    bid = round_to_tick_size(bid, tick_size)
    ask = round_to_tick_size(ask, tick_size)
    
    # 边界检查
    bid = max(bid, 0.01)
    ask = min(ask, 0.99)
    
    # 确保买价 < 卖价
    if bid >= ask:
        bid = round_to_tick_size(ask - tick_size * 2, tick_size)
    
    return bid, ask


def calculate_bid_ask(
    mid_price: float,
    spread: float,
    tick_size: float = 0.01
) -> Tuple[float, float]:
    """
    根据中间价和价差计算买卖价
    
    Args:
        mid_price: 中间价
        spread: 价差
        tick_size: 最小价格单位
    
    Returns:
        (bid, ask) 元组
    """
    bid = mid_price - spread / 2
    ask = mid_price + spread / 2
    
    # 舍入
    bid = round_to_tick_size(bid, tick_size)
    ask = round_to_tick_size(ask, tick_size)
    
    return bid, ask


def calculate_spread(
    bid: float,
    ask: float
) -> float:
    """
    计算价差
    
    Args:
        bid: 买价
        ask: 卖价
    
    Returns:
        价差
    """
    return ask - bid


def is_valid_spread(
    spread: float,
    min_spread: float = 0.01,
    max_spread: float = 0.05
) -> bool:
    """
    检查价差是否在有效范围
    
    Args:
        spread: 价差
        min_spread: 最小价差
        max_spread: 最大价差
    
    Returns:
        是否有效
    """
    return min_spread <= spread <= max_spread


def calculate_order_size(
    order_book: Dict,
    base_size: int = 50,
    max_size: int = 250
) -> int:
    """
    根据订单簿深度计算订单大小
    
    Args:
        order_book: 订单簿数据
        base_size: 基础订单大小
        max_size: 最大订单大小
    
    Returns:
        订单大小
    """
    best_bid_size = order_book.get('best_bid_size', 100)
    best_ask_size = order_book.get('best_ask_size', 100)
    
    # 根据流动性调整
    min_liquidity = min(best_bid_size, best_ask_size)
    
    if min_liquidity >= 500:
        size = base_size
    elif min_liquidity >= 200:
        size = int(base_size * 0.7)
    elif min_liquidity >= 100:
        size = int(base_size * 0.5)
    else:
        size = int(base_size * 0.3)
    
    return min(size, max_size)


def should_adjust_for_imbalance(
    order_book: Dict,
    imbalance_threshold: float = 2.0
) -> Tuple[bool, str]:
    """
    检查订单簿是否失衡，需要调整定价
    
    Args:
        order_book: 订单簿数据
        imbalance_threshold: 失衡阈值
    
    Returns:
        (是否失衡, 失衡方向)
    """
    bid_sum = order_book.get('bid_sum_within_n_percent', 1000)
    ask_sum = order_book.get('ask_sum_within_n_percent', 1000)
    
    if bid_sum == 0 or ask_sum == 0:
        return True, "unknown"
    
    ratio = bid_sum / ask_sum
    
    if ratio > imbalance_threshold:
        return True, "buy_heavy"  # 买方占优
    elif ratio < 1 / imbalance_threshold:
        return True, "sell_heavy"  # 卖方占优
    
    return False, "balanced"


def adjust_for_imbalance(
    bid: float,
    ask: float,
    imbalance: str,
    adjustment_factor: float = 0.5
) -> Tuple[float, float]:
    """
    根据订单簿失衡调整定价
    
    Args:
        bid: 原始买价
        ask: 原始卖价
        imbalance: 失衡方向 ('buy_heavy' 或 'sell_heavy')
        adjustment_factor: 调整因子
    
    Returns:
        调整后的 (bid, ask)
    """
    mid = (bid + ask) / 2
    spread = ask - bid
    
    if imbalance == "buy_heavy":
        # 买方占优，偏向卖方定价（提高卖价）
        new_mid = mid + spread * adjustment_factor * 0.5
    elif imbalance == "sell_heavy":
        # 卖方占优，偏向买方定价（降低买价）
        new_mid = mid - spread * adjustment_factor * 0.5
    else:
        return bid, ask
    
    new_bid = new_mid - spread / 2
    new_ask = new_mid + spread / 2
    
    return new_bid, new_ask


def validate_order_book(order_book: Dict) -> Tuple[bool, str]:
    """
    验证订单簿数据有效性
    
    Args:
        order_book: 订单簿数据
    
    Returns:
        (是否有效, 错误信息)
    """
    if not order_book:
        return False, "Empty order book"
    
    best_bid = order_book.get('best_bid')
    best_ask = order_book.get('best_ask')
    
    if best_bid is None or best_ask is None:
        return False, "Missing bid or ask price"
    
    if best_bid <= 0 or best_ask <= 0:
        return False, "Invalid price values"
    
    if best_bid >= best_ask:
        return False, "Invalid spread (bid >= ask)"
    
    return True, "OK"


class OrderPricer:
    """订单定价器类"""
    
    def __init__(
        self,
        tick_size: float = 0.01,
        min_spread: float = 0.01,
        max_spread: float = 0.05,
    ):
        """
        初始化订单定价器
        
        Args:
            tick_size: 最小价格单位
            min_spread: 最小价差
            max_spread: 最大价差
        """
        self.tick_size = tick_size
        self.min_spread = min_spread
        self.max_spread = max_spread
    
    def get_prices(
        self,
        order_book: Dict,
        avg_price: float = 0,
        position_size: int = 0
    ) -> Tuple[float, float]:
        """
        获取买卖价格
        
        Args:
            order_book: 订单簿数据
            avg_price: 持仓均价
            position_size: 持仓数量
        
        Returns:
            (bid, ask) 元组
        """
        return get_order_prices(
            order_book,
            avg_price,
            position_size=position_size,
            tick_size=self.tick_size
        )
    
    def validate_spread(self, bid: float, ask: float) -> bool:
        """
        验证价差是否有效
        
        Args:
            bid: 买价
            ask: 卖价
        
        Returns:
            是否有效
        """
        spread = calculate_spread(bid, ask)
        return is_valid_spread(spread, self.min_spread, self.max_spread)
