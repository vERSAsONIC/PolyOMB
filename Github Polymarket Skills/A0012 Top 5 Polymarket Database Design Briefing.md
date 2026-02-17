# Top 5 Polymarket Database Design Briefing

> GitHub 排行榜前5名 Polymarket 项目数据库结构调研报告
> 
> 调研日期：2026-02-16

---

## 📊 调研概览

| 排名 | 项目 | 作者 | ⭐ Stars | 数据库类型 | 持久化存储 |
|:---:|:-----|:-----|:--------:|:----------:|:----------:|
| 🥇 1 | Polymarket/agents | Polymarket (官方) | 2,200 | ❌ 无 | JSON + ChromaDB |
| 🥈 2 | poly-maker | warproxxx | 792 | Google Sheets | ✅ 云端表格 |
| 🥉 3 | openclaw-skills | BankrBot | 685 | ❌ 无 | ❌ 无 |
| 4 | polymarket-mcp-server | caiovicentino | 167 | ❌ 无 | ❌ 无 |
| 5 | Polymarket-Trading-Bot | metaggdev | 167 | 无法访问 | - |

**关键发现：** 排行榜前5名中，仅 **poly-maker** 使用了类数据库存储（Google Sheets），官方项目 **Polymarket/agents** 虽有完整的 Pydantic 数据模型，但未实现持久化数据库。

---

## 🥇 第1名：Polymarket/agents (2,200⭐)

### 项目概况
- **类型**：官方 AI Agent 框架
- **语言**：Python 3.9
- **GitHub**：https://github.com/Polymarket/agents

### 数据存储方案

| 存储类型 | 技术实现 | 用途 |
|---------|----------|------|
| **向量数据库** | ChromaDB | 存储市场/事件描述的向量嵌入 |
| **本地 JSON 文件** | Python JSON 模块 | 临时缓存 API 返回数据 |
| **内存数据模型** | Pydantic BaseModel | 运行时数据结构定义 |
| **关系型数据库** | ❌ 暂无 | Issue #19 提议但未实现 |

### 核心数据模型（Pydantic）

#### Trade（交易）模型
```python
class Trade(BaseModel):
    id: int
    taker_order_id: str
    market: str
    asset_id: str
    side: str           # BUY/SELL
    size: str
    price: str
    status: str
    match_time: str
    outcome: str
    maker_address: str
    owner: str
    transaction_hash: str
    type: str
```

#### Market（市场）模型（50+ 字段）
```python
class Market(BaseModel):
    id: int
    question: Optional[str]
    conditionId: Optional[str]      # 条件ID（关键字段）
    slug: Optional[str]             # 市场标识
    liquidity: Optional[float]      # 流动性
    volume: Optional[float]         # 交易量
    volume24hr: Optional[float]     # 24H交易量
    active: Optional[bool]          # 是否活跃
    closed: Optional[bool]          # 是否关闭
    outcomePrices: Optional[list]   # 结果价格 [YES, NO]
    clobTokenIds: Optional[list]    # CLOB代币ID
    events: Optional[list[PolymarketEvent]]
    # ... 其他字段
```

#### PolymarketEvent（事件）模型
```python
class PolymarketEvent(BaseModel):
    id: str
    ticker: Optional[str]
    title: Optional[str]
    startDate: Optional[str]
    endDate: Optional[str]
    active: Optional[bool]
    closed: Optional[bool]
    liquidity: Optional[float]
    volume: Optional[float]
    volume24hr: Optional[float]
    markets: Optional[list[Market]]
    tags: Optional[list[Tag]]
```

### 本地文件存储结构
```
./local_db/
├── all-current-markets_{timestamp}.json
├── events.json
├── markets.json
└── chroma/                  # ChromaDB 向量存储
```

### 参考价值
- ✅ **Pydantic 模型可直接参考**：完整的 Gamma API 数据结构映射
- ❌ **无数据库表结构**：需自行实现持久化

---

## 🥈 第2名：poly-maker (792⭐)

### 项目概况
- **类型**：Polymarket 做市商机器人
- **语言**：Python
- **数据库**：Google Sheets（云端表格）
- **GitHub**：https://github.com/warproxxx/poly-maker

### Google Sheets 表结构

#### 1. Full Markets（完整市场表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| question | string | 市场问题/标题 |
| answer1, answer2 | string | 两种结果的答案 |
| token1, token2 | string | 代币ID |
| neg_risk | boolean | 是否为负风险市场 |
| spread | float | 买卖价差 |
| best_bid, best_ask | float | 最佳买卖价 |
| rewards_daily_rate | float | 日奖励率 |
| min_size, max_spread, tick_size | float | 交易限制参数 |
| market_slug | string | 市场标识 |
| condition_id | string | 条件ID |

#### 2. All Markets（所有市场表）
**额外字段：**
| 字段名 | 类型 | 说明 |
|--------|------|------|
| volatility_sum | float | 波动率总和 |
| 1_hour, 3_hour, 6_hour | float | 各时间段年化波动率 |
| 12_hour, 24_hour, 7_day, 30_day | float | 各时间段年化波动率 |
| volatility_price | float | 波动率计算价格 |

#### 3. Volatility Markets（波动率市场表）
- **筛选条件**：`volatility_sum < 20`
- 用于筛选低波动率市场进行做市

#### 4. Selected Markets（选中市场表）
- 用户手动选择要交易的市场
- 字段与 Full Markets 类似

#### 5. Hyperparameters（超参数表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| type | string | 参数类型 |
| param | string | 参数名 |
| value | float/string | 参数值 |

#### 6. Summary（汇总表）
| 字段名 | 类型 | 说明 |
|--------|------|------|
| question | string | 市场问题 |
| answer | string | 答案 |
| order_size | float | 订单数量 |
| position_size | float | 持仓数量 |
| marketInSelected | boolean | 是否在选中市场 |
| earnings | float | 收益 |
| earning_percentage | float | 收益率 |

### 本地文件存储
- `positions/*.json` - 风险状态文件（止损后休眠时间）
- `data/*.csv` - 历史价格数据缓存

### 内存数据结构（global_state.py）
```python
# 市场数据
all_tokens = []              # 所有追踪的代币列表
REVERSE_TOKENS = {}          # 代币映射（YES <-> NO）
all_data = {}                # 订单簿数据
df = None                    # 市场配置 DataFrame

# 交易状态
orders = {}                  # 当前订单 {token: {'buy': {}, 'sell': {}}}
positions = {}               # 当前持仓 {token: {'size': x, 'avgPrice': y}}
performing = {}              # 待处理交易
```

### 参考价值
- ✅ **完整的做市策略表设计**
- ✅ **波动率计算字段参考**
- ✅ **超参数配置表设计**

---

## 🥉 第3名：openclaw-skills (685⭐)

### 项目概况
- **类型**：OpenClaw 技能库
- **性质**：纯文档/配置项目
- **GitHub**：https://github.com/BankrBot/openclaw-skills

### 数据库情况
**❌ 该项目无任何数据库相关内容**

- 仅包含 SKILL.md 技能定义文件
- 通过外部 API 调用实现功能
- 无代码、无表结构、无数据模型

---

## 第4名：polymarket-mcp-server (167⭐)

### 项目概况
- **类型**：MCP 代理服务器
- **语言**：Python
- **GitHub**：https://github.com/caiovicentino/polymarket-mcp-server

### 数据存储方案
**❌ 该项目无任何本地数据库**

- 无状态服务器设计
- 所有数据通过 API 实时获取：
  - `Gamma API` → 市场数据
  - `CLOB API` → 交易数据
  - `WebSocket` → 实时数据
- 仅内存缓存（`PortfolioDataCache` 类）

### Pydantic 数据类
```python
@dataclass
class OrderRequest:
    token_id: str
    price: float
    size: float
    side: str
    market_id: Optional[str] = None

@dataclass
class Position:
    token_id: str
    market_id: str
    size: float
    avg_price: float
    current_price: float
    unrealized_pnl: float
```

---

## 第5名：Polymarket-Trading-Bot (167⭐)

### 项目状态
**❌ 仓库无法访问（404）**

- 仓库已删除或设为私有
- 无法获取源代码

---

## 🔍 替代项目完整数据库设计

虽然前5名项目大多无数据库，但调研过程中发现了以下具有完整数据库设计的项目：

### 方案A：PostgreSQL (Supabase) ⭐⭐⭐⭐⭐
**项目**：GiordanoSouza/polymarket-copy-trading-bot
**数据库**：PostgreSQL (通过 Supabase)

#### 表1：historic_trades（历史交易记录表）
```sql
CREATE TABLE historic_trades (
    id BIGSERIAL PRIMARY KEY,
    proxy_wallet VARCHAR(255),
    timestamp BIGINT,
    activity_datetime TIMESTAMPTZ,
    condition_id VARCHAR(255),          -- 市场条件ID
    type VARCHAR(50),                   -- 交易类型
    size NUMERIC(20,6),                 -- 交易数量
    usdc_size NUMERIC(20,6),            -- USDC金额
    transaction_hash VARCHAR(255),      -- 交易哈希
    price NUMERIC(20,10),               -- 价格
    asset TEXT,                         -- 资产
    side VARCHAR(10),                   -- BUY/SELL
    outcome_index INTEGER,              -- 结果索引
    title TEXT,                         -- 市场标题
    slug VARCHAR(255),                  -- 市场标识
    event_slug VARCHAR(255),            -- 事件标识
    outcome VARCHAR(50),                -- 结果
    trader_name VARCHAR(255),           -- 交易者名称
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    unique_key VARCHAR(500) UNIQUE
);
```

#### 表2：polymarket_positions（持仓表）
```sql
CREATE TABLE polymarket_positions (
    proxy_wallet CHAR(42),              -- 钱包地址
    asset NUMERIC(78,0),                -- 资产ID
    condition_id CHAR(66),              -- 市场条件ID
    size NUMERIC(20,6),                 -- 持仓数量
    avg_price NUMERIC(10,6),            -- 平均价格
    initial_value NUMERIC(24,6),        -- 初始价值
    current_value NUMERIC(24,6),        -- 当前价值
    cash_pnl NUMERIC(24,6),             -- 现金盈亏
    percent_pnl NUMERIC(10,6),          -- 盈亏百分比
    total_bought NUMERIC(24,6),         -- 总买入量
    realized_pnl NUMERIC(24,6),         -- 已实现盈亏
    cur_price NUMERIC(10,6),            -- 当前价格
    redeemable BOOLEAN,                 -- 可赎回
    title VARCHAR(255),                 -- 市场标题
    slug VARCHAR(255),                  -- 市场标识
    event_slug VARCHAR(255),            -- 事件标识
    outcome VARCHAR(32),                -- 结果
    end_date DATE,                      -- 结束日期
    negative_risk BOOLEAN,              -- 负风险
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    PRIMARY KEY (proxy_wallet, asset)   -- 复合主键
);
```

### 方案B：MongoDB
**项目**：dexorynLabs/polymarket-copy-trading-bot-v2.0

#### Collections 设计
- `user_positions_{wallet_address}` - 用户持仓（动态集合名）
- `user_activities_{wallet_address}` - 用户活动（动态集合名）

**字段定义：**
```javascript
// UserPosition
{
  proxyWallet: String,
  asset: String,              // 资产ID
  conditionId: String,        // 市场条件ID
  size: Number,               // 持仓数量
  avgPrice: Number,           // 平均价格
  cashPnl: Number,            // 现金盈亏
  realizedPnl: Number,        // 已实现盈亏
  curPrice: Number,           // 当前价格
  title: String,              // 市场标题
  outcome: String,            // 结果
  endDate: Date,              // 结束日期
  negativeRisk: Boolean       // 负风险
}
```

### 方案C：MongoDB (Mongoose)
**项目**：zydomus219/Polymarket-betting-bot

```javascript
const PolyMarketSchema = new mongoose.Schema({
  asset: String,
  condition_id: String,
  question: String,
  market_slug: String,
  end_date_iso: Date,
  neg_risk: Boolean,
  tokens: [{
    token_id: String,
    outcome: String,
    price: Number,
    winner: Boolean
  }],
  tags: [String],
  transactions: [{
    blockNumber: Number,
    transactionHash: { type: String, index: true },
    tokenId: String,
    side: String,
    makerAmount: String,
    takerAmount: String,
    timestamp: Date
  }]
});
```

---

## 📊 总结对比

| 排名 | 项目 | 数据库 | 核心数据表 | 参考价值 |
|:---:|:-----|:------:|:-----------|:--------:|
| 1 | Polymarket/agents | ❌ 无 | Pydantic 模型 | ⭐⭐ |
| 2 | poly-maker | Google Sheets | 6个工作表 | ⭐⭐⭐ |
| 3 | openclaw-skills | ❌ 无 | ❌ 无 | ❌ |
| 4 | polymarket-mcp-server | ❌ 无 | Pydantic 类 | ❌ |
| 5 | Polymarket-Trading-Bot | 无法访问 | - | - |
| - | **GiordanoSouza项目** | ✅ PostgreSQL | trades + positions | ⭐⭐⭐⭐⭐ |
| - | **dexorynLabs项目** | ✅ MongoDB | 动态集合 | ⭐⭐⭐⭐ |

---

## 💡 PolyOMB 模块1数据库设计建议

基于以上调研，为 PolyOMB 模块1推荐以下数据库表结构：

### 核心数据表（参考 GiordanoSouza + poly-maker）

#### 1. markets（市场表）
```sql
CREATE TABLE markets (
    id SERIAL PRIMARY KEY,
    condition_id VARCHAR(66) UNIQUE NOT NULL,
    question TEXT,
    slug VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    -- 价格数据
    outcome_prices NUMERIC[] DEFAULT '{}',
    best_bid NUMERIC(10,6),
    best_ask NUMERIC(10,6),
    spread NUMERIC(10,6),
    -- 交易数据
    volume NUMERIC(24,6),
    volume_24hr NUMERIC(24,6),
    liquidity NUMERIC(24,6),
    -- 状态
    active BOOLEAN DEFAULT TRUE,
    closed BOOLEAN DEFAULT FALSE,
    archived BOOLEAN DEFAULT FALSE,
    -- 时间
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- 原始数据（JSONB）
    raw_data JSONB
);
```

#### 2. events（事件表）
```sql
CREATE TABLE events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(255) UNIQUE NOT NULL,
    title TEXT,
    slug VARCHAR(255),
    description TEXT,
    category VARCHAR(100),
    tags VARCHAR[] DEFAULT '{}',
    -- 统计数据
    volume NUMERIC(24,6),
    volume_24hr NUMERIC(24,6),
    liquidity NUMERIC(24,6),
    -- 状态
    active BOOLEAN DEFAULT TRUE,
    closed BOOLEAN DEFAULT FALSE,
    -- 时间
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    -- 关联市场
    market_ids INTEGER[] DEFAULT '{}'
);
```

#### 3. price_history（价格历史表）
```sql
CREATE TABLE price_history (
    id BIGSERIAL PRIMARY KEY,
    market_id INTEGER REFERENCES markets(id),
    timestamp TIMESTAMPTZ NOT NULL,
    price_yes NUMERIC(10,6),
    price_no NUMERIC(10,6),
    volume NUMERIC(24,6),
    -- 复合索引
    CONSTRAINT idx_price_history_market_time 
        UNIQUE (market_id, timestamp)
);
```

#### 4. sync_jobs（同步任务表）
```sql
CREATE TABLE sync_jobs (
    id SERIAL PRIMARY KEY,
    job_type VARCHAR(50) NOT NULL,      -- 'markets', 'events', 'prices'
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    metadata JSONB
);
```

---

## 📚 参考链接

| 项目 | 链接 | 说明 |
|:-----|:-----|:-----|
| Polymarket/agents | https://github.com/Polymarket/agents | 官方框架 |
| poly-maker | https://github.com/warproxxx/poly-maker | 做市机器人 |
| openclaw-skills | https://github.com/BankrBot/openclaw-skills | 技能库 |
| polymarket-mcp-server | https://github.com/caiovicentino/polymarket-mcp-server | MCP服务器 |
| GiordanoSouza (PostgreSQL) | https://github.com/GiordanoSouza/polymarket-copy-trading-bot | 完整SQL表结构 |
| dexorynLabs (MongoDB) | https://github.com/dexorynLabs/polymarket-copy-trading-bot-v2.0 | MongoDB设计 |
| zydomus219 (Mongoose) | https://github.com/zydomus219/Polymarket-betting-bot | Mongoose模型 |

---

*报告生成时间：2026-02-16*
*调研人员：Kimi Code CLI*
