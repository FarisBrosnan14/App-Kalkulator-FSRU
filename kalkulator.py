import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# ==========================================
# INJEKSI OTOMATIS DARK MODE & RESPONSIVITAS
# ==========================================
# Kode ini akan otomatis memaksa server Streamlit ke Dark Mode
if not os.path.exists(".streamlit/config.toml"):
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/config.toml", "w") as f:
        f.write("[theme]\nbase=\"dark\"\nprimaryColor=\"#1a73e8\"\n")

# Konfigurasi Halaman (Auto-Ratio Mobile)
st.set_page_config(page_title="CTO Workflow Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Custody Transfer Operational Workflow")
st.markdown("Sistem Panduan Alur Kerja, Kalkulasi Parameter, & Manajemen Dokumen Resmi CTO")
st.divider()

# Inisialisasi Session State untuk Durasi Kegiatan
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

# Arsitektur 4 Tab
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "⏳ Fase 1: H-1 (Pre-Arrival)", 
    "🤝 Fase 2: Hari H (Sandar)", 
    "🔍 Fase 3: Monitoring",
    "📝 Fase 4: Selesai (Report)"
])

# ==========================================
# FASE 1: H-1 (PRE-ARRIVAL & ADMINISTRASI)
# ==========================================
with tab_h1:
    st.header("⏳ Persiapan Tahap H-1: Parameter & Perizinan")
    
    with st.expander("📌 Checklist CTO: Tugas H-1 (Administrasi & Korespondensi)", expanded=True):
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

    st.markdown("#### 🧮 Kalkulator Awal Risiko & ROB (Worst Case Scenario)")
    col1, col2, col3 = st.columns(3)
    with col1:
        cargo_vol = st.number_input("Rencana Kargo Masuk Manifes (m³)", min_value=10000.0, value=130000.0, step=1000.0)
    with col2:
        rob_h_minus_1 = st.number_input("Pencatatan ROB H-1 Pukul 00:00 (m³)", min_value=0.0, value=42000.0, step=500.0)
    with col3:
        serapan_harian = st.number_input("Target Penyerapan Gas PLN (m³/hari)", min_value=0.0, value=17000.0, step=500.0)

    col_waktu1, col_waktu2 = st.columns(2)
    with col_waktu1:
        tgl_eta = st.date_input("Tanggal Estimasi Kedatangan (ETA)", datetime(2026, 6, 10))
        jam_eta = st.time_input("Jam Estimasi Kedatangan (ETA LCT)", value=pd.to_datetime("06:00").time())
        waktu_eta = datetime.combine(tgl_eta, jam_eta)
        waktu_commence = waktu_eta + timedelta(hours=8)
        
    with col_waktu2:
        st.write(f"**Proyeksi Skenario Mulai Discharging:** {waktu_commence.strftime('%d-%b-%Y %H:%M')}")
        target_jam_bongkar = st.number_input("Target Waktu Durasi Pompa Murni (Jam)", min_value=1.0, value=35.0, step=0.5)

    rob_hari_h = rob_h_minus_1 - serapan_harian
    jam_commence_desimal = waktu_commence.hour + (waktu_commence.minute / 60.0)
    worst_case_serapan = 8000.0 
    rob_commence = rob_hari_h - worst_case_serapan
    volume_disrub = (rob_commence + cargo_vol) - 122500.0 
    
    st.markdown("---")
    col_res1, col_res2, col_res3 = st.columns(3)
    col_res1.metric(f"Estimasi ROB Saat Commence", f"{rob_commence:,.0f} m³")
    
    if volume_disrub > 0:
        col_res2.metric("Wajib Serap ke Darat (Disrub)", f"{volume_disrub:,.0f} m³", "Risiko Overfill!")
    else:
        volume_disrub = 0
        col_res2.metric("Wajib Serap ke Darat (Disrub)", "0 m³", "Kapasitas Aman", delta_color="normal")
        
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
    st.header("🤝 Tahap Hari H: Koordinasi Lapangan & Sandar")
    
    with st.expander("📌 Checklist CTO: Discharging Activity (Preparation)", expanded=True):
        st.markdown("""
        * **1. Report to ISPS Post:** Lapor pos dan jalankan prosedur ISPS sebelum keberangkatan.
        * **2. Coordination & Trip:** Koordinasi dengan Master NRS & Tim, berangkat menuju FSRU.
        * **3. Monitoring STS until All Fast:** Awasi pergerakan manuver *Ship-to-Ship* sampai kapal diikat sempurna (*All Fast*).
        * **4. Pre-cargo Meeting & L/A Connected:** Lakukan rapat dengan LNGC (ideal 30 menit setelah *All Fast*) dan pastikan lengan kargo tersambung.
        * **5. Opening CTM:** Ambil snapshot radar. Minta kru menahan aktivitas crane agar kondisi kapal stabil.
        * **6. Supervision of Preparation Process:** Lakukan *Warm ESD Test*, *Arm Cooldown*, hingga *Cold ESD Test*.
        """)

    st.markdown("#### Susunan Rantai Waktu (ESOD)")
    st.info("💡 **Mobile Friendly:** Tap angka menit atau jam untuk mengedit. Tabel akan otomatis mengoreksi jam kegiatan lainnya!")

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
            if row_idx == 0:
                continue
                
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
    st.header("🔍 Tahap Berjalan: Pengawasan & Pengiriman Progres")
    
    with st.expander("📌 Checklist CTO: Discharging Activity (Execution)", expanded=True):
        st.markdown("""
        * **1. Collect Data:** Kumpulkan bukti *Open CTM* (NRS & LNGC). Ambil snapshot 30 menit & 15 menit sebelum *Commence Loading*.
        * **2. Send Email Report Start Discharging:** Rilis email resmi segera setelah menembus *Full Rate*.
        * **3. Monitoring & Coordination:** Kawal rutin di grup WhatsApp. Pantau aliran penyerapan PLN.
        """)

    st.markdown("#### 🧮 Kalkulator Progres Penurunan Aliran (LNG To Go)")
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
    st.header("📝 Penyelesaian Operasi: Serah Terima & Berita Acara (CTMS)")
    
    with st.expander("📌 Checklist CTO: Dokumentasi Akhir & POB Out", expanded=True):
        col_doc_c_a, col_doc_c_b = st.columns(2)
        with col_doc_c_a:
            st.info("""
            **📋 Dokumen Pengesahan:**
            * **Closing CTM Printout:** Dicetak pasca *Draining & Purging* rampung.
            * **Timesheet Operasi:** Ditandatangani 3 pihak (Surveyor, LNGC, NRS).
            * **Gas Sampling Analysis Report:** Acuan nilai GHV aktual dari Surveyor Independen.
            """)
            
        with col_doc_c_b:
            st.warning("""
            **📧 Kewajiban Final:**
            * **Email Complete Discharging Report:** **WAJIB** dikirimkan sebelum petugas Pandu naik kapal (*Pilot On Board*) atau kapal lepas sandar.
            * **Distlist Khusus:** CC ke Manajemen, Operasi, Komersial, Engineering, Top Risk, & Data Subholding.
            """)
            
    st.markdown("#### 📐 Kalkulator Validasi CTMS (Klaim Serah Terima Final)")
    col_ctm1, col_ctm2 = st.columns(2)
    with col_ctm1:
        ctm_before = st.number_input("1. CTMS Opening Register / Before Unloading (m³)", min_value=0.0, value=134111.0, step=10.0)
        ctm_after = st.number_input("2. CTMS Closing Register / After Unloading (m³)", min_value=0.0, value=4611.0, step=10.0)
        ghv_input = st.number_input("3. Gross Heating Value / GHV (BTU/SCF)", min_value=500.0, value=1033.3, step=0.1)
    
    with col_ctm2:
        actual_discharged = ctm_before - ctm_after
        variance = actual_discharged - cargo_vol
        gas_volume_mmscf = (actual_discharged / 2.0) * (ghv_input / 1033.3)
        energy_mmbtu = gas_volume_mmscf * (ghv_input / 1000.0) * 1000.0
        
        st.metric("Total Aktual LNG (Serah Terima)", f"{actual_discharged:,.0f} m³")
        st.metric("Konversi Volume Satuan Gas", f"{gas_volume_mmscf:,.2f} MMSCF")
        st.metric("Total Hak Klaim Nilai Energi Bersih", f"{energy_mmbtu:,.2f} MMBTU")

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
