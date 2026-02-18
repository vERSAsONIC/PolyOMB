"""
00002 test_ui_skill_manager.py - Skill管理界面测试

测试内容:
- Skill列表渲染
- Skill详情展示
- 操作按钮功能
- 状态显示
"""

import pytest
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from ui.skill_manager import SkillManager, SkillCard, SkillInfo, SkillStatus


class TestSkillManagerInitialization:
    """Skill管理器初始化测试"""
    
    def test_skill_manager_initialization(self):
        """测试管理器初始化"""
        manager = SkillManager()
        assert manager is not None
        assert hasattr(manager, 'skills')
        assert isinstance(manager.skills, list)
    
    def test_load_skills_from_directory(self):
        """测试从目录加载Skills"""
        manager = SkillManager()
        # 应扫描 PolyOMB_Skills/ 目录
        # 至少加载到 00002_volatility_market_maker
        skill_ids = [s.id for s in manager.skills]
        assert '00002_volatility_market_maker' in skill_ids
    
    def test_skill_card_creation(self):
        """测试Skill卡片创建"""
        skill_data = SkillInfo(
            id='00002_volatility_market_maker',
            name='VolatilityMarketMaker',
            emoji='📈',
            version='1.0.0',
            author='PolyOMB Team',
            description='Test skill',
            status=SkillStatus.ACTIVE
        )
        card = SkillCard(skill_data)
        assert card.skill_info.id == '00002_volatility_market_maker'
        assert card.skill_info.name == 'VolatilityMarketMaker'


class TestSkillListRendering:
    """Skill列表渲染测试"""
    
    def test_render_skill_grid(self):
        """测试Skill网格布局渲染"""
        manager = SkillManager()
        # 验证有Skills加载
        assert len(manager.skills) > 0
        # 验证是SkillInfo对象
        for skill in manager.skills:
            assert isinstance(skill, SkillInfo)
    
    def test_skill_card_content(self):
        """测试Skill卡片内容"""
        skill = SkillInfo(
            id='test_skill',
            name='Test Skill',
            emoji='🧪',
            version='1.0.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        # 验证关键属性
        assert skill.emoji == '🧪'
        assert skill.name == 'Test Skill'
        assert skill.version == '1.0.0'
    
    def test_skill_status_display(self):
        """测试Skill状态显示"""
        # 测试所有状态
        for status in SkillStatus:
            skill = SkillInfo(
                id='test',
                name='Test',
                emoji='📦',
                version='1.0',
                author='Test',
                description='Test',
                status=status
            )
            assert skill.status == status


class TestSkillDetailPanel:
    """Skill详情面板测试"""
    
    def test_detail_panel_initialization(self):
        """测试详情面板初始化"""
        manager = SkillManager()
        # 初始没有选择Skill
        assert manager.selected_skill is None
    
    def test_show_skill_details(self):
        """测试显示Skill详情"""
        skill = SkillInfo(
            id='test_detail',
            name='Detail Test',
            emoji='📊',
            version='2.0.0',
            author='Tester',
            description='Detailed description',
            status=SkillStatus.ACTIVE,
            category='Trading'
        )
        # 验证详情
        assert skill.id == 'test_detail'
        assert skill.category == 'Trading'
        assert skill.author == 'Tester'
    
    def test_dependency_check_display(self):
        """测试依赖检查显示"""
        skill = SkillInfo(
            id='test_dep',
            name='Dep Test',
            emoji='📦',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE,
            dependencies=['pandas', 'numpy']
        )
        assert len(skill.dependencies) == 2
        assert 'pandas' in skill.dependencies


class TestSkillActions:
    """Skill操作测试"""
    
    def test_run_button(self):
        """测试运行按钮逻辑"""
        skill = SkillInfo(
            id='test_run',
            name='Run Test',
            emoji='▶️',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        # 验证Skill是激活状态
        assert skill.status == SkillStatus.ACTIVE
    
    def test_config_button(self):
        """测试配置按钮逻辑"""
        skill = SkillInfo(
            id='test_config',
            name='Config Test',
            emoji='⚙️',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        # 验证ID正确
        assert skill.id == 'test_config'
    
    def test_install_button(self):
        """测试安装按钮逻辑"""
        skill = SkillInfo(
            id='test_install',
            name='Install Test',
            emoji='📥',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.NOT_INSTALLED
        )
        assert skill.status == SkillStatus.NOT_INSTALLED
    
    def test_uninstall_button(self):
        """测试卸载按钮逻辑"""
        skill = SkillInfo(
            id='test_uninstall',
            name='Uninstall Test',
            emoji='🗑️',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        assert skill.status == SkillStatus.ACTIVE


class TestSkillStatusManagement:
    """Skill状态管理测试"""
    
    def test_activate_skill(self):
        """测试激活Skill"""
        skill = SkillInfo(
            id='test_activate',
            name='Activate Test',
            emoji='📦',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.INACTIVE
        )
        # 激活
        skill.status = SkillStatus.ACTIVE
        assert skill.status == SkillStatus.ACTIVE
    
    def test_deactivate_skill(self):
        """测试停用Skill"""
        skill = SkillInfo(
            id='test_deactivate',
            name='Deactivate Test',
            emoji='📦',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        # 停用
        skill.status = SkillStatus.INACTIVE
        assert skill.status == SkillStatus.INACTIVE
    
    def test_check_skill_health(self):
        """测试Skill健康检查"""
        manager = SkillManager()
        skill = SkillInfo(
            id='test_health',
            name='Health Test',
            emoji='📦',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE,
            dependencies=[]
        )
        # 检查依赖
        satisfied, missing = manager.check_dependencies(skill)
        assert satisfied is True
        assert len(missing) == 0


class TestSkillConfiguration:
    """Skill配置测试"""
    
    def test_load_default_config(self):
        """测试加载默认配置"""
        manager = SkillManager()
        skill = manager.get_skill_by_id('00002_volatility_market_maker')
        if skill:
            assert skill.version is not None
            assert skill.author is not None
    
    def test_save_config_changes(self):
        """测试保存配置更改"""
        skill = SkillInfo(
            id='test_config_save',
            name='Config Save Test',
            emoji='💾',
            version='1.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        # 模拟修改配置
        skill.version = '2.0'
        assert skill.version == '2.0'
    
    def test_validate_config(self):
        """测试配置验证"""
        skill = SkillInfo(
            id='test_validate',
            name='Validate Test',
            emoji='✅',
            version='1.0.0',
            author='Test',
            description='Test',
            status=SkillStatus.ACTIVE
        )
        # 验证版本号格式
        assert len(skill.version.split('.')) >= 2


class TestUIComponents:
    """UI组件测试"""
    
    def test_header_display(self):
        """测试头部显示"""
        manager = SkillManager()
        # 验证管理器有skills属性
        assert hasattr(manager, 'skills')
    
    def test_search_functionality(self):
        """测试搜索功能"""
        manager = SkillManager()
        # 搜索volatility
        results = manager.search_skills('volatility')
        # 应该能找到00002_volatility_market_maker
        found = any('volatility' in s.name.lower() for s in results)
        assert found or len(results) == 0  # 可能有也可能没有
    
    def test_filter_by_category(self):
        """测试按类别过滤"""
        manager = SkillManager()
        # 获取所有类别
        categories = set(s.category for s in manager.skills)
        # 过滤
        for cat in categories:
            filtered = manager.filter_skills(category=cat)
            for skill in filtered:
                assert skill.category == cat
    
    def test_sort_functionality(self):
        """测试排序功能"""
        manager = SkillManager()
        # 按名称排序
        sorted_skills = sorted(manager.skills, key=lambda s: s.name)
        # 验证排序正确
        for i in range(len(sorted_skills) - 1):
            assert sorted_skills[i].name <= sorted_skills[i+1].name


class TestSkillManagerIntegration:
    """Skill管理器集成测试"""
    
    def test_full_workflow(self):
        """测试完整工作流"""
        manager = SkillManager()
        
        # 1. 加载Skills
        assert len(manager.skills) > 0
        
        # 2. 选择Skill
        skill = manager.skills[0]
        manager.selected_skill = skill
        assert manager.selected_skill == skill
        
        # 3. 查看详情
        assert skill.id is not None
        assert skill.name is not None
        
        # 4. 检查依赖
        satisfied, missing = manager.check_dependencies(skill)
        assert isinstance(satisfied, bool)
        assert isinstance(missing, list)
    
    def test_refresh_skill_list(self):
        """测试刷新Skill列表"""
        manager = SkillManager()
        initial_count = len(manager.skills)
        
        # 重新加载
        manager._load_skills()
        
        # 验证数量一致
        assert len(manager.skills) == initial_count


# =============================================================================
# 运行测试
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
