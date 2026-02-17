# GitHub Polymarket Skills / MCP / Agent 汇总文档

> 记录 GitHub 上所有与 Polymarket 相关的 Skill、MCP Server 和 AI Agent 工具
> 
> 📊 数据更新时间：2026-02-16

---

## 📊 OpenClaw Skill / MCP Server 汇总表

| 项目名称 | 作者 | 类型 | 主要功能 | 技术栈 | ⭐ Stars | 📥 包管理器 | 安装方式 | 特点 |
|:---------|:-----|:-----|:---------|:-------|:--------:|:----------:|:---------|:-----|
| **PolyClaw** | chainstacklabs | OpenClaw Skill | • 市场浏览（热门/搜索）<br>• 交易执行（买/卖 YES/NO）<br>• 持仓跟踪与 P&L<br>• 对冲机会扫描<br>• 钱包管理 | Python | N/A | N/A | `clawhub install polyclaw` | ✅ 专为 OpenClaw 设计<br>✅ Split + CLOB 交易执行<br>✅ LLM 对冲分析 |
| **Polymarket MCP Server** | caiovicentino | MCP Server | • **45 个工具**分 5 类：<br>  - 市场发现(8)<br>  - 市场分析(10)<br>  - 交易(12)<br>  - 投资组合(8)<br>  - 实时监控(7)<br>• Web Dashboard<br>• 企业级风控 | Python | **167** | N/A | `curl -sSL quickstart.sh \| bash` | ✅ 功能最完整<br>✅ WebSocket 实时数据<br>✅ DEMO 模式（无需钱包）<br>✅ 支持 Claude Desktop |
| **PolyMarket-MCP** | guangxiangdebizi | MCP Server | • 市场数据获取<br>• 用户持仓查询<br>• 交易历史<br>• 订单簿深度<br>• 市场持有者分析 | TypeScript/Node.js | N/A | N/A | 手动安装 | ✅ TypeScript 实现<br>✅ SSE/Stdio 双模式<br>✅ 多 API 集成 |
| **polymarket-mcp** | ozgureyilmaz | MCP Server | • 实时数据：活跃市场、趋势<br>• 当前价格查询 | Rust | **39** | N/A | Rust 1.70+ | ✅ Rust 实现<br>✅ 高性能 |
| **polymarket-predictions-mcp** | kukapay | MCP Server | • 实时市场赔率<br>• AI Agent 数据访问 | Python | N/A | N/A | MCP 配置 | ✅ MCP 协议兼容<br>✅ 预测市场数据 |
| **Polymarket Agents** | Polymarket (官方) | AI Agent 框架 | • Gamma API 集成<br>• 本地/远程 RAG<br>• 新闻数据源<br>• LLM 工具集 | Python 3.9 | **2,200** | N/A | `pip install -r requirements.txt` | ✅ 官方框架<br>✅ 完整 CLI 工具<br>✅ Docker 支持 |
| **Polymarket AI** | Dhaiwat10 | AI Agent 竞技场 | • 多代理竞争交易<br>• 实时 Dashboard<br>• 新闻分析(Exa API)<br>• 风险管理<br>• 持仓跟踪 | Next.js + SQLite | N/A | N/A | `bun install` + Docker | ✅ 多 Agent 竞争<br>✅ 实时 Web UI<br>✅ SQLite 持久化 |
| **Bankr OpenClaw Skills** | BankrBot | Skill 库 | • 包含 Polymarket 文档<br>• 交易参考指南 | OpenClaw Skill | **685** | N/A | `https://github.com/BankrBot/openclaw-skills` | ✅ 金融基础设施 Skill<br>✅ DeFi 集成 |
| **polymarket-ai-market-suggestor** | lorine93s | AI 市场建议 | • 实时新闻分析<br>• 社交情绪<br>• 链上趋势<br>• LLM 市场提议 | - | N/A | N/A | - | ✅ 市场创建建议 |

---

## 🔧 其他 Polymarket 交易机器人（非 Skill/MCP）

| 项目 | 作者 | 类型 | 功能 | 语言 | ⭐ Stars | 📥 包管理器 |
|:-----|:-----|:-----|:-----|:-----|:--------:|:----------:|
| **Polymarket-Trading-Bot** | metaggdev | 交易机器人 | 订单执行、市场分析、自动套利 | Python | **167** | N/A |
| **polymarket-trading-bot** | discountry | 交易机器人 | Gasless 交易、WebSocket 实时数据 | Python | N/A | N/A |
| **polymarket-trading-bot** | Now-Or-Neverr | 交易机器人 | 核心交易、跟单交易、套利检测 | Python | N/A | N/A |
| **Polymarket-betting-bot** | echandsome | 交易机器人 | Copy Trading、MM Bot | TypeScript/Node.js | N/A | N/A |
| **poly-maker** | warproxxx | 做市机器人 | 自动做市、流动性提供 | Python | **792** | N/A |
| **polybot** | ent0n29 | 交易基础设施 | 逆向工程、策略工具包 | Python | N/A | N/A |
| **polymarket-automated-mm** | terrytrl100 | 做市机器人 | 自动市场选择、仓位管理 | - | N/A | N/A |
| **pamela** | theSchein | ElizaOS Agent | 24/7 自主交易、新闻分析 | - | N/A | N/A |
| **Polyagent** | 0xPhysis | AI Agent | 自主预测下注、区块链记录 | - | N/A | N/A |
| **polymarket-agent** | SidharthK2 | Telegram Bot | 多代理架构、个性化市场发现 | - | N/A | N/A |

---

## 📈 Stars 排行榜

### ⭐ Stars 数量最高的前 5 个项目：

| 排名 | 项目 | 作者 | Stars |
|:---:|:-----|:-----|:-----:|
| 🥇 1 | **Polymarket/agents** | Polymarket (官方) | **2,200** |
| 🥈 2 | **poly-maker** | warproxxx | **792** |
| 🥉 3 | **openclaw-skills** | BankrBot | **685** |
| 4 | **polymarket-mcp-server** | caiovicentino | **167** |
| 5 | **Polymarket-Trading-Bot** | metaggdev | **167** |

---

## 📝 数据说明

- **⭐ Stars**：GitHub 仓库的 Star 数量，反映项目受欢迎程度
- **📥 包管理器**：N/A 表示该项目未发布到 PyPI/npm/crates.io 等包管理器，或数据未公开
- **N/A 说明**：标记为 "N/A" 表示该数据在 GitHub 页面或搜索结果中未公开显示，可能是因为：
  1. 项目是较新的仓库或私有仓库
  2. 未发布到公共包管理器
  3. GitHub API 限制导致数据无法获取

---

## 💡 推荐使用建议

| 场景 | 推荐工具 |
|:-----|:---------|
| **OpenClaw 用户** | PolyClaw (chainstacklabs) |
| **Claude Desktop 用户** | Polymarket MCP Server (caiovicentino) |
| **Node.js/TypeScript 开发者** | PolyMarket-MCP (guangxiangdebizi) |
| **Python 开发者** | Polymarket Agents (官方) 或 caiovicentino MCP |
| **多 Agent 竞技场** | Polymarket AI (Dhaiwat10) |
| **企业级交易** | caiovicentino MCP Server（风控最全）|
| **寻找成熟项目** | Polymarket/agents (2,200⭐ 官方项目) |
| **做市策略** | poly-maker (792⭐ 自动做市机器人) |

---

## 🔗 相关链接

| 项目 | GitHub 链接 |
|:-----|:------------|
| PolyClaw | https://github.com/chainstacklabs/polyclaw |
| Polymarket MCP Server | https://github.com/caiovicentino/polymarket-mcp-server |
| PolyMarket-MCP | https://github.com/guangxiangdebizi/PolyMarket-MCP |
| polymarket-mcp (Rust) | https://github.com/ozgureyilmaz/polymarket-mcp |
| polymarket-predictions-mcp | https://github.com/kukapay/polymarket-predictions-mcp |
| Polymarket Agents (官方) | https://github.com/Polymarket/agents |
| Polymarket AI | https://github.com/Dhaiwat10/polymarket-ai |
| Bankr OpenClaw Skills | https://github.com/BankrBot/openclaw-skills |
| Polymarket-Trading-Bot | https://github.com/metaggdev/Polymarket-Trading-Bot |
| poly-maker | https://github.com/warproxxx/poly-maker |

---

*文档生成时间: 2026-02-16*
