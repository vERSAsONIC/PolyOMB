"""
00002 param_config.py - 参数配置界面

提供Streamlit参数配置功能
"""

import streamlit as st
import yaml
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class StrategyParams:
    """策略参数"""
    stop_loss_threshold: float = -5.0
    take_profit_threshold: float = 3.0
    volatility_threshold: float = 0.15
    max_position_size: int = 250
    trade_size: int = 50
    min_size: int = 5
    spread_threshold: float = 0.02
    sleep_period: int = 6  # hours
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyParams':
        """从字典创建"""
        return cls(**data)


class ParamValidator:
    """参数验证器"""
    
    @staticmethod
    def validate_stop_loss(value: float) -> Tuple[bool, str]:
        """验证止损阈值"""
        if -20 <= value <= 0:
            return True, ""
        return False, "止损阈值应在 -20% 到 0% 之间"
    
    @staticmethod
    def validate_take_profit(value: float) -> Tuple[bool, str]:
        """验证止盈阈值"""
        if 0 <= value <= 20:
            return True, ""
        return False, "止盈阈值应在 0% 到 20% 之间"
    
    @staticmethod
    def validate_volatility_threshold(value: float) -> Tuple[bool, str]:
        """验证波动率阈值"""
        if 0.01 <= value <= 1.0:
            return True, ""
        return False, "波动率阈值应在 0.01 到 1.0 之间"
    
    @staticmethod
    def validate_positive_integer(value: int, name: str, max_val: int = 10000) -> Tuple[bool, str]:
        """验证正整数"""
        if 1 <= value <= max_val:
            return True, ""
        return False, f"{name}应在 1 到 {max_val} 之间"
    
    @staticmethod
    def validate_spread_threshold(value: float) -> Tuple[bool, str]:
        """验证价差阈值"""
        if 0.001 <= value <= 0.1:
            return True, ""
        return False, "价差阈值应在 0.001 到 0.1 之间"
    
    @staticmethod
    def validate_sleep_period(value: int) -> Tuple[bool, str]:
        """验证暂停期"""
        if 1 <= value <= 48:
            return True, ""
        return False, "暂停期应在 1 到 48 小时之间"
    
    def validate_all(self, params: StrategyParams) -> Tuple[bool, List[str]]:
        """
        验证所有参数
        
        Returns:
            (是否全部有效, 错误信息列表)
        """
        errors = []
        
        validators = [
            (self.validate_stop_loss(params.stop_loss_threshold), "止损阈值"),
            (self.validate_take_profit(params.take_profit_threshold), "止盈阈值"),
            (self.validate_volatility_threshold(params.volatility_threshold), "波动率阈值"),
            (self.validate_positive_integer(params.max_position_size, "最大持仓", 1000), "最大持仓"),
            (self.validate_positive_integer(params.trade_size, "交易数量", 1000), "交易数量"),
            (self.validate_positive_integer(params.min_size, "最小数量", 100), "最小数量"),
            (self.validate_spread_threshold(params.spread_threshold), "价差阈值"),
            (self.validate_sleep_period(params.sleep_period), "暂停期"),
        ]
        
        for (is_valid, error_msg), name in validators:
            if not is_valid:
                errors.append(f"{name}: {error_msg}")
        
        return len(errors) == 0, errors


class ParamConfig:
    """参数配置"""
    
    def __init__(self, skill_id: str = "00002_volatility_market_maker"):
        """
        初始化参数配置
        
        Args:
            skill_id: Skill ID
        """
        self.skill_id = skill_id
        self.skill_dir = Path(__file__).parent.parent
        self.config_file = self.skill_dir / f"{skill_id}_config.yaml"
        
        self.validator = ParamValidator()
        self.params = self._load_params()
    
    def _load_params(self) -> StrategyParams:
        """加载参数"""
        # 尝试从文件加载
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    data = yaml.safe_load(f)
                if data:
                    return StrategyParams.from_dict(data)
            except Exception as e:
                st.error(f"加载配置失败: {e}")
        
        # 尝试从strategy.yaml加载默认值
        yaml_file = self.skill_dir / f"{self.skill_id}.yaml"
        if yaml_file.exists():
            try:
                with open(yaml_file, 'r') as f:
                    config = yaml.safe_load(f)
                if config and 'params' in config:
                    return StrategyParams.from_dict(config['params'])
            except:
                pass
        
        # 返回默认值
        return StrategyParams()
    
    def save_params(self, params: StrategyParams) -> bool:
        """
        保存参数
        
        Args:
            params: 策略参数
            
        Returns:
            是否保存成功
        """
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(params.to_dict(), f, default_flow_style=False)
            return True
        except Exception as e:
            st.error(f"保存配置失败: {e}")
            return False
    
    def render_header(self):
        """渲染头部"""
        st.subheader("⚙️ 策略参数配置")
        st.markdown("配置你的波动率做市策略参数")
        st.divider()
    
    def render_risk_params(self, params: StrategyParams) -> StrategyParams:
        """
        渲染风控参数
        
        Args:
            params: 当前参数
            
        Returns:
            更新后的参数
        """
        st.markdown("### 🛡️ 风控参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**止损阈值** (%)")
            st.caption("当亏损达到此百分比时触发止损")
            stop_loss = st.number_input(
                "止损",
                min_value=-20.0,
                max_value=0.0,
                value=params.stop_loss_threshold,
                step=1.0,
                key="param_stop_loss",
                label_visibility="collapsed"
            )
            params.stop_loss_threshold = stop_loss
        
        with col2:
            st.markdown("**止盈阈值** (%)")
            st.caption("当盈利达到此百分比时触发止盈")
            take_profit = st.number_input(
                "止盈",
                min_value=0.0,
                max_value=20.0,
                value=params.take_profit_threshold,
                step=1.0,
                key="param_take_profit",
                label_visibility="collapsed"
            )
            params.take_profit_threshold = take_profit
        
        st.markdown("**波动率阈值**")
        st.caption("3小时波动率超过此值时暂停交易")
        volatility = st.slider(
            "波动率阈值",
            min_value=0.01,
            max_value=1.0,
            value=params.volatility_threshold,
            step=0.01,
            key="param_volatility"
        )
        params.volatility_threshold = volatility
        
        st.markdown("**暂停期** (小时)")
        st.caption("止损后的暂停交易时间")
        sleep_period = st.slider(
            "暂停期",
            min_value=1,
            max_value=48,
            value=params.sleep_period,
            step=1,
            key="param_sleep_period"
        )
        params.sleep_period = sleep_period
        
        return params
    
    def render_trading_params(self, params: StrategyParams) -> StrategyParams:
        """
        渲染交易参数
        
        Args:
            params: 当前参数
            
        Returns:
            更新后的参数
        """
        st.markdown("### 💼 交易参数")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**最大持仓**")
            st.caption("最大允许持仓数量")
            max_position = st.number_input(
                "最大持仓",
                min_value=1,
                max_value=1000,
                value=params.max_position_size,
                step=10,
                key="param_max_position"
            )
            params.max_position_size = max_position
        
        with col2:
            st.markdown("**交易数量**")
            st.caption("每次交易的数量")
            trade_size = st.number_input(
                "交易数量",
                min_value=1,
                max_value=1000,
                value=params.trade_size,
                step=5,
                key="param_trade_size"
            )
            params.trade_size = trade_size
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**最小数量**")
            st.caption("最小交易数量限制")
            min_size = st.number_input(
                "最小数量",
                min_value=1,
                max_value=100,
                value=params.min_size,
                step=1,
                key="param_min_size"
            )
            params.min_size = min_size
        
        with col2:
            st.markdown("**价差阈值**")
            st.caption("触发止损所需的最小价差")
            spread = st.number_input(
                "价差阈值",
                min_value=0.001,
                max_value=0.1,
                value=params.spread_threshold,
                step=0.001,
                format="%.3f",
                key="param_spread"
            )
            params.spread_threshold = spread
        
        return params
    
    def render_current_values(self, params: StrategyParams):
        """渲染当前参数值"""
        st.markdown("### 📋 当前配置")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**风控参数**")
            st.markdown(f"- 止损: {params.stop_loss_threshold:+.1f}%")
            st.markdown(f"- 止盈: {params.take_profit_threshold:+.1f}%")
            st.markdown(f"- 波动率: {params.volatility_threshold:.2f}")
            st.markdown(f"- 暂停期: {params.sleep_period}h")
        
        with col2:
            st.markdown("**交易参数**")
            st.markdown(f"- 最大持仓: {params.max_position_size}")
            st.markdown(f"- 交易数量: {params.trade_size}")
            st.markdown(f"- 最小数量: {params.min_size}")
            st.markdown(f"- 价差: {params.spread_threshold:.3f}")
        
        with col3:
            st.markdown("**状态**")
            is_valid, errors = self.validator.validate_all(params)
            if is_valid:
                st.success("✅ 参数有效")
            else:
                st.error("❌ 参数有误")
                for error in errors[:3]:
                    st.caption(f"- {error}")
    
    def render_action_buttons(self, params: StrategyParams) -> Tuple[bool, bool]:
        """
        渲染操作按钮
        
        Returns:
            (是否保存, 是否重置)
        """
        col1, col2, col3 = st.columns(3)
        
        save_clicked = False
        reset_clicked = False
        recalc_clicked = False
        
        with col1:
            if st.button("💾 保存配置", type="primary", use_container_width=True):
                save_clicked = True
        
        with col2:
            if st.button("🔄 重置默认", use_container_width=True):
                reset_clicked = True
        
        with col3:
            if st.button("🚀 重新运行", use_container_width=True):
                recalc_clicked = True
        
        return save_clicked, reset_clicked, recalc_clicked
    
    def run(self):
        """运行参数配置界面"""
        self.render_header()
        
        # 创建两列布局
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            # 风控参数
            self.params = self.render_risk_params(self.params)
            
            st.divider()
            
            # 交易参数
            self.params = self.render_trading_params(self.params)
            
            st.divider()
            
            # 操作按钮
            save_clicked, reset_clicked, recalc_clicked = self.render_action_buttons(self.params)
            
            # 处理按钮点击
            if save_clicked:
                is_valid, errors = self.validator.validate_all(self.params)
                if is_valid:
                    if self.save_params(self.params):
                        st.success("✅ 配置已保存")
                else:
                    st.error("❌ 参数验证失败")
                    for error in errors:
                        st.caption(f"- {error}")
            
            if reset_clicked:
                self.params = StrategyParams()
                st.info("已重置为默认值")
                st.rerun()
            
            if recalc_clicked:
                is_valid, errors = self.validator.validate_all(self.params)
                if is_valid:
                    st.session_state['trigger_recalculation'] = True
                    st.success("🚀 触发重新计算")
                else:
                    st.error("❌ 请先修复参数错误")
        
        with col_right:
            # 显示当前配置
            self.render_current_values(self.params)
            
            st.divider()
            
            # 参数说明
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


def main():
    """主函数"""
    st.set_page_config(
        page_title="参数配置",
        page_icon="⚙️",
        layout="wide"
    )
    
    st.title("⚙️ 策略参数配置")
    
    config = ParamConfig()
    config.run()


if __name__ == "__main__":
    main()
