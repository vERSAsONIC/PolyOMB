# imported/ - 外部导入策略

此目录存放从 GitHub 等外部来源导入并转换的策略。

## 命名规则

导入策略使用序号范围：`00050 - 00999`

格式：`000XX_source_strategy_name/`

## 导入流程

1. **克隆源码**
   ```bash
   git clone https://github.com/xxx/strategy-repo.git
   ```

2. **分析依赖**
   - 检查策略需要的数据
   - 检查策略依赖的 API
   - 识别需要适配的部分

3. **创建转换后文件**
   - `000XX_strategy.yaml` - PolyOMB 格式的配置
   - `000XX_strategy.py` - 适配后的 Python 代码
   - `000XX_strategy.description.md` - 说明文档

4. **可选：保留原始代码**
   ```
   000XX_strategy_name/
   ├── 000XX_strategy.yaml      # 转换后的配置
   ├── 000XX_strategy.py        # 适配后的代码
   ├── 000XX_strategy.description.md
   └── 000XX_original/          # 原始代码（可选）
       └── ...
   ```

## 示例

```
imported/
├── 00050_polyclaw_arbitrage/
│   ├── 00050_strategy.yaml
│   ├── 00050_strategy.py
│   ├── 00050_strategy.description.md
│   └── 00050_original/
│       └── ...
└── 00051_other_source_strategy/
    └── ...
```

## 已导入策略列表

| 序号 | 名称 | 来源 | 状态 | 描述 |
|------|------|------|------|------|
| - | - | - | - | 暂无导入策略 |

---
**注意**: 导入策略时需检查许可证兼容性
