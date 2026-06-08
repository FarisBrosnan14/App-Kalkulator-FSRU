import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Ops Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Discharging Plan Simulator")
st.markdown("Dashboard interaktif untuk persiapan **Pre-Cargo Meeting**")
st.divider()

# ==========================================
# TAHAP 1: KONDISI AWAL & WAKTU ACUAN
# ==========================================
st.header("1️⃣ Tahap 1: Parameter Kargo & Kalkulasi Waktu Acuan")
st.info("Sistem akan otomatis menghitung ROB Saat Commence berdasarkan waktu tunggu dan serapan harian PLN.")

col1, col2, col3 = st.columns(3)
with col1:
    cargo_vol = st.number_input("Volume Kargo Masuk (m³)", min_value=10000.0, value=125000.0, step=1000.0)
with col2:
    rob_acuan = st.number_input("ROB FSRU pada Jam Acuan (m³)", min_value=0.0, value=25000.0, step=500.0, help="Contoh: ROB tercatat pada pukul 00:00")
with col3:
    serapan_harian = st.number_input("Rata-rata Serapan PLN (m³/hari)", min_value=0.0, value=17000.0, step=500.0)

st.markdown("#### ⏳ Pengaturan Waktu Tunggu Kapal")
col_waktu1, col_waktu2, col_waktu3 = st.columns(3)
with col_waktu1:
    jam_acuan = st.number_input("Jam Acuan ROB (0-24)", min_value=0.0, max_value=24.0, value=0.0, step=0.5, help="Ketik 0.0 untuk jam 00:00")
with col_waktu2:
    jam_commence = st.number_input("Estimasi Jam Commence (0-24)", min_value=0.0, max_value=24.0, value=14.0, step=0.5, help="Jam katup mulai dibuka. Misal 14.5 untuk jam 14:30")

# --- PROSES KALKULASI ROB COMMENCE ---
selisih_jam = jam_commence - jam_acuan
# Jika menyeberang hari (misal acuan 20:00, commence 08:00 besoknya)
if selisih_jam < 0:
    selisih_jam += 24.0

serapan_per_jam = serapan_harian / 24.0
gas_terpakai_menunggu = serapan_per_jam * selisih_jam
rob_commence = rob_acuan - gas_terpakai_menunggu

with col_waktu3:
    st.metric(
        label="Estimasi ROB Saat Commence", 
        value=f"{rob_commence:,.0f} m³", 
        delta=f"-{gas_terpakai_menunggu:,.0f} m³ (Terpakai selama {selisih_jam} jam menunggu)", 
        delta_color="inverse"
    )

# ==========================================
# TAHAP 2: KALKULASI RISIKO (DISRUB)
# ==========================================
st.divider()
st.header("2️⃣ Tahap 2: Analisis Kapasitas (Volume Disrub)")
safe_limit = 122500.0
total_akumulasi = cargo_vol + rob_commence
disrub_vol = total_akumulasi - safe_limit

if disrub_vol > 0:
    st.warning(f"⚠️ **RISIKO OVERFILL TERDETEKSI:** Total kargo + ROB mencapai **{total_akumulasi:,.0f} m³**.")
    st.markdown(f"**Tindakan Wajib:** Selama proses bongkar, Anda harus memastikan gas diserap ke darat minimal sebesar **{disrub_vol:,.0f} m³** (Volume Disrub).")
else:
    disrub_vol = 0
    st.success(f"✅ **KAPASITAS AMAN:** Total kargo + ROB hanya **{total_akumulasi:,.0f} m³** (Tidak melampaui batas 122.500 m³). Tidak ada paksaan serapan tambahan.")

# ==========================================
# TAHAP 3: SIMULATOR KEPUTUSAN (INTERAKTIF)
# ==========================================
st.divider()
st.header("3️⃣ Tahap 3: Skenario Rate & Laytime (Interaktif)")
st.markdown("💡 *Geser slider target durasi di bawah ini. Kecepatan pompa (Rate) akan terkalkulasi otomatis.*")

col_slider, col_buffer = st.columns([2, 1])
with col_slider:
    target_laytime = st.slider(
        "Target Total Waktu Operasi (Jam)", 
        min_value=24.0, 
        max_value=42.0, 
        value=35.0, 
        step=0.5
    )
with col_buffer:
    buffer_time = st.number_input(
        "Alokasi Waktu Buffer (Jam)", 
        value=4.0, 
        step=0.5,
        help="Waktu untuk Draining, Purging, dan Disconnect."
    )

waktu_pompa_murni = target_laytime - buffer_time

if waktu_pompa_murni <= 0:
    st.error("Target Waktu Operasi terlalu singkat dibandingkan Waktu Buffer!")
else:
    loading_rate = cargo_vol / waktu_pompa_murni
    regas_rate = disrub_vol / target_laytime if disrub_vol > 0 else 0
    
    st.markdown("### 🎯 Rekomendasi Instruksi (Action Plan)")
    res_col1, res_col2, res_col3 = st.columns(3)
    
    res_col1.metric("1. Durasi Bongkar Murni", f"{waktu_pompa_murni} Jam")
    res_col2.metric("2. Loading Rate (Ke Kapal)", f"{loading_rate:,.0f} m³/jam")
    res_col3.metric("3. Regas Rate (Ke Darat/PLN)", f"{regas_rate:,.0f} m³/jam")
    
    st.write("**Evaluasi Skenario:**")
    if target_laytime >= 40.0:
        st.error("🚨 Skenario Berisiko: Waktu sangat mepet dengan batas Demurrage (42 jam).")
    elif loading_rate > 4500:
        st.warning("⚠️ Skenario Berisiko: Loading Rate ke kapal terlalu tinggi. Pastikan pompa LNGC sanggup.")
    else:
        st.success("✅ Skenario Optimal: Waktu aman dari penalti, laju pompa berada di batas wajar.")
