# PolyOMB Skills 策略仓库

> 🎯 存放 PolyOMB 策略管理器的交易策略（Skills）

## 快速开始

### 创建新策略

1. 在根目录下创建新文件夹：`000XX_strategy_name/`
2. 复制 `templates/` 中的模板文件
3. 修改配置和代码
4. 编写说明文档

### 导入外部策略

1. 将外部策略（如 PolyClaw）放入 `imported/`
2. 按序号命名：`000XX_source_name/`
3. 确保包含转换后的 `.yaml` 和 `.py` 文件

## 目录说明

| 目录 | 用途 |
|------|------|
| `templates/` | 策略模板，供复制使用 |
| `imported/` | 从 GitHub 导入的第三方策略 |
| `000XX_*/` | 用户自定义策略 |

## 策略格式

每个策略必须包含：
- `000XX_strategy.yaml` - 配置和元数据
- `000XX_strategy.py` - 策略执行代码
- `000XX_strategy.description.md` - 说明文档

详细规范见：[A0011 PolyOMB_Skills 文件夹说明.md](../A0011%20PolyOMB_Skills%20文件夹说明.md)
