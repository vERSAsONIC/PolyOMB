"""
策略名称: 基础模板
作者: your_username
描述: 这是一个策略模板，复制后修改内容创建新策略
"""

from polyomb.strategy import BaseStrategy
from polyomb.data import MarketData
from typing import Dict, Any


class BasicTemplateStrategy(BaseStrategy):
    """
    基础策略模板类
    
    继承 BaseStrategy 并实现必要的方法
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化策略
        
        Args:
            config: 策略配置参数
        """
        super().__init__(config)
        
        # 从配置中获取参数（带默认值）
        self.param1 = config.get("param1", 10)
        self.param2 = config.get("param2", 0.01)
    
    def on_init(self):
        """策略初始化时调用（订阅数据等）"""
        pass
    
    def on_data(self, data: MarketData):
        """
        接收市场数据时触发
        
        Args:
            data: 市场数据对象
        """
        # 在此实现策略逻辑
        pass
    
    def on_signal(self, signal: Dict[str, Any]):
        """
        生成交易信号
        
        Args:
            signal: 信号数据
            
        Returns:
            交易指令或 None
        """
        pass
    
    def on_order_update(self, order: Dict[str, Any]):
        """订单状态更新时触发"""
        pass
    
    def on_stop(self):
        """策略停止时调用（清理资源）"""
        pass
