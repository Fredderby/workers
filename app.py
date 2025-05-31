import streamlit as st
from workersdata import workers




# Set page configuration
st.set_page_config(page_title="WorkersdclmghApp", page_icon="🟢", layout="centered")

with st.container(border=True):
    st.image('./media/workers.jpg')
    st.markdown("""
                *NB:All DCLM workers must:*  
                      🗸 *Register their interest for the upcoming retreat*.      
                      
            """)


    workers()

st.markdown(
    """
    <style>
    #MainMenu {visibility: hidden;}  # Hide the hamburger menu
    footer {visibility: hidden;}  # Hide the footer
    header {visibility: hidden;}  # Hide the header
    </style>
    """,
    unsafe_allow_html=True
)

