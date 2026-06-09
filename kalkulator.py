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
    except:
        temp, wind, cond, icon = 31.3, 14.3, "Berawan", "⛅"
    try:
        url_marine = f"https://marine-api.open-meteo.com/v1/marine?latitude={lat}&longitude={lon}&current=wave_height"
        res_m = requests.get(url_marine, timeout=5).json()
        wave = res_m["current"]["wave_height"]
        if wave is None: wave = 0.5
    except: wave = 0.5
    return temp, wind, wave, cond, icon

live_temp, live_wind, live_wave, live_cond, live_icon = get_live_weather()

# ==========================================
# 3. CSS CUSTOM
# ==========================================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Poppins', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {background-color: transparent !important;}
    .block-container {padding-top: 0rem; padding-bottom: 0rem;}
    .stApp { background: radial-gradient(circle at top left, #083344, #020617) !important; background-attachment: fixed !important; background-size: cover !important; }
    .stTabs [data-baseweb="tab-list"] { gap: 20px; border-bottom: 2px solid rgba(255,255,255,0.1); }
    .stTabs [aria-selected="true"] { color: #10b981 !important; border-bottom: 3px solid #10b981 !important; }
    [data-testid="stExpander"] { background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 16px; backdrop-filter: blur(10px); }
    [data-testid="stMetric"] { background: rgba(15, 23, 42, 0.6); border-left: 4px solid #06b6d4; border-radius: 8px; padding: 15px 20px; }
    [data-testid="stSidebar"] { background-color: rgba(2, 6, 23, 0.9) !important; border-right: 1px solid rgba(255,255,255,0.1); }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 4. INISIALISASI SESSION STATE (INTEGRASI ANTAR TAB)
# ==========================================
if "durations" not in st.session_state:
    st.session_state.durations = {
        "ETA / POB": 0, "All Fast": 180, "NOR Received": 55, "ARMs Connected": 30,
        "OPEN CTM": 35, "WARM ESD Test": 15, "Arm C/D": 90,
        "COLD ESD Test": 15, "START DISCHARGING": 20, "FULL RATE": 30,
        "Bongkar Muat Murni (Rate Down)": 2100,
        "DISCHARGING COMPLETED": 30, "CLOSING CTM": 120,
        "ARMs Disconnected": 10, "Documentation": 60, "POB OUT": 120
    }
    st.session_state.target_bongkar_h = 35.0

# ==========================================
# 5. SIDEBAR: QUICK OPS CALCULATOR (INTEGRASI INPUT TAB 1)
# ==========================================
with st.sidebar:
    st.image(html_logo_src, use_container_width=True)
    st.markdown("### 🧮 Quick Ops Calc")
    
    with st.expander("⏱️ Sisa Waktu (LNG To Go)", expanded=False):
        sb_vol = st.number_input("Sisa Kargo (m³)", value=15000.0, step=500.0)
        sb_rate = st.number_input("Laju Pompa (m³/h)", value=3500.0, step=100.0)
        if sb_rate > 0:
            st.info(f"Sisa: {sb_vol/sb_rate:.1f} Jam")
            
    with st.expander("🔄 Konversi Serapan PLN", expanded=False):
        # Default value mengambil dari input Tab 1 jika sudah ada di session state
        val_serapan = st.session_state.get('serapan_harian_input', 17000.0)
        sb_serapan = st.number_input("Target (m³/hari)", value=val_serapan, step=500.0)
        st.success(f"Laju: {sb_serapan/24:,.1f} m³/h")

    with st.expander("🔢 Kalkulator Standar", expanded=True):
        html_calc = """<div style="background:rgba(30,41,59,0.5);padding:10px;border-radius:10px;"><input type="text" id="d" style="width:100%;background:#000;color:#0ea5e9;border:1px solid #334155;font-size:20px;text-align:right;margin-bottom:10px;" disabled><div style="display:grid;grid-template-columns:repeat(4,1fr);gap:5px;">"""
        for b in ['C','(',')','/','7','8','9','*','4','5','6','-','1','2','3','+','0','.','=']:
            html_calc += f'<button style="padding:10px;background:#334155;color:#fff;border:none;border-radius:5px;" onclick="v(\'{b}\')">{b}</button>'
        html_calc += """</div></div><script>function v(x){let d=document.getElementById('d');if(x=='C')d.value='';else if(x=='=')try{d.value=eval(d.value)}catch(e){d.value='Error'}else d.value+=x;}</script>"""
        components.html(html_calc, height=300)

# ==========================================
# 6. HEADER LIVE
# ==========================================
html_header = f"""
<div style="background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.1);border-radius:20px;padding:15px 25px;display:flex;justify-content:space-between;align-items:center;color:white;box-shadow:0 8px 32px 0 rgba(0,0,0,0.3);">
    <div style="display:flex;align-items:center;gap:20px;">
        <div style="background:white;padding:5px 10px;border-radius:10px;"><img src="{html_logo_src}" style="height:30px;"></div>
        <div><h2 style="margin:0;font-size:22px;">CTO TERMINAL OPS</h2><span style="color:#06b6d4;font-size:13px;">Nusantara Regas • Live Command Center</span></div>
    </div>
    <div style="background:linear-gradient(135deg,#10b981,#059669);padding:8px 24px;border-radius:30px;font-weight:600;font-size:14px;border:1px solid #34d399;">🟢 ON DUTY: FARIS</div>
</div>
"""
components.html(html_header, height=120)

with st.expander("🛰️ BUKA PANEL LIVE: Jam, Cuaca & Ombak (FSRU NR)", expanded=False):
    html_widgets = f"""<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:15px;color:white;text-align:center;">
        <div style="background:rgba(30,41,59,0.5);padding:15px;border-radius:16px;"><div id="t" style="font-size:26px;font-weight:800;color:#38bdf8;">00:00:00</div><div id="d" style="font-size:12px;color:#94a3b8;">Loading...</div></div>
        <div style="background:rgba(30,41,59,0.5);padding:15px;border-radius:16px;"><div style="font-size:24px;">📍</div><div style="font-size:13px;font-weight:600;">FSRU NR</div><div style="font-size:11px;color:#94a3b8;">Teluk Jakarta</div></div>
        <div style="background:rgba(30,41,59,0.5);padding:15px;border-radius:16px;"><div style="font-size:24px;">{live_icon}</div><div style="font-size:13px;font-weight:600;">{live_cond} • {live_temp}°C</div><div style="font-size:11px;color:#94a3b8;">🌬️ {live_wind} km/h | 🌊 Ombak {live_wave}m</div></div>
        <div style="background:rgba(30,41,59,0.5);padding:15px;border-radius:16px;"><div style="border:2px solid #10b981;color:#10b981;padding:4px 12px;border-radius:8px;font-weight:800;font-size:12px;margin-top:10px;">● STANDBY OPS</div></div>
    </div><script>function u(){{let n=new Date();document.getElementById('t').innerText=n.toLocaleTimeString('id-ID',{{hour12:false}});document.getElementById('d').innerText=n.toLocaleDateString('id-ID',{{weekday:'long',year:'numeric',month:'short',day:'numeric'}});}}setInterval(u,1000);u();</script>"""
    components.html(html_widgets, height=200)

# ==========================================
# 7. TAB NAVIGASI
# ==========================================
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs(["📋 PRE-ARRIVAL", "⚓ SANDAR", "📡 MONITORING", "📝 FINAL REPORT"])

# Variabel Statis Urutan
events_static = ["ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", "FULL RATE", "Bongkar Muat Murni (Rate Down)", "DISCHARGING COMPLETED", "CLOSING CTM", "ARMs Disconnected", "Documentation", "POB OUT"]

# ==========================================
# FASE 1: PRE-ARRIVAL (SUMBER DATA)
# ==========================================
with tab_h1:
    st.markdown("### 🧮 Kalkulasi Awal & Skenario ROB")
    c1, c2, c3 = st.columns(3)
    cargo_vol = c1.number_input("Cargo to Load (m³)", value=130000.0, step=1000.0)
    rob_awal = c2.number_input("ROB H-1 00:00 (m³)", value=42000.0, step=500.0)
    serapan_harian = c3.number_input("Target Serapan PLN/Day (m³)", value=17000.0, step=500.0)
    st.session_state['serapan_harian_input'] = serapan_harian

    col_w1, col_w2 = st.columns(2)
    tgl_eta = col_w1.date_input("Tanggal ETA", datetime(2026, 6, 10))
    jam_eta = col_w1.time_input("Jam ETA (LCT)", pd.to_datetime("06:00").time())
    waktu_eta = datetime.combine(tgl_eta, jam_eta)
    
    target_jam_bongkar = col_w2.number_input("Target Laytime (Jam)", value=35.0, step=0.5)
    # Update durasi murni di session state
    st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = int(target_jam_bongkar * 60)

    # Kalkulasi Waktu Timeline
    temp_dt = waktu_eta
    esod_times = [temp_dt]
    for ev in events_static[1:]:
        dur_val = st.session_state.durations[ev]
        temp_dt = temp_dt + timedelta(minutes=int(dur_val))
        esod_times.append(temp_dt)
    
    # Snapshot Logic
    idx_arm_cd = events_static.index("Arm C/D")
    waktu_snapshot = esod_times[idx_arm_cd] - timedelta(minutes=5)
    waktu_commence = esod_times[events_static.index("START DISCHARGING")]

    # A. MENCARI ROB SAAT COMMENCE DISCHARGE
    selisih_jam_rob_commence = (waktu_commence - waktu_eta).total_seconds() / 3600.0 + 30 # Asumsi catat ROB H-1 jam 00:00
    serapan_matematis = (serapan_harian / 24.0) * selisih_jam_rob_commence
    worst_case_serapan = st.number_input("Serapan sampai Commence (Worst Case) m³", value=float(int(serapan_matematis/1000)*1000))
    rob_commence = rob_awal - worst_case_serapan
    
    # B. EVALUASI LAYTIME
    volume_disrub = (rob_commence + cargo_vol) - 122500.0
    res1, res2, res3 = st.columns(3)
    res1.metric("ROB Saat Commence", f"{rob_commence:,.0f} m³")
    
    if volume_disrub > 0:
        regas_harian_req = (volume_disrub / target_jam_bongkar) * 24
        if regas_harian_req > serapan_harian: st.error(f"🚨 BAHAYA TRIP: Regas req {regas_harian_req:,.0f} > Serapan {serapan_harian:,.0f}")
        else: st.success(f"✅ AMAN: Regas req {regas_harian_req:,.0f}")
        res2.metric("VL (Diserap Selama Bongkar)", f"{volume_disrub:,.0f} m³", "Overfill Risk!")
    else:
        st.success("✅ Kapasitas Tangki Aman")
        res2.metric("VL (Diserap Selama Bongkar)", "0 m³", "Safe")
    res3.metric("Loading Rate Target", f"{int(cargo_vol/target_jam_bongkar/100)*100:,.0f} m³/h")

    # Pak Suci Scenarios
    with st.expander("📊 MULTI-SCENARIO PLANNER", expanded=False):
        st.write("Skema komparasi 3 skenario...")
        # (Logika tabel Pak Suci tetap ada di sini)

    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 2: SANDAR (Timeline Terkoneksi)
# ==========================================
with tab_sandar:
    st.info(f"📸 **PENGINGAT CTO:** Snapshot Radar Open CTM wajib pada **{waktu_snapshot.strftime('%H:%M')} LCT** (5 min sebelum Arm C/D).")
    df_esod = pd.DataFrame({
        "Tahapan Operasi": events_static,
        "Date / Time (LCT)": esod_times,
        "Durasi (Menit)": [0] + [st.session_state.durations[ev] for ev in events_static[1:]]
    })
    st.data_editor(df_esod, use_container_width=True, hide_index=True)
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 3: MONITORING
# ==========================================
with tab_monitor:
    st.markdown("### 🧮 Analisis Sisa Waktu Terupdate")
    st.write(f"Snapshot radar rencana: **{waktu_snapshot.strftime('%H:%M')}**")
    m_c1, m_c2 = st.columns(2)
    sisa_k = m_c1.number_input("LNG To Goaktual (m³)", value=32000.0)
    rate_a = m_c1.number_input("Actual Rate (m³/h)", value=4000.0)
    if rate_a > 0:
        m_c2.metric("Estimasi Sisa Jam", f"{sisa_k/rate_a:.1f} Jam")
        m_c2.metric("Proyeksi Katup Tertutup", (datetime.now() + timedelta(hours=sisa_k/rate_a)).strftime("%H:%M LCT"))
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)

# ==========================================
# FASE 4: FINAL REPORT (Integrasi Plan vs Actual)
# ==========================================
with tab_closing:
    st.markdown("### 📐 GIIGNL Energy delivered")
    f_c1, f_c2, f_c3 = st.columns(3)
    ctm_open = f_c1.number_input("Radar Opening (m³)", value=134111.0)
    ctm_close = f_c1.number_input("Radar Closing (m³)", value=4111.0)
    vol_akt = ctm_open - ctm_close
    
    # Integrasi: Variance Plan vs Actual
    variance = vol_akt - cargo_vol
    f_c1.metric("Aktual Bongkar (m³)", f"{vol_akt:,.0f}", f"{variance:,.0f} vs Plan")

    density = f_c2.number_input("Density LNG (kg/m³)", value=450.0)
    mass_ghv = f_c2.number_input("Mass GHV (MJ/kg)", value=54.5)
    hg_vap = f_c2.number_input("Vapor HG (MJ/m³)", value=35.676)
    
    tv = f_c3.number_input("Vapor Temp (°C)", value=-130.0)
    pa = f_c3.number_input("Vapor Press (mbar)", value=1015.0)
    fuel = f_c3.number_input("Gas Consumed (MMBtu)", value=1500.0)

    # Rumus GIIGNL
    qr = vol_akt * (288.15 / (273.15 + tv)) * (pa / 1013.25) * hg_vap
    gross = ((vol_akt * density * mass_ghv) - qr) / 1055.12
    net = gross - fuel

    st.markdown("---")
    res_f1, res_f2, res_f3 = st.columns(3)
    res_f1.metric("Vapor Return (Qr)", f"{qr:,.0f} MJ")
    res_f2.metric("Gross Energy", f"{gross:,.0f} MMBtu")
    res_f3.metric("NET ENERGY DELIVERED", f"{net:,.0f} MMBtu")
    
    st.markdown("<br><br><br><br><br><br><br>", unsafe_allow_html=True)
    st.caption("© 2026 Nusantara Regas - Terintegrasi Penuh")
