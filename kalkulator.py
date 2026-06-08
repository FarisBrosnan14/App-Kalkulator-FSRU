import streamlit as st

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Ops Dashboard - Nusantara Regas", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Discharging Operations Tool")
st.markdown("Automated calculation for **Custody Transfer Officer (CTO)**")
st.divider()

# Membuat 3 Tab Berbeda
tab1, tab2, tab3 = st.tabs(["⏳ Laytime Calculator", "🔥 Serapan (Disrub) & Capacity", "📊 Rate Finder"])

# ==========================================
# TAB 1: MENGHITUNG LAYTIME (WAKTU)
# ==========================================
with tab1:
    st.subheader("⏳ Estimasi Durasi Bongkar (Laytime)")
    st.info("Gunakan tab ini untuk mengetahui berapa lama waktu yang dibutuhkan berdasarkan kecepatan pompa kapal saat ini.")
    
    col1, col2 = st.columns(2)
    with col1:
        cargo_vol = st.number_input("Total Kargo Kapal (m³)", min_value=1.0, value=125000.0, step=1000.0, key="t1_vol")
        current_rate = st.number_input("Loading Rate Saat Ini (m³/jam)", min_value=1.0, value=4000.0, step=100.0, key="t1_rate")
    
    with col2:
        buffer_time = st.slider("Buffer Waktu (Draining/Purging/Arm Discon) - Jam", 0.0, 10.0, 4.0)
        
    duration = cargo_vol / current_rate
    total_laytime = duration + buffer_time
    
    st.divider()
    res_col1, res_col2 = st.columns(2)
    res_col1.metric("Durasi Bongkar Murni", f"{duration:.1f} Jam")
    res_col2.metric("Total Estimasi Laytime (+Buffer)", f"{total_laytime:.1f} Jam")
    
    if total_laytime > 42.0:
        st.error(f"⚠️ **RISIKO DEMURRAGE:** Total waktu ({total_laytime:.1f} Jam) melebihi batas kontrak 42 Jam!")
    else:
        st.success(f"✅ **AMAN:** Masih tersisa {42.0 - total_laytime:.1f} Jam sebelum batas demurrage.")

# ==========================================
# TAB 2: MENGHITUNG SERAPAN (DISRUB)
# ==========================================
with tab2:
    st.subheader("🔥 Kalkulasi Serapan Gas (Volume Disrub)")
    st.info("Gunakan tab ini untuk menghitung berapa banyak gas yang harus diserap ke darat agar tangki FSRU tidak meluap (Overfill).")
    
    col1, col2 = st.columns(2)
    with col1:
        rob_start = st.number_input("ROB FSRU Saat Mulai Bongkar (m³)", min_value=0.0, value=20000.0, step=500.0, key="t2_rob")
        cargo_to_unload = st.number_input("Volume Kargo yang Akan Masuk (m³)", min_value=0.0, value=125000.0, step=1000.0, key="t2_cargo")
    
    with col2:
        max_limit = st.number_input("Batas Aman Tangki (98% Level) - m³", value=122500.0, disabled=True)
        laytime_target = st.number_input("Target Waktu Operasi (Jam)", min_value=1.0, value=36.0, key="t2_time")

    total_accumulation = rob_start + cargo_to_unload
    disrub_vol = total_accumulation - max_limit
    
    st.divider()
    if disrub_vol > 0:
        st.warning(f"⚠️ **OVERFILL RISK:** Anda harus membuang/menyerap sebesar **{disrub_vol:,.0f} m³** kargo.")
        needed_regas_rate = disrub_vol / laytime_target
        st.metric("Minimal Regas Rate (Serapan Darat)", f"{needed_regas_rate:,.0f} m³/jam")
        st.write(f"Hubungi Dispatcher: Pastikan serapan minimal {needed_regas_rate:,.0f} m³ per jam selama proses bongkar.")
    else:
        st.success("✅ **SAFE CAPACITY:** Tangki FSRU cukup untuk menampung seluruh kargo tanpa bantuan serapan ekstra.")

# ==========================================
# TAB 3: MENGHITUNG RATE (PENCARI RATE)
# ==========================================
with tab3:
    st.subheader("📊 Mencari Loading Rate Optimal")
    st.info("Gunakan tab ini jika Anda punya tenggat waktu (misal: harus selesai dalam 32 jam) dan ingin tahu berapa rate pompa yang harus diminta ke kapal.")
    
    col1, col2 = st.columns(2)
    with col1:
        cargo_target = st.number_input("Total Kargo Kapal (m³)", min_value=1.0, value=125000.0, key="t3_vol")
    with col2:
        time_limit = st.number_input("Deadline Waktu Bongkar Murni (Jam)", min_value=1.0, value=34.0, key="t3_time")
    
    required_rate = cargo_target / time_limit
    
    st.divider()
    st.metric("Rekomendasi Loading Rate ke Kapal", f"{required_rate:,.0f} m³/jam")
    st.write(f"**Instruksi:** Minta Chief Officer Kapal untuk maintain rate di **{required_rate:,.0f} m³/jam**.")
    
    if required_rate > 4500:
        st.warning("⚠️ Peringatan: Rate di atas 4500 m³/jam mungkin melebihi kapasitas standar pompa kapal tertentu. Cek spesifikasi kapal saat Pre-Cargo Meeting!")

# Footer
st.divider()
st.caption("FSRU Jawa Barat - PT Nusantara Regas | Dashboard by Faris")
