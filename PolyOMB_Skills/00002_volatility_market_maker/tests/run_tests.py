#!/usr/bin/env python3
"""
00002 run_tests.py - 测试运行脚本

提供便捷的测试运行方式，支持多种测试场景

使用方法:
    python tests/run_tests.py              # 运行所有测试
    python tests/run_tests.py unit         # 只运行单元测试
    python tests/run_tests.py integration  # 只运行集成测试
    python tests/run_tests.py smb          # 运行 SMB 测试（需要网络）
    python tests/run_tests.py coverage     # 生成覆盖率报告
"""

import sys
import subprocess
import argparse
from pathlib import Path

# 测试目录
TEST_DIR = Path(__file__).parent
PROJECT_ROOT = TEST_DIR.parent


def run_command(cmd: list, description: str) -> int:
    """运行命令并返回退出码"""
    print(f"\n{'='*60}")
    print(f"🔍 {description}")
    print(f"{'='*60}")
    print(f"命令: {' '.join(cmd)}\n")
    
    result = subprocess.run(cmd, cwd=PROJECT_ROOT)
    return result.returncode


def run_all_tests():
    """运行所有测试（不包括 SMB）"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-m", "not smb",  # 跳过 SMB 测试
    ]
    return run_command(cmd, "运行所有测试")


def run_unit_tests():
    """运行单元测试"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_volatility_calc.py",
        "tests/test_order_pricing.py",
        "tests/test_risk_management.py",
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, "运行单元测试")


def run_integration_tests():
    """运行集成测试"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_data_adapter.py",
        "tests/test_backtest_flow.py",
        "-v",
        "--tb=short",
        "-m", "not smb",
    ]
    return run_command(cmd, "运行集成测试")


def run_smb_tests():
    """运行 SMB 测试（需要网络连接）"""
    print("\n⚠️  警告: SMB 测试需要连接到:")
    print("   smb://MM2018._smb._tcp.local/liuqiong/prediction-market-analysis/data")
    print("   请确保网络连接正常。\n")
    
    input("按 Enter 继续，或 Ctrl+C 取消...")
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "-m", "smb",
        "--run-smb",
    ]
    return run_command(cmd, "运行 SMB 测试")


def run_coverage():
    """生成覆盖率报告"""
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=.",
        "--cov-report=html:htmlcov",
        "--cov-report=term-missing",
        "-m", "not smb",
    ]
    code = run_command(cmd, "生成覆盖率报告")
    
    if code == 0:
        print(f"\n✅ 覆盖率报告已生成: {PROJECT_ROOT}/htmlcov/index.html")
        print("   在浏览器中打开查看详细报告\n")
    
    return code


def run_specific_test(test_file: str):
    """运行特定测试文件"""
    test_path = TEST_DIR / test_file
    if not test_path.exists():
        print(f"❌ 测试文件不存在: {test_path}")
        return 1
    
    cmd = [
        sys.executable, "-m", "pytest",
        str(test_path),
        "-v",
        "--tb=short",
    ]
    return run_command(cmd, f"运行 {test_file}")


def main():
    parser = argparse.ArgumentParser(
        description="VolatilityMarketMaker Skill 测试运行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tests/run_tests.py                    # 运行所有测试
  python tests/run_tests.py unit               # 单元测试
  python tests/run_tests.py integration        # 集成测试
  python tests/run_tests.py smb                # SMB 测试
  python tests/run_tests.py coverage           # 覆盖率报告
  python tests/run_tests.py test_volatility_calc.py  # 特定文件
        """
    )
    
    parser.add_argument(
        "target",
        nargs="?",
        default="all",
        help="测试目标: all, unit, integration, smb, coverage, 或具体测试文件"
    )
    
    args = parser.parse_args()
    
    # 检查 pytest 是否安装
    try:
        import pytest
    except ImportError:
        print("❌ 请先安装 pytest: pip install pytest pytest-cov")
        return 1
    
    # 根据目标执行相应测试
    targets = {
        "all": run_all_tests,
        "unit": run_unit_tests,
        "integration": run_integration_tests,
        "smb": run_smb_tests,
        "coverage": run_coverage,
    }
    
    if args.target in targets:
        code = targets[args.target]()
    elif args.target.endswith(".py"):
        code = run_specific_test(args.target)
    else:
        print(f"❌ 未知目标: {args.target}")
        print(f"可用目标: {', '.join(targets.keys())}, 或具体 .py 文件")
        return 1
    
    # 输出总结
    print(f"\n{'='*60}")
    if code == 0:
        print("✅ 所有测试通过!")
    else:
        print(f"❌ 测试失败 (退出码: {code})")
    print(f"{'='*60}\n")
    
    return code


if __name__ == "__main__":
    sys.exit(main())
