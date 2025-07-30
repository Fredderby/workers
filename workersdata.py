import streamlit as st
import pandas as pd
from config import reg_div
from datetime import datetime
from connect import cred
import gspread

def workers():
    client = cred()
    spreadsheet = client.open("mini_congress")
    worksheet = spreadsheet.worksheet("national_wk")
    st.write("✅ Network Active!")

    with st.container(border=True):
        name = st.text_input("Full Name", placeholder="Full Name", key="name").strip()
        
        gender_options = ["Select", "Male", "Female"]
        gender = st.selectbox("Gender", gender_options, index=0, key="gender")

        designation_options = ["Select", "National", "Regional", "Divisional", "Group", "District", "Local"]
        designation = st.selectbox("Designation Level", designation_options, index=0, key="designation")

        position = st.text_input("Position", placeholder="Your Role", key="position").strip()

        region_options = ["Select Region"] + list(reg_div.keys())
        selected_region = st.selectbox("Region", region_options, index=0, key="region")

        # Avoid KeyError for division list when no region is selected
        actual_region = selected_region if selected_region != "Select Region" else None
        divisions = reg_div.get(actual_region, [])
        division_options = ["Select Division"] + divisions
        selected_division = st.selectbox("Division", division_options, index=0, key="division")

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

            if designation == "Select":
                st.error("Select Designation Level")
                validation_error = True

            if not position:
                st.error("Position is required")
                validation_error = True

            if selected_region == "Select Region":
                st.error("Select a Region")
                validation_error = True

            if selected_division == "Select Division":
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
                contact,
                "Confirmed",  # Add Registration Status
                datetime.now().strftime("%a %d %b, %H:%M")  # Add Confirmation Time
            ]

            try:
                # Get current headers to ensure we have the correct columns
                current_headers = worksheet.row_values(1)
                required_headers = [
                    "Timestamp", "Region", "Division", "Designation Level", 
                    "Name", "Gender", "Position", "Contact", 
                    "Registration Status", "Confirmation Time"
                ]
                
                # Add missing columns if needed
                missing_headers = [h for h in required_headers if h not in current_headers]
                if missing_headers:
                    # Add missing headers to the worksheet
                    new_headers = current_headers + missing_headers
                    worksheet.update('A1', [new_headers])
                
                # Append the new registration
                worksheet.append_row(wk_regis)
                
                st.success("✅ Successfully Submitted!")
                st.balloons()
            except Exception as e:
                st.error(f"Data not submitted: {str(e)}")

if __name__ == "__main__":
    workers()