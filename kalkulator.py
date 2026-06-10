import os
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import io
import requests
import streamlit.components.v1 as components
import base64
import pickle
import json

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
# 2. HALAMAN LOGIN & SSO (SINGLE SIGN-ON)
# ==========================================
SESSION_FILE = "user_session.json"

if "logged_in" not in st.session_state:
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                saved_session = json.load(f)
            st.session_state["logged_in"] = saved_session.get("logged_in", False)
            st.session_state["user_name"] = saved_session.get("user_name", "")
        except:
            st.session_state["logged_in"] = False
            st.session_state["user_name"] = ""
    else:
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""

if not st.session_state["logged_in"]:
    st.markdown("""
        <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .login-box {
            background: rgba(15, 23, 42, 0.8);
            padding: 40px;
            border-radius: 20px;
            border: 1px solid rgba(255,255,255,0.1);
            box-shadow: 0 8px 32px 0 rgba(0,0,0,0.5);
            text-align: center;
            margin-top: 50px;
        }
        </style>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        st.markdown(f"<div class='login-box'>", unsafe_allow_html=True)
        st.markdown(f"<img src='{html_logo_src}' width='150' style='margin-bottom: 20px;'>", unsafe_allow_html=True)
        st.markdown("<h2 style='color: white; font-weight: 800;'>CTO COMMAND CENTER</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color: #06b6d4; letter-spacing: 2px; margin-bottom: 30px;'>FSRU NUSANTARA REGAS</p>", unsafe_allow_html=True)
        
        user_selected = st.selectbox("👤 PILIH IDENTITAS PETUGAS (CTO ON DUTY):", ["Faris Taruna", "Suci Helwandi"])
        st.write("")
        if st.button("🚀 MASUK WORKSPACE", use_container_width=True):
            st.session_state["logged_in"] = True
            st.session_state["user_name"] = user_selected
            with open(SESSION_FILE, "w") as f:
                json.dump({"logged_in": True, "user_name": user_selected}, f)
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ==========================================
# 3. FUNGSI PENGAMBIL DATA CUACA & OMBAK
# ==========================================
@st.cache_data(ttl=900)
def get_live_weather():
    lat, lon = -5.98, 106.83
    head = {"User-Agent": "CTO-Ops/1.0"}
    try:
        url_weather = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&windspeed_unit=kmh"
        res_w = requests.get(url_weather, headers=head, timeout=2).json()
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
        res_m = requests.get(url_marine, headers=head, timeout=2).json()
        wave = res_m["current"]["wave_height"]
        if wave is None: wave = 0.5
    except: wave = 0.5
    return temp, wind, wave, cond, icon

live_temp, live_wind, live_wave, live_cond, live_icon = get_live_weather()
live_wind_knots = live_wind * 0.539957

# ==========================================
# 4. CSS CUSTOM & FLOATING BUTTON
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
# 5. GLOBAL EVENTS & CALLBACK FUNGSI ANTI-LAG
# ==========================================
events_list = ["ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", "FULL RATE", "Bongkar Muat Murni (Rate Down)", "DISCHARGING COMPLETED", "CLOSING CTM", "ARMs Disconnected", "Documentation", "POB OUT"]

if "durations" not in st.session_state:
    st.session_state.durations = {
        "All Fast": 180, "NOR Received": 55, "ARMs Connected": 30,
        "OPEN CTM": 35, "WARM ESD Test": 15, "Arm C/D": 90,
        "COLD ESD Test": 15, "START DISCHARGING": 20, "FULL RATE": 30,
        "Bongkar Muat Murni (Rate Down)": 2100,
        "DISCHARGING COMPLETED": 30, "CLOSING CTM": 120,
        "ARMs Disconnected": 10, "Documentation": 60, "POB OUT": 120
    }

def update_esod():
    if "esod_ed" in st.session_state:
        edited = st.session_state.esod_ed.get("edited_rows", {})
        for r, change in edited.items():
            if "Durasi (Min)" in change: 
                original_event_name = events_list[int(r)]
                st.session_state.durations[original_event_name] = change["Durasi (Min)"]

# ==========================================
# 6. SIDEBAR: MANAJEMEN SESI & QUICK OPS CALC
# ==========================================
with st.sidebar:
    st.image(html_logo_src, use_container_width=True)
    
    st.markdown("### 💾 Manajemen Sesi Operasi")
    col_sv1, col_sv2 = st.columns(2)
    if col_sv1.button("Simpan Kondisi", help="Simpan semua data input saat ini"):
        save_dict = {}
        for k, v in st.session_state.items():
            if k.endswith("_input") or k == "durations":
                save_dict[k] = v
        with open("ops_kondisi_terakhir.pkl", "wb") as f:
            pickle.dump(save_dict, f)
        st.toast("✅ Kondisi operasional berhasil disimpan ke sistem!")

    if col_sv2.button("Muat Kondisi", help="Kembalikan data dari penyimpanan terakhir"):
        if os.path.exists("ops_kondisi_terakhir.pkl"):
            with open("ops_kondisi_terakhir.pkl", "rb") as f:
                loaded_state = pickle.load(f)
            for k, v in loaded_state.items():
                st.session_state[k] = v
            st.toast("✅ Kondisi berhasil dikembalikan!")
            st.rerun()
        else:
            st.error("Belum ada file kondisi yang disimpan.")
            
    if st.button("🚪 Logout / Ganti User", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()
            
    st.divider()

    st.markdown("### 🧮 Quick Ops Calc")
    st.caption("Kalkulator Cepat Evaluasi Parameter FSRU")
    
    with st.expander("⚡ Hitung Kebutuhan Serapan & Laytime", expanded=True):
        qo_rob = st.number_input("ROB Aktual / Estimasi (m³)", min_value=0.0, value=42000.0, step=500.0, key="qo_rob")
        qo_cargo = st.number_input("Cargo In / To Go (m³)", min_value=0.0, value=130000.0, step=1000.0, key="qo_cargo")
        qo_rate = st.number_input("Rencana Loading Rate (m³/h)", min_value=1.0, value=3700.0, step=100.0, key="qo_rate")
        qo_safe = st.number_input("Safe Filling Limit (m³)", min_value=100000.0, value=122500.0, step=500.0, key="qo_safe")
        
        st.markdown("---")
        if qo_rate > 0:
            qo_durasi = qo_cargo / qo_rate
            qo_vl = (qo_rob + qo_cargo) - qo_safe
            qo_req_serapan_h = qo_vl / qo_durasi if qo_vl > 0 else 0
            qo_req_serapan_d = qo_req_serapan_h * 24
            
            st.markdown(f"<div style='font-size:13px; color:#94a3b8;'>⏱️ Durasi Pompa Dibutuhkan:</div><div style='font-size:18px; font-weight:bold; color:#38bdf8; margin-bottom:10px;'>{qo_durasi:.1f} Jam</div>", unsafe_allow_html=True)
            
            if qo_vl > 0:
                st.markdown(f"<div style='font-size:13px; color:#94a3b8;'>🔥 Serapan Wajib (Mencegah Overfill):</div><div style='font-size:18px; font-weight:bold; color:#f59e0b;'>{qo_req_serapan_h:,.0f} m³/h</div><div style='font-size:14px; color:#fbbf24;'>({qo_req_serapan_d:,.0f} m³/day)</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size:13px; color:#94a3b8;'>🔥 Serapan Wajib:</div><div style='font-size:18px; font-weight:bold; color:#10b981;'>Aman (0 m³/h)</div><div style='font-size:14px; color:#34d399;'>Kapasitas tangki memadai</div>", unsafe_allow_html=True)
            
            qo_est_selesai = datetime.now() + timedelta(hours=qo_durasi)
            st.markdown(f"<div style='margin-top:10px; padding-top:10px; border-top:1px solid #334155; font-size:12px; color:#94a3b8;'>Selesai pada (Real-Time): <strong style='color:#10b981;'>{qo_est_selesai.strftime('%H:%M LCT')}</strong></div>", unsafe_allow_html=True)

    with st.expander("🔢 Kalkulator Standar", expanded=False):
        components.html("""
        <style>@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'); body{font-family:'Poppins',sans-serif;background:transparent;margin:0;}.calc{background:rgba(30,41,59,0.5);border-radius:12px;padding:10px;}.disp{width:100%;background:#0f172a;color:#fff;font-size:20px;text-align:right;padding:10px;border-radius:8px;border:1px solid #334155;margin-bottom:10px;box-sizing:border-box;}.btns{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;}button{background:rgba(255,255,255,0.1);color:#fff;border:none;padding:10px;border-radius:5px;cursor:pointer;}.btn-eq{background:#10b981;grid-column:span 2;}.btn-c{background:rgba(239,68,68,0.2);color:#f87171;grid-column:span 2;}</style>
        <div class="calc"><input type="text" class="disp" id="d" disabled><div class="btns"><button class="btn-c" onclick="d.value=''">C</button><button onclick="d.value+='('">(</button><button onclick="d.value+=')')">)</button><button onclick="d.value+='7'">7</button><button onclick="d.value+='8'">8</button><button onclick="d.value+='9'">9</button><button onclick="d.value+='/'">÷</button><button onclick="d.value+='4'">4</button><button onclick="d.value+='5'">5</button><button onclick="d.value+='6'">6</button><button onclick="d.value+='*'">×</button><button onclick="d.value+='1'">1</button><button onclick="d.value+='2'">2</button><button onclick="d.value+='3'">3</button><button onclick="d.value+='-'">-</button><button onclick="d.value+='0'">0</button><button onclick="d.value+='.'">.</button><button class="btn-eq" onclick="d.value=eval(d.value)">=</button><button onclick="d.value+='+'">+</button></div></div>
        """, height=300)

# ==========================================
# 7. HEADER LIVE
# ==========================================
user_display = str(st.session_state["user_name"]).upper()
components.html(f"""
<div style="background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:15px 25px;display:flex;justify-content:space-between;align-items:center;color:white;font-family:'Poppins',sans-serif;">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="background:white;padding:5px 10px;border-radius:10px;"><img src="{html_logo_src}" style="height:30px;"></div>
        <div><div style="font-size:22px;font-weight:800;">CTO TERMINAL OPS</div><div style="color:#06b6d4;font-size:13px;">Nusantara Regas • Live Command Center</div></div>
    </div>
    <div style="background:linear-gradient(135deg,#10b981,#059669);padding:8px 24px;border-radius:30px;font-weight:600;font-size:14px;border:1px solid #34d399;">🟢 ON DUTY: {user_display}</div>
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
# 8. MAIN NAVIGATION & INTEGRASI LINTAS TAB
# ==========================================
tab_weather, tab_h1, tab_sandar, tab_monitor, tab_rob, tab_closing = st.tabs([
    "PHASE 0: WEATHER LIMIT", "PHASE 1: PRE-ARRIVAL", "PHASE 2: BERTHING", "PHASE 3: MONITORING", "PHASE 4: ROB PROJECTION", "PHASE 5: FINAL REPORT"
])

# ==========================================
# FASE 0: WEATHER RESTRICTIONS
# ==========================================
with tab_weather:
    st.markdown("### 🌪️ Evaluasi Cuaca & Keselamatan Operasi")
    st.caption("Berdasarkan NRS Terminal Guide - Evaluasi Go/No-Go operasional kapal.")
    
    cw_1, cw_2, cw_3, cw_4 = st.columns(4)
    with cw_1:
        inp_wind = st.number_input("Wind Speed (Knots)", min_value=0.0, value=float(live_wind_knots), step=1.0)
    with cw_2:
        inp_gust = st.number_input("Wind Gusts (Knots)", min_value=0.0, value=float(live_wind_knots * 1.2), step=1.0)
    with cw_3:
        inp_sea = st.number_input("Sea / Wave (m)", min_value=0.0, value=float(live_wave), step=0.1)
    with cw_4:
        inp_vis = st.number_input("Visibility (Nm)", min_value=0.0, value=5.0, step=0.5)
        
    inp_lightning = st.checkbox("⚡ Terdapat Petir / Lightning (Radius berbahaya)?")
    
    st.markdown("---")
    st.markdown("#### 🚨 Keputusan Operasional (NRS Guide):")
    
    action_triggered = False
    
    if inp_wind > 35 or inp_gust > 40 or inp_sea > 2.0:
        st.error("🔴 **CRITICAL ACTION: DISCONNECT ARM IMMEDIATELY!**")
        st.markdown("*Kondisi cuaca telah melebihi batas toleransi FSRU untuk menahan kapal. Segera diskonek lengan pemuat dan persiapkan evakuasi jika diperlukan.*")
        action_triggered = True
        
    elif inp_wind > 28 or inp_gust > 34 or inp_lightning:
        st.error("🔴 **CRITICAL ACTION: STOP CARGO OPERATION!**")
        st.markdown("*Hentikan seluruh operasi pompa. (Catatan: Cargo lines dapat tetap dijaga suhunya menggunakan spray pumps selama petir).*")
        action_triggered = True
        
    elif inp_wind > 20 or inp_sea > 1.5 or inp_vis < 2.0:
        st.warning("🟠 **RESTRICTION: NO BERTHING ALLOWED!**")
        st.markdown("*Kapal tidak diizinkan sandar. Cuaca belum memenuhi standar keselamatan manuver. Tunda operasi (Postponed).*")
        action_triggered = True
        
    elif inp_wind >= 17:
        st.info("🟡 **CAUTION: BERTHING / UNBERTHING ALLOWED WITH 4 TUGS.**")
        st.markdown("*Kondisi angin cukup kuat. Wajib menggunakan 4 Tugboat untuk assist manuver.*")
        action_triggered = True
        
    if inp_wind > 20 and not action_triggered:
        st.warning("🟠 **RESTRICTION: STOP USE OF PERSONNEL CRANE.**")
        action_triggered = True
    elif inp_wind > 20 and action_triggered:
        st.write("*(Tambahan: Stop Use of Personnel Crane)*")
        
    if not action_triggered:
        st.success("✅ **SAFE TO OPERATE: NORMAL CONDITION.**")
        st.markdown("*Cuaca memenuhi standar. Silakan lanjutkan operasi sesuai prosedur.*")

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)


# ==========================================
# FASE 1: PRE-ARRIVAL & 3 SKENARIO
# ==========================================
with tab_h1:
    st.markdown("### 🧮 1. Parameter Kargo & Sinkronisasi Waktu")
    
    c1, c2, c3 = st.columns(3)
    with c1: 
        cargo_vol = st.number_input("Cargo to Load (m³)", min_value=10000.0, value=st.session_state.get("cargo_vol_input", 130000.0), step=1000.0, key="cargo_vol_input")
        safe_filling_limit = st.number_input("Safe Filling Limit (m³)", min_value=100000.0, value=st.session_state.get("safe_filling_limit_input", 122500.0), step=500.0, key="safe_filling_limit_input", help="Batas maksimal volume aman tangki FSRU")
    with c2: 
        rob_awal = st.number_input("ROB H-1 00:00 (m³)", min_value=0.0, value=st.session_state.get("rob_awal_input", 42000.0), step=500.0, key="rob_awal_input")
    with c3: 
        serapan_harian_target = st.number_input("Target Serapan PLN/Day (m³)", min_value=1000.0, value=st.session_state.get("serapan_harian_target_input", 17000.0), step=500.0, key="serapan_harian_target_input")
        serapan_per_jam_aktual = serapan_harian_target / 24.0
        st.markdown(f"<div style='text-align:right; font-size:13px; color:#38bdf8; margin-top:-15px; font-weight:600;'>💡 Aktual: {serapan_per_jam_aktual:,.2f} m³/h</div>", unsafe_allow_html=True)
    
    cw1, cw2 = st.columns(2)
    with cw1:
        st.caption("Record ROB")
        rd1, rt1 = st.columns(2)
        tgl_rob = rd1.date_input("Tanggal ROB", value=st.session_state.get("tgl_rob_input", datetime(2026, 6, 9).date()), key="tgl_rob_input")
        jam_rob = rt1.time_input("Jam ROB", value=st.session_state.get("jam_rob_input", datetime.strptime("00:00", "%H:%M").time()), key="jam_rob_input")
        waktu_rob = datetime.combine(tgl_rob, jam_rob)
    with cw2:
        st.caption("ETA Kapal")
        rd2, rt2 = st.columns(2)
        tgl_eta = rd2.date_input("Tanggal ETA", value=st.session_state.get("tgl_eta_input", datetime(2026, 6, 10).date()), key="tgl_eta_input")
        jam_eta = rt2.time_input("Jam ETA", value=st.session_state.get("jam_eta_input", datetime.strptime("06:00", "%H:%M").time()), key="jam_eta_input")
        waktu_eta = datetime.combine(tgl_eta, jam_eta)

    allowance_prep_mins = (
        st.session_state.durations["ARMs Connected"] + 
        st.session_state.durations["OPEN CTM"] + 
        st.session_state.durations["WARM ESD Test"] + 
        st.session_state.durations["Arm C/D"] + 
        st.session_state.durations["COLD ESD Test"] + 
        st.session_state.durations["START DISCHARGING"] + 
        st.session_state.durations["FULL RATE"]
    )
    allowance_closing_mins = (
        st.session_state.durations["DISCHARGING COMPLETED"] + 
        st.session_state.durations["CLOSING CTM"] + 
        st.session_state.durations["ARMs Disconnected"]
    )
    total_allowance_hours = (allowance_prep_mins + allowance_closing_mins) / 60.0

    st.markdown("---")
    st.markdown("### ⚙️ 2. Evaluasi Laytime & Kebutuhan Regasifikasi")
    
    col_lt1, col_lt2, col_lt3 = st.columns(3)
    
    with col_lt1:
        laytime_kontrak = st.number_input("Batas Laytime Kontrak (Jam)", min_value=1.0, value=st.session_state.get("laytime_kontrak_input", 42.0), step=0.5, key="laytime_kontrak_input", help="Max Time dari NOR s.d Disconnect")
        input_loading_rate = st.number_input("Rencana Loading Rate Aktual (m³/h)", min_value=100.0, value=st.session_state.get("input_loading_rate_input", 3700.0), step=100.0, key="input_loading_rate_input")
        max_loading_rate = st.number_input("Batas Atas Loading Rate (m³/h)", min_value=100.0, value=st.session_state.get("max_loading_rate_input", 4000.0), step=100.0, key="max_loading_rate_input", help="Maksimal kecepatan pompa LNGC/FSRU")
        
        waktu_commence = waktu_eta + timedelta(hours=8)
        selisih_jam_rob = (waktu_commence - waktu_rob).total_seconds() / 3600.0
        serapan_matematis = serapan_per_jam_aktual * selisih_jam_rob
        worst_case_default = float(int(serapan_matematis / 1000) * 1000)
        
        worst_case_serapan_input = st.number_input("Serapan s.d Commence (Worst Case) m³", value=worst_case_default, step=500.0)

    # ==========================================
    # KALKULASI 3 SKENARIO 
    # ==========================================
    # 1. Skenario Batas Bawah (Paling Lambat)
    max_pumping_hours = laytime_kontrak - total_allowance_hours
    min_loading_rate = cargo_vol / max_pumping_hours if max_pumping_hours > 0 else 0
    
    # 2. Skenario Aktual
    actual_pumping_hours = cargo_vol / input_loading_rate if input_loading_rate > 0 else 0
    actual_laytime = actual_pumping_hours + total_allowance_hours
    
    # 3. Skenario Batas Atas (Paling Cepat)
    min_pumping_hours = cargo_vol / max_loading_rate if max_loading_rate > 0 else 0
    min_laytime = min_pumping_hours + total_allowance_hours
    
    # Kalkulasi Jam Selesai Discharge
    t_start_pumping = waktu_eta + timedelta(hours=8) + timedelta(hours=allowance_prep_mins/60.0)
    t_comp_bawah = t_start_pumping + timedelta(hours=max_pumping_hours)
    t_comp_aktual = t_start_pumping + timedelta(hours=actual_pumping_hours)
    t_comp_atas = t_start_pumping + timedelta(hours=min_pumping_hours)

    # Sinkronisasi parameter ke sistem ESOD (Menggunakan Skenario Aktual)
    rob_commence = rob_awal - worst_case_serapan_input
    volume_disrub = (rob_commence + cargo_vol) - safe_filling_limit
    st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = int(actual_pumping_hours * 60)

    with col_lt2:
        st.metric("Total Waktu Allowance", f"{total_allowance_hours:.1f} Jam", "Potongan Persiapan & Closing", delta_color="inverse")
        st.metric("ROB Saat Commence", f"{rob_commence:,.0f} m³", f"Jeda Tunggu: {selisih_jam_rob:.1f} Jam", delta_color="off")

    with col_lt3:
        if volume_disrub > 0:
            regas_harian_dibutuhkan = (volume_disrub / actual_pumping_hours) * 24
            regas_per_jam_dibutuhkan = volume_disrub / actual_pumping_hours
            
            st.metric("VL (Wajib Serap Darat)", f"{volume_disrub:,.0f} m³", "Overfill Risk!", delta_color="inverse")
            
            if regas_harian_dibutuhkan > serapan_harian_target:
                st.error(f"🚨 **BAHAYA TRIP!** Melebihi kapasitas {serapan_harian_target:,.0f} m³/day.")
            else:
                st.success(f"✅ **AMAN.** Kapasitas serapan masih mumpuni.")
                
            st.markdown(f"""
            <div style='background:rgba(15,23,42,0.6); border-left:4px solid #f59e0b; padding:10px; border-radius:5px;'>
                <div style='font-size:12px; color:#94a3b8;'>Kebutuhan Serapan (Aktual):</div>
                <div style='font-size:18px; font-weight:bold; color:#f59e0b;'>{regas_harian_dibutuhkan:,.0f} m³ / Day</div>
                <div style='font-size:16px; font-weight:600; color:#fbbf24;'>{regas_per_jam_dibutuhkan:,.0f} m³ / Hour</div>
            </div>
            """, unsafe_allow_html=True)
            
        else:
            st.metric("VL (Wajib Serap Darat)", "0 m³", "Safe Tank", delta_color="normal")
            st.success("✅ Kapasitas tangki aman menampung seluruh kargo.")
            st.markdown(f"""
            <div style='background:rgba(15,23,42,0.6); border-left:4px solid #10b981; padding:10px; border-radius:5px;'>
                <div style='font-size:12px; color:#94a3b8;'>Kebutuhan Serapan (Aktual):</div>
                <div style='font-size:18px; font-weight:bold; color:#10b981;'>0 m³ / Day</div>
                <div style='font-size:16px; font-weight:600; color:#34d399;'>0 m³ / Hour</div>
            </div>
            """, unsafe_allow_html=True)

    st.write("")
    st.markdown("#### 📊 Hasil Proyeksi 3 Skenario Laytime & Loading Rate")
    st.caption("Skenario Aktual, Batas Bawah (Max Laytime), dan Batas Atas (Max Rate) untuk acuan operasional.")
    
    sc_c1, sc_c2, sc_c3 = st.columns(3)
    with sc_c1:
        st.markdown(f"""
        <div style='background:rgba(239, 68, 68, 0.1); border-left:4px solid #ef4444; padding:15px; border-radius:8px;'>
            <div style='font-size:14px; font-weight:bold; color:#ef4444;'>📉 BATAS BAWAH (Paling Lambat)</div>
            <div style='margin-top:10px; font-size:12px; color:#94a3b8;'>Loading Rate Minimum:</div>
            <div style='font-size:22px; font-weight:bold; color:#f8fafc;'>{min_loading_rate:,.0f} m³/h</div>
            <div style='margin-top:5px; font-size:12px; color:#94a3b8;'>Estimasi Laytime Terpakai:</div>
            <div style='font-size:20px; font-weight:bold; color:#f8fafc;'>{laytime_kontrak:.1f} Jam (Mentok)</div>
            <div style='margin-top:15px; border-top:1px solid rgba(239, 68, 68, 0.3); padding-top:10px;'>
                <div style='font-size:11px; color:#94a3b8;'>Jam Selesai Discharge (Pompa Mati):</div>
                <div style='font-size:14px; font-weight:bold; color:#f8fafc;'>{t_comp_bawah.strftime('%d %b %Y - %H:%M LCT')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with sc_c2:
        st.markdown(f"""
        <div style='background:rgba(16, 185, 129, 0.1); border-left:4px solid #10b981; padding:15px; border-radius:8px;'>
            <div style='font-size:14px; font-weight:bold; color:#10b981;'>🎯 AKTUAL (Rencana Operasi)</div>
            <div style='margin-top:10px; font-size:12px; color:#94a3b8;'>Loading Rate Rencana:</div>
            <div style='font-size:22px; font-weight:bold; color:#f8fafc;'>{input_loading_rate:,.0f} m³/h</div>
            <div style='margin-top:5px; font-size:12px; color:#94a3b8;'>Estimasi Laytime Terpakai:</div>
            <div style='font-size:20px; font-weight:bold; color:#f8fafc;'>{actual_laytime:.1f} Jam</div>
            <div style='margin-top:15px; border-top:1px solid rgba(16, 185, 129, 0.3); padding-top:10px;'>
                <div style='font-size:11px; color:#94a3b8;'>Jam Selesai Discharge (Pompa Mati):</div>
                <div style='font-size:14px; font-weight:bold; color:#10b981;'>{t_comp_aktual.strftime('%d %b %Y - %H:%M LCT')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    with sc_c3:
        st.markdown(f"""
        <div style='background:rgba(56, 189, 248, 0.1); border-left:4px solid #38bdf8; padding:15px; border-radius:8px;'>
            <div style='font-size:14px; font-weight:bold; color:#38bdf8;'>📈 BATAS ATAS (Paling Cepat)</div>
            <div style='margin-top:10px; font-size:12px; color:#94a3b8;'>Loading Rate Maksimal:</div>
            <div style='font-size:22px; font-weight:bold; color:#f8fafc;'>{max_loading_rate:,.0f} m³/h</div>
            <div style='margin-top:5px; font-size:12px; color:#94a3b8;'>Estimasi Laytime Terpakai:</div>
            <div style='font-size:20px; font-weight:bold; color:#f8fafc;'>{min_laytime:.1f} Jam</div>
            <div style='margin-top:15px; border-top:1px solid rgba(56, 189, 248, 0.3); padding-top:10px;'>
                <div style='font-size:11px; color:#94a3b8;'>Jam Selesai Discharge (Pompa Mati):</div>
                <div style='font-size:14px; font-weight:bold; color:#f8fafc;'>{t_comp_atas.strftime('%d %b %Y - %H:%M LCT')}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with st.expander("📊 Lihat Tabel Detail 3 Skenario (Metode Pak Suci)", expanded=False):
        def build_sc(c_sc, l_sc_terpakai, t_comp_exact):
            t_start = waktu_eta + timedelta(hours=8)
            t_out = t_start + timedelta(hours=l_sc_terpakai)
            return [waktu_eta.strftime("%d %b / %H:%M"), t_start.strftime("%d %b / %H:%M"), f"{c_sc:,.0f}", f"{l_sc_terpakai:.1f}", t_comp_exact.strftime("%d %b / %H:%M"), t_out.strftime("%d %b / %H:%M")]
        
        st.dataframe(pd.DataFrame({
            "Parameter": ["POB (ETA)", "Est. Start Discharge", "Cargo to Load", "Estimasi Laytime (H)", "Est. Complete Pumping", "Est. Disconnect (End Laytime)"],
            "1st Est (Aktual)": build_sc(cargo_vol, actual_laytime, t_comp_aktual),
            "2nd Est (Bawah/Max Time)": build_sc(cargo_vol, laytime_kontrak, t_comp_bawah),
            "3rd Est (Atas/Max Rate)": build_sc(cargo_vol, min_laytime, t_comp_atas)
        }), use_container_width=True, hide_index=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# PROYEKSI WAKTU ESOD (GLOBAL LIST)
# ==========================================
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
    st.info(f"📸 **PENGINGAT (Terkait Open CTM):** Snapshot Radar wajib diambil pada pukul **{waktu_snapshot.strftime('%H:%M')} LCT** (Tepat 5 menit sebelum *Arm Cooldown* dimulai).")
    
    st.markdown("### 📅 Live ESOD Timeline")
    
    display_tahapan = []
    for ev in events_list:
        if ev == "NOR Received":
            display_tahapan.append("🟢 NOR Received (START LAYTIME)")
        elif ev == "ARMs Disconnected":
            display_tahapan.append("🛑 ARMs Disconnected (END LAYTIME)")
        else:
            display_tahapan.append(ev)
            
    df_esod = pd.DataFrame({
        "Tahapan": display_tahapan, 
        "Waktu (LCT)": esod_times, 
        "Durasi (Min)": [0] + [st.session_state.durations[e] for e in events_list[1:]]
    })
    
    def color_laytime(row):
        if "START LAYTIME" in row['Tahapan']:
            return ['background-color: rgba(16, 185, 129, 0.2); color: #10b981; font-weight: 800'] * len(row)
        elif "END LAYTIME" in row['Tahapan']:
            return ['background-color: rgba(239, 68, 68, 0.2); color: #ef4444; font-weight: 800'] * len(row)
        else:
            return [''] * len(row)
            
    styled_esod = df_esod.style.apply(color_laytime, axis=1)

    ed_table = st.data_editor(styled_esod, column_config={"Tahapan": st.column_config.TextColumn(disabled=True)}, use_container_width=True, hide_index=True, key="esod_ed", on_change=update_esod)
        
    try:
        start_laytime_idx = events_list.index("NOR Received")
        end_laytime_idx = events_list.index("ARMs Disconnected")
        start_dt = esod_times[start_laytime_idx]
        end_dt = esod_times[end_laytime_idx]
        laytime_duration = (end_dt - start_dt).total_seconds() / 3600.0
        
        st.markdown(f"""
        <div style='background:rgba(15,23,42,0.6); border-left:4px solid #38bdf8; padding:15px; border-radius:8px; margin-top: 15px;'>
            <div style='font-size:13px; color:#94a3b8;'>⏱️ Total Waktu Laytime (Sesuai ESOD Aktual):</div>
            <div style='font-size:20px; font-weight:bold; color:#38bdf8;'>{laytime_duration:.1f} Jam</div>
            <div style='font-size:12px; color:#64748b; margin-top:5px;'>Mulai: {start_dt.strftime('%d %b %Y %H:%M LCT')} &nbsp; | &nbsp; Selesai: {end_dt.strftime('%d %b %Y %H:%M LCT')}</div>
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        pass
        
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 3: MONITORING
# ==========================================
with tab_monitor:
    st.markdown(f"**Jadwal Eksekusi Snapshot Radar (Pre-Cooling):** {waktu_snapshot.strftime('%H:%M')} LCT")
    
    st.markdown("### ⏲️ Input Waktu Pemantauan Terkini")
    col_tnow1, col_tnow2 = st.columns(2)
    with col_tnow1:
        tgl_laporan = st.date_input("Tanggal Pencatatan", value=st.session_state.get("tgl_laporan_input", datetime.now().date()), key="tgl_laporan_input")
    with col_tnow2:
        jam_laporan = st.time_input("Jam Pencatatan Terkini", value=st.session_state.get("jam_laporan_input", datetime.now().time()), key="jam_laporan_input")
        
    waktu_sekarang = datetime.combine(tgl_laporan, jam_laporan)
    
    st.markdown("---")
    mt1, mt2 = st.columns(2)
    togo_vol = mt1.number_input("Volume LNG To Go (m³)", value=st.session_state.get("togo_vol_input", float(cargo_vol)), step=1000.0, key="togo_vol_input")
    togo_rate = mt1.number_input("Actual Loading Rate (m³/h)", value=st.session_state.get("togo_rate_input", float(input_loading_rate)), step=100.0, key="togo_rate_input")
    
    sisa_h = togo_vol / togo_rate if togo_rate > 0 else 0
    
    mt2.metric("Sisa Waktu Pemompaan", f"{sisa_h:.1f} Jam")
    estimasi_selesai_monitoring = waktu_sekarang + timedelta(hours=sisa_h)
    mt2.metric("Estimasi Selesai Pemompaan", estimasi_selesai_monitoring.strftime("%d %b %Y - %H:%M LCT"))
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 4: ROB PROJECTION
# ==========================================
with tab_rob:
    st.markdown("### 📈 Proyeksi Level Tangki FSRU (Hourly ROB)")
    st.caption("Simulasi pergerakan muatan tangki FSRU dari awal Start Discharging hingga selesai, diproyeksikan setiap jam.")
    
    idx_start_pompa = events_list.index("START DISCHARGING")
    waktu_start_pompa = esod_times[idx_start_pompa]
    
    jeda_dari_commence_ke_pompa = (waktu_start_pompa - (waktu_eta + timedelta(hours=8))).total_seconds() / 3600.0
    rob_saat_pompa_nyala = rob_commence - (serapan_per_jam_aktual * jeda_dari_commence_ke_pompa)
    
    proj_data = []
    current_waktu = waktu_start_pompa
    current_rob = rob_saat_pompa_nyala
    kargo_masuk_kumulatif = 0
    
    proj_data.append({
        "Jam ke-": 0.0,
        "Waktu (LCT)": current_waktu.strftime("%d %b %H:%M"),
        "Cargo In (m³)": 0.0,
        "Serapan Out (m³)": 0.0,
        "FSRU ROB (m³)": current_rob
    })
    
    jam_bulat = int(actual_pumping_hours)
    sisa_desimal = actual_pumping_hours - jam_bulat
    
    if jam_bulat > 150:
        st.warning("⚠️ Rencana Loading Rate sangat kecil. Grafik dibatasi maksimum 150 jam (6 hari) untuk mencegah *lag/crash* sistem.")
        jam_bulat = 150
        sisa_desimal = 0
        
    for i in range(1, jam_bulat + 1):
        current_waktu += timedelta(hours=1)
        kargo_masuk_kumulatif += input_loading_rate
        current_rob = current_rob + input_loading_rate - serapan_per_jam_aktual
        
        proj_data.append({
            "Jam ke-": float(i),
            "Waktu (LCT)": current_waktu.strftime("%d %b %H:%M"),
            "Cargo In (m³)": kargo_masuk_kumulatif,
            "Serapan Out (m³)": serapan_per_jam_aktual * i,
            "FSRU ROB (m³)": current_rob
        })
        
    if sisa_desimal > 0:
        current_waktu += timedelta(hours=sisa_desimal)
        kargo_in_sisa = input_loading_rate * sisa_desimal
        serapan_out_sisa = serapan_per_jam_aktual * sisa_desimal
        
        kargo_masuk_kumulatif += kargo_in_sisa
        current_rob = current_rob + kargo_in_sisa - serapan_out_sisa
        
        proj_data.append({
            "Jam ke-": float(round(actual_pumping_hours, 1)),
            "Waktu (LCT)": current_waktu.strftime("%d %b %H:%M"),
            "Cargo In (m³)": kargo_masuk_kumulatif,
            "Serapan Out (m³)": serapan_per_jam_aktual * actual_pumping_hours,
            "FSRU ROB (m³)": current_rob
        })
        
    df_proj = pd.DataFrame(proj_data)
    
    def highlight_overfill_col(col):
        return [f'background-color: rgba(239, 68, 68, 0.4); color: white; font-weight:bold' if v > safe_filling_limit else '' for v in col]

    styled_df_proj = df_proj.style.apply(highlight_overfill_col, subset=['FSRU ROB (m³)']).format({
        "Jam ke-": "{:.1f}",
        "Cargo In (m³)": "{:,.0f}", 
        "Serapan Out (m³)": "{:,.0f}", 
        "FSRU ROB (m³)": "{:,.0f}"
    })
    
    st.dataframe(styled_df_proj, use_container_width=True, hide_index=True)
                 
    st.markdown("### 📊 Grafik Pergerakan ROB")
    chart_data = df_proj.set_index("Waktu (LCT)")["FSRU ROB (m³)"]
    st.line_chart(chart_data, color="#10b981")
    
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 5: FINAL REPORT & AUTO RECAP
# ==========================================
with tab_closing:
    st.markdown("### 📐 Validasi Hak Milik & Energy Delivered")
    f1, f2, f3 = st.columns(3)
    
    v_open_default = float(cargo_vol + 5000)
    v_open = f1.number_input("CTMS Opening Register (m³)", value=v_open_default, step=10.0)
    v_close = f1.number_input("CTMS Closing Register (m³)", value=st.session_state.get("v_close_input", 5000.0), step=10.0, key="v_close_input")
    v_act = v_open - v_close
    
    dens = f2.number_input("Density LNG (kg/m³)", value=st.session_state.get("dens_input", 450.0), step=0.1, key="dens_input")
    mghv = f2.number_input("Mass GHV (MJ/kg)", value=st.session_state.get("mghv_input", 54.5), step=0.01, key="mghv_input")
    vghv = f2.number_input("Vapor GHV (MJ/m³)", value=st.session_state.get("vghv_input", 35.676), step=0.001, key="vghv_input")
    
    vt = f3.number_input("Vapor Temp (°C)", value=st.session_state.get("vt_input", -130.0), step=0.5, key="vt_input")
    vp = f3.number_input("Vapor Press (mbar)", value=st.session_state.get("vp_input", 1013.0), step=1.0, key="vp_input")
    gc = f3.number_input("Gas Consumed (MMBtu)", value=st.session_state.get("gc_input", 1500.0), step=1.0, key="gc_input")

    suhu_kelvin_bawah = 273.15 + vt
    if suhu_kelvin_bawah != 0:
        qr = v_act * (288.15 / suhu_kelvin_bawah) * (vp / 1013.25) * vghv
    else:
        qr = 0.0
        
    qty_gross = ((v_act * dens * mghv) - qr) / 1055.12
    qty_net = qty_gross - gc

    st.divider()
    rf1, rf2, rf3 = st.columns(3)
    rf1.metric("Vapor Return (Qr)", f"{qr:,.0f} MJ")
    rf2.metric("Gross Energy", f"{qty_gross:,.0f} MMBtu")
    rf3.metric("NET ENERGY DELIVERED", f"{qty_net:,.0f} MMBtu")
    
    st.markdown("---")
    st.markdown("### 🗄️ Auto Recap Database")
    st.caption("Klik tombol di bawah ini untuk menyimpan seluruh data operasi saat ini ke dalam Master Spreadsheet (Database).")
    
    col_rcp1, col_rcp2 = st.columns([1, 2])
    
    with col_rcp1:
        if st.button("💾 SIMPAN DATA KE DATABASE REKAP", use_container_width=True):
            recap_dict = {
                "Timestamp Input": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "CTO On Duty": st.session_state["user_name"],
                "ETA Kedatangan": waktu_eta.strftime("%Y-%m-%d %H:%M"),
                "Volume Cargo (m³)": cargo_vol,
                "Loading Rate (m³/h)": input_loading_rate,
                "Laytime Kontrak (Jam)": laytime_kontrak,
                "Actual Laytime (Jam)": actual_laytime,
                "Volume Dibongkar (m³)": v_act,
                "Vapor Return (MJ)": qr,
                "Gross Energy (MMBtu)": qty_gross,
                "Net Energy Delivered (MMBtu)": qty_net
            }
            
            df_recap = pd.DataFrame([recap_dict])
            file_path = "recap_cto_database.csv"
            
            if os.path.exists(file_path):
                df_recap.to_csv(file_path, mode='a', header=False, index=False)
            else:
                df_recap.to_csv(file_path, index=False)
                
            st.toast("✅ Data operasi berhasil direkap ke database utama!")
            st.success("Tersimpan ke file recap_cto_database.csv")

    with col_rcp2:
        if os.path.exists("recap_cto_database.csv"):
            with open("recap_cto_database.csv", "rb") as f:
                st.download_button("📥 UNDUH MASTER SPREADSHEET REKAP", data=f, file_name="Master_Rekap_CTO_Ops.csv", mime="text/csv", use_container_width=True)
        else:
            st.info("Belum ada riwayat rekap data yang tersimpan.")

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.caption("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>© 2026 PT Nusantara Regas - FSRU NR Command Center Workspace</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)
