import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io

# ==========================================
# 1. INJEKSI TEMA WARNA (DEEP OCEAN & EMERALD)
# ==========================================
if not os.path.exists(".streamlit/config.toml"):
    os.makedirs(".streamlit", exist_ok=True)
    with open(".streamlit/config.toml", "w") as f:
        f.write("""
[theme]
base="dark"
primaryColor="#10b981"
backgroundColor="#020617"
secondaryBackgroundColor="#0f172a"
textColor="#f8fafc"
font="sans serif"
""")

st.set_page_config(page_title="CTO Premium Workspace", page_icon="🌊", layout="wide")

# ==========================================
# 2. INJEKSI CUSTOM CSS (GLASSMORPHISM & MENU AKTIF)
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Poppins', sans-serif;
    }

    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 0rem;}
    
    .stApp {
        background: radial-gradient(circle at top left, #083344, #020617);
    }

    /* Kustomisasi Top Bar */
    .glass-top-bar {
        background: rgba(15, 23, 42, 0.4);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 20px 30px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3);
    }
    .top-bar-title {
        color: #ffffff;
        font-size: 24px;
        font-weight: 800;
        margin: 0;
        letter-spacing: 1px;
    }
    .top-bar-subtitle {
        color: #06b6d4;
        font-size: 14px;
        font-weight: 400;
    }
    .profile-pill {
        background: linear-gradient(135deg, #10b981, #059669);
        color: #ffffff;
        padding: 8px 24px;
        border-radius: 30px;
        font-weight: 600;
        font-size: 14px;
    }

    /* Kustomisasi Info Widget Row */
    .info-widget-row {
        display: flex;
        gap: 20px;
        margin-bottom: 20px;
        flex-wrap: wrap;
    }
    .info-widget {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 15px 20px;
        flex: 1;
        min-width: 200px;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 15px;
    }
    .time-text {
        font-size: 26px;
        font-weight: 800;
        color: #06b6d4;
    }
    
    /* Pengumuman Bar */
    .announcement-bar {
        background: rgba(15, 23, 42, 0.6);
        border-left: 4px solid #fde047;
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 30px;
        display: flex;
        align-items: center;
        gap: 15px;
        font-size: 14px;
    }

    /* Kustomisasi Menu Utama Interaktif (Menyembunyikan bulat radio) */
    div[data-testid="stRadio"] > div {
        display: flex;
        background-color: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 5px;
        gap: 5px;
    }
    div[data-testid="stRadio"] > div > label {
        flex: 1;
        text-align: center;
        justify-content: center;
        padding: 12px 20px;
        border-radius: 8px;
        cursor: pointer;
        transition: all 0.3s;
    }
    div[data-testid="stRadio"] > div > label:hover {
        background-color: rgba(16, 185, 129, 0.2);
    }
    div[data-testid="stRadio"] > div > label[data-checked="true"] {
        background-color: #0ea5e9;
    }
    div[data-testid="stRadio"] > div > label > div:first-child {
        display: none;
    }
    div[data-testid="stRadio"] > div > label > div:last-child {
        color: white;
        font-weight: 600;
        font-size: 15px;
    }

    /* Kustomisasi Tab Bawah */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        border-bottom: 2px solid rgba(255,255,255,0.1);
    }
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        color: #64748b;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] {
        color: #10b981 !important;
        border-bottom: 3px solid #10b981 !important;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 3. HEADER & STATE INITIALIZATION
# ==========================================
# Inisialisasi Session State Data Kapal Cerdas
if "selected_cargo" not in st.session_state:
    st.session_state.selected_cargo = 130000.0
if "selected_eta" not in st.session_state:
    st.session_state.selected_eta = datetime(2026, 6, 9)
if "active_ship" not in st.session_state:
    st.session_state.active_ship = "Belum ada yang dipilih"

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

st.markdown("""
<div class="glass-top-bar">
    <div style="font-size: 30px; margin-right: 20px;">🌊</div>
    <div style="flex-grow: 1;">
        <div class="top-bar-title">Dashboard Distribusi Gas NR</div>
        <div class="top-bar-subtitle">Halo, Faris (Custody Transfer Officer)</div>
    </div>
    <div class="profile-pill">🟢 ACTIVE SHIFT</div>
</div>
""", unsafe_allow_html=True)

now = datetime(2026, 6, 9, 16, 4)
st.markdown(f"""
<div class="info-widget-row">
    <div class="info-widget">
        <div class="time-text">{now.strftime('%H:%M:%S')}</div>
        <div style="color: #94a3b8; font-size:14px;">Sel, 9 Jun</div>
    </div>
    <div class="info-widget">
        <div style="color: #ef4444; font-size: 24px;">📍</div>
        <div>
            <div style="font-weight: 600; color: white;">Johar Baru</div>
            <div style="color: #94a3b8; font-size: 12px;">Teluk Jakarta</div>
        </div>
    </div>
    <div class="info-widget">
        <div style="color: #fde047; font-size: 24px;">⛅</div>
        <div>
            <div style="font-weight: 600; color: white;">Berawan • 31.3°C</div>
            <div style="color: #94a3b8; font-size: 12px;">🌬️ 14.3 km/h</div>
        </div>
    </div>
</div>
<div class="announcement-bar">
    <span style="font-size:18px;">📢</span>
    <span><b>PENGUMUMAN & TO-DO LIST HARI INI:</b> Rapat koordinasi kargo domestik bersama Pak Dhana dijadwalkan ulang. Harap persiapkan draf laporan <i>Unloading Plan</i> sebelum PC Meeting.</span>
</div>
""", unsafe_allow_html=True)

# ==========================================
# 4. MENU NAVIGASI AKTIF (Tengah Layar)
# ==========================================
menu_pilihan = st.radio("Navigasi", ["Dashboard Utama", "Kalender Lengkap", "Panel Manajer"], horizontal=True, label_visibility="collapsed")

# ------------------------------------------
# HALAMAN 1: DASHBOARD UTAMA
# ------------------------------------------
if menu_pilihan == "Dashboard Utama":
    
    # KARTU JADWAL KAPAL INTERAKTIF
    st.markdown("### 🗓️ Tinjauan 14 Hari Kedepan (Pilih Kapal untuk Autocomplete Data)")
    if st.session_state.active_ship != "Belum ada yang dipilih":
        st.success(f"✅ Data kapal **{st.session_state.active_ship}** berhasil dimuat ke dalam parameter Fase 1!")
        
    c1, c2, c3, c4 = st.columns(4)
    
    with c1:
        st.markdown("<div style='text-align:center; color:#94a3b8; margin-bottom:5px;'><b>09 Jun 2026</b></div>", unsafe_allow_html=True)
        if st.button("🚢 M. T Ibrahim\n\n130.000 m³\n🟢 SHIFT PG", use_container_width=True, key="btn1"):
            st.session_state.selected_cargo = 130000.0
            st.session_state.selected_eta = datetime(2026, 6, 9)
            st.session_state.active_ship = "M. T Ibrahim"
            st.rerun()
            
    with c2:
        st.markdown("<div style='text-align:center; color:#94a3b8; margin-bottom:5px;'><b>10 Jun 2026</b></div>", unsafe_allow_html=True)
        if st.button("🚢 Itqi Arradi\n\n125.500 m³\n🟢 SHIFT PG", use_container_width=True, key="btn2"):
            st.session_state.selected_cargo = 125500.0
            st.session_state.selected_eta = datetime(2026, 6, 10)
            st.session_state.active_ship = "Itqi Arradi"
            st.rerun()

    with c3:
        st.markdown("<div style='text-align:center; color:#94a3b8; margin-bottom:5px;'><b>11 Jun 2026</b></div>", unsafe_allow_html=True)
        if st.button("🚢 Hanif Nur Ihsan\n\n138.000 m³\n🟢 SHIFT PG", use_container_width=True, key="btn3"):
            st.session_state.selected_cargo = 138000.0
            st.session_state.selected_eta = datetime(2026, 6, 11)
            st.session_state.active_ship = "Hanif Nur Ihsan"
            st.rerun()

    with c4:
        st.markdown("<div style='text-align:center; color:#94a3b8; margin-bottom:5px;'><b>12 Jun 2026</b></div>", unsafe_allow_html=True)
        if st.button("🚢 Haerul Hafiz\n\n120.000 m³\n🟢 SHIFT MLM", use_container_width=True, key="btn4"):
            st.session_state.selected_cargo = 120000.0
            st.session_state.selected_eta = datetime(2026, 6, 12)
            st.session_state.active_ship = "Haerul Hafiz"
            st.rerun()

    st.divider()

    # TAB ALUR KERJA CTO
    tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
        "PHASE 1: PRE-ARRIVAL", 
        "PHASE 2: BERTHING", 
        "PHASE 3: OPS MONITOR",
        "PHASE 4: REPORT"
    ])

    with tab_h1:
        st.markdown("### 🧮 Kalkulasi Awal & Skenario ROB")
        col1, col2, col3 = st.columns(3)
        with col1:
            cargo_vol = st.number_input("Rencana Kargo Masuk (m³)", min_value=10000.0, value=st.session_state.selected_cargo, step=1000.0)
        with col2:
            rob_awal = st.number_input("Pencatatan ROB Awal (m³)", min_value=0.0, value=42000.0, step=500.0)
        with col3:
            serapan_harian = st.number_input("Target Serapan Gas PLN (m³/hari)", min_value=0.0, value=17000.0, step=500.0)

        st.markdown("#### ⏳ Sinkronisasi Waktu")
        col_waktu1, col_waktu2 = st.columns(2)
        with col_waktu1:
            col_d1, col_t1 = st.columns(2)
            with col_d1:
                tgl_rob = st.date_input("Tanggal Record ROB", datetime(2026, 6, 9))
            with col_t1:
                jam_rob = st.time_input("Jam Record ROB", value=pd.to_datetime("00:00").time())
            waktu_rob = datetime.combine(tgl_rob, jam_rob)

        with col_waktu2:
            col_d2, col_t2 = st.columns(2)
            with col_d2:
                # Value diikat ke Session State dari klik tombol kapal
                tgl_eta = st.date_input("Tanggal ETA Kapal", value=st.session_state.selected_eta)
            with col_t2:
                jam_eta = st.time_input("Jam ETA Kapal", value=pd.to_datetime("06:00").time())
            waktu_eta = datetime.combine(tgl_eta, jam_eta)
            
        waktu_commence = waktu_eta + timedelta(hours=8)
        st.markdown(f"<div style='padding:10px; background:rgba(16,185,129,0.1); border-radius:5px; color:#10b981;'>👉 <b>Proyeksi Mulai Commence (ETA+8j):</b> {waktu_commence.strftime('%d-%b-%Y %H:%M LCT')}</div><br>", unsafe_allow_html=True)
        target_jam_bongkar = st.number_input("Target Durasi Bongkar Murni (Jam)", min_value=1.0, value=35.0, step=0.5)

        st.markdown("---")
        selisih_jam = (waktu_commence - waktu_rob).total_seconds() / 3600.0

        if selisih_jam < 0:
            st.error("⚠️ Waktu pencatatan ROB Awal terdeteksi lebih akhir dari target Commence!")
        else:
            serapan_matematis = (serapan_harian / 24.0) * selisih_jam
            default_worst_case = float(int(serapan_matematis / 1000) * 1000)
            
            col_calc1, col_calc2 = st.columns(2)
            with col_calc1:
                st.write(f"Durasi tunggu ROB hingga Commence: **{selisih_jam:.1f} Jam**")
                st.caption(f"Hitungan Matematis Murni: {serapan_matematis:,.0f} m³")
            with col_calc2:
                worst_case_serapan = st.number_input("Adjusment Worst Case (m³)", value=default_worst_case, step=500.0)

            rob_commence = rob_awal - worst_case_serapan
            volume_disrub = (rob_commence + cargo_vol) - 122500.0 
            
            col_res1, col_res2, col_res3 = st.columns(3)
            col_res1.metric(f"ROB Saat Commence", f"{rob_commence:,.0f} m³", f"-{worst_case_serapan:,.0f} m³", delta_color="inverse")
            
            if volume_disrub > 0:
                col_res2.metric("Wajib Serap Darat (Disrub)", f"{volume_disrub:,.0f} m³", "Overfill Risk!")
            else:
                volume_disrub = 0
                col_res2.metric("Wajib Serap Darat (Disrub)", "0 m³", "Aman", delta_color="normal")
                
            kebutuhan_loading_raw = cargo_vol / target_jam_bongkar if target_jam_bongkar > 0 else 0
            kebutuhan_loading_bulat = int(kebutuhan_loading_raw / 100) * 100
            col_res3.metric("Loading Rate Target", f"{kebutuhan_loading_bulat:,.0f} m³/h")

        current_waktu_murni_minutes = int(target_jam_bongkar * 60)
        if st.session_state.last_waktu_murni != target_jam_bongkar:
            st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = current_waktu_murni_minutes
            st.session_state.last_waktu_murni = target_jam_bongkar

    with tab_sandar:
        st.markdown("### 📅 Live ESOD Timeline (Auto-Calculated)")
        events = [
            "ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", 
            "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", 
            "FULL RATE", "Bongkar Muat Murni (Rate Down)", "DISCHARGING COMPLETED", 
            "CLOSING CTM", "ARMs Disconnected", "Documentation", "POB OUT"
        ]
        datetimes_list = [waktu_eta]
        current_dt = waktu_eta
        for ev in events[1:]:
            dur = st.session_state.durations[ev]
            current_dt = current_dt + timedelta(minutes=int(dur))
            datetimes_list.append(current_dt)

        df_esod = pd.DataFrame({
            "Tahapan Operasi": events,
            "Date / Time (LCT)": datetimes_list,
            "Durasi (Menit)": [0] + [st.session_state.durations[ev] for ev in events[1:]]
        })

        edited_table = st.data_editor(
            df_esod,
            column_config={
                "Tahapan Operasi": st.column_config.TextColumn("Tahapan Operasi", disabled=True),
                "Date / Time (LCT)": st.column_config.DatetimeColumn("Date / Time (LCT)", format="DD MMM / HH:mm"),
                "Durasi (Menit)": st.column_config.NumberColumn("Durasi (Menit)", min_value=0, step=1)
            },
            hide_index=True, use_container_width=True, key="esod_editor"
        )
        if "esod_editor" in st.session_state and st.session_state.esod_editor["edited_rows"]:
            edited_rows = st.session_state.esod_editor["edited_rows"]
            for row_idx, changes in edited_rows.items():
                row_idx = int(row_idx)
                if row_idx == 0: continue
                ev_name = events[row_idx]
                if "Durasi (Menit)" in changes:
                    st.session_state.durations[ev_name] = int(changes["Durasi (Menit)"])
                elif "Date / Time (LCT)" in changes:
                    new_dt = pd.to_datetime(changes["Date / Time (LCT)"])
                    prev_dt = df_esod.loc[row_idx - 1, "Date / Time (LCT)"]
                    new_calculated_dur = int((new_dt - prev_dt).total_seconds() / 60)
                    if new_calculated_dur >= 0:
                        st.session_state.durations[ev_name] = new_calculated_dur
            del st.session_state["esod_editor"]
            st.rerun()

    with tab_monitor:
        st.markdown("### 🧮 Analisis Sisa Waktu (LNG To Go)")
        col_togo1, col_togo2 = st.columns(2)
        with col_togo1:
            current_time_input = st.time_input("Jam Laporan Terkini", value=pd.to_datetime("02:00").time())
            sisa_kargo_togo = st.number_input("Volume LNG To Go (m³)", min_value=0.0, value=32029.0)
            current_rate = st.number_input("Actual Loading Rate (m³/h)", min_value=1.0, value=4000.0)
        with col_togo2:
            sisa_jam = sisa_kargo_togo / current_rate
            waktu_sekarang = datetime.combine(datetime.today(), current_time_input)
            estimasi_selesai = waktu_sekarang + timedelta(hours=sisa_jam)
            st.metric("Sisa Waktu Pemompaan", f"{sisa_jam:.1f} Jam")
            st.metric("Estimasi Selesai (Complete)", estimasi_selesai.strftime("%H:%M LCT"))

    with tab_closing:
        st.markdown("### 📐 Validasi Hak Milik (CTMS Calculation)")
        col_ctm1, col_ctm2 = st.columns(2)
        with col_ctm1:
            ctm_before = st.number_input("1. CTMS Opening Register (m³)", min_value=0.0, value=134111.0, step=10.0)
            ctm_after = st.number_input("2. CTMS Closing Register (m³)", min_value=0.0, value=4611.0, step=10.0)
            ghv_input = st.number_input("3. GHV Realisasi (BTU/SCF)", min_value=500.0, value=1033.3, step=0.1)
        with col_ctm2:
            actual_discharged = ctm_before - ctm_after
            variance = actual_discharged - cargo_vol
            gas_volume_mmscf = (actual_discharged / 2.0) * (ghv_input / 1033.3)
            energy_mmbtu = gas_volume_mmscf * (ghv_input / 1000.0) * 1000.0
            st.metric("Total LNG Discharged", f"{actual_discharged:,.0f} m³")
            st.metric("Konversi Gas", f"{gas_volume_mmscf:,.2f} MMSCF")
            st.metric("Total Hak Klaim Energi", f"{energy_mmbtu:,.2f} MMBTU")

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
            df_report.to_excel(writer, index=False, sheet_name='Official_CTMS')
        st.download_button(
            label="📊 Unduh Dokumen Excel (Official Report)",
            data=buffer.getvalue(),
            file_name=f"Official_CTM_Report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ------------------------------------------
# HALAMAN 2: KALENDER LENGKAP
# ------------------------------------------
elif menu_pilihan == "Kalender Lengkap":
    st.markdown("<div style='text-align:center; padding: 100px; color:#64748b;'><h3>📅 Modul Kalender Lengkap</h3><p>Tampilan Gantt Chart dan rekapitulasi jadwal bulanan akan dimuat di sini.</p></div>", unsafe_allow_html=True)

# ------------------------------------------
# HALAMAN 3: PANEL MANAJER
# ------------------------------------------
elif menu_pilihan == "Panel Manajer":
    st.markdown("<div style='text-align:center; padding: 100px; color:#64748b;'><h3>📊 Panel Persetujuan Manajer</h3><p>Modul untuk otorisasi dokumen JOA, evaluasi Demurrage, dan pelaporan top-level management.</p></div>", unsafe_allow_html=True)
