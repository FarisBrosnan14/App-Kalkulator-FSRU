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
# TAHAP 3: KALKULASI KEBUTUHAN RATE & WAKTU
# ==========================================
st.divider()
st.header("3️⃣ Tahap 3: Kalkulasi Kebutuhan Rate & Waktu")
st.info("Pilih pendekatan perhitungan Anda: Apakah Anda sedang mengejar target waktu penyelesaian, atau menyesuaikan dengan kemampuan laju pompa kapal?")

col_skenario_a, col_skenario_b = st.columns(2)

with col_skenario_a:
    st.subheader("Skenario A: Cari Kebutuhan Rate")
    st.write("*(Mencari Rate minimum jika Anda memiliki target batas waktu tertentu)*")
    target_laytime = st.number_input("Target Total Laytime (Jam)", min_value=1.0, value=35.0, step=0.5)
    buffer_time_a = st.number_input("Waktu Buffer (Jam)", value=4.0, step=0.5, key="buf_a")
    
    waktu_murni_a = target_laytime - buffer_time_a
    req_loading_rate = cargo_vol / waktu_murni_a if waktu_murni_a > 0 else 0
    req_regas_rate_a = disrub_vol / target_laytime if disrub_vol > 0 else 0
    
    st.success(f"🔹 **Kebutuhan Loading Rate:** {req_loading_rate:,.0f} m³/jam")
    st.success(f"🔹 **Kebutuhan Regas Rate:** {req_regas_rate_a:,.0f} m³/jam")

with col_skenario_b:
    st.subheader("Skenario B: Cari Waktu Operasi")
    st.write("*(Mencari kepastian durasi waktu jika Loading Rate kapal sudah disepakati)*")
    input_loading_rate = st.number_input("Rencana Loading Rate (m³/jam)", min_value=100.0, value=3900.0, step=100.0)
    buffer_time_b = st.number_input("Waktu Buffer (Jam)", value=4.0, step=0.5, key="buf_b")
    
    waktu_murni_b = cargo_vol / input_loading_rate
    total_laytime_b = waktu_murni_b + buffer_time_b
    req_regas_rate_b = disrub_vol / total_laytime_b if disrub_vol > 0 else 0
    
    st.info(f"⏳ **Estimasi Waktu Bongkar Murni:** {waktu_murni_b:.1f} Jam")
    st.info(f"⏳ **Estimasi Total Laytime:** {total_laytime_b:.1f} Jam")
    st.info(f"🔹 **Kebutuhan Regas Rate:** {req_regas_rate_b:,.0f} m³/jam")

st.markdown("---")
pilihan_skenario = st.radio(
    "👉 **Pilih sumber data yang akan digunakan untuk menggenerate Tabel ESOD di Tahap 4:**", 
    ["Gunakan Data Skenario A", "Gunakan Data Skenario B"]
)

if pilihan_skenario == "Gunakan Data Skenario A":
    final_waktu_murni = waktu_murni_a
else:
    final_waktu_murni = waktu_murni_b

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
durasi_bongkar_menit = int(final_waktu_murni * 60) if final_waktu_murni > 0 else 1980

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
            "Mulai": start_time.strftime("%d-%b %H:%M"),
            "Selesai": end_time.strftime("%d-%b %H:%M")
        })
        current_time = end_time
        
    df_result = pd.DataFrame(schedule_result)
    st.dataframe(df_result[["Kegiatan", "Durasi (Menit)", "Mulai", "Selesai"]], use_container_width=True, hide_index=True)
