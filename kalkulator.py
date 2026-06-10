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

st.set_page_config(page_title="CTO Premium Workspace", page_icon=page_icon_src, layout="wide", initial_sidebar_state="expanded")

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
    except: temp, wind, cond, icon = 31.3, 14.3, "Berawan", "⛅"
    try:
        url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height"
        res_m = requests.get(url_marine, timeout=5).json()
        wave = res_m["current"]["wave_height"]
        if wave is None: wave = 0.5
    except: wave = 0.5
    return temp, wind, wave, cond, icon

live_temp, live_wind, live_wave, live_cond, live_icon = get_live_weather()

# ==========================================
# 3. CSS CUSTOM & FLOATING BUTTON
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {background-color: transparent !important;}
    .block-container {padding-top: 0rem; padding-bottom: 0rem;}
    .stApp, [data-testid="stAppViewContainer"] {
        background: radial-gradient(circle at top left, #083344, #020617) !important;
        background-attachment: fixed !important; background-size: cover !important;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 2px solid rgba(255,255,255,0.1); }
    .stTabs [aria-selected="true"] { color: #10b981 !important; border-bottom: 3px solid #10b981 !important; }
    [data-testid="stExpander"] { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; backdrop-filter: blur(10px); }
    [data-testid="stMetric"] { background: rgba(15, 23, 42, 0.6); border-left: 4px solid #06b6d4; border-radius: 8px; padding: 15px 20px; }
    [data-testid="stSidebar"] { background-color: rgba(2, 6, 23, 0.9) !important; border-right: 1px solid rgba(255,255,255,0.1); }
    .stCheckbox label { font-size: 13px !important; color: #e2e8f0 !important; }
    
    /* Tombol Floating untuk akses Sidebar */
    .floating-btn {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background: #10b981;
        color: white;
        padding: 15px 25px;
        border-radius: 50px;
        font-weight: 800;
        cursor: pointer;
        z-index: 9999;
        box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4);
        border: none;
    }
</style>
""", unsafe_allow_html=True)

# Tombol Floating JavaScript
components.html("""
<button class="floating-btn" onclick="openSidebar()">☰ MENU OPS</button>
<script>
    function openSidebar() {
        var buttons = window.parent.document.querySelectorAll('button[aria-label="Open sidebar"]');
        if (buttons.length > 0) { buttons[0].click(); }
    }
</script>
""", height=70)

# ==========================================
# 4. INISIALISASI SESSION STATE (GLOBAL)
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

# ==========================================
# 5. SIDEBAR: TO-DO LIST & QUICK OPS CALC
# ==========================================
with st.sidebar:
    st.image(html_logo_src, use_container_width=True)
    
    st.markdown("### ✅ Interactive To-Do Ops")
    with st.expander("🗓️ DAY -1 (Pre-Arrival)", expanded=False):
        st.checkbox("WAG Monitoring (Info posisi & cuaca)", key="td_d1_1")
        st.checkbox("WAG Patroli Laut (Waktu STS)", key="td_d1_2")
        st.checkbox("Hubungi Dispatcher JCC (Serapan)", key="td_d1_3")
        st.checkbox("Hubungi PLN & Surveyor (Onboard)", key="td_d1_4")
        st.checkbox("Konfirmasi Surat Perintah PLN EPI", key="td_d1_5")
        st.markdown("---")
        st.checkbox("Draft Loading Plan", key="td_d1_6")
        st.checkbox("Draft List Personeel & Persyaratan", key="td_d1_7")
        st.checkbox("Draft Flowchart Estimation", key="td_d1_8")
        st.checkbox("TTD JoA & CoU (Master NRS)", key="td_d1_9")
        st.markdown("---")
        st.checkbox("Email Permission Onboard & Boat", key="td_d1_10")
        st.checkbox("Email JoA, CoU, Loading Plan", key="td_d1_11")

    with st.expander("🗓️ DAY 1 (Berthing & Start)", expanded=False):
        st.checkbox("Lapor Pos ISPS & Trip ke FSRU", key="td_d2_1")
        st.checkbox("Monitor STS sampai All Fast", key="td_d2_2")
        st.checkbox("Pelaksanaan Pre-cargo Meeting", key="td_d2_3")
        st.checkbox("Snapshot Radar: Open CTM", key="td_d2_4")
        st.checkbox("Supervisi Warm/Cold ESD & Arm C/D", key="td_d2_5")
        st.checkbox("Start Discharging s.d Full Rate", key="td_d2_6")
        st.checkbox("Email Report: Start Discharging", key="td_d2_7")

    with st.expander("🗓️ DAY 2 (Monitoring)", expanded=False):
        st.checkbox("Update POB Out (Keagenan & ISPS)", key="td_d3_1")
        st.checkbox("Update perhitungan LNG to go", key="td_d3_2")
        st.checkbox("Koordinasi Rate Down (Kargo Kritis)", key="td_d3_3")
        st.checkbox("Persiapan awal Closing CTM", key="td_d3_4")

    with st.expander("🗓️ DAY 3 (Completed & Out)", expanded=False):
        st.checkbox("Eksekusi Draining & Purging", key="td_d4_1")
        st.checkbox("Snapshot Radar: Closing CTM", key="td_d4_2")
        st.checkbox("Proses Arm Disconnect", key="td_d4_3")
        st.checkbox("TTD Dokumen (Timesheet, Sertifikat)", key="td_d4_4")
        st.checkbox("POB Out, Unmooring, Trip Pos ISPS", key="td_d4_5")
        st.checkbox("Email Report Final (Cargo Document)", key="td_d4_6")

    st.divider()
    
    st.markdown("### 🧮 Quick Ops Calc")
    with st.expander("⏱️ Hitung Sisa Waktu (LNG)", expanded=False):
        sb_vol = st.number_input("Sisa Kargo (m³)", min_value=0.0, value=15000.0, step=500.0)
        sb_rate = st.number_input("Laju Pompa (m³/h)", min_value=1.0, value=3500.0, step=100.0)
        st.markdown(f"<div style='padding:10px; background:#1e293b; border-radius:5px; border-left:3px solid #0ea5e9;'><span style='color:#94a3b8; font-size:12px;'>Estimasi Sisa Jam</span><br><span style='font-size:18px; font-weight:bold; color:#0ea5e9;'>{(sb_vol/sb_rate if sb_rate > 0 else 0):.1f} Jam</span></div>", unsafe_allow_html=True)
    with st.expander("🔄 Konversi Serapan PLN", expanded=False):
        sb_serapan = st.number_input("Target (m³/hari)", min_value=0.0, value=17000.0, step=500.0)
        st.markdown(f"<div style='padding:10px; background:#1e293b; border-radius:5px; border-left:3px solid #10b981;'><span style='color:#94a3b8; font-size:12px;'>Laju Regas Aktual</span><br><span style='font-size:18px; font-weight:bold; color:#10b981;'>{(sb_serapan/24):,.1f} m³/h</span></div>", unsafe_allow_html=True)
    with st.expander("🔢 Kalkulator Standar", expanded=False):
        components.html("""
        <style>@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'); body{font-family:'Poppins',sans-serif;background:transparent;margin:0;}.calc{background:rgba(30,41,59,0.5);border-radius:12px;padding:10px;}.disp{width:100%;background:#0f172a;color:#fff;font-size:20px;text-align:right;padding:10px;border-radius:8px;border:1px solid #334155;margin-bottom:10px;box-sizing:border-box;}.btns{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;}button{background:rgba(255,255,255,0.1);color:#fff;border:none;padding:10px;border-radius:5px;cursor:pointer;}.btn-eq{background:#10b981;grid-column:span 2;}.btn-c{background:rgba(239,68,68,0.2);color:#f87171;grid-column:span 2;}</style>
        <div class="calc"><input type="text" class="disp" id="d" disabled><div class="btns"><button class="btn-c" onclick="d.value=''">C</button><button onclick="d.value+='('">(</button><button onclick="d.value+=')')">)</button><button onclick="d.value+='7'">7</button><button onclick="d.value+='8'">8</button><button onclick="d.value+='9'">9</button><button onclick="d.value+='/'">÷</button><button onclick="d.value+='4'">4</button><button onclick="d.value+='5'">5</button><button onclick="d.value+='6'">6</button><button onclick="d.value+='*'">×</button><button onclick="d.value+='1'">1</button><button onclick="d.value+='2'">2</button><button onclick="d.value+='3'">3</button><button onclick="d.value+='-'">-</button><button onclick="d.value+='0'">0</button><button onclick="d.value+='.'">.</button><button class="btn-eq" onclick="d.value=eval(d.value)">=</button><button onclick="d.value+='+'">+</button></div></div>
        """, height=300)

# ==========================================
# 6. HEADER LIVE
# ==========================================
components.html(f"""
<div style="background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:15px 25px;display:flex;justify-content:space-between;align-items:center;color:white;font-family:'Poppins',sans-serif;">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="background:white;padding:5px 10px;border-radius:10px;"><img src="{html_logo_src}" style="height:30px;"></div>
        <div><div style="font-size:22px;font-weight:800;">CTO TERMINAL OPS</div><div style="color:#06b6d4;font-size:13px;">Nusantara Regas • Live Command Center</div></div>
    </div>
    <div style="background:linear-gradient(135deg,#10b981,#059669);padding:8px 24px;border-radius:30px;font-weight:600;font-size:14px;border:1px solid #34d399;">🟢 ON DUTY: FARIS</div>
</div>
""", height=120)

with st.expander("🛰️ BUKA PANEL LIVE: Jam, Cuaca & Ombak (FSRU NR)", expanded=False):
    components.html(f"""
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:15px;color:white;font-family:'Poppins',sans-serif;">
        <div style="background:rgba(30,41,59,0.5);border-radius:16px;padding:15px;text-align:center;"><div style="font-size:26px;font-weight:800;color:#38bdf8;" id="t">00:00:00</div><div style="font-size:12px;color:#94a3b8;" id="d2">...</div></div>
        <div style="background:rgba(30,41,59,0.5);border-radius:16px;padding:15px;text-align:center;"><div style="color:#06b6d4;font-size:24px;">📍</div><div style="font-weight:600;font-size:13px;">FSRU NR</div><div style="font-size:11px;color:#94a3b8;">Teluk Jakarta</div></div>
        <div style="background:rgba(30,41,59,0.5);border-radius:16px;padding:15px;text-align:center;"><div style="font-size:24px;">{live_icon}</div><div style="font-weight:600;font-size:13px;">{live_cond} • {live_temp}°C</div><div style="font-size:11px;color:#94a3b8;">🌬️ {live_wind} km/h | 🌊 Ombak {live_wave}m</div></div>
        <div style="background:rgba(30,41,59,0.5);border-radius:16px;padding:15px;text-align:center;"><div style="border:2px solid #10b981;color:#10b981;padding:4px 12px;border-radius:8px;font-weight:800;font-size:12px;margin-top:5px;">● STANDBY OPS</div></div>
    </div>
    <script>setInterval(()=>{{const n=new Date();t.innerText=n.toLocaleTimeString('id-ID',{{hour12:false}});d2.innerText=n.toLocaleDateString('id-ID',{{weekday:'long',year:'numeric',month:'short',day:'numeric'}})}},1000);</script>
    """, height=180)

# ==========================================
# 7. MAIN NAVIGATION & INTEGRASI
# ==========================================
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "PHASE 1: PRE-ARRIVAL", "PHASE 2: BERTHING", "PHASE 3: MONITORING", "PHASE 4: FINAL REPORT"
])

# ==========================================
# FASE 1: PRE-ARRIVAL
# ==========================================
with tab_h1:
    with st.expander("📌 TO-DO LIST: DAY -1 (Aktivitas H-1 Sebelum STS)", expanded=False):
        col_td1, col_td2, col_td3 = st.columns(3)
        with col_td1:
            st.info("""
            **🗣️ Coordination:**
            * **WAG Monitoring Discharge:** Info posisi LNGC & Cuaca.
            * **WAG Patroli Laut:** Info rencana waktu STS.
            * **Dispatcher JCC:** Hubungi terkait rencana serapan.
            * **PLN & Surveyor:** Konfirmasi perwakilan *onboard*.
            * **PLN EPI:** Konfirmasi Surat Perintah Discharge.
            """)
        with col_td2:
            st.success("""
            **📝 Draft Report:**
            * Susun *Loading Plan*.
            * *List Lampiran Personeel Onboard*.
            * Lampiran persyaratan Onboard LNGC.
            * *Draft Flow chart Estimation Discharging*.
            * *Sign JoA & CoU* dari Master NRS.
            """)
        with col_td3:
            st.warning("""
            **📧 Send Email:**
            * *Permission Onboard and Using Hutasuhut*.
            * Dokumen *JoA and CoU*.
            * *Loading / Unloading Plan*.
            """)

    st.markdown("### 🧮 Kalkulasi Laytime & Durasi Pompa Murni")
    st.caption("Pemisahan otomatis antara Laytime Kontrak (NOR s.d Disconnect Arm) dengan Waktu Pemompaan Murni.")
    
    col_lt1, col_lt2 = st.columns(2)
    with col_lt1:
        # INPUT LAYTIME KONTRAK (Payung Besar)
        laytime_kontrak = st.number_input("Total Laytime Kontrak (Jam)", min_value=1.0, value=42.0, step=0.5, help="Dihitung dari NOR Receive sampai Disconnect Arm")
    with col_lt2:
        # Menghitung Allowance Persiapan (NOR Receive s.d Start Full Rate)
        allowance_prep_mins = (
            st.session_state.durations["ARMs Connected"] + 
            st.session_state.durations["OPEN CTM"] + 
            st.session_state.durations["WARM ESD Test"] + 
            st.session_state.durations["Arm C/D"] + 
            st.session_state.durations["COLD ESD Test"] + 
            st.session_state.durations["START DISCHARGING"] + 
            st.session_state.durations["FULL RATE"]
        )
        # Menghitung Allowance Closing (Complete Discharging s.d Disconnect Arm)
        allowance_closing_mins = (
            st.session_state.durations["DISCHARGING COMPLETED"] + 
            st.session_state.durations["CLOSING CTM"] + 
            st.session_state.durations["ARMs Disconnected"]
        )
        
        total_allowance_hours = (allowance_prep_mins + allowance_closing_mins) / 60.0
        
        # TARGET JAM BONGKAR = WAKTU PEMOMPAAN MURNI (Rate Down)
        target_jam_bongkar = laytime_kontrak - total_allowance_hours
        
        st.metric(
            "Durasi Pompa Murni (Tersedia)", 
            f"{target_jam_bongkar:.1f} Jam", 
            f"Potongan Persiapan & Closing: -{total_allowance_hours:.1f} Jam", 
            delta_color="inverse"
        )
        
    # Update Session State Durasi Pompa Murni secara otomatis!
    st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = int(target_jam_bongkar * 60)

    st.markdown("---")
    st.markdown("#### ⏳ Kalkulasi Kargo & Skenario ROB")
    c1, c2, c3 = st.columns(3)
    with c1: cargo_vol = st.number_input("Cargo to Load (m³)", min_value=10000.0, value=130000.0, step=1000.0)
    with c2: rob_awal = st.number_input("ROB H-1 00:00 (m³)", min_value=0.0, value=42000.0, step=500.0)
    with c3: serapan_harian = st.number_input("Target Serapan PLN/Day (m³)", min_value=1000.0, value=17000.0, step=500.0)
    
    st.markdown("#### ⏳ Sinkronisasi Waktu")
    cw1, cw2 = st.columns(2)
    with cw1:
        st.caption("Record ROB")
        rd1, rt1 = st.columns(2)
        tgl_rob = rd1.date_input("Tanggal ROB", datetime(2026, 6, 9))
        jam_rob = rt1.time_input("Jam ROB", datetime.strptime("00:00", "%H:%M").time())
        waktu_rob = datetime.combine(tgl_rob, jam_rob)
    with cw2:
        st.caption("ETA Kapal")
        rd2, rt2 = st.columns(2)
        tgl_eta = rd2.date_input("Tanggal ETA", datetime(2026, 6, 10))
        jam_eta = rt2.time_input("Jam ETA", datetime.strptime("06:00", "%H:%M").time())
        waktu_eta = datetime.combine(tgl_eta, jam_eta)

    waktu_commence = waktu_eta + timedelta(hours=8)
    selisih_jam_rob = (waktu_commence - waktu_rob).total_seconds() / 3600.0
    serapan_matematis = (serapan_harian / 24.0) * selisih_jam_rob
    worst_case_serapan = float(int(serapan_matematis / 1000) * 1000)
    rob_commence = rob_awal - worst_case_serapan
    volume_disrub = (rob_commence + cargo_vol) - 122500.0

    st.markdown("---")
    res1, res2, res3 = st.columns(3)
    res1.metric("ROB Saat Commence", f"{rob_commence:,.0f} m³")
    if volume_disrub > 0:
        regas_needed = (volume_disrub / target_jam_bongkar) * 24
        if regas_needed > serapan_harian: st.error(f"🚨 **BAHAYA TRIP:** Butuh {regas_needed:,.0f} m³/day (Max {serapan_harian:,.0f}).")
        else: st.success(f"✅ **AMAN:** Butuh {regas_needed:,.0f} m³/day.")
        res2.metric("VL (Diserap Unloading)", f"{volume_disrub:,.0f} m³", "Overfill Risk")
    else: res2.metric("VL (Diserap Unloading)", "0 m³", "Safe Tank")
    
    loading_rate_target = cargo_vol / target_jam_bongkar if target_jam_bongkar > 0 else 0
    res3.metric("Loading Rate Target", f"{int(loading_rate_target/100)*100:,.0f} m³/h")

    with st.expander("📊 MULTI-SCENARIO PLANNER (Metode Pak Suci)", expanded=False):
        def build_sc(c_sc, l_sc_total, r_sc):
            # l_sc_total = Laytime kontrak (payung besar)
            t_start = waktu_eta + timedelta(hours=8)
            # Waktu pemompaan murni = l_sc_total - allowance
            t_pure_pumping = l_sc_total - total_allowance_hours
            t_comp = t_start + timedelta(hours=t_pure_pumping)
            t_out = t_start + timedelta(hours=l_sc_total) # Disconnect Arm / Akhir Laytime
            return [waktu_eta.strftime("%d %b / %H:%M"), t_start.strftime("%d %b / %H:%M"), f"{c_sc:,.0f}", f"{l_sc_total}", t_comp.strftime("%d %b / %H:%M"), t_out.strftime("%d %b / %H:%M")]
        
        st.dataframe(pd.DataFrame({
            "Parameter": ["POB (ETA)", "Est. Start Discharge", "Cargo to Load", "Laytime Kontrak (H)", "Est. Complete Pumping", "Est. Disconnect (End Laytime)"],
            "1st Est (Aktual)": build_sc(cargo_vol, laytime_kontrak, 709),
            "2nd Est (Aman)": build_sc(cargo_vol, 46.3, 577),
            "3rd Est (Cepat)": build_sc(120000, 38.0, 561)
        }), use_container_width=True, hide_index=True)

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# PROYEKSI WAKTU ESOD (INTEGRASI TAB 2 & 3)
# ==========================================
events_list = ["ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", "FULL RATE", "Bongkar Muat Murni (Rate Down)", "DISCHARGING COMPLETED", "CLOSING CTM", "ARMs Disconnected", "Documentation", "POB OUT"]
temp_dt = waktu_eta
esod_times = [temp_dt]
for ev in events_list[1:]:
    temp_dt += timedelta(minutes=st.session_state.durations[ev])
    esod_times.append(temp_dt)

waktu_snapshot = esod_times[events_list.index("Arm C/D")] - timedelta(minutes=5)

# ==========================================
# FASE 2: BERTHING
# ==========================================
with tab_sandar:
    with st.expander("📌 TO-DO LIST: DAY 1 (Berthing & Start Discharging)", expanded=False):
        st.markdown(f"""
        * **Trip to FSRU:** Lapor pos ISPS dan berangkat.
        * **Proses STS - All Fast:** Awasi manuver sandar kapal (*Ship to Ship*) hingga *All Fast*.
        * **Precargo Meeting:** Laksanakan rapat koordinasi dengan Master LNGC.
        * **Open CTM:** Ambil snapshot radar CTM.
        * **Preparation & Start:** Lakukan pengujian (*Warm ESD, Arm C/D, Cold ESD*) berlanjut ke *Start Discharging* hingga mencapai *Full Rate*.
        * **📧 Send Email Report:** Kirimkan notifikasi *Start Discharging* (beserta lampiran bukti Open CTM).
        """)

    st.info(f"📸 **PENGINGAT (Terkait Open CTM):** Snapshot Radar wajib diambil pada pukul **{waktu_snapshot.strftime('%H:%M')} LCT** (Tepat 5 menit sebelum *Arm Cooldown* dimulai).")
    
    st.markdown("### 📅 Live ESOD Timeline")
    df_esod = pd.DataFrame({"Tahapan": events_list, "Waktu (LCT)": esod_times, "Durasi (Min)": [0] + [st.session_state.durations[e] for e in events_list[1:]]})
    ed_table = st.data_editor(df_esod, column_config={"Tahapan": st.column_config.TextColumn(disabled=True)}, use_container_width=True, hide_index=True, key="esod_ed")
    if st.session_state.esod_ed["edited_rows"]:
        for r, change in st.session_state.esod_ed["edited_rows"].items():
            if "Durasi (Min)" in change: st.session_state.durations[events_list[int(r)]] = change["Durasi (Min)"]
        st.rerun()
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 3: MONITORING
# ==========================================
with tab_monitor:
    with st.expander("📌 TO-DO LIST: DAY 2 (Monitoring Discharging)", expanded=False):
        st.markdown("""
        * **Coordination - Update POB Out:** Infokan estimasi keberangkatan kapal ke pihak terkait (Keagenan & Pos ISPS).
        * **Update LNG to go:** Pantau dan hitung rutin sisa volume kargo yang harus dibongkar.
        * **Rate Down - Completed:** Koordinasi dengan Chief Officer saat volume mulai kritis untuk *Rate Down* hingga *Discharging Completed*.
        * **Possibility of Closing CTM / Disconnect Arm:** Siapkan prosedur *Closing CTM*, *Disconnect Arm*, dan *Documentation* apabila operasi berpotensi selesai lebih cepat dari jadwal.
        """)

    st.markdown(f"**Jadwal Eksekusi Snapshot Radar (Pre-Cooling):** {waktu_snapshot.strftime('%H:%M')} LCT")
    mt1, mt2 = st.columns(2)
    togo_vol = mt1.number_input("Volume LNG To Go (m³)", value=32000.0)
    togo_rate = mt1.number_input("Actual Loading Rate (m³/h)", value=4000.0)
    sisa_h = togo_vol / togo_rate if togo_rate > 0 else 0
    mt2.metric("Sisa Waktu Pemompaan", f"{sisa_h:.1f} Jam")
    mt2.metric("Estimasi Selesai", (datetime.now() + timedelta(hours=sisa_h)).strftime("%H:%M LCT"))
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 4: FINAL REPORT
# ==========================================
with tab_closing:
    with st.expander("📌 TO-DO LIST: DAY 3 (Completed & Demobilization)", expanded=False):
        col_d3_a, col_d3_b = st.columns(2)
        with col_d3_a:
            st.info("""
            **📋 Final Ops & Documentation:**
            * Eksekusi *Draining, Purging*, dan *Closing CTM*.
            * Proses *Arm Disconnect* (Batas Akhir Argo Laytime).
            * Lengkapi *Documentation* (Tanda tangan Surveyor, LNGC, dan NRS).
            """)
        with col_d3_b:
            st.warning("""
            **⛴️ Demobilisasi & Reporting:**
            * *POB Out, Unmooring*, dan *Trip ke Pos ISPS*.
            * **📧 Send Email Report:** Kirim dokumen final *Cargo Document* ke manajemen.
            """)

    st.markdown("### 📐 Validasi Hak Milik & Energy Delivered")
    f1, f2, f3 = st.columns(3)
    v_open = f1.number_input("CTMS Opening Register (m³)", value=cargo_vol + 5000)
    v_close = f1.number_input("CTMS Closing Register (m³)", value=5000.0)
    v_act = v_open - v_close
    
    dens = f2.number_input("Density LNG (kg/m³)", value=450.0)
    mghv = f2.number_input("Mass GHV (MJ/kg)", value=54.5)
    vghv = f2.number_input("Vapor GHV (MJ/m³)", value=35.676)
    
    vt = f3.number_input("Vapor Temp (°C)", value=-130.0)
    vp = f3.number_input("Vapor Press (mbar)", value=1013.0)
    gc = f3.number_input("Gas Consumed (MMBtu)", value=1500.0)

    qr = v_act * (288.15 / (273.15 + vt)) * (vp / 1013.25) * vghv
    qty_gross = ((v_act * dens * mghv) - qr) / 1055.12
    qty_net = qty_gross - gc

    st.divider()
    rf1, rf2, rf3 = st.columns(3)
    rf1.metric("Vapor Return (Qr)", f"{qr:,.0f} MJ")
    rf2.metric("Gross Energy", f"{qty_gross:,.0f} MMBtu")
    rf3.metric("NET ENERGY DELIVERED", f"{qty_net:,.0f} MMBtu")
    
    st.download_button("📊 Download Official Report", data=io.BytesIO().getvalue(), file_name="CTM_Report.xlsx")
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
