#!/usr/bin/env python3
"""
00002 backtest_engine.py - 回测引擎模块

提供回测引擎、策略集成和结果验证功能
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, NamedTuple
from dataclasses import dataclass, field
from enum import Enum


class Signal(Enum):
    """交易信号枚举"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class Trade:
    """交易记录"""
    timestamp: datetime
    action: str  # 'BUY' or 'SELL'
    size: int
    price: float
    pnl: Optional[float] = None


@dataclass
class BacktestResult:
    """回测结果"""
    trades: List[Trade] = field(default_factory=list)
    pnl_series: pd.Series = field(default_factory=lambda: pd.Series(dtype=float))
    statistics: Dict = field(default_factory=dict)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_pnl: float = 0.0
    trade_count: int = 0


class VolatilityMarketMakerStrategy:
    """波动率做市策略"""
    
    def __init__(self, config: Dict):
        """
        初始化策略
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.position = 0
        self.avg_price = 0.0
        self.cash = 10000  # 初始资金
        self.trades = []
    
    def update_params(self, params: Dict):
        """更新策略参数"""
        self.config.update(params)
    
    def generate_signal(self, row: pd.Series) -> Signal:
        """
        生成交易信号
        
        Args:
            row: 当前数据行
        
        Returns:
            交易信号
        """
        # 简化的信号生成逻辑
        price = row.get('price', 0.5)
        volatility = row.get('3_hour', 0)
        
        # 高波动率时不交易
        if volatility > self.config.get('volatility_threshold', 0.15):
            return Signal.HOLD
        
        # 基于价格偏离均值产生信号
        if price < 0.45 and self.position < self.config.get('max_position_size', 250):
            return Signal.BUY
        elif price > 0.55 and self.position > 0:
            return Signal.SELL
        
        return Signal.HOLD
    
    def execute_signal(self, signal: Signal, row: pd.Series) -> Optional[Trade]:
        """
        执行交易信号
        
        Args:
            signal: 交易信号
            row: 当前数据行
        
        Returns:
            交易记录或 None
        """
        timestamp = row.get('timestamp', datetime.now())
        price = row.get('price', 0.5)
        trade_size = self.config.get('trade_size', 50)
        
        if signal == Signal.BUY:
            # 检查持仓限制
            if self.position + trade_size > self.config.get('max_position_size', 250):
                return None
            
            # 更新持仓均价
            total_cost = self.position * self.avg_price + trade_size * price
            self.position += trade_size
            self.avg_price = total_cost / self.position if self.position > 0 else 0
            
            trade = Trade(timestamp=timestamp, action='BUY', size=trade_size, price=price)
            self.trades.append(trade)
            return trade
        
        elif signal == Signal.SELL:
            # 检查持仓
            if self.position < trade_size:
                return None
            
            # 计算盈亏
            pnl = trade_size * (price - self.avg_price)
            
            self.position -= trade_size
            self.cash += trade_size * price
            
            trade = Trade(timestamp=timestamp, action='SELL', size=trade_size, price=price, pnl=pnl)
            self.trades.append(trade)
            return trade
        
        return None


class BacktestEngine:
    """回测引擎"""
    
    def __init__(
        self,
        strategy: VolatilityMarketMakerStrategy,
        initial_capital: float = 10000
    ):
        """
        初始化回测引擎
        
        Args:
            strategy: 策略实例
            initial_capital: 初始资金
        """
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.trades = []
        self.pnl_history = []
        self.timestamps = []
    
    def step(self, row: pd.Series) -> Dict:
        """
        执行单步回测
        
        Args:
            row: 当前数据行
        
        Returns:
            步骤结果
        """
        # 生成信号
        signal = self.strategy.generate_signal(row)
        
        # 执行信号
        trade = self.strategy.execute_signal(signal, row)
        
        # 记录 PnL
        current_pnl = self.calculate_current_pnl(row.get('price', 0.5))
        self.pnl_history.append(current_pnl)
        self.timestamps.append(row.get('timestamp', datetime.now()))
        
        if trade:
            self.trades.append(trade)
        
        return {
            'signal': signal.value,
            'trade': trade,
            'pnl': current_pnl,
        }
    
    def run(self, data: pd.DataFrame) -> BacktestResult:
        """
        运行完整回测
        
        Args:
            data: 历史数据
        
        Returns:
            回测结果
        """
        if data.empty:
            raise ValueError("Empty market data")
        
        if len(data) < 10:
            raise ValueError("Insufficient data")
        
        # 遍历数据
        for _, row in data.iterrows():
            self.step(row)
        
        # 计算统计指标
        total_pnl = sum(t.pnl for t in self.trades if t.pnl is not None)
        
        # 创建 PnL 序列
        pnl_series = pd.Series(
            self.pnl_history,
            index=pd.DatetimeIndex(self.timestamps)
        ) if self.pnl_history else pd.Series(dtype=float)
        
        # 计算统计指标
        statistics = self.calculate_statistics(pnl_series)
        
        return BacktestResult(
            trades=self.trades,
            pnl_series=pnl_series,
            statistics=statistics,
            start_date=data['timestamp'].min() if 'timestamp' in data.columns else None,
            end_date=data['timestamp'].max() if 'timestamp' in data.columns else None,
            total_pnl=total_pnl,
            trade_count=len(self.trades),
        )
    
    def calculate_current_pnl(self, current_price: float) -> float:
        """
        计算当前盈亏
        
        Args:
            current_price: 当前价格
        
        Returns:
            盈亏金额
        """
        position_value = self.strategy.position * current_price
        unrealized_pnl = position_value - (self.strategy.position * self.strategy.avg_price)
        
        realized_pnl = sum(t.pnl for t in self.trades if t.pnl is not None)
        
        return realized_pnl + unrealized_pnl
    
    def calculate_statistics(self, pnl_series: pd.Series) -> Dict:
        """
        计算回测统计指标
        
        Args:
            pnl_series: PnL 序列
        
        Returns:
            统计指标字典
        """
        if pnl_series.empty:
            return {
                'sharpe_ratio': 0,
                'max_drawdown': 0,
                'win_rate': 0,
            }
        
        # 计算收益率
        returns = pnl_series.diff().dropna()
        
        # 夏普比率
        sharpe = calculate_sharpe_ratio(returns) if len(returns) > 1 else 0
        
        # 最大回撤
        max_dd = calculate_max_drawdown(pnl_series)
        
        # 胜率
        win_rate = calculate_win_rate(self.trades)
        
        return {
            'sharpe_ratio': sharpe,
            'max_drawdown': max_dd,
            'win_rate': win_rate,
        }


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0,
    periods_per_year: int = 252
) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率
        periods_per_year: 每年交易周期数
    
    Returns:
        夏普比率
    """
    if returns.empty or returns.std() == 0:
        return 0.0
    
    excess_returns = returns - risk_free_rate
    sharpe = excess_returns.mean() / returns.std() * np.sqrt(periods_per_year)
    
    return float(sharpe)


def calculate_max_drawdown(pnl_series: pd.Series) -> float:
    """
    计算最大回撤
    
    Args:
        pnl_series: PnL 序列
    
    Returns:
        最大回撤（负数）
    """
    if pnl_series.empty:
        return 0.0
    
    # 计算累计最大值
    rolling_max = pnl_series.cummax()
    
    # 计算回撤
    drawdown = pnl_series - rolling_max
    
    # 最大回撤
    max_drawdown = drawdown.min()
    
    return float(max_drawdown)


def calculate_win_rate(trades: List[Trade]) -> float:
    """
    计算胜率
    
    Args:
        trades: 交易列表
    
    Returns:
        胜率 (0-1)
    """
    completed_trades = [t for t in trades if t.pnl is not None]
    
    if not completed_trades:
        return 0.0
    
    winning_trades = [t for t in completed_trades if t.pnl > 0]
    
    return len(winning_trades) / len(completed_trades)


def calculate_pnl_from_trades(trades: List[Trade]) -> float:
    """
    从交易列表计算总盈亏
    
    Args:
        trades: 交易列表
    
    Returns:
        总盈亏
    """
    return sum(t.pnl for t in trades if t.pnl is not None)


def run_backtest(
    data: pd.DataFrame,
    config: Dict,
    initial_capital: float = 10000
) -> BacktestResult:
    """
    便捷函数：运行回测
    
    Args:
        data: 历史数据
        config: 策略配置
        initial_capital: 初始资金
    
    Returns:
        回测结果
    """
    strategy = VolatilityMarketMakerStrategy(config)
    engine = BacktestEngine(strategy, initial_capital)
    return engine.run(data)
