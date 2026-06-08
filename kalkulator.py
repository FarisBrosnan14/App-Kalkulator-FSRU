import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title="Kalkulator Kargo FSRU", page_icon="🚢", layout="centered")

st.title("🧮 Kalkulator Discharging Plan FSRU")
st.markdown("*Tools otomatisasi perhitungan target operasional (Skenario Pak Suci)*")
st.divider()

# ==========================================
# 1. INPUT DATA DARI USER
# ==========================================
st.subheader("📝 1. Input Parameter Lapangan")
col1, col2 = st.columns(2)

with col1:
    vol_kargo = st.number_input("Total Kargo Kapal (m³)", min_value=0, value=130000, step=1000)
    rob_hari_h = st.number_input("ROB FSRU Hari H pukul 00:00 (m³)", min_value=0, value=25000, step=500)
    serapan_harian = st.number_input("Rata-rata Serapan PLN (m³/hari)", min_value=0, value=17000, step=500)

with col2:
    jam_commence = st.number_input("Estimasi Jam Commence Discharge (0-24)", min_value=0.0, max_value=24.0, value=14.0, step=0.5, help="Misal: Jika mulai jam 14:30, ketik 14.5")
    target_waktu = st.number_input("Target Waktu Selesai/Laytime (Jam)", min_value=1.0, value=35.0, step=0.5)
    batas_aman = st.number_input("Batas Aman Kapasitas FSRU (m³)", value=122500, disabled=True)

# ==========================================
# 2. PROSES KALKULASI LOGIKA
# ==========================================
# A. Hitung Serapan per Jam
serapan_per_jam = serapan_harian / 24

# B. Hitung ROB saat Commence
gas_terpakai_menunggu = serapan_per_jam * jam_commence
rob_commence = rob_hari_h - gas_terpakai_menunggu

# C. Hitung Volume Disrub (Gas wajib dibuang agar tidak overflow)
total_akumulasi = rob_commence + vol_kargo
volume_disrub = total_akumulasi - batas_aman

# D. Hitung Rates
loading_rate = vol_kargo / target_waktu
regas_rate = volume_disrub / target_waktu if volume_disrub > 0 else 0

# ==========================================
# 3. TAMPILAN HASIL (OUTPUT)
# ==========================================
st.divider()
st.subheader("🎯 2. Hasil Rekomendasi Operasional")

# Tampilan ROB Commence
st.info(f"**Prediksi ROB Saat Commence (Jam {jam_commence}):** {rob_commence:,.0f} m³")

# Tampilan Peringatan Kapasitas
if volume_disrub > 0:
    st.warning(f"⚠️ **Peringatan Kapasitas:** Tangki akan overfill sebesar **{volume_disrub:,.0f} m³** jika gas tidak diserap.")
else:
    st.success("✅ **Kapasitas Aman:** Total kargo masuk tidak melebihi batas aman tangki FSRU (Tidak ada risiko overflow).")

# Tampilan Rekomendasi Rate
st.markdown("### 📊 Instruksi Rate yang Diperlukan:")
col_res1, col_res2 = st.columns(2)

with col_res1:
    st.metric(label="Kapal: TARGET LOADING RATE", value=f"{loading_rate:,.0f} m³/jam", help="Instruksikan angka ini ke Chief Officer LNGC")

with col_res2:
    st.metric(label="Darat: TARGET REGAS RATE", value=f"{regas_rate:,.0f} m³/jam", help="Instruksikan angka serapan minimal ini ke Dispatcher/P2B")

# ==========================================
# 4. KESIMPULAN TINDAKAN (ACTION PLAN)
# ==========================================
st.divider()
st.subheader("📌 Kesimpulan Tindakan (Action Plan)")
if volume_disrub > 0:
    st.write(f"1. Instruksikan Kapal LNGC untuk mempertahankan *Loading Rate* stabil di kisaran **{loading_rate:,.0f} m³/jam** agar selesai dalam {target_waktu} jam.")
    st.write(f"2. Hubungi *Control Room* / Dispatcher PLN untuk memastikan serapan darat dipertahankan minimal di angka **{regas_rate:,.0f} m³/jam**.")
    if regas_rate > (serapan_per_jam + 200): # Jika regas rate yang dibutuhkan jauh lebih tinggi dari normal
        st.error("🚨 **CRITICAL ALERT:** Target Regas Rate jauh lebih tinggi dari serapan harian normal PLN. Segera koordinasi dengan komersial/P2B, atau turunkan Loading Rate kapal (tambah waktu laytime)!")
else:
    st.write(f"Instruksikan Kapal LNGC untuk mempertahankan *Loading Rate* stabil di kisaran **{loading_rate:,.0f} m³/jam**. Operasi terpantau sangat aman.")