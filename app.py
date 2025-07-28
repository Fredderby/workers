import streamlit as st
from workersdata import workers
from dash import RegistrationDashboard

# Set page configuration
st.set_page_config(page_title="workersdclmghApp", page_icon="🟢", layout="centered")



# Sidebar content (Image + Menu inside bordered container)
with st.sidebar:
    st.subheader("DCLM National Workers Conference", divider="blue")
    st.image('./display/workers.jpg')
    with st.container(border=True):
        sections = st.radio("**MENU**", ["Dashboard", "Registration"], key="sections")
    st.subheader("National Administration", divider="blue")
    st.divider()

st.divider()
with st.container(border=True):
    # Main function based on section selection
    if sections == "Dashboard":
        RegistrationDashboard().run()
    elif sections == "Registration":
        workers()

# Hide default Streamlit UI elements
st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}  /* Hide the hamburger menu */
    footer {visibility: hidden;}     /* Hide the footer */
    header {visibility: hidden;}     /* Hide the header */
    </style>
    """,
    unsafe_allow_html=True
)
