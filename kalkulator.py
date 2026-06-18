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
    "EOSP", "NOR Tendered", "ETA / POB", "First Line", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", 
    "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", 
    "FULL RATE", "RATE DOWN", "DISCHARGING COMPLETED", "CLOSING CTM", 
    "ARMs Disconnected", "Documentation", "POB OUT", "Commence Unmooring", "All Line Clear"
]

default_durations = {
    "NOR Tendered": 45, "ETA / POB": 0, "First Line": 185, "All Fast": 85, "NOR Received": 70, 
    "ARMs Connected": 10, "OPEN CTM": 35, "WARM ESD Test": 15, "Arm C/D": 90, "COLD ESD Test": 15, 
    "START DISCHARGING": 20, "FULL RATE": 30, "RATE DOWN": 1754, "DISCHARGING COMPLETED": 30, 
    "CLOSING CTM": 120, "ARMs Disconnected": 10, "Documentation": 60, "POB OUT": 120, 
    "Commence Unmooring": 34, "All Line Clear": 11
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
init_ss("editor_key_counter", 0) # Penanda Unik Auto-Save Data Editor

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
init_ss("rob_precargo_input", 42000.0) 
init_ss("rob_akhir_input", 124846.0) 
init_ss("serapan_harian_target_input", 17000.0)
init_ss("tgl_rob_input", datetime(2026, 6, 9).date())
init_ss("jam_rob_input", datetime.strptime("00:00", "%H:%M").time())
init_ss("tgl_eosp_input", datetime(2026, 6, 10).date())
init_ss("jam_eosp_input", datetime.strptime("09:00", "%H:%M").time())
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
# 5. GLOBAL LIVE AUTO-SAVE ENGINE (ANTI-KEMBALI KE AWAL)
# ==========================================
# Mesin ini menangkap setiap sel yang Anda ketik secara realtime
current_editor_key = f"esod_editor_{st.session_state.editor_key_counter}"

if current_editor_key in st.session_state:
    edits = st.session_state[current_editor_key].get("edited_rows", {})
    if edits:
        real_edits = {int(k): v for k, v in edits.items()}
        
        # Mulai dari waktu EOSP patokan
        waktu_eosp_temp = datetime.combine(st.session_state["tgl_eosp_input"], st.session_state["jam_eosp_input"])
        current_time = waktu_eosp_temp
        
        # Cek jika EOSP (baris index 0) diedit jamnya
        if 0 in real_edits and "Waktu (LCT)" in real_edits[0]:
            current_time = pd.to_datetime(real_edits[0]["Waktu (LCT)"]).tz_localize(None)
            st.session_state["tgl_eosp_input"] = current_time.date()
            st.session_state["jam_eosp_input"] = current_time.time()
        
        # Cascade iterasi ke bawah
        for i in range(1, len(events_list)):
            ev = events_list[i]
            if i in real_edits:
                changes = real_edits[i]
                if "Waktu (LCT)" in changes:
                    target_time = pd.to_datetime(changes["Waktu (LCT)"]).tz_localize(None)
                    # Menghitung durasi secara normal (bisa positif bisa negatif jika jam out-of-order)
                    new_dur = int(round((target_time - current_time).total_seconds() / 60.0))
                    st.session_state.durations[ev] = new_dur 
                elif "Durasi (Min)" in changes:
                    st.session_state.durations[ev] = int(changes["Durasi (Min)"])
            
            current_time += timedelta(minutes=st.session_state.durations[ev])
            
        # Naikkan counter agar form menjadi "bersih" di render berikutnya (mencegah loop)
        st.session_state.editor_key_counter += 1
        
        # Save Background ke Pickle
        save_dict = {}
        for k, v in st.session_state.items():
            if k.endswith("_input") or k.startswith("td_") or k == "durations" or k.startswith("qo_") or k == "checklist_unlocked" or k == "editor_key_counter":
                save_dict[k] = v
        try:
            with open("ops_kondisi_terakhir.pkl", "wb") as f: pickle.dump(save_dict, f)
        except: pass
        
        st.rerun() # Refresh instan ke UI terbaru!

# Kalkulasi Ulang Parameter Esensial
waktu_eosp = datetime.combine(st.session_state["tgl_eosp_input"], st.session_state["jam_eosp_input"])
waktu_rob = datetime.combine(st.session_state["tgl_rob_input"], st.session_state["jam_rob_input"])

allowance_prep_mins = (
    max(0, st.session_state.durations["ARMs Connected"]) + max(0, st.session_state.durations["OPEN CTM"]) + 
    max(0, st.session_state.durations["WARM ESD Test"]) + max(0, st.session_state.durations["Arm C/D"]) + 
    max(0, st.session_state.durations["COLD ESD Test"]) + max(0, st.session_state.durations["START DISCHARGING"])
)
allowance_closing_mins = max(0, st.session_state.durations["CLOSING CTM"]) + max(0, st.session_state.durations["ARMs Disconnected"])
total_allowance_hours = (allowance_prep_mins + allowance_closing_mins) / 60.0

actual_pumping_mins = (st.session_state["cargo_vol_input"] / st.session_state["input_loading_rate_input"]) * 60 if st.session_state["input_loading_rate_input"] > 0 else 0

if "prev_rate_for_esod" not in st.session_state:
    st.session_state.prev_rate_for_esod = st.session_state["input_loading_rate_input"]
    st.session_state.prev_vol_for_esod = st.session_state["cargo_vol_input"]
    st.session_state.durations["RATE DOWN"] = int(actual_pumping_mins) - max(0, st.session_state.durations["FULL RATE"]) - max(0, st.session_state.durations["DISCHARGING COMPLETED"])

if (st.session_state.prev_rate_for_esod != st.session_state["input_loading_rate_input"] or 
    st.session_state.prev_vol_for_esod != st.session_state["cargo_vol_input"]):
    st.session_state.durations["RATE DOWN"] = int(actual_pumping_mins) - max(0, st.session_state.durations["FULL RATE"]) - max(0, st.session_state.durations["DISCHARGING COMPLETED"])
    st.session_state.prev_rate_for_esod = st.session_state["input_loading_rate_input"]
    st.session_state.prev_vol_for_esod = st.session_state["cargo_vol_input"]

# Render Waktu
temp_dt = waktu_eosp
esod_times_actual = [temp_dt]
for ev in events_list[1:]:
    temp_dt += timedelta(minutes=st.session_state.durations[ev])
    esod_times_actual.append(temp_dt)

t_eosp = esod_times_actual[events_list.index("EOSP")]
t_nor_tend = esod_times_actual[events_list.index("NOR Tendered")]
t_eta = esod_times_actual[events_list.index("ETA / POB")]
t_first_line = esod_times_actual[events_list.index("First Line")]
t_allfast = esod_times_actual[events_list.index("All Fast")]
t_nor_recv = esod_times_actual[events_list.index("NOR Received")] 
t_arm_conn = esod_times_actual[events_list.index("ARMs Connected")]
t_open_ctm = esod_times_actual[events_list.index("OPEN CTM")]
t_warm_esd = esod_times_actual[events_list.index("WARM ESD Test")]
t_arm_cd = esod_times_actual[events_list.index("Arm C/D")]
t_cold_esd = esod_times_actual[events_list.index("COLD ESD Test")]
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

waktu_snapshot = t_arm_conn - timedelta(minutes=5)

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

waktu_commence = t_eta + timedelta(hours=8)
selisih_jam_rob = (waktu_commence - waktu_rob).total_seconds() / 3600.0
serapan_per_jam_aktual = st.session_state["serapan_harian_target_input"] / 24.0
serapan_matematis = serapan_per_jam_aktual * selisih_jam_rob
worst_case_default = float(int(serapan_matematis / 1000) * 1000)

if "worst_case_serapan_input_x" not in st.session_state:
    st.session_state["worst_case_serapan_input_x"] = worst_case_default

rob_commence = st.session_state["rob_awal_input"] - st.session_state["worst_case_serapan_input_x"]
volume_disrub = (rob_commence + st.session_state["cargo_vol_input"]) - st.session_state["safe_filling_limit_input"]

# Kalkulasi Durasi Mutlak (abs) untuk menghindari angka minus
dur_pob_first = abs((t_first_line - t_eta).total_seconds() / 3600.0)
dur_pob_all = abs((t_allfast - t_eta).total_seconds() / 3600.0)
dur_start_comp = abs((t_comp - t_start_disc).total_seconds() / 3600.0)
dur_laytime = abs((t_disc - t_nor_recv).total_seconds() / 3600.0)
dur_all_disc = abs((t_disc - t_allfast).total_seconds() / 3600.0)

# CSS CUSTOM
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
    .floating-btn { position: fixed; bottom: 20px; right: 20px; background: #10b981; color: white; padding: 15px 25px; border-radius: 50px; font-weight: 800; cursor: pointer; z-index: 9999; box-shadow: 0 4px 15px rgba(16, 185, 129, 0.4); border: none; }
</style>
""", unsafe_allow_html=True)
components.html("""<button class="floating-btn" onclick="openSidebar()">☰ MENU OPS</button><script>function openSidebar() { var buttons = window.parent.document.querySelectorAll('button[aria-label="Open sidebar"]'); if (buttons.length > 0) { buttons[0].click(); } }</script>""", height=70)

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
            else: st.error("Sandi salah!")
    else:
        if st.button("🔒 Kunci Akses Checklist"):
            st.session_state["checklist_unlocked"] = False
            st.rerun()
        with st.expander("🗓️ DAY -1 (Pre-Arrival)", expanded=False):
            st.checkbox("WAG Monitoring", value=st.session_state["td_d1_1"], key="td_d1_1")
            st.checkbox("WAG Patroli Laut", value=st.session_state["td_d1_2"], key="td_d1_2")
            st.checkbox("Hubungi JCC", value=st.session_state["td_d1_3"], key="td_d1_3")
            st.checkbox("Hubungi PLN", value=st.session_state["td_d1_4"], key="td_d1_4")
            st.checkbox("Surat PLN EPI", value=st.session_state["td_d1_5"], key="td_d1_5")
            st.checkbox("Draft Loading Plan", value=st.session_state["td_d1_6"], key="td_d1_6")
            st.checkbox("Draft Personeel", value=st.session_state["td_d1_7"], key="td_d1_7")
            st.checkbox("Draft Flowchart", value=st.session_state["td_d1_8"], key="td_d1_8")
            st.checkbox("TTD JoA & CoU", value=st.session_state["td_d1_9"], key="td_d1_9")
            st.checkbox("Email Permission", value=st.session_state["td_d1_10"], key="td_d1_10")
            st.checkbox("Email JoA, CoU", value=st.session_state["td_d1_11"], key="td_d1_11")

        with st.expander("🗓️ DAY 1 (Berthing & Start)", expanded=False):
            st.checkbox("Lapor ISPS", value=st.session_state["td_d2_1"], key="td_d2_1")
            st.checkbox("Monitor STS", value=st.session_state["td_d2_2"], key="td_d2_2")
            st.checkbox("Precargo Meeting", value=st.session_state["td_d2_3"], key="td_d2_3")
            st.checkbox("Snap Radar CTM", value=st.session_state["td_d2_4"], key="td_d2_4")
            st.checkbox("Supervisi ESD", value=st.session_state["td_d2_5"], key="td_d2_5")
            st.checkbox("Start Discharging", value=st.session_state["td_d2_6"], key="td_d2_6")
            st.checkbox("Email Start", value=st.session_state["td_d2_7"], key="td_d2_7")

        with st.expander("🗓️ DAY 2 (Monitoring)", expanded=False):
            st.checkbox("Update POB Out", value=st.session_state["td_d3_1"], key="td_d3_1")
            st.checkbox("Update LNG to go", value=st.session_state["td_d3_2"], key="td_d3_2")
            st.checkbox("Rate Down", value=st.session_state["td_d3_3"], key="td_d3_3")
            st.checkbox("Persiapan Closing", value=st.session_state["td_d3_4"], key="td_d3_4")

        with st.expander("🗓️ DAY 3 (Completed & Out)", expanded=False):
            st.checkbox("Draining & Purging", value=st.session_state["td_d4_1"], key="td_d4_1")
            st.checkbox("Snap Radar Closing", value=st.session_state["td_d4_2"], key="td_d4_2")
            st.checkbox("Arm Disconnect", value=st.session_state["td_d4_3"], key="td_d4_3")
            st.checkbox("TTD Dokumen", value=st.session_state["td_d4_4"], key="td_d4_4")
            st.checkbox("POB Out & ISPS", value=st.session_state["td_d4_5"], key="td_d4_5")
            st.checkbox("Email Final", value=st.session_state["td_d4_6"], key="td_d4_6")

    st.divider()
    if st.button("🚪 Logout / Ganti User", use_container_width=True):
        st.session_state["logged_in"] = False
        if os.path.exists(SESSION_FILE): os.remove(SESSION_FILE)
        st.rerun()

# ==========================================
# 7. HEADER LIVE & INDIKATOR JARINGAN
# ==========================================
user_display = str(st.session_state["user_name"]).upper()
status_jaringan = "🔴 OFFLINE MODE" if is_offline else f"🟢 ON DUTY: {user_display}"
warna_jaringan = "linear-gradient(135deg,#ef4444,#b91c1c)" if is_offline else "linear-gradient(135deg,#10b981,#059669)"
border_jaringan = "#f87171" if is_offline else "#34d399"

components.html(f"""
<style>@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');</style>
<div style="background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:15px 25px;display:flex;justify-content:space-between;align-items:center;color:white;font-family:'Poppins',sans-serif;">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="background:white;padding:5px 10px;border-radius:10px;"><img src="{html_logo_src}" style="height:30px;"></div>
        <div><div style="font-size:22px;font-weight:800;">CTO TERMINAL OPS</div><div style="color:#06b6d4;font-size:13px;">Nusantara Regas • Live Command Center</div></div>
    </div>
    <div style="background:{warna_jaringan};padding:8px 24px;border-radius:30px;font-weight:600;font-size:14px;border:1px solid {border_jaringan};">{status_jaringan}</div>
</div>
""", height=120)

# ==========================================
# 8. FUNGSI TOMBOL UNIVERSAL (SAVE & REFRESH)
# ==========================================
def render_global_save_button(tab_id):
    if st.button("🔄 SIMPAN & REFRESH APLIKASI", key=f"global_save_{tab_id}", use_container_width=True, type="primary"):
        save_dict = {}
        for k, v in st.session_state.items():
            if k.endswith("_input") or k.startswith("td_") or k == "durations" or k.startswith("qo_") or k == "checklist_unlocked" or k == "editor_key_counter": 
                save_dict[k] = v
        try:
            with open("ops_kondisi_terakhir.pkl", "wb") as f: 
                pickle.dump(save_dict, f)
        except: pass
        st.rerun()
    st.markdown("---")

# ==========================================
# 9. MAIN NAVIGATION
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
    render_global_save_button("weather")
    st.markdown("### 🌪️ Evaluasi Cuaca & Keselamatan Operasi")
    st.caption("Berdasarkan NRS Terminal Guide - Evaluasi Go/No-Go operasional kapal.")
    cw_1, cw_2, cw_3, cw_4 = st.columns(4)
    with cw_1: inp_wind = st.number_input("Wind Speed (Knots)", min_value=0.0, value=st.session_state["inp_wind_input"], step=1.0, key="inp_wind_input")
    with cw_2: inp_gust = st.number_input("Wind Gusts (Knots)", min_value=0.0, value=st.session_state["inp_gust_input"], step=1.0, key="inp_gust_input")
    with cw_3: inp_sea = st.number_input("Sea / Wave (m)", min_value=0.0, value=st.session_state["inp_sea_input"], step=0.1, key="inp_sea_input")
    with cw_4: inp_vis = st.number_input("Visibility (Nm)", min_value=0.0, value=st.session_state["inp_vis_input"], step=0.5, key="inp_vis_input")
    inp_lightning = st.checkbox("⚡ Terdapat Petir / Lightning?", value=st.session_state["inp_lightning_input"], key="inp_lightning_input")
    st.markdown("---")
    
    action_triggered = False
    if st.session_state["inp_wind_input"] > 35 or st.session_state["inp_gust_input"] > 40 or st.session_state["inp_sea_input"] > 2.0:
        st.error("🔴 **CRITICAL ACTION: DISCONNECT ARM IMMEDIATELY!**")
        action_triggered = True
    elif st.session_state["inp_wind_input"] > 28 or st.session_state["inp_gust_input"] > 34 or st.session_state["inp_lightning_input"]:
        st.error("🔴 **CRITICAL ACTION: STOP CARGO OPERATION!**")
        action_triggered = True
    elif st.session_state["inp_wind_input"] > 20 or st.session_state["inp_sea_input"] > 1.5 or st.session_state["inp_vis_input"] < 2.0:
        st.warning("🟠 **RESTRICTION: NO BERTHING ALLOWED!**")
        action_triggered = True
    elif st.session_state["inp_wind_input"] >= 17:
        st.info("🟡 **CAUTION: BERTHING / UNBERTHING ALLOWED WITH 4 TUGS.**")
        action_triggered = True
    if not action_triggered:
        st.success("✅ **SAFE TO OPERATE: NORMAL CONDITION.**")

# ==========================================
# FASE 1: PRE-ARRIVAL
# ==========================================
with tab_h1:
    render_global_save_button("h1")
    st.markdown("### 🧮 1. Parameter Kargo & Sinkronisasi Waktu")
    c1, c2, c3 = st.columns(3)
    with c1: 
        vessel_name = st.text_input("🚢 Nama Kapal LNGC", value=st.session_state["vessel_name_input"], key="vessel_name_input")
        cargo_vol = st.number_input("Cargo to Load (m³)", min_value=10000.0, value=st.session_state["cargo_vol_input"], step=1000.0, key="cargo_vol_input")
        safe_filling_limit = st.number_input("Safe Filling Limit (m³)", min_value=100000.0, value=st.session_state["safe_filling_limit_input"], step=500.0, key="safe_filling_limit_input")
    with c2: 
        rob_awal = st.number_input("ROB H-1 00:00 (m³)", min_value=0.0, value=st.session_state["rob_awal_input"], step=500.0, key="rob_awal_input")
        rob_precargo = st.number_input("ROB saat Pre-Cargo Meeting (m³)", min_value=0.0, value=st.session_state["rob_precargo_input"], step=500.0, key="rob_precargo_input")
    with c3: 
        serapan_harian_target = st.number_input("Target Serapan PLN/Day (m³)", min_value=1000.0, value=st.session_state["serapan_harian_target_input"], step=500.0, key="serapan_harian_target_input")
    
    cw1, cw2 = st.columns(2)
    with cw1:
        tgl_rob = st.date_input("Tanggal ROB", value=st.session_state["tgl_rob_input"], key="tgl_rob_input")
        jam_rob = st.time_input("Jam ROB", value=st.session_state["jam_rob_input"], key="jam_rob_input")
    with cw2:
        st.caption("EOSP Kapal (Titik Awal ESOD)")
        tgl_eosp = st.date_input("Tanggal EOSP", value=st.session_state["tgl_eosp_input"], key="tgl_eosp_input")
        jam_eosp = st.time_input("Jam EOSP", value=st.session_state["jam_eosp_input"], key="jam_eosp_input")

    st.markdown("---")
    st.markdown("### ⚙️ 2. Evaluasi Laytime & Kebutuhan Regasifikasi")
    col_lt1, col_lt2, col_lt3 = st.columns(3)
    with col_lt1:
        laytime_kontrak = st.number_input("Batas Laytime Kontrak (Jam)", min_value=1.0, value=st.session_state["laytime_kontrak_input"], step=0.5, key="laytime_kontrak_input")
        max_loading_rate = st.number_input("Kapasitas Maksimal Pompa (Batas Atas) m³/h", min_value=100.0, value=st.session_state["max_loading_rate_input"], step=100.0, key="max_loading_rate_input")
        input_loading_rate = st.number_input("⚡ Rencana Loading Rate Aktual (m³/h)", min_value=100.0, value=st.session_state["input_loading_rate_input"], step=100.0, key="input_loading_rate_input")
        worst_case_serapan_input = st.number_input("Serapan s.d Commence (Worst Case) m³", value=st.session_state["worst_case_serapan_input_x"], step=500.0, key="worst_case_serapan_input_x")

    with col_lt2:
        if st.session_state["input_loading_rate_input"] < min_loading_rate: st.error(f"🚨 **OVER LAYTIME:** Rate lambat! Min {min_loading_rate:,.0f} m³/h.")
        else: st.success(f"✅ **RATE AMAN:** Laytime Terpakai {actual_laytime:.1f} Jam")
        st.metric("Total Waktu Allowance", f"{total_allowance_hours:.1f} Jam", delta_color="inverse")
        st.metric("ROB Saat Commence", f"{rob_commence:,.0f} m³", delta_color="off")

    with col_lt3:
        if volume_disrub > 0:
            regas_harian_dibutuhkan = (volume_disrub / (actual_pumping_mins / 60.0)) * 24
            st.metric("VL (Wajib Serap Darat)", f"{volume_disrub:,.0f} m³", "Overfill Risk!", delta_color="inverse")
            if regas_harian_dibutuhkan > st.session_state["serapan_harian_target_input"]: st.error("🚨 **BAHAYA TRIP!** Kapasitas kurang.")
            else: st.success("✅ **AMAN.**")
        else:
            st.metric("VL (Wajib Serap Darat)", "0 m³", "Safe Tank", delta_color="normal")
            st.success("✅ Kapasitas tangki aman menampung seluruh kargo.")

    st.write("")
    st.markdown("#### 📊 Hasil Proyeksi 3 Skenario")
    def render_esod_card(color_rgb, title, label_rate, val_rate, val_laytime, t_start, t_comp, t_disc):
        return f"<div style='background:rgba({color_rgb}, 0.1); border-left:4px solid rgb({color_rgb}); padding:15px; border-radius:8px;'><div style='font-size:14px; font-weight:bold; color:rgb({color_rgb});'>{title}</div><div style='margin-top:10px; font-size:12px; color:#94a3b8;'>{label_rate}:</div><div style='font-size:22px; font-weight:bold; color:#f8fafc;'>{val_rate:,.0f} m³/h</div><div style='margin-top:5px; font-size:12px; color:#94a3b8;'>Estimasi Laytime Terpakai:</div><div style='font-size:20px; font-weight:bold; color:#f8fafc;'>{val_laytime:.1f} Jam</div><div style='margin-top:15px; border-top:1px solid rgba({color_rgb}, 0.3); padding-top:10px;'><div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='font-size:11px; color:#94a3b8;'>Start Discharge:</span><span style='font-size:12px; font-weight:bold; color:#f8fafc;'>{t_start.strftime('%d %b - %H:%M')}</span></div><div style='display:flex; justify-content:space-between; margin-bottom:5px;'><span style='font-size:11px; color:#94a3b8;'>Complete Discharge:</span><span style='font-size:12px; font-weight:bold; color:#f8fafc;'>{t_comp.strftime('%d %b - %H:%M')}</span></div><div style='display:flex; justify-content:space-between;'><span style='font-size:11px; color:#94a3b8;'>Arm Disconnect:</span><span style='font-size:12px; font-weight:bold; color:rgb({color_rgb});'>{t_disc.strftime('%d %b - %H:%M')}</span></div></div></div>"

    sc_c1, sc_c2, sc_c3 = st.columns(3)
    with sc_c1: st.markdown(render_esod_card("239, 68, 68", "📉 BATAS BAWAH", "Rate Min", min_loading_rate, actual_laytime, esod_start_bawah, esod_comp_bawah, esod_disc_bawah), unsafe_allow_html=True)
    with sc_c2: st.markdown(render_esod_card("16, 185, 129", "🎯 AKTUAL (Rencana)", "Rate Rencana", st.session_state["input_loading_rate_input"], actual_laytime, esod_start_aktual, esod_comp_aktual, esod_disc_aktual), unsafe_allow_html=True)
    with sc_c3: st.markdown(render_esod_card("56, 189, 248", "📈 BATAS ATAS", "Rate Max", st.session_state["max_loading_rate_input"], min_laytime, esod_start_atas, esod_comp_atas, esod_disc_atas), unsafe_allow_html=True)

# ==========================================
# FASE 2: BERTHING & EMAIL TEMPLATE
# ==========================================
with tab_sandar:
    render_global_save_button("berthing")
    st.info(f"📸 **PENGINGAT:** Snapshot Radar pada pukul **{waktu_snapshot.strftime('%H:%M')} LCT**.")
    
    st.markdown("### 📅 Live ESOD Timeline (Auto-Save)")
    st.caption("Ubah **Durasi (Min)** ATAU ketik **Waktu (LCT)** secara langsung. Sistem akan **MENYIMPAN OTOMATIS** saat Anda menekan Enter atau mengeklik di luar sel.")
    
    display_tahapan = []
    for ev in events_list:
        if ev == "NOR Received": display_tahapan.append("🟢 NOR Received (START LAYTIME)")
        elif ev == "ARMs Disconnected": display_tahapan.append("🛑 ARMs Disconnected (END LAYTIME)")
        else: display_tahapan.append(ev)
            
    df_esod = pd.DataFrame({"Tahapan": display_tahapan, "Waktu (LCT)": esod_times_actual, "Durasi (Min)": [0] + [st.session_state.durations[e] for e in events_list[1:]]})
    
    ed_df = st.data_editor(
        df_esod, 
        column_config={
            "Tahapan": st.column_config.TextColumn(disabled=True), 
            "Waktu (LCT)": st.column_config.DatetimeColumn("Waktu (LCT)", format="DD MMM YYYY - HH:mm", disabled=False), 
            "Durasi (Min)": st.column_config.NumberColumn("Durasi (Min)", disabled=False)
        }, 
        use_container_width=True, 
        hide_index=True, 
        key=current_editor_key
    )
        
    st.markdown(f"<div style='background:rgba(15,23,42,0.6); border-left:4px solid #38bdf8; padding:15px; border-radius:8px; margin-top: 15px;'><div style='font-size:13px; color:#94a3b8;'>⏱️ Total Waktu Laytime:</div><div style='font-size:20px; font-weight:bold; color:#38bdf8;'>{dur_laytime:.2f} Jam</div></div>", unsafe_allow_html=True)
    st.markdown("---")
    
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

Thank you for your kind attention.
Best Regards,
{st.session_state["user_name"]}"""

    st.code(email_body, language='text')

# ==========================================
# FASE 3 & 4: MONITORING & ROB
# ==========================================
with tab_monitor:
    render_global_save_button("monitor")
    mt1, mt2 = st.columns(2)
    togo_vol = mt1.number_input("Volume LNG To Go (m³)", value=st.session_state["togo_vol_input"], step=1000.0, key="togo_vol_input")
    togo_rate = mt1.number_input("Actual Loading Rate (m³/h)", value=st.session_state["togo_rate_input"], step=100.0, key="togo_rate_input")

with tab_rob:
    render_global_save_button("rob")
    st.markdown("### 📈 Grafik Pergerakan ROB")
    st.info("Kalkulasi Grafik Aman di Latar Belakang.")

# ==========================================
# PHASE 5: FINAL REPORT & FLOWCHART JPG
# ==========================================
with tab_closing:
    render_global_save_button("closing")
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
    qr = v_act * (288.15 / suhu_kelvin_bawah) * (vp / 1013.25) * vghv if suhu_kelvin_bawah != 0 else 0.0
    qty_gross = ((v_act * dens * mghv) - qr) / 1055.12
    qty_net = qty_gross - gc

    st.divider()
    ec1, ec2 = st.columns(2)
    with ec1: cargo_sequence = st.text_input("Urutan Cargo Tahun Ini (contoh: 19th)", value=st.session_state["cargo_seq_input"], key="cargo_seq_input")
    with ec2: rob_akhir = st.number_input("Tuliskan ROB FSRU Aktual (m³)", value=st.session_state.get("rob_akhir_input", 124846.0), step=500.0, key="rob_akhir_input")
    
    events_to_print = [
        (t_eosp, "EOSP"), (t_nor_tend, "NOR Tendered"), (t_eta, f"POB (Pandu : {st.session_state['pilot_name_input']})"),
        (t_first_line, "First Line"), (t_allfast, "All Fast"), (t_nor_recv, "Completed Precargo Meeting (NOR received)"),
        (t_arm_conn, "Arm Connected"), (t_open_ctm, "Open CTM"), (t_start_disc, "Start Discharging"),
        (t_full_rate, "Full Rate"), (t_rate_down, "Rate Down"), (t_comp, "Discharging Completed"),
        (t_close_ctm, "Closing CTMS"), (t_disc, "All Arm Disconnected"), (t_doc, "Documentation"),
        (t_pob_out, "POB out"), (t_commence_unmooring, "Commence Unmooring"), (t_all_line_clear, "All Line Clear")
    ]
    
    email_lines = []
    current_date = None
    for t, label in events_to_print:
        event_date = t.date()
        if current_date != event_date:
            current_date = event_date
            email_lines.append(f"\n{t.strftime('%A')}, {format_email_date(t)}")
        email_lines.append(f"- {t.strftime('%H.%M')} LT           =            {label}")
        
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
    # GENERATOR FLOWCHART JPG
    # ---------------------------------------------------------
    st.markdown("### 🖼️ Auto-Generate Flowchart JPG")
    st.caption("Fungsi ini menempelkan angka ESOD terbaru Anda langsung ke dalam gambar `base_flowchart.jpg`.")

    # KOORDINAT MATI (Sesuai tebakan terbaik dari contoh)
    # Jika kurang pas, ubah angkanya langsung di dalam kamus ini (X, Y)
    burn_coords = {
        "txt_eosp_time": (135, 345),
        "txt_eosp_date": (135, 365),
        "txt_pob_in": (135, 495),
        "txt_fl_time": (360, 345),
        "txt_fl_date": (360, 365),
        "txt_af_time": (360, 420),
        "txt_af_date": (360, 440),
        "dur_pob_fl": (250, 320),
        
        # S-Shape Baris 2 (Kanan ke Kiri)
        "txt_sd_time": (1180, 520),
        "txt_sd_date": (1180, 540),
        "txt_na_time": (650, 560), # NOR Accepted (Received)
        "txt_nor_meet": (600, 540), # Pre-Cargo NOR Meet span
        "txt_warm_esd": (950, 480),
        "txt_arm_cd": (1050, 480),
        "txt_cold_esd": (1150, 480),
        "txt_open_ctm": (800, 640),
        
        "txt_full_rate_time": (1380, 345),
        "txt_full_rate_date": (1380, 365),
        "txt_rate_down_time": (1600, 345),
        "txt_rate_down_date": (1600, 365),
        "txt_cd_time": (1600, 520),
        "txt_cd_date": (1600, 540),
        
        "txt_close_ctm_time": (1800, 620),
        "txt_close_ctm_date": (1800, 640),
        "txt_arm_disc_time": (1950, 620),
        "txt_arm_disc_date": (1950, 640),
        "txt_doc_time": (1950, 460),
        "txt_pob_out_time": (2200, 345),
        "txt_pob_out_date": (2200, 365),
        
        # Summary Box Tengah (Asumsi Koordinat di tengah gambar)
        "sum_laytime_est": (850, 260),
        "sum_vol_before": (850, 280),
        "sum_vol_after": (850, 300),
        "sum_vol_loaded": (850, 320),
        "sum_loading_rate": (850, 340),
        "sum_disc_time": (850, 360),
        "sum_laytime_limit": (1100, 240)
    }

    COLOR_BLACK = (15, 23, 42) 
    img_buffer = io.BytesIO()

    def render_flowchart_image():
        base_img_path = "base_flowchart.jpg"
        font_path = "arial.TTF"

        if not os.path.exists(base_img_path): return False
        if not os.path.exists(font_path): return False
            
        try:
            img = Image.open(base_img_path).convert("RGB")
            draw = ImageDraw.Draw(img)
            
            font_time = ImageFont.truetype(font_path, 22) 
            font_dur = ImageFont.truetype(font_path, 18)  
            font_total = ImageFont.truetype(font_path, 26)

            def draw_text_centered(text, coord, font, color):
                bbox = draw.textbbox((0, 0), text, font=font)
                w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                x = coord[0] - w/2
                y = coord[1] - h/2
                draw.text((x, y), text, fill=color, font=font)

            # Tulis Jam & Tanggal
            draw_text_centered(t_eosp.strftime('%H:%M'), burn_coords["txt_eosp_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_eosp.strftime('%d-%b-%y'), burn_coords["txt_eosp_date"], font_time, COLOR_BLACK)
            draw_text_centered(f"{t_eta.strftime('%d-%b-%y')} / {t_eta.strftime('%H:%M')}", burn_coords["txt_pob_in"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_first_line.strftime('%H:%M'), burn_coords["txt_fl_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_first_line.strftime('%d-%b-%y'), burn_coords["txt_fl_date"], font_time, COLOR_BLACK)
            draw_text_centered(t_allfast.strftime('%H:%M'), burn_coords["txt_af_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_allfast.strftime('%d-%b-%y'), burn_coords["txt_af_date"], font_time, COLOR_BLACK)

            draw_text_centered(f"{t_nor_tend.strftime('%H:%M')} - {t_nor_recv.strftime('%H:%M')}", burn_coords["txt_nor_meet"], font_dur, COLOR_BLACK)
            draw_text_centered(t_open_ctm.strftime('%H:%M'), burn_coords["txt_open_ctm"], font_dur, COLOR_BLACK)
            draw_text_centered(f"to {t_arm_cd.strftime('%H:%M')}", burn_coords["txt_warm_esd"], font_dur, COLOR_BLACK)
            draw_text_centered(f"to {t_cold_esd.strftime('%H:%M')}", burn_coords["txt_arm_cd"], font_dur, COLOR_BLACK)
            draw_text_centered(f"to {t_start_disc.strftime('%H:%M')}", burn_coords["txt_cold_esd"], font_dur, COLOR_BLACK)

            draw_text_centered(t_start_disc.strftime('%H:%M'), burn_coords["txt_sd_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_start_disc.strftime('%d-%b-%y'), burn_coords["txt_sd_date"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_full_rate.strftime('%H:%M'), burn_coords["txt_full_rate_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_full_rate.strftime('%d-%b-%y'), burn_coords["txt_full_rate_date"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_rate_down.strftime('%H:%M'), burn_coords["txt_rate_down_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_rate_down.strftime('%d-%b-%y'), burn_coords["txt_rate_down_date"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_comp.strftime('%H:%M'), burn_coords["txt_cd_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_comp.strftime('%d-%b-%y'), burn_coords["txt_cd_date"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_close_ctm.strftime('%H:%M'), burn_coords["txt_close_ctm_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_close_ctm.strftime('%d-%b-%y'), burn_coords["txt_close_ctm_date"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_disc.strftime('%H:%M'), burn_coords["txt_arm_disc_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_disc.strftime('%d-%b-%y'), burn_coords["txt_arm_disc_date"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_doc.strftime('%H:%M'), burn_coords["txt_doc_time"], font_time, COLOR_BLACK)
            
            draw_text_centered(t_pob_out.strftime('%H:%M'), burn_coords["txt_pob_out_time"], font_time, COLOR_BLACK)
            draw_text_centered(t_pob_out.strftime('%d-%b-%y'), burn_coords["txt_pob_out_date"], font_time, COLOR_BLACK)

            # Tulis Summary Box
            draw_text_centered(f"{dur_laytime:.1f} hours", burn_coords["sum_laytime_est"], font_dur, COLOR_BLACK)
            draw_text_centered(f"{st.session_state['cargo_vol_input'] + v_close:,.0f} m3", burn_coords["sum_vol_before"], font_dur, COLOR_BLACK)
            draw_text_centered(f"{v_close:,.0f} m3", burn_coords["sum_vol_after"], font_dur, COLOR_BLACK)
            draw_text_centered(f"{st.session_state['cargo_vol_input']:,.0f} m3", burn_coords["sum_vol_loaded"], font_dur, COLOR_BLACK)
            draw_text_centered(f"{st.session_state['input_loading_rate_input']:,.0f} m3/hour", burn_coords["sum_loading_rate"], font_dur, COLOR_BLACK)
            draw_text_centered(f"{dur_start_comp:.1f} hours", burn_coords["sum_disc_time"], font_dur, COLOR_BLACK)
            
            batas_laytime_date = t_nor_recv + timedelta(hours=st.session_state["laytime_kontrak_input"])
            draw_text_centered(f"{batas_laytime_date.strftime('%d-%b-%y / %H:%M')}", burn_coords["sum_laytime_limit"], font_dur, COLOR_BLACK)

            img.save(img_buffer, format="JPEG", quality=95)
            img_buffer.seek(0)
            return True
        except Exception as e:
            st.error(f"Gagal memproses gambar. Error: {e}")
            return False

    if st.button("🚀 Isi Angka ke Gambar Flowchart", use_container_width=True):
        if render_flowchart_image():
            st.image(img_buffer, caption=f"Flowchart Final - LNGC {st.session_state['vessel_name_input']}", use_container_width=True)
            st.download_button(label="📥 UNDUH FLOWCHART JPG", data=img_buffer, file_name=f"Flowchart_Ops_{st.session_state['vessel_name_input']}.jpg", mime="image/jpeg", use_container_width=True)

    st.markdown("---")
    st.markdown("### 🗂️ Export Full Operations Record")
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output) as writer:
            df_gen = pd.DataFrame([
                {"Parameter": "Tanggal Cetak", "Nilai": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
                {"Parameter": "CTO On Duty", "Nilai": st.session_state["user_name"]},
                {"Parameter": "Nama Kapal", "Nilai": st.session_state["vessel_name_input"]},
                {"Parameter": "ROB Pre-Cargo Mtg (m³)", "Nilai": st.session_state["rob_precargo_input"]}
            ])
            df_gen.to_excel(writer, sheet_name='General Info', index=False)
        excel_data = output.getvalue()
        st.download_button(label="📥 DOWNLOAD FULL LOG (EXCEL)", data=excel_data, file_name="Ops_Log.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    except: pass
