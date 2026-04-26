import streamlit as st

st.set_page_config(
    page_title="EgyptAir Station Operations",
    page_icon="✈️",
    layout="wide"
)

st.title("EgyptAir Station Operations Platform")
st.write("Welcome to the multi-page operations system for Baghdad Station.")

st.markdown("---")

st.subheader("Navigation")
st.write("Use the left sidebar to navigate between:")

st.markdown("""
- 🏠 Dashboard  
- ✈️ New Flight  
- 📂 Archive  
- ⚙️ Settings  
""")

st.info("This is the main entry page. All operational tools are under the pages on the left.")
