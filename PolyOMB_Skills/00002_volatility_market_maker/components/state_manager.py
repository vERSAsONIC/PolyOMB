"""
State Manager Component

Unified session state management for the multi-page app
"""

import streamlit as st
from typing import Any, Optional, Dict, List

# Default state configuration
DEFAULT_STATE = {
    # Navigation state
    "current_page": "skill_manager",
    
    # Skill manager state
    "selected_skill": None,
    "skill_filter": {
        "search": "",
        "category": "全部",
        "status": None
    },
    
    # Parameter config state
    "strategy_params": {
        "stop_loss_threshold": -5.0,
        "take_profit_threshold": 3.0,
        "volatility_threshold": 0.15,
        "max_position_size": 250,
        "trade_size": 50,
        "min_size": 5,
        "spread_threshold": 0.02,
        "sleep_period": 6,
    },
    "param_dirty": False,
    "config_version": "1.0",
    
    # Backtest runner state
    "selected_question": None,
    "filter_state": {
        "data_source": "historical",
        "selected_markets": [],
        "search_query": "",
        "selected_tags": [],
        "selected_outcomes": ["Yes", "No"],
        "time_mode": "full",
        "start_date": None,
        "end_date": None,
        "time_preset": "FULL_LIFECYCLE",
    },
    "backtest_running": False,
    "backtest_results": None,
    "backtest_error": None,
    
    # Result charts state
    "chart_config": {
        "show_price": True,
        "show_pnl": True,
        "show_trades": True,
    },
}

# List of all state keys for validation
STATE_KEYS = list(DEFAULT_STATE.keys())


def init_state() -> None:
    """
    Initialize all session state keys with default values.
    Safe to call multiple times - won't overwrite existing values.
    """
    for key, default_value in DEFAULT_STATE.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


def get_state(key: str, default: Any = None) -> Any:
    """
    Get a value from session state.
    
    Args:
        key: State key
        default: Default value if key doesn't exist
        
    Returns:
        Value from session state or default
    """
    init_state()  # Ensure state is initialized
    return st.session_state.get(key, default)


def set_state(key: str, value: Any) -> None:
    """
    Set a value in session state.
    
    Args:
        key: State key
        value: Value to set
    """
    init_state()  # Ensure state is initialized
    st.session_state[key] = value


def update_state(updates: Dict[str, Any]) -> None:
    """
    Update multiple state values at once.
    
    Args:
        updates: Dictionary of key-value pairs to update
    """
    init_state()
    for key, value in updates.items():
        st.session_state[key] = value


def clear_state(keep_keys: Optional[List[str]] = None) -> None:
    """
    Reset session state to defaults.
    
    Args:
        keep_keys: List of keys to preserve (optional)
    """
    keep_keys = keep_keys or []
    preserved = {k: st.session_state.get(k) for k in keep_keys if k in st.session_state}
    
    # Clear and reinitialize
    for key in list(st.session_state.keys()):
        if key not in keep_keys:
            del st.session_state[key]
    
    init_state()
    
    # Restore preserved values
    for key, value in preserved.items():
        st.session_state[key] = value


def is_dirty(key: str) -> bool:
    """
    Check if a specific state has been modified from default.
    
    Args:
        key: State key to check
        
    Returns:
        True if state differs from default
    """
    init_state()
    if key not in DEFAULT_STATE:
        return True
    return st.session_state.get(key) != DEFAULT_STATE[key]


def get_all_state() -> Dict[str, Any]:
    """
    Get a copy of all current state values.
    
    Returns:
        Dictionary of all state values
    """
    init_state()
    return {k: st.session_state.get(k) for k in STATE_KEYS}


def validate_state() -> List[str]:
    """
    Validate current state and return list of missing or invalid keys.
    
    Returns:
        List of error messages
    """
    errors = []
    
    for key in STATE_KEYS:
        if key not in st.session_state:
            errors.append(f"Missing state key: {key}")
    
    # Validate specific state values
    current_page = st.session_state.get("current_page")
    valid_pages = ["skill_manager", "param_config", "backtest_runner", "result_charts"]
    if current_page not in valid_pages:
        errors.append(f"Invalid current_page: {current_page}")
    
    params = st.session_state.get("strategy_params", {})
    if not isinstance(params, dict):
        errors.append("strategy_params must be a dictionary")
    
    return errors


def debug_state() -> None:
    """
    Print current state for debugging (use in development only).
    """
    init_state()
    import json
    state_dump = json.dumps(get_all_state(), indent=2, default=str)
    st.sidebar.expander("🔧 Debug State").code(state_dump)
