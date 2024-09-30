import os
import warnings
import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np

# Suppress warnings
warnings.filterwarnings('ignore')

# Streamlit page configuration
st.set_page_config(page_title="Rehandling Batubara Dashboard", page_icon=":bar_chart:", layout="wide")
st.markdown(
    """
    <style>
    .title {
        margin-top: 50px;
    }
    </style>
    """,
    unsafe_allow_html=True
)
st.title(" :bar_chart: Rehandling Batubara Data Exploration")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

fl = st.file_uploader(":file_folder: Upload a file", type=(["csv","xlsx"]))
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

    def get_value_by_status(df, status_name):

        rows = df[df['status'] == status_name]
        if not rows.empty:
            return float(rows['tonase'].sum())
        else:
            return 0.00


        
# Layout for Date selection
col1, col2 = st.columns(2)
startDate = df['date'].min()
endDate = df['date'].max()

with col1:
    date1 = st.date_input("Start Date", startDate)

with col2:
    date2 = st.date_input("End Date", endDate)

# Validasi tanggal
if date1 > date2:
    st.error("Tanggal awal tidak boleh lebih besar dari tanggal akhir.")
    st.stop()

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

# Sidebar input for target rakor (bulanan)
st.sidebar.header("Input Target Rakor Bulanan:")
rakor_targets = {
    'FOB MV': st.sidebar.number_input("Target FOB MV (masukkan nilai target)", value=get_value_by_status(df, 'FOB MV'), step=0.01),
    'Rehandling Blok Timur': st.sidebar.number_input("Target Rehandling Blok Timur (masukkan nilai target)", value=get_value_by_status(df, 'Rehandling Blok Timur'), step=0.01),
    'Rehandling Antar Stock Blok Barat': st.sidebar.number_input("Target Rehandling Antar Stock Blok Barat (masukkan nilai target)", value=get_value_by_status(df, 'Rehandling Antar Stock Blok Barat'), step=0.01),
    'Rehandling Antar Stock Blok Timur': st.sidebar.number_input("Target Rehandling Antar Stock Blok Timur (masukkan nilai target)", value=get_value_by_status(df, 'Rehandling Antar Stock Blok Timur'), step=0.01),
    'Rehandling Blok Barat': st.sidebar.number_input("Target Rehandling Blok Barat (masukkan nilai target)", value=get_value_by_status(df, 'Rehandling Blok Barat'), step=0.01),
    'Houskeeping': st.sidebar.number_input("Target Housekeeping (masukkan nilai target)", value=get_value_by_status(df, 'Houskeeping'), step=0.01),
    'Pengiriman konsumen': st.sidebar.number_input("Target Pengiriman konsumen (masukkan nilai target)", value=get_value_by_status(df, 'Pengiriman konsumen'), step=0.01)
}

# Map target rakor to dataset
if 'status' in df_filtered.columns:
    df_filtered['target_rakor'] = df_filtered['status'].map(rakor_targets).fillna(0)  # Mengisi nilai NaN dengan 0
else:
    st.error("Kolom 'status' tidak ditemukan dalam dataset.")


# Input tanggal awal dan akhir untuk menentukan periode rakor
st.sidebar.header("Input Periode Rakor:")
start_date = st.sidebar.date_input("Tanggal Mulai")
end_date = st.sidebar.date_input("Tanggal Akhir")

# Hitung jumlah hari pada bulan yang dipilih
if start_date and end_date:
    num_days_rakor = (end_date - start_date).days + 1
    if num_days_rakor > 0:
        st.sidebar.write(f"Total hari dalam periode rakor: {num_days_rakor} hari")
        
        st.sidebar.header("Pembagian Target Rakor:")
        for key, value in rakor_targets.items():
            target_harian = value / num_days_rakor  
            target_mingguan = target_harian * 7  
            st.sidebar.write(f"{key}:")
            st.sidebar.write(f"- Target Harian: {target_harian:,.2f}")
            st.sidebar.write(f"- Target Mingguan: {target_mingguan:,.2f}")
            st.sidebar.write(f"- Target Bulanan: {value:,.2f}")
    else:
        st.sidebar.write("Periode yang dipilih tidak valid. Pastikan tanggal akhir lebih besar dari tanggal mulai.")
else:
    st.sidebar.write("Silakan masukkan periode rakor yang valid.")

# Sidebar for input target SPPH/Mitra
st.sidebar.header("Input Target SPPH/Mitra:")
spph_mitra_targets = {}
for spph_mitra in df_filtered['spph'].unique():
    spph_mitra_targets[spph_mitra] = st.sidebar.number_input(f"Target for {spph_mitra} (masukkan nilai target)", min_value=0, value=0)  # Minimal value diatur ke 0

# Map target SPPH/Mitra to dataset
if 'spph' in df_filtered.columns:
    df_filtered['target_spph_mitra'] = df_filtered['spph'].map(spph_mitra_targets).fillna(0)  # Mengisi nilai NaN dengan 0
else:
    st.error("Kolom 'SPPH' tidak ditemukan dalam dataset.")

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

# Target Rakor Analysis
st.subheader("Target Rakor vs Actual Comparison")

# Grouping and aggregation
rakor_df = df_filtered.groupby("status", as_index=False).agg({"tonase": "sum", "target_rakor": "first"})
rakor_df["difference"] = rakor_df["target_rakor"] - rakor_df["tonase"]
rakor_df["percent achievement"] = (rakor_df["tonase"] / rakor_df["target_rakor"]).replace([np.inf, -np.inf], 0).fillna(0) * 100  # Pastikan tidak ada pembagian dengan 0


rakor_df.index = range(1, len(rakor_df) + 1)
# Display the DataFrame
st.dataframe(rakor_df)

# Visualisasi perbandingan target rakor dan tonase aktual
fig_rakor = px.bar(rakor_df, x="status", y=["target_rakor", "tonase"], barmode="group", text_auto=True, template="seaborn")
st.plotly_chart(fig_rakor, use_container_width=True)

# Total Target Rakor dan Total Tonase
total_target_rakor = rakor_df["target_rakor"].sum()
total_tonase = rakor_df["tonase"].sum()
total_difference = total_target_rakor - total_tonase
total_percent_achievement = (total_tonase / total_target_rakor) * 100 if total_target_rakor != 0 else 0

# Tampilkan total
st.write("### Total Target Rakor dan Tonase")
st.metric(label="Total Target Rakor", value=f"{total_target_rakor:,.2f} Ton")
st.metric(label="Total Tonase", value=f"{total_tonase:,.2f} Ton")
st.metric(label="Perbedaan (Target - Aktual)", value=f"{total_difference:,.2f} Ton")
st.metric(label="Persentase Pencapaian Rakor", value=f"{total_percent_achievement:.2f}%")

# Target SPPH/Mitra Analysis
st.subheader("Target SPPH/Mitra vs Actual Comparison")
spph_mitra_df = df_filtered.groupby("spph", as_index=False).agg({"tonase": "sum", "target_spph_mitra": "first"})
spph_mitra_df["difference"] = spph_mitra_df["target_spph_mitra"] - spph_mitra_df["tonase"]
spph_mitra_df["percent achievement"] = (spph_mitra_df["tonase"] / spph_mitra_df["target_spph_mitra"]) * 100

spph_mitra_df.index = range(1, len(spph_mitra_df) + 1)
st.dataframe(spph_mitra_df)

# Visualisasi perbandingan target SPPH/Mitra dan tonase aktual
fig_spph_mitra = px.bar(spph_mitra_df, x="spph", y=["target_spph_mitra", "tonase"], barmode="group", text_auto=True, template="seaborn")
st.plotly_chart(fig_spph_mitra, use_container_width=True)

# Total Target SPPH/Mitra dan Total Tonase
total_target_spph_mitra = spph_mitra_df["target_spph_mitra"].sum()
total_tonase_spph_mitra = spph_mitra_df["tonase"].sum()
total_difference_spph_mitra = total_target_spph_mitra - total_tonase_spph_mitra
total_percent_achievement_spph_mitra = (total_tonase_spph_mitra / total_target_spph_mitra) * 100 if total_target_spph_mitra != 0 else 0

# Tampilkan total SPPH/Mitra
st.write("### Total Target SPPH/Mitra dan Tonase")
st.metric(label="Total Target SPPH/Mitra", value=f"{total_target_spph_mitra:,.2f} Ton")
st.metric(label="Total Tonase SPPH/Mitra", value=f"{total_tonase_spph_mitra:,.2f} Ton")
st.metric(label="Perbedaan (Target - Aktual)", value=f"{total_difference_spph_mitra:,.2f} Ton")
st.metric(label="Persentase Pencapaian SPPH/Mitra", value=f"{total_percent_achievement_spph_mitra:.2f}%")

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
