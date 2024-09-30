import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Streamlit page configuration
st.set_page_config(page_title="Rehandling Batubara Dashboard", page_icon=":bar_chart:", layout="wide")

st.title(" :bar_chart: Rehandling Batubara Data Exploration")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# File uploader for the data
fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"]))
if fl is not None:
    filename = fl.name
    st.write(filename)

    # Check file extension and load accordingly
    if filename.endswith('.csv') or filename.endswith('.txt'):
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        df = pd.read_excel(fl)  # Handle Excel files
    else:
        st.error("Unsupported file type. Please upload a CSV or Excel file.")
        st.stop()  # Stop execution if the file type is not supported

    # Strip spaces and lowercase all column names for consistency
    df.columns = df.columns.str.strip().str.lower()

    # Check if 'date' column exists and convert to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        st.error("The 'Date' column is missing in the dataset.")
        st.stop()  # Stop execution if 'Date' column is missing

# Layout for Date selection
col1, col2 = st.columns(2)
startDate = df['date'].min()
endDate = df['date'].max()

with col1:
    date1 = st.date_input("Start Date", startDate)

with col2:
    date2 = st.date_input("End Date", endDate)

# Filter data based on date
df = df[(df["date"] >= pd.to_datetime(date1)) & (df["date"] <= pd.to_datetime(date2))].copy()

# Sidebar filters
st.sidebar.header("Choose your filter: ")

# Filter by Shift
shift = st.sidebar.multiselect("Select Shift", df["shift"].unique())
df_filtered = df[df["shift"].isin(shift)] if shift else df.copy()

# Filter by Dump Truck
dump_truck = st.sidebar.multiselect("Select Dump Truck", df_filtered["dump truck"].unique())
df_filtered = df_filtered[df_filtered["dump truck"].isin(dump_truck)] if dump_truck else df_filtered

# Filter by Excavator (Exca)
exca = st.sidebar.multiselect("Select Excavator", df_filtered["exca"].unique())
df_filtered = df_filtered[df_filtered["exca"].isin(exca)] if exca else df_filtered

# Filter by Loading Point and Dumping Point
loading_point = st.sidebar.multiselect("Select Loading Point", df_filtered["loading point"].unique())
df_filtered = df_filtered[df_filtered["loading point"].isin(loading_point)] if loading_point else df_filtered

dumping_point = st.sidebar.multiselect("Select Dumping Point", df_filtered["dumping point"].unique())
df_filtered = df_filtered[df_filtered["dumping point"].isin(dumping_point)] if dumping_point else df_filtered

# Input target manually for each shift
st.sidebar.header("Input Target per Shift:")
shift_targets = {}
for s in df["shift"].unique():
    shift_targets[s] = st.sidebar.number_input(f"Target for {s}", value=1000)

# Add target column to filtered dataframe
df_filtered['target'] = df_filtered['shift'].map(shift_targets)

# Tonase and SPPH Analysis
col1, col2 = st.columns(2)

# Category-wise (SPPH) bar chart
with col1:
    st.subheader("SPPH Analysis")
    spph_df = df_filtered.groupby("spph", as_index=False)["tonase"].sum()
    fig = px.bar(spph_df, x="spph", y="tonase", text=['{:,.2f}'.format(x) for x in spph_df["tonase"]], template="seaborn")
    st.plotly_chart(fig, use_container_width=True)

# Shift-wise tonnage pie chart
with col2:
    st.subheader("Shift-wise Tonage")
    fig = px.pie(df_filtered, values="tonase", names="shift", hole=0.5)
    st.plotly_chart(fig, use_container_width=True)

# Target Analysis
st.subheader("Target vs Actual Comparison")
target_df = df_filtered.groupby("shift", as_index=False).agg({"tonase": "sum", "target": "sum"})
target_df["difference"] = target_df["target"] - target_df["tonase"]
target_df["percent achievement"] = (target_df["tonase"] / target_df["target"]) * 100

st.write(target_df.style.background_gradient(cmap="Greens"))

fig4 = px.bar(target_df, x="shift", y=["target", "tonase"], barmode="group", text_auto=True, template="seaborn")
st.plotly_chart(fig4, use_container_width=True)

# Jam Dumping Analysis
if 'jam dumping' in df_filtered.columns:
    st.subheader("Jam Dumping Analysis")
    
    try:
        # Concatenate 'date' and 'jam dumping' to handle the case where time crosses midnight
        df_filtered['datetime_dumping'] = pd.to_datetime(df_filtered['date'].astype(str) + ' ' + df_filtered['jam dumping'], errors='coerce')

        # Handle rows where 'datetime_dumping' is still NaT (could be format issues)
        if df_filtered['datetime_dumping'].isnull().any():
            st.warning("Some 'Jam Dumping' values could not be parsed. Ensure the data is in 'HH:MM' format.")
        else:
            # Extract the hour for grouping (24-hour format)
            df_filtered['hour'] = df_filtered['datetime_dumping'].dt.hour
            
            # Group by the 'hour' column and calculate the sum of 'tonase'
            jam_dumping_df = df_filtered.groupby("hour", as_index=False)["tonase"].sum()

            # Create missing hours (0-23) to ensure completeness in the visualization
            all_hours = pd.DataFrame({'hour': range(24)})
            jam_dumping_df = pd.merge(all_hours, jam_dumping_df, on='hour', how='left').fillna(0)

            # Line chart visualization (grouped by hour)
            fig_jam_dumping = px.line(jam_dumping_df, x="hour", y="tonase", 
                                      title='Jam Dumping (Grouped by Hour) vs Tonase',
                                      labels={'hour': 'Jam Dumping (Hour)', 'tonase': 'Total Tonase'},
                                      template="seaborn")
            
            # Display the line chart
            st.plotly_chart(fig_jam_dumping, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error parsing 'Jam Dumping' column: {e}")

else:
    st.warning("The 'Jam Dumping' column is missing in the dataset.")

# Download options
csv_target = target_df.to_csv(index=False).encode('utf-8')
st.download_button("Download Target Comparison Data", data=csv_target, file_name="Target_comparison_data.csv", mime="text/csv")

csv_full = df.to_csv(index=False).encode('utf-8')
st.download_button('Download Full Dataset', data=csv_full, file_name="rehandling_batubara_data.csv", mime='text/csv')
