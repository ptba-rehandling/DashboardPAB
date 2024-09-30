import os
import warnings
import pandas as pd
import plotly.express as px
import streamlit as st

# Suppress warnings
warnings.filterwarnings('ignore')

# Streamlit page configuration
st.set_page_config(page_title="Rehandling Batubara Dashboard", page_icon=":bar_chart:", layout="wide")

st.title(":bar_chart: Rehandling Batubara Data Exploration")
st.markdown('<style>div.block-container{padding-top:1rem;}</style>', unsafe_allow_html=True)

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

    # Input target manually for each shift
    st.sidebar.header("Input Target per Shift:")
    shift_targets = {}
    for s in df["shift"].unique():
        shift_targets[s] = st.sidebar.number_input(f"Target for {s}", value=1)

    # Add target column to filtered dataframe
    df_filtered['target'] = df_filtered['shift'].map(shift_targets)

    # Sidebar input for target rakor (bulanan)
    st.sidebar.header("Input Target Rakor Bulanan:")
    rakor_targets = {
        'FOB MV': st.sidebar.number_input("Target FOB MV", value=1),
        'Rehandling Blok Timur': st.sidebar.number_input("Target Rehandling Blok Timur", value=1),
        'Rehandling Antar Stock Blok Barat': st.sidebar.number_input("Target Rehandling Antar Stock Blok Barat", value=1),
        'Rehandling Antar Stock Blok Timur': st.sidebar.number_input("Target Rehandling Antar Stock Blok Timur", value=1),
        'Rehandling Blok Barat': st.sidebar.number_input("Target Rehandling Blok Barat", value=1),
        'Housekeeping': st.sidebar.number_input("Target Housekeeping", value=1),
        'Pengiriman konsumen': st.sidebar.number_input("Target Pengiriman konsumen", value=1)
    }

    # Map target rakor to dataset
    if 'status' in df_filtered.columns:
        df_filtered['target_rakor'] = df_filtered['status'].map(rakor_targets)
    else:
        st.error("Kolom 'status' tidak ditemukan dalam dataset.")
        st.stop()

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
        spph_mitra_targets[spph_mitra] = st.sidebar.number_input(f"Target for {spph_mitra}", value=1)

    # Map target SPPH/Mitra to dataset
    if 'spph' in df_filtered.columns:
        df_filtered['target_spph_mitra'] = df_filtered['spph'].map(spph_mitra_targets)
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
    rakor_df = df_filtered.groupby("status", as_index=False).agg({"tonase": "sum", "target_rakor": "sum"})
    rakor_df["difference"] = rakor_df["target_rakor"] - rakor_df["tonase"]
    rakor_df["percent achievement"] = (rakor_df["tonase"] / rakor_df["target_rakor"]).fillna(0) * 100

    rakor_df.index = range(1, len(rakor_df) + 1)
    # Display the DataFrame
    st.dataframe(rakor_df)

    # Visualisasi perbandingan target rakor dan tonase aktual
    fig_rakor = px.bar(rakor_df, x="status", y=["target_rakor", "tonase"], barmode="group", text_auto=True, template="seaborn")
    st.plotly_chart(fig_rakor, use_container_width=True)

    # Total Target Rakor dan Total Tonase
    total_target_rakor = rakor_df["target_rakor"].sum()
    total_tonase = rakor_df["tonase"].sum()
    st.sidebar.header("Total Target Rakor dan Total Tonase")
    st.sidebar.write(f"Total Target Rakor: {total_target_rakor:,.2f}")
    st.sidebar.write(f"Total Tonase: {total_tonase:,.2f}")

    # Overall Achievement Percentage
    achievement_percentage = (total_tonase / total_target_rakor) * 100 if total_target_rakor > 0 else 0
    st.sidebar.write(f"Total Persentase Pencapaian: {achievement_percentage:.2f}%")
