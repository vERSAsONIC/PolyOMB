"""
00002 result_charts.py - 结果图表展示

提供Plotly图表组件
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import streamlit as st


class PriceChart:
    """价格走势图"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化价格图表
        
        Args:
            data: DataFrame with ['timestamp', 'price', 'best_bid', 'best_ask']
        """
        self.data = data
    
    def render(self, trades: Optional[pd.DataFrame] = None, height: int = 400):
        """
        渲染价格图表
        
        Args:
            trades: 交易记录，用于标记买卖点
            height: 图表高度
        """
        fig = go.Figure()
        
        # 价格线
        fig.add_trace(go.Scatter(
            x=self.data['timestamp'],
            y=self.data['price'],
            mode='lines',
            name='Price',
            line=dict(color='blue', width=2)
        ))
        
        # 买卖挂单
        if 'best_bid' in self.data.columns:
            fig.add_trace(go.Scatter(
                x=self.data['timestamp'],
                y=self.data['best_bid'],
                mode='lines',
                name='Best Bid',
                line=dict(color='green', width=1, dash='dash')
            ))
        
        if 'best_ask' in self.data.columns:
            fig.add_trace(go.Scatter(
                x=self.data['timestamp'],
                y=self.data['best_ask'],
                mode='lines',
                name='Best Ask',
                line=dict(color='red', width=1, dash='dash')
            ))
        
        # 标记交易点
        if trades is not None and not trades.empty:
            buy_trades = trades[trades['type'] == 'BUY']
            sell_trades = trades[trades['type'] == 'SELL']
            
            if not buy_trades.empty:
                fig.add_trace(go.Scatter(
                    x=buy_trades['timestamp'],
                    y=buy_trades['price'],
                    mode='markers',
                    name='Buy',
                    marker=dict(color='green', size=10, symbol='triangle-up')
                ))
            
            if not sell_trades.empty:
                fig.add_trace(go.Scatter(
                    x=sell_trades['timestamp'],
                    y=sell_trades['price'],
                    mode='markers',
                    name='Sell',
                    marker=dict(color='red', size=10, symbol='triangle-down')
                ))
        
        fig.update_layout(
            title="价格走势与交易标记",
            xaxis_title="时间",
            yaxis_title="价格",
            height=height,
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        return fig


class SignalChart:
    """策略信号图"""
    
    def __init__(self, data: pd.DataFrame):
        """
        初始化信号图表
        
        Args:
            data: DataFrame with ['timestamp', 'signal', 'position']
        """
        self.data = data
    
    def render(self, height: int = 300):
        """渲染信号图表"""
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.1,
                           subplot_titles=("交易信号", "持仓变化"))
        
        # 信号图
        buy_signals = self.data[self.data['signal'] == 'BUY']
        sell_signals = self.data[self.data['signal'] == 'SELL']
        
        if not buy_signals.empty:
            fig.add_trace(go.Scatter(
                x=buy_signals['timestamp'],
                y=[1] * len(buy_signals),
                mode='markers',
                name='Buy Signal',
                marker=dict(color='green', size=8, symbol='triangle-up')
            ), row=1, col=1)
        
        if not sell_signals.empty:
            fig.add_trace(go.Scatter(
                x=sell_signals['timestamp'],
                y=[-1] * len(sell_signals),
                mode='markers',
                name='Sell Signal',
                marker=dict(color='red', size=8, symbol='triangle-down')
            ), row=1, col=1)
        
        # 持仓线
        if 'position' in self.data.columns:
            fig.add_trace(go.Scatter(
                x=self.data['timestamp'],
                y=self.data['position'],
                mode='lines',
                name='Position',
                line=dict(color='blue', width=2),
                fill='tozeroy'
            ), row=2, col=1)
        
        fig.update_layout(
            height=height,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        return fig


class PnLChart:
    """PnL曲线"""
    
    def __init__(self, trades: pd.DataFrame):
        """
        初始化PnL图表
        
        Args:
            trades: DataFrame with ['timestamp', 'pnl']
        """
        self.trades = trades
        self.cumulative_pnl = self._calculate_cumulative_pnl()
    
    def _calculate_cumulative_pnl(self) -> pd.DataFrame:
        """计算累计PnL"""
        if self.trades.empty:
            return pd.DataFrame()
        
        df = self.trades.copy()
        df['cumulative_pnl'] = df['pnl'].cumsum()
        return df
    
    def render(self, height: int = 350):
        """渲染PnL图表"""
        if self.cumulative_pnl.empty:
            fig = go.Figure()
            fig.add_annotation(text="暂无交易数据", showarrow=False, font_size=20)
            return fig
        
        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                           vertical_spacing=0.1,
                           subplot_titles=("累计盈亏", "每日盈亏"))
        
        # 累计PnL
        fig.add_trace(go.Scatter(
            x=self.cumulative_pnl['timestamp'],
            y=self.cumulative_pnl['cumulative_pnl'],
            mode='lines',
            name='累计盈亏',
            line=dict(color='purple', width=2),
            fill='tozeroy'
        ), row=1, col=1)
        
        # 日PnL柱状图
        fig.add_trace(go.Bar(
            x=self.cumulative_pnl['timestamp'],
            y=self.cumulative_pnl['pnl'],
            name='每日盈亏',
            marker_color=['green' if x > 0 else 'red' for x in self.cumulative_pnl['pnl']]
        ), row=2, col=1)
        
        # 添加零线
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=1)
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)
        
        fig.update_layout(
            height=height,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02)
        )
        
        return fig


class TradeTable:
    """交易记录表"""
    
    def __init__(self, trades: pd.DataFrame):
        """
        初始化交易表
        
        Args:
            trades: DataFrame with ['timestamp', 'type', 'price', 'size', 'pnl']
        """
        self.trades = trades
    
    def render(self, max_rows: int = 100):
        """
        渲染交易表
        
        Args:
            max_rows: 最大显示行数
        """
        if self.trades.empty:
            st.info("暂无交易记录")
            return
        
        # 格式化数据
        display_df = self.trades.copy()
        
        if 'timestamp' in display_df.columns:
            display_df['时间'] = pd.to_datetime(display_df['timestamp']).dt.strftime('%Y-%m-%d %H:%M')
        
        if 'type' in display_df.columns:
            display_df['类型'] = display_df['type']
        
        if 'price' in display_df.columns:
            display_df['价格'] = display_df['price'].apply(lambda x: f"{x:.4f}")
        
        if 'size' in display_df.columns:
            display_df['数量'] = display_df['size']
        
        if 'pnl' in display_df.columns:
            display_df['盈亏'] = display_df['pnl'].apply(
                lambda x: f"{x:+.2f}" if pd.notna(x) else "-"
            )
        
        # 选择显示列
        columns = ['时间', '类型', '价格', '数量', '盈亏']
        columns = [c for c in columns if c in display_df.columns]
        
        st.dataframe(
            display_df[columns].head(max_rows),
            use_container_width=True,
            hide_index=True
        )


class StatisticsCards:
    """统计指标卡片"""
    
    def __init__(self, stats: Dict):
        """
        初始化统计卡片
        
        Args:
            stats: 统计指标字典
        """
        self.stats = stats
    
    def render(self):
        """渲染统计卡片"""
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_return = self.stats.get('total_return', 0)
            delta = self.stats.get('total_return_delta', 0)
            st.metric(
                label="总收益率",
                value=f"{total_return:+.2f}%",
                delta=f"{delta:+.2f}%"
            )
        
        with col2:
            sharpe = self.stats.get('sharpe_ratio', 0)
            delta = self.stats.get('sharpe_delta', 0)
            st.metric(
                label="夏普比率",
                value=f"{sharpe:.2f}",
                delta=f"{delta:+.2f}"
            )
        
        with col3:
            max_dd = self.stats.get('max_drawdown', 0)
            delta = self.stats.get('max_drawdown_delta', 0)
            st.metric(
                label="最大回撤",
                value=f"{max_dd:.2f}%",
                delta=f"{delta:+.2f}%"
            )
        
        with col4:
            win_rate = self.stats.get('win_rate', 0)
            delta = self.stats.get('win_rate_delta', 0)
            st.metric(
                label="胜率",
                value=f"{win_rate:.0%}",
                delta=f"{delta:+.0%}"
            )
        
        # 第二行
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            trade_count = self.stats.get('trade_count', 0)
            st.metric("交易次数", f"{trade_count}")
        
        with col2:
            profit_factor = self.stats.get('profit_factor', 0)
            st.metric("盈亏比", f"{profit_factor:.2f}")
        
        with col3:
            avg_profit = self.stats.get('avg_profit', 0)
            st.metric("平均盈利", f"{avg_profit:+.2f}%")
        
        with col4:
            avg_loss = self.stats.get('avg_loss', 0)
            st.metric("平均亏损", f"{avg_loss:.2f}%")


class ResultCharts:
    """结果图表组合"""
    
    def __init__(self, price_data: pd.DataFrame, trades: pd.DataFrame, stats: Dict):
        """
        初始化结果图表
        
        Args:
            price_data: 价格数据
            trades: 交易记录
            stats: 统计指标
        """
        self.price_data = price_data
        self.trades = trades
        self.stats = stats
        
        self.price_chart = PriceChart(price_data)
        self.signal_chart = SignalChart(price_data)
        self.pnl_chart = PnLChart(trades)
        self.trade_table = TradeTable(trades)
        self.stat_cards = StatisticsCards(stats)
    
    def render_full_dashboard(self):
        """渲染完整仪表板"""
        # 统计卡片
        self.stat_cards.render()
        
        st.divider()
        
        # 价格图表
        st.subheader("📊 价格走势")
        fig_price = self.price_chart.render(trades=self.trades)
        st.plotly_chart(fig_price, use_container_width=True)
        
        # PnL图表
        st.subheader("📈 盈亏分析")
        fig_pnl = self.pnl_chart.render()
        st.plotly_chart(fig_pnl, use_container_width=True)
        
        st.divider()
        
        # 交易记录
        st.subheader("📋 交易记录")
        self.trade_table.render()


def create_mock_data() -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """创建模拟数据"""
    # 价格数据
    dates = pd.date_range(start='2024-01-01', periods=100, freq='D')
    price_data = pd.DataFrame({
        'timestamp': dates,
        'price': 0.5 + 0.1 * np.sin(np.linspace(0, 4*np.pi, 100)) + np.random.normal(0, 0.02, 100),
        'best_bid': 0.5 + 0.1 * np.sin(np.linspace(0, 4*np.pi, 100)) - 0.01,
        'best_ask': 0.5 + 0.1 * np.sin(np.linspace(0, 4*np.pi, 100)) + 0.01,
        'signal': ['HOLD'] * 100,
        'position': [0] * 30 + [50] * 40 + [0] * 30
    })
    
    # 交易数据
    trades = pd.DataFrame({
        'timestamp': [dates[30], dates[70]],
        'type': ['BUY', 'SELL'],
        'price': [price_data.iloc[30]['price'], price_data.iloc[70]['price']],
        'size': [50, 50],
        'pnl': [None, 5.0]
    })
    
    # 统计数据
    stats = {
        'total_return': 12.5,
        'total_return_delta': 2.3,
        'sharpe_ratio': 1.85,
        'sharpe_delta': 0.15,
        'max_drawdown': -8.2,
        'max_drawdown_delta': -1.2,
        'win_rate': 0.68,
        'win_rate_delta': 0.05,
        'trade_count': 24,
        'profit_factor': 2.1,
        'avg_profit': 2.5,
        'avg_loss': -1.2
    }
    
    return price_data, trades, stats


def main():
    """主函数"""
    st.set_page_config(page_title="结果图表展示", layout="wide")
    st.title("📊 结果图表展示")
    
    price_data, trades, stats = create_mock_data()
    
    charts = ResultCharts(price_data, trades, stats)
    charts.render_full_dashboard()


if __name__ == "__main__":
    main()
