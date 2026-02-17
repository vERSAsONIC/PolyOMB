"""
00002 risk_management.py - 风险管理模块

提供风险管理功能，包括止损、止盈、风控等
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Optional, List


class RiskLevel(Enum):
    """风险等级枚举"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


def should_trigger_stop_loss(
    pnl: float,
    spread: float,
    stop_loss_threshold: float = -5.0,
    spread_threshold: float = 0.02
) -> bool:
    """
    检查是否应该触发止损
    
    条件:
    1. PnL 低于止损阈值
    2. 价差足够小，可以合理退出
    
    Args:
        pnl: 盈亏百分比
        spread: 当前价差
        stop_loss_threshold: 止损阈值 (负数)
        spread_threshold: 价差阈值
        
    Returns:
        True 如果应触发止损
    """
    # PnL 必须低于阈值 (更负)
    pnl_condition = pnl <= stop_loss_threshold
    
    # 价差必须足够小 (避免在流动性差时止损)
    spread_condition = spread <= spread_threshold
    
    return pnl_condition and spread_condition


def calculate_take_profit_price(
    avg_price: float,
    take_profit_threshold: float = 3.0
) -> float:
    """
    计算止盈价格
    
    公式: avg_price * (1 + take_profit_threshold / 100)
    
    Args:
        avg_price: 持仓均价
        take_profit_threshold: 止盈百分比
        
    Returns:
        止盈价格
    """
    if avg_price <= 0:
        return 0.0
    
    return avg_price * (1 + take_profit_threshold / 100)


def adjust_ask_for_take_profit(
    current_ask: float,
    avg_price: float,
    take_profit_threshold: float = 3.0
) -> float:
    """
    根据止盈调整卖价
    
    策略: 取 max(current_ask, tp_price)
    
    Args:
        current_ask: 当前卖价
        avg_price: 持仓均价
        take_profit_threshold: 止盈百分比
        
    Returns:
        调整后的卖价
    """
    if avg_price <= 0:
        return current_ask
    
    tp_price = calculate_take_profit_price(avg_price, take_profit_threshold)
    
    # 确保卖价不低于止盈价
    return max(current_ask, tp_price)


def should_pause_trading(
    volatility: float,
    threshold: float = 0.15
) -> bool:
    """
    检查是否应该因波动率暂停交易
    
    保守策略: volatility >= threshold 时暂停开新仓
    
    Args:
        volatility: 当前波动率
        threshold: 波动率阈值
        
    Returns:
        True 如果应暂停
    """
    import pandas as pd
    
    # 处理 NaN
    if volatility is None or (isinstance(volatility, float) and __import__('math').isnan(volatility)):
        return False
    
    return volatility >= threshold


def can_open_new_position(
    volatility: float,
    threshold: float = 0.15,
    in_risk_off: bool = False
) -> bool:
    """
    检查是否可以开新仓
    
    条件:
    1. 不在风险关闭期
    2. 波动率低于阈值
    
    Args:
        volatility: 当前波动率
        threshold: 波动率阈值
        in_risk_off: 是否在风险关闭期
        
    Returns:
        True 如果可以开新仓
    """
    # 风险关闭期禁止开新仓
    if in_risk_off:
        return False
    
    # 高波动率禁止开新仓
    return volatility < threshold


def can_close_position(volatility: float) -> bool:
    """
    检查是否可以平仓
    
    平仓(止损/止盈)不受波动率限制，总是允许
    
    Args:
        volatility: 当前波动率 (未使用，但保留接口)
        
    Returns:
        True 总是可以平仓
    """
    return True


def can_increase_position(
    current_position: float,
    max_position: float = 250
) -> bool:
    """
    检查是否可以增加持仓
    
    Args:
        current_position: 当前持仓 (绝对值)
        max_position: 最大持仓限制
        
    Returns:
        True 如果可以增加
    """
    return abs(current_position) < max_position


def can_buy_no(
    no_position: float,
    yes_position: float,
    min_size: float = 5.0
) -> bool:
    """
    检查是否可以买入 NO
    
    策略: 如果 YES 持仓较大，不应增加 NO 持仓 (避免对冲)
    
    Args:
        no_position: NO 持仓
        yes_position: YES 持仓
        min_size: 最小持仓阈值
        
    Returns:
        True 如果可以买入 NO
    """
    # 如果 YES 持仓较大，不应增加 NO 持仓
    if yes_position > min_size:
        return False
    
    return True


def is_valid_trade_size(
    size: float,
    min_size: float = 5.0
) -> bool:
    """
    检查交易数量是否有效
    
    Args:
        size: 交易数量
        min_size: 最小数量
        
    Returns:
        True 如果有效
    """
    return size >= min_size


def is_in_risk_off_period(sleep_until: Optional[datetime]) -> bool:
    """
    检查是否在风险关闭期
    
    Args:
        sleep_until: 风险关闭结束时间
        
    Returns:
        True 如果在关闭期
    """
    if sleep_until is None:
        return False
    
    return datetime.now() < sleep_until


def calculate_risk_off_end_time(
    triggered_at: datetime,
    sleep_period: int = 6
) -> datetime:
    """
    计算风险关闭结束时间
    
    Args:
        triggered_at: 触发时间
        sleep_period: 关闭小时数
        
    Returns:
        结束时间
    """
    return triggered_at + timedelta(hours=sleep_period)


def is_valid_buy_price(price: float) -> bool:
    """
    检查买价是否在有效范围
    
    poly-maker 限制: 0.1 <= price < 0.9
    
    Args:
        price: 买价
        
    Returns:
        True 如果在 [0.1, 0.9) 范围
    """
    return 0.1 <= price < 0.9


def is_valid_sell_price(price: float) -> bool:
    """
    检查卖价是否在有效范围
    
    poly-maker 限制: 0.1 < price <= 0.9
    
    Args:
        price: 卖价
        
    Returns:
        True 如果在 (0.1, 0.9] 范围
    """
    return 0.1 < price <= 0.9


def check_price_deviation(
    current_price: float,
    reference_price: float,
    threshold: float = 0.05
) -> bool:
    """
    检查价格偏离是否超过阈值
    
    Args:
        current_price: 当前价格
        reference_price: 参考价格
        threshold: 偏离阈值
        
    Returns:
        True 如果偏离超过阈值
    """
    if reference_price == 0:
        return False
    
    deviation = abs(current_price - reference_price) / reference_price
    return deviation >= threshold


def comprehensive_risk_check(risk_context: Dict) -> Dict:
    """
    综合风险检查
    
    整合多种风险因素，返回综合评估结果
    
    Args:
        risk_context: 风险上下文，包含:
            - pnl: 盈亏百分比
            - spread: 当前价差
            - volatility_3h: 3小时波动率
            - position_size: 持仓数量
            - max_position: 最大持仓
            - in_risk_off_period: 是否在风险关闭期
            
    Returns:
        风险检查结果，包含:
            - can_trade: 是否可以交易
            - risk_level: 风险等级
            - warnings: 警告信息列表
            - should_stop_loss: 是否应该止损
    """
    pnl = risk_context.get('pnl', 0)
    spread = risk_context.get('spread', 0)
    volatility = risk_context.get('volatility_3h', 0)
    position_size = risk_context.get('position_size', 0)
    max_position = risk_context.get('max_position', 250)
    in_risk_off = risk_context.get('in_risk_off_period', False)
    
    result = {
        'can_trade': True,
        'risk_level': RiskLevel.LOW,
        'warnings': [],
        'should_stop_loss': False
    }
    
    # 1. 检查止损 (最高优先级)
    stop_loss_threshold = risk_context.get('stop_loss_threshold', -5.0)
    spread_threshold = risk_context.get('spread_threshold', 0.02)
    
    if pnl <= stop_loss_threshold and spread <= spread_threshold:
        result['can_trade'] = False
        result['risk_level'] = RiskLevel.CRITICAL
        result['should_stop_loss'] = True
        result['warnings'].append('Stop loss triggered')
        return result
    
    # 2. 检查波动率
    volatility_threshold = risk_context.get('volatility_threshold', 0.15)
    
    if volatility >= volatility_threshold * 1.5:
        result['risk_level'] = RiskLevel.CRITICAL
        result['warnings'].append('Extreme volatility')
    elif volatility >= volatility_threshold:
        result['risk_level'] = RiskLevel.HIGH
        result['warnings'].append('High volatility')
    
    # 3. 检查风险关闭期
    if in_risk_off:
        result['can_trade'] = False
        result['risk_level'] = RiskLevel.HIGH
        result['warnings'].append('In risk-off period')
    
    # 4. 检查持仓限制
    if abs(position_size) >= max_position:
        result['can_trade'] = False
        result['risk_level'] = RiskLevel.MEDIUM
        result['warnings'].append('Max position reached')
    elif abs(position_size) >= max_position * 0.9:
        result['risk_level'] = max(result['risk_level'], RiskLevel.MEDIUM)
        result['warnings'].append('Near max position')
    
    return result


class RiskManager:
    """
    风险管理器类
    
    封装风险管理逻辑，维护风险状态
    """
    
    def __init__(
        self,
        stop_loss_threshold: float = -5.0,
        take_profit_threshold: float = 3.0,
        volatility_threshold: float = 0.15,
        max_position: float = 250,
        sleep_period: int = 6
    ):
        """
        初始化风险管理者
        
        Args:
            stop_loss_threshold: 止损阈值
            take_profit_threshold: 止盈阈值
            volatility_threshold: 波动率阈值
            max_position: 最大持仓
            sleep_period: 风险关闭期（小时）
        """
        self.stop_loss_threshold = stop_loss_threshold
        self.take_profit_threshold = take_profit_threshold
        self.volatility_threshold = volatility_threshold
        self.max_position = max_position
        self.sleep_period = sleep_period
        
        self.risk_off_until: Optional[datetime] = None
        self.last_check: Optional[datetime] = None
        self.warning_history: List[str] = []
    
    def check_position_risk(
        self,
        position: float,
        avg_price: float,
        current_price: float
    ) -> RiskLevel:
        """
        检查持仓风险
        
        Args:
            position: 持仓数量
            avg_price: 持仓均价
            current_price: 当前价格
            
        Returns:
            风险等级
        """
        if position == 0 or avg_price == 0:
            return RiskLevel.LOW
        
        # 计算盈亏
        pnl = (current_price - avg_price) / avg_price * 100
        
        # 严重亏损
        if pnl <= self.stop_loss_threshold:
            return RiskLevel.CRITICAL
        
        # 接近止损
        if pnl <= self.stop_loss_threshold * 0.7:
            return RiskLevel.HIGH
        
        # 持仓接近上限
        if abs(position) >= self.max_position * 0.9:
            return RiskLevel.HIGH
        elif abs(position) >= self.max_position * 0.7:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def check_market_risk(self, volatility: float) -> RiskLevel:
        """
        检查市场风险
        
        Args:
            volatility: 波动率
            
        Returns:
            风险等级
        """
        if volatility >= self.volatility_threshold * 1.5:
            return RiskLevel.CRITICAL
        elif volatility >= self.volatility_threshold:
            return RiskLevel.HIGH
        elif volatility >= self.volatility_threshold * 0.5:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def trigger_risk_off(self):
        """触发风险关闭期"""
        self.risk_off_until = calculate_risk_off_end_time(
            datetime.now(),
            self.sleep_period
        )
    
    def is_in_risk_off(self) -> bool:
        """检查是否在风险关闭期"""
        return is_in_risk_off_period(self.risk_off_until)
    
    def clear_risk_off(self):
        """清除风险关闭期"""
        self.risk_off_until = None
