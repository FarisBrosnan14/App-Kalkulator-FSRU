import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import io

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

# ==========================================
# TAHAP 4: ESTIMATION SCHEDULE (ESOD)
# ==========================================
st.divider()
st.header("4️⃣ Tahap 4: Estimation Schedule Operational Discharging (ESOD)")

col_eta1, col_eta2 = st.columns(2)
with col_eta1:
    eta_date = st.date_input("Tanggal Kedatangan (ETA / POB)")
with col_eta2:
    eta_time = st.time_input("Waktu Kedatangan (LCT)", value=pd.to_datetime("18:00").time())

start_datetime = datetime.combine(eta_date, eta_time)
durasi_bongkar_menit = int(waktu_pompa_murni * 60) if waktu_pompa_murni > 0 else 1980

default_schedule = [
    ["All Fast", 180], ["NOR Received", 55], ["ARMs Connected", 30],
    ["OPEN CTM", 35], ["WARM ESD Test", 15], ["Arm C/D", 90],
    ["COLD ESD Test", 15], ["START DISCHARGING", 20], ["FULL RATE", 30],
    ["Bongkar Muat Murni (Rate Down)", durasi_bongkar_menit],
    ["DISCHARGING COMPLETED", 30], ["CLOSING CTM", 120],
    ["ARMs Disconnected", 10], ["Documentation", 60], ["POB OUT", 120]
]

df_default = pd.DataFrame(default_schedule, columns=["Kegiatan", "Durasi (Menit)"])

col_edit, col_result = st.columns([1, 1.5])
with col_edit:
    st.markdown("**✍️ Edit Durasi Kegiatan (Menit)**")
    edited_df = st.data_editor(
        df_default,
        column_config={
            "Kegiatan": st.column_config.TextColumn("Kegiatan", disabled=True),
            "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
        },
        hide_index=True, use_container_width=True
    )

with col_result:
    st.markdown("**📅 Hasil Proyeksi Jadwal (Waktu Mulai & Selesai)**")
    
    schedule_result = []
    current_time = start_datetime
    
    for index, row in edited_df.iterrows():
        durasi = row["Durasi (Menit)"]
        start_time = current_time
        end_time = current_time + timedelta(minutes=int(durasi))
        
        schedule_result.append({
            "Kegiatan": row["Kegiatan"],
            "Durasi (Menit)": durasi,
            "Start": start_time,
            "End": end_time,
            "Mulai": start_time.strftime("%d-%b %H:%M"),
            "Selesai": end_time.strftime("%d-%b %H:%M")
        })
        current_time = end_time
        
    df_result = pd.DataFrame(schedule_result)
    
    # Menampilkan tabel hasil tanpa kolom datetime mentah
    st.dataframe(df_result[["Kegiatan", "Durasi (Menit)", "Mulai", "Selesai"]], use_container_width=True, hide_index=True)

# ==========================================
# TAHAP 5: VISUALISASI FLOWCHART & EXPORT
# ==========================================
st.divider()
st.header("5️⃣ Tahap 5: Flowchart Timeline & Export Data")
st.info("💡 Arahkan mouse ke atas grafik untuk melihat detail waktu. Klik ikon kamera di pojok kanan atas grafik untuk mendownload sebagai gambar PNG.")

# Membuat grafik Gantt Chart (Timeline) dengan Plotly
fig = px.timeline(
    df_result, 
    x_start="Start", 
    x_end="End", 
    y="Kegiatan",
    color="Kegiatan",
    title="Visualisasi Jadwal Operasional Discharging (ESOD)",
    text="Kegiatan"
)

# Membalik urutan Y-axis agar kegiatan awal ada di atas
fig.update_yaxes(autorange="reversed")
fig.update_layout(showlegend=False, height=500)

# Menampilkan grafik di Streamlit
st.plotly_chart(fig, use_container_width=True)

# Fitur Export ke Excel
st.markdown("### 📥 Export Jadwal")
buffer = io.BytesIO()
with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
    # Export tabel hasil yang rapi
    df_result[["Kegiatan", "Durasi (Menit)", "Mulai", "Selesai"]].to_excel(writer, index=False, sheet_name='Jadwal_ESOD')
    
st.download_button(
    label="📊 Download Tabel Jadwal (Excel .xlsx)",
    data=buffer.getvalue(),
    file_name=f"Jadwal_ESOD_FSRU_{eta_date}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
