import streamlit as st
import pandas as pd
from config import reg_div
from datetime import datetime
from links import cred
import gspread


def workers():
    client = cred()
    spreadsheet = client.open("mini_congress")
    worksheet = spreadsheet.worksheet("national_wk")
    st.write("✅ Network Active!")


    with st.container(border=True):
        name = st.text_input("Full Name", placeholder="Full Name", key="name").strip()
        gender = st.selectbox("Gender", ["Select", "Male", "Female"], key="gender")
        designation = st.selectbox(
            "Designation Level",
            ["National", "Regional", "Divisional", "Group", "District", "Local"],
            index=None,
            placeholder="Select",
            key="designation"
        )
        position = st.text_input("Position", placeholder="Your Role", key="position").strip()

        selected_region = st.selectbox(
            "Region",
            list(reg_div.keys()),
            index=None,
            placeholder="Select Region",
            key="region"
        )

        divisions = reg_div.get(selected_region, [])
        selected_division = st.selectbox(
            "Division",
            divisions,
            index=None,
            placeholder="Select Division"
        )

        contact = st.text_input("Telephone Number", placeholder="10-digit number", key="contact").strip()

        submitted = st.button("Register", type="primary")

        if submitted:
            validation_error = False

            if not name:
                st.error("Full Name is required")
                validation_error = True

            if gender == "Select":
                st.error("Select a Gender")
                validation_error = True

            if not designation:
                st.error("Select Designation Level")
                validation_error = True

            if not position:
                st.error("Position is required")
                validation_error = True

            if not selected_region:
                st.error("Select a Region")
                validation_error = True

            if not selected_division:
                st.error("Select a Division")
                validation_error = True

            if not contact or not contact.isdigit() or len(contact) != 10:
                st.error("Enter a valid 10-digit Telephone Number")
                validation_error = True

            if validation_error:
                st.stop()

            # Prepare data for saving
            wk_regis = [
                str(datetime.now()),
                selected_region.strip(),
                selected_division.strip(),
                designation.strip(),
                name.title(),
                gender,
                position.title(),
                contact
            ]

            try:
                worksheet.append_row(wk_regis)
                st.success("✅ Successfully Submitted!")
                st.balloons()
            except Exception as e:
                st.error(f"Data not submitted: {str(e)}")

if __name__ == "__main__":
    workers()
