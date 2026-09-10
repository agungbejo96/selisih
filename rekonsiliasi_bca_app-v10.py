import streamlit as st

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

# ---------------------------------------------------------
# Page Configuration & Styling (BCA Corporate Theme)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistem Rekonsiliasi Kas BCA + Tabel Utama Complete Audit",
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
    .crud-banner {
        background: #F8FAFC;
        border-left: 5px solid #00529C;
        padding: 12px 18px;
        border-radius: 6px;
        margin-bottom: 15px;
    }
    .stTable {
        font-size: 12px;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Initial Data Load (Grounding Sources: juli.png & ost.png)
# ---------------------------------------------------------
def load_default_rekon():
    data = [
        {
            "WSID": "Z5UM", "LOK": "BCA", "LOKASI": "PURWOSARI CRM 2", "Mesin": "O-CRM",
            "TGL_INS": "2026-06-29", "TGL_REM": "2026-07-03", "CASH_POS": 317400, "SETOR": 316800,
            "SEL_AWAL": -600, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 500,000 (UK Siclus d.100 x 1 lbr)",
            "TEST_CASH": "Rp 100,000 (NON-BDC)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 500,600 | Fisik: 500,500",
            "STAFF_1": "BAYU OKTA PURWANTO", "STAFF_2": "AKHMAD RIZA MAULANA",
            "STAFF_3": "MUHAMMAD RIZAL MUZAKHI", "DRIVER": "ASSYAVI ALIYULLOH M",
            "ACTIVITY": "29/06/26 19:51 - BONGKAR ISI",
            "CATATAN_PROSES": "Proses normal, UK d.100 x 1 lbr",
            "TANGGAPAN_BCA": "Selisih Awal : -600\nUK : 500\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZM16", "LOK": "T", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "Mesin": "ITM",
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
        {
            "WSID": "Z0X2", "LOK": "T", "LOKASI": "IDM SUDIMORO MALANG", "Mesin": "CRMHYO",
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
        },
        {
            "WSID": "ZDA3", "LOK": "T", "LOKASI": "WINGS PROBOLINGGO", "Mesin": "ITM",
            "TGL_INS": "2026-07-09", "TGL_REM": "2026-07-11", "CASH_POS": 576950, "SETOR": 602500,
            "SEL_AWAL": 25550, "SEL_AKHIR": -50,
            "UK_BDC": "Rp 25,600,000 (Koreksi Adm)",
            "TEST_CASH": "Rp 200,000",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Balanced (-50)",
            "REVIEW_STOCK": "Sislok: 576,950 | Fisik: 576,900",
            "STAFF_1": "RIZKY PRATAMA", "STAFF_2": "FAJAR SHODIQ",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER 05",
            "ACTIVITY": "09/07/26 10:15 - KOREKSI ADM",
            "CATATAN_PROSES": "Koreksi Administrasi -25,600",
            "TANGGAPAN_BCA": "Selisih Awal : 25,550\nKoreksi Adm : -25,600\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZB3X", "LOK": "T", "LOKASI": "PT ANEKA TUNA INDONESIA", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-09", "TGL_REM": "2026-07-12", "CASH_POS": 359200, "SETOR": 372100,
            "SEL_AWAL": 12900, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 12,900,000 (Keluhan Nasabah)",
            "TEST_CASH": "Rp 200,000 (NON-BDC)",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 359,200 | Fisik: 359,100",
            "STAFF_1": "AGUS SETIAWAN", "STAFF_2": "HENDRA WIJAYA",
            "STAFF_3": "-", "DRIVER": "DRIVER VENDOR",
            "ACTIVITY": "09/07/26 14:20 - AUDIT CASH",
            "CATATAN_PROSES": "Multiple claim keluhan nasabah tgl 11/07",
            "TANGGAPAN_BCA": "Selisih Awal : 12,900\nKeluhan Nsb : -2,500 tgl 11/07 jam 12:14\n-2,500 tgl 11/07 jam 12:13\n-2,500 tgl 11/07 jam 12:11\n-500 tgl 11/07 jam 10:33\n-2,500 tgl 11/07 jam 09:17\n-2,500 tgl 11/07 jam 15:02\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZK82", "LOK": "T", "LOKASI": "IDM WARUNGDOWO PASURUAN", "Mesin": "O-CRM",
            "TGL_INS": "2026-07-15", "TGL_REM": "2026-07-18", "CASH_POS": 360750, "SETOR": 356500,
            "SEL_AWAL": -4250, "SEL_AKHIR": -50,
            "UK_BDC": "Rp 5,400,000 (UK BDC & Keluhan)",
            "TEST_CASH": "Rp 100,000",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-50)",
            "REVIEW_STOCK": "Sislok: 360,750 | Fisik: 360,700",
            "STAFF_1": "EKO PURWANTO", "STAFF_2": "ARIS MUNANDAR",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER 01",
            "ACTIVITY": "15/07/26 19:25 - REKONSILIASI",
            "CATATAN_PROSES": "UK : 5,400 & Keluhan Nsb : -1,200",
            "TANGGAPAN_BCA": "Selisih Awal : -4,250\nKeluhan Nsb : -1,200 tgl 15/07 jam 19:25\nUK : 5,400\nSelisih Akhir : -50"
        }
    ]
    df = pd.DataFrame(data)
    df["TGL_INS"] = pd.to_datetime(df["TGL_INS"])
    df["TGL_REM"] = pd.to_datetime(df["TGL_REM"])
    return df

def load_default_cencon():
    data = [
        {"WSID": "Z5UM", "LOKASI": "CRM PURWOSARI 2", "TANGGAL": "2026-06-27", "JAM": "20:22", "BDC": 0, "NON_BDC": 100000, "STATUS": "Close", "KETERANGAN": "Tes Cash Sesuai 100,000"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI", "TANGGAL": "2026-06-25", "JAM": "21:34", "BDC": 50000, "NON_BDC": 50000, "STATUS": "Open", "KETERANGAN": "Tes Cash Pending Konfirmasi"},
        {"WSID": "ZB3X", "LOKASI": "PT ANEKA TUNA INDONESIA", "TANGGAL": "2026-07-09", "JAM": "12:15", "BDC": 0, "NON_BDC": 200000, "STATUS": "Close", "KETERANGAN": "Tes Cash OK"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"])
    return df

def load_default_uk():
    data = [
        {"WSID": "Z5UM", "LOKASI": "CRM PURWOSARI 2", "TANGGAL": "2026-06-27", "JAM": "20:21", "TIPE_UK": "UK Siclus", "BDC": 0, "NON_BDC": 100000, "TOTAL_UK": 100000, "KETERANGAN": "UK Siclus d.100 x 1 lbr"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "TANGGAL": "2026-06-25", "JAM": "13:20", "TIPE_UK": "UK TC", "BDC": 3350000, "NON_BDC": 0, "TOTAL_UK": 3350000, "KETERANGAN": "UK TC d.50 x 67 lbr"},
        {"WSID": "ZH9M", "LOKASI": "KRAKSAAN", "TANGGAL": "2026-07-12", "JAM": "15:10", "TIPE_UK": "UK BDC", "BDC": 200000, "NON_BDC": 0, "TOTAL_UK": 200000, "KETERANGAN": "UK BDC Dispen 200k"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"])
    return df

def load_default_ebos():
    data = [
        {"NO_LAPORAN": "EBOS-202607-001", "WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "TANGGAL": "2026-06-29", "TIPE_MESIN": "O-CRM", "NOMINAL_SELISIH": 600000, "STATUS_EBOS": "Resolved", "CATATAN_EBOS": "Selisih EBOS telah disesuaikan dengan UK 500k"},
        {"NO_LAPORAN": "EBOS-202607-002", "WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "TANGGAL": "2026-06-25", "TIPE_MESIN": "ITM", "NOMINAL_SELISIH": 3350000, "STATUS_EBOS": "In Review", "CATATAN_EBOS": "Menunggu kliring keluhan nasabah tgl 25/06"},
        {"NO_LAPORAN": "EBOS-202607-003", "WSID": "ZDA3", "LOKASI": "WINGS PROBOLINGGO", "TANGGAL": "2026-07-09", "TIPE_MESIN": "ITM", "NOMINAL_SELISIH": 25550000, "STATUS_EBOS": "Closed", "CATATAN_EBOS": "Koreksi administrasi -25,600k disetujui"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"])
    return df

def load_default_ej():
    data = [
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "TANGGAL_EJ": "2026-06-29", "JAM_TX": "20:57", "NO_KARTU_REK": "5379-XXXX-1029", "NOMINAL_EJ": 100000, "STATUS_EJ": "Matched", "CATATAN_EJ": "Tx Jam 20:57 dispenser d.100 x 1 lbr match"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "TANGGAL_EJ": "2026-06-25", "JAM_TX": "13:20", "NO_KARTU_REK": "5221-XXXX-8812", "NOMINAL_EJ": 100000, "STATUS_EJ": "Discrepancy - Short", "CATATAN_EJ": "Uang terdispense sebagian, keluhan nasabah -100k"},
        {"WSID": "ZB3X", "LOKASI": "PT ANEKA TUNA INDONESIA", "TANGGAL_EJ": "2026-07-11", "JAM_TX": "12:14", "NO_KARTU_REK": "5412-XXXX-9001", "NOMINAL_EJ": 2500000, "STATUS_EJ": "Discrepancy - Short", "CATATAN_EJ": "Proses klaim keluhan nasabah tgl 11/07"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL_EJ"] = pd.to_datetime(df["TANGGAL_EJ"])
    return df

def load_default_sislok():
    data = [
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "TANGGAL_AUDIT": "2026-07-03", "STOK_SISLOK_AWAL": 500000, "KAS_MASUK": 317400, "KAS_KELUAR": 316800, "STOK_SISLOK_AKHIR": 500600, "FISIK_KAS_ACTUAL": 500500, "SELISIH_STOK": -100, "STATUS_REVIEW": "Variance Detected"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "TANGGAL_AUDIT": "2026-07-07", "STOK_SISLOK_AWAL": 400000, "KAS_MASUK": 342500, "KAS_KELUAR": 339150, "STOK_SISLOK_AKHIR": 403350, "FISIK_KAS_ACTUAL": 403250, "SELISIH_STOK": -100, "STATUS_REVIEW": "Variance Detected"},
        {"WSID": "Z0X2", "LOKASI": "IDM SUDIMORO MALANG", "TANGGAL_AUDIT": "2026-07-10", "STOK_SISLOK_AWAL": 600000, "KAS_MASUK": 649850, "KAS_KELUAR": 649800, "STOK_SISLOK_AKHIR": 600050, "FISIK_KAS_ACTUAL": 600000, "SELISIH_STOK": -50, "STATUS_REVIEW": "Balanced"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL_AUDIT"] = pd.to_datetime(df["TANGGAL_AUDIT"])
    return df

def load_default_kolong():
    data = [
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "TANGGAL_TEMUAN": "2026-06-29", "DENOMINASI": "100,000", "LEMBAR": 1, "TOTAL_RUPIAH": 100000, "LOKASI_TEMUAN": "Kolong Dispenser", "KETERANGAN": "Ditemukan 1 lbr d.100k di kolong dispenser saat bongkar isi"},
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "TANGGAL_TEMUAN": "2026-06-29", "DENOMINASI": "50,000", "LEMBAR": 3, "TOTAL_RUPIAH": 150000, "LOKASI_TEMUAN": "Fascia Roll / Kolong Bawah", "KETERANGAN": "Ditemukan 3 lbr d.50k terselip di fascia roll"},
        {"WSID": "ZK82", "LOKASI": "IDM WARUNGDOWO PASURUAN", "TANGGAL_TEMUAN": "2026-07-15", "DENOMINASI": "100,000", "LEMBAR": 2, "TOTAL_RUPIAH": 200000, "LOKASI_TEMUAN": "Reject Box Chamber", "KETERANGAN": "Nyangkut di reject chamber 2 lbr d.100k"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL_TEMUAN"] = pd.to_datetime(df["TANGGAL_TEMUAN"])
    return df

# Initialize Session States
if "df_rekon" not in st.session_state:
    st.session_state.df_rekon = load_default_rekon()
if "df_cencon" not in st.session_state:
    st.session_state.df_cencon = load_default_cencon()
if "df_uk" not in st.session_state:
    st.session_state.df_uk = load_default_uk()
if "df_ebos" not in st.session_state:
    st.session_state.df_ebos = load_default_ebos()
if "df_ej" not in st.session_state:
    st.session_state.df_ej = load_default_ej()
if "df_sislok" not in st.session_state:
    st.session_state.df_sislok = load_default_sislok()
if "df_kolong" not in st.session_state:
    st.session_state.df_kolong = load_default_kolong()
if "image_store" not in st.session_state:
    st.session_state.image_store = {}

# Standardize Columns Security Check
def sanitize_df(df, required_cols):
    for col in required_cols:
        if col not in df.columns:
            matches = [c for c in df.columns if c.strip().lower() == col.strip().lower()]
            if matches:
                df.rename(columns={matches[0]: col}, inplace=True)
            else:
                df[col] = "-"
    return df

df_rekon = sanitize_df(st.session_state.df_rekon, [
    "WSID", "LOK", "LOKASI", "Mesin", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", 
    "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", 
    "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", 
    "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
])

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Bank_Central_Asia_logo.svg", width=180)
st.sidebar.title("Navigasi Operasional BCA")

menu = st.sidebar.radio(
    "Pilih Modul / Tabel:",
    [
        "📊 Dashboard Executive Overview",
        "📋 Tabel Utama (Complete Audit)",
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
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🎛️ Filter Global Terminal")
all_mesin = df_rekon["Mesin"].unique().tolist() if "Mesin" in df_rekon.columns else ["O-CRM", "ITM", "CRMHYO", "ACH"]
all_lok = df_rekon["LOK"].unique().tolist() if "LOK" in df_rekon.columns else ["BCA", "T"]

mesin_filter = st.sidebar.multiselect("Tipe Mesin Terminal:", options=all_mesin, default=all_mesin)
lok_filter = st.sidebar.multiselect("Pengelola (LOK):", options=all_lok, default=all_lok)

filtered_df = df_rekon[
    (df_rekon["Mesin"].isin(mesin_filter)) &
    (df_rekon["LOK"].isin(lok_filter))
]

# ---------------------------------------------------------
# Executive Header Banner
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <h1>BCA ATM Reconciliation & Integrated Operational System</h1>
            <p>Sistem Pengawasan Rekonsiliasi Kas, Audit UK BDC, Tes Cash, Cencon, Sislok Stock, Staff & CRUD Terpadu</p>
        </div>
        <div style="text-align: right;">
            <span class="status-badge">🟢 LIVE RECONCILIATION</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Helper for Safe Formatting in Streamlit Dataframe
def display_styled_df(df, num_cols):
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
    st.subheader("📌 Ringkasan Eksekutif Rekonsiliasi Kas & Operasional")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Terminal", f"{len(filtered_df)} Unit")
    with col2:
        tot_pos = filtered_df["CASH_POS"].sum() * 1000 if "CASH_POS" in filtered_df.columns else 0
        st.metric("Total Cash Position", f"Rp {tot_pos:,.0f}")
    with col3:
        tot_setor = filtered_df["SETOR"].sum() * 1000 if "SETOR" in filtered_df.columns else 0
        st.metric("Total Disetor", f"Rp {tot_setor:,.0f}")
    with col4:
        tot_sel_awal = filtered_df["SEL_AWAL"].sum() * 1000 if "SEL_AWAL" in filtered_df.columns else 0
        st.metric("Total Selisih Awal", f"Rp {tot_sel_awal:,.0f}", delta=f"{tot_sel_awal:,.0f}", delta_color="inverse")
    with col5:
        tot_sel_akhir = filtered_df["SEL_AKHIR"].sum() * 1000 if "SEL_AKHIR" in filtered_df.columns else 0
        st.metric("Total Selisih Akhir", f"Rp {tot_sel_akhir:,.0f}", delta=f"{tot_sel_akhir:,.0f}", delta_color="inverse")

    st.markdown("---")

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

    st.markdown("---")
    st.markdown("### 💡 Audit Status Temuan Kas Operasional Ringkas")
    col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
    with col_sum1:
        st.info(f"**Close/Open Cencon:** {len(st.session_state.df_cencon)} Transaksi Recorded")
    with col_sum2:
        st.warning(f"**Uang Kembali (UK):** {len(st.session_state.df_uk)} Entri Pengembalian")
    with col_sum3:
        st.error(f"**Laporan EBOS:** {len(st.session_state.df_ebos)} Laporan Terdaftar")
    with col_sum4:
        tot_kolong_rp = st.session_state.df_kolong["TOTAL_RUPIAH"].sum() if "TOTAL_RUPIAH" in st.session_state.df_kolong.columns else 0
        st.success(f"**Uang Kolong:** Rp {tot_kolong_rp:,.0f} Total Temuan")

# ---------------------------------------------------------
# MODUL 2: TABEL UTAMA COMPLETE AUDIT
# ---------------------------------------------------------
elif menu == "📋 Tabel Utama (Complete Audit)":
    st.subheader("📋 Rekonsiliasi Utama Lengkap (Termasuk UK BDC, Tes Cash, Cencon, Rekon Sislok & Review Stock)")

    search_kw = st.text_input("🔍 Cari WSID, Lokasi, Status UK BDC, Tes Cash, atau Staff:", "")
    
    disp_df = filtered_df.copy()
    if search_kw:
        mask = (
            disp_df["WSID"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["LOKASI"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["UK_BDC"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["TEST_CASH"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["CLOSE_OPEN_CENCON"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["REKON_SISLOK"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["STAFF_1"].astype(str).str.contains(search_kw, case=False, na=False)
        )
        disp_df = disp_df[mask]

    formatted_df = disp_df.copy()
    if "TGL_INS" in formatted_df.columns and pd.api.types.is_datetime64_any_dtype(formatted_df["TGL_INS"]):
        formatted_df["TGL_INS"] = formatted_df["TGL_INS"].dt.strftime("%Y-%m-%d")
    if "TGL_REM" in formatted_df.columns and pd.api.types.is_datetime64_any_dtype(formatted_df["TGL_REM"]):
        formatted_df["TGL_REM"] = formatted_df["TGL_REM"].dt.strftime("%Y-%m-%d")

    # Display Columns on Main Table including requested fields
    cols_to_show = [
        "WSID", "LOK", "LOKASI", "Mesin", "TGL_INS", "TGL_REM", 
        "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR",
        "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", "REKON_SISLOK", "REVIEW_STOCK",
        "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
    ]
    cols_exist = [c for c in cols_to_show if c in formatted_df.columns]
    
    st.markdown("#### 📊 Tabel Utama Rekonsiliasi Kas")
    display_styled_df(formatted_df[cols_exist], ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"])

    st.markdown("---")
    st.markdown("### 👷 Detail Audit Operasional Terpadu per WSID")
    if not disp_df.empty:
        selected_wsid = st.selectbox("Pilih WSID untuk melihat rincian Lengkap (UK BDC, Tes Cash, Sislok & Staff):", disp_df["WSID"].unique())
        wsid_row = disp_df[disp_df["WSID"] == selected_wsid].iloc[0]
        
        tab_dt1, tab_dt2, tab_dt3, tab_dt4 = st.tabs(["💳 UK BDC & Tes Cash", "📦 Sislok & Review Stock", "👥 Staff & Driver", "📸 Foto Bukti"])
        
        with tab_dt1:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown("##### 💳 UK BDC / Uang Kembali")
                st.info(f"**Rincian UK BDC:** {wsid_row.get('UK_BDC', '-')}")
            with c2:
                st.markdown("##### 💵 Tes Cash")
                st.success(f"**Status Tes Cash:** {wsid_row.get('TEST_CASH', '-')}")
            with c3:
                st.markdown("##### 🔑 Close / Open Cencon")
                st.warning(f"**Status Cencon:** {wsid_row.get('CLOSE_OPEN_CENCON', '-')}")

        with tab_dt2:
            s1, s2 = st.columns(2)
            with s1:
                st.markdown("##### 📦 Rekon Sislok")
                st.info(f"**Status Rekon Sislok:** {wsid_row.get('REKON_SISLOK', '-')}")
            with s2:
                st.markdown("##### 📊 Review Stock Kas")
                st.write(f"**Rincian Review Stock:** {wsid_row.get('REVIEW_STOCK', '-')}")

        with tab_dt3:
            p1, p2, p3 = st.columns(3)
            with p1:
                st.write(f"**WSID / Terminal:** {wsid_row['WSID']} ({wsid_row['Mesin']})")
                st.write(f"**Lokasi:** {wsid_row['LOKASI']}")
                st.write(f"**Pengelola (LOK):** {wsid_row['LOK']}")
            with p2:
                st.write(f"**Petugas 1:** 👤 {wsid_row.get('STAFF_1', '-')}")
                st.write(f"**Petugas 2:** 👤 {wsid_row.get('STAFF_2', '-')}")
                st.write(f"**Petugas 3:** 👤 {wsid_row.get('STAFF_3', '-')}")
            with p3:
                st.write(f"**Driver Pengawal:** 🚚 {wsid_row.get('DRIVER', '-')}")
                st.write(f"**Aktivitas Jam:** ⏱️ {wsid_row.get('ACTIVITY', '-')}")
                st.write(f"**Catatan Lapangan:** 📝 {wsid_row.get('CATATAN_PROSES', '-')}")

        with tab_dt4:
            if selected_wsid in st.session_state.image_store:
                st.markdown("#### 📸 Foto Bukti Lapangan / Catatan Papan Tulis:")
                st.image(st.session_state.image_store[selected_wsid], caption=f"Bukti Fisik Rekonsiliasi WSID {selected_wsid}", width=450)
            else:
                st.info(f"💡 Belum ada foto bukti khusus yang diunggah untuk WSID {selected_wsid}. Anda dapat mengunggahnya pada menu **📸 Unggah & Galeri Foto Bukti**.")

# ---------------------------------------------------------
# MODUL 3: CLOSE / OPEN CENCON & TES CASH
# ---------------------------------------------------------
elif menu == "💵 Close / Open Cencon & Tes Cash":
    st.subheader("💵 Pengawasan Close / Open Cencon & Tes Cash")
    df_cen = st.session_state.df_cencon.copy()
    if "TANGGAL" in df_cen.columns and pd.api.types.is_datetime64_any_dtype(df_cen["TANGGAL"]):
        df_cen["TANGGAL"] = df_cen["TANGGAL"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_cen, ["BDC", "NON_BDC"])

# ---------------------------------------------------------
# MODUL 4: UK TC, UK BDC & UK SICLUS
# ---------------------------------------------------------
elif menu == "🔄 UK TC, UK BDC & UK Siclus":
    st.subheader("🔄 Audit Uang Kembali (UK TC, UK BDC, UK Siclus)")
    df_u = st.session_state.df_uk.copy()
    if "TANGGAL" in df_u.columns and pd.api.types.is_datetime64_any_dtype(df_u["TANGGAL"]):
        df_u["TANGGAL"] = df_u["TANGGAL"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_u, ["BDC", "NON_BDC", "TOTAL_UK"])

# ---------------------------------------------------------
# MODUL 5: LAPORAN EBOS
# ---------------------------------------------------------
elif menu == "📑 Laporan EBOS":
    st.subheader("📑 Monitoring & Registrasi Laporan EBOS")
    df_eb = st.session_state.df_ebos.copy()
    if "TANGGAL" in df_eb.columns and pd.api.types.is_datetime64_any_dtype(df_eb["TANGGAL"]):
        df_eb["TANGGAL"] = df_eb["TANGGAL"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_eb, ["NOMINAL_SELISIH"])

# ---------------------------------------------------------
# MODUL 6: REKON EJ (ELECTRONIC JOURNAL)
# ---------------------------------------------------------
elif menu == "💻 Rekon EJ (Electronic Journal)":
    st.subheader("💻 Rekonsiliasi Electronic Journal (EJ Audit)")
    df_j = st.session_state.df_ej.copy()
    if "TANGGAL_EJ" in df_j.columns and pd.api.types.is_datetime64_any_dtype(df_j["TANGGAL_EJ"]):
        df_j["TANGGAL_EJ"] = df_j["TANGGAL_EJ"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_j, ["NOMINAL_EJ"])

# ---------------------------------------------------------
# MODUL 7: REKON SISLOK & REVIEW STOCK
# ---------------------------------------------------------
elif menu == "📦 Rekon Sislok & Review Stock":
    st.subheader("📦 Rekonsiliasi Sistem Lokasi (Sislok) & Review Stock Kas")
    df_s = st.session_state.df_sislok.copy()
    if "TANGGAL_AUDIT" in df_s.columns and pd.api.types.is_datetime64_any_dtype(df_s["TANGGAL_AUDIT"]):
        df_s["TANGGAL_AUDIT"] = df_s["TANGGAL_AUDIT"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_s, ["STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR", "STOK_SISLOK_AKHIR", "FISIK_KAS_ACTUAL", "SELISIH_STOK"])

# ---------------------------------------------------------
# MODUL 8: UANG KOLONG & TEMUAN FISIK
# ---------------------------------------------------------
elif menu == "🪙 Uang Kolong & Temuan Fisik":
    st.subheader("🪙 Pencatatan Uang Kolong & Temuan Fisik Terselip")
    df_k = st.session_state.df_kolong.copy()
    if "TANGGAL_TEMUAN" in df_k.columns and pd.api.types.is_datetime64_any_dtype(df_k["TANGGAL_TEMUAN"]):
        df_k["TANGGAL_TEMUAN"] = df_k["TANGGAL_TEMUAN"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_k, ["LEMBAR", "TOTAL_RUPIAH"])

# ---------------------------------------------------------
# MODUL 9: UNGGAH & GALERI FOTO BUKTI
# ---------------------------------------------------------
elif menu == "📸 Unggah & Galeri Foto Bukti":
    st.subheader("📸 Galeri & Unggah Lampiran Foto Bukti Fisik")
    col_up1, col_up2 = st.columns([1, 1])

    with col_up1:
        st.markdown("### 📤 Unggah Foto Bukti Baru")
        target_wsid = st.selectbox("Pilih WSID Target:", df_rekon["WSID"].unique())
        uploaded_img = st.file_uploader("Unggah File Foto Bukti (PNG / JPG / JPEG):", type=["png", "jpg", "jpeg"])
        if uploaded_img is not None:
            st.session_state.image_store[target_wsid] = uploaded_img.read()
            st.success(f"Foto bukti untuk WSID {target_wsid} berhasil diunggah!")

    with col_up2:
        st.markdown("### 🖼️ Preview Foto Bukti Tersimpan")
        view_wsid = st.selectbox("Pilih WSID untuk Pratinjau:", df_rekon["WSID"].unique(), key="preview_wsid")
        if view_wsid in st.session_state.image_store:
            st.image(st.session_state.image_store[view_wsid], caption=f"Bukti Fisik WSID {view_wsid}", use_container_width=True)
        else:
            st.info(f"Belum ada foto bukti yang diunggah untuk WSID {view_wsid}.")

# ---------------------------------------------------------
# MODUL 10: KELOLA DATA (FULL CRUD OPERATIONS)
# ---------------------------------------------------------
elif menu == "🛠️ Kelola Data (CRUD Operations)":
    st.subheader("🛠️ Manajemen Data Terpadu (Create, Read, Update, Delete)")

    crud_target = st.selectbox(
        "Pilih Tabel Operasional yang Ingin Dikelola:",
        [
            "📋 Rekonsiliasi Utama & UK BDC / Tes Cash / Sislok",
            "💵 Close / Open Cencon & Tes Cash",
            "🔄 Uang Kembali (UK)",
            "📑 Laporan EBOS",
            "💻 Rekon Electronic Journal (EJ)",
            "📦 Rekon Sislok & Stock",
            "🪙 Uang Kolong"
        ]
    )

    st.markdown("---")

    # TABEL 1: REKONSILIASI UTAMA CRUD
    if crud_target == "📋 Rekonsiliasi Utama & UK BDC / Tes Cash / Sislok":
        crud_action = st.radio("Pilih Aksi CRUD:", ["➕ CREATE (Tambah Data)", "👁️ READ (Lihat Data)", "✏️ UPDATE (Edit Data)", "🗑️ DELETE (Hapus Data)"], horizontal=True)
        
        if crud_action == "➕ CREATE (Tambah Data)":
            st.markdown("#### ➕ Tambah Record Rekonsiliasi Utama Baru")
            with st.form("crud_create_rekon"):
                c1, c2, c3 = st.columns(3)
                with c1:
                    c_wsid = st.text_input("WSID Terminal", "Z99M")
                    c_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
                    c_lokasi = st.text_input("Nama Lokasi", "KCP MALANG KOTA")
                    c_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
                with c2:
                    c_tgl_ins = st.date_input("Tanggal Pengisian (TGL_INS)")
                    c_tgl_rem = st.date_input("Tanggal Penarikan (TGL_REM)")
                    c_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=500000)
                    c_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=499500)
                    c_sel_awal = c_setor - c_cash_pos
                    c_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100)
                with c3:
                    c_uk_bdc = st.text_input("UK BDC / Rincian UK", "Rp 500,000 (UK Siclus)")
                    c_test_cash = st.text_input("Tes Cash Status", "Rp 100,000 (NON-BDC)")
                    c_cencon = st.selectbox("Close / Open Cencon", ["Close", "Open", "Pending"])
                    c_sislok = st.text_input("Rekon Sislok Status", "Variance (-100)")
                    c_review_stock = st.text_input("Review Stock Kas", "Sislok: 500,000 | Fisik: 499,900")

                st.markdown("##### 👥 Petugas / Staff & Log Audit")
                st1, st2, st3, st4 = st.columns(4)
                with st1:
                    c_staff1 = st.text_input("Petugas 1", "BAYU OKTA PURWANTO")
                with st2:
                    c_staff2 = st.text_input("Petugas 2", "AKHMAD RIZA MAULANA")
                with st3:
                    c_staff3 = st.text_input("Petugas 3", "MUHAMMAD RIZAL MUZAKHI")
                with st4:
                    c_driver = st.text_input("Driver", "ASSYAVI ALIYULLOH M")

                c_act = st.text_input("Aktivitas Jam", f"{datetime.now().strftime('%d/%m/%y %H:%M')} - BONGKAR ISI")
                c_catatan = st.text_input("Catatan Lapangan", "Proses normal")
                c_tanggapan = st.text_area("Tanggapan BCA", f"Selisih Awal : {c_sel_awal}\nSelisih Akhir : {c_sel_akhir}")

                sub_c = st.form_submit_button("💾 [CREATE] Simpan Data Baru")
                if sub_c:
                    new_rec = {
                        "WSID": c_wsid, "LOK": c_lok, "LOKASI": c_lokasi, "Mesin": c_mesin,
                        "TGL_INS": pd.to_datetime(c_tgl_ins), "TGL_REM": pd.to_datetime(c_tgl_rem),
                        "CASH_POS": c_cash_pos, "SETOR": c_setor, "SEL_AWAL": c_sel_awal, "SEL_AKHIR": c_sel_akhir,
                        "UK_BDC": c_uk_bdc, "TEST_CASH": c_test_cash, "CLOSE_OPEN_CENCON": c_cencon,
                        "REKON_SISLOK": c_sislok, "REVIEW_STOCK": c_review_stock,
                        "STAFF_1": c_staff1, "STAFF_2": c_staff2, "STAFF_3": c_staff3, "DRIVER": c_driver,
                        "ACTIVITY": c_act, "CATATAN_PROSES": c_catatan, "TANGGAPAN_BCA": c_tanggapan
                    }
                    st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_rec])], ignore_index=True)
                    st.success(f"Record {c_wsid} berhasil dibuat!")
                    safe_rerun()

        elif crud_action == "👁️ READ (Lihat Data)":
            st.markdown("#### 👁️ Database Rekonsiliasi Utama")
            st.dataframe(st.session_state.df_rekon, use_container_width=True)

        elif crud_action == "✏️ UPDATE (Edit Data)":
            st.markdown("#### ✏️ Update Record Rekonsiliasi Utama")
            if not st.session_state.df_rekon.empty:
                idx_edit = st.number_input("Pilih Index Baris yang Ingin Di-edit (0 - N):", min_value=0, max_value=len(st.session_state.df_rekon)-1, value=0)
                row_edit = st.session_state.df_rekon.iloc[idx_edit]
                st.info(f"Mengedit WSID: **{row_edit['WSID']}** ({row_edit['LOKASI']})")

                with st.form("crud_update_rekon"):
                    u1, u2, u3 = st.columns(3)
                    with u1:
                        e_wsid = st.text_input("WSID Terminal", row_edit['WSID'])
                        e_lok = st.selectbox("LOK", ["BCA", "T"], index=0 if row_edit['LOK']=="BCA" else 1)
                        e_lokasi = st.text_input("Nama Lokasi", row_edit['LOKASI'])
                        e_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"], index=["O-CRM", "ITM", "CRMHYO", "ACH"].index(row_edit['Mesin']) if row_edit['Mesin'] in ["O-CRM", "ITM", "CRMHYO", "ACH"] else 0)
                    with u2:
                        e_cash_pos = st.number_input("Cash Position Sistem", value=float(row_edit['CASH_POS']))
                        e_setor = st.number_input("Total Disetor Aktual", value=float(row_edit['SETOR']))
                        e_sel_awal = e_setor - e_cash_pos
                        e_sel_akhir = st.number_input("Selisih Akhir Audit", value=float(row_edit['SEL_AKHIR']))
                    with u3:
                        e_uk_bdc = st.text_input("UK BDC / Rincian", str(row_edit.get('UK_BDC', '-')))
                        e_test_cash = st.text_input("Tes Cash Status", str(row_edit.get('TEST_CASH', '-')))
                        e_cencon = st.selectbox("Close / Open Cencon", ["Close", "Open", "Pending"], index=0 if str(row_edit.get('CLOSE_OPEN_CENCON'))=="Close" else 1)
                        e_sislok = st.text_input("Rekon Sislok Status", str(row_edit.get('REKON_SISLOK', '-')))
                        e_review_stock = st.text_input("Review Stock Kas", str(row_edit.get('REVIEW_STOCK', '-')))

                    e_staff1 = st.text_input("Petugas 1", str(row_edit.get('STAFF_1', '-')))
                    e_driver = st.text_input("Driver", str(row_edit.get('DRIVER', '-')))
                    e_tanggapan = st.text_area("Tanggapan BCA", str(row_edit.get('TANGGAPAN_BCA', '-')))

                    sub_u = st.form_submit_button("✏️ [UPDATE] Simpan Perubahan Data")
                    if sub_u:
                        st.session_state.df_rekon.at[idx_edit, 'WSID'] = e_wsid
                        st.session_state.df_rekon.at[idx_edit, 'LOK'] = e_lok
                        st.session_state.df_rekon.at[idx_edit, 'LOKASI'] = e_lokasi
                        st.session_state.df_rekon.at[idx_edit, 'Mesin'] = e_mesin
                        st.session_state.df_rekon.at[idx_edit, 'CASH_POS'] = e_cash_pos
                        st.session_state.df_rekon.at[idx_edit, 'SETOR'] = e_setor
                        st.session_state.df_rekon.at[idx_edit, 'SEL_AWAL'] = e_sel_awal
                        st.session_state.df_rekon.at[idx_edit, 'SEL_AKHIR'] = e_sel_akhir
                        st.session_state.df_rekon.at[idx_edit, 'UK_BDC'] = e_uk_bdc
                        st.session_state.df_rekon.at[idx_edit, 'TEST_CASH'] = e_test_cash
                        st.session_state.df_rekon.at[idx_edit, 'CLOSE_OPEN_CENCON'] = e_cencon
                        st.session_state.df_rekon.at[idx_edit, 'REKON_SISLOK'] = e_sislok
                        st.session_state.df_rekon.at[idx_edit, 'REVIEW_STOCK'] = e_review_stock
                        st.session_state.df_rekon.at[idx_edit, 'STAFF_1'] = e_staff1
                        st.session_state.df_rekon.at[idx_edit, 'DRIVER'] = e_driver
                        st.session_state.df_rekon.at[idx_edit, 'TANGGAPAN_BCA'] = e_tanggapan
                        st.success(f"Data index {idx_edit} ({e_wsid}) berhasil diperbarui!")
                        safe_rerun()

        elif crud_action == "🗑️ DELETE (Hapus Data)":
            st.markdown("#### 🗑️ Hapus Record Rekonsiliasi Utama")
            if not st.session_state.df_rekon.empty:
                idx_del = st.number_input("Pilih Index Baris yang Ingin Dihapus:", min_value=0, max_value=len(st.session_state.df_rekon)-1, value=0)
                row_del = st.session_state.df_rekon.iloc[idx_del]
                st.error(f"⚠️ Yakin ingin menghapus record Index **{idx_del}**: WSID **{row_del['WSID']}** ({row_del['LOKASI']})?")

                if st.button("🗑️ [DELETE] Konfirmasi Hapus Record Ini"):
                    st.session_state.df_rekon = st.session_state.df_rekon.drop(idx_del).reset_index(drop=True)
                    st.success(f"Record index {idx_del} berhasil dihapus!")
                    safe_rerun()

    else:
        st.info("💡 Silakan gunakan modul tabel spesifik pada bilah navigasi untuk mengelola data Cencon, UK, EBOS, EJ, Sislok, dan Uang Kolong secara interaktif.")

# ---------------------------------------------------------
# MODUL 11: INPUT & TAMBAH DATA TERPADU
# ---------------------------------------------------------
elif menu == "➕ Input & Tambah Data Terpadu":
    st.subheader("📝 Form Penginputan Data Rekonsiliasi, UK BDC, Tes Cash, Cencon & Sislok Terpadu")

    tab_in1, tab_in2, tab_in3, tab_in4 = st.tabs(["📋 Rekon Utama & UK BDC", "💵 Cencon & Tes Cash", "📦 Sislok & Review Stock", "📸 Foto Bukti"])

    with tab_in1:
        st.markdown("#### 📝 Input Rekonsiliasi Utama & UK BDC")
        with st.form("form_terpadu_rekon"):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                in_wsid = st.text_input("WSID Terminal", "Z88M")
                in_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
                in_lokasi = st.text_input("Lokasi Terminal", "PURWOSARI CRM 3")
                in_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
            with col_f2:
                in_tgl_ins = st.date_input("Tanggal Pengisian (TGL_INS)")
                in_tgl_rem = st.date_input("Tanggal Penarikan (TGL_REM)")
                in_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=400000)
                in_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=399500)
                in_sel_awal = in_setor - in_cash_pos
                in_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100)
            with col_f3:
                in_uk_bdc = st.text_input("UK BDC / Rincian UK", "Rp 500,000 (UK Siclus)")
                in_test_cash = st.text_input("Tes Cash Status", "Rp 100,000 (NON-BDC)")
                in_cencon = st.selectbox("Close / Open Cencon", ["Close", "Open", "Pending"])
                in_sislok = st.text_input("Rekon Sislok Status", "Variance (-100)")
                in_review_stock = st.text_input("Review Stock Kas", "Sislok: 400,000 | Fisik: 399,900")

            st.markdown("##### 👥 Staff Operasional")
            st_col1, st_col2, st_col3, st_col4 = st.columns(4)
            with st_col1:
                in_staff1 = st.text_input("Petugas 1", "BAYU OKTA PURWANTO")
            with st_col2:
                in_staff2 = st.text_input("Petugas 2", "AKHMAD RIZA MAULANA")
            with st_col3:
                in_staff3 = st.text_input("Petugas 3", "YOYOK BUDI RAKHMAN")
            with st_col4:
                in_driver = st.text_input("Driver", "ASSYAVI ALIYULLOH M")

            in_act = st.text_input("Aktivitas Jam", f"{datetime.now().strftime('%d/%m/%y %H:%M')} - BONGKAR ISI")
            in_catatan = st.text_input("Catatan Lapangan", "Proses normal, UK d.100 x 1 lbr")
            in_tanggapan = st.text_area("Tanggapan BCA / Audit Log", f"Selisih Awal : {in_sel_awal}\nUK : {abs(in_sel_awal - in_sel_akhir)}\nSelisih Akhir : {in_sel_akhir}")

            sub_terpadu = st.form_submit_button("💾 Simpan Data Transaksi Terpadu")
            if sub_terpadu:
                new_row = {
                    "WSID": in_wsid, "LOK": in_lok, "LOKASI": in_lokasi, "Mesin": in_mesin,
                    "TGL_INS": pd.to_datetime(in_tgl_ins), "TGL_REM": pd.to_datetime(in_tgl_rem),
                    "CASH_POS": in_cash_pos, "SETOR": in_setor, "SEL_AWAL": in_sel_awal, "SEL_AKHIR": in_sel_akhir,
                    "UK_BDC": in_uk_bdc, "TEST_CASH": in_test_cash, "CLOSE_OPEN_CENCON": in_cencon,
                    "REKON_SISLOK": in_sislok, "REVIEW_STOCK": in_review_stock,
                    "STAFF_1": in_staff1, "STAFF_2": in_staff2, "STAFF_3": in_staff3,
                    "DRIVER": in_driver, "ACTIVITY": in_act, "CATATAN_PROSES": in_catatan,
                    "TANGGAPAN_BCA": in_tanggapan
                }
                st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Data WSID {in_wsid} berhasil ditambahkan!")
                safe_rerun()

    with tab_in2:
        st.markdown("#### 💵 Input Close / Open Cencon & Tes Cash")
        with st.form("form_terpadu_cencon"):
            tc1, tc2 = st.columns(2)
            with tc1:
                tc_wsid = st.text_input("WSID Terminal", "Z5UM")
                tc_lokasi = st.text_input("Nama Lokasi", "CRM PURWOSARI 2")
                tc_tgl = st.date_input("Tanggal Transaksi")
                tc_jam = st.text_input("Jam (HH:MM)", "20:22")
            with tc2:
                tc_bdc = st.number_input("Nominal BDC (Rp)", value=0, step=10000)
                tc_non_bdc = st.number_input("Nominal NON-BDC (Rp)", value=100000, step=10000)
                tc_status = st.selectbox("Status Cencon", ["Close", "Open", "Pending"])
                tc_ket = st.text_input("Keterangan Tes Cash", "Tes cash sesuai 100,000")

            sub_tc = st.form_submit_button("💾 Simpan Data Cencon & Tes Cash")
            if sub_tc:
                new_c = {
                    "WSID": tc_wsid, "LOKASI": tc_lokasi, "TANGGAL": pd.to_datetime(tc_tgl),
                    "JAM": tc_jam, "BDC": tc_bdc, "NON_BDC": tc_non_bdc,
                    "STATUS": tc_status, "KETERANGAN": tc_ket
                }
                st.session_state.df_cencon = pd.concat([st.session_state.df_cencon, pd.DataFrame([new_c])], ignore_index=True)
                st.success("Record Cencon berhasil ditambahkan!")
                safe_rerun()

    with tab_in3:
        st.markdown("#### 📦 Input Rekon Sislok & Review Stock")
        with st.form("form_terpadu_sislok"):
            s1, s2 = st.columns(2)
            with s1:
                s_wsid = st.text_input("WSID Terminal", "Z0X2")
                s_lokasi = st.text_input("Lokasi Terminal", "IDM SUDIMORO MALANG")
                s_tgl = st.date_input("Tanggal Audit Stock")
                s_awal = st.number_input("Stok Sislok Awal (Ribu Rp)", value=600000, step=10000)
            with s2:
                s_masuk = st.number_input("Kas Masuk (Ribu Rp)", value=649850, step=10000)
                s_keluar = st.number_input("Kas Keluar (Ribu Rp)", value=649800, step=10000)
                s_fisik = st.number_input("Fisik Kas Actual (Ribu Rp)", value=600000, step=10000)
                s_sislok_akhir = s_awal + s_masuk - s_keluar
                s_selisih = s_fisik - s_sislok_akhir

            sub_sislok = st.form_submit_button("💾 Simpan Record Sislok & Stock")
            if sub_sislok:
                new_s = {
                    "WSID": s_wsid, "LOKASI": s_lokasi, "TANGGAL_AUDIT": pd.to_datetime(s_tgl),
                    "STOK_SISLOK_AWAL": s_awal, "KAS_MASUK": s_masuk, "KAS_KELUAR": s_keluar,
                    "STOK_SISLOK_AKHIR": s_sislok_akhir, "FISIK_KAS_ACTUAL": s_fisik,
                    "SELISIH_STOK": s_selisih, "STATUS_REVIEW": "Balanced" if s_selisih==0 else "Variance Detected"
                }
                st.session_state.df_sislok = pd.concat([st.session_state.df_sislok, pd.DataFrame([new_s])], ignore_index=True)
                st.success("Record Sislok berhasil ditambahkan!")
                safe_rerun()

    with tab_in4:
        st.markdown("#### 📸 Unggah Foto Bukti Fisik")
        up_target = st.selectbox("Pilih WSID Target:", df_rekon["WSID"].unique(), key="in_img_target")
        up_file = st.file_uploader("Pilih File Gambar Foto Bukti (PNG / JPG / JPEG):", type=["png", "jpg", "jpeg"], key="in_img_file")
        if up_file is not None:
            st.session_state.image_store[up_target] = up_file.read()
            st.success(f"Foto bukti untuk WSID {up_target} berhasil diunggah!")

# ---------------------------------------------------------
# MODUL 12: EKSPOR & IMPOR DATA EXCEL
# ---------------------------------------------------------
elif menu == "📁 Ekspor & Impor Data Excel":
    st.subheader("📥 Unduh Seluruh Workbook Laporan Rekonsiliasi (.xlsx)")
    st.write("Ekspor seluruh modul tabel ke dalam satu file Excel multi-sheet terpadu.")

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
        st.markdown("### 📤 Upload Master Excel Rekonsiliasi")
        uploaded_file = st.file_uploader("Pilih file Excel (.xlsx) untuk memperbarui data:", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    new_df = pd.read_csv(uploaded_file)
                else:
                    new_df = pd.read_excel(uploaded_file)

                st.session_state.df_rekon = new_df
                st.success("Master data rekonsiliasi berhasil dimuat!")
                safe_rerun()
            except Exception as e:
                st.error(f"Gagal memuat file: {e}")
