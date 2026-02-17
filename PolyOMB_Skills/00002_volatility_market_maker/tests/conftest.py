"""
00002 conftest.py - Pytest 共享 Fixtures

提供测试数据、Mock 对象和共享资源
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os
import sys

# 添加父目录到路径以导入被测模块
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# =============================================================================
# 测试配置
# =============================================================================

TEST_MARKET_ID = "0x218919622a6132646d149021008659d834927b2b81005a92a54b38d781b0a56f"
TEST_CONFIG = {
    "stop_loss_threshold": -5.0,
    "take_profit_threshold": 3.0,
    "volatility_threshold": 0.15,
    "max_position_size": 250,
    "trade_size": 50,
    "min_size": 5,
    "spread_threshold": 0.02,
    "sleep_period": 6,  # hours
}

SMB_PATH = "smb://MM2018._smb._tcp.local/liuqiong/prediction-market-analysis/data"


# =============================================================================
# Mock 数据 Fixtures
# =============================================================================

@pytest.fixture
def sample_market_metadata() -> Dict:
    """
    示例市场元数据
    
    模拟 prediction-market-analysis 中 markets.parquet 的单条记录
    """
    return {
        "condition_id": TEST_MARKET_ID,
        "question": "Will Donald Trump win the 2024 US Presidential Election?",
        "description": "This market will resolve to Yes if Donald Trump wins...",
        "category": "Politics",
        "subcategory": "US Elections",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 11, 5),
        "resolution_date": datetime(2024, 11, 6),
        "token1": "0x123...",
        "token2": "0x456...",
        "answer1": "Yes",
        "answer2": "No",
        "tick_size": 0.01,
        "neg_risk": False,
        "min_order_size": 1,
    }


@pytest.fixture
def sample_trades_1k() -> pd.DataFrame:
    """
    生成 1000 条模拟交易数据
    
    模拟 prediction-market-analysis 中 trades.parquet 的结构
    小型数据集用于快速测试
    """
    np.random.seed(42)  # 可复现
    
    n = 1000
    start_time = datetime(2024, 1, 1)
    
    # 生成时间序列（每小时多条交易）
    timestamps = [start_time + timedelta(minutes=i*10) for i in range(n)]
    
    # 生成价格（基于正弦波 + 随机游走，模拟真实市场）
    base_price = 0.5
    price_trend = np.sin(np.linspace(0, 4*np.pi, n)) * 0.1  # 波动
    price_noise = np.random.normal(0, 0.02, n)  # 噪音
    prices = base_price + price_trend + price_noise
    prices = np.clip(prices, 0.01, 0.99)  # 限制在有效范围
    
    # 生成交易量
    volumes = np.random.randint(10, 500, n)
    
    # 生成买卖方向
    sides = np.random.choice(["BUY", "SELL"], n, p=[0.55, 0.45])
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "market": [TEST_MARKET_ID] * n,
        "asset_id": np.where(sides == "BUY", "token_yes", "token_no"),
        "side": sides,
        "price": np.round(prices, 4),
        "size": volumes,
        "transaction_hash": [f"0x{np.random.randint(10**16, 10**17)}" for _ in range(n)],
    })
    
    return df


@pytest.fixture
def sample_orderbook_snapshots() -> pd.DataFrame:
    """
    生成模拟订单簿快照数据
    
    用于测试订单定价逻辑
    """
    np.random.seed(42)
    
    n = 100
    timestamps = [datetime(2024, 1, 1) + timedelta(minutes=i*30) for i in range(n)]
    
    # 生成中心价格
    mid_prices = 0.5 + np.sin(np.linspace(0, 2*np.pi, n)) * 0.1
    
    data = []
    for i, ts in enumerate(timestamps):
        mid = mid_prices[i]
        spread = np.random.uniform(0.01, 0.03)
        
        data.append({
            "timestamp": ts,
            "best_bid": round(mid - spread/2, 4),
            "best_bid_size": np.random.randint(50, 200),
            "second_best_bid": round(mid - spread/2 - 0.01, 4),
            "second_best_bid_size": np.random.randint(30, 150),
            "top_bid": round(mid - spread/2 - np.random.uniform(0.01, 0.05), 4),
            "best_ask": round(mid + spread/2, 4),
            "best_ask_size": np.random.randint(50, 200),
            "second_best_ask": round(mid + spread/2 + 0.01, 4),
            "second_best_ask_size": np.random.randint(30, 150),
            "top_ask": round(mid + spread/2 + np.random.uniform(0.01, 0.05), 4),
            "bid_sum_within_n_percent": np.random.uniform(500, 2000),
            "ask_sum_within_n_percent": np.random.uniform(500, 2000),
        })
    
    return pd.DataFrame(data)


@pytest.fixture
def mock_smb_adapter(mocker):
    """
    Mock SMB 数据适配器
    
    用于单元测试，避免实际网络连接
    """
    class MockSMBAdapter:
        def __init__(self, smb_url: str, mount_point: str = "/tmp/test-mount"):
            self.smb_url = smb_url
            self.mount_point = mount_point
            self._is_mounted = True
            self._mock_data = {}
        
        def mount(self):
            """模拟挂载"""
            self._is_mounted = True
            return True
        
        def unmount(self):
            """模拟卸载"""
            self._is_mounted = False
            return True
        
        def read_parquet(self, relative_path: str) -> pd.DataFrame:
            """模拟读取 Parquet"""
            # 返回模拟数据
            return self._mock_data.get(relative_path, pd.DataFrame())
        
        def set_mock_data(self, path: str, df: pd.DataFrame):
            """设置模拟数据"""
            self._mock_data[path] = df
        
        def get_market_trades(self, market_id: str) -> pd.DataFrame:
            """获取市场交易数据"""
            return self._mock_data.get("trades", pd.DataFrame())
        
        def get_market_metadata(self, market_id: str) -> Dict:
            """获取市场元数据"""
            return {
                "condition_id": market_id,
                "question": "Mock Question",
                "category": "Test",
            }
    
    return MockSMBAdapter


@pytest.fixture
def sample_position_history() -> pd.DataFrame:
    """
    生成模拟持仓历史
    
    用于测试策略执行和 PnL 计算
    """
    np.random.seed(42)
    
    trades = []
    position = 0
    avg_price = 0
    cash = 10000  # 初始资金
    
    timestamps = [datetime(2024, 1, 1) + timedelta(hours=i) for i in range(100)]
    
    for ts in timestamps:
        action = np.random.choice(["BUY", "SELL", "HOLD"], p=[0.3, 0.2, 0.5])
        
        if action == "BUY" and cash > 100:
            size = np.random.randint(10, 50)
            price = np.random.uniform(0.45, 0.55)
            cost = size * price
            if cost <= cash:
                # 更新均价
                total_cost = position * avg_price + cost
                position += size
                avg_price = total_cost / position if position > 0 else 0
                cash -= cost
                
                trades.append({
                    "timestamp": ts,
                    "action": "BUY",
                    "size": size,
                    "price": price,
                    "position": position,
                    "avg_price": avg_price,
                    "cash": cash,
                })
        
        elif action == "SELL" and position > 10:
            size = min(np.random.randint(10, 30), position)
            price = np.random.uniform(0.45, 0.55)
            revenue = size * price
            
            # 计算 PnL
            cost_basis = size * avg_price
            pnl = revenue - cost_basis
            
            position -= size
            cash += revenue
            
            trades.append({
                "timestamp": ts,
                "action": "SELL",
                "size": size,
                "price": price,
                "pnl": pnl,
                "position": position,
                "avg_price": avg_price,
                "cash": cash,
            })
    
    return pd.DataFrame(trades)


# =============================================================================
# 配置 Fixtures
# =============================================================================

@pytest.fixture
def default_skill_config() -> Dict:
    """默认 Skill 配置"""
    return TEST_CONFIG.copy()


@pytest.fixture
def mock_environment_vars(monkeypatch):
    """设置测试环境变量"""
    env_vars = {
        "POLYOMB_DATA_PATH": "/tmp/test-data",
        "SMB_MOUNT_POINT": "/tmp/test-smb-mount",
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars


# =============================================================================
# Pytest 配置
# =============================================================================

def pytest_configure(config):
    """Pytest 全局配置"""
    config.addinivalue_line(
        "markers", "smb: marks tests that require SMB connection (skipped by default)"
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m not slow')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试项 - 默认跳过需要 SMB 的测试"""
    skip_smb = pytest.mark.skip(reason="需要 SMB 连接，使用 --run-smb 启用")
    
    for item in items:
        if "smb" in item.keywords and not config.getoption("--run-smb"):
            item.add_marker(skip_smb)


def pytest_addoption(parser):
    """添加命令行选项"""
    parser.addoption(
        "--run-smb",
        action="store_true",
        default=False,
        help="运行需要 SMB 连接的测试"
    )
