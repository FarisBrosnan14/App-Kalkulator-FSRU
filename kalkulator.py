import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Workflow Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Custody Transfer Operational Workflow")
st.markdown("Sistem Panduan Alur Kerja, Kalkulasi Parameter, & Manajemen Dokumen Resmi CTO")
st.divider()

# Arsitektur 4 Tab Berdasarkan Timeline Operasional & Manajemen Dokumen Resmi
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "⏳ Fase 1: H-1 (Pre-Arrival)", 
    "🤝 Fase 2: Hari H (Sandar & Meeting)", 
    "🔍 Fase 3: Monitoring (Bongkar)",
    "📝 Fase 4: Selesai (CTMS & Report)"
])

# ==========================================
# FASE 1: H-1 (PRE-ARRIVAL & ADMINISTRASI)
# ==========================================
with tab_h1:
    st.header("⏳ Persiapan Tahap H-1: Parameter & Perizinan")
    
    with st.expander("📌 Checklist CTO: Tugas H-1 (Administrasi & Korespondensi)", expanded=True):
        col_doc_h1_a, col_doc_h1_b = st.columns(2)
        with col_doc_h1_a:
            st.markdown("""
            <div style='background-color: #f1f3f4; padding: 15px; border-radius: 5px; border-left: 5px solid #1a73e8; height: 100%;'>
                <h4 style='margin-top:0; color: #1a73e8;'>📋 Dokumen untuk Diperiksa:</h4>
                <ul>
                    <li><b>Cargo Manifest:</b> Periksa data muatan asal dari kilang penyuplai.</li>
                    <li><b>Arrival LNG Declaration:</b> Pernyataan resmi dari Kapten LNGC.</li>
                    <li><b>Sertifikat & MCU:</b> Pastikan dokumen BSS/BOSIET dan tensi darah personel valid. Wajib dapat <i>clearance</i> Dokter Perusahaan sebelum <i>on-board</i>.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col_doc_h1_b:
            st.markdown("""
            <div style='background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 5px solid #e8710a; height: 100%;'>
                <h4 style='margin-top:0; color: #e8710a;'>📧 Email yang Harus Dikirim:</h4>
                <ul>
                    <li><b>Draft Report & Unloading Plan:</b> Skema simulasi pembongkaran awal.</li>
                    <li><b>POB List:</b> Daftar manifes personel yang akan naik ke FSRU (Kirim ke Keagenan/PTK/AMI).</li>
                    <li><b>Request Hutasuhut (Transport Boat):</b> Order kapal jemputan untuk tim operasi.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

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
        st.write(f"**Proyeksi Skenario Mulai Discharging (ETA + 8 Jam):** {waktu_commence.strftime('%d-%b-%Y %H:%M LCT')}")
        target_jam_bongkar = st.number_input("Target Waktu Durasi Pompa Murni (Jam)", min_value=1.0, value=35.0, step=0.5)

    # Logika Hitungan Mengikuti SOP (Worst Case)
    rob_hari_h = rob_h_minus_1 - serapan_harian
    jam_commence_desimal = waktu_commence.hour + (waktu_commence.minute / 60.0)
    worst_case_serapan = 8000.0 # Pengamanan teoretis serapan
    rob_commence = rob_hari_h - worst_case_serapan
    volume_disrub = (rob_commence + cargo_vol) - 122500.0 # 122500 adalah Safe Limit Tangki FSRU
    
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

# ==========================================
# FASE 2: HARI H (SANDAR & PERTEMUAN)
# ==========================================
with tab_sandar:
    st.header("🤝 Tahap Hari H: Koordinasi Lapangan & Sandar")
    
    with st.expander("📌 Checklist CTO: Discharging Activity (Preparation)", expanded=True):
        st.markdown("""
        * **1. Report to ISPS Post:** Lapor pos dan jalankan prosedur ISPS sebelum keberangkatan.
        * **2. Coordination & Trip:** Koordinasi dengan Master NRS & Tim, berangkat menuju FSRU menggunakan *Hutasuhut*.
        * **3. Monitoring STS until All Fast:** Awasi pergerakan manuver *Ship-to-Ship* sampai kapal diikat sempurna (*All Fast*).
        * **4. Pre-cargo Meeting & L/A Connected:** Lakukan rapat dengan LNGC (ideal 30 menit setelah *All Fast*) dan pastikan lengan kargo tersambung.
        * **5. Opening CTM:** Ambil <i>snapshot</i> radar. Minta kru menahan aktivitas <i>crane/provision</i> agar kondisi kapal stabil (Trim/List).
        * **6. Supervision of Preparation Process:** Lakukan *Warm ESD Test*, *Arm Cooldown*, hingga *Cold ESD Test* dengan cermat.
        """)

    st.markdown("#### Susunan Rantai Waktu Estimation Schedule Operational Discharging (ESOD)")
    durasi_bongkar_menit = int(target_jam_bongkar * 60) if target_jam_bongkar > 0 else 1980

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
        st.markdown("**✍️ Editor Jadwal (Dalam Menit):**")
        edited_df = st.data_editor(
            df_default,
            column_config={
                "Kegiatan": st.column_config.TextColumn("Kegiatan", disabled=True),
                "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
            },
            hide_index=True, use_container_width=True, height=530
        )

    with col_result:
        st.markdown("**📅 Hasil Proyeksi Otomatis Jadwal Lapangan:**")
        schedule_result = []
        current_time = waktu_eta
        for index, row in edited_df.iterrows():
            durasi = row["Durasi (Menit)"]
            start_time = current_time
            end_time = current_time + timedelta(minutes=int(durasi))
            schedule_result.append({
                "Kegiatan": row["Kegiatan"],
                "Mulai": start_time.strftime("%d-%b %H:%M"),
                "Selesai": end_time.strftime("%d-%b %H:%M")
            })
            current_time = end_time
            
        st.dataframe(pd.DataFrame(schedule_result), use_container_width=True, hide_index=True, height=530)

# ==========================================
# FASE 3: MONITORING (BONGKAR & UPDATE)
# ==========================================
with tab_monitor:
    st.header("🔍 Tahap Berjalan: Pengawasan & Pengiriman Progres")
    
    with st.expander("📌 Checklist CTO: Discharging Activity (Execution)", expanded=True):
        st.markdown("""
        * **1. Collect Data:** Kumpulkan bukti *Open CTM* (NRS & LNGC). Pastikan mengambil *snapshot* radar 30 menit dan 15 menit sebelum pembukaan katup (*Commence Loading*).
        * **2. Send Email Report Start Discharging:** Rilis email resmi laporan *Start Discharging* segera setelah kecepatan pompa menembus titik stabil (*Full Rate*).
        * **3. Monitoring & Coordination During Discharging Process:** Kawal secara rutin di grup WhatsApp (Update per 2-4 jam). Pantau aliran penyerapan PLN dan proyeksikan waktu sisa bongkar.
        """)

    st.markdown("#### 🧮 Kalkulator Progres Penurunan Aliran (LNG To Go)")
    st.info("💡 Gunakan kalkulator ini saat berjaga malam untuk memastikan sisa *Laytime* aman dari penalti (Batas 42 Jam) dan merencanakan waktu *Rate Down*.")
    col_togo1, col_togo2 = st.columns(2)
    with col_togo1:
        current_time_input = st.time_input("Jam Pengecekan Lapangan Saat Ini (LCT)", value=pd.to_datetime("02:00").time())
        sisa_kargo_togo = st.number_input("Sisa Kargo Belum Dibongkar / LNG To Go (m³)", min_value=0.0, value=32029.0)
        current_rate = st.number_input("Laju Kecepatan Pompa Kapal Aktual (m³/h)", min_value=1.0, value=4000.0)
        
    with col_togo2:
        sisa_jam = sisa_kargo_togo / current_rate
        waktu_sekarang = datetime.combine(datetime.today(), current_time_input)
        estimasi_selesai = waktu_sekarang + timedelta(hours=sisa_jam)
        
        st.metric("Estimasi Sisa Durasi Pemompaan Murni", f"{sisa_jam:.1f} Jam")
        st.metric("Proyeksi Jam Katup Ditutup (Complete Discharging)", estimasi_selesai.strftime("%H:%M LCT"))
        st.caption("Jika sisa kargo menipis (kisaran ±1.000 m³), segera instruksikan LNGC untuk *Rate Down*.")

# ==========================================
# FASE 4: SELESAI (PENUTUPAN & PELAPORAN)
# ==========================================
with tab_closing:
    st.header("📝 Penyelesaian Operasi: Serah Terima & Berita Acara (CTMS)")
    
    with st.expander("📌 Checklist CTO: Dokumentasi Akhir & POB Out", expanded=True):
        col_doc_c_a, col_doc_c_b = st.columns(2)
        with col_doc_c_a:
            st.markdown("""
            <div style='background-color: #f1f3f4; padding: 15px; border-radius: 5px; border-left: 5px solid #1a73e8; height: 100%;'>
                <h4 style='margin-top:0; color: #1a73e8;'>📋 Dokumen Pengesahan:</h4>
                <ul>
                    <li><b>Closing CTM Printout:</b> Dicetak pasca <i>Draining & Purging</i> rampung.</li>
                    <li><b>Timesheet Operasi:</b> Catatan kronologis yang ditandatangani 3 pihak (Surveyor, LNGC, NRS).</li>
                    <li><b>Gas Sampling Analysis Report:</b> Acuan nilai GHV aktual dari Surveyor Independen.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col_doc_c_b:
            st.markdown("""
            <div style='background-color: #f9f9f9; padding: 15px; border-radius: 5px; border-left: 5px solid #e8710a; height: 100%;'>
                <h4 style='margin-top:0; color: #e8710a;'>📧 Kewajiban Final:</h4>
                <ul>
                    <li><b>Email Complete Discharging Report:</b> <b>WAJIB</b> dikirimkan sebelum petugas Pandu naik kapal (<i>Pilot On Board</i>) atau kapal lepas sandar.</li>
                    <li><b>Distlist Khusus:</b> CC ke Manajemen, Operasi, Komersial, Engineering, Top Risk, & Data Subholding.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
    st.markdown("#### 📐 Kalkulator Validasi CTMS (Klaim Serah Terima Final)")
    col_ctm1, col_ctm2 = st.columns(2)
    with col_ctm1:
        ctm_before = st.number_input("1. CTMS Opening Register / Before Unloading (m³)", min_value=0.0, value=134111.0, step=10.0)
        ctm_after = st.number_input("2. CTMS Closing Register / After Unloading (m³)", min_value=0.0, value=4611.0, step=10.0)
        ghv_input = st.number_input("3. Nilai Mutu Kalor Realisasi / Gross Heating Value (GHV) - BTU/SCF", min_value=500.0, value=1033.3, step=0.1)
    
    with col_ctm2:
        actual_discharged = ctm_before - ctm_after
        variance = actual_discharged - cargo_vol
        gas_volume_mmscf = (actual_discharged / 2.0) * (ghv_input / 1033.3)
        energy_mmbtu = gas_volume_mmscf * (ghv_input / 1000.0) * 1000.0
        
        st.metric("Total Aktual LNG Discharged (Serah Terima)", f"{actual_discharged:,.0f} m³")
        st.metric("Konversi Volume Satuan Gas", f"{gas_volume_mmscf:,.2f} MMSCF")
        st.metric("Total Hak Klaim Nilai Energi Bersih", f"{energy_mmbtu:,.2f} MMBTU")

    st.divider()
    
    # Pengaturan Format Data untuk Ekspor Excel
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
    
    # Fitur Ekspor Excel Tanpa Perlu Save File Fisik
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_report.to_excel(writer, index=False, sheet_name='CTMS_Official_Report')
    
    st.download_button(
        label="📊 Unduh Berita Acara Excel (Official Discharging Report)",
        data=buffer.getvalue(),
        file_name=f"Official_CTM_Report_LN.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
