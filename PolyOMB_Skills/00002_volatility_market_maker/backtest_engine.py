"""
00002 backtest_engine.py - 回测引擎模块

提供回测功能
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Callable
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
    action: str
    size: float
    price: float
    pnl: Optional[float] = None
    position_after: float = 0
    fee: float = 0.0


@dataclass
class BacktestResult:
    """回测结果"""
    trades: List[Trade] = field(default_factory=list)
    pnl_series: pd.Series = field(default_factory=pd.Series)
    total_pnl: float = 0.0
    total_return_pct: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown_pct: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'total_pnl': self.total_pnl,
            'total_return_pct': self.total_return_pct,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown_pct': self.max_drawdown_pct,
            'win_rate': self.win_rate,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
        }


class VolatilityMarketMakerStrategy:
    """
    波动率做市策略
    
    基于 poly-maker 核心算法
    """
    
    def __init__(self, config: Dict):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config
        
        # 持仓状态
        self.position = 0.0
        self.avg_price = 0.0
        self.cash = 0.0
        
        # 历史记录
        self.position_history: List[Dict] = []
        
        # 风险状态
        self.risk_off_until: Optional[datetime] = None
    
    def reset(self):
        """重置策略状态"""
        self.position = 0.0
        self.avg_price = 0.0
        self.cash = 0.0
        self.position_history = []
        self.risk_off_until = None
    
    def analyze(self, data: pd.DataFrame) -> Dict:
        """
        分析市场数据
        
        Args:
            data: 市场数据
            
        Returns:
            分析结果
        """
        volatility = data.get('3_hour', 0)
        price = data.get('price', 0.5)
        
        return {
            'volatility': volatility if pd.notna(volatility) else 0,
            'price': price,
        }
    
    def generate_signal(self, row: pd.Series) -> Signal:
        """
        生成交易信号
        
        Args:
            row: 当前市场数据行
            
        Returns:
            交易信号
        """
        from .risk_management import should_pause_trading, is_in_risk_off_period
        
        # 获取参数
        volatility = row.get('3_hour', 0)
        threshold = self.config.get('volatility_threshold', 0.15)
        
        # 处理 NaN
        if pd.isna(volatility):
            volatility = 0
        
        # 检查风险关闭期
        if self.risk_off_until and is_in_risk_off_period(self.risk_off_until):
            return Signal.HOLD
        
        # 高波动率时 Hold
        if should_pause_trading(volatility, threshold):
            return Signal.HOLD
        
        # 简化策略：根据持仓决定
        # 可以根据更复杂的逻辑扩展
        return Signal.HOLD
    
    def update_params(self, params: Dict):
        """
        更新策略参数
        
        Args:
            params: 新参数
        """
        self.config.update(params)
    
    def run_backtest(
        self,
        market_data: pd.DataFrame,
        time_preset: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> BacktestResult:
        """
        运行回测
        
        Args:
            market_data: 市场数据
            time_preset: 时间预设 ('lifecycle', 'full_year')
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果
        """
        from .data_adapter import (
            get_lifecycle_date_range,
            get_full_year_date_range,
            filter_by_date_range
        )
        
        # 重置状态
        self.reset()
        
        # 处理日期范围
        if time_preset == 'lifecycle':
            start_date, end_date = get_lifecycle_date_range(market_data)
        elif time_preset == 'full_year':
            start_date, end_date = get_full_year_date_range(market_data)
        
        # 过滤数据
        if start_date and end_date:
            data = filter_by_date_range(market_data, start_date, end_date)
        else:
            data = market_data.copy()
        
        if len(data) == 0:
            return BacktestResult()
        
        # 运行回测
        engine = BacktestEngine(self)
        result = engine.run(data)
        
        result.start_date = start_date
        result.end_date = end_date
        
        return result


class BacktestEngine:
    """
    回测引擎
    
    执行策略回测
    """
    
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
        self.trades: List[Trade] = []
        self.pnl_history: List[float] = []
    
    def step(self, row: pd.Series) -> Dict:
        """
        执行单步回测
        
        Args:
            row: 当前市场数据
            
        Returns:
            执行结果
        """
        signal = self.strategy.generate_signal(row)
        
        # 获取当前价格
        price = row.get('price', 0.5)
        timestamp = row.get('timestamp', datetime.now())
        if isinstance(timestamp, str):
            timestamp = pd.to_datetime(timestamp)
        
        trade_pnl = 0.0
        
        # 执行交易 (简化版本)
        if signal == Signal.BUY:
            # 执行买入
            pass
        elif signal == Signal.SELL:
            # 执行卖出，计算盈亏
            if self.strategy.position > 0 and self.strategy.avg_price > 0:
                trade_pnl = (price - self.strategy.avg_price) * self.strategy.position
        
        self.pnl_history.append(trade_pnl)
        
        return {
            'signal': signal.value,
            'pnl': trade_pnl,
            'price': price,
        }
    
    def run(self, data: pd.DataFrame) -> BacktestResult:
        """
        运行完整回测
        
        Args:
            data: 市场数据
            
        Returns:
            回测结果
        """
        trades = []
        pnls = []
        
        for _, row in data.iterrows():
            result = self.step(row)
            pnls.append(result.get('pnl', 0))
        
        # 构建结果
        result = BacktestResult()
        result.trades = trades
        result.pnl_series = pd.Series(pnls)
        result.total_pnl = sum(pnls)
        
        if self.initial_capital > 0:
            result.total_return_pct = (result.total_pnl / self.initial_capital) * 100
        
        # 计算统计指标
        if len(trades) > 0:
            result.total_trades = len(trades)
            winning = [t for t in trades if t.pnl and t.pnl > 0]
            losing = [t for t in trades if t.pnl and t.pnl < 0]
            result.winning_trades = len(winning)
            result.losing_trades = len(losing)
            result.win_rate = len(winning) / len(trades) if trades else 0
        
        if len(result.pnl_series) > 0:
            result.max_drawdown_pct = calculate_max_drawdown(result.pnl_series)
            result.sharpe_ratio = calculate_sharpe_ratio(result.pnl_series)
        
        return result


def calculate_sharpe_ratio(
    returns: pd.Series,
    risk_free_rate: float = 0.0
) -> float:
    """
    计算夏普比率
    
    公式: (mean(return) - risk_free_rate) / std(return)
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率
        
    Returns:
        夏普比率
    """
    if len(returns) < 2:
        return 0.0
    
    # 移除 NaN
    returns = returns.dropna()
    
    if len(returns) < 2 or returns.std() == 0:
        return 0.0
    
    return (returns.mean() - risk_free_rate) / returns.std()


def calculate_max_drawdown(pnl_series: pd.Series) -> float:
    """
    计算最大回撤
    
    基于累计盈亏计算最大回撤百分比
    
    Args:
        pnl_series: 盈亏序列 (每笔交易的盈亏)
        
    Returns:
        最大回撤百分比 (负数)
    """
    if len(pnl_series) == 0:
        return 0.0
    
    # 累计盈亏曲线
    cumulative = pnl_series.cumsum()
    
    # 历史最高值（到当前为止）
    running_max = cumulative.expanding().max()
    
    # 计算回撤百分比
    drawdown_pct = pd.Series(0.0, index=cumulative.index)
    
    for i in range(len(cumulative)):
        if running_max.iloc[i] > 0:
            drawdown_pct.iloc[i] = ((cumulative.iloc[i] - running_max.iloc[i]) / running_max.iloc[i]) * 100
    
    # 最大回撤 (最负的值)
    return drawdown_pct.min()


def calculate_win_rate(trades: List[Trade]) -> float:
    """
    计算胜率
    
    Args:
        trades: 交易列表
        
    Returns:
        胜率（0-1）
    """
    if len(trades) == 0:
        return 0.0
    
    winning_trades = [t for t in trades if t.pnl is not None and t.pnl > 0]
    return len(winning_trades) / len(trades)


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
    strategy: VolatilityMarketMakerStrategy,
    data: pd.DataFrame,
    initial_capital: float = 10000
) -> BacktestResult:
    """
    便捷回测函数
    
    Args:
        strategy: 策略实例
        data: 市场数据
        initial_capital: 初始资金
        
    Returns:
        回测结果
    """
    engine = BacktestEngine(strategy, initial_capital)
    return engine.run(data)
