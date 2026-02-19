"""
PolyOMB Volatility Market Maker - Multi-Page App

Main entry point for the unified Streamlit application.
"""

import streamlit as st
from components import init_state, get_state, set_state
from components.common import render_header, render_navbar, render_footer, PAGES

# Page configuration - must be first st command
st.set_page_config(
    page_title="PolyOMB Volatility Market Maker",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


def navigate_to(page_key: str) -> None:
    """
    Navigate to a specific page.
    
    Args:
        page_key: Target page key
    """
    if page_key in PAGES:
        set_state("current_page", page_key)
        st.rerun()


def render_sidebar() -> None:
    """Render sidebar with navigation and status."""
    with st.sidebar:
        st.title("📦 PolyOMB")
        st.markdown("*Volatility Market Maker*")
        st.divider()
        
        # Navigation
        st.subheader("导航")
        current_page = get_state("current_page", "skill_manager")
        
        for page_key, page_info in PAGES.items():
            is_current = page_key == current_page
            button_type = "primary" if is_current else "secondary"
            
            if st.button(
                f"{page_info['icon']} {page_info['title']}",
                key=f"sidebar_nav_{page_key}",
                use_container_width=True,
                type=button_type
            ):
                navigate_to(page_key)
        
        st.divider()
        
        # Status panel
        st.subheader("状态")
        
        selected_skill = get_state("selected_skill")
        if selected_skill:
            st.success(f"已选择 Skill: {selected_skill}")
        else:
            st.info("未选择 Skill")
        
        if get_state("param_dirty", False):
            st.warning("参数有未保存的修改")
        
        backtest_results = get_state("backtest_results")
        if backtest_results:
            st.success("✅ 回测结果已加载")
        
        st.divider()
        
        # Quick actions
        st.subheader("快捷操作")
        
        if st.button("🔄 重置所有状态", use_container_width=True):
            from components import clear_state
            clear_state()
            st.success("状态已重置")
            st.rerun()
        
        # Debug mode toggle
        debug_mode = st.checkbox("调试模式", value=get_state("debug_mode", False))
        if debug_mode != get_state("debug_mode", False):
            set_state("debug_mode", debug_mode)
            st.rerun()


def render_skill_manager_page() -> None:
    """Render Skill Manager page."""
    from ui.skill_manager import SkillManager, SkillStatus
    
    render_header("Skill 管理", "管理和选择策略 Skills", "📦")
    
    manager = SkillManager()
    
    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input(
            "🔍 搜索 Skills",
            value=get_state("skill_filter", {}).get("search", ""),
            key="skill_search"
        )
    with col2:
        categories = ["全部"] + list(set([s.category for s in manager.skills]))
        selected_category = st.selectbox(
            "📁 类别",
            options=categories,
            key="skill_category"
        )
    
    # Update filter state
    set_state("skill_filter", {
        "search": search_query,
        "category": selected_category
    })
    
    # Filter skills
    filtered_skills = manager.skills
    if search_query:
        filtered_skills = manager.search_skills(search_query)
    if selected_category != "全部":
        filtered_skills = [s for s in filtered_skills if s.category == selected_category]
    
    # Main content
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        st.subheader(f"已安装 Skills ({len(filtered_skills)})")
        
        if not filtered_skills:
            st.info("暂无匹配的 Skills")
        else:
            # Grid layout
            cols = st.columns(3)
            for i, skill in enumerate(filtered_skills):
                with cols[i % 3]:
                    with st.container():
                        # Status color
                        status_colors = {
                            SkillStatus.ACTIVE: "🟢",
                            SkillStatus.INACTIVE: "⚪",
                            SkillStatus.ERROR: "🔴",
                            SkillStatus.NOT_INSTALLED: "⚫"
                        }
                        status_icon = status_colors.get(skill.status, "⚪")
                        
                        st.markdown(f"""
                        <div style="
                            border: 1px solid #ddd;
                            border-radius: 8px;
                            padding: 15px;
                            margin: 5px;
                            background-color: {'#f0f8ff' if skill.status == SkillStatus.ACTIVE else 'white'};
                        ">
                            <div style="font-size: 32px; text-align: center;">{skill.emoji}</div>
                            <div style="font-weight: bold; text-align: center;">{skill.name}</div>
                            <div style="font-size: 12px; color: #666; text-align: center;">v{skill.version}</div>
                            <div style="text-align: center; margin-top: 5px;">{status_icon} {skill.status.value}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Action buttons
                        btn_col1, btn_col2 = st.columns(2)
                        with btn_col1:
                            if st.button("▶️ 运行", key=f"run_{skill.id}", use_container_width=True):
                                set_state("selected_skill", skill.id)
                                navigate_to("backtest_runner")
                        with btn_col2:
                            if st.button("⚙️ 配置", key=f"config_{skill.id}", use_container_width=True):
                                set_state("selected_skill", skill.id)
                                navigate_to("param_config")
    
    with col_right:
        st.subheader("📋 Skill 详情")
        
        # Get selected skill from state or first skill
        selected_skill_id = get_state("selected_skill")
        selected_skill = None
        
        if selected_skill_id:
            selected_skill = manager.get_skill_by_id(selected_skill_id)
        
        if selected_skill:
            st.markdown(f"""
            ### {selected_skill.emoji} {selected_skill.name}
            
            **ID**: `{selected_skill.id}`
            
            **版本**: {selected_skill.version}
            
            **作者**: {selected_skill.author}
            
            **类别**: {selected_skill.category}
            
            **状态**: {selected_skill.status.value}
            """)
            
            st.markdown("**描述**:")
            st.markdown(selected_skill.description[:500])
            
            # Actions
            if selected_skill.status == SkillStatus.ACTIVE:
                if st.button("⏸️ 停用", use_container_width=True):
                    selected_skill.status = SkillStatus.INACTIVE
                    st.rerun()
            else:
                if st.button("▶️ 激活", use_container_width=True):
                    selected_skill.status = SkillStatus.ACTIVE
                    st.rerun()
        else:
            st.info("请选择一个 Skill 查看详情")


def render_param_config_page() -> None:
    """Render Parameter Configuration page."""
    from ui.param_config import ParamConfig
    
    render_header("参数配置", "配置波动率做市策略参数", "⚙️")
    
    config = ParamConfig()
    params = config.params
    
    # Check if skill is selected
    selected_skill = get_state("selected_skill")
    if not selected_skill:
        st.warning("⚠️ 请先选择一个 Skill")
        if st.button("前往 Skill 管理"):
            navigate_to("skill_manager")
        return
    
    st.success(f"当前配置 Skill: {selected_skill}")
    
    # Main content
    col_left, col_right = st.columns([2, 1])
    
    with col_left:
        # Risk parameters
        st.markdown("### 🛡️ 风控参数")
        
        col1, col2 = st.columns(2)
        with col1:
            stop_loss = st.number_input(
                "止损阈值 (%)",
                min_value=-20.0,
                max_value=0.0,
                value=params.stop_loss_threshold,
                step=1.0,
                key="param_stop_loss"
            )
        with col2:
            take_profit = st.number_input(
                "止盈阈值 (%)",
                min_value=0.0,
                max_value=20.0,
                value=params.take_profit_threshold,
                step=1.0,
                key="param_take_profit"
            )
        
        volatility = st.slider(
            "波动率阈值",
            min_value=0.01,
            max_value=1.0,
            value=params.volatility_threshold,
            step=0.01,
            key="param_volatility"
        )
        
        sleep_period = st.slider(
            "暂停期 (小时)",
            min_value=1,
            max_value=48,
            value=params.sleep_period,
            step=1,
            key="param_sleep_period"
        )
        
        st.divider()
        
        # Trading parameters
        st.markdown("### 💼 交易参数")
        
        col1, col2 = st.columns(2)
        with col1:
            max_position = st.number_input(
                "最大持仓",
                min_value=1,
                max_value=1000,
                value=params.max_position_size,
                step=10,
                key="param_max_position"
            )
        with col2:
            trade_size = st.number_input(
                "交易数量",
                min_value=1,
                max_value=1000,
                value=params.trade_size,
                step=5,
                key="param_trade_size"
            )
        
        col1, col2 = st.columns(2)
        with col1:
            min_size = st.number_input(
                "最小数量",
                min_value=1,
                max_value=100,
                value=params.min_size,
                step=1,
                key="param_min_size"
            )
        with col2:
            spread = st.number_input(
                "价差阈值",
                min_value=0.001,
                max_value=0.1,
                value=params.spread_threshold,
                step=0.001,
                format="%.3f",
                key="param_spread"
            )
        
        st.divider()
        
        # Update params object
        params.stop_loss_threshold = stop_loss
        params.take_profit_threshold = take_profit
        params.volatility_threshold = volatility
        params.sleep_period = sleep_period
        params.max_position_size = max_position
        params.trade_size = trade_size
        params.min_size = min_size
        params.spread_threshold = spread
        
        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("💾 保存配置", type="primary", use_container_width=True):
                if config.save_params(params):
                    set_state("param_dirty", False)
                    st.success("✅ 配置已保存")
                else:
                    st.error("❌ 保存失败")
        
        with col2:
            if st.button("🔄 重置默认", use_container_width=True):
                st.info("已重置为默认值")
                st.rerun()
        
        with col3:
            if st.button("🚀 运行回测", use_container_width=True):
                set_state("strategy_params", params.to_dict())
                navigate_to("backtest_runner")
    
    with col_right:
        st.markdown("### 📋 当前配置")
        
        st.markdown("**风控参数**")
        st.markdown(f"- 止损: {stop_loss:+.1f}%")
        st.markdown(f"- 止盈: {take_profit:+.1f}%")
        st.markdown(f"- 波动率: {volatility:.2f}")
        st.markdown(f"- 暂停期: {sleep_period}h")
        
        st.markdown("**交易参数**")
        st.markdown(f"- 最大持仓: {max_position}")
        st.markdown(f"- 交易数量: {trade_size}")
        st.markdown(f"- 最小数量: {min_size}")
        st.markdown(f"- 价差: {spread:.3f}")
        
        st.divider()
        
        st.markdown("### 📖 参数说明")
        st.markdown("""
        **止损阈值**: 触发止损的亏损百分比
        
        **止盈阈值**: 触发止盈的盈利百分比
        
        **波动率阈值**: 3小时波动率超过此值暂停交易
        
        **暂停期**: 止损后的冷却时间
        
        **最大持仓**: 允许的最大持仓数量
        
        **交易数量**: 每次下单的数量
        
        **最小数量**: 最小允许的交易数量
        
        **价差阈值**: 止损时的最小价差要求
        """)


def render_backtest_runner_page() -> None:
    """Render Backtest Runner page."""
    render_header("回测运行", "Volatility Market Maker 回测分析工具", "🔷")
    
    # Check prerequisites
    selected_skill = get_state("selected_skill")
    if not selected_skill:
        st.warning("⚠️ 请先选择一个 Skill")
        if st.button("前往 Skill 管理"):
            navigate_to("skill_manager")
        return
    
    st.success(f"当前 Skill: {selected_skill}")
    
    # Three column layout
    col_left, col_middle, col_right = st.columns([0.20, 0.30, 0.50])
    
    with col_left:
        st.subheader("📊 筛选器")
        
        # Data source
        st.markdown("**1️⃣ 数据源**")
        data_source = st.radio(
            "选择数据源",
            options=["historical", "realtime"],
            format_func=lambda x: {
                "historical": "📁 Historical Data",
                "realtime": "🌐 Real-time API [未来可用]"
            }[x],
            key="backtest_data_source"
        )
        
        st.divider()
        
        # Market filter
        st.markdown("**2️⃣ Market 筛选**")
        categories = ["Politics", "Crypto", "Sports", "Tech", "Other"]
        selected_categories = []
        for cat in categories:
            if st.checkbox(cat, value=True, key=f"backtest_cat_{cat}"):
                selected_categories.append(cat)
        
        st.divider()
        
        # Time range
        st.markdown("**3️⃣ 时间周期**")
        time_mode = st.radio(
            "时间模式",
            options=["full", "custom"],
            format_func=lambda x: {"full": "全生命周期", "custom": "自定义区间"}[x],
            key="backtest_time_mode"
        )
        
        if time_mode == "custom":
            from datetime import datetime
            col1, col2 = st.columns(2)
            with col1:
                st.date_input("开始", datetime(2024, 1, 1), key="backtest_start_date")
            with col2:
                st.date_input("结束", datetime(2024, 12, 31), key="backtest_end_date")
        
        # Action buttons
        st.divider()
        if st.button("🔄 应用筛选", type="primary", use_container_width=True):
            st.success("筛选已应用")
    
    with col_middle:
        st.subheader("📋 Question 列表")
        
        # Mock questions
        questions = [
            {"title": "Will Trump win 2024?", "category": "Politics", "liquidity": 1500000, "volume": 50000},
            {"title": "Will ETH reach $5k?", "category": "Crypto", "liquidity": 800000, "volume": 30000},
            {"title": "Will Fed cut rates in Q1?", "category": "Politics", "liquidity": 1200000, "volume": 45000},
        ]
        
        search = st.text_input("🔍 在结果中搜索", key="backtest_question_search")
        
        if search:
            questions = [q for q in questions if search.lower() in q["title"].lower()]
        
        st.markdown(f"**{len(questions)} 个结果**")
        st.divider()
        
        for i, question in enumerate(questions):
            with st.container():
                st.markdown(f"**{question['title']}**")
                st.caption(f"[{question['category']}] 流动性: ${question['liquidity']:,.0f}")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption(f"24h成交: {question['volume']:,.0f}")
                with col2:
                    if st.button("🔍 分析", key=f"select_question_{i}"):
                        set_state("selected_question", question)
                        st.rerun()
                
                st.divider()
    
    with col_right:
        st.subheader("📈 分析结果")
        
        selected_question = get_state("selected_question")
        
        if not selected_question:
            st.info("👈 从左侧选择一个 Question 开始分析")
            return
        
        st.markdown(f"### {selected_question.get('title', 'Unknown')}")
        
        # Mock charts
        import pandas as pd
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots
        
        dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
        prices = 0.5 + 0.1 * (pd.Series(range(100)) / 100)
        
        # Price chart
        st.markdown("**📊 价格波动图表**")
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=dates,
            y=prices,
            mode='lines',
            name='Price',
            line=dict(color='blue')
        ))
        fig.update_layout(height=300, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Signal chart
        st.markdown("**📈 策略信号图表**")
        position = [0] * 30 + [50] * 40 + [0] * 30
        pnl = [0]
        for i in range(1, 100):
            pnl.append(pnl[-1] + (0.01 if position[i] > 0 else 0))
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True)
        fig.add_trace(go.Scatter(x=dates, y=position, mode='lines', name='Position'), row=1, col=1)
        fig.add_trace(go.Scatter(x=dates, y=pnl, mode='lines', name='PnL'), row=2, col=1)
        fig.update_layout(height=400, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Trade table
        st.markdown("**📋 交易记录**")
        trades = pd.DataFrame({
            '时间': ['2024-01-15 10:30', '2024-01-20 14:20', '2024-01-25 09:15'],
            '类型': ['BUY', 'SELL', 'BUY'],
            '价格': [0.52, 0.58, 0.55],
            '数量': [50, 50, 50],
        })
        st.dataframe(trades, use_container_width=True, hide_index=True)
        
        # Statistics
        st.markdown("**📊 统计指标**")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总收益率", "+12.5%", "+2.3%")
        with col2:
            st.metric("夏普比率", "1.85", "+0.15")
        with col3:
            st.metric("最大回撤", "-8.2%", "-1.2%")
        with col4:
            st.metric("胜率", "68%", "+5%")


def render_result_charts_page() -> None:
    """Render Result Charts page."""
    from ui.result_charts import ResultCharts, create_mock_data
    
    render_header("结果图表", "查看回测结果图表", "📊")
    
    # Check prerequisites
    selected_skill = get_state("selected_skill")
    if not selected_skill:
        st.warning("⚠️ 请先选择一个 Skill 并运行回测")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("前往 Skill 管理"):
                navigate_to("skill_manager")
        with col2:
            if st.button("前往回测运行"):
                navigate_to("backtest_runner")
        return
    
    # Load results (use mock data if none available)
    results = get_state("backtest_results")
    if results:
        st.success("显示真实回测结果")
        price_data = results.get("price_data")
        trades = results.get("trades")
        stats = results.get("stats")
    else:
        st.info("暂无真实回测数据，显示示例数据")
        price_data, trades, stats = create_mock_data()
    
    # Create and render charts
    try:
        charts = ResultCharts(price_data, trades, stats)
        charts.render_full_dashboard()
    except Exception as e:
        st.error(f"渲染图表时出错: {e}")


def main() -> None:
    """Main entry point."""
    # Initialize session state
    init_state()
    
    # Render sidebar
    render_sidebar()
    
    # Render current page
    current_page = get_state("current_page", "skill_manager")
    
    if current_page == "skill_manager":
        render_skill_manager_page()
    elif current_page == "param_config":
        render_param_config_page()
    elif current_page == "backtest_runner":
        render_backtest_runner_page()
    elif current_page == "result_charts":
        render_result_charts_page()
    else:
        st.error(f"Unknown page: {current_page}")
        set_state("current_page", "skill_manager")
        st.rerun()
    
    # Render footer
    render_footer()
    
    # Debug panel
    if get_state("debug_mode", False):
        from components import debug_state
        st.sidebar.divider()
        debug_state()


if __name__ == "__main__":
    main()
