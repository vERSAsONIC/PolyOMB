#!/usr/bin/env python3
"""
验证模块导入测试
"""

import sys
import importlib

def test_import(module_name):
    """测试模块导入"""
    try:
        module = importlib.import_module(module_name)
        print(f"✓ {module_name} 导入成功")
        return True
    except Exception as e:
        print(f"✗ {module_name} 导入失败: {e}")
        return False

# 测试所有模块
modules = [
    "volatility_calc",
    "order_pricing", 
    "risk_management",
    "data_adapter",
    "backtest_engine",
]

print("=" * 50)
print("模块导入验证")
print("=" * 50)

all_ok = True
for mod in modules:
    if not test_import(mod):
        all_ok = False

print("=" * 50)
if all_ok:
    print("✓ 所有模块导入成功!")
else:
    print("✗ 部分模块导入失败")
print("=" * 50)

sys.exit(0 if all_ok else 1)
