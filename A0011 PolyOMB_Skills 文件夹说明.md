# A0011 PolyOMB_Skills 文件夹说明

## 1. 用途

`PolyOMB_Skills/` 文件夹用于存储 **PolyOMB 策略管理器** 中的具体交易策略（Skills）。

每个策略都是一个独立的可插拔模块，包含配置、代码和说明文档。

## 2. 策略来源

| 来源类型 | 存放位置 | 说明 |
|---------|----------|------|
| **用户创建** | `PolyOMB_Skills/000XX_*/` | 通过 UI 编辑或代码编写的自定义策略 |
| **GitHub 导入** | `PolyOMB_Skills/imported/` | 从开源项目（如 PolyClaw）抓取并转换的策略 |
| **系统模板** | `PolyOMB_Skills/templates/` | 供用户参考和复制的策略模板 |

## 3. 文件命名规则

遵循项目统一的 **5位数字序号** 规则：

| 类型 | 命名格式 | 示例 |
|------|----------|------|
| 策略文件夹 | `000XX_strategy_name/` | `00001_momentum_strategy/` |
| 策略配置 | `000XX_strategy.yaml` | `00001_strategy.yaml` |
| 策略代码 | `000XX_strategy.py` | `00001_strategy.py` |
| 说明文档 | `000XX_strategy.description.md` | `00001_strategy.description.md` |

## 4. 策略格式规范

参考 OpenClaw Skill 设计，PolyOMB 策略采用 YAML + Python 的混合格式：

### 4.1 策略配置文件（.yaml）

```yaml
---
name: momentum-strategy
description: "基于价格动量的交易策略"
metadata:
  polyomb:
    emoji: "📈"
    author: "username"
    source: "github|custom"
    version: "1.0.0"
    created_at: "2024-01-15"
    requires:
      data: ["price_history", "volume", "order_book"]
      apis: ["gamma"]
    params:
      - name: "lookback_period"
        type: "int"
        default: 14
        description: "回看周期"
      - name: "threshold"
        type: "float"
        default: 0.05
        description: "动量阈值"
---
```

### 4.2 策略代码文件（.py）

```python
"""
策略名称: 动量策略
作者: username
描述: 基于价格动量的自动化交易策略
"""

from polyomb.strategy import BaseStrategy
from polyomb.data import MarketData

class MomentumStrategy(BaseStrategy):
    def __init__(self, config):
        super().__init__(config)
        self.lookback = config.get("lookback_period", 14)
        self.threshold = config.get("threshold", 0.05)
    
    def on_data(self, data: MarketData):
        """接收市场数据时触发"""
        pass
    
    def on_signal(self, signal):
        """生成交易信号"""
        pass
```

## 5. GitHub 策略导入流程

将外部策略（如 PolyClaw）转换为 PolyOMB 可用格式的步骤：

```
步骤 1: 从 GitHub 克隆策略源码
    ↓
步骤 2: 分析策略依赖和数据需求
    ↓
步骤 3: 创建适配器（如有必要）
    ↓
步骤 4: 转换为 PolyOMB Skill 格式
    ↓
步骤 5: 放置到 imported/ 目录，按序号命名
    ↓
步骤 6: 注册到策略管理器
```

### 5.1 导入策略示例

假设从 PolyClaw 导入一个策略：

```
PolyOMB_Skills/imported/
└── 00050_polyclaw_arbitrage/          # 序号从 00050 开始留给导入策略
    ├── 00050_strategy.yaml            # 转换后的配置
    ├── 00050_strategy.py              # 适配后的代码
    ├── 00050_original/                # 原始代码备份（可选）
    │   └── ...
    └── 00050_strategy.description.md  # 说明文档（含来源和转换记录）
```

## 6. 目录结构

```
PolyOMB_Skills/
├── README.md                              # 策略仓库使用指南
│
├── templates/                             # 策略模板
│   ├── 00001_basic_template.yaml
│   ├── 00001_basic_template.py
│   └── 00001_basic_template.description.md
│
├── imported/                              # 从 GitHub 导入的策略
│   └── 00050_polyclaw_example/
│       ├── 00050_strategy.yaml
│       ├── 00050_strategy.py
│       └── 00050_strategy.description.md
│
└── 00001_momentum_strategy/               # 用户创建的示例策略
    ├── 00001_strategy.yaml
    ├── 00001_strategy.py
    └── 00001_strategy.description.md
```

## 7. 与策略管理器的集成

策略管理器将通过以下方式发现和使用 Skills：

1. **扫描机制**: 启动时扫描 `PolyOMB_Skills/` 目录
2. **动态加载**: 根据 `.yaml` 配置动态加载策略类
3. **版本控制**: 支持策略的版本管理和更新
4. **沙箱执行**: 策略在隔离环境中运行，确保安全

## 8. 相关文档

- [R0002 项目B-OpenClaw Skill系统深度分析.md](../R0002%20项目B-OpenClaw%20Skill系统深度分析.md) - Skill 系统设计参考
- [polyomb_design_draft.md](../polyomb_design_draft.md) - 系统架构草案
- `AGENTS.md` - 项目开发规则（含文件命名规范）

---

**创建时间**: 2024-02-17  
**最后更新**: 2024-02-17
