import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Ops Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Discharging Plan Simulator")
st.markdown("Dashboard interaktif untuk persiapan **Pre-Cargo Meeting**")
st.divider()

# ==========================================
# TAHAP 1: KONDISI AWAL (PARAMETER)
# ==========================================
st.header("1️⃣ Tahap 1: Input Parameter Kapal & FSRU")
st.info("Masukkan data dari Cargo Manifest dan kondisi tangki FSRU saat ini.")

col1, col2, col3 = st.columns(3)
with col1:
    cargo_vol = st.number_input("Volume Kargo Masuk (m³)", min_value=10000.0, value=125000.0, step=1000.0)
with col2:
    rob_vol = st.number_input("ROB FSRU Saat Commence (m³)", min_value=0.0, value=25000.0, step=500.0)
with col3:
    safe_limit = st.number_input("Batas Aman 98% (m³)", value=122500.0, disabled=True)

# ==========================================
# TAHAP 2: KALKULASI RISIKO (DISRUB)
# ==========================================
st.header("2️⃣ Tahap 2: Analisis Kapasitas (Volume Disrub)")
total_akumulasi = cargo_vol + rob_vol
disrub_vol = total_akumulasi - safe_limit

if disrub_vol > 0:
    st.warning(f"⚠️ **RISIKO OVERFILL TERDETEKSI:** Total kargo + ROB mencapai **{total_akumulasi:,.0f} m³**.")
    st.markdown(f"**Tindakan Wajib:** Selama proses bongkar, Anda harus memastikan gas diserap ke darat minimal sebesar **{disrub_vol:,.0f} m³** (Volume Disrub).")
else:
    disrub_vol = 0
    st.success(f"✅ **KAPASITAS AMAN:** Total kargo + ROB hanya **{total_akumulasi:,.0f} m³** (Tidak melampaui batas aman 122.500 m³). Tidak ada paksaan serapan.")

st.divider()

# ==========================================
# TAHAP 3: SIMULATOR KEPUTUSAN (INTERAKTIF)
# ==========================================
st.header("3️⃣ Tahap 3: Skenario Rate & Laytime (Interaktif)")
st.markdown("💡 *Geser slider di bawah ini untuk menentukan target durasi operasi. Kecepatan pompa (Rate) akan terkalkulasi otomatis secara real-time.*")

# Slider interaktif untuk waktu operasi
col_slider, col_buffer = st.columns([2, 1])
with col_slider:
    target_laytime = st.slider(
        "Tentukan Target Total Waktu Operasi (Jam)", 
        min_value=24.0, 
        max_value=42.0, 
        value=35.0, 
        step=0.5,
        help="Batas maksimal kontrak biasanya 42 Jam. Hindari menyentuh angka ini untuk mencegah Demurrage."
    )
with col_buffer:
    buffer_time = st.number_input(
        "Alokasi Waktu Buffer (Jam)", 
        value=4.0, 
        step=0.5,
        help="Waktu tambahan untuk Draining, Purging, dan pelepasan Loading Arm."
    )

# Kalkulasi Waktu Pompa Murni
waktu_pompa_murni = target_laytime - buffer_time

if waktu_pompa_murni <= 0:
    st.error("Target Waktu Operasi terlalu singkat dibandingkan Waktu Buffer!")
else:
    # Kalkulasi Rates
    loading_rate = cargo_vol / waktu_pompa_murni
    regas_rate = disrub_vol / target_laytime if disrub_vol > 0 else 0
    
    # Tampilan Hasil Output
    st.markdown("### 🎯 Rekomendasi Instruksi (Action Plan)")
    res_col1, res_col2, res_col3 = st.columns(3)
    
    res_col1.metric("1. Durasi Bongkar Murni", f"{waktu_pompa_murni} Jam")
    res_col2.metric("2. Loading Rate (Ke Kapal)", f"{loading_rate:,.0f} m³/jam")
    res_col3.metric("3. Regas Rate (Ke Darat/PLN)", f"{regas_rate:,.0f} m³/jam")
    
    # Indikator Keamanan Skenario
    st.write("**Evaluasi Skenario:**")
    if target_laytime >= 40.0:
        st.error("🚨 Skenario Berisiko: Waktu sangat mepet dengan batas penalti Demurrage (42 jam). Kurangi target waktu!")
    elif loading_rate > 4500:
        st.warning("⚠️ Skenario Berisiko: Loading Rate ke kapal terlalu tinggi. Pastikan pompa LNGC sanggup mencapai angka ini.")
    else:
        st.success("✅ Skenario Optimal: Waktu aman dari penalti, dan beban kecepatan pompa berada di batas normal.")
