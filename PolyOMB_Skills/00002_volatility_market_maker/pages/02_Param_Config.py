"""
Page 2: Parameter Configuration

This page is integrated into the main app.py.
Run the main app instead: streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Parameter Configuration", page_icon="⚙️")

st.title("⚙️ Parameter Configuration")
st.info("This page is integrated into the main application.")

st.markdown("""
Please run the main application instead:

```bash
streamlit run app.py
```

Then navigate to **参数配置** from the sidebar.
""")

# Redirect button
if st.button("🚀 Open Main App"):
    st.switch_page("app.py")
