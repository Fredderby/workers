import streamlit as st
import pandas as pd
from config import reg_div
from datetime import datetime
from connect import cred
import gspread
import time

def workers():
    client = cred()
    spreadsheet = client.open("mini_congress")
    worksheet = spreadsheet.worksheet("national_wk")
    st.write("✅ Network Active!")

    # Pre-check headers once at start
    if 'headers_checked' not in st.session_state:
        try:
            # Get current headers
            current_headers = worksheet.row_values(1)
            required_headers = [
                "Timestamp", "Region", "Division", "Designation Level", 
                "Name", "Gender", "Position", "Contact", 
                "Registration Status", "Confirmation Time"
            ]
            
            # Handle duplicate headers
            header_counts = {}
            clean_headers = []
            for header in current_headers:
                if header in header_counts:
                    header_counts[header] += 1
                    clean_header = f"{header}_{header_counts[header]}"
                else:
                    header_counts[header] = 0
                    clean_header = header
                clean_headers.append(clean_header)
            
            # Add missing columns if needed
            missing_headers = [h for h in required_headers if h not in clean_headers]
            
            if missing_headers or any(k > 0 for k in header_counts.values()):
                # Add missing headers to the worksheet
                new_headers = clean_headers + missing_headers
                worksheet.update('A1', [new_headers])
            
            st.session_state.headers_checked = True
            st.session_state.clean_headers = new_headers if 'new_headers' in locals() else clean_headers
        except Exception as e:
            st.error(f"Header check failed: {str(e)}")
            return

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
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                selected_region.strip(),
                selected_division.strip(),
                designation.strip(),
                name.title(),
                gender,
                position.title(),
                contact,
                "Confirmed",
                datetime.now().strftime("%a %d %b, %H:%M")
            ]

            try:
                # Append the new registration with retry logic
                success = False
                attempts = 0
                max_attempts = 3
                
                while not success and attempts < max_attempts:
                    try:
                        # Get current headers to determine column order
                        current_headers = st.session_state.clean_headers
                        
                        # Create a dictionary for the new row
                        row_data = {}
                        for i, header in enumerate(current_headers):
                            if i < len(wk_regis):
                                row_data[header] = wk_regis[i]
                            else:
                                row_data[header] = ""  # Fill missing columns
                        
                        # Convert to list in header order
                        row_values = [row_data.get(header, "") for header in current_headers]
                        
                        # Append the new registration
                        worksheet.append_row(row_values)
                        success = True
                    except gspread.exceptions.APIError as e:
                        if "RESOURCE_EXHAUSTED" in str(e):
                            attempts += 1
                            st.warning(f"API busy, retrying ({attempts}/{max_attempts})...")
                            time.sleep(2)  # Wait before retrying
                        else:
                            raise
                
                if success:
                    st.success("✅ Successfully Submitted!")
                    st.balloons()
                    time.sleep(1.5)
                    st.rerun()
                else:
                    st.error("Failed to submit after multiple attempts. Please try again later.")
                
            except Exception as e:
                st.error(f"Data not submitted: {str(e)}")

if __name__ == "__main__":
    workers()