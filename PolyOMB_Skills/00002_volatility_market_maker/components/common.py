"""
Common UI Components

Shared UI components for all pages
"""

import streamlit as st
from typing import Optional, Callable, List, Dict, Any
from contextlib import contextmanager

from .state_manager import get_state, set_state

# Page definitions for navigation
PAGES = {
    "skill_manager": {
        "title": "Skill 管理",
        "icon": "📦",
        "description": "管理和选择策略 Skill"
    },
    "param_config": {
        "title": "参数配置",
        "icon": "⚙️",
        "description": "配置策略参数"
    },
    "backtest_runner": {
        "title": "回测运行",
        "icon": "🔷",
        "description": "运行策略回测"
    },
    "result_charts": {
        "title": "结果图表",
        "icon": "📊",
        "description": "查看回测结果"
    },
}


def render_header(title: str, subtitle: Optional[str] = None, icon: str = "📦") -> None:
    """
    Render unified page header.
    
    Args:
        title: Page title
        subtitle: Optional subtitle
        icon: Icon emoji
    """
    st.title(f"{icon} {title}")
    if subtitle:
        st.markdown(subtitle)
    st.divider()


def render_navbar(orientation: str = "horizontal") -> str:
    """
    Render navigation bar.
    
    Args:
        orientation: 'horizontal' or 'vertical'
        
    Returns:
        Selected page key
    """
    current_page = get_state("current_page", "skill_manager")
    
    if orientation == "horizontal":
        # Horizontal navigation with buttons
        cols = st.columns(len(PAGES))
        selected_page = current_page
        
        for i, (page_key, page_info) in enumerate(PAGES.items()):
            with cols[i]:
                is_current = page_key == current_page
                button_type = "primary" if is_current else "secondary"
                
                if st.button(
                    f"{page_info['icon']} {page_info['title']}",
                    key=f"nav_{page_key}",
                    use_container_width=True,
                    type=button_type
                ):
                    selected_page = page_key
                    set_state("current_page", page_key)
                    st.rerun()
    
    else:  # vertical
        # Sidebar navigation
        st.sidebar.title("导航")
        
        options = [f"{p['icon']} {p['title']}" for p in PAGES.values()]
        page_keys = list(PAGES.keys())
        
        current_index = page_keys.index(current_page) if current_page in page_keys else 0
        
        selected = st.sidebar.radio(
            "选择页面",
            options=options,
            index=current_index,
            key="nav_radio"
        )
        
        selected_page = page_keys[options.index(selected)]
        if selected_page != current_page:
            set_state("current_page", selected_page)
            st.rerun()
    
    return selected_page


def render_page_selector() -> str:
    """
    Render page selector dropdown.
    
    Returns:
        Selected page key
    """
    current_page = get_state("current_page", "skill_manager")
    
    options = {f"{p['icon']} {p['title']}": k for k, p in PAGES.items()}
    
    current_label = next(
        (label for label, key in options.items() if key == current_page),
        list(options.keys())[0]
    )
    
    selected_label = st.selectbox(
        "选择页面",
        options=list(options.keys()),
        index=list(options.keys()).index(current_label),
        key="page_selector"
    )
    
    selected_page = options[selected_label]
    if selected_page != current_page:
        set_state("current_page", selected_page)
        st.rerun()
    
    return selected_page


def render_footer() -> None:
    """Render unified page footer."""
    st.divider()
    st.caption("📦 PolyOMB Volatility Market Maker | Built with Streamlit")


def render_error(message: str, exception: Optional[Exception] = None) -> None:
    """
    Render error message.
    
    Args:
        message: Error message
        exception: Optional exception object
    """
    st.error(f"❌ {message}")
    if exception and get_state("debug_mode", False):
        st.exception(exception)


def render_success(message: str) -> None:
    """
    Render success message.
    
    Args:
        message: Success message
    """
    st.success(f"✅ {message}")


def render_info(message: str) -> None:
    """
    Render info message.
    
    Args:
        message: Info message
    """
    st.info(f"ℹ️ {message}")


def render_warning(message: str) -> None:
    """
    Render warning message.
    
    Args:
        message: Warning message
    """
    st.warning(f"⚠️ {message}")


@contextmanager
def render_loading(message: str = "加载中..."):
    """
    Context manager for loading state.
    
    Usage:
        with render_loading("处理数据..."):
            # Long running operation
            process_data()
    
    Args:
        message: Loading message
    """
    with st.spinner(message):
        yield


def render_card(title: str, content: str, icon: str = "📄") -> None:
    """
    Render a card component.
    
    Args:
        title: Card title
        content: Card content (markdown supported)
        icon: Card icon
    """
    with st.container():
        st.markdown(f"""
        <div style="
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 16px;
            margin: 8px 0;
            background-color: white;
        ">
            <div style="font-size: 24px; margin-bottom: 8px;">{icon} {title}</div>
            <div style="color: #666;">{content}</div>
        </div>
        """, unsafe_allow_html=True)


def render_stat_card(label: str, value: str, delta: Optional[str] = None, help_text: Optional[str] = None) -> None:
    """
    Render a statistics card.
    
    Args:
        label: Label text
        value: Value text
        delta: Optional delta value
        help_text: Optional help text
    """
    if delta:
        st.metric(label=label, value=value, delta=delta, help=help_text)
    else:
        st.metric(label=label, value=value, help=help_text)


def render_breadcrumb(pages: List[Dict[str, str]]) -> None:
    """
    Render breadcrumb navigation.
    
    Args:
        pages: List of {'name': str, 'key': str} dicts
    """
    breadcrumb_html = " > ".join([
        f"<span style='color: #666;'>{p['name']}</span>"
        for p in pages
    ])
    st.markdown(f"<small>{breadcrumb_html}</small>", unsafe_allow_html=True)


def render_divider_with_text(text: str) -> None:
    """
    Render a divider with centered text.
    
    Args:
        text: Text to display on divider
    """
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: center;
        margin: 16px 0;
    ">
        <div style="flex: 1; border-top: 1px solid #ddd;"></div>
        <div style="padding: 0 16px; color: #666;">{text}</div>
        <div style="flex: 1; border-top: 1px solid #ddd;"></div>
    </div>
    """, unsafe_allow_html=True)


def button_with_confirmation(
    label: str,
    confirmation_message: str,
    on_confirm: Callable,
    key: Optional[str] = None,
    button_type: str = "secondary"
) -> None:
    """
    Render a button with confirmation dialog.
    
    Args:
        label: Button label
        confirmation_message: Confirmation message
        on_confirm: Callback function when confirmed
        key: Button key
        button_type: Button type ('primary' or 'secondary')
    """
    button_key = key or f"btn_{label}"
    confirm_key = f"{button_key}_confirm"
    
    if st.button(label, key=button_key, type=button_type):
        st.session_state[confirm_key] = True
    
    if st.session_state.get(confirm_key, False):
        st.warning(confirmation_message)
        col1, col2 = st.columns(2)
        with col1:
            if st.button("确认", key=f"{button_key}_yes"):
                on_confirm()
                st.session_state[confirm_key] = False
                st.rerun()
        with col2:
            if st.button("取消", key=f"{button_key}_no"):
                st.session_state[confirm_key] = False
                st.rerun()


def render_page_container(page_content: Callable) -> None:
    """
    Render a page with standard container structure.
    
    Args:
        page_content: Function that renders the page content
    """
    # Initialize state
    from .state_manager import init_state
    init_state()
    
    # Render navigation
    render_navbar(orientation="horizontal")
    
    # Render page content
    page_content()
    
    # Render footer
    render_footer()
    
    # Debug panel (only in debug mode)
    if get_state("debug_mode", False):
        from .state_manager import debug_state
        debug_state()


# Convenience function for page imports
def get_page_module(page_key: str):
    """
    Get page module by key.
    
    Args:
        page_key: Page key
        
    Returns:
        Page module
    """
    import importlib
    module_name = f"pages.{page_key}"
    try:
        return importlib.import_module(module_name)
    except ImportError:
        return None
