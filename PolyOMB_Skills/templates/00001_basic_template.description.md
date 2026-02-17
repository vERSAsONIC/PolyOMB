# 00001 基础策略模板

## 描述

这是一个策略模板文件，用于演示 PolyOMB 策略的基本结构和格式。

## 使用方法

1. 复制整个 `templates/` 文件夹内容到新的策略目录
2. 重命名文件为 `000XX_strategy_name.*`
3. 修改 `.yaml` 中的 `name`、`description`、`author` 等字段
4. 在 `.py` 文件中实现策略逻辑
5. 更新本说明文档

## 策略参数

| 参数名 | 类型 | 默认值 | 描述 |
|--------|------|--------|------|
| param1 | int | 10 | 示例参数1 |
| param2 | float | 0.01 | 示例参数2 |

## 数据需求

- price_history: 历史价格数据
- volume: 交易量数据

## 依赖 API

- gamma: Polymarket Gamma API

## 作者

your_username
