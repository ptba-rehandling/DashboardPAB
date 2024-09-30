import streamlit as st
import plotly.express as px
import pandas as pd
import warnings

# Suppress warnings
warnings.filterwarnings('ignore')

# Streamlit page configuration
st.set_page_config(page_title="Rehandling Batubara Dashboard", page_icon=":bar_chart:", layout="wide")

# Title
st.title(" :bar_chart: Rehandling Batubara Data Exploration")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

# File uploader for the data
fl = st.file_uploader(":file_folder: Upload a file", type=(["csv", "txt", "xlsx", "xls"]))
if fl is not None:
    filename = fl.name
    st.write(filename)

    # Load the data based on file extension
    if filename.endswith('.csv') or filename.endswith('.txt'):
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        df = pd.read_excel(fl)  
    else:
        st.error("Unsupported file type. Please upload a CSV or Excel file.")
        st.stop()

    # Prepare data
    df.columns = df.columns.str.strip().str.lower()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        st.error("The 'Date' column is missing in the dataset.")
        st.stop()

# Layout for date selection
col1, col2 = st.columns(2)
startDate = df['date'].min()
endDate = df['date'].max()

with col1:
    date1 = st.date_input("Start Date", startDate)

with col2:
    date2 = st.date_input("End Date", endDate)

# Validate date range
if date1 > date2:
    st.error("Start date cannot be later than end date.")
    st.stop()

# Filter data based on date range
df = df[(df["date"] >= pd.to_datetime(date1)) & (df["date"] <= pd.to_datetime(date2))].copy()

# Sidebar filters
st.sidebar.header("Choose your filter:")
shift = st.sidebar.multiselect("Select Shift", df["shift"].unique())
df_filtered = df[df["shift"].isin(shift)] if shift else df.copy()

dump_truck = st.sidebar.multiselect("Select Dump Truck", df_filtered["dump truck"].unique())
df_filtered = df_filtered[df_filtered["dump truck"].isin(dump_truck)] if dump_truck else df_filtered

exca = st.sidebar.multiselect("Select Excavator", df_filtered["exca"].unique())
df_filtered = df_filtered[df_filtered["exca"].isin(exca)] if exca else df_filtered

loading_point = st.sidebar.multiselect("Select Loading Point", df_filtered["loading point"].unique())
df_filtered = df_filtered[df_filtered["loading point"].isin(loading_point)] if loading_point else df_filtered

dumping_point = st.sidebar.multiselect("Select Dumping Point", df_filtered["dumping point"].unique())
df_filtered = df_filtered[df_filtered["dumping point"].isin(dumping_point)] if dumping_point else df_filtered

# Input target manually for each shift
st.sidebar.header("Input Target per Shift:")
shift_targets = {s: st.sidebar.number_input(f"Target for {s}", value=1000) for s in df["shift"].unique()}
df_filtered['target'] = df_filtered['shift'].map(shift_targets)

# Sidebar for input target rakor per status
st.sidebar.header("Input Target Rakor:")
rakor_targets = {
    'FOB MV': st.sidebar.number_input("Target FOB MV", value=1000),
    'Rehandling Blok Timur': st.sidebar.number_input("Target Rehandling Blok Timur", value=1000),
    'Rehandling Antar Stock Blok Barat': st.sidebar.number_input("Target Rehandling Antar Stock Blok Barat", value=1000),
    'Rehandling Antar Stock Blok Timur': st.sidebar.number_input("Target Rehandling Antar Stock Blok Timur", value=1000),
    'Rehandling Blok Barat': st.sidebar.number_input("Target Rehandling Blok Barat", value=1000),
    'Housekeeping': st.sidebar.number_input("Target Housekeeping", value=1000),
    'Pengiriman konsumen': st.sidebar.number_input("Target Pengiriman konsumen", value=1000)
}
if 'status' in df_filtered.columns:
    df_filtered['target_rakor'] = df_filtered['status'].map(rakor_targets)
else:
    st.error("Kolom 'status' tidak ditemukan dalam dataset.")

# Filter tanggal untuk target rakor
st.sidebar.header("Pilih Periode Target Rakor:")
rakor_start = st.sidebar.date_input("Start Date for Target Rakor", date1)
rakor_end = st.sidebar.date_input("End Date for Target Rakor", date2)

# Validate rakor date range
if rakor_start > rakor_end:
    st.error("Start date for target rakor cannot be later than end date.")
    st.stop()

num_days_rakor = (pd.to_datetime(rakor_end) - pd.to_datetime(rakor_start)).days + 1
st.sidebar.write(f"Jumlah hari dalam rentang target rakor: {num_days_rakor} hari")

# Input manual for daily rakor targets
st.sidebar.header("Input Target Harian Rakor:")
rakor_daily_targets = {key: st.sidebar.number_input(f"Target harian untuk {key}", value=value/num_days_rakor) for key, value in rakor_targets.items()}
st.sidebar.write("Target harian rakor:")
for key, value in rakor_daily_targets.items():
    st.sidebar.write(f"{key}: {value:,.2f} per hari")

# Sidebar for input target SPPH/Mitra
st.sidebar.header("Input Target SPPH/Mitra:")
spph_mitra_targets = {spph_mitra: st.sidebar.number_input(f"Target for {spph_mitra}", value=1000) for spph_mitra in df_filtered['spph'].unique()}
if 'spph' in df_filtered.columns:
    df_filtered['target_spph_mitra'] = df_filtered['spph'].map(spph_mitra_targets)
else:
    st.error("Kolom 'SPPH' tidak ditemukan dalam dataset.")

# Analysis and visualizations
col1, col2 = st.columns(2)

# SPPH Analysis
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

# Target Rakor Analysis
st.subheader("Target Rakor vs Actual Comparison")
rakor_df = df_filtered.groupby("status", as_index=False).agg({"tonase": "sum", "target_rakor": "sum"})
rakor_df["difference"] = rakor_df["target_rakor"] - rakor_df["tonase"]
rakor_df["percent achievement"] = (rakor_df["tonase"] / rakor_df["target_rakor"]) * 100

st.write(rakor_df.style.background_gradient(cmap="Blues"))
fig_rakor = px.bar(rakor_df, x="status", y=["target_rakor", "tonase"], barmode="group", text_auto=True, template="seaborn")
st.plotly_chart(fig_rakor, use_container_width=True)

# Total Target Rakor and Total Tonase
total_target_rakor = rakor_df["target_rakor"].sum()
total_tonase = rakor_df["tonase"].sum()
total_difference = total_target_rakor - total_tonase
total_percent_achievement = (total_tonase / total_target_rakor) * 100 if total_target_rakor != 0 else 0

# Display total
st.write("### Total Target Rakor dan Tonase")
st.metric(label="Total Target Rakor", value=f"{total_target_rakor:,.2f} Ton")
st.metric(label="Total Tonase", value=f"{total_tonase:,.2f} Ton")
st.metric(label="Perbedaan (Target - Aktual)", value=f"{total_difference:,.2f} Ton")
st.metric(label="Persentase Pencapaian Rakor", value=f"{total_percent_achievement:.2f}%")

# Target SPPH/Mitra Analysis
st.subheader("Target SPPH/Mitra vs Actual Comparison")
spph_mitra_df = df_filtered.groupby("spph", as_index=False).agg({"tonase": "sum", "target_spph_mitra": "sum"})
spph_mitra_df["difference"] = spph_mitra_df["target_spph_mitra"] - spph_mitra_df["tonase"]
spph_mitra_df["percent achievement"] = (spph_mitra_df["tonase"] / spph_mitra_df["target_spph_mitra"]) * 100

st.write(spph_mitra_df.style.background_gradient(cmap="Blues"))
fig_spph_mitra = px.bar(spph_mitra_df, x="spph", y=["target_spph_mitra", "tonase"], barmode="group", text_auto=True, template="seaborn")
st.plotly_chart(fig_spph_mitra, use_container_width=True)

# Total Target SPPH/Mitra and Total Tonase
total_target_spph = spph_mitra_df["target_spph_mitra"].sum()
total_spph_tonase = spph_mitra_df["tonase"].sum()
total_spph_difference = total_target_spph - total_spph_tonase
total_spph_percent_achievement = (total_spph_tonase / total_target_spph) * 100 if total_target_spph != 0 else 0

# Display total for SPPH/Mitra
st.write("### Total Target SPPH/Mitra dan Tonase")
st.metric(label="Total Target SPPH/Mitra", value=f"{total_target_spph:,.2f} Ton")
st.metric(label="Total Tonase SPPH/Mitra", value=f"{total_spph_tonase:,.2f} Ton")
st.metric(label="Perbedaan SPPH/Mitra (Target - Aktual)", value=f"{total_spph_difference:,.2f} Ton")
st.metric(label="Persentase Pencapaian SPPH/Mitra", value=f"{total_spph_percent_achievement:.2f}%")

# Jam Dumping Analysis
if 'jam dumping' in df_filtered.columns:
    st.subheader("Jam Dumping Analysis")
    
    # Assume 'jam dumping' has format like "23:00", "00:15", "01:30", etc.
    try:
        # Concatenate 'date' and 'jam dumping' to handle the case where time crosses midnight
        df_filtered['datetime_dumping'] = pd.to_datetime(df_filtered['date'].astype(str) + ' ' + df_filtered['jam dumping'], errors='coerce')

        # Handle rows where 'datetime_dumping' is still NaT (could be format issues)
        if df_filtered['datetime_dumping'].isnull().any():
            st.warning(f"Total {df_filtered['datetime_dumping'].isnull().sum()} data 'Jam Dumping' gagal di-parse.")
        else:
            # Extract the hour for grouping (including the date to handle across midnight correctly)
            df_filtered['hour'] = df_filtered['datetime_dumping'].dt.hour
            
            # Group by the 'hour' column and calculate the sum of 'tonase'
            jam_dumping_df = df_filtered.groupby("hour", as_index=False)["tonase"].sum()

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
csv_rakor = rakor_df.to_csv(index=False).encode('utf-8')
st.download_button("Download Target Rakor Comparison Data", data=csv_rakor, file_name="Target_rakor_comparison_data.csv", mime="text/csv")

csv_full = df.to_csv(index=False).encode('utf-8')
st.download_button('Download Full Dataset', data=csv_full, file_name="rehandling_batubara_data.csv", mime='text/csv')