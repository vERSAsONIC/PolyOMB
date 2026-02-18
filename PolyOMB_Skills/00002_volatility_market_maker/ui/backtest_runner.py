"""
00002 backtest_runner.py - 回试运行界面

提供Streamlit回试运行功能
三列布局: 20%筛选器 | 30%Question列表 | 50%结果面板
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple
from enum import Enum
import json


class TimeRangePreset(Enum):
    """时间范围预设"""
    LAST_7_DAYS = "近7天"
    LAST_30_DAYS = "近30天"
    THIS_QUARTER = "本季度"
    FULL_YEAR = "全年"
    FULL_LIFECYCLE = "生命周期"


@dataclass
class FilterState:
    """筛选器状态"""
    data_source: str = "historical"  # historical / realtime
    selected_markets: List[str] = field(default_factory=list)
    search_query: str = ""
    selected_tags: List[str] = field(default_factory=list)
    selected_outcomes: List[str] = field(default_factory=lambda: ["Yes", "No"])
    time_mode: str = "full"  # full / custom
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    time_preset: TimeRangePreset = TimeRangePreset.FULL_LIFECYCLE


@dataclass
class QuestionInfo:
    """Question信息"""
    id: str
    title: str
    category: str
    liquidity: float
    volume_24h: float
    outcomes: List[Dict]
    end_date: datetime


class BacktestRunner:
    """回试运行器"""
    
    def __init__(self):
        """初始化回试运行器"""
        self.filter_state = FilterState()
        self.selected_question: Optional[QuestionInfo] = None
        self.backtest_results: Optional[Dict] = None
        
        # 初始化session state
        if 'filter_state' not in st.session_state:
            st.session_state.filter_state = FilterState()
        if 'selected_question' not in st.session_state:
            st.session_state.selected_question = None
        if 'backtest_running' not in st.session_state:
            st.session_state.backtest_running = False
    
    def render_header(self):
        """渲染头部"""
        st.title("🔷 Poly-Maker-Run")
        st.markdown("Volatility Market Maker 回测分析工具")
        st.divider()
    
    def render_filter_panel(self) -> FilterState:
        """
        渲染筛选器面板 (左列 20%)
        
        Returns:
            更新后的FilterState
        """
        st.subheader("📊 筛选器")
        
        # 1. 数据源选择
        st.markdown("**1️⃣ 数据源**")
        data_source = st.radio(
            "选择数据源",
            options=["historical", "realtime"],
            format_func=lambda x: {
                "historical": "📁 Historical Data (Parquet)",
                "realtime": "🌐 Real-time API (Gamma) [未来可用]"
            }[x],
            key="data_source"
        )
        self.filter_state.data_source = data_source
        
        st.divider()
        
        # 2. Market 筛选
        st.markdown("**2️⃣ Market 筛选**")
        categories = ["Politics", "Crypto", "Sports", "Tech", "Other"]
        selected_categories = []
        for cat in categories:
            if st.checkbox(cat, value=True, key=f"cat_{cat}"):
                selected_categories.append(cat)
        self.filter_state.selected_markets = selected_categories
        
        st.divider()
        
        # 3. Question 搜索
        st.markdown("**3️⃣ Question 筛选**")
        search_query = st.text_input("🔍 搜索 questions...", key="question_search")
        self.filter_state.search_query = search_query
        
        # 热门标签
        st.markdown("**热门 Tags:**")
        tags = ["#Trump", "#BTC", "#Election", "#AI"]
        selected_tags = []
        cols = st.columns(2)
        for i, tag in enumerate(tags):
            with cols[i % 2]:
                if st.button(tag, key=f"tag_{tag}"):
                    selected_tags.append(tag)
        self.filter_state.selected_tags = selected_tags
        
        st.divider()
        
        # 4. Outcome 筛选
        st.markdown("**4️⃣ Outcome 筛选**")
        outcomes = st.multiselect(
            "选择 Outcomes",
            options=["Yes", "No"],
            default=["Yes", "No"],
            key="outcome_filter"
        )
        self.filter_state.selected_outcomes = outcomes
        
        st.divider()
        
        # 5. 时间周期
        st.markdown("**5️⃣ 时间周期**")
        time_mode = st.radio(
            "时间模式",
            options=["full", "custom"],
            format_func=lambda x: {
                "full": "全生命周期",
                "custom": "自定义区间"
            }[x],
            key="time_mode"
        )
        self.filter_state.time_mode = time_mode
        
        if time_mode == "custom":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("开始", datetime(2024, 1, 1), key="start_date")
            with col2:
                end_date = st.date_input("结束", datetime(2024, 12, 31), key="end_date")
            self.filter_state.start_date = datetime.combine(start_date, datetime.min.time())
            self.filter_state.end_date = datetime.combine(end_date, datetime.min.time())
        
        # 时间预设
        st.markdown("**预设:**")
        preset_cols = st.columns(3)
        presets = [
            TimeRangePreset.LAST_7_DAYS,
            TimeRangePreset.LAST_30_DAYS,
            TimeRangePreset.THIS_QUARTER
        ]
        for i, preset in enumerate(presets):
            with preset_cols[i]:
                if st.button(preset.value, key=f"preset_{preset.name}"):
                    self.filter_state.time_preset = preset
        
        st.divider()
        
        # 操作按钮
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 应用筛选", type="primary", use_container_width=True):
                st.session_state.filter_state = self.filter_state
                st.rerun()
        with col2:
            if st.button("重置", use_container_width=True):
                self.filter_state = FilterState()
                st.session_state.filter_state = FilterState()
                st.rerun()
        
        return self.filter_state
    
    def get_mock_questions(self) -> List[QuestionInfo]:
        """获取模拟Question数据"""
        return [
            QuestionInfo(
                id="0x123...",
                title="Will Trump win 2024?",
                category="Politics",
                liquidity=1500000,
                volume_24h=50000,
                outcomes=[{"name": "Yes", "price": 0.65}, {"name": "No", "price": 0.35}],
                end_date=datetime(2024, 11, 5)
            ),
            QuestionInfo(
                id="0x456...",
                title="Will ETH reach $5k?",
                category="Crypto",
                liquidity=800000,
                volume_24h=30000,
                outcomes=[{"name": "Yes", "price": 0.42}, {"name": "No", "price": 0.58}],
                end_date=datetime(2024, 12, 31)
            ),
            QuestionInfo(
                id="0x789...",
                title="Will Fed cut rates in Q1?",
                category="Politics",
                liquidity=1200000,
                volume_24h=45000,
                outcomes=[{"name": "Yes", "price": 0.55}, {"name": "No", "price": 0.45}],
                end_date=datetime(2024, 3, 31)
            ),
        ]
    
    def render_question_list(self, questions: Optional[List[QuestionInfo]] = None):
        """
        渲染Question列表 (中列 30%)
        
        Args:
            questions: Question列表
        """
        st.subheader("📋 Question 列表")
        
        if questions is None:
            questions = self.get_mock_questions()
        
        # 搜索框
        search = st.text_input("🔍 在结果中搜索", key="list_search")
        if search:
            questions = [q for q in questions if search.lower() in q.title.lower()]
        
        st.markdown(f"**{len(questions)} 个结果**")
        st.divider()
        
        # Question卡片列表
        for i, question in enumerate(questions):
            with st.container():
                # 标题和类别
                st.markdown(f"**{question.title}**")
                st.caption(f"[{question.category}] 流动性: ${question.liquidity:,.0f}")
                
                # Outcomes 价格
                for outcome in question.outcomes:
                    st.markdown(f"• {outcome['name']}: {outcome['price']:.2f}")
                
                # 选择按钮
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"24h成交: {question.volume_24h:,.0f}")
                with col2:
                    if st.button("🔍 分析", key=f"select_q_{i}"):
                        st.session_state.selected_question = question
                        st.rerun()
                
                st.divider()
    
    def render_result_panel(self):
        """
        渲染结果面板 (右列 50%)
        """
        st.subheader("📈 分析结果")
        
        question = st.session_state.get('selected_question')
        
        if question is None:
            st.info("👈 从左侧选择一个 Question 开始分析")
            return
        
        st.markdown(f"### {question.title}")
        st.caption(f"ID: {question.id}")
        
        # 价格图表
        st.markdown("**📊 价格波动图表**")
        self._render_price_chart()
        
        # 策略信号图
        st.markdown("**📈 策略信号图表**")
        self._render_signal_chart()
        
        # 交易记录表
        st.markdown("**📋 交易记录**")
        self._render_trade_table()
        
        # 参数面板
        st.markdown("**⚙️ 策略参数**")
        self._render_param_panel()
        
        # 统计指标
        st.markdown("**📊 统计指标**")
        self._render_statistics()
    
    def _render_price_chart(self):
        """渲染价格图表"""
        # 模拟价格数据
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = 0.5 + 0.1 * (pd.Series(range(100)) / 100) + pd.Series([0.02 * (i % 10 - 5) for i in range(100)])
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='Price',
            line=dict(color='blue')
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=0, r=0, t=30, b=0),
            title="历史价格走势"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_signal_chart(self):
        """渲染策略信号图表"""
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        position = [0] * 30 + [50] * 40 + [0] * 30
        pnl = [0]
        for i in range(1, 100):
            pnl.append(pnl[-1] + (0.01 if position[i] > 0 else 0))
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        
        fig.add_trace(go.Scatter(
            x=dates, y=position,
            mode='lines', name='Position',
            line=dict(color='green')
        ), row=1, col=1)
        
        fig.add_trace(go.Scatter(
            x=dates, y=pnl,
            mode='lines', name='PnL',
            line=dict(color='purple')
        ), row=2, col=1)
        
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_trade_table(self):
        """渲染交易记录表"""
        trades = pd.DataFrame({
            '时间': ['2024-01-15 10:30', '2024-01-20 14:20', '2024-01-25 09:15'],
            '类型': ['BUY', 'SELL', 'BUY'],
            '价格': [0.52, 0.58, 0.55],
            '数量': [50, 50, 50],
            '盈亏': [None, 3.0, None]
        })
        st.dataframe(trades, use_container_width=True, hide_index=True)
    
    def _render_param_panel(self):
        """渲染参数面板"""
        col1, col2, col3 = st.columns(3)
        
        with col1:
            stop_loss = st.number_input("止损 (%)", value=-5.0, step=1.0, key="param_sl")
        with col2:
            take_profit = st.number_input("止盈 (%)", value=3.0, step=1.0, key="param_tp")
        with col3:
            vol_threshold = st.number_input("波动率阈值", value=0.15, step=0.01, key="param_vol")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💾 保存参数", key="save_params"):
                st.success("参数已保存")
        with col2:
            if st.button("🔄 重新运行", type="primary", key="rerun_backtest"):
                st.success("正在重新运行...")
    
    def _render_statistics(self):
        """渲染统计指标"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("总收益率", "+12.5%", "+2.3%")
        with col2:
            st.metric("夏普比率", "1.85", "+0.15")
        with col3:
            st.metric("最大回撤", "-8.2%", "-1.2%")
        with col4:
            st.metric("胜率", "68%", "+5%")
    
    def run(self):
        """运行回试运行器"""
        self.render_header()
        
        # 三列布局: 20% - 30% - 50%
        col_left, col_middle, col_right = st.columns([0.20, 0.30, 0.50])
        
        with col_left:
            self.render_filter_panel()
        
        with col_middle:
            self.render_question_list()
        
        with col_right:
            self.render_result_panel()


def main():
    """主函数"""
    st.set_page_config(
        page_title="Poly-Maker-Run",
        page_icon="🔷",
        layout="wide"
    )
    
    runner = BacktestRunner()
    runner.run()


if __name__ == "__main__":
    main()
