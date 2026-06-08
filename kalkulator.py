import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Ops Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Discharging Plan Simulator")
st.markdown("Dashboard interaktif operasional **Custody Transfer Officer**")
st.divider()

# Membuat 3 Tab Utama
tab_param, tab_skenario, tab_esod = st.tabs([
    "📋 1. Parameter & Risiko", 
    "⚙️ 2. Skenario Kalkulasi", 
    "📅 3. Jadwal ESOD"
])

# ==========================================
# TAB 1: KONDISI AWAL & WAKTU ACUAN
# ==========================================
with tab_param:
    st.header("Parameter Kargo & Kapasitas FSRU")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        cargo_vol = st.number_input("Volume Kargo Masuk (m³)", min_value=10000.0, value=130000.0, step=1000.0)
    with col2:
        rob_acuan = st.number_input("ROB FSRU pada Waktu Acuan (m³)", min_value=0.0, value=25000.0, step=500.0)
    with col3:
        serapan_harian = st.number_input("Rata-rata Serapan PLN (m³/hari)", min_value=0.0, value=17000.0, step=500.0)

    st.markdown("#### ⏳ Kalkulasi Waktu & ROB Commence")
    st.info("💡 Sesuai SOP, estimasi waktu Commence (Mulai Bongkar) diatur otomatis 8 jam setelah kapal tiba (ETA).")
    
    col_waktu1, col_waktu2 = st.columns(2)
    with col_waktu1:
        st.write("**1. Waktu Acuan Pencatatan ROB**")
        col_tgl1, col_jam1 = st.columns(2)
        with col_tgl1:
            tgl_acuan = st.date_input("Tanggal Acuan", key="tgl_acuan")
        with col_jam1:
            jam_acuan = st.time_input("Jam Acuan (LCT)", value=pd.to_datetime("00:00").time(), key="jam_acuan")
        waktu_acuan = datetime.combine(tgl_acuan, jam_acuan)

    with col_waktu2:
        st.write("**2. Waktu Kedatangan Kapal (ETA / POB)**")
        col_tgl2, col_jam2 = st.columns(2)
        with col_tgl2:
            tgl_eta = st.date_input("Tanggal ETA", key="tgl_eta")
        with col_jam2:
            jam_eta = st.time_input("Jam ETA (LCT)", value=pd.to_datetime("06:00").time(), key="jam_eta")
        waktu_eta = datetime.combine(tgl_eta, jam_eta)

    # Logika Waktu Commence (ETA + 8 Jam)
    waktu_commence = waktu_eta + timedelta(hours=8)
    
    # Kalkulasi Selisih Waktu (dalam Jam)
    selisih_jam = (waktu_commence - waktu_acuan).total_seconds() / 3600.0

    st.markdown("---")
    
    if selisih_jam < 0:
        st.error("⚠️ Peringatan: Waktu Commence terdeteksi lebih awal dari Waktu Acuan ROB. Harap periksa kembali input tanggal dan jam Anda.")
        rob_commence = rob_acuan
        gas_terpakai_menunggu = 0
        total_akumulasi = cargo_vol + rob_commence
        disrub_vol = 0
    else:
        serapan_per_jam = serapan_harian / 24.0
        gas_terpakai_menunggu = serapan_per_jam * selisih_jam
        rob_commence = rob_acuan - gas_terpakai_menunggu
        
        col_res1, col_res2 = st.columns(2)
        col_res1.metric("Waktu Commence (ETA + 8 Jam)", waktu_commence.strftime("%d-%b-%Y %H:%M"))
        col_res2.metric("Estimasi ROB Saat Commence", f"{rob_commence:,.0f} m³", f"-{gas_terpakai_menunggu:,.0f} m³ (Terpakai selama {selisih_jam:.1f} jam menunggu)", delta_color="inverse")

        # Analisis Kapasitas
        safe_limit = 122500.0
        total_akumulasi = cargo_vol + rob_commence
        disrub_vol = total_akumulasi - safe_limit

        st.subheader("📝 Narasi Analisa Operasional")
        if disrub_vol > 0:
            status_tangki = "berisiko **OVERFILL** karena melampaui batas aman 122.500 m³"
            tindakan = f"Oleh karena itu, wajib dipastikan adanya serapan gas ke darat (Disrub) minimal sebesar **{disrub_vol:,.0f} m³** selama proses bongkar muat."
            st.warning(f"⚠️ **OVERFILL RISK:** Total kargo + ROB mencapai **{total_akumulasi:,.0f} m³**.")
        else:
            disrub_vol = 0
            status_tangki = "dalam kondisi **AMAN**"
            tindakan = "Kapasitas tangki FSRU memadai untuk menampung seluruh kargo tanpa paksaan serapan ekstra."
            st.success(f"✅ **KAPASITAS AMAN:** Total kargo + ROB hanya **{total_akumulasi:,.0f} m³**.")
            
        narasi = f"""
        Berdasarkan data manifest, LNGC dijadwalkan tiba (ETA) pada **{waktu_eta.strftime('%d %B %Y pukul %H:%M LCT')}**. 
        Mengacu pada standar prosedur, operasi discharging (Commence) diestimasikan mulai 8 jam setelah ETA, yakni pada **{waktu_commence.strftime('%d %B %Y pukul %H:%M LCT')}**. 
        
        Selama periode tunggu dari waktu acuan pencatatan ROB hingga commence ({selisih_jam:.1f} jam), fasilitas PLN diperkirakan akan menyerap gas sebesar **{gas_terpakai_menunggu:,.0f} m³**. 
        Penyerapan ini menyebabkan ROB FSRU pada saat commence akan turun ke level **{rob_commence:,.0f} m³**. 
        
        Memperhitungkan tambahan kargo yang akan dibongkar sebesar **{cargo_vol:,.0f} m³**, total akumulasi volume cairan di dalam tangki FSRU akan mencapai **{total_akumulasi:,.0f} m³**. 
        Proyeksi ini menunjukkan bahwa operasi berada {status_tangki}. {tindakan}
        """
        st.info(narasi)

# ==========================================
# TAB 2: KALKULASI KEBUTUHAN RATE & WAKTU
# ==========================================
with tab_skenario:
    st.header("Simulasi Kebutuhan Rate vs Target Waktu")
    st.info("Pilih pendekatan yang paling sesuai dengan instruksi operasional saat ini.")

    col_skenario_a, col_skenario_b = st.columns(2)

    with col_skenario_a:
        st.markdown("### 🎯 Skenario A: Target Waktu")
        st.caption("Jika Anda dikejar batas waktu Laytime kontrak")
        target_laytime = st.number_input("Target Total Laytime (Jam)", min_value=1.0, value=35.0, step=0.5)
        buffer_time_a = st.number_input("Alokasi Waktu Buffer (Jam)", value=4.0, step=0.5, key="buf_a")
        
        waktu_murni_a = target_laytime - buffer_time_a
        req_loading_rate = cargo_vol / waktu_murni_a if waktu_murni_a > 0 else 0
        req_regas_rate_a = disrub_vol / target_laytime if disrub_vol > 0 else 0
        
        st.success(f"🔹 **Minta Loading Rate Kapal:** {req_loading_rate:,.0f} m³/jam")
        st.success(f"🔹 **Target Regas Rate Darat:** {req_regas_rate_a:,.0f} m³/jam")

    with col_skenario_b:
        st.markdown("### ⚓ Skenario B: Target Rate")
        st.caption("Jika Rate pompa LNGC sudah disepakati (Fix)")
        input_loading_rate = st.number_input("Rencana Loading Rate (m³/jam)", min_value=100.0, value=3900.0, step=100.0)
        buffer_time_b = st.number_input("Alokasi Waktu Buffer (Jam)", value=4.0, step=0.5, key="buf_b")
        
        waktu_murni_b = cargo_vol / input_loading_rate
        total_laytime_b = waktu_murni_b + buffer_time_b
        req_regas_rate_b = disrub_vol / total_laytime_b if disrub_vol > 0 else 0
        
        st.info(f"⏳ **Estimasi Waktu Bongkar Murni:** {waktu_murni_b:.1f} Jam")
        st.info(f"⏳ **Estimasi Total Waktu Laytime:** {total_laytime_b:.1f} Jam")
        st.info(f"🔹 **Target Regas Rate Darat:** {req_regas_rate_b:,.0f} m³/jam")

    st.divider()
    st.markdown("### 📤 Pengaturan Ekspor ke ESOD")
    pilihan_skenario = st.radio(
        "Pilih hasil skenario mana yang akan dikirim ke tabel Jadwal (ESOD) di Tab 3:", 
        ["Gunakan Skenario A (Berdasarkan Waktu)", "Gunakan Skenario B (Berdasarkan Rate)"]
    )

    if pilihan_skenario == "Gunakan Skenario A (Berdasarkan Waktu)":
        final_waktu_murni = waktu_murni_a
    else:
        final_waktu_murni = waktu_murni_b

# ==========================================
# TAB 3: ESTIMATION SCHEDULE (ESOD)
# ==========================================
with tab_esod:
    st.header("Estimation Schedule Operational Discharging (ESOD)")
    st.info("💡 Jadwal kedatangan (ETA) sudah ditarik otomatis dari Tab 1. Durasi 'Bongkar Muat Murni' menyesuaikan skenario dari Tab 2.")

    # Menggunakan waktu_eta dari Tab 1 sebagai titik awal
    start_datetime = waktu_eta
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
        st.markdown("**✍️ Data Editor: Sesuaikan Durasi (Menit)**")
        edited_df = st.data_editor(
            df_default,
            column_config={
                "Kegiatan": st.column_config.TextColumn("Kegiatan", disabled=True),
                "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
            },
            hide_index=True, use_container_width=True, height=550
        )

    with col_result:
        st.markdown(f"**📅 Proyeksi Jadwal Final (Mulai dari ETA: {waktu_eta.strftime('%d-%b %H:%M')})**")
        
        schedule_result = []
        current_time = start_datetime
        
        for index, row in edited_df.iterrows():
            durasi = row["Durasi (Menit)"]
            start_time = current_time
            end_time = current_time + timedelta(minutes=int(durasi))
            
            schedule_result.append({
                "Kegiatan": row["Kegiatan"],
                "Durasi": f"{durasi} mnt",
                "Mulai": start_time.strftime("%d-%b %H:%M"),
                "Selesai": end_time.strftime("%d-%b %H:%M")
            })
            current_time = end_time
            
        df_result = pd.DataFrame(schedule_result)
        st.dataframe(df_result, use_container_width=True, hide_index=True, height=550)
