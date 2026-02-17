# 00002 VolatilityMarketMaker 测试套件

> PolyOMB Skill 测试基础设施

---

## 📁 测试文件结构

```
tests/
├── __init__.py                    # 测试包初始化
├── conftest.py                    # Pytest 共享 fixtures 和配置
├── README.md                      # 本文件
├── run_tests.py                   # 测试运行脚本
├── mock_data_generator.py         # Mock 数据生成器
│
├── volatility_calc.py             # 波动率计算模块（核心实现）
├── risk_management.py             # 风险管理模块（核心实现）
├── order_pricing.py               # 订单定价模块（核心实现）
├── data_adapter.py                # 数据适配模块（核心实现）
├── backtest_engine.py             # 回测引擎模块（核心实现）
│
├── test_volatility_calc.py        # 波动率计算单元测试
├── test_order_pricing.py          # 订单定价单元测试
├── test_risk_management.py        # 风险管理单元测试
├── test_data_adapter.py           # 数据适配器测试（Mock + SMB）
├── test_backtest_flow.py          # 集成测试（完整回测流程）
│
├── A0001 测试覆盖率报告.md        # 覆盖率报告
└── A0002 测试使用指南.md          # 使用指南
```

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install pytest pytest-cov pandas numpy
```

### 2. 生成 Mock 数据（无需 SMB）

```bash
python tests/mock_data_generator.py
```

这将生成:
- `mock_data/polymarket/markets.parquet`
- `mock_data/polymarket/trades/{market_id}.parquet`
- `mock_data/polymarket/orderbooks/{market_id}.parquet`
- `mock_data/polymarket/blocks.parquet`

### 3. 运行测试

```bash
# 运行所有测试
python tests/run_tests.py

# 只运行单元测试
python tests/run_tests.py unit

# 只运行集成测试
python tests/run_tests.py integration

# 生成覆盖率报告
python tests/run_tests.py coverage

# 运行特定测试文件
python tests/run_tests.py test_volatility_calc.py

# 运行 SMB 测试（需要网络连接）
python tests/run_tests.py smb
```

---

## 🧪 测试分类

### 单元测试 (Unit Tests)

| 文件 | 测试内容 | 依赖 |
|------|----------|------|
| `test_volatility_calc.py` | 波动率计算准确性、边界情况 | Mock 数据 |
| `test_order_pricing.py` | 订单定价逻辑、价差约束 | Mock 数据 |
| `test_risk_management.py` | 止损/止盈、风控逻辑 | Mock 数据 |

### 集成测试 (Integration Tests)

| 文件 | 测试内容 | 依赖 |
|------|----------|------|
| `test_data_adapter.py` | 数据读取、转换、验证 | Mock / SMB |
| `test_backtest_flow.py` | 完整回测流程 | Mock 数据 |

---

## 📊 测试数据

### Mock 数据 (默认)

- **规模**: 小型（1 个市场，1000 条交易记录）
- **生成**: `python tests/mock_data_generator.py`
- **位置**: `tests/mock_data/`
- **用途**: 无需网络，快速测试

### 真实数据 (可选)

- **路径**: `smb://MM2018._smb._tcp.local/liuqiong/prediction-market-analysis/data`
- **启用**: `pytest --run-smb`
- **用途**: 与真实数据对比验证

---

## 🔧 Fixtures (conftest.py)

### 数据 Fixtures

| Fixture | 说明 | 数据量 |
|---------|------|--------|
| `sample_trades_1k` | 模拟交易数据 | 1000 条 |
| `sample_orderbook_snapshots` | 订单簿快照 | 100 条 |
| `sample_market_metadata` | 市场元数据 | 1 条 |
| `sample_position_history` | 持仓历史 | 100 条 |

### Mock Fixtures

| Fixture | 说明 |
|---------|------|
| `mock_smb_adapter` | Mock SMB 适配器类 |
| `default_skill_config` | 默认 Skill 配置 |
| `mock_environment_vars` | 测试环境变量 |

### 常量

```python
TEST_MARKET_ID = "0x218919622a6132646d149021008659d834927b2b81005a92a54b38d781b0a56f"
SMB_PATH = "smb://MM2018._smb._tcp.local/liuqiong/prediction-market-analysis/data"
```

---

## 📝 测试编写指南

### 添加新测试

1. **在现有文件中添加**

```python
# tests/test_volatility_calc.py

def test_my_new_feature(self):
    """测试新功能"""
    # 准备数据
    data = sample_trades_1k
    
    # 执行测试
    result = my_function(data)
    
    # 验证结果
    assert result == expected_value
```

2. **创建新测试文件**

```python
# tests/test_my_module.py
import pytest
from conftest import TEST_MARKET_ID

def test_something():
    pass
```

### 标记测试

```python
@pytest.mark.smb  # 需要 SMB 连接
def test_real_data():
    pass

@pytest.mark.slow  # 慢测试
@pytest.mark.integration  # 集成测试
def test_slow_integration():
    pass
```

### 跳过测试

```python
# 条件跳过
@pytest.mark.skip(reason="待实现")
def test_not_ready():
    pass

# 基于条件跳过
@pytest.mark.skipif(not HAS_SMB, reason="无 SMB 环境")
def test_smb_feature():
    pass
```

---

## 🎯 测试策略

### TDD 流程

```
1. 编写测试（先失败）
   ↓
2. 实现代码（让测试通过）
   ↓
3. 重构（保持测试通过）
   ↓
4. 循环
```

### 自动修复流程

```bash
# 第 1 次运行
tests fail → 自动修复 → tests run

# 第 2 次运行
tests fail → 自动修复 → tests run

# 第 3 次运行
tests fail → 停止，人工介入
```

---

## 📈 覆盖率目标

| 模块 | 目标覆盖率 | 当前状态 |
|------|-----------|----------|
| 波动率计算 | 95% | ⏳ 待实现 |
| 订单定价 | 90% | ⏳ 待实现 |
| 风险管理 | 90% | ⏳ 待实现 |
| DataAdapter | 85% | ⏳ 待实现 |
| Skill 核心 | 80% | ⏳ 待实现 |
| 回测引擎 | 75% | ⏳ 待实现 |

---

## 🐛 调试技巧

### 查看详细错误

```bash
pytest tests/test_volatility_calc.py -v --tb=long
```

### 只运行失败的测试

```bash
pytest tests/ --lf  # last-failed
```

### 进入 PDB 调试

```python
def test_something():
    import pdb; pdb.set_trace()
    result = my_function()
```

### 使用 pytest 的 capsys

```python
def test_output(capsys):
    print("hello")
    captured = capsys.readouterr()
    assert captured.out == "hello\n"
```

---

## 🔗 相关文件

- [A0012 VolatilityMarketMaker Skill 架构规划.md](../../A0012%20VolatilityMarketMaker%20Skill%20架构规划.md)
- [00002_strategy.py](../00002_strategy.py) - 策略实现（待生成）
- [00002_adapter.py](../00002_adapter.py) - 数据适配器（待生成）

---

## ✅ 检查清单

测试基础设施准备:

- [x] conftest.py - Fixtures 和配置
- [x] test_volatility_calc.py - 波动率测试
- [x] test_order_pricing.py - 定价测试
- [x] test_risk_management.py - 风控测试
- [x] test_data_adapter.py - 适配器测试
- [x] test_backtest_flow.py - 集成测试
- [x] mock_data_generator.py - Mock 数据生成
- [x] run_tests.py - 测试运行脚本
- [x] README.md - 本文档

---

## 📞 问题反馈

测试相关问题请记录到:
- `A0012 VolatilityMarketMaker Skill 架构规划.md` 的"问题记录"部分
- 或直接修改本文件

---

**版本**: 1.0  
**创建**: 2026-02-17  
**状态**: 待代码实现后启用测试
