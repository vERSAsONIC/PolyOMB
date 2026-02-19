"""
Page 1: Skill Manager

This page is integrated into the main app.py.
Run the main app instead: streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Skill Manager", page_icon="📦")

st.title("📦 Skill Manager")
st.info("This page is integrated into the main application.")

st.markdown("""
Please run the main application instead:

```bash
streamlit run app.py
```

Then navigate to **Skill 管理** from the sidebar.
""")

# Redirect button
if st.button("🚀 Open Main App"):
    st.switch_page("app.py")
