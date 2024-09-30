import streamlit as st
import plotly.express as px
import pandas as pd
import os
import warnings
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
    else:
        df = pd.read_excel(fl)  # Handle Excel files

    # Strip spaces and lowercase all column names for consistency
    df.columns = df.columns.str.strip().str.lower()

    # Check if 'date' column exists and convert to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        st.error("The 'Date' column is missing in the dataset.")
        st.stop()  # Stop execution if 'Date' column is missing

else:
    # Local loading as a fallback
    os.chdir(r"C:\path_to_your_file")
    df = pd.read_csv("your_file.csv", encoding="ISO-8859-1")
    df.columns = df.columns.str.strip().str.lower()
    df['date'] = pd.to_datetime(df['date'])

# Layout for Date selection
col1, col2 = st.columns(2)
startDate = pd.to_datetime(df["date"]).min()
endDate = pd.to_datetime(df["date"]).max()

with col1:
    date1 = pd.to_datetime(st.date_input("Start Date", startDate))

with col2:
    date2 = pd.to_datetime(st.date_input("End Date", endDate))

# Filter data based on date
df = df[(df["date"] >= date1) & (df["date"] <= date2)].copy()

# Sidebar filters
st.sidebar.header("Choose your filter: ")

# Filter by Shift
shift = st.sidebar.multiselect("Select Shift", df["shift"].unique())
if not shift:
    df_filtered = df.copy()
else:
    df_filtered = df[df["shift"].isin(shift)]

# Filter by Dump Truck
dump_truck = st.sidebar.multiselect("Select Dump Truck", df_filtered["dump truck"].unique())
if dump_truck:
    df_filtered = df_filtered[df_filtered["dump truck"].isin(dump_truck)]

# Filter by Excavator (Exca)
exca = st.sidebar.multiselect("Select Excavator", df_filtered["exca"].unique())
if exca:
    df_filtered = df_filtered[df_filtered["exca"].isin(exca)]

# Filter by Loading Point and Dumping Point
loading_point = st.sidebar.multiselect("Select Loading Point", df_filtered["loading point"].unique())
if loading_point:
    df_filtered = df_filtered[df_filtered["loading point"].isin(loading_point)]

dumping_point = st.sidebar.multiselect("Select Dumping Point", df_filtered["dumping point"].unique())
if dumping_point:
    df_filtered = df_filtered[df_filtered["dumping point"].isin(dumping_point)]

# Check if 'target' column exists in dataset
if 'target' in df_filtered.columns:
    st.sidebar.write("Target data is available in the dataset.")
else:
    st.error("The 'target' column is missing in the dataset.")
    st.stop()

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

csv = target_df.to_csv(index=False).encode('utf-8')
st.download_button("Download Target Comparison Data", data=csv, file_name="Target_comparison_data.csv", mime="text/csv")

# Download full dataset
csv = df.to_csv(index=False).encode('utf-8')
st.download_button('Download Full Dataset', data=csv, file_name="rehandling_batubara_data.csv", mime='text/csv')
