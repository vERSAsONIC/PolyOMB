#!/usr/bin/env python3
"""
00002 risk_management.py - 风险管理模块

提供止损、止盈、风控等核心功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, NamedTuple
from enum import Enum


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class RiskCheckResult(NamedTuple):
    """风险检查结果"""
    can_trade: bool
    risk_level: RiskLevel
    messages: list


def should_trigger_stop_loss(
    pnl: float,
    spread: float,
    stop_loss_threshold: float,
    spread_threshold: float
) -> bool:
    """
    判断是否触发止损
    
    Args:
        pnl: 当前盈亏百分比
        spread: 当前价差
        stop_loss_threshold: 止损阈值（负数，如 -5.0 表示亏损 5%）
        spread_threshold: 价差阈值
    
    Returns:
        是否触发止损
    """
    # 条件1: 亏损达到阈值
    loss_triggered = pnl <= stop_loss_threshold
    
    # 条件2: 价差在可接受范围（避免高价差时止损导致滑点损失）
    spread_acceptable = spread <= spread_threshold
    
    return loss_triggered and spread_acceptable


def calculate_take_profit_price(avg_price: float, take_profit_threshold: float) -> float:
    """
    计算止盈价格
    
    Args:
        avg_price: 持仓均价
        take_profit_threshold: 止盈阈值（百分比，如 3.0 表示 3%）
    
    Returns:
        止盈价格
    """
    return avg_price * (1 + take_profit_threshold / 100)


def adjust_ask_for_take_profit(
    current_ask: float,
    avg_price: float,
    take_profit_threshold: float
) -> float:
    """
    根据止盈目标调整卖价
    
    Args:
        current_ask: 当前卖价
        avg_price: 持仓均价
        take_profit_threshold: 止盈阈值
    
    Returns:
        调整后的卖价
    """
    tp_price = calculate_take_profit_price(avg_price, take_profit_threshold)
    # 取较高者，确保达到止盈目标
    return max(current_ask, tp_price)


def should_pause_trading(volatility: float, threshold: float) -> bool:
    """
    根据波动率判断是否暂停交易
    
    Args:
        volatility: 当前波动率
        threshold: 波动率阈值
    
    Returns:
        是否应暂停交易
    """
    return volatility >= threshold


def can_open_new_position(
    volatility: float,
    volatility_threshold: float,
    has_position: bool = False
) -> bool:
    """
    判断是否允许开新仓
    
    Args:
        volatility: 当前波动率
        volatility_threshold: 波动率阈值
        has_position: 是否已有持仓
    
    Returns:
        是否允许开新仓
    """
    # 高波动率时不开新仓
    if volatility >= volatility_threshold:
        return False
    return True


def can_close_position(
    volatility: float,
    has_position: bool = True
) -> bool:
    """
    判断是否允许平仓
    
    即使在高波动率下，也应允许平仓（止损/止盈）
    
    Args:
        volatility: 当前波动率
        has_position: 是否已有持仓
    
    Returns:
        是否允许平仓
    """
    # 有持仓时总是允许平仓（风险控制优先）
    return has_position


def can_increase_position(
    current_position: int,
    max_position_size: int
) -> bool:
    """
    判断是否允许增加持仓
    
    Args:
        current_position: 当前持仓数量
        max_position_size: 最大持仓限制
    
    Returns:
        是否允许增加持仓
    """
    return current_position < max_position_size


def can_buy_no(yes_position: int, no_position: int, max_position_size: int = 250) -> bool:
    """
    判断是否允许买入 NO（考虑反向持仓）
    
    如果持有大量 YES，不应买更多 NO（应先合并或平仓）
    
    Args:
        yes_position: YES 持仓数量
        no_position: NO 持仓数量
        max_position_size: 最大持仓限制
    
    Returns:
        是否允许买入 NO
    """
    # 如果持有 YES 仓位，限制 NO 仓位增加
    if yes_position > 10 and no_position > 0:
        return False
    
    # 检查是否超过总持仓限制
    if yes_position + no_position >= max_position_size:
        return False
    
    return True


def is_valid_trade_size(proposed_size: int, min_size: int) -> bool:
    """
    检查交易数量是否有效
    
    Args:
        proposed_size: 提议的交易数量
        min_size: 最小交易数量
    
    Returns:
        是否有效
    """
    return proposed_size >= min_size


def is_in_risk_off_period(sleep_until: datetime) -> bool:
    """
    检查是否在风险关闭期内
    
    Args:
        sleep_until: 风险关闭期结束时间
    
    Returns:
        是否在风险关闭期内
    """
    return datetime.now() < sleep_until


def calculate_risk_off_end_time(trigger_time: datetime, sleep_period: int) -> datetime:
    """
    计算风险关闭期结束时间
    
    Args:
        trigger_time: 触发时间
        sleep_period: 关闭期小时数
    
    Returns:
        结束时间
    """
    return trigger_time + timedelta(hours=sleep_period)


def is_valid_buy_price(price: float, min_price: float = 0.1, max_price: float = 0.9) -> bool:
    """
    检查买单价格是否有效
    
    poly-maker 限制: 0.1 <= price < 0.9
    
    Args:
        price: 提议的价格
        min_price: 最低价格
        max_price: 最高价格
    
    Returns:
        是否有效
    """
    return min_price <= price < max_price


def is_valid_sell_price(price: float, min_price: float = 0.1, max_price: float = 0.9) -> bool:
    """
    检查卖单价格是否有效
    
    Args:
        price: 提议的价格
        min_price: 最低价格
        max_price: 最高价格
    
    Returns:
        是否有效
    """
    return min_price < price <= max_price


def check_price_deviation(
    current_price: float,
    reference_price: float,
    threshold: float
) -> bool:
    """
    检查价格偏离是否超过阈值
    
    Args:
        current_price: 当前价格
        reference_price: 参考价格
        threshold: 偏离阈值
    
    Returns:
        是否超过阈值
    """
    deviation = abs(current_price - reference_price)
    return deviation > threshold


def comprehensive_risk_check(
    pnl: float,
    spread: float,
    volatility_3h: float,
    position_size: int,
    max_position: int,
    in_risk_off_period: bool,
    stop_loss_threshold: float = -5.0,
    spread_threshold: float = 0.02,
    volatility_threshold: float = 0.15,
) -> RiskCheckResult:
    """
    综合风险检查
    
    Args:
        pnl: 当前盈亏百分比
        spread: 当前价差
        volatility_3h: 3小时波动率
        position_size: 当前持仓数量
        max_position: 最大持仓限制
        in_risk_off_period: 是否在风险关闭期
        stop_loss_threshold: 止损阈值
        spread_threshold: 价差阈值
        volatility_threshold: 波动率阈值
    
    Returns:
        风险检查结果
    """
    messages = []
    
    # 1. 检查止损（最高优先级）
    if pnl <= stop_loss_threshold:
        if spread <= spread_threshold:
            messages.append(f"CRITICAL: Stop loss triggered at {pnl:.2f}%")
            return RiskCheckResult(
                can_trade=False,
                risk_level=RiskLevel.CRITICAL,
                messages=messages
            )
        else:
            messages.append(f"WARNING: Stop loss condition met but spread too high ({spread:.4f})")
    
    # 2. 检查风险关闭期
    if in_risk_off_period:
        messages.append("HIGH: In risk-off period")
        return RiskCheckResult(
            can_trade=False,
            risk_level=RiskLevel.HIGH,
            messages=messages
        )
    
    # 3. 检查波动率
    if volatility_3h >= volatility_threshold:
        messages.append(f"MEDIUM: High volatility detected ({volatility_3h:.4f})")
        # 高波动率不禁止交易，但标记为中风险
        return RiskCheckResult(
            can_trade=True,
            risk_level=RiskLevel.MEDIUM,
            messages=messages
        )
    
    # 4. 检查持仓限制
    if position_size >= max_position:
        messages.append(f"MEDIUM: Position at max limit ({position_size})")
        return RiskCheckResult(
            can_trade=False,  # 禁止开新仓
            risk_level=RiskLevel.MEDIUM,
            messages=messages
        )
    
    # 低风险
    messages.append("LOW: All risk checks passed")
    return RiskCheckResult(
        can_trade=True,
        risk_level=RiskLevel.LOW,
        messages=messages
    )


class RiskManager:
    """风险管理器类"""
    
    def __init__(self, config: Dict):
        """
        初始化风险管理器
        
        Args:
            config: 配置字典，包含各种阈值
        """
        self.config = config
        self.risk_off_until = None
        self.last_stop_loss_triggered = None
    
    def trigger_stop_loss(self):
        """触发止损，进入风险关闭期"""
        self.last_stop_loss_triggered = datetime.now()
        sleep_period = self.config.get("sleep_period", 6)
        self.risk_off_until = calculate_risk_off_end_time(
            self.last_stop_loss_triggered, 
            sleep_period
        )
    
    def is_in_risk_off_period(self) -> bool:
        """检查是否在风险关闭期内"""
        if self.risk_off_until is None:
            return False
        return datetime.now() < self.risk_off_until
    
    def clear_risk_off_period(self):
        """清除风险关闭期"""
        self.risk_off_until = None
    
    def check_risk(
        self,
        pnl: float,
        spread: float,
        volatility_3h: float,
        position_size: int
    ) -> RiskCheckResult:
        """
        执行风险检查
        
        Args:
            pnl: 当前盈亏
            spread: 当前价差
            volatility_3h: 3小时波动率
            position_size: 当前持仓
        
        Returns:
            风险检查结果
        """
        return comprehensive_risk_check(
            pnl=pnl,
            spread=spread,
            volatility_3h=volatility_3h,
            position_size=position_size,
            max_position=self.config.get("max_position_size", 250),
            in_risk_off_period=self.is_in_risk_off_period(),
            stop_loss_threshold=self.config.get("stop_loss_threshold", -5.0),
            spread_threshold=self.config.get("spread_threshold", 0.02),
            volatility_threshold=self.config.get("volatility_threshold", 0.15),
        )
