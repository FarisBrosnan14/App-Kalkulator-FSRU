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

# Library untuk pemrosesan gambar flowchart
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    st.error("Library 'Pillow' belum terinstall. Silakan ketik 'pip install Pillow' di terminal agar fitur flowchart bisa digunakan.")

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
# 3. FUNGSI PENGAMBIL DATA CUACA
# ==========================================
WEATHER_CACHE_FILE = "weather_cache.json"

@st.cache_data(ttl=900)
def get_live_weather():
    lat, lon = -5.98, 106.83
    head = {"User-Agent": "CTO-Ops/1.0"}
    offline_mode = False
    
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
        
        try:
            url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height"
            res_m = requests.get(url_marine, headers=head, timeout=2).json()
            wave = res_m["current"]["wave_height"]
            if wave is None: wave = 0.5
        except:
            wave = 0.5
            
        with open(WEATHER_CACHE_FILE, "w") as f:
            json.dump({"temp": temp, "wind": wind, "wave": wave, "cond": cond, "icon": icon}, f)
            
    except Exception:
        offline_mode = True
        if os.path.exists(WEATHER_CACHE_FILE):
            try:
                with open(WEATHER_CACHE_FILE, "r") as f:
                    cached = json.load(f)
                temp, wind, wave, cond, icon = cached["temp"], cached["wind"], cached["wave"], cached["cond"], cached["icon"]
            except:
                temp, wind, wave, cond, icon = 31.3, 14.3, 0.5, "Offline", "📡"
        else:
            temp, wind, wave, cond, icon = 31.3, 14.3, 0.5, "Offline", "📡"
            
    return temp, wind, wave, cond, icon, offline_mode

live_temp, live_wind, live_wave, live_cond, live_icon, is_offline = get_live_weather()
live_wind_knots = live_wind * 0.539957

# ==========================================
# 4. INISIALISASI SESSION AUTO-LOAD RESPONSIF
# ==========================================
def init_ss(key, default):
    if key not in st.session_state:
        st.session_state[key] = default

events_list = [
    "ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", 
    "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", 
    "FULL RATE", "RATE DOWN", "DISCHARGING COMPLETED", "CLOSING CTM", 
    "ARMs Disconnected", "Documentation", "POB OUT", "Commence Unmooring", "All Line Clear"
]

default_durations = {
    "All Fast": 270, "NOR Received": 70, "ARMs Connected": 10, "OPEN CTM": 35, 
    "WARM ESD Test": 15, "Arm C/D": 90, "COLD ESD Test": 15, "START DISCHARGING": 20, 
    "FULL RATE": 30, "RATE DOWN": 1754, "DISCHARGING COMPLETED": 30, "CLOSING CTM": 120, 
    "ARMs Disconnected": 10, "Documentation": 60, "POB OUT": 120, "Commence Unmooring": 34, "All Line Clear": 11
}

if "app_initialized" not in st.session_state:
    if os.path.exists("ops_kondisi_terakhir.pkl"):
        try:
            with open("ops_kondisi_terakhir.pkl", "rb") as f:
                loaded_state = pickle.load(f)
            for k, v in loaded_state.items():
                st.session_state[k] = v
        except Exception:
            pass
    st.session_state["app_initialized"] = True

init_ss("durations", default_durations)

for ev in events_list[1:]:
    if ev not in st.session_state.durations:
        st.session_state.durations[ev] = default_durations[ev]

checklist_keys = [
    "td_d1_1", "td_d1_2", "td_d1_3", "td_d1_4", "td_d1_5", "td_d1_6", "td_d1_7", "td_d1_8", "td_d1_9", "td_d1_10", "td_d1_11",
    "td_d2_1", "td_d2_2", "td_d2_3", "td_d2_4", "td_d2_5", "td_d2_6", "td_d2_7",
    "td_d3_1", "td_d3_2", "td_d3_3", "td_d3_4",
    "td_d4_1", "td_d4_2", "td_d4_3", "td_d4_4", "td_d4_5", "td_d4_6"
]
for key in checklist_keys: init_ss(key, False)

init_ss("checklist_unlocked", False)
init_ss("inp_wind_input", float(live_wind_knots))
init_ss("inp_gust_input", float(live_wind_knots * 1.2))
init_ss("inp_sea_input", float(live_wave))
init_ss("inp_vis_input", 5.0)
init_ss("inp_lightning_input", False)
init_ss("vessel_name_input", "Danaputri 1")
init_ss("cargo_vol_input", 130000.0)
init_ss("safe_filling_limit_input", 122500.0)
init_ss("rob_awal_input", 42000.0)
init_ss("rob_akhir_input", 124846.0) 
init_ss("serapan_harian_target_input", 17000.0)
init_ss("tgl_rob_input", datetime(2026, 6, 9).date())
init_ss("jam_rob_input", datetime.strptime("00:00", "%H:%M").time())
init_ss("tgl_eta_input", datetime(2026, 6, 10).date())
init_ss("jam_eta_input", datetime.strptime("09:45", "%H:%M").time())
init_ss("laytime_kontrak_input", 42.0)
init_ss("max_loading_rate_input", 4000.0)
init_ss("input_loading_rate_input", 4300.0)
init_ss("cargo_no_input", "LJ08")
init_ss("cargo_origin_input", "Tangguh")
init_ss("pilot_name_input", "Capt. Medi")
init_ss("tugboat_info_input", "3 tugboats with normal operation Berthing (TB Aqua harbour, TB Medelin Citra & TB. Patra Tunda 4201)")
init_ss("arm_info_input", "3 Arm Loading : L/A no 1 & 3 for Liquid, L/A no.2 for Vapor.")
init_ss("tgl_laporan_input", datetime.now().date())
init_ss("jam_laporan_input", datetime.now().time())
init_ss("togo_vol_input", 130000.0)
init_ss("togo_rate_input", 4300.0)
init_ss("v_open_input", 135000.0)
init_ss("v_close_input", 5000.0)
init_ss("dens_input", 450.0)
init_ss("mghv_input", 54.5)
init_ss("vghv_input", 35.676)
init_ss("vt_input", -130.0)
init_ss("vp_input", 1013.0)
init_ss("gc_input", 1500.0)
init_ss("qo_time", datetime.now().time())
init_ss("qo_rob", 42000.0)
init_ss("qo_cargo", 130000.0)
init_ss("qo_rate", 3700.0)
init_ss("qo_safe", 122500.0)
init_ss("cargo_seq_input", "19th")

# ==========================================
# 5. GLOBAL CALCULATION ENGINE (ANTI-ERROR SCOPING)
# ==========================================
# Mesin ini menghitung semua waktu sebelum tab di render, mencegah NameError.

waktu_eta = datetime.combine(st.session_state["tgl_eta_input"], st.session_state["jam_eta_input"])
waktu_rob = datetime.combine(st.session_state["tgl_rob_input"], st.session_state["jam_rob_input"])

# Kalkulasi Allowance
allowance_prep_mins = (
    max(0, st.session_state.durations["ARMs Connected"]) + max(0, st.session_state.durations["OPEN CTM"]) + 
    max(0, st.session_state.durations["WARM ESD Test"]) + max(0, st.session_state.durations["Arm C/D"]) + 
    max(0, st.session_state.durations["COLD ESD Test"]) + max(0, st.session_state.durations["START DISCHARGING"])
)
allowance_closing_mins = max(0, st.session_state.durations["CLOSING CTM"]) + max(0, st.session_state.durations["ARMs Disconnected"])
total_allowance_hours = (allowance_prep_mins + allowance_closing_mins) / 60.0

actual_pumping_mins = (st.session_state["cargo_vol_input"] / st.session_state["input_loading_rate_input"]) * 60 if st.session_state["input_loading_rate_input"] > 0 else 0

# Auto-Adjust Rate Down
if "prev_rate_for_esod" not in st.session_state:
    st.session_state.prev_rate_for_esod = st.session_state["input_loading_rate_input"]
    st.session_state.prev_vol_for_esod = st.session_state["cargo_vol_input"]
    st.session_state.durations["RATE DOWN"] = int(actual_pumping_mins) - max(0, st.session_state.durations["FULL RATE"]) - max(0, st.session_state.durations["DISCHARGING COMPLETED"])

if (st.session_state.prev_rate_for_esod != st.session_state["input_loading_rate_input"] or 
    st.session_state.prev_vol_for_esod != st.session_state["cargo_vol_input"]):
    st.session_state.durations["RATE DOWN"] = int(actual_pumping_mins) - max(0, st.session_state.durations["FULL RATE"]) - max(0, st.session_state.durations["DISCHARGING COMPLETED"])
    st.session_state.prev_rate_for_esod = st.session_state["input_loading_rate_input"]
    st.session_state.prev_vol_for_esod = st.session_state["cargo_vol_input"]

# Kalkulasi Waktu ESOD
temp_dt = waktu_eta
esod_times_actual = [temp_dt]
for ev in events_list[1:]:
    temp_dt += timedelta(minutes=st.session_state.durations[ev])
    esod_times_actual.append(temp_dt)

# Ekstraksi Variabel Waktu
t_eta = esod_times_actual[events_list.index("ETA / POB")]
t_allfast = esod_times_actual[events_list.index("All Fast")]
t_nor_recv = esod_times_actual[events_list.index("NOR Received")]
t_arm_conn = esod_times_actual[events_list.index("ARMs Connected")]
t_open_ctm = esod_times_actual[events_list.index("OPEN CTM")]
t_start_disc = esod_times_actual[events_list.index("START DISCHARGING")]
t_full_rate = esod_times_actual[events_list.index("FULL RATE")]
t_rate_down = esod_times_actual[events_list.index("RATE DOWN")]
t_comp = esod_times_actual[events_list.index("DISCHARGING COMPLETED")]
t_close_ctm = esod_times_actual[events_list.index("CLOSING CTM")]
t_disc = esod_times_actual[events_list.index("ARMs Disconnected")]
t_doc = esod_times_actual[events_list.index("Documentation")]
t_pob_out = esod_times_actual[events_list.index("POB OUT")]
t_commence_unmooring = esod_times_actual[events_list.index("Commence Unmooring")]
t_all_line_clear = esod_times_actual[events_list.index("All Line Clear")]

t_eosp = t_eta - timedelta(minutes=45)
t_nor_tend = t_eta
t_first_line = t_allfast - timedelta(minutes=85)
waktu_snapshot = t_arm_conn - timedelta(minutes=5)

# Kalkulasi Skenario Batas Laytime & Rate
max_pumping_hours = st.session_state["laytime_kontrak_input"] - total_allowance_hours
min_loading_rate = st.session_state["cargo_vol_input"] / max_pumping_hours if max_pumping_hours > 0 else 0

actual_laytime = (actual_pumping_mins / 60.0) + total_allowance_hours
min_pumping_mins = (st.session_state["cargo_vol_input"] / st.session_state["max_loading_rate_input"]) * 60 if st.session_state["max_loading_rate_input"] > 0 else 0
min_laytime = (min_pumping_mins / 60.0) + total_allowance_hours

esod_start_aktual = t_start_disc
esod_comp_aktual = t_comp
esod_disc_aktual = t_disc

delta_mins_bawah = (max_pumping_hours * 60) - actual_pumping_mins
esod_start_bawah = esod_start_aktual
esod_comp_bawah = esod_comp_aktual + timedelta(minutes=delta_mins_bawah)
esod_disc_bawah = esod_disc_aktual + timedelta(minutes=delta_mins_bawah)

delta_mins_atas = min_pumping_mins - actual_pumping_mins
esod_start_atas = esod_start_aktual
esod_comp_atas = esod_comp_aktual + timedelta(minutes=delta_mins_atas)
esod_disc_atas = esod_disc_aktual + timedelta(minutes=delta_mins_atas)

# Kalkulasi ROB & Serapan
waktu_commence = t_eta + timedelta(hours=8)
selisih_jam_rob = (waktu_commence - waktu_rob).total_seconds() / 3600.0
serapan_per_jam_aktual = st.session_state["serapan_harian_target_input"] / 24.0
serapan_matematis = serapan_per_jam_aktual * selisih_jam_rob
worst_case_default = float(int(serapan_matematis / 1000) * 1000)

if "worst_case_serapan_input_x" not in st.session_state:
    st.session_state["worst_case_serapan_input_x"] = worst_case_default

rob_commence = st.session_state["rob_awal_input"] - st.session_state["worst_case_serapan_input_x"]
volume_disrub = (rob_commence + st.session_state["cargo_vol_input"]) - st.session_state["safe_filling_limit_input"]

# Kalkulasi Durasi Jam untuk Final Report
dur_pob_first = (t_first_line - t_eta).total_seconds() / 3600.0
dur_pob_all = (t_allfast - t_eta).total_seconds() / 3600.0
dur_start_comp = (t_comp - t_start_disc).total_seconds() / 3600.0
dur_laytime = (t_disc - t_nor_recv).total_seconds() / 3600.0
dur_all_disc = (t_disc - t_allfast).total_seconds() / 3600.0

# ==========================================
# 6. SIDEBAR: MANAJEMEN SESI & QUICK OPS CALC
# ==========================================
with st.sidebar:
    st.image(html_logo_src, use_container_width=True)
    
    st.markdown("### ✅ Interactive To-Do Ops")
    
    if not st.session_state["checklist_unlocked"]:
        st.info("🔒 Akses checklist operasional dikunci.")
        pwd = st.text_input("Sandi Akses:", type="password", key="chk_pwd")
        if st.button("Buka Akses"):
            if pwd == "CTO2026":
                st.session_state["checklist_unlocked"] = True
                st.rerun()
            else:
                st.error("Sandi salah!")
    else:
        if st.button("🔒 Kunci Akses Checklist"):
            st.session_state["checklist_unlocked"] = False
            st.rerun()
            
        with st.expander("🗓️ DAY -1 (Pre-Arrival)", expanded=False):
            st.checkbox("WAG Monitoring (Info posisi & cuaca)", value=st.session_state["td_d1_1"], key="td_d1_1")
            st.checkbox("WAG Patroli Laut (Waktu STS)", value=st.session_state["td_d1_2"], key="td_d1_2")
            st.checkbox("Hubungi Dispatcher JCC (Serapan)", value=st.session_state["td_d1_3"], key="td_d1_3")
            st.checkbox("Hubungi PLN & Surveyor (Onboard)", value=st.session_state["td_d1_4"], key="td_d1_4")
            st.checkbox("Konfirmasi Surat Perintah PLN EPI", value=st.session_state["td_d1_5"], key="td_d1_5")
            st.markdown("---")
            st.checkbox("Draft Loading Plan", value=st.session_state["td_d1_6"], key="td_d1_6")
            st.checkbox("Draft List Personeel & Persyaratan", value=st.session_state["td_d1_7"], key="td_d1_7")
            st.checkbox("Draft Flowchart Estimation", value=st.session_state["td_d1_8"], key="td_d1_8")
            st.checkbox("TTD JoA & CoU (Master NRS)", value=st.session_state["td_d1_9"], key="td_d1_9")
            st.markdown("---")
            st.checkbox("Email Permission Onboard & Boat", value=st.session_state["td_d1_10"], key="td_d1_10")
            st.checkbox("Email JoA, CoU, Loading Plan", value=st.session_state["td_d1_11"], key="td_d1_11")

        with st.expander("🗓️ DAY 1 (Berthing & Start)", expanded=False):
            st.checkbox("Lapor Pos ISPS & Trip ke FSRU", value=st.session_state["td_d2_1"], key="td_d2_1")
            st.checkbox("Monitor STS sampai All Fast", value=st.session_state["td_d2_2"], key="td_d2_2")
            st.checkbox("Pelaksanaan Pre-cargo Meeting", value=st.session_state["td_d2_3"], key="td_d2_3")
            st.checkbox("Snapshot Radar: Open CTM", value=st.session_state["td_d2_4"], key="td_d2_4")
            st.checkbox("Supervisi Warm/Cold ESD & Arm C/D", value=st.session_state["td_d2_5"], key="td_d2_5")
            st.checkbox("Start Discharging s.d Full Rate", value=st.session_state["td_d2_6"], key="td_d2_6")
            st.checkbox("Email Report: Start Discharging", value=st.session_state["td_d2_7"], key="td_d2_7")

        with st.expander("🗓️ DAY 2 (Monitoring)", expanded=False):
            st.checkbox("Update POB Out (Keagenan & ISPS)", value=st.session_state["td_d3_1"], key="td_d3_1")
            st.checkbox("Update perhitungan LNG to go", value=st.session_state["td_d3_2"], key="td_d3_2")
            st.checkbox("Koordinasi Rate Down (Kargo Kritis)", value=st.session_state["td_d3_3"], key="td_d3_3")
            st.checkbox("Persiapan awal Closing CTM", value=st.session_state["td_d3_4"], key="td_d3_4")

        with st.expander("🗓️ DAY 3 (Completed & Out)", expanded=False):
            st.checkbox("Eksekusi Draining & Purging", value=st.session_state["td_d4_1"], key="td_d4_1")
            st.checkbox("Snapshot Radar: Closing CTM", value=st.session_state["td_d4_2"], key="td_d4_2")
            st.checkbox("Proses Arm Disconnect", value=st.session_state["td_d4_3"], key="td_d4_3")
            st.checkbox("TTD Dokumen (Timesheet, Sertifikat)", value=st.session_state["td_d4_4"], key="td_d4_4")
            st.checkbox("POB Out, Unmooring, Trip Pos ISPS", value=st.session_state["td_d4_5"], key="td_d4_5")
            st.checkbox("Email Report Final (Cargo Document)", value=st.session_state["td_d4_6"], key="td_d4_6")

    st.divider()
    
    st.markdown("### 💾 Manajemen Sesi Operasi")
    st.info("🟢 **Auto-Save Cerdas Aktif:** Data tersimpan lokal, tahan putus koneksi internet.")
            
    if st.button("🚪 Logout / Ganti User", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["user_name"] = ""
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
        st.rerun()
            
    st.divider()

    st.markdown("### 🧮 Quick Ops Calc")
    st.caption("Hitung cepat Serapan & Waktu tanpa mengubah data Utama")
    
    with st.expander("⚡ Kalkulator Cepat ROB & Waktu", expanded=True):
        qo_time = st.time_input("Jam Patokan / Start", value=st.session_state["qo_time"], key="qo_time")
        qo_rob = st.number_input("ROB di Jam tsb (m³)", min_value=0.0, value=st.session_state["qo_rob"], step=500.0, key="qo_rob")
        qo_cargo = st.number_input("Cargo In / To Go (m³)", min_value=0.0, value=st.session_state["qo_cargo"], step=1000.0, key="qo_cargo")
        qo_rate = st.number_input("Target Loading Rate (m³/h)", min_value=1.0, value=st.session_state["qo_rate"], step=100.0, key="qo_rate")
        qo_safe = st.number_input("Safe Filling Limit (m³)", min_value=100000.0, value=st.session_state["qo_safe"], step=500.0, key="qo_safe")
        
        st.markdown("---")
        if st.session_state["qo_rate"] > 0:
            qo_durasi = st.session_state["qo_cargo"] / st.session_state["qo_rate"]
            qo_vl = (st.session_state["qo_rob"] + st.session_state["qo_cargo"]) - st.session_state["qo_safe"]
            qo_req_serapan_h = qo_vl / qo_durasi if qo_vl > 0 else 0
            qo_req_serapan_d = qo_req_serapan_h * 24
            
            today = datetime.now().date()
            base_datetime = datetime.combine(today, st.session_state["qo_time"])
            qo_est_selesai = base_datetime + timedelta(hours=qo_durasi)
            
            st.markdown(f"<div style='font-size:13px; color:#94a3b8;'>⏱️ Durasi Pompa Dibutuhkan:</div><div style='font-size:18px; font-weight:bold; color:#38bdf8; margin-bottom:10px;'>{qo_durasi:.1f} Jam</div>", unsafe_allow_html=True)
            
            if qo_vl > 0:
                st.markdown(f"<div style='font-size:13px; color:#94a3b8;'>🔥 Wajib Serap (Mencegah Overfill):</div><div style='font-size:18px; font-weight:bold; color:#f59e0b;'>{qo_req_serapan_h:,.0f} m³/h</div><div style='font-size:14px; color:#fbbf24;'>({qo_req_serapan_d:,.0f} m³/day)</div>", unsafe_allow_html=True)
            else:
                st.markdown(f"<div style='font-size:13px; color:#94a3b8;'>🔥 Wajib Serap:</div><div style='font-size:18px; font-weight:bold; color:#10b981;'>Aman (0 m³/h)</div><div style='font-size:14px; color:#34d399;'>Kapasitas tangki memadai</div>", unsafe_allow_html=True)
            
            st.markdown(f"<div style='margin-top:10px; padding-top:10px; border-top:1px solid #334155; font-size:12px; color:#94a3b8;'>Estimasi Selesai: <strong style='color:#10b981;'>{qo_est_selesai.strftime('%d %b - %H:%M LCT')}</strong></div>", unsafe_allow_html=True)

    with st.expander("🔢 Kalkulator Standar", expanded=False):
        components.html("""
        <style>@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600&display=swap'); body{font-family:'Poppins',sans-serif;background:transparent;margin:0;}.calc{background:rgba(30,41,59,0.5);border-radius:12px;padding:10px;}.disp{width:100%;background:#0f172a;color:#fff;font-size:20px;text-align:right;padding:10px;border-radius:8px;border:1px solid #334155;margin-bottom:10px;box-sizing:border-box;}.btns{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;}button{background:rgba(255,255,255,0.1);color:#fff;border:none;padding:10px;border-radius:5px;cursor:pointer;}.btn-eq{background:#10b981;grid-column:span 2;}.btn-c{background:rgba(239,68,68,0.2);color:#f87171;grid-column:span 2;}</style>
        <div class="calc"><input type="text" class="disp" id="d" disabled><div class="btns"><button class="btn-c" onclick="d.value=''">C</button><button onclick="d.value+='('">(</button><button onclick="d.value+=')')">)</button><button onclick="d.value+='7'">7</button><button onclick="d.value+='8'">8</button><button onclick="d.value+='9'">9</button><button onclick="d.value+='/'">÷</button><button onclick="d.value+='4'">4</button><button onclick="d.value+='5'">5</button><button onclick="d.value+='6'">6</button><button onclick="d.value+='*'">×</button><button onclick="d.value+='1'">1</button><button onclick="d.value+='2'">2</button><button onclick="d.value+='3'">3</button><button onclick="d.value+='-'">-</button><button onclick="d.value+='0'">0</button><button onclick="d.value+='.'">.</button><button class="btn-eq" onclick="d.value=eval(d.value)">=</button><button onclick="d.value+='+'">+</button></div></div>
        """, height=300)

# ==========================================
# 7. HEADER LIVE & INDIKATOR JARINGAN
# ==========================================
user_display = str(st.session_state["user_name"]).upper()

status_jaringan = "🔴 OFFLINE MODE (Data Lokal)" if is_offline else f"🟢 ON DUTY: {user_display}"
warna_jaringan = "linear-gradient(135deg,#ef4444,#b91c1c)" if is_offline else "linear-gradient(135deg,#10b981,#059669)"
border_jaringan = "#f87171" if is_offline else "#34d399"

components.html(f"""
<div style="background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:15px 25px;display:flex;justify-content:space-between;align-items:center;color:white;font-family:'Poppins',sans-serif;">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="background:white;padding:5px 10px;border-radius:10px;"><img src="{html_logo_src}" style="height:30px;"></div>
        <div><div style="font-size:22px;font-weight:800;">CTO TERMINAL OPS</div><div style="color:#06b6d4;font-size:13px;">Nusantara Regas • Live Command Center</div></div>
    </div>
    <div style="background:{warna_jaringan};padding:8px 24px;border-radius:30px;font-weight:600;font-size:14px;border:1px solid {border_jaringan};">{status_jaringan}</div>
</div>
""", height=120)

with st.expander("🛰️ BUKA PANEL LIVE: Jam, Cuaca & Ombak (FSRU NR)", expanded=False):
    if is_offline:
        st.warning("Menampilkan data cuaca simpanan terakhir karena koneksi internet terputus.")
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

def get_date_suffix(day):
    if 11 <= day <= 13: return 'th'
    return {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
def format_email_date(t):
    return f"{t.strftime('%B')} {t.day}{get_date_suffix(t.day)}, {t.year}"
def safe_to_naive(dt):
    parsed = pd.to_datetime(dt)
    if parsed.tzinfo is not None: return parsed.tz_localize(None)
    return parsed

# ==========================================
# FASE 0: WEATHER RESTRICTIONS
# ==========================================
with tab_weather:
    st.markdown("### 🌪️ Evaluasi Cuaca & Keselamatan Operasi")
    st.caption("Berdasarkan NRS Terminal Guide - Evaluasi Go/No-Go operasional kapal.")
    
    cw_1, cw_2, cw_3, cw_4 = st.columns(4)
    with cw_1:
        inp_wind = st.number_input("Wind Speed (Knots)", min_value=0.0, value=st.session_state["inp_wind_input"], step=1.0, key="inp_wind_input")
    with cw_2:
        inp_gust = st.number_input("Wind Gusts (Knots)", min_value=0.0, value=st.session_state["inp_gust_input"], step=1.0, key="inp_gust_input")
    with cw_3:
        inp_sea = st.number_input("Sea / Wave (m)", min_value=0.0, value=st.session_state["inp_sea_input"], step=0.1, key="inp_sea_input")
    with cw_4:
        inp_vis = st.number_input("Visibility (Nm)", min_value=0.0, value=st.session_state["inp_vis_input"], step=0.5, key="inp_vis_input")
        
    inp_lightning = st.checkbox("⚡ Terdapat Petir / Lightning (Radius berbahaya)?", value=st.session_state["inp_lightning_input"], key="inp_lightning_input")
    
    st.markdown("---")
    st.markdown("#### 🚨 Keputusan Operasional (NRS Guide):")
    
    action_triggered = False
    
    if st.session_state["inp_wind_input"] > 35 or st.session_state["inp_gust_input"] > 40 or st.session_state["inp_sea_input"] > 2.0:
        st.error("🔴 **CRITICAL ACTION: DISCONNECT ARM IMMEDIATELY!**")
        st.markdown("*Kondisi cuaca telah melebihi batas toleransi FSRU untuk menahan kapal. Segera diskonek lengan pemuat dan persiapkan evakuasi jika diperlukan.*")
        action_triggered = True
        
    elif st.session_state["inp_wind_input"] > 28 or st.session_state["inp_gust_input"] > 34 or st.session_state["inp_lightning_input"]:
        st.error("🔴 **CRITICAL ACTION: STOP CARGO OPERATION!**")
        st.markdown("*Hentikan seluruh operasi pompa. (Catatan: Cargo lines dapat tetap dijaga suhunya menggunakan spray pumps selama petir).*")
        action_triggered = True
        
    elif st.session_state["inp_wind_input"] > 20 or st.session_state["inp_sea_input"] > 1.5 or st.session_state["inp_vis_input"] < 2.0:
        st.warning("🟠 **RESTRICTION: NO BERTHING ALLOWED!**")
        st.markdown("*Kapal tidak diizinkan sandar. Cuaca belum memenuhi standar keselamatan manuver. Tunda operasi (Postponed).*")
        action_triggered = True
        
    elif st.session_state["inp_wind_input"] >= 17:
        st.info("🟡 **CAUTION: BERTHING / UNBERTHING ALLOWED WITH 4 TUGS.**")
        st.markdown("*Kondisi angin cukup kuat. Wajib menggunakan 4 Tugboat untuk assist manuver.*")
        action_triggered = True
        
    if st.session_state["inp_wind_input"] > 20 and not action_triggered:
        st.warning("🟠 **RESTRICTION: STOP USE OF PERSONNEL CRANE.**")
        action_triggered = True
    elif st.session_state["inp_wind_input"] > 20 and action_triggered:
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
        vessel_name = st.text_input("🚢 Nama Kapal LNGC", value=st.session_state["vessel_name_input"], key="vessel_name_input")
        cargo_vol = st.number_input("Cargo to Load (m³)", min_value=10000.0, value=st.session_state["cargo_vol_input"], step=1000.0, key="cargo_vol_input")
        safe_filling_limit = st.number_input("Safe Filling Limit (m³)", min_value=100000.0, value=st.session_state["safe_filling_limit_input"], step=500.0, key="safe_filling_limit_input")
    with c2: 
        rob_awal = st.number_input("ROB H-1 00:00 (m³)", min_value=0.0, value=st.session_state["rob_awal_input"], step=500.0, key="rob_awal_input")
    with c3: 
        serapan_harian_target = st.number_input("Target Serapan PLN/Day (m³)", min_value=1000.0, value=st.session_state["serapan_harian_target_input"], step=500.0, key="serapan_harian_target_input")
        st.markdown(f"<div style='text-align:right; font-size:13px; color:#38bdf8; margin-top:-15px; font-weight:600;'>💡 Aktual: {serapan_per_jam_aktual:,.2f} m³/h</div>", unsafe_allow_html=True)
    
    cw1, cw2 = st.columns(2)
    with cw1:
        st.caption("Record ROB")
        rd1, rt1 = st.columns(2)
        tgl_rob = rd1.date_input("Tanggal ROB", value=st.session_state["tgl_rob_input"], key="tgl_rob_input")
        jam_rob = rt1.time_input("Jam ROB", value=st.session_state["jam_rob_input"], key="jam_rob_input")
    with cw2:
        st.caption("ETA Kapal")
        rd2, rt2 = st.columns(2)
        tgl_eta = rd2.date_input("Tanggal ETA", value=st.session_state["tgl_eta_input"], key="tgl_eta_input")
        jam_eta = rt2.time_input("Jam ETA", value=st.session_state["jam_eta_input"], key="jam_eta_input")

    st.markdown("---")
    st.markdown("### ⚙️ 2. Evaluasi Laytime & Kebutuhan Regasifikasi")
    
    col_lt1, col_lt2, col_lt3 = st.columns(3)
    
    with col_lt1:
        laytime_kontrak = st.number_input("Batas Laytime Kontrak (Jam)", min_value=1.0, value=st.session_state["laytime_kontrak_input"], step=0.5, key="laytime_kontrak_input")
        max_loading_rate = st.number_input("Kapasitas Maksimal Pompa (Batas Atas) m³/h", min_value=100.0, value=st.session_state["max_loading_rate_input"], step=100.0, key="max_loading_rate_input")
        
        st.markdown(f"<div style='margin-top:10px; margin-bottom:5px; padding:10px; background:rgba(15,23,42,0.5); border-radius:5px; border-left:3px solid #10b981;'><span style='font-size:12px; color:#94a3b8;'>Rentang Rate Aman:</span><br><strong style='color:#ef4444;'>{min_loading_rate:,.0f}</strong> <span style='color:#94a3b8;'>s.d</span> <strong style='color:#38bdf8;'>{st.session_state['max_loading_rate_input']:,.0f}</strong> <span style='font-size:12px; color:#94a3b8;'>m³/h</span></div>", unsafe_allow_html=True)
        
        input_loading_rate = st.number_input("⚡ Rencana Loading Rate Aktual (m³/h)", min_value=100.0, value=st.session_state["input_loading_rate_input"], step=100.0, key="input_loading_rate_input")
        worst_case_serapan_input = st.number_input("Serapan s.d Commence (Worst Case) m³", value=st.session_state["worst_case_serapan_input_x"], step=500.0, key="worst_case_serapan_input_x")

    with col_lt2:
        if st.session_state["input_loading_rate_input"] < min_loading_rate:
            st.error(f"🚨 **OVER LAYTIME:** Rate terlalu lambat! Minimum {min_loading_rate:,.0f} m³/h.")
        elif st.session_state["input_loading_rate_input"] > st.session_state["max_loading_rate_input"]:
            st.warning(f"⚠️ **OVER CAPACITY:** Melebihi standar aman operasi FSRU/LNGC.")
        else:
            st.success(f"✅ **RATE AMAN:** Laytime Terpakai {actual_laytime:.1f} Jam")
            
        st.metric("Total Waktu Allowance", f"{total_allowance_hours:.1f} Jam", "Potongan Persiapan & Closing", delta_color="inverse")
        st.metric("ROB Saat Commence", f"{rob_commence:,.0f} m³", f"Jeda Tunggu: {selisih_jam_rob:.1f} Jam", delta_color="off")

    with col_lt3:
        if volume_disrub > 0:
            regas_harian_dibutuhkan = (volume_disrub / (actual_pumping_mins / 60.0)) * 24
            regas_per_jam_dibutuhkan = volume_disrub / (actual_pumping_mins / 60.0)
            
            st.metric("VL (Wajib Serap Darat)", f"{volume_disrub:,.0f} m³", "Overfill Risk!", delta_color="inverse")
            
            if regas_harian_dibutuhkan > st.session_state["serapan_harian_target_input"]:
                st.error(f"🚨 **BAHAYA TRIP!** Melebihi kapasitas {st.session_state['serapan_harian_target_input']:,.0f} m³/day.")
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
    st.markdown("#### 📊 Hasil Proyeksi 3 Skenario")
    st.caption("Skenario Aktual, Batas Bawah (Max Laytime), dan Batas Atas (Max Rate) untuk acuan waktu operasional.")
    
    def render_esod_card(color_rgb, title, label_rate, val_rate, val_laytime, t_start, t_comp, t_disc):
        return f"<div style='background:rgba({color_rgb}, 0.1); border-left:4px solid rgb({color_rgb}); padding:15px; border-radius:8px;'><div style='font-size:14px; font-weight:bold; color:rgb({color_rgb});'>{title}</div><div style='margin-top:10px; font-size:12px; color:#94a3b8;'>{label_rate}:</div><div style='font-size:22px; font-weight:bold; color:#f8fafc;'>{val_rate:,.0f} m³/h</div><div style='margin-top:5px; font-size:12px; color:#94a3b8;'>Estimasi Laytime Terpakai:</div><div style='font-size:20px; font-weight:bold; color:#f8fafc;'>{val_laytime:.1f} Jam</div><div style='margin-top:15px; border-top:1px solid rgba({color_rgb}, 0.3); padding-top:10px;'><div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='font-size:11px; color:#94a3b8;'>Start Discharge:</span><span style='font-size:12px; font-weight:bold; color:#f8fafc;'>{t_start.strftime('%d %b - %H:%M')}</span></div><div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='font-size:11px; color:#94a3b8;'>Complete Discharge:</span><span style='font-size:12px; font-weight:bold; color:#f8fafc;'>{t_comp.strftime('%d %b - %H:%M')}</span></div><div style='display:flex; justify-content:space-between;'><span style='font-size:11px; color:#94a3b8;'>Arm Disconnect:</span><span style='font-size:12px; font-weight:bold; color:rgb({color_rgb});'>{t_disc.strftime('%d %b - %H:%M')}</span></div></div></div>"

    sc_c1, sc_c2, sc_c3 = st.columns(3)
    with sc_c1:
        st.markdown(render_esod_card("239, 68, 68", "📉 BATAS BAWAH (Paling Lambat)", "Loading Rate Minimum", min_loading_rate, actual_laytime, esod_start_bawah, esod_comp_bawah, esod_disc_bawah), unsafe_allow_html=True)
    with sc_c2:
        st.markdown(render_esod_card("16, 185, 129", "🎯 AKTUAL (Rencana Operasi)", "Loading Rate Rencana", st.session_state["input_loading_rate_input"], actual_laytime, esod_start_aktual, esod_comp_aktual, esod_disc_aktual), unsafe_allow_html=True)
    with sc_c3:
        st.markdown(render_esod_card("56, 189, 248", "📈 BATAS ATAS (Paling Cepat)", "Loading Rate Maksimal", st.session_state["max_loading_rate_input"], min_laytime, esod_start_atas, esod_comp_atas, esod_disc_atas), unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 2: BERTHING & EMAIL TEMPLATE
# ==========================================
with tab_sandar:
    st.info(f"📸 **PENGINGAT (Terkait Open CTM):** Snapshot Radar wajib diambil pada pukul **{waktu_snapshot.strftime('%H:%M')} LCT** (Tepat 5 menit sebelum *Arm Cooldown* dimulai).")
    
    with st.form("esod_edit_form"):
        st.markdown("### 📅 Live ESOD Timeline (Manual Save)")
        st.caption("Ubah **Durasi (Min)** ATAU ketik **Waktu (LCT)** secara langsung. Keduanya akan otomatis saling menyesuaikan setelah Anda mengeklik tombol **Simpan**.")
        
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
            "Waktu (LCT)": esod_times_actual,
            "Durasi (Min)": [0] + [st.session_state.durations[e] for e in events_list[1:]]
        })
    
        ed_df = st.data_editor(
            df_esod, 
            column_config={
                "Tahapan": st.column_config.TextColumn(disabled=True), 
                "Waktu (LCT)": st.column_config.DatetimeColumn("Waktu (LCT)", format="DD MMM YYYY - HH:mm", disabled=False),
                "Durasi (Min)": st.column_config.NumberColumn("Durasi (Min)", disabled=False)
            }, 
            use_container_width=True, 
            hide_index=True,
            key="esod_editor"
        )
        
        submit_esod = st.form_submit_button("💾 Simpan Perubahan ESOD", use_container_width=True)
    
    if submit_esod:
        try:
            editor_data = st.session_state.get("esod_editor", {})
            edited_rows = editor_data.get("edited_rows", {})
            
            edits = {}
            for k, v in edited_rows.items():
                try: edits[int(k)] = v
                except: pass
            
            current_time = pd.to_datetime(esod_times_actual[0]).tz_localize(None)
            
            if 0 in edits and "Waktu (LCT)" in edits[0]:
                current_time = pd.to_datetime(edits[0]["Waktu (LCT)"]).tz_localize(None)
                st.session_state["tgl_eta_input"] = current_time.date()
                st.session_state["jam_eta_input"] = current_time.time()
                
            for i in range(1, len(events_list)):
                ev = events_list[i]
                
                if i in edits:
                    changes = edits[i]
                    if "Waktu (LCT)" in changes:
                        target_time = pd.to_datetime(changes["Waktu (LCT)"]).tz_localize(None)
                        new_dur = int(round((target_time - current_time).total_seconds() / 60.0))
                        st.session_state.durations[ev] = new_dur 
                    elif "Durasi (Min)" in changes:
                        st.session_state.durations[ev] = int(changes["Durasi (Min)"])
                
                current_time += timedelta(minutes=st.session_state.durations[ev])
            
            save_dict = {}
            for k, v in st.session_state.items():
                if k.endswith("_input") or k.startswith("td_") or k == "durations" or k.startswith("qo_") or k == "checklist_unlocked":
                    save_dict[k] = v
            with open("ops_kondisi_terakhir.pkl", "wb") as f:
                pickle.dump(save_dict, f)
                
            st.success("✅ Waktu ESOD berhasil diperbarui dan disimpan secara presisi!")
            st.rerun()
        except Exception as e:
            st.error(f"Terjadi kesalahan format penulisan jam: {e}")
            
    st.markdown(f"""
    <div style='background:rgba(15,23,42,0.6); border-left:4px solid #38bdf8; padding:15px; border-radius:8px; margin-top: 15px;'>
        <div style='font-size:13px; color:#94a3b8;'>⏱️ Total Waktu Laytime (Sesuai ESOD Aktual):</div>
        <div style='font-size:20px; font-weight:bold; color:#38bdf8;'>{dur_laytime:.2f} Jam</div>
        <div style='font-size:12px; color:#64748b; margin-top:5px;'>Mulai: {t_nor_recv.strftime('%d %b %Y %H:%M LCT')} &nbsp; | &nbsp; Selesai: {t_disc.strftime('%d %b %Y %H:%M LCT')}</div>
    </div>
    """, unsafe_allow_html=True)
        
    st.markdown("---")
    
    em_c1, em_c2 = st.columns([3, 1])
    with em_c1:
        st.markdown("### 📧 Auto-Generate Email Report (Commence Discharging)")
        st.caption("Lengkapi parameter di bawah ini agar template email menyesuaikan secara otomatis.")
    with em_c2:
        if st.button("🔄 Refresh Pesan Email", key="ref_em1"):
            st.rerun()
            
    col_em1, col_em2 = st.columns(2)
    with col_em1:
        cargo_no = st.text_input("Nomor Cargo (Cargo No)", value=st.session_state["cargo_no_input"], key="cargo_no_input")
        cargo_origin = st.text_input("Asal Cargo (Origin)", value=st.session_state["cargo_origin_input"], key="cargo_origin_input")
        pilot_name = st.text_input("Nama Pandu (Pilot)", value=st.session_state["pilot_name_input"], key="pilot_name_input")
    with col_em2:
        tugboat_info = st.text_area("Info Tugboat", value=st.session_state["tugboat_info_input"], key="tugboat_info_input")
        arm_info = st.text_input("Info Loading Arm", value=st.session_state["arm_info_input"], key="arm_info_input")

    vol_str = f"{st.session_state['cargo_vol_input']:,.0f}".replace(",", ".")
    rob_str = f"{rob_commence:,.0f}".replace(",", ".")
    rate_str = f"{st.session_state['input_loading_rate_input']:,.0f}".replace(",", ".")
    
    email_body = f"""Dear Pak Dhana,

The following is reported Start Discharge LNGC {st.session_state['vessel_name_input']} - Cargo No : {st.session_state['cargo_no_input']}.
{t_start_disc.strftime('%A')}, {format_email_date(t_start_disc)}
- {t_eosp.strftime('%H.%M')} LT          =            EOSP
- {t_nor_tend.strftime('%H.%M')} LT          =            NOR Tendered
- {t_eta.strftime('%H.%M')} LT          =            POB (Pandu : {st.session_state['pilot_name_input']})
- {t_first_line.strftime('%H.%M')} LT          =            First Line
- {t_allfast.strftime('%H.%M')} LT          =            All Fast
- {t_nor_recv.strftime('%H.%M')} LT          =            Completed Precargo Meeting (NOR received)
- {t_arm_conn.strftime('%H.%M')} LT          =            Arm Connected
- {t_open_ctm.strftime('%H.%M')} LT          =            Open CTM
- {t_start_disc.strftime('%H.%M')} LT          =            Start Discharging
- {t_full_rate.strftime('%H.%M')} LT          =            Full Rate

- The STS operations use {st.session_state['tugboat_info_input']}.

- ROB FSRU {rob_str} M3
- LNG Quantity {vol_str} M3
- Discharge average rate {rate_str} M3/h
- Using {st.session_state['arm_info_input']}

- Estimation Completed Discharging , {format_email_date(t_comp)}, around {t_comp.strftime('%H.%M')} LT.

- Estimation POB out {format_email_date(t_pob_out)} / {t_pob_out.strftime('%H.%M')} LT.

We will update the above data when complete discharging or if there is any new information.
The following is attached snapshot data (Open CTM, snapshot 30 & 15 minute Before Start Discharging, Commence Discharging and Estimation discharge Process) {st.session_state['vessel_name_input'].upper()} cargo {st.session_state['cargo_origin_input']} {st.session_state['cargo_no_input']}.

Thank you for your kind attention.

Best Regards,

{st.session_state["user_name"]}"""

    st.code(email_body, language='text')

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 3: MONITORING
# ==========================================
with tab_monitor:
    st.markdown(f"**Jadwal Eksekusi Snapshot Radar (Pre-Cooling):** {waktu_snapshot.strftime('%H:%M')} LCT")
    
    st.markdown("### ⏲️ Input Waktu Pemantauan Terkini")
    col_tnow1, col_tnow2 = st.columns(2)
    with col_tnow1:
        tgl_laporan = st.date_input("Tanggal Pencatatan", value=st.session_state["tgl_laporan_input"], key="tgl_laporan_input")
    with col_tnow2:
        jam_laporan = st.time_input("Jam Pencatatan Terkini", value=st.session_state["jam_laporan_input"], key="jam_laporan_input")
        
    waktu_sekarang = datetime.combine(st.session_state["tgl_laporan_input"], st.session_state["jam_laporan_input"])
    
    st.markdown("---")
    mt1, mt2 = st.columns(2)
    togo_vol = mt1.number_input("Volume LNG To Go (m³)", value=st.session_state["togo_vol_input"], step=1000.0, key="togo_vol_input")
    togo_rate = mt1.number_input("Actual Loading Rate (m³/h)", value=st.session_state["togo_rate_input"], step=100.0, key="togo_rate_input")
    
    sisa_h = st.session_state["togo_vol_input"] / st.session_state["togo_rate_input"] if st.session_state["togo_rate_input"] > 0 else 0
    
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
    
    jeda_dari_commence_ke_pompa = (t_start_disc - (t_eta + timedelta(hours=8))).total_seconds() / 3600.0
    rob_saat_pompa_nyala = rob_commence - (serapan_per_jam_aktual * jeda_dari_commence_ke_pompa)
    
    proj_data = []
    current_waktu = t_start_disc
    current_rob = rob_saat_pompa_nyala
    kargo_masuk_kumulatif = 0
    
    proj_data.append({
        "Jam ke-": 0.0,
        "Waktu (LCT)": current_waktu.strftime("%d %b %H:%M"),
        "Cargo In (m³)": 0.0,
        "Serapan Out (m³)": 0.0,
        "FSRU ROB (m³)": current_rob
    })
    
    jam_bulat = int(actual_pumping_mins / 60.0)
    sisa_desimal = (actual_pumping_mins / 60.0) - jam_bulat
    
    if jam_bulat > 150:
        st.warning("⚠️ Rencana Loading Rate sangat kecil. Grafik dibatasi maksimum 150 jam (6 hari) untuk mencegah *lag/crash* sistem.")
        jam_bulat = 150
        sisa_desimal = 0
        
    for i in range(1, jam_bulat + 1):
        current_waktu += timedelta(hours=1)
        kargo_masuk_kumulatif += st.session_state["input_loading_rate_input"]
        current_rob = current_rob + st.session_state["input_loading_rate_input"] - serapan_per_jam_aktual
        
        proj_data.append({
            "Jam ke-": float(i),
            "Waktu (LCT)": current_waktu.strftime("%d %b %H:%M"),
            "Cargo In (m³)": kargo_masuk_kumulatif,
            "Serapan Out (m³)": serapan_per_jam_aktual * i,
            "FSRU ROB (m³)": current_rob
        })
        
    if sisa_desimal > 0:
        current_waktu += timedelta(hours=sisa_desimal)
        kargo_in_sisa = st.session_state["input_loading_rate_input"] * sisa_desimal
        serapan_out_sisa = serapan_per_jam_aktual * sisa_desimal
        
        kargo_masuk_kumulatif += kargo_in_sisa
        current_rob = current_rob + kargo_in_sisa - serapan_out_sisa
        
        proj_data.append({
            "Jam ke-": float(round(actual_pumping_mins / 60.0, 1)),
            "Waktu (LCT)": current_waktu.strftime("%d %b %H:%M"),
            "Cargo In (m³)": kargo_masuk_kumulatif,
            "Serapan Out (m³)": serapan_per_jam_aktual * (actual_pumping_mins / 60.0),
            "FSRU ROB (m³)": current_rob
        })
        
    df_proj = pd.DataFrame(proj_data)
    
    def highlight_overfill_col(col):
        return [f'background-color: rgba(239, 68, 68, 0.4); color: white; font-weight:bold' if v > st.session_state["safe_filling_limit_input"] else '' for v in col]

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
# PHASE 5: FINAL REPORT & FLOWCHART
# ==========================================
with tab_closing:
    st.markdown("### 📐 Validasi Hak Milik & Energy Delivered")
    f1, f2, f3 = st.columns(3)
    
    init_ss("v_open_input", float(st.session_state["cargo_vol_input"] + 5000))
    v_open = f1.number_input("CTMS Opening Register (m³)", value=st.session_state["v_open_input"], step=10.0, key="v_open_input")
    v_close = f1.number_input("CTMS Closing Register (m³)", value=st.session_state.get("v_close_input", 5000.0), step=10.0, key="v_close_input")
    v_act = v_open - v_close
    
    dens = f2.number_input("Density LNG (kg/m³)", value=st.session_state["dens_input"], step=0.1, key="dens_input")
    mghv = f2.number_input("Mass GHV (MJ/kg)", value=st.session_state["mghv_input"], step=0.01, key="mghv_input")
    vghv = f2.number_input("Vapor GHV (MJ/m³)", value=st.session_state["vghv_input"], step=0.001, key="vghv_input")
    
    vt = f3.number_input("Vapor Temp (°C)", value=st.session_state["vt_input"], step=0.5, key="vt_input")
    vp = f3.number_input("Vapor Press (mbar)", value=st.session_state["vp_input"], step=1.0, key="vp_input")
    gc = f3.number_input("Gas Consumed (MMBtu)", value=st.session_state["gc_input"], step=1.0, key="gc_input")

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
    
    em_c3, em_c4 = st.columns([3, 1])
    with em_c3:
        st.markdown("### 📧 Auto-Generate Email Report (Completed Discharging)")
        st.caption("Salin templat email final di bawah ini untuk dilaporkan ke Manajemen.")
    with em_c4:
        if st.button("🔄 Refresh Pesan Email", key="ref_em2"):
            st.rerun()
            
    ec1, ec2 = st.columns(2)
    with ec1:
        cargo_sequence = st.text_input("Urutan Cargo Tahun Ini (contoh: 19th)", value=st.session_state["cargo_seq_input"], key="cargo_seq_input")
    with ec2:
        rob_akhir = st.number_input("Tuliskan ROB FSRU Aktual (m³)", value=st.session_state.get("rob_akhir_input", 124846.0), step=500.0, key="rob_akhir_input")
    
    events_to_print = [
        (t_eosp, "EOSP"),
        (t_nor_tend, "NOR Tendered"),
        (t_eta, f"POB (Pandu : {st.session_state['pilot_name_input']})"),
        (t_first_line, "First Line"),
        (t_allfast, "All Fast"),
        (t_nor_recv, "Completed Precargo Meeting (NOR received)"),
        (t_arm_conn, "Arm Connected"),
        (t_open_ctm, "Open CTM"),
        (t_start_disc, "Start Discharging"),
        (t_full_rate, "Full Rate"),
        (t_rate_down, "Rate Down"),
        (t_comp, "Discharging Completed"),
        (t_close_ctm, "Closing CTMS"),
        (t_disc, "All Arm Disconnected"),
        (t_doc, "Documentation"),
        (t_pob_out, "POB out"),
        (t_commence_unmooring, "Commence Unmooring"),
        (t_all_line_clear, "All Line Clear")
    ]
    
    email_lines = []
    current_date = None
    for t, label in events_to_print:
        event_date = t.date()
        if current_date != event_date:
            current_date = event_date
            date_header = f"\n{t.strftime('%A')}, {format_email_date(t)}"
            email_lines.append(date_header)
        
        time_str = t.strftime('%H.%M')
        email_lines.append(f"- {time_str} LT           =            {label}")
        
    timeline_text = "\n".join(email_lines)

    email_body_complete = f"""Dear All,

The following is a report on operational STS and discharging/unloading of {cargo_sequence} cargoes in {t_eta.year}. Cargo No : {st.session_state['cargo_no_input']} – LNGC {st.session_state['vessel_name_input'].upper()};
{timeline_text}

Total LNG Transferred   =     {v_act:,.3f} M3 (Rev.)

Total Discharging Operation Time :
- From POB – First Line                                  =               {dur_pob_first:.2f} Hour
- From POB – All Fast                                    =               {dur_pob_all:.2f} Hour
- From Start Discharge – Completed Discharge      =              {dur_start_comp:.2f} Hour
- From N.O.R Received – Disconnected All Arm      =            {dur_laytime:.2f} Hour - (Lay time)
- From All Fast – Disconnected all Arm                   =               {dur_all_disc:.2f} Hour

The following is attached cargo document {st.session_state['cargo_no_input']} – {st.session_state['cargo_origin_input']}.

Thank you for your attention.
Regards,

{st.session_state['user_name']}"""

    st.code(email_body_complete.replace(",", "."), language='text')
    
    st.markdown("---")
    
    # ---------------------------------------------------------
    # GENERATOR FLOWCHART JPG BERBASIS PILLOW
    # ---------------------------------------------------------
    st.markdown("### 🖼️ Auto-Generate Flowchart JPG")
    st.caption("Fungsi ini akan membuka file `base_flowchart.jpg` kosong Anda, menempelkan angka ESOD terbaru, dan menyimpannya sebagai gambar baru yang siap diunduh.")

    burn_coords = {
        "txt_pob_time": (246, 266),
        "txt_fl_time": (668, 266),
        "txt_af_time": (1085, 266),
        "dur_pob_fl": (460, 240),
        "dur_fl_af": (880, 240),
        "txt_sd_time": (246, 563),
        "txt_na_time": (668, 563),
        "txt_nt_time": (1085, 563), 
        "dur_sd_na": (460, 538),
        "dur_na_nt": (880, 538),
        "txt_cd_time": (246, 856),
        "txt_da_time": (668, 856),
        "txt_alc_time": (1085, 856),
        "dur_cd_da": (460, 831),
        "dur_da_alc": (880, 831),
        "dur_total_laytime": (850, 1010)
    }

    COLOR_BLACK = (15, 23, 42) 
    COLOR_RED = (185, 28, 28)   

    generated_image_ready = False
    img_buffer = io.BytesIO()

    if st.button("🚀 Generate & Isi Flowchart JPG", use_container_width=True):
        
        base_img_path = "base_flowchart.jpg"
        font_path = "arial.ttf"

        if not os.path.exists(base_img_path):
            st.error(f"File gambar statis kosong bernama '{base_img_path}' tidak ditemukan di folder proyek.")
        elif not os.path.exists(font_path):
            st.error(f"File font bernama '{font_path}' (misal Arial.ttf) tidak ditemukan di folder proyek.")
        else:
            with st.spinner("Python sedang memproses gambar..."):
                try:
                    img = Image.open(base_img_path).convert("RGB")
                    draw = ImageDraw.Draw(img)
                    
                    font_time = ImageFont.truetype(font_path, 26) 
                    font_dur = ImageFont.truetype(font_path, 22)  
                    font_total = ImageFont.truetype(font_path, 28)

                    def draw_text_centered(text, coord, font, color):
                        bbox = draw.textbbox((0, 0), text, font=font)
                        w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                        x = coord[0] - w/2
                        y = coord[1] - h/2
                        draw.text((x, y), text, fill=color, font=font)

                    draw_text_centered(t_eta.strftime('%H.%M'), burn_coords["txt_pob_time"], font_time, COLOR_BLACK)
                    draw_text_centered(t_first_line.strftime('%H.%M'), burn_coords["txt_fl_time"], font_time, COLOR_BLACK)
                    draw_text_centered(t_allfast.strftime('%H.%M'), burn_coords["txt_af_time"], font_time, COLOR_BLACK)
                    draw_text_centered(f"{dur_pob_first:.2f} HOURS", burn_coords["dur_pob_fl"], font_dur, COLOR_RED)
                    draw_text_centered(f"{(t_allfast - t_first_line).total_seconds() / 3600.0:.2f} HOURS", burn_coords["dur_fl_af"], font_dur, COLOR_RED)

                    draw_text_centered(t_start_disc.strftime('%H.%M'), burn_coords["txt_sd_time"], font_time, COLOR_BLACK)
                    draw_text_centered(t_nor_recv.strftime('%H.%M'), burn_coords["txt_na_time"], font_time, COLOR_BLACK)
                    draw_text_centered(f"{(t_start_disc - t_nor_recv).total_seconds() / 3600.0:.2f} HOURS", burn_coords["dur_sd_na"], font_dur, COLOR_RED)
                    draw_text_centered(f"{(t_nor_recv - t_allfast).total_seconds() / 3600.0:.2f} HOURS", burn_coords["dur_na_nt"], font_dur, COLOR_RED)

                    draw_text_centered(t_comp.strftime('%H.%M'), burn_coords["txt_cd_time"], font_time, COLOR_BLACK)
                    draw_text_centered(t_disc.strftime('%H.%M'), burn_coords["txt_da_time"], font_time, COLOR_BLACK)
                    draw_text_centered(t_all_line_clear.strftime('%H.%M'), burn_coords["txt_alc_time"], font_time, COLOR_BLACK)
                    draw_text_centered(f"{(t_disc - t_comp).total_seconds() / 3600.0:.2f} HOURS", burn_coords["dur_cd_da"], font_dur, COLOR_RED)
                    draw_text_centered(f"{(t_all_line_clear - t_disc).total_seconds() / 3600.0:.2f} HOURS", burn_coords["dur_da_alc"], font_dur, COLOR_RED)

                    draw_text_centered(f"{dur_laytime:.2f} HOURS", burn_coords["dur_total_laytime"], font_total, COLOR_RED)

                    img.save(img_buffer, format="JPEG", quality=95)
                    img_buffer.seek(0)
                    generated_image_ready = True
                    st.success("✅ Flowchart berhasil diisi! Lihat pratinjau dan unduh di bawah.")

                except Exception as e:
                    st.error(f"Gagal memproses gambar. Error: {e}")

    if generated_image_ready:
        st.image(img_buffer, caption=f"Pratinjau Flowchart Terisi - LNGC {st.session_state['vessel_name_input']}", use_container_width=True)
        
        st.download_button(
            label="📥 UNDUH FLOWCHART JPG (SIAP LAMPIRKAN)",
            data=img_buffer,
            file_name=f"Flowchart_Ops_{st.session_state['vessel_name_input']}_{datetime.now().strftime('%H%M')}.jpg",
            mime="image/jpeg",
            use_container_width=True
        )

    st.markdown("---")
    st.markdown("### 🗂️ Export Full Operations Record")
    st.caption("Unduh seluruh aktivitas, checklist, parameter, dan timeline ESOD dalam satu file Excel lengkap.")
    
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            
            df_gen = pd.DataFrame([
                {"Parameter": "Tanggal Cetak", "Nilai": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {"Parameter": "CTO On Duty", "Nilai": st.session_state["user_name"]},
                {"Parameter": "Nama Kapal", "Nilai": st.session_state["vessel_name_input"]},
                {"Parameter": "No Kargo", "Nilai": st.session_state["cargo_no_input"]},
                {"Parameter": "ETA Kapal", "Nilai": waktu_eta.strftime("%Y-%m-%d %H:%M:%S")},
                {"Parameter": "Volume Kargo (m³)", "Nilai": st.session_state["cargo_vol_input"]},
                {"Parameter": "Rate Pompa (m³/h)", "Nilai": st.session_state["input_loading_rate_input"]},
                {"Parameter": "Laytime Kontrak (Jam)", "Nilai": st.session_state["laytime_kontrak_input"]},
                {"Parameter": "Laytime Aktual (Jam)", "Nilai": actual_laytime},
            ])
            df_gen.to_excel(writer, sheet_name='General Info', index=False)
            
            df_esod_export = pd.DataFrame({
                "Tahapan Operasi": events_list,
                "Waktu Aktual (LCT)": [t.strftime("%Y-%m-%d %H:%M:%S") for t in esod_times_actual],
                "Durasi (Menit)": [0] + [st.session_state.durations[e] for e in events_list[1:]]
            })
            df_esod_export.to_excel(writer, sheet_name='Timeline ESOD', index=False)
            
            chk_data = []
            for key in checklist_keys:
                status = "Selesai" if st.session_state.get(key, False) else "Belum"
                chk_data.append({"Task ID (Sidebar)": key, "Status": status})
            df_chk_export = pd.DataFrame(chk_data)
            df_chk_export.to_excel(writer, sheet_name='Checklist Log', index=False)
            
            df_energy = pd.DataFrame([
                {"Parameter": "Volume Dibongkar (m³)", "Nilai": v_act},
                {"Parameter": "Vapor Return (MJ)", "Nilai": qr},
                {"Parameter": "Gross Energy (MMBtu)", "Nilai": qty_gross},
                {"Parameter": "Net Energy Delivered (MMBtu)", "Nilai": qty_net}
            ])
            df_energy.to_excel(writer, sheet_name='Energy Report', index=False)
            
        excel_data = output.getvalue()
        
        st.download_button(
            label="📥 DOWNLOAD FULL OPERATIONS LOG (EXCEL)",
            data=excel_data,
            file_name=f"Ops_Log_{st.session_state['vessel_name_input']}_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error("Gagal membuat Excel. Harap pastikan package 'openpyxl' terinstall (Ketik: pip install openpyxl).")

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
    st.caption("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>© 2026 PT Nusantara Regas - FSRU NR Command Center Workspace</div>", unsafe_allow_html=True)
    st.markdown("<br><br>", unsafe_allow_html=True)

# ==========================================
# 9. INVISIBLE AUTO-SAVE EXECUTION
# ==========================================
save_dict = {}
for k, v in st.session_state.items():
    if k.endswith("_input") or k.startswith("td_") or k == "durations" or k.startswith("qo_") or k == "checklist_unlocked":
        save_dict[k] = v
try:
    with open("ops_kondisi_terakhir.pkl", "wb") as f:
        pickle.dump(save_dict, f)
except Exception:
    pass
