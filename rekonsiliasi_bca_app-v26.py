import streamlit as st
import re

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        safe_rerun()

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io
from PIL import Image

def safe_float(val):
    if val is None or pd.isna(val):
        return 0.0
    if isinstance(val, (int, float, np.number)):
        return float(val)
    try:
        s = str(val).replace(",", "").replace("Rp", "").replace("rp", "").strip()
        return float(s) if s else 0.0
    except (ValueError, TypeError):
        return 0.0


def generate_combined_staff_str(row):
    staff_list = []
    # Scan all possible staff columns
    for col_key in ["STAFF_1", "STAFF_2", "STAFF_3", "STAFF_4", "STAFF_5", "STAFF_LAINNYA", "PETUGAS_TAMBAHAN", "STAFF_EXTRA", "DAFTAR_PETUGAS"]:
        if col_key in row and pd.notna(row[col_key]):
            val = str(row[col_key]).strip()
            if val and val not in ["-", "nan", "None"]:
                parts = [p.strip() for p in re.split(r'[,\n;]+', val) if p.strip() and p.strip() not in ["-", "nan", "None"]]
                for p in parts:
                    if p not in staff_list:
                        staff_list.append(p)
    
    driver_val = ""
    if "DRIVER" in row and pd.notna(row["DRIVER"]):
        d_str = str(row["DRIVER"]).strip()
        if d_str and d_str not in ["-", "nan", "None"]:
            driver_val = d_str
            
    if not staff_list and not driver_val:
        return "-"
        
    formatted_items = []
    for idx, s_name in enumerate(staff_list):
        formatted_items.append(f"👤 {idx+1}. {s_name}")
        
    if driver_val:
        formatted_items.append(f"🚚 Driver: {driver_val}")
        
    return "\n".join(formatted_items)

def ensure_numeric_df(df):
    if df.empty:
        return df
    num_cols = ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "BDC", "NON_BDC", "TOTAL_UK", "NOMINAL_SELISIH", "NOMINAL_EJ", "STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR", "STOK_SISLOK_AKHIR", "FISIK_KAS_ACTUAL", "SELISIH_STOK", "LEMBAR", "TOTAL_RUPIAH"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.replace("Rp", "").str.strip(), errors="coerce").fillna(0)
    return df

# ---------------------------------------------------------
# Page Configuration & Styling (BCA Corporate Theme)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistem Rekonsiliasi Kas BCA + Tampilan Full Staff Lengkap",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Executive BCA Branding & Data Display
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #002B49 0%, #00529C 50%, #0072CE 100%);
        padding: 24px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 10px 20px rgba(0, 43, 73, 0.15);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .main-header h1 {
        color: #FFFFFF !important;
        margin: 0;
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }
    .main-header p {
        color: #D1E5F7 !important;
        margin: 6px 0 0 0;
        font-size: 14px;
        font-weight: 500;
    }
    .status-badge {
        background-color: rgba(255, 255, 255, 0.2);
        color: #FFFFFF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        display: inline-block;
        margin-top: 10px;
    }
    .card-box {
        background: #FFFFFF;
        border-radius: 10px;
        padding: 18px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 15px;
    }
    .month-badge {
        background-color: #00529C;
        color: white;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: bold;
    }
    .empty-banner {
        background: #FEF3C7;
        border-left: 5px solid #F59E0B;
        padding: 15px 20px;
        border-radius: 8px;
        color: #92400E;
        margin-bottom: 20px;
    }
    .stTable {
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Empty Dataframe Creators & Default Loaders
# ---------------------------------------------------------
def create_empty_rekon():
    cols = ["WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"]
    return pd.DataFrame(columns=cols)

def create_empty_cencon():
    return pd.DataFrame(columns=["WSID", "LOKASI", "TANGGAL", "JAM", "BDC", "NON_BDC", "STATUS", "KETERANGAN"])

def create_empty_uk():
    return pd.DataFrame(columns=["WSID", "LOKASI", "TANGGAL", "JAM", "TIPE_UK", "BDC", "NON_BDC", "TOTAL_UK", "KETERANGAN"])

def create_empty_ebos():
    return pd.DataFrame(columns=["NO_LAPORAN", "WSID", "LOKASI", "TANGGAL", "TIPE_MESIN", "NOMINAL_SELISIH", "STATUS_EBOS", "CATATAN_EBOS"])

def create_empty_ej():
    return pd.DataFrame(columns=["WSID", "LOKASI", "TANGGAL_EJ", "JAM_TX", "NO_KARTU_REK", "NOMINAL_EJ", "STATUS_EJ", "CATATAN_EJ"])

def create_empty_sislok():
    return pd.DataFrame(columns=["WSID", "LOKASI", "TANGGAL_AUDIT", "STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR", "STOK_SISLOK_AKHIR", "FISIK_KAS_ACTUAL", "SELISIH_STOK", "STATUS_REVIEW"])

def create_empty_kolong():
    return pd.DataFrame(columns=["WSID", "LOKASI", "TANGGAL_TEMUAN", "DENOMINASI", "LEMBAR", "TOTAL_RUPIAH", "LOKASI_TEMUAN", "KETERANGAN"])

def load_default_rekon():
    data = [
        # Z5UM - Multiple Staff Entries matching ost.png
        {
            "WSID": "Z5UM", "LOK": "BCA", "LOKASI": "PURWOSARI CRM 2", "Mesin": "O-CRM",
            "BULAN": "Juni 2026",
            "TGL_INS": "2026-06-27 19:51", "TGL_REM": "2026-06-27 20:07", "CASH_POS": 317400, "SETOR": 316800,
            "SEL_AWAL": -600, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 500,000 (UK Siclus d.100 x 1 lbr)",
            "TEST_CASH": "Rp 100,000 (NON-BDC)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 500,600 | Fisik: 500,500",
            "STAFF_1": "BAYU OKTA PURWANTO", "STAFF_2": "AKHMAD RIZA MAULANA",
            "STAFF_3": "-", "DRIVER": "-",
            "ACTIVITY": "0:16:59 BONGKAR ISI",
            "CATATAN_PROSES": "proses normal, uk d.100 x 1 lbr",
            "TANGGAPAN_BCA": "Selisih Awal : -600\nUK : 500\nSelisih Akhir : -100"
        },
        {
            "WSID": "Z5UM", "LOK": "BCA", "LOKASI": "CRM PURWOSARI 2", "Mesin": "O-CRM",
            "BULAN": "Juni 2026",
            "TGL_INS": "2026-06-27 21:34", "TGL_REM": "2026-06-27 21:43", "CASH_POS": 317400, "SETOR": 316800,
            "SEL_AWAL": -600, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 500,000 (UK Siclus d.100 x 1 lbr)",
            "TEST_CASH": "Rp 100,000 (NON-BDC)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 500,600 | Fisik: 500,500",
            "STAFF_1": "MUHAMMAD RIZAL MUZAKHI", "STAFF_2": "RAKA EDO DWI MARDANY",
            "STAFF_3": "-", "DRIVER": "-",
            "ACTIVITY": "0:08:53 06-DISPENSER",
            "CATATAN_PROSES": "Pengecekan modul dispenser",
            "TANGGAPAN_BCA": "Tes cash ok"
        },
        {
            "WSID": "Z5UM", "LOK": "BCA", "LOKASI": "CRM PURWOSARI 2", "Mesin": "O-CRM",
            "BULAN": "Juni 2026",
            "TGL_INS": "2026-06-29 06:34", "TGL_REM": "2026-06-29 06:41", "CASH_POS": 317400, "SETOR": 316800,
            "SEL_AWAL": -600, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 500,000 (UK Siclus d.100 x 1 lbr)",
            "TEST_CASH": "Rp 100,000 (NON-BDC)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 500,600 | Fisik: 500,500",
            "STAFF_1": "YOYOK BUDI RAKHMAN", "STAFF_2": "ADAM REYHAN HERLAMBANG (SGI)",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER",
            "ACTIVITY": "0:07:00 06-DISPENSER",
            "CATATAN_PROSES": "Audit lapangan dispenser",
            "TANGGAPAN_BCA": "Selesai audit"
        },
        {
            "WSID": "Z5UM", "LOK": "BCA", "LOKASI": "CRM PURWOSARI 2", "Mesin": "O-CRM",
            "BULAN": "Juni 2026",
            "TGL_INS": "2026-06-29 17:54", "TGL_REM": "2026-06-29 19:10", "CASH_POS": 317400, "SETOR": 316800,
            "SEL_AWAL": -600, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 500,000 (UK Siclus d.100 x 1 lbr)",
            "TEST_CASH": "Rp 100,000 (NON-BDC)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 500,600 | Fisik: 500,500",
            "STAFF_1": "EEND MUHAIRIZ ATHA", "STAFF_2": "ASSYAVI ALIYULLOH M (DRIVER)",
            "STAFF_3": "-", "DRIVER": "ASSYAVI ALIYULLOH M",
            "ACTIVITY": "1:16:35 BONGKAR ISI",
            "CATATAN_PROSES": "Proses bongkar isi kas rutin",
            "TANGGAPAN_BCA": "Penyelesaian bongkar isi"
        },
        # ZM16
        {
            "WSID": "ZM16", "LOK": "T", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "Mesin": "ITM",
            "BULAN": "Juli 2026",
            "TGL_INS": "2026-06-25", "TGL_REM": "2026-07-07", "CASH_POS": 342500, "SETOR": 339150,
            "SEL_AWAL": -3350, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 3,350,000 (UK TC d.50 x 67 lbr)",
            "TEST_CASH": "Rp 50,000 (BDC & NON-BDC)",
            "CLOSE_OPEN_CENCON": "Open",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 403,350 | Fisik: 403,250",
            "STAFF_1": "YOYOK BUDI RAKHMAN", "STAFF_2": "ADAM REYHAN HERLAMBANG",
            "STAFF_3": "EEND MUHAIRIZ ATHA", "DRIVER": "SGI VENDOR",
            "ACTIVITY": "25/06/26 21:34 - PENGISIAN KAS",
            "CATATAN_PROSES": "UK d.50 x 67 lbr, Keluhan nasabah teridentifikasi",
            "TANGGAPAN_BCA": "Selisih Awal : -3,350\nUK : 3,350\nKeluhan Nsb : -100 tgl 25/06 jam 13:20\nSelisih Akhir : -100"
        },
        # Z0X2
        {
            "WSID": "Z0X2", "LOK": "T", "LOKASI": "IDM SUDIMORO MALANG", "Mesin": "CRMHYO",
            "BULAN": "Juli 2026",
            "TGL_INS": "2026-07-04", "TGL_REM": "2026-07-10", "CASH_POS": 649850, "SETOR": 649800,
            "SEL_AWAL": -50, "SEL_AKHIR": -50,
            "UK_BDC": "Rp 0 (Sesuai)",
            "TEST_CASH": "Rp 100,000 (Tes Cash OK)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Balanced (-50)",
            "REVIEW_STOCK": "Sislok: 600,050 | Fisik: 600,000",
            "STAFF_1": "BAMBANG HERMANTO", "STAFF_2": "DEDI KURNIAWAN",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER 02",
            "ACTIVITY": "04/07/26 18:30 - BONGKAR ISI",
            "CATATAN_PROSES": "Sesuai selisih fisik -50",
            "TANGGAPAN_BCA": "Selisih Awal : -50\nSelisih Akhir : -50"
        }
    ]
    df = pd.DataFrame(data)
    return df

# Initialize Session States
if "df_rekon" not in st.session_state:
    st.session_state.df_rekon = create_empty_rekon()
if "df_cencon" not in st.session_state:
    st.session_state.df_cencon = create_empty_cencon()
if "df_uk" not in st.session_state:
    st.session_state.df_uk = create_empty_uk()
if "df_ebos" not in st.session_state:
    st.session_state.df_ebos = create_empty_ebos()
if "df_ej" not in st.session_state:
    st.session_state.df_ej = create_empty_ej()
if "df_sislok" not in st.session_state:
    st.session_state.df_sislok = create_empty_sislok()
if "df_kolong" not in st.session_state:
    st.session_state.df_kolong = create_empty_kolong()
if "image_store" not in st.session_state:
    st.session_state.image_store = {}
if "target_nav_menu" in st.session_state and st.session_state.target_nav_menu:
    st.session_state["nav_menu"] = st.session_state.target_nav_menu
    st.session_state.target_nav_menu = None
elif "nav_menu" not in st.session_state:
    st.session_state["nav_menu"] = "📋 Tabel Utama (Complete Audit)"

# Standardize Columns Security Check
def sanitize_df(df, required_cols):
    if df.empty:
        return pd.DataFrame(columns=required_cols)
    for col in required_cols:
        if col not in df.columns:
            matches = [c for c in df.columns if c.strip().lower() == col.strip().lower()]
            if matches:
                df.rename(columns={matches[0]: col}, inplace=True)
            else:
                df[col] = "-"
    return ensure_numeric_df(df)

# Auto fill/extract BULAN from TGL_REM (Tanggal Removal) in Indonesian Month Format
def auto_fill_bulan(df, date_col="TGL_REM"):
    if df.empty:
        return df
    if "BULAN" not in df.columns:
        df["BULAN"] = "-"
    
    month_names = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
    
    rem_col = None
    for c in df.columns:
        if c.strip().lower() in ["tgl_rem", "tgl_removal", "tanggal_rem", "tanggal_removal"]:
            rem_col = c
            break
    if not rem_col:
        rem_col = date_col

    for idx, row in df.iterrows():
        val = str(row.get("BULAN", "")).strip()
        if val in ["-", "", "nan", "None"] or pd.isna(row.get("BULAN")):
            target_date = row.get(rem_col, None)
            if pd.isna(target_date) or str(target_date).strip() in ["", "-", "nan", "None"]:
                target_date = row.get("TGL_INS", None)
            
            try:
                dt = pd.to_datetime(target_date, dayfirst=True)
                if not pd.isna(dt):
                    df.at[idx, "BULAN"] = f"{month_names[dt.month]} {dt.year}"
                else:
                    df.at[idx, "BULAN"] = "Juli 2026"
            except:
                df.at[idx, "BULAN"] = "Juli 2026"
    return df

df_rekon = sanitize_df(st.session_state.df_rekon, [
    "WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", 
    "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", 
    "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", "STAFF_LAINNYA", 
    "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
])

df_rekon = auto_fill_bulan(df_rekon, "TGL_REM")
st.session_state.df_rekon = df_rekon

# ---------------------------------------------------------
# Sidebar Navigation & Global Filters
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Bank_Central_Asia_logo.svg", width=180)
st.sidebar.title("Navigasi Operasional BCA")

menu = st.sidebar.radio(
    "Pilih Modul / Tabel:",
    [
        "📊 Dashboard Executive Overview",
        "📋 Tabel Utama (Complete Audit)",
        "👥 Multi-Staff Operasional per WSID",
        "💵 Close / Open Cencon & Tes Cash",
        "🔄 UK TC, UK BDC & UK Siclus",
        "📑 Laporan EBOS",
        "💻 Rekon EJ (Electronic Journal)",
        "📦 Rekon Sislok & Review Stock",
        "🪙 Uang Kolong & Temuan Fisik",
        "📸 Unggah & Galeri Foto Bukti",
        "🛠️ Kelola Data (CRUD Operations)",
        "➕ Input & Tambah Data Terpadu",
        "📁 Ekspor & Impor Data Excel"
    ],
    key="nav_menu"
)

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ Kelola Status Data Tabel")
col_sb1, col_sb2 = st.columns(2)
with col_sb1:
    if st.sidebar.button("🗑️ Kosongkan Data", use_container_width=True):
        st.session_state.df_rekon = create_empty_rekon()
        st.session_state.df_cencon = create_empty_cencon()
        st.session_state.df_uk = create_empty_uk()
        st.session_state.df_ebos = create_empty_ebos()
        st.session_state.df_ej = create_empty_ej()
        st.session_state.df_sislok = create_empty_sislok()
        st.session_state.df_kolong = create_empty_kolong()
        st.session_state.image_store = {}
        st.sidebar.success("Seluruh data tabel berhasil dikosongkan!")
        safe_rerun()

with col_sb2:
    if st.sidebar.button("🔄 Muat Default", use_container_width=True):
        st.session_state.df_rekon = load_default_rekon()
        st.sidebar.success("Data sampel default berhasil dimuat!")
        safe_rerun()

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Filter Global Terminal & Periode")

all_mesin = df_rekon["Mesin"].unique().tolist() if "Mesin" in df_rekon.columns and not df_rekon.empty else ["O-CRM", "ITM", "CRMHYO", "ACH"]
all_lok = df_rekon["LOK"].unique().tolist() if "LOK" in df_rekon.columns and not df_rekon.empty else ["BCA", "T"]
all_bulan = sorted(df_rekon["BULAN"].unique().tolist()) if "BULAN" in df_rekon.columns and not df_rekon.empty else ["Juni 2026", "Juli 2026", "Agustus 2026"]

bulan_filter = st.sidebar.multiselect("📅 Filter Bulan Laporan:", options=all_bulan, default=all_bulan)
mesin_filter = st.sidebar.multiselect("📟 Tipe Mesin Terminal:", options=all_mesin, default=all_mesin)
lok_filter = st.sidebar.multiselect("🏢 Pengelola (LOK):", options=all_lok, default=all_lok)

if not df_rekon.empty:
    filtered_df = df_rekon[
        (df_rekon["Mesin"].isin(mesin_filter)) &
        (df_rekon["LOK"].isin(lok_filter)) &
        (df_rekon["BULAN"].isin(bulan_filter))
    ]
else:
    filtered_df = df_rekon.copy()

# ---------------------------------------------------------
# Executive Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>BCA ATM Reconciliation & Integrated Operational System</h1>
            <p>Sistem Pengawasan Rekonsiliasi Kas, Audit Staff per WSID, UK BDC, Tes Cash, Cencon & Sislok Stock</p>
        </div>
        <div style="text-align: right;">
            <span class="status-badge">🟢 LIVE RECONCILIATION</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if df_rekon.empty:
    st.markdown("""
    <div class="empty-banner">
        💡 <b>Status Tabel Saat Ini: KOSONG (Siap Untuk Input Data Baru)</b><br>
        Seluruh tabel rekonsiliasi kas saat ini dalam kondisi kosong. Anda dapat langsung menginput data baru melalui menu <b>➕ Input & Tambah Data Terpadu</b> atau mengunggah file Excel master pada menu <b>📁 Ekspor & Impor Data Excel</b>.
    </div>
    """, unsafe_allow_html=True)

# Helper for Safe Formatting in Streamlit Dataframe
def display_styled_df(df, num_cols):
    if df.empty:
        st.info("ℹ️ Tabel ini saat ini masih kosong. Silakan tambahkan data baru melalui menu Input Data atau Upload File Excel.")
        return
    styler = df.style.format({c: "{:,.0f}" for c in num_cols if c in df.columns})
    
    def highlight_neg(val):
        if isinstance(val, (int, float)) and val < 0:
            return 'color: #E11D48; font-weight: bold; background-color: #FFE4E6;'
        return ''
    
    if hasattr(styler, "map"):
        styled = styler.map(highlight_neg, subset=[c for c in num_cols if c in df.columns])
    else:
        styled = styler.applymap(highlight_neg, subset=[c for c in num_cols if c in df.columns])
    
    st.dataframe(styled, use_container_width=True)

# ---------------------------------------------------------
# MODUL 1: DASHBOARD EXECUTIVE OVERVIEW
# ---------------------------------------------------------
if menu == "📊 Dashboard Executive Overview":
    st.subheader("📌 Ringkasan Eksekutif Rekonsiliasi Kas & Operasional Multi-Bulan")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Terminal", f"{len(filtered_df['WSID'].unique()) if not filtered_df.empty else 0} Unit")
    with col2:
        tot_pos = safe_float(filtered_df["CASH_POS"].sum()) * 1000 if "CASH_POS" in filtered_df.columns and not filtered_df.empty else 0
        st.metric("Total Cash Position", f"Rp {tot_pos:,.0f}")
    with col3:
        tot_setor = safe_float(filtered_df["SETOR"].sum()) * 1000 if "SETOR" in filtered_df.columns and not filtered_df.empty else 0
        st.metric("Total Disetor", f"Rp {tot_setor:,.0f}")
    with col4:
        tot_sel_awal = safe_float(filtered_df["SEL_AWAL"].sum()) * 1000 if "SEL_AWAL" in filtered_df.columns and not filtered_df.empty else 0
        st.metric("Total Selisih Awal", f"Rp {tot_sel_awal:,.0f}", delta=f"{tot_sel_awal:,.0f}", delta_color="inverse")
    with col5:
        tot_sel_akhir = safe_float(filtered_df["SEL_AKHIR"].sum()) * 1000 if "SEL_AKHIR" in filtered_df.columns and not filtered_df.empty else 0
        st.metric("Total Selisih Akhir", f"Rp {tot_sel_akhir:,.0f}", delta=f"{tot_sel_akhir:,.0f}", delta_color="inverse")

    st.markdown("---")

    if not filtered_df.empty:
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.markdown("### 📊 Posisi Kas System vs Realisasi Setor (per WSID)")
            fig_bar = px.bar(
                filtered_df,
                x="WSID",
                y=["CASH_POS", "SETOR"],
                barmode="group",
                labels={"value": "Nominal (Ribu Rp)", "variable": "Indikator"},
                color_discrete_map={"CASH_POS": "#00529C", "SETOR": "#10B981"},
                template="plotly_white"
            )
            fig_bar.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

        with col_g2:
            st.markdown("### 🍩 Sebaran Tipe Mesin Operasional")
            fig_pie = px.pie(
                filtered_df,
                names="Mesin",
                values="CASH_POS",
                hole=0.4,
                color_discrete_sequence=["#00529C", "#0072CE", "#10B981", "#F59E0B"],
                template="plotly_white"
            )
            fig_pie.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=350)
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("ℹ️ Belum ada data untuk ditampilkan di Dashboard. Silakan tambahkan atau unggah data Excel terlebih dahulu.")

# ---------------------------------------------------------
# MODUL 2: TABEL UTAMA COMPLETE AUDIT (PER BULAN)
# ---------------------------------------------------------
elif menu == "📋 Tabel Utama (Complete Audit)":
    st.subheader("📋 Rekonsiliasi Kas Utama (Tabel Aksi: Direct Edit, Update & Delete)")

    if "upload_success_msg" in st.session_state and st.session_state.upload_success_msg:
        st.success(st.session_state.upload_success_msg)
        del st.session_state["upload_success_msg"]

    # Quick Upload Image Banner on Main Table
    with st.expander("📤 Upload / Lampirkan Foto Bukti Baru di Menu Utama"):
        col_m_up1, col_m_up2 = st.columns([1, 1])
        with col_m_up1:
            m_target_wsid = st.text_input("WSID Target Foto:", "")
            m_file_up = st.file_uploader("Pilih File Foto (PNG / JPG / JPEG):", type=["png", "jpg", "jpeg"], key="up_main_menu")
            if m_file_up is not None and m_target_wsid:
                st.session_state.image_store[m_target_wsid] = m_file_up.read()
                st.success(f"Foto bukti untuk WSID {m_target_wsid} berhasil diunggah!")
                safe_rerun()

    if not filtered_df.empty:
        st.markdown("### 📅 Ringkasan Selisih Kas Per Bulan")
        if "BULAN" in filtered_df.columns:
            bulan_list = sorted(filtered_df["BULAN"].unique().tolist())
            cols_m = st.columns(max(len(bulan_list), 1))
            
            for idx, b_name in enumerate(bulan_list):
                b_df = filtered_df[filtered_df["BULAN"] == b_name]
                b_sel_awal = safe_float(b_df["SEL_AWAL"].sum()) * 1000
                b_sel_akhir = safe_float(b_df["SEL_AKHIR"].sum()) * 1000
                b_count = len(b_df["WSID"].unique())
                
                with cols_m[idx % len(cols_m)]:
                    st.markdown(f"""
                    <div class="card-box" style="border-top: 4px solid #00529C;">
                        <span class="month-badge">🗓️ {b_name}</span>
                        <p style="margin-top: 8px; font-size: 13px; color: #475569;">Total Unit: <b>{b_count} Terminal</b></p>
                        <p style="margin: 0; font-size: 13px;">Selisih Awal: <b style="color: #E11D48;">Rp {b_sel_awal:,.0f}</b></p>
                        <p style="margin: 0; font-size: 13px;">Selisih Akhir: <b style="color: #059669;">Rp {b_sel_akhir:,.0f}</b></p>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")

    col_srch, col_m_select, col_mode = st.columns([2, 1, 1.2])
    with col_srch:
        search_kw = st.text_input("🔍 Cari WSID, Lokasi, Bulan, Status UK BDC, Tes Cash, atau Staff:", "")
    with col_m_select:
        selected_month_filter = st.selectbox("📅 Filter Khusus Bulan Tabel:", ["Semua Bulan"] + all_bulan)
    with col_mode:
        table_mode = st.radio("🛠️ Mode Tampilan Tabel:", ["👁️ Mode Format", "✏️ Mode Data Editor"], horizontal=True)

    disp_df = filtered_df.copy()
    
    if selected_month_filter != "Semua Bulan" and not disp_df.empty:
        disp_df = disp_df[disp_df["BULAN"] == selected_month_filter]

    if search_kw and not disp_df.empty:
        search_masks = [disp_df[col].astype(str).str.contains(search_kw, case=False, na=False) for col in disp_df.columns]
        if search_masks:
            mask = pd.concat(search_masks, axis=1).any(axis=1)
            disp_df = disp_df[mask]

    if not disp_df.empty:
        disp_df["DAFTAR_STAFF_LENGKAP"] = disp_df.apply(generate_combined_staff_str, axis=1)

    predefined_cols = [
        "WSID", "BULAN", "LOK", "LOKASI", "Mesin", "TGL_INS", "TGL_REM", 
        "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR",
        "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", "REKON_SISLOK", "REVIEW_STOCK",
        "DAFTAR_STAFF_LENGKAP", "STAFF_1", "STAFF_2", "STAFF_3", "STAFF_LAINNYA", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
    ]
    cols_exist = [c for c in predefined_cols if c in disp_df.columns] + [c for c in disp_df.columns if c not in predefined_cols]

    if table_mode == "👁️ Mode Format":
        display_styled_df(disp_df[cols_exist], ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "BDC", "NON_BDC", "TOTAL_UK", "NOMINAL_SELISIH", "STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR"])
    else:
        st.info("✏️ **Mode Data Editor Interaktif**: Anda dapat mengubah isi sel tabel secara langsung. Klik tombol di bawah setelah mengedit untuk menyimpan ke sistem.")
        edited_table = st.data_editor(
            disp_df[cols_exist],
            num_rows="dynamic",
            key="main_data_editor",
            use_container_width=True
        )
        if st.button("💾 [SIMPAN EDITS] Update Perubahan Tabel Utama", type="primary"):
            st.session_state.df_rekon = edited_table
            st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, "TGL_REM")
            st.session_state.upload_success_msg = "🎉 Perubahan data tabel utama berhasil disimpan!"
            safe_rerun()

    # Expander for Multi-Staff View in Main Table
    if not disp_df.empty:
        st.markdown("---")
        with st.expander("👥 Rincian Semua Staff Operasional Per WSID (Multi-Staff View)", expanded=False):
            wsid_opt_main = [str(w) for w in disp_df["WSID"].unique().tolist()]
            sel_main_wsid = st.selectbox("Pilih WSID Terminal untuk Audit Staff:", wsid_opt_main, key="m_select_wsid_staff")
            
            sub_staff_df = disp_df[disp_df["WSID"].astype(str) == sel_main_wsid]
            st.info(f"Ditemukan **{len(sub_staff_df)} Log Petugas/Staff** terdaftar untuk WSID **{sel_main_wsid}**")
            
            staff_show_cols = ["WSID", "LOKASI", "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "TGL_INS", "TGL_REM", "ACTIVITY", "CATATAN_PROSES"]
            existing_s_cols = [c for c in staff_show_cols if c in sub_staff_df.columns]
            st.dataframe(sub_staff_df[existing_s_cols], use_container_width=True)

    # Dedicated Row-level Action Panel (Edit & Delete Form Panel)
    st.markdown("---")
    st.markdown("### ⚙️ Panel Aksi Edit & Hapus Baris Data (Row Action Panel)")
    
    if not disp_df.empty:
        tab_act_u, tab_act_d, tab_act_a = st.tabs(["✏️ [UPDATE] Edit Record Baris Data", "🗑️ [DELETE] Hapus Record Baris Data", "➕ [CREATE] Tambah Baris Baru"])
        
        wsid_list = [str(w) for w in disp_df["WSID"].unique().tolist()] if "WSID" in disp_df.columns else [str(i) for i in disp_df.index]
        
        with tab_act_u:
            sel_u_wsid = st.selectbox("Pilih WSID Target yang Ingin Di-Edit:", wsid_list, key="m_select_edit_wsid")
            match_rows = st.session_state.df_rekon[st.session_state.df_rekon["WSID"].astype(str) == sel_u_wsid] if "WSID" in st.session_state.df_rekon.columns else pd.DataFrame()
            
            if not match_rows.empty:
                e_idx = match_rows.index[0]
                row_val = st.session_state.df_rekon.loc[e_idx]
                
                with st.form(f"form_main_edit_{sel_u_wsid}"):
                    st.info(f"Mengubah Rincian Data untuk WSID **{sel_u_wsid}** (Row Index: {e_idx})")
                    e_col1, e_col2, e_col3, e_col4 = st.columns(4)
                    with e_col1:
                        me_wsid = st.text_input("WSID Terminal", value=str(row_val.get("WSID", "")))
                        me_lok = st.selectbox("LOK", ["BCA", "T"], index=0 if str(row_val.get("LOK")) != "T" else 1)
                        me_lokasi = st.text_input("Lokasi Terminal", value=str(row_val.get("LOKASI", "")))
                    with e_col2:
                        me_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"], index=0 if str(row_val.get("Mesin")) not in ["O-CRM", "ITM", "CRMHYO", "ACH"] else ["O-CRM", "ITM", "CRMHYO", "ACH"].index(str(row_val.get("Mesin"))))
                        me_cash_pos = st.number_input("Cash Position (Ribu Rp)", value=float(safe_float(row_val.get("CASH_POS", 0))))
                        me_setor = st.number_input("Total Setor (Ribu Rp)", value=float(safe_float(row_val.get("SETOR", 0))))
                    with e_col3:
                        me_sel_akhir = st.number_input("Selisih Akhir (Ribu Rp)", value=float(safe_float(row_val.get("SEL_AKHIR", 0))))
                        me_uk_bdc = st.text_input("Catatan UK BDC", value=str(row_val.get("UK_BDC", "")))
                        me_test_cash = st.text_input("Catatan Tes Cash", value=str(row_val.get("TEST_CASH", "")))
                    with e_col4:
                        me_cencon = st.selectbox("Close / Open Cencon", ["Close", "Open", "Pending"], index=0 if str(row_val.get("CLOSE_OPEN_CENCON")) not in ["Close", "Open", "Pending"] else ["Close", "Open", "Pending"].index(str(row_val.get("CLOSE_OPEN_CENCON"))))
                        me_staff1 = st.text_input("Petugas 1", value=str(row_val.get("STAFF_1", "")))
                        me_staff_extra = st.text_input("Petugas Tambahan / Banyak Staff (Pisahkan Koma)", value=str(row_val.get("STAFF_LAINNYA", "")))
                        me_driver = st.text_input("Driver Pengawal", value=str(row_val.get("DRIVER", "")))

                    me_activity = st.text_input("Aktivitas Operasional", value=str(row_val.get("ACTIVITY", "")))
                    me_catatan = st.text_input("Catatan Lapangan", value=str(row_val.get("CATATAN_PROSES", "")))
                    me_tanggapan = st.text_area("Tanggapan BCA / Audit Log", value=str(row_val.get("TANGGAPAN_BCA", "")))
                    
                    sub_edit_main = st.form_submit_button("✏️ [UPDATE] Simpan Perubahan Data WSID Ini", type="primary")
                    if sub_edit_main:
                        st.session_state.df_rekon.at[e_idx, "WSID"] = me_wsid
                        st.session_state.df_rekon.at[e_idx, "LOK"] = me_lok
                        st.session_state.df_rekon.at[e_idx, "LOKASI"] = me_lokasi
                        st.session_state.df_rekon.at[e_idx, "Mesin"] = me_mesin
                        st.session_state.df_rekon.at[e_idx, "CASH_POS"] = me_cash_pos
                        st.session_state.df_rekon.at[e_idx, "SETOR"] = me_setor
                        st.session_state.df_rekon.at[e_idx, "SEL_AWAL"] = me_setor - me_cash_pos
                        st.session_state.df_rekon.at[e_idx, "SEL_AKHIR"] = me_sel_akhir
                        st.session_state.df_rekon.at[e_idx, "UK_BDC"] = me_uk_bdc
                        st.session_state.df_rekon.at[e_idx, "TEST_CASH"] = me_test_cash
                        st.session_state.df_rekon.at[e_idx, "CLOSE_OPEN_CENCON"] = me_cencon
                        st.session_state.df_rekon.at[e_idx, "STAFF_1"] = me_staff1
                        st.session_state.df_rekon.at[e_idx, "STAFF_LAINNYA"] = me_staff_extra
                        st.session_state.df_rekon.at[e_idx, "DRIVER"] = me_driver
                        st.session_state.df_rekon.at[e_idx, "ACTIVITY"] = me_activity
                        st.session_state.df_rekon.at[e_idx, "CATATAN_PROSES"] = me_catatan
                        st.session_state.df_rekon.at[e_idx, "TANGGAPAN_BCA"] = me_tanggapan
                        
                        st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, "TGL_REM")
                        st.session_state.upload_success_msg = f"🎉 Data WSID '{me_wsid}' berhasil diperbarui!"
                        safe_rerun()

        with tab_act_d:
            sel_d_wsid = st.selectbox("Pilih WSID Target yang Ingin Dihapus:", wsid_list, key="m_select_del_wsid")
            st.warning(f"⚠️ Apakah Anda yakin ingin menghapus seluruh data untuk WSID **{sel_d_wsid}**?")
            if st.button(f"🗑️ [DELETE] Konfirmasi Hapus Data WSID {sel_d_wsid}", type="primary", key="btn_confirm_del"):
                st.session_state.df_rekon = st.session_state.df_rekon[st.session_state.df_rekon["WSID"].astype(str) != sel_d_wsid].reset_index(drop=True)
                st.session_state.upload_success_msg = f"🗑️ Data WSID '{sel_d_wsid}' berhasil dihapus!"
                safe_rerun()

        with tab_act_a:
            with st.form("form_main_add"):
                st.info("➕ Menambahkan Baris Rekonsiliasi Kas Baru ke Tabel Utama")
                a_col1, a_col2, a_col3, a_col4 = st.columns(4)
                with a_col1:
                    a_wsid = st.text_input("WSID Terminal", "")
                    a_lok = st.selectbox("LOK", ["BCA", "T"])
                    a_lokasi = st.text_input("Lokasi Terminal", "")
                with a_col2:
                    a_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
                    a_cash_pos = st.number_input("Cash Position (Ribu Rp)", value=0)
                    a_setor = st.number_input("Total Setor (Ribu Rp)", value=0)
                with a_col3:
                    a_sel_akhir = st.number_input("Selisih Akhir (Ribu Rp)", value=0)
                    a_uk_bdc = st.text_input("Catatan UK BDC", "")
                    a_test_cash = st.text_input("Catatan Tes Cash", "")
                with a_col4:
                    a_cencon = st.selectbox("Close / Open Cencon", ["Close", "Open", "Pending"])
                    a_staff1 = st.text_input("Petugas 1", "")
                    a_driver = st.text_input("Driver Pengawal", "")

                a_activity = st.text_input("Aktivitas Operasional", "")
                a_catatan = st.text_input("Catatan Lapangan", "")
                a_tanggapan = st.text_area("Tanggapan BCA", "")
                
                sub_add_main = st.form_submit_button("➕ [CREATE] Simpan Baris Data Baru", type="primary")
                if sub_add_main and a_wsid:
                    new_main_row = {
                        "WSID": a_wsid, "LOK": a_lok, "LOKASI": a_lokasi, "Mesin": a_mesin,
                        "CASH_POS": a_cash_pos, "SETOR": a_setor, "SEL_AWAL": a_setor - a_cash_pos, "SEL_AKHIR": a_sel_akhir,
                        "UK_BDC": a_uk_bdc, "TEST_CASH": a_test_cash, "CLOSE_OPEN_CENCON": a_cencon,
                        "STAFF_1": a_staff1, "DRIVER": a_driver, "ACTIVITY": a_activity,
                        "CATATAN_PROSES": a_catatan, "TANGGAPAN_BCA": a_tanggapan,
                        "TGL_INS": datetime.now().strftime("%Y-%m-%d"),
                        "TGL_REM": datetime.now().strftime("%Y-%m-%d")
                    }
                    st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_main_row])], ignore_index=True)
                    st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, "TGL_REM")
                    st.session_state.upload_success_msg = f"🎉 Baris baru WSID '{a_wsid}' berhasil ditambahkan!"
                    safe_rerun()

    # Live Image Viewer Banner in Main Menu
    if st.session_state.image_store:
        st.markdown("---")
        st.markdown("### 📸 Foto Bukti Fisik Tersimpan (Lampiran Menu Utama)")
        tab_img1, tab_img2 = st.tabs(["🔍 Lihat Detail Per WSID", "🖼️ Galeri Semua Foto"])
        
        with tab_img1:
            img_wsids = list(st.session_state.image_store.keys())
            sel_img_wsid = st.selectbox("Pilih WSID Target Foto:", img_wsids, key="m_view_wsid")
            if sel_img_wsid in st.session_state.image_store:
                col_i1, col_i2 = st.columns([1.2, 1])
                with col_i1:
                    st.image(st.session_state.image_store[sel_img_wsid], caption=f"Bukti Fisik WSID {sel_img_wsid}", use_container_width=True)
                with col_i2:
                    st.markdown(f"#### Detail Foto Bukti WSID: **{sel_img_wsid}**")
                    st.success(f"✅ Foto bukti fisik telah terlampir secara aktif untuk WSID **{sel_img_wsid}**.")
                    if st.button(f"🗑️ Hapus Foto WSID {sel_img_wsid}", key=f"del_img_{sel_img_wsid}"):
                        del st.session_state.image_store[sel_img_wsid]
                        st.success("Foto berhasil dihapus!")
                        safe_rerun()

        with tab_img2:
            img_wsids = list(st.session_state.image_store.keys())
            grid_cols = st.columns(min(len(img_wsids), 3))
            for i, w_id in enumerate(img_wsids):
                with grid_cols[i % 3]:
                    st.image(st.session_state.image_store[w_id], caption=f"WSID: {w_id}", use_container_width=True)

# ---------------------------------------------------------
# MODUL 3: MULTI-STAFF OPERASIONAL PER WSID
# ---------------------------------------------------------
elif menu == "👥 Multi-Staff Operasional per WSID":
    st.subheader("👥 Pengawasan & Rincian Semua Staff Operasional per WSID")
    st.write("Modul khusus untuk melihat, menambah, mengubah, dan mengaudit seluruh tim petugas / staff operasional untuk setiap WSID Terminal.")

    if not df_rekon.empty:
        wsid_opt_s = [str(w) for w in df_rekon["WSID"].unique().tolist()]
        sel_s_wsid = st.selectbox("🔍 Pilih WSID Terminal untuk Menampilkan Seluruh Staff:", wsid_opt_s, key="s_mod_select_wsid")
        
        staff_records = df_rekon[df_rekon["WSID"].astype(str) == sel_s_wsid]
        
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("WSID Target", sel_s_wsid)
        with col_m2:
            st.metric("Total Log Staff Terdaftar", f"{len(staff_records)} Entri Staff")

        st.markdown(f"### 📋 Daftar Semua Staff & Petugas Terdaftar untuk WSID **{sel_s_wsid}**:")
        staff_cols_show = ["WSID", "LOKASI", "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "TGL_INS", "TGL_REM", "ACTIVITY", "CATATAN_PROSES"]
        s_exist_cols = [c for c in staff_cols_show if c in staff_records.columns]
        
        st.dataframe(staff_records[s_exist_cols], use_container_width=True)

        st.markdown("---")
        st.markdown(f"### ➕ Tambah Log Petugas / Staff Baru untuk WSID **{sel_s_wsid}**")
        
        with st.form(f"form_add_staff_{sel_s_wsid}"):
            st.info(f"Menambahkan entri petugas/staff operasional baru ke WSID **{sel_s_wsid}**")
            
            s_c1, s_c2, s_c3 = st.columns(3)
            with s_c1:
                as_staff1 = st.text_input("Petugas 1 (Staff 1)", "")
                as_staff2 = st.text_input("Petugas 2 (Staff 2)", "")
            with s_c2:
                as_staff3 = st.text_input("Petugas 3 (Staff 3)", "")
                as_driver = st.text_input("Driver Pengawal", "")
            with s_c3:
                as_tgl_ins = st.text_input("Jam / Tgl Masuk (TGL_INS)", datetime.now().strftime("%Y-%m-%d %H:%M"))
                as_tgl_rem = st.text_input("Jam / Tgl Selesai (TGL_REM)", datetime.now().strftime("%Y-%m-%d %H:%M"))

            as_activity = st.text_input("Durasi & Aktivitas Operasional", "0:15:00 BONGKAR ISI")
            as_catatan = st.text_input("Catatan Lapangan / Keterangan", "Proses pengisian kas lancar")
            
            sub_add_s = st.form_submit_button("💾 [SIMPAN STAFF] Tambahkan Log Staff Ini", type="primary")
            if sub_add_s:
                first_row = staff_records.iloc[0] if not staff_records.empty else {}
                new_staff_row = {
                    "WSID": sel_s_wsid,
                    "LOK": first_row.get("LOK", "BCA"),
                    "LOKASI": first_row.get("LOKASI", "ATM BCA"),
                    "Mesin": first_row.get("Mesin", "O-CRM"),
                    "BULAN": first_row.get("BULAN", "Juli 2026"),
                    "TGL_INS": as_tgl_ins,
                    "TGL_REM": as_tgl_rem,
                    "CASH_POS": safe_float(first_row.get("CASH_POS", 0)),
                    "SETOR": safe_float(first_row.get("SETOR", 0)),
                    "SEL_AWAL": safe_float(first_row.get("SEL_AWAL", 0)),
                    "SEL_AKHIR": safe_float(first_row.get("SEL_AKHIR", 0)),
                    "UK_BDC": first_row.get("UK_BDC", "-"),
                    "TEST_CASH": first_row.get("TEST_CASH", "-"),
                    "CLOSE_OPEN_CENCON": first_row.get("CLOSE_OPEN_CENCON", "Close"),
                    "REKON_SISLOK": first_row.get("REKON_SISLOK", "Balanced"),
                    "REVIEW_STOCK": first_row.get("REVIEW_STOCK", "-"),
                    "STAFF_1": as_staff1,
                    "STAFF_2": as_staff2,
                    "STAFF_3": as_staff3,
                    "DRIVER": as_driver,
                    "ACTIVITY": as_activity,
                    "CATATAN_PROSES": as_catatan,
                    "TANGGAPAN_BCA": first_row.get("TANGGAPAN_BCA", "-")
                }
                st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_staff_row])], ignore_index=True)
                st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, "TGL_REM")
                st.success(f"Log staff baru untuk WSID {sel_s_wsid} berhasil ditambahkan!")
                safe_rerun()
    else:
        st.info("ℹ️ Belum ada data rekonsiliasi. Silakan muat data sampel default atau upload file Excel terlebih dahulu.")

# ---------------------------------------------------------
# MODUL 4: CLOSE / OPEN CENCON & TES CASH
# ---------------------------------------------------------
elif menu == "💵 Close / Open Cencon & Tes Cash":
    st.subheader("💵 Pengawasan Close / Open Cencon & Tes Cash")
    display_styled_df(st.session_state.df_cencon, ["BDC", "NON_BDC"])

# ---------------------------------------------------------
# MODUL 5: UK TC, UK BDC & UK SICLUS
# ---------------------------------------------------------
elif menu == "🔄 UK TC, UK BDC & UK Siclus":
    st.subheader("🔄 Audit Uang Kembali (UK TC, UK BDC, UK Siclus)")
    display_styled_df(st.session_state.df_uk, ["BDC", "NON_BDC", "TOTAL_UK"])

# ---------------------------------------------------------
# MODUL 6: LAPORAN EBOS
# ---------------------------------------------------------
elif menu == "📑 Laporan EBOS":
    st.subheader("📑 Monitoring & Registrasi Laporan EBOS")
    display_styled_df(st.session_state.df_ebos, ["NOMINAL_SELISIH"])

# ---------------------------------------------------------
# MODUL 7: REKON EJ (ELECTRONIC JOURNAL)
# ---------------------------------------------------------
elif menu == "💻 Rekon EJ (Electronic Journal)":
    st.subheader("💻 Rekonsiliasi Electronic Journal (EJ Audit)")
    display_styled_df(st.session_state.df_ej, ["NOMINAL_EJ"])

# ---------------------------------------------------------
# MODUL 8: REKON SISLOK & REVIEW STOCK
# ---------------------------------------------------------
elif menu == "📦 Rekon Sislok & Review Stock":
    st.subheader("📦 Rekonsiliasi Sistem Lokasi (Sislok) & Review Stock Kas")
    display_styled_df(st.session_state.df_sislok, ["STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR", "STOK_SISLOK_AKHIR", "FISIK_KAS_ACTUAL", "SELISIH_STOK"])

# ---------------------------------------------------------
# MODUL 9: UANG KOLONG & TEMUAN FISIK
# ---------------------------------------------------------
elif menu == "🪙 Uang Kolong & Temuan Fisik":
    st.subheader("🪙 Pencatatan Uang Kolong & Temuan Fisik Terselip")
    display_styled_df(st.session_state.df_kolong, ["LEMBAR", "TOTAL_RUPIAH"])

# ---------------------------------------------------------
# MODUL 10: UNGGAH & GALERI FOTO BUKTI
# ---------------------------------------------------------
elif menu == "📸 Unggah & Galeri Foto Bukti":
    st.subheader("📸 Galeri & Unggah Lampiran Foto Bukti Fisik")
    col_up1, col_up2 = st.columns([1, 1])

    wsid_options = df_rekon["WSID"].unique().tolist() if not df_rekon.empty else ["Z5UM", "ZM16"]

    with col_up1:
        st.markdown("### 📤 Unggah Foto Bukti Baru")
        target_wsid = st.text_input("Ketik WSID Target Foto:", "")
        uploaded_img = st.file_uploader("Unggah File Foto Bukti (PNG / JPG / JPEG):", type=["png", "jpg", "jpeg"])

        if uploaded_img is not None and target_wsid:
            image_bytes = uploaded_img.read()
            st.session_state.image_store[target_wsid] = image_bytes
            st.success(f"Foto bukti untuk WSID {target_wsid} berhasil diunggah!")

    with col_up2:
        st.markdown("### 🖼️ Preview Foto Bukti Tersimpan")
        if st.session_state.image_store:
            view_wsid = st.selectbox("Pilih WSID untuk Pratinjau:", list(st.session_state.image_store.keys()), key="preview_wsid")
            if view_wsid in st.session_state.image_store:
                st.image(st.session_state.image_store[view_wsid], caption=f"Bukti Fisik WSID {view_wsid}", use_container_width=True)
        else:
            st.info("Belum ada foto bukti yang diunggah.")

# ---------------------------------------------------------
# MODUL 11: KELOLA DATA (CRUD OPERATIONS)
# ---------------------------------------------------------
elif menu == "🛠️ Kelola Data (CRUD Operations)":
    st.subheader("🛠️ Manajemen & Modul CRUD (Create, Read, Update, Delete)")

    crud_table = st.selectbox("Pilih Tabel Target CRUD:", [
        "1. Rekon Utama & Staff Operasional",
        "2. Close / Open Cencon & Tes Cash",
        "3. Uang Kembali (UK TC/BDC/Siclus)",
        "4. Laporan EBOS",
        "5. Rekon EJ Log",
        "6. Sislok Stock Review",
        "7. Uang Kolong & Temuan Fisik"
    ])

    if crud_table.startswith("1"):
        target_df_key = "df_rekon"
    elif crud_table.startswith("2"):
        target_df_key = "df_cencon"
    elif crud_table.startswith("3"):
        target_df_key = "df_uk"
    elif crud_table.startswith("4"):
        target_df_key = "df_ebos"
    elif crud_table.startswith("5"):
        target_df_key = "df_ej"
    elif crud_table.startswith("6"):
        target_df_key = "df_sislok"
    else:
        target_df_key = "df_kolong"

    current_df = st.session_state[target_df_key]

    tab_c, tab_r, tab_u, tab_d = st.tabs(["➕ [CREATE] Tambah Data", "👁️ [READ] Lihat Data", "✏️ [UPDATE] Edit Data", "🗑️ [DELETE] Hapus Data"])

    with tab_r:
        st.markdown("### 👁️ Read / Tampilan Data Terbaru")
        st.dataframe(current_df, use_container_width=True)

    with tab_c:
        st.markdown("### ➕ Create / Tambah Record Baru")
        with st.form("form_create_crud"):
            st.info(f"Mengisi data baru ke dalam **{crud_table}**")
            
            c_wsid = st.text_input("WSID Terminal", "")
            c_lokasi = st.text_input("Nama Lokasi", "")
            c_bulan = st.selectbox("Periode Bulan", ["Juni 2026", "Juli 2026", "Agustus 2026", "September 2026"])
            c_cash_pos = st.number_input("Cash Position (Ribu Rp)", value=0)
            c_setor = st.number_input("Total Setor (Ribu Rp)", value=0)
            
            submit_c = st.form_submit_button("💾 [CREATE] Simpan Data Baru")
            if submit_c:
                new_entry = {
                    "WSID": c_wsid, "LOKASI": c_lokasi, "BULAN": c_bulan,
                    "CASH_POS": c_cash_pos, "SETOR": c_setor,
                    "SEL_AWAL": c_setor - c_cash_pos, "SEL_AKHIR": -100,
                    "TGL_INS": datetime.now().strftime("%Y-%m-%d"),
                    "TGL_REM": datetime.now().strftime("%Y-%m-%d")
                }
                st.session_state[target_df_key] = pd.concat([st.session_state[target_df_key], pd.DataFrame([new_entry])], ignore_index=True)
                st.success("Record baru berhasil disimpan!")
                safe_rerun()

    with tab_u:
        st.markdown("### ✏️ Update / Edit Record Data")
        if not current_df.empty:
            edit_idx = st.number_input("Pilih Baris Index Data yang Ingin Diubah:", min_value=0, max_value=len(current_df)-1, value=0, step=1)
            row_data = current_df.iloc[edit_idx]
            
            with st.form("form_update_crud"):
                u_wsid = st.text_input("WSID", value=str(row_data.get("WSID", "")))
                u_lokasi = st.text_input("Lokasi", value=str(row_data.get("LOKASI", "")))
                u_bulan = st.selectbox("Periode Bulan", ["Juni 2026", "Juli 2026", "Agustus 2026"], index=0)
                u_setor = st.number_input("Nominal Disetor (Ribu Rp)", value=float(safe_float(row_data.get("SETOR", 0))))
                
                submit_u = st.form_submit_button("✏️ [UPDATE] Simpan Perubahan Data")
                if submit_u:
                    st.session_state[target_df_key].at[edit_idx, "WSID"] = u_wsid
                    st.session_state[target_df_key].at[edit_idx, "LOKASI"] = u_lokasi
                    st.session_state[target_df_key].at[edit_idx, "BULAN"] = u_bulan
                    st.session_state[target_df_key].at[edit_idx, "SETOR"] = u_setor
                    st.success(f"Baris Index {edit_idx} berhasil diperbarui!")
                    safe_rerun()
        else:
            st.info("Tabel saat ini masih kosong.")

    with tab_d:
        st.markdown("### 🗑️ Delete / Hapus Record Data")
        if not current_df.empty:
            del_idx = st.number_input("Pilih Baris Index Data yang Ingin Dihapus:", min_value=0, max_value=len(current_df)-1, value=0, step=1, key="del_idx")
            st.warning(f"Anda akan menghapus baris Index {del_idx} dari tabel {crud_table}.")
            if st.button("🗑️ [DELETE] Konfirmasi Hapus Record Ini"):
                st.session_state[target_df_key] = st.session_state[target_df_key].drop(del_idx).reset_index(drop=True)
                st.success(f"Record index {del_idx} berhasil dihapus!")
                safe_rerun()
        else:
            st.info("Tabel saat ini masih kosong.")

# ---------------------------------------------------------
# MODUL 12: INPUT & TAMBAH DATA TERPADU
# ---------------------------------------------------------
elif menu == "➕ Input & Tambah Data Terpadu":
    st.subheader("📝 Input & Tambah Data Terpadu ke Seluruh Modul Tabel")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "📋 Staff & Rekon Utama", "💵 Close/Open Cencon", "🔄 UK (Uang Kembali)",
        "📑 Laporan EBOS", "💻 Rekon EJ Log", "📦 Sislok Stock Review",
        "🪙 Uang Kolong", "📸 Upload Foto Bukti"
    ])

    with tab1:
        st.markdown("### 📋 Input Data Rekonsiliasi Utama & Staff Operasional")
        with st.form("form_inp_rekon"):
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                i_wsid = st.text_input("WSID Terminal", "")
                i_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
                i_lokasi = st.text_input("Nama Lokasi", "")
            with c2:
                i_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
                i_bulan = st.selectbox("Periode Bulan", ["Juni 2026", "Juli 2026", "Agustus 2026"])
                i_tgl_ins = st.date_input("Tanggal Insert (TGL_INS)")
                i_tgl_rem = st.date_input("Tanggal Removal (TGL_REM)")
            with c3:
                i_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=0)
                i_setor = st.number_input("Total Disetor (Ribu Rp)", value=0)
                i_sel_awal = i_setor - i_cash_pos
                st.info(f"Estimasi Selisih Awal: **{i_sel_awal:,.0f} (Ribu Rp)**")
            with c4:
                i_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=0)
                i_uk_bdc = st.text_input("Catatan UK BDC", "")
                i_test_cash = st.text_input("Catatan Tes Cash", "")

            c5, c6, c7, c8, c9 = st.columns(5)
            with c5:
                i_staff1 = st.text_input("Petugas 1", "")
            with c6:
                i_staff2 = st.text_input("Petugas 2", "")
            with c7:
                i_staff3 = st.text_input("Petugas 3", "")
            with c8:
                i_staff_extra = st.text_input("Staff Lainnya (Koma)", "", help="Input banyak nama staff dipisahkan koma")
            with c9:
                i_driver = st.text_input("Driver Pengawal", "")

            i_activity = st.text_input("Aktivitas Operasional", "")
            i_catatan = st.text_input("Catatan Lapangan", "")
            i_tanggapan = st.text_area("Tanggapan BCA", "")

            sub1 = st.form_submit_button("💾 Simpan Record Rekon Utama")
            if sub1:
                new_r = {
                    "WSID": i_wsid, "LOK": i_lok, "LOKASI": i_lokasi, "Mesin": i_mesin, "BULAN": i_bulan,
                    "TGL_INS": pd.to_datetime(i_tgl_ins), "TGL_REM": pd.to_datetime(i_tgl_rem),
                    "CASH_POS": i_cash_pos, "SETOR": i_setor, "SEL_AWAL": i_sel_awal, "SEL_AKHIR": i_sel_akhir,
                    "UK_BDC": i_uk_bdc, "TEST_CASH": i_test_cash, "CLOSE_OPEN_CENCON": "Close",
                    "REKON_SISLOK": "Balanced", "REVIEW_STOCK": f"Sislok: {i_cash_pos:,.0f} | Fisik: {i_setor:,.0f}",
                    "STAFF_1": i_staff1, "STAFF_2": i_staff2, "STAFF_3": i_staff3, "STAFF_LAINNYA": i_staff_extra,
                    "DRIVER": i_driver, "ACTIVITY": i_activity, "CATATAN_PROSES": i_catatan, "TANGGAPAN_BCA": i_tanggapan
                }
                st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_r])], ignore_index=True)
                st.session_state.upload_success_msg = f"Data WSID {i_wsid} berhasil disimpan ke Tabel Utama!"
                st.session_state.target_nav_menu = "📋 Tabel Utama (Complete Audit)"
                safe_rerun()

    with tab2:
        st.markdown("### 💵 Input Record Close / Open Cencon & Tes Cash")
        with st.form("form_inp_cencon"):
            c_c1, c_c2, c_c3, c_c4 = st.columns(4)
            with c_c1:
                cn_wsid = st.text_input("WSID Terminal", "")
                cn_lokasi = st.text_input("Nama Lokasi", "")
            with c_c2:
                cn_tgl = st.date_input("Tanggal Transaksi")
                cn_jam = st.text_input("Jam (HH:MM)", "")
            with c_c3:
                cn_bdc = st.number_input("Nominal BDC (Rp)", value=0, step=10000)
                cn_non_bdc = st.number_input("Nominal NON-BDC (Rp)", value=0, step=10000)
            with c_c4:
                cn_status = st.selectbox("Status Cencon", ["Close", "Open", "Pending"])
                cn_ket = st.text_input("Keterangan Tes Cash", "")

            sub2 = st.form_submit_button("💾 Simpan Record Cencon")
            if sub2:
                new_cn = {
                    "WSID": cn_wsid, "LOKASI": cn_lokasi, "TANGGAL": pd.to_datetime(cn_tgl),
                    "JAM": cn_jam, "BDC": cn_bdc, "NON_BDC": cn_non_bdc,
                    "STATUS": cn_status, "KETERANGAN": cn_ket
                }
                st.session_state.df_cencon = pd.concat([st.session_state.df_cencon, pd.DataFrame([new_cn])], ignore_index=True)
                st.success("Record Cencon berhasil disimpan!")
                safe_rerun()

    with tab3:
        st.markdown("### 🔄 Input Klaim Uang Kembali (UK)")
        with st.form("form_inp_uk"):
            u_1, u_2, u_3, u_4 = st.columns(4)
            with u_1:
                uk_wsid = st.text_input("WSID Terminal", "")
                uk_lokasi = st.text_input("Nama Lokasi", "")
            with u_2:
                uk_tipe = st.selectbox("Tipe UK", ["UK Siclus", "UK TC", "UK BDC"])
                uk_tgl = st.date_input("Tanggal Klaim")
            with u_3:
                uk_jam = st.text_input("Jam Transaksi", "")
                uk_bdc = st.number_input("Nominal UK BDC (Rp)", value=0, step=50000)
            with u_4:
                uk_non_bdc = st.number_input("Nominal UK Non-BDC (Rp)", value=0, step=50000)
                uk_ket = st.text_input("Keterangan Rincian UK", "")

            sub3 = st.form_submit_button("💾 Simpan Record UK")
            if sub3:
                new_uk = {
                    "WSID": uk_wsid, "LOKASI": uk_lokasi, "TANGGAL": pd.to_datetime(uk_tgl),
                    "JAM": uk_jam, "TIPE_UK": uk_tipe, "BDC": uk_bdc, "NON_BDC": uk_non_bdc,
                    "TOTAL_UK": uk_bdc + uk_non_bdc, "KETERANGAN": uk_ket
                }
                st.session_state.df_uk = pd.concat([st.session_state.df_uk, pd.DataFrame([new_uk])], ignore_index=True)
                st.success("Record UK berhasil disimpan!")
                safe_rerun()

    with tab4:
        st.markdown("### 📑 Registrasi Laporan EBOS")
        with st.form("form_inp_ebos"):
            e_1, e_2, e_3 = st.columns(3)
            with e_1:
                e_no = st.text_input("No Tiket EBOS", "")
                e_wsid = st.text_input("WSID Terminal", "")
                e_lokasi = st.text_input("Lokasi Terminal", "")
            with e_2:
                e_tgl = st.date_input("Tanggal Laporan")
                e_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
                e_nom = st.number_input("Nominal Selisih EBOS (Rp)", value=0, step=50000)
            with e_3:
                e_status = st.selectbox("Status Tiket", ["Open", "In Review", "Resolved", "Closed"])
                e_catatan = st.text_area("Catatan Laporan EBOS", "")

            sub4 = st.form_submit_button("💾 Registrasi Tiket EBOS")
            if sub4:
                new_eb = {
                    "NO_LAPORAN": e_no, "WSID": e_wsid, "LOKASI": e_lokasi,
                    "TANGGAL": pd.to_datetime(e_tgl), "TIPE_MESIN": e_mesin,
                    "NOMINAL_SELISIH": e_nom, "STATUS_EBOS": e_status, "CATATAN_EBOS": e_catatan
                }
                st.session_state.df_ebos = pd.concat([st.session_state.df_ebos, pd.DataFrame([new_eb])], ignore_index=True)
                st.success("Tiket EBOS berhasil dicatat!")
                safe_rerun()

    with tab5:
        st.markdown("### 💻 Input Log Rekon EJ (Electronic Journal)")
        with st.form("form_inp_ej"):
            j_1, j_2, j_3 = st.columns(3)
            with j_1:
                j_wsid = st.text_input("WSID Terminal", "")
                j_lokasi = st.text_input("Nama Lokasi", "")
                j_tgl = st.date_input("Tanggal Log EJ")
            with j_2:
                j_jam = st.text_input("Jam Transaksi", "")
                j_kartu = st.text_input("No Kartu / Rekening", "")
                j_nom = st.number_input("Nominal Transaksi EJ (Rp)", value=0, step=50000)
            with j_3:
                j_status = st.selectbox("Status Matching EJ", ["Matched", "Discrepancy - Short", "Discrepancy - Over"])
                j_catatan = st.text_area("Catatan Temuan EJ", "")

            sub5 = st.form_submit_button("💾 Simpan Record Log EJ")
            if sub5:
                new_ej = {
                    "WSID": j_wsid, "LOKASI": j_lokasi, "TANGGAL_EJ": pd.to_datetime(j_tgl),
                    "JAM_TX": j_jam, "NO_KARTU_REK": j_kartu, "NOMINAL_EJ": j_nom,
                    "STATUS_EJ": j_status, "CATATAN_EJ": j_catatan
                }
                st.session_state.df_ej = pd.concat([st.session_state.df_ej, pd.DataFrame([new_ej])], ignore_index=True)
                st.success("Record EJ berhasil disimpan!")
                safe_rerun()

    with tab6:
        st.markdown("### 📦 Input Audit Sislok & Stock Review")
        with st.form("form_inp_sislok"):
            s_1, s_2, s_3 = st.columns(3)
            with s_1:
                s_wsid = st.text_input("WSID Terminal", "")
                s_lokasi = st.text_input("Lokasi Terminal", "")
                s_tgl = st.date_input("Tanggal Audit Stock")
            with s_2:
                s_awal = st.number_input("Stok Sislok Awal (Ribu Rp)", value=0, step=10000)
                s_masuk = st.number_input("Total Kas Masuk (Ribu Rp)", value=0, step=10000)
                s_keluar = st.number_input("Total Kas Keluar (Ribu Rp)", value=0, step=10000)
            with s_3:
                s_sislok_akhir = s_awal + s_masuk - s_keluar
                st.info(f"Stok Sislok Akhir: **Rp {s_sislok_akhir:,.0f} (Ribu Rp)**")
                s_fisik = st.number_input("Fisik Kas Actual (Ribu Rp)", value=0, step=10000)
                s_selisih = s_fisik - s_sislok_akhir
                s_status = "Balanced" if s_selisih == 0 else "Variance Detected"

            sub6 = st.form_submit_button("💾 Simpan Audit Sislok Stock")
            if sub6:
                new_sl = {
                    "WSID": s_wsid, "LOKASI": s_lokasi, "TANGGAL_AUDIT": pd.to_datetime(s_tgl),
                    "STOK_SISLOK_AWAL": s_awal, "KAS_MASUK": s_masuk, "KAS_KELUAR": s_keluar,
                    "STOK_SISLOK_AKHIR": s_sislok_akhir, "FISIK_KAS_ACTUAL": s_fisik,
                    "SELISIH_STOK": s_selisih, "STATUS_REVIEW": s_status
                }
                st.session_state.df_sislok = pd.concat([st.session_state.df_sislok, pd.DataFrame([new_sl])], ignore_index=True)
                st.success("Audit Sislok berhasil disimpan!")
                safe_rerun()

    with tab7:
        st.markdown("### 🪙 Input Temuan Uang Kolong")
        with st.form("form_inp_kolong"):
            k_1, k_2, k_3 = st.columns(3)
            with k_1:
                k_wsid = st.text_input("WSID Terminal", "")
                k_lokasi = st.text_input("Nama Lokasi", "")
                k_tgl = st.date_input("Tanggal Temuan")
            with k_2:
                k_denom = st.selectbox("Denominasi Uang", ["100,000", "50,000", "20,000"])
                k_lembar = st.number_input("Jumlah Lembar", value=0, min_value=0)
                val_denom = 100000 if k_denom == "100,000" else (50000 if k_denom == "50,000" else 20000)
                k_total = val_denom * k_lembar
                st.info(f"Total Nominal Temuan: **Rp {k_total:,.0f}**")
            with k_3:
                k_posisi = st.selectbox("Lokasi Temuan Fisik", ["Kolong Dispenser", "Fascia Roll / Bawah", "Reject Box Chamber", "Transport Mechanism"])
                k_ket = st.text_area("Keterangan Fisik", "")

            sub7 = st.form_submit_button("💾 Simpan Temuan Uang Kolong")
            if sub7:
                new_kl = {
                    "WSID": k_wsid, "LOKASI": k_lokasi, "TANGGAL_TEMUAN": pd.to_datetime(k_tgl),
                    "DENOMINASI": k_denom, "LEMBAR": k_lembar, "TOTAL_RUPIAH": k_total,
                    "LOKASI_TEMUAN": k_posisi, "KETERANGAN": k_ket
                }
                st.session_state.df_kolong = pd.concat([st.session_state.df_kolong, pd.DataFrame([new_kl])], ignore_index=True)
                st.success("Temuan Uang Kolong berhasil dicatat!")
                safe_rerun()

    with tab8:
        st.markdown("### 📸 Unggah Foto Bukti Fisik")
        target_wsid_tab = st.text_input("WSID Target Foto:", "")
        uploaded_img_tab = st.file_uploader("Pilih File Foto Bukti (PNG / JPG / JPEG):", type=["png", "jpg", "jpeg"], key="up_tab8")
        if uploaded_img_tab is not None and target_wsid_tab:
            image_bytes = uploaded_img_tab.read()
            st.session_state.image_store[target_wsid_tab] = image_bytes
            st.success(f"Foto bukti untuk WSID {target_wsid_tab} berhasil diunggah!")

# ---------------------------------------------------------
# MODUL 13: EKSPOR & IMPOR DATA EXCEL
# ---------------------------------------------------------
elif menu == "📁 Ekspor & Impor Data Excel":
    st.subheader("📥 Unduh Seluruh Workbook Laporan Rekonsiliasi (.xlsx)")

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("### 📄 Unduh File Excel Multi-Sheet")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.df_rekon.to_excel(writer, sheet_name='Rekon_Utama_Staff', index=False)
            st.session_state.df_cencon.to_excel(writer, sheet_name='Tes_Cash_Cencon', index=False)
            st.session_state.df_uk.to_excel(writer, sheet_name='Uang_Kembali_UK', index=False)
            st.session_state.df_ebos.to_excel(writer, sheet_name='Laporan_EBOS', index=False)
            st.session_state.df_ej.to_excel(writer, sheet_name='Rekon_EJ', index=False)
            st.session_state.df_sislok.to_excel(writer, sheet_name='Sislok_Stock_Review', index=False)
            st.session_state.df_kolong.to_excel(writer, sheet_name='Temuan_Uang_Kolong', index=False)

        st.download_button(
            label="💾 Download Complete Workbook (.xlsx)",
            data=output.getvalue(),
            file_name=f"Rekonsiliasi_Lengkap_BCA_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_ex2:
        st.markdown("### 📤 Upload Master Excel / CSV Rekonsiliasi Baru")
        uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls / .csv) untuk memuat data:", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    new_df = pd.read_csv(uploaded_file)
                else:
                    xl = pd.ExcelFile(uploaded_file)
                    if 'Rekon_Utama_Staff' in xl.sheet_names:
                        new_df = xl.parse('Rekon_Utama_Staff')
                    else:
                        new_df = xl.parse(0)

                    if 'Tes_Cash_Cencon' in xl.sheet_names:
                        st.session_state.df_cencon = xl.parse('Tes_Cash_Cencon')
                    if 'Uang_Kembali_UK' in xl.sheet_names:
                        st.session_state.df_uk = xl.parse('Uang_Kembali_UK')
                    if 'Laporan_EBOS' in xl.sheet_names:
                        st.session_state.df_ebos = xl.parse('Laporan_EBOS')
                    if 'Rekon_EJ' in xl.sheet_names:
                        st.session_state.df_ej = xl.parse('Rekon_EJ')
                    if 'Sislok_Stock_Review' in xl.sheet_names:
                        st.session_state.df_sislok = xl.parse('Sislok_Stock_Review')
                    if 'Temuan_Uang_Kolong' in xl.sheet_names:
                        st.session_state.df_kolong = xl.parse('Temuan_Uang_Kolong')

                new_df = sanitize_df(new_df, [
                    "WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", 
                    "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", 
                    "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", 
                    "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
                ])
                new_df = auto_fill_bulan(new_df, date_col="TGL_REM")

                st.session_state.df_rekon = new_df
                st.session_state.upload_success_msg = f"🎉 File '{uploaded_file.name}' berhasil diunggah! Seluruh {len(new_df.columns)} kolom/header dan {len(new_df)} baris data langsung aktif dan menyesuaikan di Tabel Utama."
                st.session_state.target_nav_menu = "📋 Tabel Utama (Complete Audit)"
                safe_rerun()
            except Exception as e:
                st.error(f"Gagal memuat file: {e}")

    if not st.session_state.df_rekon.empty:
        st.markdown("---")
        st.markdown("### 👁️ Preview Data Rekonsiliasi Saat Ini:")
        display_styled_df(st.session_state.df_rekon, ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"])
