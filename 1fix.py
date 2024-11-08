import os
import warnings
import pandas as pd
import plotly.express as px
import streamlit as st
import numpy as np
import base64
import io
import os
import json
from PIL import Image
import plotly.graph_objs as go

# Suppress warnings
warnings.filterwarnings('ignore')

def get_base64_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode()

# Path to your local image
image_path = "assets/RBPab.png"
image_base64 = get_base64_image(image_path)

# Streamlit page configuration
st.set_page_config(
    page_title="Rehandling Batubara Dashboard", 
    page_icon=f"data:image/png;base64,{image_base64}", 
    layout="wide"
)

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

# Create the HTML with the base64 image embedded
st.markdown(
    f"""
    <div style="display: flex; align-items: center;margin-bottom: 40px;">
        <img src="data:image/png;base64,{image_base64}" alt="Logo" width="195" style="margin-right: 20px;">
        <h1>Rehandling Batubara Dashboard</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

fl = st.file_uploader(":file_folder: Upload a file", type=(["csv","xlsx"]))
if fl is not None:
    filename = fl.name
    st.write(filename)

    # Check file extension and load accordingly
    if filename.endswith('.csv') or filename.endswith('.txt'):
        df = pd.read_csv(fl, encoding="ISO-8859-1")
    elif filename.endswith('.xlsx') or filename.endswith('.xls'):
        # Membaca semua sheet dan menggabungkannya
        df = pd.concat(pd.read_excel(fl, sheet_name=None), ignore_index=True)
    else:
        st.error("Unsupported file type. Please upload a CSV or Excel file.")
        st.stop()  # Stop execution if the file type is not supported

    # Strip spaces and lowercase all column names for consistency
    df.columns = df.columns.str.strip().str.lower()

    # Check if 'date' column exists and convert to datetime
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    else:
        st.error("Kolom 'Date' tidak ditemukan dalam dataset.")
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

    # File paths for storing targets
    rakor_targets_file = 'rakor_targets.json'
    spph_mitra_targets_file = 'spph_mitra_targets.json'

    # Function to load target values from JSON
    def load_json(file_path):
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
        return {}

    # Function to save target values to JSON
    def save_json(file_path, data):
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)

    # Load existing rakor targets if available
    rakor_targets = load_json(rakor_targets_file)

    # Sidebar input for target rakor (bulanan)
    st.sidebar.header("Input Target Rakor Bulanan:")
    new_rakor_targets = {
        'FOB MV': st.sidebar.number_input("Target FOB MV (masukkan nilai target)", value=rakor_targets.get('FOB MV', get_value_by_status(df, 'FOB MV')), step=0.01),
        'Rehandling Blok Timur': st.sidebar.number_input("Target Rehandling Blok Timur (masukkan nilai target)", value=rakor_targets.get('Rehandling Blok Timur', get_value_by_status(df, 'Rehandling Blok Timur')), step=0.01),
        'Rehandling Antar Stock Blok Barat': st.sidebar.number_input("Target Rehandling Antar Stock Blok Barat (masukkan nilai target)", value=rakor_targets.get('Rehandling Antar Stock Blok Barat', get_value_by_status(df, 'Rehandling Antar Stock Blok Barat')), step=0.01),
        'Rehandling Antar Stock Blok Timur': st.sidebar.number_input("Target Rehandling Antar Stock Blok Timur (masukkan nilai target)", value=rakor_targets.get('Rehandling Antar Stock Blok Timur', get_value_by_status(df, 'Rehandling Antar Stock Blok Timur')), step=0.01),
        'Rehandling Blok Barat': st.sidebar.number_input("Target Rehandling Blok Barat (masukkan nilai target)", value=rakor_targets.get('Rehandling Blok Barat', get_value_by_status(df, 'Rehandling Blok Barat')), step=0.01),
        'Housekeeping': st.sidebar.number_input("Target Housekeeping (masukkan nilai target)", value=rakor_targets.get('Housekeeping', get_value_by_status(df, 'Housekeeping')), step=0.01),
        'Rehandling Pengiriman Konsumen': st.sidebar.number_input("Target Pengiriman Konsumen (masukkan nilai target)", value=rakor_targets.get('Rehandling Pengiriman Konsumen', get_value_by_status(df, 'Rehandling Pengiriman Konsumen')), step=0.01)
    }

    # Save the rakor targets to JSON after input
    save_json(rakor_targets_file, new_rakor_targets)

    # Map target rakor to dataset
    if 'status' in df_filtered.columns:
        df_filtered['target_rakor'] = df_filtered['status'].map(new_rakor_targets).fillna(0)
    else:
        st.error("Kolom 'status' tidak ditemukan dalam dataset.")

    # Input tanggal awal dan akhir untuk menentukan periode rakor
    st.sidebar.header("Input Periode Rakor:")
    start_date = st.sidebar.date_input("Tanggal Mulai", date1)
    end_date = st.sidebar.date_input("Tanggal Akhir", date2)

    # Logic for rakor target breakdown (unchanged)
    if start_date and end_date:
        num_days_rakor = (end_date - start_date).days + 1
        if num_days_rakor > 0:
            st.sidebar.write(f"Total hari dalam periode rakor: {num_days_rakor} hari")
            
            st.sidebar.header("Pembagian Target Rakor:")
            for key, value in new_rakor_targets.items():
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

    # Assign daily and weekly target rakor to the dataframe
    df_filtered['target_rakor_harian'] = df_filtered['target_rakor'] / num_days_rakor
    df_filtered['target_rakor_mingguan'] = df_filtered['target_rakor_harian'] * 7

    # Load existing SPPH/Mitra targets if available
    spph_mitra_targets = load_json(spph_mitra_targets_file)

    # Sidebar for input target SPPH/Mitra
    st.sidebar.header("Input Target SPPH/Mitra:")
    new_spph_mitra_targets = {}
    for spph_mitra in df_filtered['spph'].unique():
        new_spph_mitra_targets[spph_mitra] = st.sidebar.number_input(f"Target for {spph_mitra} (masukkan nilai target)", min_value=0.0, value=spph_mitra_targets.get(spph_mitra, 0.0), step=0.01)

    # Save the SPPH/Mitra targets to JSON after input
    save_json(spph_mitra_targets_file, new_spph_mitra_targets)

    # Map target SPPH/Mitra to dataset
    if 'spph' in df_filtered.columns:
        df_filtered['target_spph_mitra'] = df_filtered['spph'].map(new_spph_mitra_targets).fillna(0)
    else:
        st.error("Kolom 'SPPH' tidak ditemukan dalam dataset.")

    # Assign daily and weekly target SPPH/Mitra to the dataframe
    df_filtered['target_spph_mitra_harian'] = df_filtered['target_spph_mitra'] / num_days_rakor
    df_filtered['target_spph_mitra_mingguan'] = df_filtered['target_spph_mitra_harian'] * 7

    # Tonase and SPPH Analysis
    col1, col2 = st.columns(2)

    # Category-wise (SPPH) bar chart
    with col1:
        st.subheader("SPPH Analysis")
        
        # Grouping data by SPPH
        spph_df = df_filtered.groupby("spph", as_index=False)["tonase"].sum()

        # Menghitung SGJTotal dari penjumlahan SGJ1, SGJ2, SGJ3, dan SPARE
        sgj_total = spph_df[spph_df["spph"].isin(["SGJ1", "SGJ2", "SGJ3", "SPARE"])]["tonase"].sum()

        # Menambahkan SGJTotal ke dataframe
        sgj_total_row = pd.DataFrame({"spph": ["SGJTotal"], "tonase": [sgj_total]})
        spph_df = pd.concat([spph_df, sgj_total_row], ignore_index=True)

        # Menghitung Grand Total dari seluruh tonase kecuali SGJTotal
        grand_total = spph_df[spph_df["spph"] != "SGJTotal"]["tonase"].sum()

        # Menambahkan Grand Total sebagai baris baru ke spph_df
        grand_total_row = pd.DataFrame({"spph": ["Grand Total"], "tonase": [grand_total]})
        spph_df = pd.concat([spph_df, grand_total_row], ignore_index=True)

        # Membuat grafik interaktif untuk SPPH/Mitra
        fig = px.bar(spph_df, 
                    x="spph", 
                    y="tonase", 
                    text=['{:,.2f}'.format(x) for x in spph_df["tonase"]], 
                    template="seaborn")
        
        fig.update_traces(marker_line_width=1, opacity=0.8)
        
        # Tampilkan grafik
        st.plotly_chart(fig, use_container_width=True)


    # Shift-wise tonnage pie chart
    with col2:
        st.subheader("Shift-wise Tonage")
        fig = px.pie(df_filtered, values="tonase", names="shift", hole=0.5)
        st.plotly_chart(fig, use_container_width=True)

    import calendar
    from datetime import datetime

    # Mendapatkan bulan dan tahun saat ini
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Menghitung jumlah hari dalam bulan ini
    DAYS_IN_MONTH = calendar.monthrange(current_year, current_month)[1]
    WEEKS_IN_MONTH = DAYS_IN_MONTH / 7
    st.markdown(
    """
    <hr style="border: 1px solid red;" />
    """, 
    unsafe_allow_html=True
)

    # Target Rakor Analysis
    st.subheader("Target Rakor vs Actual Comparison")

    # Pengelompokan dan agregasi
    rakor_df = df_filtered.groupby("status", as_index=False).agg({
        "tonase": "sum", 
        "target_rakor": "first"
    })

    # Menghitung target harian dan mingguan berdasarkan target bulanan
    rakor_df["target_rakor_harian"] = (rakor_df["target_rakor"] / DAYS_IN_MONTH).round(2)
    rakor_df["target_rakor_mingguan"] = (rakor_df["target_rakor"] / WEEKS_IN_MONTH).round(2)

    # Menghitung perbedaan dan pencapaian persentase
    rakor_df["difference"] = rakor_df.apply(
        lambda row: round(max(row["target_rakor"] - row["tonase"], 0), 2) if row["target_rakor"] > 0 else 0, axis=1
    )
    rakor_df["percent achievement"] = rakor_df.apply(
        lambda row: round((row["tonase"] / row["target_rakor"] * 100), 2) if row["target_rakor"] > 0 else 0, axis=1
    )

    # Membulatkan tonase dan target_rakor di DataFrame
    rakor_df["tonase"] = rakor_df["tonase"].round(2)  # Pembulatan ke bilangan bulat
    rakor_df["target_rakor"] = rakor_df["target_rakor"].round(2)  # Pembulatan ke bilangan bulat

    # Menghilangkan Housekeeping dari total
    rakor_df_no_housekeeping = rakor_df.loc[rakor_df["status"] != "Housekeeping"]

    # Menambahkan baris total tanpa Housekeeping
    total_row = pd.DataFrame({
        "status": ["Total"],
        "tonase": [round(rakor_df_no_housekeeping["tonase"].sum(), 0)],  # Total tonase tanpa Housekeeping
        "target_rakor": [round(rakor_df_no_housekeeping["target_rakor"].sum(), 0)],  # Total target_rakor tanpa Housekeeping
        "target_rakor_harian": [round(rakor_df_no_housekeeping["target_rakor_harian"].sum(), 2)],  # Total target_rakor_harian tanpa Housekeeping
        "target_rakor_mingguan": [round(rakor_df_no_housekeeping["target_rakor_mingguan"].sum(), 2)],  # Total target_rakor_mingguan tanpa Housekeeping
        "difference": [round(rakor_df_no_housekeeping["difference"].sum(), 2)],  # Total difference tanpa Housekeeping
        "percent achievement": [round(rakor_df_no_housekeeping["percent achievement"].mean(), 2)]  # Rata-rata percent achievement tanpa Housekeeping
    })

    # Menggabungkan baris total ke akhir DataFrame
    rakor_df = pd.concat([rakor_df, total_row], ignore_index=True)

    # Mengatur ulang indeks dan menampilkan DataFrame
    rakor_df.reset_index(drop=True, inplace=True)  # Mengatur ulang indeks dan menghapus indeks lama
    rakor_df.index = [*range(1, len(rakor_df) + 1)]  # Membuat indeks baru mulai dari 1
    st.dataframe(rakor_df)

    # Menampilkan filter interaktif untuk memilih status yang ingin dilihat
    status_options = rakor_df['status'].unique()
    selected_status = st.multiselect("Pilih status untuk dilihat:", status_options, default=status_options)

    # Filter data berdasarkan status yang dipilih
    filtered_rakor_df = rakor_df[rakor_df['status'].isin(selected_status)]

    # Visualisasi perbandingan target_rakor dan tonase aktual berdasarkan filter
    if not filtered_rakor_df.empty:
        # Pastikan semua nilai dibulatkan di DataFrame yang digunakan untuk plot
        filtered_rakor_df["tonase"] = filtered_rakor_df["tonase"].round(2)  # Pembulatan ke bilangan bulat
        filtered_rakor_df["target_rakor"] = filtered_rakor_df["target_rakor"].round(2)  # Pembulatan ke bilangan bulat

        # Membuat grafik
        fig_rakor = px.bar(
            filtered_rakor_df, 
            x="status", 
            y=["target_rakor", "tonase"], 
            barmode="group", 
            text_auto=True, 
            template="seaborn"
        )

        # Format nilai di label menjadi bilangan bulat
        for trace in fig_rakor.data:
            trace.text = [str(int(value)) for value in trace.y]  # Mengonversi nilai ke bilangan bulat dan ke string

        st.plotly_chart(fig_rakor, use_container_width=True)
    else:
        st.write("Tidak ada data yang tersedia untuk status yang dipilih.")


    import calendar
    from datetime import datetime

    # Mendapatkan bulan dan tahun saat ini
    current_year = datetime.now().year
    current_month = datetime.now().month

    # Menghitung jumlah hari dalam bulan ini
    DAYS_IN_MONTH = calendar.monthrange(current_year, current_month)[1]  # Mengembalikan jumlah hari dalam bulan ini
    WEEKS_IN_MONTH = DAYS_IN_MONTH / 7
    st.markdown(
    """
    <hr style="border: 1px solid red;" />
    """, 
    unsafe_allow_html=True
)

    # Target SPPH/Mitra Analysis
    st.subheader("Target SPPH/Mitra vs Actual Comparison")

    # Grouping and aggregation
    spph_mitra_df = df_filtered.groupby("spph", as_index=False).agg({
        "tonase": "sum", 
        "target_spph_mitra": "first"
    })

    # Menghitung SGJ Total dari SGJ1, SGJ2, SGJ3, dan SPARE
    sgj_total_tonase = spph_mitra_df[spph_mitra_df['spph'].isin(['SGJ1', 'SGJ2', 'SGJ3', 'SPARE'])]['tonase'].sum()
    sgj_total_target = spph_mitra_df[spph_mitra_df['spph'].isin(['SGJ1', 'SGJ2', 'SGJ3', 'SPARE'])]['target_spph_mitra'].sum()

    # Menambahkan baris SGJ Total ke DataFrame
    sgj_total_row = pd.DataFrame({
        "spph": ["SGJ Total"],
        "tonase": [round(sgj_total_tonase, 2)],  # Membulatkan tonase
        "target_spph_mitra": [round(sgj_total_target, 2)],  # Membulatkan target
        "target_spph_mitra_harian": [round(sgj_total_target / DAYS_IN_MONTH, 2)],  # Membulatkan target harian
        "target_spph_mitra_mingguan": [round(sgj_total_target / WEEKS_IN_MONTH, 2)],  # Membulatkan target mingguan
        "difference": [round(max(sgj_total_target - sgj_total_tonase, 0), 2)],  # Membulatkan perbedaan
        "percent achievement": [round((sgj_total_tonase / sgj_total_target * 100), 2) if sgj_total_target > 0 else 0]  # Membulatkan pencapaian persentase
    })

    # Menghitung target harian dan mingguan berdasarkan target bulanan
    spph_mitra_df["tonase"] = spph_mitra_df["tonase"].round(2)
    spph_mitra_df["target_spph_mitra_harian"] = spph_mitra_df["target_spph_mitra"] / DAYS_IN_MONTH
    spph_mitra_df["target_spph_mitra_harian"] = spph_mitra_df["target_spph_mitra_harian"].round(2)
    spph_mitra_df["target_spph_mitra_mingguan"] = spph_mitra_df["target_spph_mitra"] / WEEKS_IN_MONTH
    spph_mitra_df["target_spph_mitra_mingguan"] = spph_mitra_df["target_spph_mitra_mingguan"].round(2)

    # Menghitung perbedaan dan pencapaian persentase
    spph_mitra_df["difference"] = spph_mitra_df.apply(lambda row: round(max(row["target_spph_mitra"] - row["tonase"], 0), 2) if row["target_spph_mitra"] > 0 else 0, axis=1)
    spph_mitra_df["percent achievement"] = spph_mitra_df.apply(lambda row: round((row["tonase"] / row["target_spph_mitra"] * 100), 2) if row["target_spph_mitra"] > 0 else 0, axis=1)

    # Menambahkan SGJ Total ke dalam DataFrame
    spph_mitra_df = pd.concat([spph_mitra_df, sgj_total_row], ignore_index=True)

    # Menambahkan baris Total tanpa SGJ Total
    total_row2 = pd.DataFrame({
        "spph": ["Total"],
        "tonase": [round(spph_mitra_df[~spph_mitra_df['spph'].isin(['SGJ Total'])]["tonase"].sum(), 2)],
        "target_spph_mitra": [round(spph_mitra_df[~spph_mitra_df['spph'].isin(['SGJ Total'])]["target_spph_mitra"].sum(), 2)],
        "target_spph_mitra_harian": [round(spph_mitra_df[~spph_mitra_df['spph'].isin(['SGJ Total'])]["target_spph_mitra_harian"].sum(), 2)],
        "target_spph_mitra_mingguan": [round(spph_mitra_df[~spph_mitra_df['spph'].isin(['SGJ Total'])]["target_spph_mitra_mingguan"].sum(), 2)],
        "difference": [round(spph_mitra_df[~spph_mitra_df['spph'].isin(['SGJ Total'])]["difference"].sum(), 2)],
        "percent achievement": [round(spph_mitra_df[~spph_mitra_df['spph'].isin(['SGJ Total'])]["percent achievement"].mean(), 2)]
    })

    # Menambahkan total_row2 ke DataFrame hanya sekali
    spph_mitra_df = pd.concat([spph_mitra_df, total_row2], ignore_index=True)

    # Reset indeks dan tampilkan DataFrame
    spph_mitra_df.index = [*range(1, len(spph_mitra_df)), '']
    st.dataframe(spph_mitra_df)

    # Menampilkan filter interaktif untuk memilih SPPH/Mitra yang ingin dilihat
    spph_options = spph_mitra_df['spph'].unique()
    selected_spph = st.multiselect("Pilih SPPH/Mitra untuk dilihat:", spph_options, default=spph_options)

    # Filter data berdasarkan pilihan SPPH/Mitra
    filtered_spph_mitra_df = spph_mitra_df[spph_mitra_df['spph'].isin(selected_spph)]
    
    # Visualisasi perbandingan target_spph_mitra dan tonase aktual berdasarkan filter
    if not filtered_spph_mitra_df.empty:
        fig_spph_mitra = px.bar(
            filtered_spph_mitra_df, 
            x="spph", 
            y=["target_spph_mitra", "tonase"], 
            barmode="group", 
            text_auto=True, 
            template="seaborn"
        )

        # Membulatkan nilai di chart
        fig_spph_mitra.update_traces(texttemplate='%{y:.2f}')  # Membulatkan nilai yang ditampilkan pada grafik
        st.plotly_chart(fig_spph_mitra, use_container_width=True)
    else:
        st.write("Tidak ada data yang tersedia untuk SPPH/Mitra yang dipilih.")


    # Total Target SPPH/Mitra dan Total Tonase
    total_target_spph_mitra = spph_mitra_df["target_spph_mitra"].sum()
    total_tonase_spph_mitra = spph_mitra_df["tonase"].sum()
    total_difference_spph_mitra = total_target_spph_mitra - total_tonase_spph_mitra
    total_percent_achievement_spph_mitra = (total_tonase_spph_mitra / total_target_spph_mitra) * 100 if total_target_spph_mitra != 0 else 0

    st.markdown(
    """
    <hr style="border: 1px solid red;" />
    """, 
    unsafe_allow_html=True
)


    # Fungsi untuk meng-encode gambar menjadi base64
    def get_base64_image(image_path):
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode()

    # Path ke gambar lokal
    image_path = "assets/RBPab.png"
    encoded_image = get_base64_image(image_path)

    # Jam Dumping Analysis
    if 'jam dumping' in df_filtered.columns:
        st.subheader("Jam Dumping Analysis")

        try:
            # Form untuk memilih filter dan tombol Refresh
            with st.form("filter_form_jam_dumping"):
                # Filter by Mitra (multi-choice)
                mitra_options = df_filtered['spph'].unique().tolist()
                mitra_options.append("SGJTotal")
                selected_mitra = st.multiselect("Pilih SPPH/Mitra", mitra_options, default=mitra_options)

                # Filter by Dump Truck (if available in the dataset)
                truck_options = ['Semua Dump Truck'] + df_filtered['dump_truck'].unique().tolist() if 'dump_truck' in df_filtered.columns else ['Semua Dump Truck']
                selected_truck = st.selectbox("Pilih Dump Truck", truck_options)

                # Filter by Lokasi (if available in the dataset)
                lokasi_options = ['Semua Lokasi'] + df_filtered['lokasi'].unique().tolist() if 'lokasi' in df_filtered.columns else ['Semua Lokasi']
                selected_lokasi = st.selectbox("Pilih Lokasi", lokasi_options)

                # Filter by date range
                date_min = pd.to_datetime(df_filtered['date']).min()
                date_max = pd.to_datetime(df_filtered['date']).max()
                selected_date_range = st.date_input("Pilih Rentang Tanggal", [date_min, date_max])

                # Filter by period (daily/weekly/monthly)
                period_options = ["Harian", "Mingguan", "Bulanan"]
                selected_period = st.radio("Pilih Periode", period_options)

                refresh_button = st.form_submit_button("Refresh Data")

            # Jika tombol Refresh ditekan, jalankan proses
            if refresh_button:
                # 1. Filter by selected_mitra, including SGJTotal handling
                if selected_mitra:
                    if "SGJTotal" in selected_mitra:
                        sgj_filter = df_filtered['spph'].isin(['SGJ1', 'SGJ2', 'SGJ3', 'SPARE'])
                        df_sgj_total = df_filtered[sgj_filter]
                        other_mitra = [m for m in selected_mitra if m != "SGJTotal"]
                        df_filtered_period = pd.concat([df_filtered[df_filtered['spph'].isin(other_mitra)], df_sgj_total]) if other_mitra else df_sgj_total
                    else:
                        df_filtered_period = df_filtered[df_filtered['spph'].isin(selected_mitra)]

                # 2. Filter by selected_truck
                if selected_truck != "Semua Dump Truck":
                    df_filtered_period = df_filtered_period[df_filtered_period['dump_truck'] == selected_truck]

                # 3. Filter by selected_lokasi
                if selected_lokasi != "Semua Lokasi":
                    df_filtered_period = df_filtered_period[df_filtered_period['lokasi'] == selected_lokasi]

                # 4. Filter by selected_date_range
                df_filtered_period = df_filtered_period[
                    (pd.to_datetime(df_filtered_period['date']) >= pd.to_datetime(selected_date_range[0])) &
                    (pd.to_datetime(df_filtered_period['date']) <= pd.to_datetime(selected_date_range[1]))
                ]

                # Hanya kolom jam_dumping yang tidak kosong dan parsing ke datetime sekali saja
                df_filtered_period = df_filtered_period.dropna(subset=['jam dumping'])
                df_filtered_period['datetime_dumping'] = pd.to_datetime(
                    df_filtered_period['date'].astype(str) + ' ' + df_filtered_period['jam dumping'], errors='coerce'
                )

                # Buang data yang tidak bisa di-parse ke datetime
                if df_filtered_period['datetime_dumping'].isnull().any():
                    st.warning(f"Total {df_filtered_period['datetime_dumping'].isnull().sum()} data 'Jam Dumping' gagal di-parse.")
                    df_filtered_period = df_filtered_period.dropna(subset=['datetime_dumping'])

                # Tambahkan kolom 'hour' untuk grouping dan set kolom 'ritase'
                df_filtered_period['hour'] = df_filtered_period['datetime_dumping'].dt.hour
                df_filtered_period['ritase'] = 1

                # Hitung jumlah hari total
                total_days = (pd.to_datetime(selected_date_range[1]) - pd.to_datetime(selected_date_range[0])).days + 1

                # Pengelompokan sesuai periode yang dipilih
                if selected_period == "Harian":
                    df_filtered_period['day'] = df_filtered_period['datetime_dumping'].dt.date
                    jam_dumping_df = df_filtered_period.groupby(["day", "hour"], as_index=False).agg(
                        total_tonase=('tonase', 'sum'),
                        total_ritase=('ritase', 'sum')
                    )
                    fig_title = "Jam Dumping Harian"
                elif selected_period == "Mingguan":
                    df_filtered_period['week'] = df_filtered_period['datetime_dumping'].dt.isocalendar().week
                    jam_dumping_df = df_filtered_period.groupby(["week", "hour"], as_index=False).agg(
                        total_tonase=('tonase', 'sum'),
                        total_ritase=('ritase', 'sum')
                    )
                    fig_title = "Jam Dumping Mingguan"
                else:
                    df_filtered_period['month'] = df_filtered_period['datetime_dumping'].dt.to_period('M')
                    jam_dumping_df = df_filtered_period.groupby(["month", "hour"], as_index=False).agg(
                        total_tonase=('tonase', 'sum'),
                        total_ritase=('ritase', 'sum')
                    )
                    fig_title = "Jam Dumping Bulanan"

                jam_dumping_df["total_tonase"] = jam_dumping_df["total_tonase"].round(2)
                jam_dumping_df["total_ritase"] = jam_dumping_df["total_ritase"].round(2)
                jam_dumping_df["avg_ritase"] = (jam_dumping_df["total_ritase"] / total_days).round(2)

                # Membuat grafik total tonase
                fig_jam_dumping = px.line(
                    jam_dumping_df,
                    x="hour",
                    y="total_tonase",
                    title=f'{fig_title} vs Tonase ({", ".join(selected_mitra)}, {selected_truck}, {selected_lokasi})',
                    labels={'total_tonase': 'Total Tonase', 'hour': 'Jam Dumping (Hour)'},
                    template="plotly_dark",
                    color_discrete_sequence=['#00CC96']
                )

                # Menambahkan gambar ke grafik
                fig_jam_dumping.add_layout_image(
                    dict(
                        source="data:image/png;base64," + encoded_image,
                        xref="paper", yref="paper",
                        x=1.00, y=1.35,
                        sizex=0.45, sizey=0.45,
                        xanchor="right", yanchor="top"
                    )
                )

                fig_jam_dumping.update_layout(
                    xaxis=dict(tickmode='linear', tick0=0, dtick=1),
                    yaxis=dict(tickformat=','),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=15, color="white")
                )

                st.plotly_chart(fig_jam_dumping, use_container_width=True)

                st.markdown("<hr style='border: 1px solid red;' />", unsafe_allow_html=True)

                # Grafik rata-rata ritase per jam dumping
                fig_avg_ritase = px.line(
                    jam_dumping_df,
                    x="hour",
                    y="avg_ritase",
                    title=f'Rata-rata Ritase per {fig_title} ({", ".join(selected_mitra)}, {selected_truck}, {selected_lokasi})',
                    labels={'avg_ritase': 'Rata-rata Ritase', 'hour': 'Jam Dumping (Hour)'},
                    template="plotly_dark",
                    color_discrete_sequence=['#FFA15A']
                )

                # Menambahkan gambar di sudut kanan atas di luar area plot
                fig_avg_ritase.add_layout_image(
                    dict(
                        source="data:image/png;base64," + encoded_image,
                        xref="paper", yref="paper",
                        x=1.01, y=1.35,
                        sizex=0.45, sizey=0.45,
                        xanchor="right", yanchor="top"
                    )
                )

                fig_avg_ritase.update_layout(
                    xaxis=dict(tickmode='linear', tick0=0, dtick=1),
                    yaxis=dict(tickformat=','),
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(size=15, color="white")
                )

                st.plotly_chart(fig_avg_ritase, use_container_width=True)

                st.subheader("Tabel Jam Dumping dan Rata-rata Ritase")
                st.dataframe(jam_dumping_df)

                csv_jam_dumping = jam_dumping_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Download Tabel Jam Dumping dan Rata-rata Ritase sebagai CSV",
                    data=csv_jam_dumping,
                    file_name='jam_dumping_analysis_with_avg_ritase.csv',
                    mime='text/csv'
                )
        except Exception as e:
            st.error(f"Terjadi kesalahan: {e}")

    else:
        st.warning("Kolom 'Jam Dumping' tidak ditemukan dalam dataset.")

    st.markdown("<hr style='border: 1px solid red;' />", unsafe_allow_html=True)



    # Pastikan 'nama operator' dan 'spph' ada di dalam dataset
    if 'nama operator' in df_filtered.columns and 'spph' in df_filtered.columns:
        st.subheader("Top Operator Dump Truck Berdasarkan Ritase")

        try:
            @st.cache_data
            def process_data(df):
                df['spph'] = df['spph'].replace({
                    'SGJ1': 'SGJ',
                    'SGJ2': 'SGJ',
                    'SGJ3': 'SGJ',
                    'SPARE': 'SGJ'
                })
                df['ritase'] = 1  # Setiap baris dihitung sebagai 1 ritase
                return df

            df_filtered = process_data(df_filtered)
            mitra_options = df_filtered['spph'].unique().tolist()

            with st.form("filter_form"):
                selected_mitra = st.multiselect("Pilih SPPH/Mitra", mitra_options, default=mitra_options, key="mitra_operator")
                refresh_button = st.form_submit_button("Refresh Data")

            if refresh_button:
                @st.cache_data(hash_funcs={list: lambda x: hash(tuple(x))})
                def compute_ritase(df, selected_mitra):
                    if selected_mitra:
                        df = df[df['spph'].isin(selected_mitra)]
                    return df.groupby(['nama operator', 'spph'], as_index=False).agg(total_ritase=('ritase', 'sum'))

                operator_ritase_df = compute_ritase(df_filtered, selected_mitra)
                operator_ritase_df['operator_mitra'] = operator_ritase_df['nama operator'] + " (" + operator_ritase_df['spph'] + ")"
                operator_ritase_df = operator_ritase_df.sort_values(by='total_ritase', ascending=False).reset_index(drop=True)

                # Tentukan warna untuk Top 1, 2, 3 Tertinggi dan Terendah
                top_10_operator = operator_ritase_df.head(10).copy()
                bottom_10_operator = operator_ritase_df[operator_ritase_df['total_ritase'] > 0].tail(10).copy()

                # Fungsi untuk mengatur warna berdasarkan peringkat
                def set_color_rank(data):
                    colors = []
                    for i in range(len(data)):
                        if i == 0:
                            colors.append("Top 1")     # Warna Emas untuk Top 1
                        elif i == 1:
                            colors.append("Top 2")   # Warna Perak untuk Top 2
                        elif i == 2:
                            colors.append("Top 3")   # Warna Perunggu untuk Top 3
                        else:
                            colors.append("Top 4-10")  # Warna Biru Muda untuk yang lain
                    return colors

                # Terapkan fungsi pewarnaan pada top dan bottom operator
                top_10_operator['color'] = set_color_rank(top_10_operator)
                bottom_10_operator = bottom_10_operator.sort_values(by='total_ritase')  # Urutkan dari rendah ke tinggi
                bottom_10_operator['color'] = set_color_rank(bottom_10_operator)

                # Fungsi untuk membuat grafik dengan warna yang disesuaikan
                def plot_ritase(data, title):
                    fig = px.bar(
                        data,
                        x='operator_mitra',
                        y='total_ritase',
                        title=title,
                        labels={'total_ritase': 'Total Ritase', 'operator_mitra': 'Nama Operator (Mitra)'},
                        template="plotly_dark",
                        width=1200,
                        height=500,
                        color='color',
                        color_discrete_map={
                            "Top 1": "#ffb31a",      # Emas untuk Top 1
                            "Top 2": "#C0C0C0",    # Perak untuk Top 2
                            "Top 3": "#CD7F32",    # Perunggu untuk Top 3
                            "Top 4-10": "#ADD8E6"  # Biru Muda untuk lainnya
                        }
                    )

                    # Menambahkan gambar di sudut kanan atas di luar area plot
                    fig.add_layout_image(
                        dict(
                            source="data:image/png;base64," + encoded_image,
                            xref="paper", yref="paper",
                            x=1.00, y=1.55,
                            sizex=0.65, sizey=0.65,
                            xanchor="right", yanchor="top"
                        )
                    )

                    fig.update_layout(
                        bargap=0.6, bargroupgap=0.2, 
                        xaxis_tickangle=-45, 
                        xaxis_tickfont=dict(size=12),
                        plot_bgcolor='rgba(0,0,0,0)',
                        paper_bgcolor='rgba(0,0,0,0)',
                        font=dict(size=15, color="white")
                    )
                    fig.update_traces(marker_line_color='black', marker_line_width=1.5)
                    return fig

                # Tampilkan grafik
                st.plotly_chart(plot_ritase(top_10_operator, "Top 10 Operator Dump Truck dengan Ritase Tertinggi"), use_container_width=True)
                st.plotly_chart(plot_ritase(bottom_10_operator, "Top 10 Operator Dump Truck dengan Ritase Terendah"), use_container_width=True)

                operator_ritase_df['Kategori'] = 'Di Luar Top 10'
                operator_ritase_df.loc[operator_ritase_df['operator_mitra'].isin(top_10_operator['operator_mitra']), 'Kategori'] = 'Top 10 Tertinggi'
                operator_ritase_df.loc[operator_ritase_df['operator_mitra'].isin(bottom_10_operator['operator_mitra']), 'Kategori'] = 'Top 10 Terendah'
                operator_ritase_df['No'] = operator_ritase_df.index + 1

                st.subheader("Operator dengan Kategori Top 10 Tertinggi, Terendah, dan Di Luar Top 10")
                st.dataframe(operator_ritase_df[['No', 'operator_mitra', 'total_ritase', 'Kategori']].set_index('No'))

                csv = operator_ritase_df[['No', 'operator_mitra', 'total_ritase', 'Kategori']].reset_index().to_csv(index=False).encode('utf-8')
                st.download_button(label="Download Tabel Operator", data=csv, file_name='operator_dump_truck.csv', mime='text/csv', key='download-csv')

        except Exception as e:
            st.error(f"Terjadi kesalahan: {str(e)}")
    else:
        st.warning("Kolom 'Nama Operator' atau 'SPPH' tidak ditemukan dalam dataset.")


    # Download options
    csv_rakor = rakor_df.to_csv(index=False).encode('utf-8')
    st.download_button("Download Target Rakor Comparison Data", data=csv_rakor, file_name="Target_rakor_comparison_data.csv", mime="text/csv")

    csv_full = df.to_csv(index=False).encode('utf-8')
    st.download_button('Download Full Dataset', data=csv_full, file_name="rehandling_batubara_data.csv", mime='text/csv')
    
    
