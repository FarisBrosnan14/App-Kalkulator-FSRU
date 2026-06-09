import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import requests
import streamlit.components.v1 as components
import base64

# ==========================================
# 1. TEMA WARNA & KONFIGURASI HALAMAN
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

def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

logo_path = "pertamina2.png"
if os.path.exists(logo_path):
    img_base64 = get_base64_of_bin_file(logo_path)
    html_logo_src = f"data:image/png;base64,{img_base64}"
    page_icon_src = logo_path
else:
    html_logo_src = "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b3/Pertamina_Logo.svg/300px-Pertamina_Logo.svg.png"
    page_icon_src = "🌊"

st.set_page_config(page_title="CTO Premium Workspace", page_icon=page_icon_src, layout="wide")

# ==========================================
# 2. FUNGSI PENGAMBIL DATA CUACA & OMBAK
# ==========================================
@st.cache_data(ttl=900)
def get_live_weather():
    lat, lon = -5.98, 106.83
    try:
        url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&windspeed_unit=kmh"
        res_w = requests.get(url_weather, timeout=5).json()
        temp = res_w["current_weather"]["temperature"]
        wind = res_w["current_weather"]["windspeed"]
        code = res_w["current_weather"]["weathercode"]
        
        if code <= 1: cond, icon = "Cerah", "☀️"
        elif code <= 3: cond, icon = "Berawan", "⛅"
        elif code <= 48: cond, icon = "Gerimis", "🌫️"
        elif code <= 65: cond, icon = "Hujan", "🌧️"
        elif code <= 82: cond, icon = "Hujan Deras", "⛈️"
        else: cond, icon = "Badai Petir", "🌩️"
    except:
        temp, wind, cond, icon = 31.3, 14.3, "Berawan", "⛅"
        
    try:
        url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height"
        res_m = requests.get(url_marine, timeout=5).json()
        wave = res_m["current"]["wave_height"]
        if wave is None: wave = 0.5
    except:
        wave = 0.5
        
    return temp, wind, wave, cond, icon

live_temp, live_wind, live_wave, live_cond, live_icon = get_live_weather()

# ==========================================
# 3. CSS UNTUK ELEMEN STREAMLIT UTAMA 
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    #MainMenu {visibility: hidden;} header {visibility: hidden;} footer {visibility: hidden;}
    .block-container {padding-top: 0rem; padding-bottom: 0rem;}
    
    .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #083344, #020617) !important;
        background-attachment: fixed !important;
        background-size: cover !important;
    }

    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 2px solid rgba(255,255,255,0.1); }
    .stTabs [data-baseweb="tab"] { background-color: transparent !important; border: none !important; color: #64748b; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: #10b981 !important; border-bottom: 3px solid #10b981 !important; }
    
    [data-testid="stExpander"] { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; backdrop-filter: blur(10px); }
    [data-testid="stExpander"] summary p { font-weight: 600; color: #38bdf8; font-family: 'Poppins', sans-serif; letter-spacing: 0.5px; }
    
    [data-testid="stMetric"] { background: rgba(15, 23, 42, 0.6); border-left: 4px solid #06b6d4; border-radius: 8px; padding: 15px 20px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. HEADER UTAMA
# ==========================================
html_header = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
    body {{ margin: 0; padding: 10px 0; font-family: 'Poppins', sans-serif; background: transparent; color: white; }}
    .glass-top-bar {{ background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; padding: 15px 25px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; flex-wrap: wrap; gap: 15px; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.3); }}
    .header-content {{ display: flex; align-items: center; gap: 20px; }}
    .logo-container {{ background-color: white; padding: 6px 12px; border-radius: 12px; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 10px rgba(0,0,0,0.3); }}
    .top-bar-title {{ font-size: 22px; font-weight: 800; margin: 0; color: #ffffff; letter-spacing: 1px; line-height: 1.2; }}
    .top-bar-subtitle {{ color: #06b6d4; font-size: 13px; font-weight: 400; margin-top: 4px; }}
    .profile-pill {{ background: linear-gradient(135deg, #10b981, #059669); color: #ffffff; padding: 8px 24px; border-radius: 30px; font-weight: 600; font-size: 14px; white-space: nowrap; border: 1px solid #34d399; }}
    @media (max-width: 650px) {{ .glass-top-bar {{ flex-direction: column; padding: 15px; text-align: left; align-items: stretch; }} .header-content {{ gap: 12px; }} .logo-container img {{ height: 25px !important; }} .top-bar-title {{ font-size: 18px; }} .profile-pill {{ width: 100%; text-align: center; margin-top: 5px; box-sizing: border-box; }} }}
</style>
</head>
<body>
    <div class="glass-top-bar">
        <div class="header-content">
            <div class="logo-container"><img src="{html_logo_src}" alt="Pertamina" style="height: 30px; object-fit: contain;"></div>
            <div>
                <div class="top-bar-title">CTO TERMINAL OPS</div>
                <div class="top-bar-subtitle">Nusantara Regas • Live Command Center</div>
            </div>
        </div>
        <div class="profile-pill">🟢 ON DUTY: FARIS</div>
    </div>
</body>
</html>
"""
components.html(html_header, height=140)

# ==========================================
# 5. SLIDE DROPDOWN (WIDGET CUACA, LOKASI & JAM)
# ==========================================
with st.expander("🛰️ BUKA PANEL LIVE: Jam, Cuaca & Ombak (FSRU NR)", expanded=False):
    html_widgets = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;800&display=swap');
        body {{ margin: 0; padding: 5px; font-family: 'Poppins', sans-serif; background: transparent; color: white; }}
        .info-widget-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 15px; }}
        .info-widget {{ background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 16px; padding: 15px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; gap: 5px; }}
        .time-text {{ font-size: 26px; font-weight: 800; background: -webkit-linear-gradient(#67e8f9, #06b6d4); -webkit-background-clip: text; -webkit-text-fill-color: transparent; margin: 0; line-height: 1.2; }}
        .date-text {{ font-size: 12px; font-weight: 400; color: #94a3b8; }}
        .status-badge {{ border: 2px solid #10b981; color: #10b981; padding: 4px 12px; border-radius: 8px; font-weight: 800; font-size: 12px; margin-top: 5px; }}
        @media (max-width: 650px) {{ .info-widget-row {{ grid-template-columns: repeat(2, 1fr); }} .info-widget {{ padding: 12px; }} .time-text {{ font-size: 20px; }} }}
    </style>
    </head>
    <body>
        <div class="info-widget-row">
            <div class="info-widget"><div class="time-text" id="live-time">00:00:00</div><div class="date-text" id="live-date">Memuat Tanggal...</div></div>
            <div class="info-widget"><div style="color: #06b6d4; font-size: 24px; line-height: 1;">📍</div><div><div style="font-weight: 600; font-size: 13px; color: white;">FSRU NR</div><div style="color: #94a3b8; font-size: 11px;">Teluk Jakarta</div></div></div>
            <div class="info-widget"><div style="font-size: 24px; line-height: 1;">{live_icon}</div><div><div style="font-weight: 600; font-size: 13px; color: white;">{live_cond} • {live_temp}°C</div><div style="color: #94a3b8; font-size: 11px;">🌬️ {live_wind} km/h | 🌊 Ombak {live_wave}m</div></div></div>
            <div class="info-widget"><div class="status-badge">● STANDBY OPS</div></div>
        </div>
        <script>
            function updateClock() {{ const now = new Date(); const options = {{ weekday: 'long', year: 'numeric', month: 'short', day: 'numeric' }}; document.getElementById('live-time').innerText = now.toLocaleTimeString('id-ID', {{ hour12: false }}); document.getElementById('live-date').innerText = now.toLocaleDateString('id-ID', options); }}
            setInterval(updateClock, 1000); updateClock();
        </script>
    </body>
    </html>
    """
    components.html(html_widgets, height=220)

# ==========================================
# INISIALISASI VARIABEL ESOD
# ==========================================
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
# TAB NAVIGASI UTAMA
# ==========================================
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "PHASE 1: PRE-ARRIVAL", 
    "PHASE 2: BERTHING & MEETING", 
    "PHASE 3: OPS MONITORING",
    "PHASE 4: FINAL REPORT"
])

# ==========================================
# FASE 1: H-1 (PRE-ARRIVAL & ADMINISTRASI)
# ==========================================
with tab_h1:
    with st.expander("📌 TO-DO LIST: Administrasi H-1", expanded=False):
        col_doc_h1_a, col_doc_h1_b = st.columns(2)
        with col_doc_h1_a:
            st.info("""
            **📋 Periksa Dokumen:**
            * **Cargo Manifest:** Review muatan asal.
            * **Arrival Declaration:** Pernyataan dari LNGC.
            * **MCU & Sertifikat:** Cek BSS/BOSIET dan tensi personel. Wajib clearance Dokter.
            """)
        with col_doc_h1_b:
            st.warning("""
            **📧 Kirim Korespondensi Email:**
            * **Unloading Plan:** Skema awal ke tim operasi.
            * **POB List:** Manifes surveyor ke keagenan.
            * **Hutasuhut Order:** Pesan boat untuk tim.
            """)

    st.markdown("### 🧮 Kalkulasi Awal & Skenario ROB")
    col1, col2, col3 = st.columns(3)
    with col1:
        cargo_vol = st.number_input("Rencana Kargo Masuk / Cargo to Load (m³)", min_value=10000.0, value=130000.0, step=1000.0)
    with col2:
        rob_awal = st.number_input("ROB H-1 00:00 (m³)", min_value=0.0, value=42000.0, step=500.0)
    with col3:
        serapan_harian = st.number_input("Target Serapan PLN/Day (m³)", min_value=1000.0, value=17000.0, step=500.0)

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
            tgl_eta = st.date_input("Tanggal ETA Kapal", datetime(2026, 6, 10))
        with col_t2:
            jam_eta = st.time_input("Jam ETA Kapal", value=pd.to_datetime("06:00").time())
        waktu_eta = datetime.combine(tgl_eta, jam_eta)
        
    waktu_commence = waktu_eta + timedelta(hours=8)
    st.markdown(f"<div style='padding:10px; background:rgba(16,185,129,0.1); border-radius:5px; color:#10b981;'>👉 <b>Proyeksi Mulai Commence (ETA+8j):</b> {waktu_commence.strftime('%d-%b-%Y %H:%M LCT')}</div><br>", unsafe_allow_html=True)
    target_jam_bongkar = st.number_input("Target Laytime / Durasi Bongkar Murni (Jam)", min_value=1.0, value=35.0, step=0.5)

    st.markdown("---")
    selisih_jam = (waktu_commence - waktu_rob).total_seconds() / 3600.0

    if selisih_jam < 0:
        st.error("⚠️ Waktu ROB Awal terdeteksi lebih akhir dari target Commence!")
    else:
        # A. MENCARI ROB SAAT COMMENCE DISCHARGE
        serapan_matematis = (serapan_harian / 24.0) * selisih_jam
        default_worst_case = float(int(serapan_matematis / 1000) * 1000) # Cek Worstcase (misal 8.500 jadi 8.000)
        
        col_calc1, col_calc2 = st.columns(2)
        with col_calc1:
            st.write(f"Durasi tunggu ROB hingga Commence: **{selisih_jam:.1f} Jam**")
            st.caption(f"Hitungan Matematis Murni: {serapan_matematis:,.0f} m³")
        with col_calc2:
            worst_case_serapan = st.number_input("Serapan sampai Commence (Worst Case) m³", value=default_worst_case, step=500.0)

        rob_commence = rob_awal - worst_case_serapan
        
        # B. MENCARI LAYTIME & EVALUASI SERAPAN
        volume_disrub = (rob_commence + cargo_vol) - 122500.0 # Safe filling 98%
        
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(f"ROB Saat Commence", f"{rob_commence:,.0f} m³", f"-{worst_case_serapan:,.0f} m³", delta_color="inverse")
        
        if volume_disrub > 0:
            # Evaluasi Cek apakah memenuhi Serapan/day
            regas_harian_dibutuhkan = (volume_disrub / target_jam_bongkar) * 24
            
            if regas_harian_dibutuhkan > serapan_harian:
                st.error(f"🚨 **BAHAYA TRIP:** Untuk membuang {volume_disrub:,.0f} m³ dalam {target_jam_bongkar} jam, FSRU harus memompa **{regas_harian_dibutuhkan:,.0f} m³/hari**. Ini melebihi kapasitas serapan PLN ({serapan_harian:,.0f} m³/hari). **NAIKKAN LAYTIME!**")
            else:
                st.success(f"✅ **LAYTIME AMAN:** Laju serapan regas yang dibutuhkan adalah **{regas_harian_dibutuhkan:,.0f} m³/hari**, masih di dalam batas kapasitas maksimal PLN ({serapan_harian:,.0f} m³/hari).")
                
            col_res2.metric("Volume diserap selama unloading (VL)", f"{volume_disrub:,.0f} m³", "Overfill Risk!")
        else:
            volume_disrub = 0
            col_res2.metric("Volume diserap selama unloading (VL)", "0 m³", "Aman", delta_color="normal")
            st.success("✅ Kapasitas tangki aman menampung seluruh kargo tanpa paksaan serapan ekstra.")
            
        # C. MENENTUKAN SERAPAN (LOADING RATE)
        kebutuhan_loading_raw = cargo_vol / target_jam_bongkar if target_jam_bongkar > 0 else 0
        kebutuhan_loading_bulat = int(kebutuhan_loading_raw / 100) * 100
        col_res3.metric("Loading Rate Target (CL/Laytime)", f"{kebutuhan_loading_bulat:,.0f} m³/h")

    current_waktu_murni_minutes = int(target_jam_bongkar * 60)
    if st.session_state.last_waktu_murni != target_jam_bongkar:
        st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = current_waktu_murni_minutes
        st.session_state.last_waktu_murni = target_jam_bongkar

    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.caption("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>© 2026 PT Nusantara Regas - FSRU NR Command Center Workspace</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 2: HARI H (SANDAR & PERTEMUAN)
# ==========================================
with tab_sandar:
    with st.expander("📌 TO-DO LIST: Preparation & Meeting", expanded=False):
        st.markdown("""
        * **1. ISPS Post:** Lapor & cek kelengkapan di pos.
        * **2. Trip to FSRU:** Berangkat dengan kapal Hutasuhut.
        * **3. Monitor STS:** Awasi *Ship-to-Ship* sampai *All Fast*.
        * **4. Pre-cargo Meeting:** Rapat dengan LNGC (30 mnt pasca All Fast) & L/A Connected.
        * **5. Open CTM:** Snapshot radar kapal dalam kondisi stabil.
        * **6. Supervision:** *Warm ESD Test*, *Arm Cooldown*, *Cold ESD Test*.
        """)

    st.markdown("### 📅 Live ESOD Timeline")
    st.caption("Editor Interaktif: Ubah menit atau jam, sistem akan menghitung ulang jadwal ke bawah secara otomatis.")

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
        "Tahapan Operasi": events,
        "Date / Time (LCT)": datetimes_list,
        "Durasi (Menit)": [0] + [st.session_state.durations[ev] for ev in events[1:]]
    })

    edited_table = st.data_editor(
        df_esod,
        column_config={
            "Tahapan Operasi": st.column_config.TextColumn("Tahapan Operasi", disabled=True),
            "Date / Time (LCT)": st.column_config.DatetimeColumn("Date / Time (LCT)", format="DD MMM YYYY / HH:mm"),
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
            elif "Date / Time (LCT)" in changes:
                new_dt = pd.to_datetime(changes["Date / Time (LCT)"])
                prev_dt = df_esod.loc[row_idx - 1, "Date / Time (LCT)"]
                new_calculated_dur = int((new_dt - prev_dt).total_seconds() / 60)
                if new_calculated_dur >= 0:
                    st.session_state.durations[ev_name] = new_calculated_dur
        del st.session_state["esod_editor"]
        st.rerun()

    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.caption("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>© 2026 PT Nusantara Regas - FSRU NR Command Center Workspace</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 3: MONITORING (BONGKAR & UPDATE)
# ==========================================
with tab_monitor:
    with st.expander("📌 TO-DO LIST: Discharging Execution", expanded=False):
        st.markdown("""
        * **1. Collect Data:** Ambil snapshot Open CTM (30 mnt & 15 mnt sebelum commence).
        * **2. Email Start Discharging:** Kirim saat mencapai *Full Rate*.
        * **3. Coordination:** Update rutin WA per 2-4 jam. Pantau serapan aktual PLN.
        """)

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

    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.caption("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>© 2026 PT Nusantara Regas - FSRU NR Command Center Workspace</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 4: SELESAI (PENUTUPAN & PELAPORAN)
# ==========================================
with tab_closing:
    with st.expander("📌 TO-DO LIST: Closing & Disembark", expanded=False):
        col_doc_c_a, col_doc_c_b = st.columns(2)
        with col_doc_c_a:
            st.info("""
            **📋 Validasi Dokumen Akhir:**
            * **Closing CTM:** Dicetak setelah *Draining & Purging*.
            * **Timesheet:** TTD Surveyor, LNGC, NRS.
            * **Gas Sampling Report:** GHV dari Lab Surveyor.
            * **Tank Table Tolerance:** Pastikan selisih angka radar (toleransi 0,009 antar tank table) telah divalidasi.
            """)
        with col_doc_c_b:
            st.warning("""
            **📧 Distribusi Laporan Final:**
            * **Complete Discharging Report:** Kirim sebelum POB Out / Lepas sandar.
            * **Distlist Khusus:** Manajemen, Komersial, Engineering, Top Risk.
            """)
            
    st.markdown("### 📐 Validasi Hak Milik (D. Konversi ke MMBTU)")
    col_ctm1, col_ctm2 = st.columns(2)
    with col_ctm1:
        ctm_before = st.number_input("1. CTMS Opening Register (m³)", min_value=0.0, value=134111.0, step=10.0)
        ctm_after = st.number_input("2. CTMS Closing Register (m³)", min_value=0.0, value=4611.0, step=10.0)
        ghv_input = st.number_input("3. GHV dari Sampling (BTU/SCF)", min_value=500.0, value=1033.3, step=0.1)
    
    with col_ctm2:
        actual_discharged = ctm_before - ctm_after
        variance = actual_discharged - cargo_vol
        gas_volume_mmscf = (actual_discharged / 2.0) * (ghv_input / 1033.3)
        energy_mmbtu = gas_volume_mmscf * (ghv_input / 1000.0) * 1000.0
        
        st.metric("Total LNG Discharged", f"{actual_discharged:,.0f} m³")
        st.metric("Konversi Gas (M³/GHV)", f"{gas_volume_mmscf:,.2f} MMSCF")
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

    st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.caption("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>© 2026 PT Nusantara Regas - FSRU NR Command Center Workspace</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
