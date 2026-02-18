"""
00002 skill_manager.py - Skill管理界面

提供Streamlit Skill管理功能
参考 OpenClaw 的 Skill 管理界面设计
"""

import streamlit as st
import pandas as pd
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class SkillStatus(Enum):
    """Skill状态"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    NOT_INSTALLED = "not_installed"


@dataclass
class SkillInfo:
    """Skill信息"""
    id: str
    name: str
    emoji: str
    version: str
    author: str
    description: str
    status: SkillStatus
    category: str = "General"
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []


class SkillCard:
    """Skill卡片组件"""
    
    def __init__(self, skill_info: SkillInfo):
        self.skill_info = skill_info
    
    def render(self, on_select=None, key=None):
        """渲染Skill卡片"""
        # 状态颜色映射
        status_colors = {
            SkillStatus.ACTIVE: "🟢",
            SkillStatus.INACTIVE: "⚪",
            SkillStatus.ERROR: "🔴",
            SkillStatus.NOT_INSTALLED: "⚫"
        }
        
        status_icon = status_colors.get(self.skill_info.status, "⚪")
        
        with st.container():
            st.markdown(f"""
            <div style="
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
                background-color: {'#f0f8ff' if self.skill_info.status == SkillStatus.ACTIVE else 'white'};
            ">
                <div style="font-size: 32px; text-align: center;">{self.skill_info.emoji}</div>
                <div style="font-weight: bold; text-align: center;">{self.skill_info.name}</div>
                <div style="font-size: 12px; color: #666; text-align: center;">v{self.skill_info.version}</div>
                <div style="text-align: center; margin-top: 5px;">{status_icon} {self.skill_info.status.value}</div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("▶️ 运行", key=f"run_{self.skill_info.id}_{key}"):
                    if on_select:
                        on_select(self.skill_info, "run")
            with col2:
                if st.button("⚙️ 配置", key=f"config_{self.skill_info.id}_{key}"):
                    if on_select:
                        on_select(self.skill_info, "config")


class SkillManager:
    """Skill管理器"""
    
    def __init__(self, skills_dir: Optional[Path] = None):
        """
        初始化Skill管理器
        
        Args:
            skills_dir: Skills目录路径，默认为 PolyOMB_Skills/
        """
        if skills_dir is None:
            # 默认路径: 当前文件的上两级目录
            self.skills_dir = Path(__file__).parent.parent.parent
        else:
            self.skills_dir = Path(skills_dir)
        
        self.skills: List[SkillInfo] = []
        self.selected_skill: Optional[SkillInfo] = None
        self._load_skills()
    
    def _load_skills(self):
        """从目录加载Skills"""
        self.skills = []
        
        if not self.skills_dir.exists():
            return
        
        # 扫描目录下的所有 000XX_* 文件夹
        for skill_dir in sorted(self.skills_dir.glob("000[0-9][0-9]_*")):
            if skill_dir.is_dir():
                skill_info = self._parse_skill_dir(skill_dir)
                if skill_info:
                    self.skills.append(skill_info)
    
    def _parse_skill_dir(self, skill_dir: Path) -> Optional[SkillInfo]:
        """解析Skill目录"""
        skill_id = skill_dir.name
        
        # 尝试读取 description.md
        desc_file = skill_dir / f"{skill_id}.description.md"
        description = ""
        if desc_file.exists():
            description = desc_file.read_text(encoding='utf-8')[:200]
        
        # 尝试读取 strategy.yaml 获取元数据
        yaml_file = skill_dir / f"{skill_id}.yaml"
        metadata = {}
        if yaml_file.exists():
            try:
                with open(yaml_file) as f:
                    metadata = yaml.safe_load(f) or {}
            except:
                pass
        
        # 确定状态
        status = SkillStatus.ACTIVE if (skill_dir / "__init__.py").exists() else SkillStatus.INACTIVE
        
        # 提取数字序号和名称
        parts = skill_id.split('_', 1)
        seq_num = parts[0] if len(parts) > 0 else "00000"
        name = parts[1].replace('_', ' ').title() if len(parts) > 1 else "Unknown"
        
        return SkillInfo(
            id=skill_id,
            name=metadata.get('name', name),
            emoji=metadata.get('metadata', {}).get('emoji', '📦'),
            version=metadata.get('version', '1.0.0'),
            author=metadata.get('author', 'Unknown'),
            description=description,
            status=status,
            category=metadata.get('category', 'General'),
            dependencies=metadata.get('dependencies', [])
        )
    
    def get_skill_by_id(self, skill_id: str) -> Optional[SkillInfo]:
        """通过ID获取Skill"""
        for skill in self.skills:
            if skill.id == skill_id:
                return skill
        return None
    
    def filter_skills(self, category: Optional[str] = None, status: Optional[SkillStatus] = None) -> List[SkillInfo]:
        """过滤Skills"""
        result = self.skills
        
        if category:
            result = [s for s in result if s.category == category]
        
        if status:
            result = [s for s in result if s.status == status]
        
        return result
    
    def search_skills(self, query: str) -> List[SkillInfo]:
        """搜索Skills"""
        query = query.lower()
        return [
            s for s in self.skills
            if query in s.name.lower() or query in s.description.lower()
        ]
    
    def check_dependencies(self, skill_info: SkillInfo) -> Tuple[bool, List[str]]:
        """
        检查Skill依赖
        
        Returns:
            (是否满足, 缺失依赖列表)
        """
        missing = []
        
        for dep in skill_info.dependencies:
            # 简单检查：假设依赖是Python包
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        
        return len(missing) == 0, missing
    
    def render_header(self):
        """渲染头部"""
        st.title("📦 PolyOMB Skill Manager")
        st.markdown("管理你的交易策略 Skills")
        st.divider()
    
    def render_skill_grid(self, skills: Optional[List[SkillInfo]] = None, on_select=None):
        """渲染Skill网格"""
        if skills is None:
            skills = self.skills
        
        if not skills:
            st.info("暂无Skills，请创建或导入")
            return
        
        # 每行显示3个卡片
        cols = st.columns(3)
        
        for i, skill in enumerate(skills):
            with cols[i % 3]:
                card = SkillCard(skill)
                card.render(on_select=on_select, key=i)
    
    def render_detail_panel(self, skill_info: Optional[SkillInfo] = None):
        """渲染详情面板"""
        st.subheader("📋 Skill 详情")
        
        if skill_info is None:
            st.info("请从左侧选择一个 Skill 查看详情")
            return
        
        st.markdown(f"""
        ### {skill_info.emoji} {skill_info.name}
        
        **ID**: `{skill_info.id}`
        
        **版本**: {skill_info.version}
        
        **作者**: {skill_info.author}
        
        **类别**: {skill_info.category}
        
        **状态**: {skill_info.status.value}
        """)
        
        st.markdown("**描述**:")
        st.markdown(skill_info.description[:500])
        
        # 依赖检查
        if skill_info.dependencies:
            st.markdown("**依赖**:")
            satisfied, missing = self.check_dependencies(skill_info)
            
            for dep in skill_info.dependencies:
                if dep in missing:
                    st.error(f"❌ {dep}")
                else:
                    st.success(f"✅ {dep}")
        
        # 操作按钮
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if skill_info.status == SkillStatus.ACTIVE:
                if st.button("⏸️ 停用", key=f"deactivate_{skill_info.id}"):
                    skill_info.status = SkillStatus.INACTIVE
                    st.rerun()
            else:
                if st.button("▶️ 激活", key=f"activate_{skill_info.id}"):
                    skill_info.status = SkillStatus.ACTIVE
                    st.rerun()
        
        with col2:
            if st.button("⚙️ 配置参数", key=f"config_{skill_info.id}"):
                st.session_state['show_config'] = skill_info.id
        
        with col3:
            if st.button("🚀 运行回测", key=f"run_{skill_info.id}"):
                st.session_state['run_backtest'] = skill_info.id
    
    def render_search_and_filter(self):
        """渲染搜索和过滤"""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            search_query = st.text_input("🔍 搜索 Skills", placeholder="输入关键词...")
        
        with col2:
            categories = list(set([s.category for s in self.skills]))
            categories.insert(0, "全部")
            selected_category = st.selectbox("📁 类别", categories)
        
        return search_query, selected_category
    
    def run(self):
        """运行管理器界面"""
        self.render_header()
        
        # 搜索和过滤
        search_query, selected_category = self.render_search_and_filter()
        
        # 过滤Skills
        filtered_skills = self.skills
        
        if search_query:
            filtered_skills = self.search_skills(search_query)
        
        if selected_category != "全部":
            filtered_skills = [s for s in filtered_skills if s.category == selected_category]
        
        # 主布局：两列
        col_left, col_right = st.columns([2, 1])
        
        with col_left:
            st.subheader(f"已安装 Skills ({len(filtered_skills)})")
            
            def on_skill_select(skill_info, action):
                self.selected_skill = skill_info
                if action == "config":
                    st.session_state['show_config'] = skill_info.id
                elif action == "run":
                    st.session_state['run_backtest'] = skill_info.id
            
            self.render_skill_grid(filtered_skills, on_select=on_skill_select)
        
        with col_right:
            self.render_detail_panel(self.selected_skill)
        
        # 处理状态
        if 'show_config' in st.session_state:
            skill_id = st.session_state['show_config']
            st.sidebar.info(f"配置 Skill: {skill_id}")
        
        if 'run_backtest' in st.session_state:
            skill_id = st.session_state['run_backtest']
            st.sidebar.success(f"运行回测: {skill_id}")


def main():
    """主函数 - 独立运行"""
    st.set_page_config(
        page_title="PolyOMB Skill Manager",
        page_icon="📦",
        layout="wide"
    )
    
    manager = SkillManager()
    manager.run()


if __name__ == "__main__":
    main()
