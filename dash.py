import streamlit as st
import pandas as pd
from datetime import datetime
from rapidfuzz import process, fuzz
from connect import cred
import gspread
import time

class RegistrationDashboard:
    def __init__(self):
        self.client = self.get_google_client()
        self.national_ws, self.manual_ws = self.get_worksheets()
        self.df = self.load_and_clean_data()
    
    @st.cache_resource(show_spinner="Connecting to Google Sheets...")
    def get_google_client(_self):
        try:
            return cred()
        except Exception as e:
            st.error(f"Connection initialization failed: {e}")
            st.stop()
    
    def get_worksheets(self):
        try:
            spreadsheet = self.client.open("mini_congress")
            national_ws = spreadsheet.worksheet("national_wk")
            manual_ws = spreadsheet.worksheet("manual_wk")
            st.success("Database Connected!")
            return national_ws, manual_ws
        except Exception as e:
            st.error(f"Worksheet access failed: {e}")
            st.stop()
    
    @st.cache_data(ttl=60, show_spinner="Loading participant data...")
    def load_and_clean_data(_self):
        try:
            # Load both worksheets
            national_records = _self.national_ws.get_all_records()
            manual_records = _self.manual_ws.get_all_records()
            
            # Create DataFrames and combine
            national_df = pd.DataFrame(national_records)
            manual_df = pd.DataFrame(manual_records)
            combined_df = pd.concat([national_df, manual_df], ignore_index=True)
            
            if combined_df.empty:
                st.error("No data found in the Google Sheets")
                st.stop()
                
            # Normalize column names - handle variations
            combined_df.columns = [col.strip().title().replace('  ', ' ') for col in combined_df.columns]
            
            # Map common variants to standard column names
            column_mapping = {
                'Regstatus': 'Registration Status',
                'Reg Status': 'Registration Status',
                'Status': 'Registration Status',
                'Confirmationstatus': 'Registration Status',
                'Confirmstatus': 'Registration Status',
                'Confirmtime': 'Confirmation Time',
                'Confirm Time': 'Confirmation Time',
                'Confirmdate': 'Confirmation Time',
                'Contactinfo': 'Contact',
                'Contact Info': 'Contact',
                'Phone': 'Contact',
                'Designation': 'Designation Level',
                'Designationlevel': 'Designation Level',
                'Pos': 'Position',
                'Post': 'Position',
                'Div': 'Division',
                'Dept': 'Division',
                'Gender': 'Gender',
                'Sex': 'Gender'
            }
            
            # Apply column name mapping
            combined_df.rename(columns=column_mapping, inplace=True)
            
            # Add default columns if missing
            required_columns = {
                'Region': '',
                'Division': '',
                'Designation Level': '',
                'Name': '',
                'Gender': '',
                'Position': '',
                'Contact': '',
                'Registration Status': '',  # Keep empty until confirmed
                'Confirmation Time': ''
            }
            
            for col, default_val in required_columns.items():
                if col not in combined_df.columns:
                    combined_df[col] = default_val
            
            # Convert all columns to string to avoid ArrowTypeError
            text_columns = ['Region', 'Division', 'Designation Level', 'Name', 
                           'Gender', 'Position', 'Contact', 'Registration Status']
            
            for col in text_columns:
                if col in combined_df.columns:
                    combined_df[col] = combined_df[col].astype(str)
            
            # Convert registration status to consistent format
            if 'Registration Status' in combined_df.columns:
                combined_df['Registration Status'] = (
                    combined_df['Registration Status']
                    .str.strip()
                    .str.title()
                    .replace({'Nan': '', 'Na': '', 'None': '', '': ''})
                )
            else:
                combined_df['Registration Status'] = ''
            
            return combined_df
        
        except Exception as e:
            st.error(f"Data loading failed: {e}")
            st.stop()
    
    def build_metrics(self):
        st.subheader("📊 Registration Dashboard")
        with st.container(border=True):
            cols = st.columns(3)
            
            # Calculate metrics
            total_participants = len(self.df)
            
            # Count confirmed participants (non-empty status)
            confirmed_count = self.df[self.df['Registration Status'] == 'Confirmed'].shape[0]
            
            # Count unconfirmed as those with empty status
            unconfirmed_count = total_participants - confirmed_count
            confirmation_rate = (confirmed_count / total_participants) * 100 if total_participants else 0
            
            # Gender breakdown (only confirmed participants)
            confirmed_df = self.df[self.df['Registration Status'] == 'Confirmed']
            gender_counts = confirmed_df['Gender'].value_counts()
            male_count = gender_counts.get('Male', 0)
            female_count = gender_counts.get('Female', 0)
            
            with cols[0]:
                st.metric("Total Participants", total_participants)
                st.progress(100, text="All registrations")
                
            with cols[1]:
                st.metric("Confirmed", f"{confirmed_count} ({confirmation_rate:.1f}%)")
                st.progress(int(confirmation_rate), text="Confirmation rate")
                
            with cols[2]:
                st.metric("Gender (M/F)", f"{male_count}/{female_count}")
                progress_value = int((male_count / confirmed_count * 100) if confirmed_count else 0)
                st.progress(progress_value, text=f"Male: {male_count}")
    
    def build_filters(self):
        st.subheader("🔍 Participant Search")
        with st.container(border=True):
            # Create two columns layout
            filter_col1, filter_col2 = st.columns([1, 1])
            
            # Region filter - always shown at top
            region_options = ['All Regions'] + sorted(self.df['Region'].dropna().unique().tolist())
            selected_region = st.selectbox("Filter by Region:", region_options)
            
            # Create two columns for search type and search input
            col1, col2 = st.columns([1, 3])
            
            # Search type selection - only Name or Contact
            with col1:
                self.search_type = st.selectbox("Search by:", ['Name', 'Contact'])
            
            # Search input
            with col2:
                self.search_term = st.text_input("Search term:", placeholder=f"Enter {self.search_type} to search")
            
            # Apply region filter first
            if selected_region != 'All Regions':
                self.filtered_df = self.df[self.df['Region'] == selected_region].copy()
            else:
                self.filtered_df = self.df.copy()
            
            # Apply search filter if search term is provided
            if self.search_term:
                try:
                    # Extract search series and convert to string
                    search_series = self.filtered_df[self.search_type].astype(str)
                    
                    # Get matches using vectorized processing
                    matches = process.extract(
                        self.search_term.lower(),
                        search_series.str.lower(),
                        scorer=fuzz.partial_ratio,
                        score_cutoff=80,
                        limit=None
                    )
                    
                    if matches:
                        # Create DataFrame from matches
                        match_df = pd.DataFrame(matches, columns=['match', 'score', 'index'])
                        # Filter and sort
                        self.filtered_df = self.filtered_df.loc[match_df['index']]
                        self.filtered_df = self.filtered_df.assign(match_score=match_df['score'].values)
                        self.filtered_df = self.filtered_df.sort_values('match_score', ascending=False)
                    else:
                        self.filtered_df = pd.DataFrame()  # No matches found
                        
                except Exception as e:
                    st.error(f"Search error: {str(e)}")
    
    def display_results(self):
        st.subheader(f"👥 Participants ({len(self.filtered_df)})")
        with st.container(border=True):
            # Row styling function: Only color "Registration Status" column
            def style_registration_status(val):
                if val == 'Confirmed':
                    return 'background-color: #d4edda'
                elif not val or val.strip() == '':  # Empty status (unconfirmed)
                    return 'background-color: #f8d7da'
                return ''

            # Display results
            if not self.filtered_df.empty:
                display_cols = ['Name', 'Gender', 'Region', 'Position', 'Registration Status']
                
                # Prepare dataframe to display - show "Unconfirmed" for empty status
                display_df = self.filtered_df[display_cols].copy()
                display_df['Registration Status'] = display_df['Registration Status'].replace('', 'Unconfirmed')
                
                # Apply styling
                styled_df = display_df.style.map(
                    style_registration_status, subset=['Registration Status']
                )
                
                st.dataframe(
                    styled_df,
                    height=400,
                    use_container_width=True
                )
            else:
                st.warning("No participants found matching your criteria")
        
    def confirmation_section(self):
        st.subheader("✅ Confirm Registration")
        tab1, tab2 = st.tabs(["Individual Confirmation", "Bulk Confirmation"])
        
        with tab1:
            self.individual_confirmation()
        
        with tab2:
            self.bulk_confirmation()
    
    def individual_confirmation(self):
        """Confirm participants one by one"""
        with st.container(border=True):
            # Get unconfirmed participants (empty status) from filtered results
            unconfirmed_df = self.filtered_df[
                (self.filtered_df['Registration Status'] != 'Confirmed') & 
                (self.filtered_df['Registration Status'].isna() | 
                 (self.filtered_df['Registration Status'] == ''))
            ]
            
            if not unconfirmed_df.empty:
                # Participant selection
                participant_list = unconfirmed_df['Name'].tolist()
                self.selected_name = st.selectbox("Select participant to confirm:", participant_list)
                
                # Display details
                participant = unconfirmed_df[unconfirmed_df['Name'] == self.selected_name].iloc[0]
                
                with st.expander("Participant Details:"):
                    st.write(f"**Name:** {participant['Name']}")
                    st.write(f"**Gender:** {participant['Gender']}")
                    st.write(f"**Position:** {participant.get('Position', '')}")
                    st.write(f"**Division:** {participant.get('Division', '')}")
                    st.write(f"**Region:** {participant.get('Region', '')}")
                    st.write(f"**Contact:** {participant.get('Contact', '')}")
                    st.write(f"**Status:** Unconfirmed")  # Always unconfirmed in this section
                
                # Confirmation button
                if st.button("Confirm Registration", type="primary", key="individual_confirm"):
                    try:
                        # Update local DataFrame
                        idx = self.df.index[self.df['Name'] == self.selected_name].tolist()[0]
                        
                        # Only set status when confirming
                        self.df.at[idx, 'Registration Status'] = 'Confirmed'
                        self.df.at[idx, 'Confirmation Time'] = datetime.now().strftime("%a %d %b, %H:%M")
                        
                        # Update Google Sheets - both original worksheets
                        self.update_source_worksheets()
                        
                        # Clear cache to force refresh
                        st.cache_data.clear()
                        
                        # Success feedback
                        st.success(f"✅ {self.selected_name} confirmed successfully!")
                        time.sleep(1.0)
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Confirmation failed: {str(e)}")
            else:
                st.success("All participants in current view are already confirmed!")
    
    def bulk_confirmation(self):
        """Confirm multiple participants using a DataFrame with checkboxes"""
        with st.container(border=True):
            # Get all unconfirmed participants
            unconfirmed_df = self.df[
                (self.df['Registration Status'] != 'Confirmed') & 
                (self.df['Registration Status'].isna() | 
                 (self.df['Registration Status'] == ''))
            ]
            
            if unconfirmed_df.empty:
                st.success("All participants are already confirmed!")
                return
                
            # Grouping options
            group_type = st.radio("Group by:", ["Region", "Division"], horizontal=True)
            
            # Get unique groups
            if group_type == "Region":
                group_options = ['All Regions'] + sorted(unconfirmed_df['Region'].dropna().unique().tolist())
            else:
                group_options = ['All Divisions'] + sorted(unconfirmed_df['Division'].dropna().unique().tolist())
            
            # Group selection
            selected_group = st.selectbox(f"Select {group_type}:", group_options)
            
            # Filter participants by selected group
            if selected_group.startswith('All'):
                group_participants = unconfirmed_df
            else:
                if group_type == "Region":
                    group_participants = unconfirmed_df[unconfirmed_df['Region'] == selected_group]
                else:
                    group_participants = unconfirmed_df[unconfirmed_df['Division'] == selected_group]
            
            if group_participants.empty:
                st.info(f"No unconfirmed participants in {selected_group}")
                return
                
            # Show participants count
            st.info(f"Found {len(group_participants)} unconfirmed participants in {selected_group}")
            
            # Prepare DataFrame for editing with checkboxes
            display_df = group_participants[['Name', 'Region', 'Division', 'Position']].copy()
            display_df['Select'] = False  # Initialize all as unselected
            
            # Reset index to use as identifier
            display_df = display_df.reset_index()
            
            # Create data editor with checkbox column
            st.write("Select participants to confirm:")
            edited_df = st.data_editor(
                display_df,
                column_config={
                    "index": st.column_config.Column("ID", disabled=True),
                    "Select": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select participants to confirm",
                        default=False,
                    ),
                    "Name": st.column_config.Column("Name", disabled=True),
                    "Region": st.column_config.Column("Region", disabled=True),
                    "Division": st.column_config.Column("Division", disabled=True),
                    "Position": st.column_config.Column("Position", disabled=True),
                },
                hide_index=True,
                use_container_width=True,
                height=min(400, 35 * len(display_df) + 40),
                key=f"bulk_editor_{selected_group}"
            )
            
            # Count selected participants
            selected_count = edited_df['Select'].sum()
            st.write(f"Selected: {selected_count} participants")
            
            # Confirmation button
            if st.button("Confirm Selected Participants", type="primary", key="bulk_confirm"):
                if selected_count == 0:
                    st.warning("Please select at least one participant")
                    return
                    
                try:
                    # Get selected indices
                    selected_indices = edited_df[edited_df['Select']]['index'].tolist()
                    
                    # Update selected participants
                    for idx in selected_indices:
                        self.df.at[idx, 'Registration Status'] = 'Confirmed'
                        self.df.at[idx, 'Confirmation Time'] = datetime.now().strftime("%a %d %b, %H:%M")
                    
                    # Update Google Sheets
                    self.update_source_worksheets()
                    
                    # Clear cache to force refresh
                    st.cache_data.clear()
                    
                    st.success(f"✅ Confirmed {len(selected_indices)} participants successfully!")
                    time.sleep(1.5)
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Bulk confirmation failed: {str(e)}")
    
    def update_source_worksheets(self):
        """Update both source worksheets with cleaned data"""
        try:
            # Get original record counts
            national_records = self.national_ws.get_all_records()
            manual_records = self.manual_ws.get_all_records()
            
            # Split dataframe using original counts
            national_count = len(national_records)
            manual_count = len(manual_records)
            
            # Ensure we don't go beyond dataframe length
            if len(self.df) < national_count + manual_count:
                # Handle case where dataframe is smaller than expected
                national_df = self.df.iloc[:min(national_count, len(self.df))].copy()
                manual_df = self.df.iloc[min(national_count, len(self.df)):].copy()
            else:
                national_df = self.df.iloc[:national_count].copy()
                manual_df = self.df.iloc[national_count:national_count+manual_count].copy()
            
            # Remove temporary columns before updating
            for df in [national_df, manual_df]:
                if 'match_score' in df.columns:
                    df.drop(columns=['match_score'], inplace=True)
            
            # Convert all text columns to string before updating
            text_columns = ['Region', 'Division', 'Designation Level', 'Name', 
                           'Gender', 'Position', 'Contact', 'Registration Status']
            for col in text_columns:
                if col in national_df.columns:
                    national_df[col] = national_df[col].astype(str)
                if col in manual_df.columns:
                    manual_df[col] = manual_df[col].astype(str)
            
            # Update national worksheet
            self.national_ws.clear()
            self.national_ws.update([national_df.columns.tolist()] + national_df.values.tolist())
            
            # Update manual worksheet
            self.manual_ws.clear()
            self.manual_ws.update([manual_df.columns.tolist()] + manual_df.values.tolist())
            
        except Exception as e:
            st.error(f"Worksheet update failed: {str(e)}")
            raise
        
    def build_footer(self):
        st.divider()
        st.caption(f"DCLM Registration Dashboard v1.0 | Data updated at: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    def run(self):
        self.build_metrics()
        self.build_filters()
        self.display_results()
        self.confirmation_section()
        self.build_footer()

# Run the application
if __name__ == "__main__":
    RegistrationDashboard().run()