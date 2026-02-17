#!/usr/bin/env python3
"""
00002 mock_data_generator.py - Mock 数据生成器

生成模拟的 prediction-market-analysis 数据结构
用于测试，无需实际 SMB 连接

使用方法:
    python tests/mock_data_generator.py              # 生成所有数据
    python tests/mock_data_generator.py --market-id 0x...  # 指定市场
    python tests/mock_data_generator.py --output ./mock_data  # 指定输出目录
"""

import argparse
import json
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional


# =============================================================================
# 默认配置
# =============================================================================

DEFAULT_MARKET_ID = "0x218919622a6132646d149021008659d834927b2b81005a92a54b38d781b0a56f"
DEFAULT_OUTPUT_DIR = Path(__file__).parent / "mock_data"

# 模拟市场元数据
SAMPLE_MARKETS = [
    {
        "condition_id": DEFAULT_MARKET_ID,
        "question": "Will Donald Trump win the 2024 US Presidential Election?",
        "description": "This market will resolve to Yes if Donald Trump wins the 2024 US Presidential Election.",
        "category": "Politics",
        "subcategory": "US Elections",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 11, 5),
        "resolution_date": datetime(2024, 11, 6),
        "token1": "0x1234567890abcdef1234567890abcdef12345678",
        "token2": "0xfedcba0987654321fedcba0987654321fedcba09",
        "answer1": "Yes",
        "answer2": "No",
        "tick_size": 0.01,
        "neg_risk": False,
        "min_order_size": 1,
        "icon": "https://example.com/icon.png",
    },
    {
        "condition_id": "0xabcdef1234567890abcdef1234567890abcdef12",
        "question": "Will Bitcoin exceed $100,000 in 2024?",
        "description": "This market will resolve to Yes if Bitcoin trades above $100,000 USD.",
        "category": "Crypto",
        "subcategory": "Bitcoin",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 12, 31),
        "resolution_date": datetime(2025, 1, 1),
        "token1": "0x1111111111111111111111111111111111111111",
        "token2": "0x2222222222222222222222222222222222222222",
        "answer1": "Yes",
        "answer2": "No",
        "tick_size": 0.01,
        "neg_risk": False,
        "min_order_size": 1,
        "icon": "https://example.com/btc.png",
    },
    {
        "condition_id": "0x9999999999999999999999999999999999999999",
        "question": "Will there be a US government shutdown in 2024?",
        "description": "This market will resolve to Yes if the US government has a shutdown.",
        "category": "Politics",
        "subcategory": "US Government",
        "start_date": datetime(2024, 1, 1),
        "end_date": datetime(2024, 12, 31),
        "resolution_date": datetime(2025, 1, 1),
        "token1": "0x3333333333333333333333333333333333333333",
        "token2": "0x4444444444444444444444444444444444444444",
        "answer1": "Yes",
        "answer2": "No",
        "tick_size": 0.01,
        "neg_risk": False,
        "min_order_size": 1,
        "icon": "https://example.com/gov.png",
    },
]


# =============================================================================
# 数据生成函数
# =============================================================================

def generate_trades(
    market_id: str,
    n: int = 1000,
    start_date: datetime = None,
    end_date: datetime = None,
    base_price: float = 0.5,
    volatility: float = 0.02,
    seed: int = 42
) -> pd.DataFrame:
    """
    生成模拟交易数据
    
    Args:
        market_id: 市场 ID
        n: 交易数量
        start_date: 开始日期
        end_date: 结束日期
        base_price: 基础价格
        volatility: 价格波动率
        seed: 随机种子
    
    Returns:
        DataFrame 包含 trades 数据
    """
    np.random.seed(seed)
    
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    if end_date is None:
        end_date = start_date + timedelta(days=7)
    
    # 生成时间戳（每 10 分钟一条）
    timestamps = [start_date + timedelta(minutes=i*10) for i in range(n)]
    
    # 生成价格（使用随机游走 + 趋势）
    price_changes = np.random.normal(0, volatility, n)
    # 添加正弦趋势（模拟市场情绪变化）
    trend = np.sin(np.linspace(0, 4*np.pi, n)) * 0.1
    prices = base_price + np.cumsum(price_changes) * 0.01 + trend
    prices = np.clip(prices, 0.01, 0.99)  # 限制在有效范围
    
    # 生成交易量
    volumes = np.random.randint(10, 500, n)
    
    # 生成买卖方向（55% 买盘，模拟多头市场）
    sides = np.random.choice(["BUY", "SELL"], n, p=[0.55, 0.45])
    
    # 生成交易哈希
    tx_hashes = [f"0x{np.random.randint(10**16, 10**17):016x}" for _ in range(n)]
    
    df = pd.DataFrame({
        "timestamp": timestamps,
        "market": [market_id] * n,
        "asset_id": np.where(sides == "BUY", 
                            f"{market_id[:20]}_yes", 
                            f"{market_id[:20]}_no"),
        "side": sides,
        "price": np.round(prices, 4),
        "size": volumes,
        "transaction_hash": tx_hashes,
    })
    
    return df


def generate_markets_df(markets: List[Dict]) -> pd.DataFrame:
    """生成 markets DataFrame"""
    return pd.DataFrame(markets)


def generate_orderbook_snapshots(
    market_id: str,
    n: int = 100,
    start_date: datetime = None,
    seed: int = 42
) -> pd.DataFrame:
    """
    生成模拟订单簿快照
    
    Args:
        market_id: 市场 ID
        n: 快照数量
        start_date: 开始日期
        seed: 随机种子
    
    Returns:
        DataFrame 包含订单簿数据
    """
    np.random.seed(seed)
    
    if start_date is None:
        start_date = datetime(2024, 1, 1)
    
    timestamps = [start_date + timedelta(minutes=i*30) for i in range(n)]
    
    data = []
    for i, ts in enumerate(timestamps):
        # 中心价格随时间变化
        mid_price = 0.5 + np.sin(i / 20) * 0.1 + np.random.normal(0, 0.02)
        mid_price = np.clip(mid_price, 0.1, 0.9)
        
        # 价差
        spread = np.random.uniform(0.01, 0.03)
        
        data.append({
            "timestamp": ts,
            "market": market_id,
            "best_bid": round(mid_price - spread/2, 4),
            "best_bid_size": np.random.randint(50, 200),
            "second_best_bid": round(mid_price - spread/2 - 0.01, 4),
            "second_best_bid_size": np.random.randint(30, 150),
            "top_bid": round(mid_price - spread/2 - np.random.uniform(0.01, 0.05), 4),
            "best_ask": round(mid_price + spread/2, 4),
            "best_ask_size": np.random.randint(50, 200),
            "second_best_ask": round(mid_price + spread/2 + 0.01, 4),
            "second_best_ask_size": np.random.randint(30, 150),
            "top_ask": round(mid_price + spread/2 + np.random.uniform(0.01, 0.05), 4),
            "bid_sum_within_n_percent": np.random.uniform(500, 2000),
            "ask_sum_within_n_percent": np.random.uniform(500, 2000),
        })
    
    return pd.DataFrame(data)


def generate_blocks(n: int = 100) -> pd.DataFrame:
    """生成模拟区块链数据"""
    np.random.seed(42)
    
    base_time = datetime(2024, 1, 1)
    
    data = []
    for i in range(n):
        data.append({
            "block_number": 50000000 + i,
            "timestamp": base_time + timedelta(seconds=i*12),  # 12秒/块
            "block_hash": f"0x{np.random.randint(10**16, 10**17):016x}",
            "transaction_count": np.random.randint(50, 200),
        })
    
    return pd.DataFrame(data)


# =============================================================================
# 输出函数
# =============================================================================

def save_data(df: pd.DataFrame, path: Path, filename: str):
    """保存 DataFrame 为 CSV（兼容性更好）"""
    path.mkdir(parents=True, exist_ok=True)
    # 使用 CSV 格式避免 pyarrow 依赖
    csv_filename = filename.replace('.parquet', '.csv')
    filepath = path / csv_filename
    df.to_csv(filepath, index=False)
    print(f"  ✓ 生成: {filepath} ({len(df)} 行)")
    return filepath


def save_json(data: Dict, path: Path, filename: str):
    """保存数据为 JSON"""
    path.mkdir(parents=True, exist_ok=True)
    filepath = path / filename
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    print(f"  ✓ 生成: {filepath}")
    return filepath


def generate_all_mock_data(
    output_dir: Path,
    market_id: str = None,
    n_trades: int = 1000
):
    """生成所有 Mock 数据"""
    
    print(f"\n{'='*60}")
    print("🎲 生成 Mock 数据")
    print(f"{'='*60}")
    print(f"输出目录: {output_dir}")
    print(f"交易数量: {n_trades}")
    print()
    
    output_dir = Path(output_dir)
    
    # 1. 生成 Markets 数据
    print("📊 生成 Markets 数据...")
    markets_df = generate_markets_df(SAMPLE_MARKETS)
    save_data(markets_df, output_dir / "polymarket", "markets.csv")
    
    # 2. 为每个市场生成 Trades 数据
    print("\n💱 生成 Trades 数据...")
    
    target_markets = [m for m in SAMPLE_MARKETS if market_id is None or m["condition_id"] == market_id]
    
    for market in target_markets:
        mid = market["condition_id"]
        print(f"\n  市场: {market['question'][:50]}...")
        
        # 生成交易数据
        trades_df = generate_trades(
            market_id=mid,
            n=n_trades,
            start_date=market["start_date"],
            end_date=market["start_date"] + timedelta(days=7),
        )
        save_data(trades_df, output_dir / "polymarket" / "trades", f"{mid}.csv")
        
        # 生成订单簿快照
        orderbook_df = generate_orderbook_snapshots(
            market_id=mid,
            n=100,
            start_date=market["start_date"],
        )
        save_data(orderbook_df, output_dir / "polymarket" / "orderbooks", f"{mid}.csv")
    
    # 3. 生成 Blocks 数据
    print("\n⛓️  生成 Blocks 数据...")
    blocks_df = generate_blocks(n=100)
    save_data(blocks_df, output_dir / "polymarket", "blocks.csv")
    
    # 4. 生成元数据文件
    print("\n📝 生成元数据...")
    metadata = {
        "generated_at": datetime.now().isoformat(),
        "version": "1.0.0",
        "markets": [{"id": m["condition_id"], "question": m["question"]} for m in SAMPLE_MARKETS],
        "data_stats": {
            "trades_per_market": n_trades,
            "orderbook_snapshots": 100,
            "blocks": 100,
        },
    }
    save_json(metadata, output_dir, "metadata.json")
    
    print(f"\n{'='*60}")
    print("✅ Mock 数据生成完成!")
    print(f"{'='*60}")
    print(f"数据位置: {output_dir}")
    print()
    print("使用方式:")
    print(f"  1. 在测试中设置环境变量:")
    print(f"     export POLYOMB_MOCK_DATA_PATH={output_dir}")
    print(f"  2. 或在 conftest.py 中使用 mock_smb_adapter fixture")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="生成 Mock 测试数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/mock_data_generator.py
  python tests/mock_data_generator.py --market-id 0x2189...
  python tests/mock_data_generator.py --n-trades 5000 --output ./my_data
        """
    )
    
    parser.add_argument(
        "--market-id",
        type=str,
        default=None,
        help=f"指定市场 ID (默认: 所有市场)"
    )
    
    parser.add_argument(
        "--n-trades",
        type=int,
        default=1000,
        help="每个市场生成的交易数量 (默认: 1000)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default=str(DEFAULT_OUTPUT_DIR),
        help=f"输出目录 (默认: {DEFAULT_OUTPUT_DIR})"
    )
    
    args = parser.parse_args()
    
    generate_all_mock_data(
        output_dir=Path(args.output),
        market_id=args.market_id,
        n_trades=args.n_trades
    )


if __name__ == "__main__":
    main()
