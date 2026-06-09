import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# ==========================================
# 1. INJEKSI TEMA WARNA CUSTOM (DARK NAVY)
# ==========================================
# Memaksa server menggunakan palet warna spesifik yang meniru referensi gambar
if not os.path.exists(".streamlit/config.toml"):
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/config.toml", "w") as f:
        f.write("""
[theme]
base="dark"
primaryColor="#0ea5e9"
backgroundColor="#0f172a"
secondaryBackgroundColor="#1e293b"
textColor="#f8fafc"
font="sans serif"
""")

# Konfigurasi Halaman 
st.set_page_config(page_title="CTO Dashboard NR", page_icon="🚢", layout="wide")

# ==========================================
# 2. INJEKSI CUSTOM CSS TINGKAT LANJUT
# ==========================================
st.markdown("""
<style>
    /* Menyembunyikan elemen bawaan Streamlit agar terlihat seperti Web App murni */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    
    /* Kustomisasi Top Bar (Pill Putih) */
    .top-bar {
        background-color: #ffffff;
        border-radius: 20px;
        padding: 15px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }
    .top-bar-title {
        color: #0f172a;
        font-size: 24px;
        font-weight: 800;
        margin: 0;
        text-align: center;
        flex-grow: 1;
    }
    .top-bar-subtitle {
        color: #64748b;
        font-size: 14px;
        font-weight: 500;
        text-align: center;
    }
    .profile-pill {
        background-color: #f1f5f9;
        color: #0f172a;
        padding: 8px 20px;
        border-radius: 20px;
        font-weight: 600;
        font-size: 14px;
        border: 1px solid #e2e8f0;
    }

    /* Kustomisasi Info Widget Row */
    .info-widget-row {
        display: flex;
        gap: 15px;
        margin-bottom: 30px;
        flex-wrap: wrap;
    }
    .info-widget {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px 20px;
        flex: 1;
        min-width: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
        box-shadow: inset 0 0 10px rgba(0,0,0,0.2);
    }
    .time-text {
        font-size: 28px;
        font-weight: 800;
        color: #38bdf8;
        text-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }
    .date-text {
        font-size: 18px;
        font-weight: 600;
        color: #f8fafc;
    }
    .status-badge {
        background-color: #eab308;
        color: #0f172a;
        padding: 6px 15px;
        border-radius: 8px;
        font-weight: 800;
        font-size: 14px;
    }

    /* Kustomisasi Tab Streamlit */
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1e293b !important;
        border-radius: 8px 8px 0px 0px;
        border: 1px solid #334155;
        border-bottom: none;
        padding: 10px 20px;
        color: #94a3b8;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0ea5e9 !important;
        color: #ffffff !important;
        border: 1px solid #0ea5e9;
        box-shadow: 0 -4px 10px rgba(14, 165, 233, 0.3);
    }
    
    /* Metric Card Styling */
    [data-testid="stMetric"] {
        background-color: #1e293b;
        border: 1px solid #334155;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. MEMBANGUN HEADER & WIDGET (Sesuai Referensi)
# ==========================================
# Header Putih
st.markdown("""
<div class="top-bar">
    <div style="font-size: 24px;">🏠 🚢</div>
    <div>
        <div class="top-bar-title">Dashboard Operasional FSRU Nusantara Regas</div>
        <div class="top-bar-subtitle">Sistem Panduan Alur Kerja & Custody Transfer Officer</div>
    </div>
    <div class="profile-pill">🔔 Halo, Faris (CTO)</div>
</div>
""", unsafe_allow_html=True)

# Widget Info Bar (Menyimulasikan jam saat ini)
now = datetime(2026, 6, 9, 16, 4)
st.markdown(f"""
<div class="info-widget-row">
    <div class="info-widget">
        <div class="time-text">⏱️ {now.strftime('%H:%M:%S')}</div>
        <div class="date-text">Sel, 9 Jun 2026</div>
    </div>
    <div class="info-widget">
        <div style="color: #ef4444; font-size: 24px;">📍</div>
        <div>
            <div style="font-weight: 700; font-size: 14px;">Teluk Jakarta</div>
            <div style="color: #94a3b8; font-size: 12px;">Koordinat FSRU</div>
        </div>
    </div>
    <div class="info-widget">
        <div style="color: #eab308; font-size: 24px;">⛅</div>
        <div>
            <div style="font-weight: 700; font-size: 14px;">Berawan • 31.3°C</div>
            <div style="color: #94a3b8; font-size: 12px;">🌬️ 14.3 km/h Timur</div>
        </div>
    </div>
    <div class="info-widget">
        <div class="status-badge">📢 STANDBY OPS</div>
    </div>
</div>
""", unsafe_allow_html=True)


# Inisialisasi Session State ESOD
if "durations" not in st.session_state:
    st.session_state.durations = {
        "All Fast": 180, "NOR Received": 55, "ARMs Connected": 30,
        "OPEN CTM": 35, "WARM ESD Test": 15, "Arm C/D": 90,
        "COLD ESD Test": 15, "START DISCHARGING": 20, "FULL RATE": 30,
        "Bongkar Muat Murni (Rate Down)": 2100,
        "DISCHARGING COMPLETED": 30, "CLOSING CTM": 120,
        "ARMs Disconnected": 10, "Documentation": 60, "POB OUT": 120
    }
    st.session_state.last_waktu_murni = 0.0

# ==========================================
# 4. TAB NAVIGASI UTAMA
# ==========================================
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "📋 Fase 1: H-1 (Pre-Arrival)", 
    "⚓ Fase 2: Hari H (Sandar)", 
    "📡 Fase 3: Monitoring",
    "📝 Fase 4: Final Report"
])

# ==========================================
# FASE 1: H-1 (PRE-ARRIVAL & ADMINISTRASI)
# ==========================================
with tab_h1:
    with st.expander("📌 PENGUMUMAN & TO-DO LIST HARI INI ✨ BARU", expanded=True):
        col_doc_h1_a, col_doc_h1_b = st.columns(2)
        with col_doc_h1_a:
            st.info("""
            **📋 Dokumen untuk Diperiksa:**
            * **Cargo Manifest:** Periksa data muatan asal dari kilang penyuplai.
            * **Arrival LNG Declaration:** Pernyataan resmi dari Kapten LNGC.
            * **Sertifikat & MCU:** Pastikan dokumen BSS/BOSIET dan tensi darah personel valid. Wajib dapat clearance Dokter Perusahaan.
            """)
            
        with col_doc_h1_b:
            st.warning("""
            **📧 Email yang Harus Dikirim:**
            * **Draft Report & Unloading Plan:** Skema simulasi pembongkaran awal.
            * **POB List:** Daftar manifes personel yang akan naik ke FSRU (Kirim ke Keagenan).
            * **Request Hutasuhut (Transport Boat):** Order kapal jemputan untuk tim operasi.
            """)

    st.markdown("### 🧮 Kalkulator Awal Risiko & ROB (Worst Case Scenario)")
    col1, col2, col3 = st.columns(3)
    with col1:
        cargo_vol = st.number_input("Rencana Kargo Masuk (m³)", min_value=10000.0, value=130000.0, step=1000.0)
    with col2:
        rob_awal = st.number_input("Pencatatan ROB Awal (m³)", min_value=0.0, value=42000.0, step=500.0)
    with col3:
        serapan_harian = st.number_input("Target Serapan Gas PLN (m³/hari)", min_value=0.0, value=17000.0, step=500.0)

    st.markdown("#### ⏳ Sinkronisasi Waktu Acuan")
    col_waktu1, col_waktu2 = st.columns(2)
    with col_waktu1:
        st.info("**1. Waktu Pencatatan ROB Awal**")
        col_d1, col_t1 = st.columns(2)
        with col_d1:
            tgl_rob = st.date_input("Tanggal ROB", datetime(2026, 6, 9))
        with col_t1:
            jam_rob = st.time_input("Jam ROB (LCT)", value=pd.to_datetime("00:00").time())
        waktu_rob = datetime.combine(tgl_rob, jam_rob)

    with col_waktu2:
        st.info("**2. Waktu Kedatangan Kapal (ETA)**")
        col_d2, col_t2 = st.columns(2)
        with col_d2:
            tgl_eta = st.date_input("Tanggal ETA", datetime(2026, 6, 10))
        with col_t2:
            jam_eta = st.time_input("Jam ETA (LCT)", value=pd.to_datetime("06:00").time())
        waktu_eta = datetime.combine(tgl_eta, jam_eta)
        
    waktu_commence = waktu_eta + timedelta(hours=8)
    st.markdown(f"👉 <span style='color:#38bdf8; font-weight:bold;'>Proyeksi Skenario Mulai Commence (ETA + 8 Jam):</span> **{waktu_commence.strftime('%d-%b-%Y %H:%M LCT')}**", unsafe_allow_html=True)
    target_jam_bongkar = st.number_input("Target Waktu Durasi Pompa Murni (Jam)", min_value=1.0, value=35.0, step=0.5)

    st.markdown("---")
    selisih_jam = (waktu_commence - waktu_rob).total_seconds() / 3600.0

    if selisih_jam < 0:
        st.error("⚠️ Peringatan: Waktu pencatatan ROB Awal terdeteksi lebih akhir dari target Commence!")
    else:
        serapan_matematis = (serapan_harian / 24.0) * selisih_jam
        default_worst_case = float(int(serapan_matematis / 1000) * 1000)
        
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            st.write(f"Durasi tunggu ROB hingga Commence: **{selisih_jam:.1f} Jam**")
            st.caption(f"Hitungan Matematis Murni: {serapan_matematis:,.0f} m³")
        with col_calc2:
            worst_case_serapan = st.number_input("Serapan Aktual / Worst Case (m³)", value=default_worst_case, step=500.0)

        rob_commence = rob_awal - worst_case_serapan
        volume_disrub = (rob_commence + cargo_vol) - 122500.0 
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(f"Estimasi ROB Commence", f"{rob_commence:,.0f} m³", f"-{worst_case_serapan:,.0f} m³", delta_color="inverse")
        
        if volume_disrub > 0:
            col_res2.metric("Wajib Serap Darat (Disrub)", f"{volume_disrub:,.0f} m³", "Risiko Overfill!")
        else:
            volume_disrub = 0
            col_res2.metric("Wajib Serap Darat (Disrub)", "0 m³", "Kapasitas Aman", delta_color="normal")
            
        kebutuhan_loading_raw = cargo_vol / target_jam_bongkar if target_jam_bongkar > 0 else 0
        kebutuhan_loading_bulat = int(kebutuhan_loading_raw / 100) * 100
        col_res3.metric("Rekomendasi Loading Rate", f"{kebutuhan_loading_bulat:,.0f} m³/h")

    current_waktu_murni_minutes = int(target_jam_bongkar * 60)
    if st.session_state.last_waktu_murni != target_jam_bongkar:
        st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = current_waktu_murni_minutes
        st.session_state.last_waktu_murni = target_jam_bongkar

# ==========================================
# FASE 2: HARI H (SANDAR & PERTEMUAN)
# ==========================================
with tab_sandar:
    with st.expander("📌 TO-DO LIST: Discharging Activity (Preparation)", expanded=False):
        st.markdown("""
        * **1. Report to ISPS Post:** Lapor pos dan jalankan prosedur ISPS sebelum keberangkatan.
        * **2. Coordination & Trip:** Koordinasi dengan Master NRS & Tim, berangkat menuju FSRU.
        * **3. Monitoring STS until All Fast:** Awasi pergerakan manuver *Ship-to-Ship* sampai kapal diikat sempurna (*All Fast*).
        * **4. Pre-cargo Meeting & L/A Connected:** Lakukan rapat dengan LNGC (ideal 30 menit setelah *All Fast*) dan pastikan lengan kargo tersambung.
        * **5. Opening CTM:** Ambil snapshot radar. Minta kru menahan aktivitas crane agar kondisi kapal stabil.
        * **6. Supervision of Preparation Process:** Lakukan *Warm ESD Test*, *Arm Cooldown*, hingga *Cold ESD Test*.
        """)

    st.markdown("### 📅 Tinjauan Rantai Waktu (ESOD)")
    st.caption("💡 **Mobile Friendly Editor:** Tap angka menit atau jam untuk mengedit. Tabel otomatis mengoreksi jam kegiatan lainnya!")

    events = [
        "ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", 
        "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", 
        "FULL RATE", "Bongkar Muat Murni (Rate Down)", "DISCHARGING COMPLETED", 
        "CLOSING CTM", "ARMs Disconnected", "Documentation", "POB OUT"
    ]

    datetimes_list = []
    current_dt = waktu_eta
    datetimes_list.append(current_dt) 
    
    for ev in events[1:]:
        dur = st.session_state.durations[ev]
        current_dt = current_dt + timedelta(minutes=int(dur))
        datetimes_list.append(current_dt)

    df_esod = pd.DataFrame({
        "Event": events,
        "Date / Time": datetimes_list,
        "Durasi (Menit)": [0] + [st.session_state.durations[ev] for ev in events[1:]]
    })

    edited_table = st.data_editor(
        df_esod,
        column_config={
            "Event": st.column_config.TextColumn("Event", disabled=True),
            "Date / Time": st.column_config.DatetimeColumn("Date / Time", format="DD-MMM / HH:mm"),
            "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
        },
        hide_index=True,
        use_container_width=True,
        key="esod_editor"
    )

    if "esod_editor" in st.session_state and st.session_state.esod_editor["edited_rows"]:
        edited_rows = st.session_state.esod_editor["edited_rows"]
        for row_idx, changes in edited_rows.items():
            row_idx = int(row_idx)
            if row_idx == 0: continue
            ev_name = events[row_idx]
            if "Durasi (Menit)" in changes:
                st.session_state.durations[ev_name] = int(changes["Durasi (Menit)"])
            elif "Date / Time" in changes:
                new_dt = pd.to_datetime(changes["Date / Time"])
                prev_dt = df_esod.loc[row_idx - 1, "Date / Time"]
                new_calculated_dur = int((new_dt - prev_dt).total_seconds() / 60)
                if new_calculated_dur >= 0:
                    st.session_state.durations[ev_name] = new_calculated_dur
        del st.session_state["esod_editor"]
        st.rerun()

# ==========================================
# FASE 3: MONITORING (BONGKAR & UPDATE)
# ==========================================
with tab_monitor:
    with st.expander("📌 TO-DO LIST: Discharging Activity (Execution)", expanded=True):
        st.markdown("""
        * **1. Collect Data:** Kumpulkan bukti *Open CTM* (NRS & LNGC). Ambil snapshot 30 menit & 15 menit sebelum *Commence Loading*.
        * **2. Send Email Report Start Discharging:** Rilis email resmi segera setelah menembus *Full Rate*.
        * **3. Monitoring & Coordination:** Kawal rutin di grup WhatsApp. Pantau aliran penyerapan PLN.
        """)

    st.markdown("### 🧮 Kalkulator Progres Penurunan Aliran (LNG To Go)")
    col_togo1, col_togo2 = st.columns(2)
    with col_togo1:
        current_time_input = st.time_input("Jam Pengecekan Lapangan Saat Ini (LCT)", value=pd.to_datetime("02:00").time())
        sisa_kargo_togo = st.number_input("Sisa Kargo Belum Dibongkar / LNG To Go (m³)", min_value=0.0, value=32029.0)
        current_rate = st.number_input("Laju Kecepatan Pompa Kapal Aktual (m³/h)", min_value=1.0, value=4000.0)
        
    with col_togo2:
        sisa_jam = sisa_kargo_togo / current_rate
        waktu_sekarang = datetime.combine(datetime.today(), current_time_input)
        estimasi_selesai = waktu_sekarang + timedelta(hours=sisa_jam)
        
        st.metric("Estimasi Sisa Durasi", f"{sisa_jam:.1f} Jam")
        st.metric("Proyeksi Katup Ditutup", estimasi_selesai.strftime("%H:%M LCT"))

# ==========================================
# FASE 4: SELESAI (PENUTUPAN & PELAPORAN)
# ==========================================
with tab_closing:
    with st.expander("📌 TO-DO LIST: Dokumentasi Akhir & POB Out", expanded=False):
        col_doc_c_a, col_doc_c_b = st.columns(2)
        with col_doc_c_a:
            st.info("""
            **📋 Dokumen Pengesahan:**
            * **Closing CTM Printout:** Dicetak pasca *Draining & Purging* rampung.
            * **Timesheet Operasi:** Ditandatangani 3 pihak (Surveyor, LNGC, NRS).
            * **Gas Sampling Analysis Report:** Acuan GHV dari Surveyor.
            """)
        with col_doc_c_b:
            st.warning("""
            **📧 Kewajiban Final:**
            * **Email Complete Discharging Report:** **WAJIB** dikirim sebelum Pandu naik kapal atau lepas sandar.
            * **Distlist:** CC ke Manajemen, Operasi, Komersial, Engineering, Top Risk, & Data Subholding.
            """)
            
    st.markdown("### 📐 Kalkulator Validasi CTMS (Klaim Serah Terima Final)")
    col_ctm1, col_ctm2 = st.columns(2)
    with col_ctm1:
        ctm_before = st.number_input("1. CTMS Opening Register (m³)", min_value=0.0, value=134111.0, step=10.0)
        ctm_after = st.number_input("2. CTMS Closing Register (m³)", min_value=0.0, value=4611.0, step=10.0)
        ghv_input = st.number_input("3. Gross Heating Value / GHV (BTU/SCF)", min_value=500.0, value=1033.3, step=0.1)
    
    with col_ctm2:
        actual_discharged = ctm_before - ctm_after
        variance = actual_discharged - cargo_vol
        gas_volume_mmscf = (actual_discharged / 2.0) * (ghv_input / 1033.3)
        energy_mmbtu = gas_volume_mmscf * (ghv_input / 1000.0) * 1000.0
        
        st.metric("Total Aktual LNG (Serah Terima)", f"{actual_discharged:,.0f} m³")
        st.metric("Konversi Volume Satuan Gas", f"{gas_volume_mmscf:,.2f} MMSCF")
        st.metric("Total Hak Klaim Nilai Energi", f"{energy_mmbtu:,.2f} MMBTU")

    st.divider()
    
    report_data = {
        "Parameter Laporan Serah Terima": [
            "Tanggal Pelaksanaan Bongkar", "Target Rencana Manifes", "Pencatatan CTMS Opening", "Pencatatan CTMS Closing", 
            "TOTAL AKTUAL VOLUME DISCHARGED", "Variance Selisih Kargo", "Gross Heating Value Realisasi", "Volume Gas Konversi (MMSCF)", "Total Klaim Energi (MMBTU)"
        ],
        "Angka Validasi": [
            waktu_eta.strftime("%d-%b-%Y"), f"{cargo_vol:,.0f} m³",
            f"{ctm_before:,.0f} m³", f"{ctm_after:,.0f} m³", f"{actual_discharged:,.0f} m³",
            f"{variance:,.0f} m³", f"{ghv_input:.1f} BTU/SCF",
            f"{gas_volume_mmscf:,.2f}", f"{energy_mmbtu:,.2f}"
        ]
    }
    df_report = pd.DataFrame(report_data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_report.to_excel(writer, index=False, sheet_name='CTMS_Official_Report')
    
    st.download_button(
        label="📊 Unduh Berita Acara Excel (Official Report)",
        data=buffer.getvalue(),
        file_name=f"Official_CTM_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
