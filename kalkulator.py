import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# Konfigurasi Halaman
st.set_page_config(page_title="CTO Workflow Dashboard", page_icon="🚢", layout="wide")

st.title("🚢 FSRU Custody Transfer Workflow")
st.markdown("Sistem Asisten & Kalkulasi Operasional CTO - PT Nusantara Regas")
st.divider()

# Arsitektur 4 Tab Berdasarkan Timeline Operasional
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "⏳ Fase 1: H-1 (Pre-Arrival & Kalkulasi)", 
    "🤝 Fase 2: Hari H (Sandar & Meeting)", 
    "🔍 Fase 3: Monitoring (During Discharging)",
    "📝 Fase 4: Selesai (Final Report CTMS)"
])

# ==========================================
# FASE 1: H-1 (PRE-ARRIVAL & KALKULASI)
# ==========================================
with tab_h1:
    st.header("Persiapan H-1: Kalkulasi Parameter & Risiko")
    
    with st.expander("📌 Checklist CTO: Tugas H-1", expanded=True):
        st.markdown("""
        * **Pantau Notice ETA:** Cek email update 96h, 72h, 48h, dan 24h notice dari kapal.
        * **Verifikasi Dokumen Safety:** Pastikan dokumen MCU, Basic Sea Survival (BSS),/BOSIET milik personel (Surveyor/PLN) yang akan *on-board* valid (terutama tensi darah).
        * **Kirim Draft Report & Email:** Email daftar *Personnel On-board*, *Joint Operations Agreement (JOA)*, dan *Unloading Plan*.
        * **Order Kapal:** Minta kapten/agen siapkan tasibut (Utas boat) untuk keberangkatan tim *on-board*.
        """)

    col1, col2, col3 = st.columns(3)
    with col1:
        cargo_vol = st.number_input("Rencana Kargo (m³)", min_value=10000.0, value=130000.0, step=1000.0)
    with col2:
        rob_h_minus_1 = st.number_input("ROB H-1 (Pukul 00:00)", min_value=0.0, value=42000.0, step=500.0)
    with col3:
        serapan_harian = st.number_input("Serapan Harian PLN (m³)", min_value=0.0, value=17000.0, step=500.0)

    col_waktu1, col_waktu2 = st.columns(2)
    with col_waktu1:
        tgl_eta = st.date_input("Tanggal ETA", datetime(2026, 6, 10))
        jam_eta = st.time_input("Jam ETA (LCT)", value=pd.to_datetime("06:00").time())
        waktu_eta = datetime.combine(tgl_eta, jam_eta)
        waktu_commence = waktu_eta + timedelta(hours=8)
        
    with col_waktu2:
        st.write(f"**Target Commence:** {waktu_commence.strftime('%d-%b %H:%M LCT')} (ETA + 8 Jam)")
        target_jam_bongkar = st.number_input("Target Waktu Bongkar Murni (Jam)", min_value=1.0, value=35.0, step=0.5)

    # Kalkulasi Logika Pak Suci (Worst Case)
    rob_hari_h = rob_h_minus_1 - serapan_harian
    jam_commence_desimal = waktu_commence.hour + (waktu_commence.minute / 60.0)
    serapan_matematis = (serapan_harian / 24.0) * jam_commence_desimal
    
    st.markdown("#### 📊 Hasil Kalkulasi Skenario H-1")
    col_res1, col_res2, col_res3 = st.columns(3)
    
    worst_case_serapan = 8000.0 # Standard pembulatan aman
    rob_commence = rob_hari_h - worst_case_serapan
    volume_disrub = (rob_commence + cargo_vol) - 122500.0
    
    col_res1.metric(f"ROB Saat Commence", f"{rob_commence:,.0f} m³")
    if volume_disrub > 0:
        col_res2.metric("Wajib Disrub (Risiko Overfill)", f"{volume_disrub:,.0f} m³")
    else:
        volume_disrub = 0
        col_res2.metric("Wajib Disrub", "0 m³", "Kapasitas Aman")
        
    kebutuhan_loading_raw = cargo_vol / target_jam_bongkar if target_jam_bongkar > 0 else 0
    kebutuhan_loading_bulat = int(kebutuhan_loading_raw / 100) * 100
    col_res3.metric("Rekomendasi Loading Rate", f"{kebutuhan_loading_bulat:,.0f} m³/h")

# ==========================================
# FASE 2: HARI H (SANDAR & MEETING)
# ==========================================
with tab_sandar:
    st.header("Hari H: Pre-Cargo Meeting & ESOD")
    
    with st.expander("📌 Checklist CTO: Pre-Cargo Meeting", expanded=True):
        st.markdown("""
        * **Lapor POS ISPS:** Sebelum naik tasibut, pastikan lapor security & cek buku tamu. Pakai APD lengkap (Helm wajib ada *chin strap*, sepatu safety standar).
        * **Verifikasi NOR Received:** Pastikan waktu NOR dikunci bertepatan dengan selesainya rapat (*Complete Meeting*), bukan saat *All Fast*.
        * **CTM Opening:** Minta *Chief Officer* untuk menyetop sementara *Provision/Crane* kapal agar kapal tidak goyang (Trim/List stabil) saat mengambil angka radar awal.
        * **Safety Tests:** Ingat, *Warm ESD Test* dilakukan sebelum arm cooldown, dan *Cold ESD Test* dilakukan setelah *arm cooldown*.
        """)

    st.markdown("#### Susun Estimation Schedule Operational Discharging (ESOD)")
    start_datetime = waktu_eta
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
        edited_df = st.data_editor(
            df_default,
            column_config={
                "Kegiatan": st.column_config.TextColumn("Kegiatan", disabled=True),
                "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
            },
            hide_index=True, use_container_width=True, height=530
        )

    with col_result:
        schedule_result = []
        current_time = start_datetime
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
# FASE 3: MONITORING (DURING DISCHARGING)
# ==========================================
with tab_monitor:
    st.header("Monitoring: Pengawasan Saat Bongkar")
    
    with st.expander("📌 Checklist CTO: Selama Discharging", expanded=True):
        st.markdown("""
        * **Kirim Update Berkala:** Terbitkan email "Start Discharging" setelah mencapai Full Rate. Update rutin di WhatsApp per 2-4 jam.
        * **Pantau Serapan PLN:** Jika rate aktual darat turun drastis, segera hubungi P2B PLN agar tidak berisiko demorage.
        * **Kalkulasi Rate Down:** Jika sisa kargo sudah menipis (mendekati 133.000 m³), koordinasikan dengan kapal untuk menurunkan laju pompa (*Rate Down*).
        """)

    st.markdown("#### 🧮 Kalkulator Sisa Waktu (LNG To Go)")
    st.info("Kalkulator interaktif ini digunakan untuk memproyeksikan sisa waktu saat melakukan pengecekan di tengah operasi (misal jam 2 pagi).")
    
    col_togo1, col_togo2 = st.columns(2)
    with col_togo1:
        current_time_input = st.time_input("Waktu Pengecekan Saat Ini (LCT)", value=pd.to_datetime("02:00").time())
        sisa_kargo_togo = st.number_input("Sisa Kargo Belum Dibongkar / LNG To Go (m³)", min_value=0.0, value=32029.0)
        current_rate = st.number_input("Loading Rate Saat Ini (m³/h)", min_value=1.0, value=4000.0)
        
    with col_togo2:
        sisa_jam = sisa_kargo_togo / current_rate
        waktu_sekarang = datetime.combine(datetime.today(), current_time_input)
        estimasi_selesai = waktu_sekarang + timedelta(hours=sisa_jam)
        
        st.metric("Estimasi Sisa Waktu Murni", f"{sisa_jam:.1f} Jam")
        st.metric("Proyeksi Jam Selesai (Complete Discharging)", estimasi_selesai.strftime("%H:%M LCT"))
        st.write(f"*Jika laytime mepet, pastikan tidak melewati batas denda 42 jam dari NOR.*")

# ==========================================
# FASE 4: SELESAI (FINAL REPORT CTMS)
# ==========================================
with tab_closing:
    st.header("Penyelesaian: Laporan Akhir & CTMS")
    
    with st.expander("📌 Checklist CTO: Dokumentasi Akhir", expanded=True):
        st.markdown("""
        * **Closing CTM:** Lakukan setelah Draining & Purging *loading arm* selesai dilakukan di kedua sisi.
        * **CTMS Before/After:** Verifikasi dan tanda tangani angka radar awal dan akhir kargo yang akan digunakan untuk *Invoicing*.
        * **Gas Sampling:** Jika menggunakan *boom sampling*, pastikan tabung sampel dibawa ke darat sesegera mungkin agar komposisi nilai *Gross Heating Value* (GHV) tidak berubah.
        * **POB Out:** Setelah dokumen selesai, *Pilot* naik, *Tugboat* narik, kirim laporan akhir via email.
        """)
        
    col_ctm1, col_ctm2 = st.columns(2)
    with col_ctm1:
        st.markdown("#### 📐 Input CTMS & GHV")
        ctm_before = st.number_input("1. CTMS Before Unloading (m³)", min_value=0.0, value=134111.0, step=10.0)
        ctm_after = st.number_input("2. CTMS After Unloading (m³)", min_value=0.0, value=4611.0, step=10.0)
        ghv_input = st.number_input("3. Nilai Kalor / GHV Aktual (BTU/SCF)", min_value=500.0, value=1033.3, step=0.1)
    
    with col_ctm2:
        st.markdown("#### 📊 Hasil Konversi Komersial")
        actual_discharged = ctm_before - ctm_after
        variance = actual_discharged - cargo_vol
        gas_volume_mmscf = (actual_discharged / 2.0) * (ghv_input / 1033.3)
        energy_mmbtu = gas_volume_mmscf * (ghv_input / 1000.0) * 1000.0
        
        st.metric("Total LNG Aktual (Discharged)", f"{actual_discharged:,.0f} m³")
        st.metric("Konversi Gas (MMSCF)", f"{gas_volume_mmscf:,.2f} MMSCF")
        st.metric("Energi Final (MMBTU)", f"{energy_mmbtu:,.2f} MMBTU")

    st.divider()
    
    report_data = {
        "Data Administrasi & Komersial": [
            "Tanggal ETA", "Target Kargo Manifes", "CTMS Awal", "CTMS Sisa", 
            "TOTAL DISCHARGED", "Variance", "GHV", "MMSCF", "MMBTU"
        ],
        "Validasi Angka": [
            waktu_eta.strftime("%d-%b-%Y"), f"{cargo_vol:,.0f} m3",
            f"{ctm_before:,.0f} m3", f"{ctm_after:,.0f} m3", f"{actual_discharged:,.0f} m3",
            f"{variance:,.0f} m3", f"{ghv_input:.1f} BTU/SCF",
            f"{gas_volume_mmscf:,.2f}", f"{energy_mmbtu:,.2f}"
        ]
    }
    df_report = pd.DataFrame(report_data)
    
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_report.to_excel(writer, index=False, sheet_name='CTMS_Final_Report')
    
    st.download_button(
        label="📊 Download Dokumen CTMS (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"CTMS_Final_Report_LNGC.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
