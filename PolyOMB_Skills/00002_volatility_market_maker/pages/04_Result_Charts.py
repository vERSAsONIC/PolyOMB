"""
Page 4: Result Charts

This page is integrated into the main app.py.
Run the main app instead: streamlit run app.py
"""

import streamlit as st

st.set_page_config(page_title="Result Charts", page_icon="📊")

st.title("📊 Result Charts")
st.info("This page is integrated into the main application.")

st.markdown("""
Please run the main application instead:

```bash
streamlit run app.py
```

Then navigate to **结果图表** from the sidebar.
""")

# Redirect button
if st.button("🚀 Open Main App"):
    st.switch_page("app.py")
