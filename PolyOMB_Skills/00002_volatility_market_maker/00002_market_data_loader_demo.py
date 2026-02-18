"""
00002 market_data_loader_demo.py - 数据加载器使用示例

演示如何使用 MarketDataLoader 高效加载市场数据
"""

import sys
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from market_data_loader import MarketDataLoader, create_default_loader, convert_raw_trades_to_market_format
import pandas as pd
from datetime import datetime, timedelta


def demo_basic_usage():
    """基础使用演示"""
    print("=" * 80)
    print("🎯 Demo 1: 基础使用")
    print("=" * 80)
    
    # 创建加载器
    loader = create_default_loader()
    
    # 2020年特朗普选举市场
    market_id = "0xf2e631ea675c5b09caea0bf65cf7887e25907af2657c8c907f02d9afbff20d05"
    
    print(f"\n📊 加载市场: {market_id[:30]}...")
    print("  (Will Trump win the 2020 U.S. presidential election?)")
    
    # 获取市场信息
    info = loader.get_market_info(market_id)
    if info:
        print(f"\n✅ 市场信息:")
        print(f"  问题: {info.get('question')}")
        print(f"  结束日期: {info.get('end_date')}")
        print(f"  交易量: {info.get('volume', 0):,.0f}")
        token_ids = info.get('clob_token_ids', [])
        print(f"  Token IDs: {len(token_ids)} 个")
    else:
        print("\n⚠️ 未找到市场信息")
        return
    
    # 加载交易数据
    print("\n⏳ 加载交易数据...")
    try:
        trades = loader.get_market_trades(market_id)
        
        if trades.empty:
            print("  ⚠️ 未找到交易数据")
            return
        
        print(f"\n✅ 加载成功:")
        print(f"  记录数: {len(trades):,}")
        print(f"  列名: {list(trades.columns)}")
        
        # 转换为策略格式
        market_trades = convert_raw_trades_to_market_format(trades)
        print(f"\n📈 转换后的数据:")
        print(f"  记录数: {len(market_trades):,}")
        print(f"  列名: {list(market_trades.columns)}")
        
        if not market_trades.empty:
            print(f"\n  价格统计:")
            print(f"    平均: {market_trades['price'].mean():.4f}")
            print(f"    最小: {market_trades['price'].min():.4f}")
            print(f"    最大: {market_trades['price'].max():.4f}")
            
            print(f"\n  前5行:")
            print(market_trades.head().to_string())
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()


def demo_cache_mechanism():
    """缓存机制演示"""
    print("\n" + "=" * 80)
    print("💾 Demo 2: 缓存机制")
    print("=" * 80)
    
    loader = create_default_loader()
    
    # 查看缓存统计
    print("\n📊 缓存统计:")
    stats = loader.get_cache_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # 演示二次加载（从缓存）
    market_id = "0xf2e631ea675c5b09caea0bf65cf7887e25907af2657c8c907f02d9afbff20d05"
    
    print(f"\n🔄 二次加载（应从缓存读取）...")
    print("  第一次加载后，数据已缓存到本地")
    print("  第二次加载会直接从本地缓存读取，速度更快")


def demo_multiple_markets():
    """多市场加载演示"""
    print("\n" + "=" * 80)
    print("📚 Demo 3: 批量加载多个市场")
    print("=" * 80)
    
    loader = create_default_loader()
    
    # 几个2020-2023年的市场
    market_ids = [
        "0xf2e631ea675c5b09caea0bf65cf7887e25907af2657c8c907f02d9afbff20d05",  # Trump 2020
        "0x4afe273cde9f431f55621c666b7552f11cb8acbc36e06c39ea7e87564a02b34a",  # Trump inauguration 2021
        "0xf86032dc2a893df839b93c7868e6cb206db8d5f083c2861554e7fd1deab7dd52",  # Biden inauguration 2021
    ]
    
    results = []
    
    for i, market_id in enumerate(market_ids, 1):
        print(f"\n{i}. 加载 {market_id[:30]}...")
        
        info = loader.get_market_info(market_id)
        if info:
            print(f"   Q: {info.get('question', 'Unknown')[:50]}...")
            print(f"   Volume: {info.get('volume', 0):,.0f}")
            
            try:
                trades = loader.get_market_trades(market_id)
                if not trades.empty:
                    market_trades = convert_raw_trades_to_market_format(trades)
                    results.append({
                        'market_id': market_id[:20],
                        'question': info.get('question', 'Unknown')[:30],
                        'trades_count': len(market_trades),
                        'avg_price': market_trades['price'].mean() if not market_trades.empty else 0
                    })
            except Exception as e:
                print(f"   ⚠️ 加载失败: {e}")
    
    print("\n📊 汇总:")
    if results:
        df = pd.DataFrame(results)
        print(df.to_string(index=False))


def demo_time_filter():
    """时间过滤演示"""
    print("\n" + "=" * 80)
    print("⏰ Demo 4: 时间范围过滤")
    print("=" * 80)
    
    loader = create_default_loader()
    
    market_id = "0xf2e631ea675c5b09caea0bf65cf7887e25907af2657c8c907f02d9afbff20d05"
    
    # 加载全部数据
    print(f"\n加载全部数据...")
    all_trades = loader.get_market_trades(market_id)
    print(f"  总记录数: {len(all_trades):,}")
    
    # 模拟时间过滤（实际应根据数据中的时间戳）
    # 这里仅演示接口用法
    print(f"\n时间过滤接口示例:")
    print("  start_time=datetime(2020, 11, 1)")
    print("  end_time=datetime(2020, 11, 30)")


def demo_cache_management():
    """缓存管理演示"""
    print("\n" + "=" * 80)
    print("🗑️ Demo 5: 缓存管理")
    print("=" * 80)
    
    loader = create_default_loader()
    
    # 查看当前缓存状态
    print("\n📊 清除前缓存统计:")
    stats_before = loader.get_cache_stats()
    for key, value in stats_before.items():
        print(f"  {key}: {value}")
    
    # 清除缓存
    print("\n🗑️ 清除缓存...")
    # loader.clear_cache()  # 注释掉，避免误操作
    print("  (已注释掉，避免误操作)")
    print("  如需清除，请取消注释并运行")


def main():
    """主函数"""
    print("\n" + "🚀" * 40)
    print("  MarketDataLoader 使用示例")
    print("🚀" * 40 + "\n")
    
    # 运行各个演示
    demo_basic_usage()
    demo_cache_mechanism()
    demo_multiple_markets()
    demo_time_filter()
    demo_cache_management()
    
    print("\n" + "=" * 80)
    print("✅ 所有演示完成！")
    print("=" * 80)
    print("\n使用建议:")
    print("  1. 首次加载较慢（从SMB读取），后续从本地缓存很快")
    print("  2. 使用 convert_raw_trades_to_market_format() 转换数据格式")
    print("  3. 缓存位置: ~/.cache/polymarket/")
    print("  4. 定期清理缓存: loader.clear_cache()")


if __name__ == "__main__":
    main()
