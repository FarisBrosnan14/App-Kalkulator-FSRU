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
# 3. CSS CUSTOM
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
</style>
""", unsafe_allow_html=True)

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
# 5. SIDEBAR: QUICK OPS CALC
# ==========================================
with st.sidebar:
    st.image(html_logo_src, use_container_width=True)
    st.markdown("### 🧮 Quick Ops Calc")
    st.caption("Akses Cepat Perhitungan Lapangan")
    st.divider()
    with st.expander("⏱️ Hitung Sisa Waktu (LNG)", expanded=False):
        sb_vol = st.number_input("Sisa Kargo (m³)", min_value=0.0, value=15000.0, step=500.0)
        sb_rate = st.number_input("Laju Pompa (m³/h)", min_value=1.0, value=3500.0, step=100.0)
        st.markdown(f"<div style='padding:10px; background:#1e293b; border-radius:5px; border-left:3px solid #0ea5e9;'><span style='color:#94a3b8; font-size:12px;'>Estimasi Sisa Jam</span><br><span style='font-size:18px; font-weight:bold; color:#0ea5e9;'>{(sb_vol/sb_rate if sb_rate > 0 else 0):.1f} Jam</span></div>", unsafe_allow_html=True)
    with st.expander("🔄 Konversi Serapan PLN", expanded=False):
        sb_serapan = st.number_input("Target (m³/hari)", min_value=0.0, value=17000.0, step=500.0)
        st.markdown(f"<div style='padding:10px; background:#1e293b; border-radius:5px; border-left:3px solid #10b981;'><span style='color:#94a3b8; font-size:12px;'>Laju Regas Aktual</span><br><span style='font-size:18px; font-weight:bold; color:#10b981;'>{(sb_serapan/24):,.1f} m³/h</span></div>", unsafe_allow_html=True)
    with st.expander("🔢 Kalkulator Standar", expanded=True):
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
    <script>setInterval(()=>{const n=new Date();t.innerText=n.toLocaleTimeString('id-ID',{hour12:false});d2.innerText=n.toLocaleDateString('id-ID',{weekday:'long',year:'numeric',month:'short',day:'numeric'})},1000);</script>
    """, height=180)

# ==========================================
# 7. MAIN NAVIGATION & INTEGRASI
# ==========================================
tab_h1, tab_sandar, tab_monitor, tab_closing = st.tabs([
    "PHASE 1: PRE-ARRIVAL (H-1)", "PHASE 2: BERTHING (DAY 1)", "PHASE 3: MONITORING (DAY 2)", "PHASE 4: FINAL REPORT (DAY 3)"
])

# FASE 1 INPUTS 
with tab_h1:
    with st.expander("📌 TO-DO LIST: H-1 Sebelum STS (Setelah Email ETA 24H)", expanded=False):
        col_td1, col_td2, col_td3 = st.columns(3)
        with col_td1:
            st.info("""
            **🗣️ 1. COORDINATION**
            * Update WAG Monitoring: Posisi LNGC & Cuaca.
            * Update WAG Patroli Laut: Rencana waktu STS.
            * Hubungi Dispatcher JCC: Rencana serapan saat discharging.
            * Hubungi PLN & Surveyor: Pastikan perwakilan Onboard.
            * Hubungi PLN EPI: Pastikan Surat Perintah Discharge terkirim.
            """)
        with col_td2:
            st.success("""
            **📝 2. DRAFT REPORT**
            * Susun Loading / Unloading Plan.
            * Siapkan List Lampiran Personel Onboard.
            * Siapkan Lampiran Persyaratan Onboard LNGC.
            * Draft Flowchart Estimation Discharging (Metode Pak Suci).
            * Minta TTD JoA & CoU dari Master NRS.
            """)
        with col_td3:
            st.warning("""
            **📧 3. SEND EMAIL**
            * Kirim Permission Onboard & Pemakaian Boat Hutasuhut.
            * Kirim Dokumen JoA (Joint Operating Agreement) & CoU.
            * Kirim Dokumen Loading / Unloading Plan ke pihak terkait.
            """)

    st.markdown("### 🧮 Kalkulasi Awal & Skenario ROB")
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
        
    target_jam_bongkar = st.number_input("Target Laytime / Durasi Pompa (Jam)", min_value=1.0, value=35.0, step=0.5)
    
    st.session_state.durations["Bongkar Muat Murni (Rate Down)"] = int(target_jam_bongkar * 60)

    # LOGIKA A, B, C (ALGORITMA USER)
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
    res3.metric("Loading Rate Target", f"{int((cargo_vol/target_jam_bongkar)/100)*100:,.0f} m³/h")

    # PAK SUCI SCENARIOS
    with st.expander("📊 MULTI-SCENARIO PLANNER (Metode Pak Suci)", expanded=False):
        def build_sc(c_sc, l_sc, r_sc):
            t_start = waktu_eta + timedelta(hours=8)
            t_comp = t_start + timedelta(hours=l_sc)
            t_out = t_comp + timedelta(hours=5)
            return [waktu_eta.strftime("%d %b / %H:%M"), t_start.strftime("%d %b / %H:%M"), f"{c_sc:,.0f}", f"{l_sc}", t_comp.strftime("%d %b / %H:%M"), t_out.strftime("%d %b / %H:%M")]
        
        st.dataframe(pd.DataFrame({
            "Parameter": ["POB (ETA)", "Est. Start Discharge", "Cargo to Load", "Discharge Time (H)", "Est. Complete", "Est. POB Out"],
            "1st Est": build_sc(cargo_vol, target_jam_bongkar, 709),
            "2nd Est": build_sc(cargo_vol, 46.3, 577),
            "3rd Est": build_sc(120000, 41.4, 561)
        }), use_container_width=True, hide_index=True)

    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# PROYEKSI WAKTU ESOD (INTEGRASI TAB 2 & 3)
events_list = ["ETA / POB", "All Fast", "NOR Received", "ARMs Connected", "OPEN CTM", "WARM ESD Test", "Arm C/D", "COLD ESD Test", "START DISCHARGING", "FULL RATE", "Bongkar Muat Murni (Rate Down)", "DISCHARGING COMPLETED", "CLOSING CTM", "ARMs Disconnected", "Documentation", "POB OUT"]
temp_dt = waktu_eta
esod_times = [temp_dt]
for ev in events_list[1:]:
    temp_dt += timedelta(minutes=st.session_state.durations[ev])
    esod_times.append(temp_dt)
waktu_snapshot = esod_times[events_list.index("Arm C/D")] - timedelta(minutes=5)

# FASE 2: BERTHING (DAY 1)
with tab_sandar:
    with st.expander("📌 TO-DO LIST: Day 1 (Sandar & Mulai Bongkar)", expanded=False):
        st.markdown(f"""
        * **1. Trip to FSRU:** Berangkat menuju fasilitas menggunakan Transport Boat.
        * **2. Proses STS - All Fast:** Pantau manuver kapal merapat hingga tali tambat terpasang sempurna.
        * **3. Pre-Cargo Meeting:** Lakukan rapat koordinasi keselamatan & operasional dengan Kapten LNGC.
        * **4. OPEN CTM:** **AMBIL SNAPSHOT RADAR** tepat pada pukul **{waktu_snapshot.strftime('%H:%M')} LCT** (5 Menit sebelum Arm Cooldown).
        * **5. Preparation - Start Discharging:** Supervisi Warm ESD, Arm Cooldown, Cold ESD, hingga Start Discharging.
        * **6. Send Email Report:** Kirimkan laporan bahwa bongkar muat telah mencapai *Full Rate*.
        """)

    st.info(f"📸 **PENGINGAT:** Snapshot Radar Open CTM wajib diambil pada pukul **{waktu_snapshot.strftime('%H:%M')} LCT**.")
    df_esod = pd.DataFrame({"Tahapan": events_list, "Waktu (LCT)": esod_times, "Durasi (Min)": [0] + [st.session_state.durations[e] for e in events_list[1:]]})
    ed_table = st.data_editor(df_esod, column_config={"Tahapan": st.column_config.TextColumn(disabled=True)}, use_container_width=True, hide_index=True, key="esod_ed")
    if st.session_state.esod_ed["edited_rows"]:
        for r, change in st.session_state.esod_ed["edited_rows"].items():
            if "Durasi (Min)" in change: st.session_state.durations[events_list[int(r)]] = change["Durasi (Min)"]
        st.rerun()
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# FASE 3: MONITORING (DAY 2)
with tab_monitor:
    with st.expander("📌 TO-DO LIST: Day 2 (Monitoring Operasi)", expanded=False):
        st.markdown("""
        * **1. Monitoring Discharging:** Pantau terus parameter tekanan dan suhu dari Control Room.
        * **2. Coordination - Update POB Out:** Lakukan pembaruan (update) jam estimasi pelepasan sandar (POB Out) ke pihak relevan.
        * **3. Update LNG To Go:** Secara berkala komunikasikan sisa kargo yang belum terbongkar.
        * **4. Rate Down - Completed:** Koordinasikan penurunan laju pompa (Rate Down) saat kargo menipis hingga status *Discharging Completed*.
        * **5. Persiapan Akhir:** Mulai persiapkan *Possibility of Closing CTM*, prosedur *Disconnect Arm*, dan *Documentation*.
        """)

    st.markdown(f"**Snapshot Radar:** {waktu_snapshot.strftime('%H:%M')} LCT")
    mt1, mt2 = st.columns(2)
    togo_vol = mt1.number_input("Volume LNG To Go (m³)", value=32000.0)
    togo_rate = mt1.number_input("Actual Loading Rate (m³/h)", value=4000.0)
    sisa_h = togo_vol / togo_rate if togo_rate > 0 else 0
    mt2.metric("Sisa Waktu Pemompaan", f"{sisa_h:.1f} Jam")
    mt2.metric("Estimasi Selesai", (datetime.now() + timedelta(hours=sisa_h)).strftime("%H:%M LCT"))
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)

# FASE 4: FINAL REPORT (DAY 3)
with tab_closing:
    with st.expander("📌 TO-DO LIST: Day 3 (Selesai & Pelaporan)", expanded=False):
        st.markdown("""
        * **1. Final Ops:** Draining -> Purging -> **CLOSING CTM** -> Arm Disconnect -> Penyelesaian Documentation (Timesheet, dll).
        * **2. Disembark:** Kapal melepas sandar (POB Out) -> Unmooring -> Trip kembali ke darat (Pos ISPS).
        * **3. Send Email Report Cargo Document:** Kirimkan hasil rekap Excel CTMS resmi (unduh dari bawah) ke departemen Komersial & Manajemen.
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

    qr = v_act * (288.15 / (273.15 + vt)) * (vp / 1013.25) * vghv if (273.15 + vt) != 0 else 0
    qty_gross = ((v_act * dens * mghv) - qr) / 1055.12
    qty_net = qty_gross - gc

    st.divider()
    rf1, rf2, rf3 = st.columns(3)
    rf1.metric("Vapor Return (Qr)", f"{qr:,.0f} MJ")
    rf2.metric("Gross Energy", f"{qty_gross:,.0f} MMBtu")
    rf3.metric("NET ENERGY DELIVERED", f"{qty_net:,.0f} MMBtu")
    
    st.download_button("📊 Download Official Report", data=io.BytesIO().getvalue(), file_name="CTM_Report.xlsx")
    st.markdown("<br><br><br><br>", unsafe_allow_html=True)
