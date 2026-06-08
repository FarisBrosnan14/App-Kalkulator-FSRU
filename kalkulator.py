import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Ops Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Discharging Plan Simulator")
st.markdown("Dashboard interaktif untuk persiapan **Pre-Cargo Meeting & ESOD**")
st.divider()

# ==========================================
# TAHAP 1: KONDISI AWAL & WAKTU ACUAN
# ==========================================
st.header("1️⃣ Tahap 1: Parameter Kargo & Kalkulasi Waktu Acuan")
col1, col2, col3 = st.columns(3)
with col1:
    cargo_vol = st.number_input("Volume Kargo Masuk (m³)", min_value=10000.0, value=130000.0, step=1000.0)
with col2:
    rob_acuan = st.number_input("ROB FSRU pada Jam Acuan (m³)", min_value=0.0, value=25000.0, step=500.0)
with col3:
    serapan_harian = st.number_input("Rata-rata Serapan PLN (m³/hari)", min_value=0.0, value=17000.0, step=500.0)

st.markdown("#### ⏳ Pengaturan Waktu Tunggu Kapal")
col_waktu1, col_waktu2, col_waktu3 = st.columns(3)
with col_waktu1:
    jam_acuan = st.number_input("Jam Acuan ROB (0-24)", min_value=0.0, max_value=24.0, value=0.0, step=0.5)
with col_waktu2:
    jam_commence = st.number_input("Estimasi Jam Commence (0-24)", min_value=0.0, max_value=24.0, value=14.0, step=0.5)

selisih_jam = jam_commence - jam_acuan
if selisih_jam < 0:
    selisih_jam += 24.0

serapan_per_jam = serapan_harian / 24.0
gas_terpakai_menunggu = serapan_per_jam * selisih_jam
rob_commence = rob_acuan - gas_terpakai_menunggu

with col_waktu3:
    st.metric("Estimasi ROB Saat Commence", f"{rob_commence:,.0f} m³", f"-{gas_terpakai_menunggu:,.0f} m³ (Terpakai saat menunggu)")

# ==========================================
# TAHAP 2: KALKULASI RISIKO (DISRUB)
# ==========================================
st.divider()
st.header("2️⃣ Tahap 2: Analisis Kapasitas (Volume Disrub)")
safe_limit = 122500.0
total_akumulasi = cargo_vol + rob_commence
disrub_vol = total_akumulasi - safe_limit

if disrub_vol > 0:
    st.warning(f"⚠️ **RISIKO OVERFILL:** Total kargo + ROB mencapai **{total_akumulasi:,.0f} m³**.")
    st.markdown(f"**Tindakan:** Selama proses bongkar, pastikan gas diserap ke darat minimal **{disrub_vol:,.0f} m³**.")
else:
    disrub_vol = 0
    st.success(f"✅ **KAPASITAS AMAN:** Total kargo + ROB hanya **{total_akumulasi:,.0f} m³**.")

# ==========================================
# TAHAP 3: SIMULATOR KEPUTUSAN (INTERAKTIF)
# ==========================================
st.divider()
st.header("3️⃣ Tahap 3: Skenario Rate & Laytime")
col_slider, col_buffer = st.columns([2, 1])
with col_slider:
    target_laytime = st.slider("Target Total Waktu Operasi (Jam)", min_value=24.0, max_value=42.0, value=35.0, step=0.5)
with col_buffer:
    buffer_time = st.number_input("Alokasi Waktu Buffer (Jam)", value=4.0, step=0.5)

waktu_pompa_murni = target_laytime - buffer_time

if waktu_pompa_murni > 0:
    loading_rate = cargo_vol / waktu_pompa_murni
    regas_rate = disrub_vol / target_laytime if disrub_vol > 0 else 0
    
    res_col1, res_col2, res_col3 = st.columns(3)
    res_col1.metric("1. Durasi Bongkar Murni", f"{waktu_pompa_murni} Jam")
    res_col2.metric("2. Loading Rate (Ke Kapal)", f"{loading_rate:,.0f} m³/jam")
    res_col3.metric("3. Regas Rate (Ke PLN)", f"{regas_rate:,.0f} m³/jam")

# ==========================================
# TAHAP 4: ESTIMATION SCHEDULE (ESOD)
# ==========================================
st.divider()
st.header("4️⃣ Tahap 4: Estimation Schedule Operational Discharging (ESOD)")
st.info("💡 Durasi pada tahap 'Bongkar Muat Murni' diambil otomatis dari Tahap 3. Anda dapat mengedit durasi kegiatan lainnya langsung di tabel.")

# Setup Waktu Kedatangan (ETA)
col_eta1, col_eta2 = st.columns(2)
with col_eta1:
    eta_date = st.date_input("Tanggal Kedatangan (ETA / POB)")
with col_eta2:
    eta_time = st.time_input("Waktu Kedatangan (LCT)", value=pd.to_datetime("18:00").time())

# Menggabungkan Tanggal dan Waktu
start_datetime = datetime.combine(eta_date, eta_time)

# Menyiapkan data default seperti format Excel
durasi_bongkar_menit = int(waktu_pompa_murni * 60) if waktu_pompa_murni > 0 else 1980

default_schedule = [
    ["All Fast", 180],
    ["NOR Received", 55],
    ["ARMs Connected", 30],
    ["OPEN CTM", 35],
    ["WARM ESD Test", 15],
    ["Arm C/D", 90],
    ["COLD ESD Test", 15],
    ["START DISCHARGING", 20],
    ["FULL RATE", 30],
    ["Bongkar Muat Murni (Rate Down)", durasi_bongkar_menit], # Otomatis dari Tahap 3
    ["DISCHARGING COMPLETED", 30],
    ["CLOSING CTM", 120],
    ["ARMs Disconnected", 10],
    ["Documentation", 60],
    ["POB OUT", 120]
]

df_default = pd.DataFrame(default_schedule, columns=["Kegiatan", "Durasi (Menit)"])

# Layout untuk Editor dan Hasil
col_edit, col_result = st.columns([1, 1.5])

with col_edit:
    st.markdown("**✍️ Edit Durasi Kegiatan (Menit)**")
    # Data Editor Interaktif
    edited_df = st.data_editor(
        df_default,
        column_config={
            "Kegiatan": st.column_config.TextColumn("Kegiatan", disabled=True),
            "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
        },
        hide_index=True,
        use_container_width=True
    )

with col_result:
    st.markdown("**📅 Hasil Proyeksi Jadwal (ESOD)**")
    
    # Kalkulasi jadwal berdasarkan input durasi
    schedule_result = []
    current_time = start_datetime
    
    # Menambahkan kegiatan pertama (ETA)
    schedule_result.append({
        "Kegiatan": "ETA / POB",
        "Waktu Pelaksanaan": current_time.strftime("%d-%b-%y / %H:%M")
    })
    
    # Looping untuk menghitung waktu setiap kegiatan
    for index, row in edited_df.iterrows():
        durasi = row["Durasi (Menit)"]
        current_time += timedelta(minutes=int(durasi))
        schedule_result.append({
            "Kegiatan": row["Kegiatan"],
            "Waktu Pelaksanaan": current_time.strftime("%d-%b-%y / %H:%M")
        })
        
    df_result = pd.DataFrame(schedule_result)
    
    # Menampilkan tabel hasil
    st.dataframe(
        df_result, 
        use_container_width=True, 
        hide_index=True
    )
    
    # Highlight Laytime Akhir
    laytime_akhir = current_time.strftime("%d-%b-%y / %H:%M")
    st.success(f"⚓ **Estimasi POB Out / Operasi Selesai:** {laytime_akhir}")
