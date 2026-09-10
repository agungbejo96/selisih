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
    page_title="Sistem Rekonsiliasi Kas BCA + Selisih Per Bulan",
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
            "BULAN": "Juni 2026",
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
            "TANGGAPAN_BCA": "Selisih Awal : -600\\nUK : 500\\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZM16", "LOK": "T", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "Mesin": "ITM",
            "BULAN": "Juni 2026",
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
            "TANGGAPAN_BCA": "Selisih Awal : -3,350\\nUK : 3,350\\nKeluhan Nsb : -100 tgl 25/06 jam 13:20\\nSelisih Akhir : -100"
        },
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
            "TANGGAPAN_BCA": "Selisih Awal : -50\\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZDA3", "LOK": "T", "LOKASI": "WINGS PROBOLINGGO", "Mesin": "ITM",
            "BULAN": "Juli 2026",
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
            "TANGGAPAN_BCA": "Selisih Awal : 25,550\\nKoreksi Adm : -25,600\\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZB3X", "LOK": "T", "LOKASI": "PT ANEKA TUNA INDONESIA", "Mesin": "CRMHYO",
            "BULAN": "Juli 2026",
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
            "TANGGAPAN_BCA": "Selisih Awal : 12,900\\nKeluhan Nsb : -2,500 tgl 11/07 jam 12:14\\n-2,500 tgl 11/07 jam 12:13\\n-2,500 tgl 11/07 jam 12:11\\n-500 tgl 11/07 jam 10:33\\n-2,500 tgl 11/07 jam 09:17\\n-2,500 tgl 11/07 jam 15:02\\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZK82", "LOK": "T", "LOKASI": "IDM WARUNGDOWO PASURUAN", "Mesin": "O-CRM",
            "BULAN": "Juli 2026",
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
            "TANGGAPAN_BCA": "Selisih Awal : -4,250\\nKeluhan Nsb : -1,200 tgl 15/07 jam 19:25\\nUK : 5,400\\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZH9M", "LOK": "BCA", "LOKASI": "KRAKSAAN", "Mesin": "ITM",
            "BULAN": "Juli 2026",
            "TGL_INS": "2026-07-12", "TGL_REM": "2026-07-15", "CASH_POS": 679350, "SETOR": 679150,
            "SEL_AWAL": -200, "SEL_AKHIR": -100,
            "UK_BDC": "Rp 200,000 (UK BDC)",
            "TEST_CASH": "Rp 100,000",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-100)",
            "REVIEW_STOCK": "Sislok: 679,350 | Fisik: 679,250",
            "STAFF_1": "BAYU OKTA PURWANTO", "STAFF_2": "AKHMAD RIZA MAULANA",
            "STAFF_3": "-", "DRIVER": "ASSYAVI ALIYULLOH M",
            "ACTIVITY": "12/07/26 15:10 - BONGKAR ISI",
            "CATATAN_PROSES": "Koreksi adm -100 & UK 200",
            "TANGGAPAN_BCA": "Selisih Awal : -200\\nKoreksi Adm : -100\\nUK : 200\\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZQ8Y", "LOK": "T", "LOKASI": "ALFAMD MERTOJOYO MALANG", "Mesin": "ACH",
            "BULAN": "Juli 2026",
            "TGL_INS": "2026-07-01", "TGL_REM": "2026-07-17", "CASH_POS": 668650, "SETOR": 668500,
            "SEL_AWAL": -150, "SEL_AKHIR": -50,
            "UK_BDC": "Rp 150,000 (UK TC)",
            "TEST_CASH": "Rp 100,000",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-50)",
            "REVIEW_STOCK": "Sislok: 668,650 | Fisik: 668,600",
            "STAFF_1": "YOYOK BUDI RAKHMAN", "STAFF_2": "ADAM REYHAN HERLAMBANG",
            "STAFF_3": "-", "DRIVER": "SGI VENDOR",
            "ACTIVITY": "01/07/26 14:00 - PENGISIAN",
            "CATATAN_PROSES": "Keluhan nsb -50 & UK 150",
            "TANGGAPAN_BCA": "Selisih Awal : -150\\nKeluhan Nsb : -50 tgl 13/07 jam 15:19\\nUK : 150\\nSelisih Akhir : -50"
        },
        {
            "WSID": "Z99A", "LOK": "BCA", "LOKASI": "KCP MALANG KOTA", "Mesin": "O-CRM",
            "BULAN": "Agustus 2026",
            "TGL_INS": "2026-08-01", "TGL_REM": "2026-08-05", "CASH_POS": 500000, "SETOR": 499800,
            "SEL_AWAL": -200, "SEL_AKHIR": -50,
            "UK_BDC": "Rp 150,000 (UK Siclus)",
            "TEST_CASH": "Rp 100,000",
            "CLOSE_OPEN_CENCON": "Close",
            "REKON_SISLOK": "Variance (-50)",
            "REVIEW_STOCK": "Sislok: 500,000 | Fisik: 499,950",
            "STAFF_1": "RIZKY PRATAMA", "STAFF_2": "BAMBANG HERMANTO",
            "STAFF_3": "-", "DRIVER": "ASSYAVI ALIYULLOH M",
            "ACTIVITY": "01/08/26 10:00 - BONGKAR ISI",
            "CATATAN_PROSES": "Proses normal bulan Agustus",
            "TANGGAPAN_BCA": "Selisih Awal : -200\\nUK : 150\\nSelisih Akhir : -50"
        }
    ]
    df = pd.DataFrame(data)
    df["TGL_INS"] = pd.to_datetime(df["TGL_INS"])
    df["TGL_REM"] = pd.to_datetime(df["TGL_REM"])
    return df

def load_default_cencon():
    data = [
        {"WSID": "Z5UM", "LOKASI": "CRM PURWOSARI 2", "BULAN": "Juni 2026", "TANGGAL": "2026-06-27", "JAM": "20:22", "BDC": 0, "NON_BDC": 100000, "STATUS": "Close", "KETERANGAN": "Tes Cash Sesuai 100,000"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI", "BULAN": "Juni 2026", "TANGGAL": "2026-06-25", "JAM": "21:34", "BDC": 50000, "NON_BDC": 50000, "STATUS": "Open", "KETERANGAN": "Tes Cash Pending Konfirmasi"},
        {"WSID": "ZB3X", "LOKASI": "PT ANEKA TUNA INDONESIA", "BULAN": "Juli 2026", "TANGGAL": "2026-07-09", "JAM": "12:15", "BDC": 0, "NON_BDC": 200000, "STATUS": "Close", "KETERANGAN": "Tes Cash OK"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"])
    return df

def load_default_uk():
    data = [
        {"WSID": "Z5UM", "LOKASI": "CRM PURWOSARI 2", "BULAN": "Juni 2026", "TANGGAL": "2026-06-27", "JAM": "20:21", "TIPE_UK": "UK Siclus", "BDC": 0, "NON_BDC": 100000, "TOTAL_UK": 100000, "KETERANGAN": "UK Siclus d.100 x 1 lbr"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "BULAN": "Juni 2026", "TANGGAL": "2026-06-25", "JAM": "13:20", "TIPE_UK": "UK TC", "BDC": 3350000, "NON_BDC": 0, "TOTAL_UK": 3350000, "KETERANGAN": "UK TC d.50 x 67 lbr"},
        {"WSID": "ZH9M", "LOKASI": "KRAKSAAN", "BULAN": "Juli 2026", "TANGGAL": "2026-07-12", "JAM": "15:10", "TIPE_UK": "UK BDC", "BDC": 200000, "NON_BDC": 0, "TOTAL_UK": 200000, "KETERANGAN": "UK BDC Dispen 200k"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"])
    return df

def load_default_ebos():
    data = [
        {"NO_LAPORAN": "EBOS-202606-001", "WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "BULAN": "Juni 2026", "TANGGAL": "2026-06-29", "TIPE_MESIN": "O-CRM", "NOMINAL_SELISIH": 600000, "STATUS_EBOS": "Resolved", "CATATAN_EBOS": "Selisih EBOS telah disesuaikan dengan UK 500k"},
        {"NO_LAPORAN": "EBOS-202606-002", "WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "BULAN": "Juni 2026", "TANGGAL": "2026-06-25", "TIPE_MESIN": "ITM", "NOMINAL_SELISIH": 3350000, "STATUS_EBOS": "In Review", "CATATAN_EBOS": "Menunggu kliring keluhan nasabah tgl 25/06"},
        {"NO_LAPORAN": "EBOS-202607-003", "WSID": "ZDA3", "LOKASI": "WINGS PROBOLINGGO", "BULAN": "Juli 2026", "TANGGAL": "2026-07-09", "TIPE_MESIN": "ITM", "NOMINAL_SELISIH": 25550000, "STATUS_EBOS": "Closed", "CATATAN_EBOS": "Koreksi administrasi -25,600k disetujui"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL"] = pd.to_datetime(df["TANGGAL"])
    return df

def load_default_ej():
    data = [
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "BULAN": "Juni 2026", "TANGGAL_EJ": "2026-06-29", "JAM_TX": "20:57", "NO_KARTU_REK": "5379-XXXX-1029", "NOMINAL_EJ": 100000, "STATUS_EJ": "Matched", "CATATAN_EJ": "Tx Jam 20:57 dispenser d.100 x 1 lbr match"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "BULAN": "Juni 2026", "TANGGAL_EJ": "2026-06-25", "JAM_TX": "13:20", "NO_KARTU_REK": "5221-XXXX-8812", "NOMINAL_EJ": 100000, "STATUS_EJ": "Discrepancy - Short", "CATATAN_EJ": "Uang terdispense sebagian, keluhan nasabah -100k"},
        {"WSID": "ZB3X", "LOKASI": "PT ANEKA TUNA INDONESIA", "BULAN": "Juli 2026", "TANGGAL_EJ": "2026-07-11", "JAM_TX": "12:14", "NO_KARTU_REK": "5412-XXXX-9001", "NOMINAL_EJ": 2500000, "STATUS_EJ": "Discrepancy - Short", "CATATAN_EJ": "Proses klaim keluhan nasabah tgl 11/07"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL_EJ"] = pd.to_datetime(df["TANGGAL_EJ"])
    return df

def load_default_sislok():
    data = [
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "BULAN": "Juli 2026", "TANGGAL_AUDIT": "2026-07-03", "STOK_SISLOK_AWAL": 500000, "KAS_MASUK": 317400, "KAS_KELUAR": 316800, "STOK_SISLOK_AKHIR": 500600, "FISIK_KAS_ACTUAL": 500500, "SELISIH_STOK": -100, "STATUS_REVIEW": "Variance Detected"},
        {"WSID": "ZM16", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "BULAN": "Juli 2026", "TANGGAL_AUDIT": "2026-07-07", "STOK_SISLOK_AWAL": 400000, "KAS_MASUK": 342500, "KAS_KELUAR": 339150, "STOK_SISLOK_AKHIR": 403350, "FISIK_KAS_ACTUAL": 403250, "SELISIH_STOK": -100, "STATUS_REVIEW": "Variance Detected"},
        {"WSID": "Z0X2", "LOKASI": "IDM SUDIMORO MALANG", "BULAN": "Juli 2026", "TANGGAL_AUDIT": "2026-07-10", "STOK_SISLOK_AWAL": 600000, "KAS_MASUK": 649850, "KAS_KELUAR": 649800, "STOK_SISLOK_AKHIR": 600050, "FISIK_KAS_ACTUAL": 600000, "SELISIH_STOK": -50, "STATUS_REVIEW": "Balanced"}
    ]
    df = pd.DataFrame(data)
    df["TANGGAL_AUDIT"] = pd.to_datetime(df["TANGGAL_AUDIT"])
    return df

def load_default_kolong():
    data = [
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "BULAN": "Juni 2026", "TANGGAL_TEMUAN": "2026-06-29", "DENOMINASI": "100,000", "LEMBAR": 1, "TOTAL_RUPIAH": 100000, "LOKASI_TEMUAN": "Kolong Dispenser", "KETERANGAN": "Ditemukan 1 lbr d.100k di kolong dispenser saat bongkar isi"},
        {"WSID": "Z5UM", "LOKASI": "PURWOSARI CRM 2", "BULAN": "Juni 2026", "TANGGAL_TEMUAN": "2026-06-29", "DENOMINASI": "50,000", "LEMBAR": 3, "TOTAL_RUPIAH": 150000, "LOKASI_TEMUAN": "Fascia Roll / Kolong Bawah", "KETERANGAN": "Ditemukan 3 lbr d.50k terselip di fascia roll"},
        {"WSID": "ZK82", "LOKASI": "IDM WARUNGDOWO PASURUAN", "BULAN": "Juli 2026", "TANGGAL_TEMUAN": "2026-07-15", "DENOMINASI": "100,000", "LEMBAR": 2, "TOTAL_RUPIAH": 200000, "LOKASI_TEMUAN": "Reject Box Chamber", "KETERANGAN": "Nyangkut di reject chamber 2 lbr d.100k"}
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
    "WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", 
    "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", 
    "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", 
    "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
])

# Ensure BULAN is auto-populated if missing or empty
def auto_fill_bulan(df, date_col="TGL_INS"):
    if "BULAN" not in df.columns:
        df["BULAN"] = "-"
    
    # Fill missing BULAN from date_col
    for idx, row in df.iterrows():
        if row["BULAN"] == "-" or pd.isna(row["BULAN"]):
            try:
                dt = pd.to_datetime(row[date_col])
                month_names = {1:"Januari", 2:"Februari", 3:"Maret", 4:"April", 5:"Mei", 6:"Juni", 7:"Juli", 8:"Agustus", 9:"September", 10:"Oktober", 11:"November", 12:"Desember"}
                df.at[idx, "BULAN"] = f"{month_names[dt.month]} {dt.year}"
            except:
                df.at[idx, "BULAN"] = "Juli 2026"
    return df

df_rekon = auto_fill_bulan(df_rekon, "TGL_INS")
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
st.sidebar.subheader("🎛️ Filter Global Terminal & Periode")

all_mesin = df_rekon["Mesin"].unique().tolist() if "Mesin" in df_rekon.columns else ["O-CRM", "ITM", "CRMHYO", "ACH"]
all_lok = df_rekon["LOK"].unique().tolist() if "LOK" in df_rekon.columns else ["BCA", "T"]
all_bulan = sorted(df_rekon["BULAN"].unique().tolist()) if "BULAN" in df_rekon.columns else ["Juni 2026", "Juli 2026"]

bulan_filter = st.sidebar.multiselect("📅 Filter Bulan Laporan:", options=all_bulan, default=all_bulan)
mesin_filter = st.sidebar.multiselect("📟 Tipe Mesin Terminal:", options=all_mesin, default=all_mesin)
lok_filter = st.sidebar.multiselect("🏢 Pengelola (LOK):", options=all_lok, default=all_lok)

filtered_df = df_rekon[
    (df_rekon["BULAN"].isin(bulan_filter)) &
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
            <h1>BCA ATM Reconciliation & Multi-Month Variance System</h1>
            <p>Sistem Rekonsiliasi Kas Operasional, Pemantauan Selisih Per Bulan, Audit UK BDC, Tes Cash, Cencon & CRUD Terpadu</p>
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
    st.subheader("📌 Ringkasan Eksekutif Rekonsiliasi Kas & Operasional Multi-Bulan")

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

    # Per-Month Variance Breakdown Chart
    st.markdown("### 📅 Perbandingan Selisih Kas Awal & Akhir Per Bulan (Monthly Variance)")
    if "BULAN" in filtered_df.columns and not filtered_df.empty:
        df_monthly_chart = filtered_df.groupby("BULAN")[["SEL_AWAL", "SEL_AKHIR", "CASH_POS", "SETOR"]].sum().reset_index()
        df_monthly_chart["SEL_AWAL_RP"] = df_monthly_chart["SEL_AWAL"] * 1000
        df_monthly_chart["SEL_AKHIR_RP"] = df_monthly_chart["SEL_AKHIR"] * 1000

        fig_month = px.bar(
            df_monthly_chart,
            x="BULAN",
            y=["SEL_AWAL_RP", "SEL_AKHIR_RP"],
            barmode="group",
            title="Tren Selisih Awal vs Selisih Akhir per Periode Bulan (Rupiah)",
            labels={"value": "Nominal Selisih (Rp)", "variable": "Jenis Selisih"},
            color_discrete_map={"SEL_AWAL_RP": "#E11D48", "SEL_AKHIR_RP": "#059669"},
            template="plotly_white"
        )
        fig_month.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=380)
        st.plotly_chart(fig_month, use_container_width=True)

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

# ---------------------------------------------------------
# MODUL 2: TABEL UTAMA COMPLETE AUDIT (PER BULAN)
# ---------------------------------------------------------
elif menu == "📋 Tabel Utama (Complete Audit)":
    st.subheader("📋 Rekonsiliasi Utama Lengkap dengan Pembeda Selisih Per Bulan")

    # Monthly Summary Cards Banner on Top of Main Table
    st.markdown("### 📅 Ringkasan Selisih Kas Per Bulan")
    if "BULAN" in filtered_df.columns and not filtered_df.empty:
        bulan_list = sorted(filtered_df["BULAN"].unique().tolist())
        cols_m = st.columns(max(len(bulan_list), 1))
        
        for idx, b_name in enumerate(bulan_list):
            b_df = filtered_df[filtered_df["BULAN"] == b_name]
            b_sel_awal = b_df["SEL_AWAL"].sum() * 1000
            b_sel_akhir = b_df["SEL_AKHIR"].sum() * 1000
            b_count = len(b_df)
            
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

    col_srch, col_m_select = st.columns([2, 1])
    with col_srch:
        search_kw = st.text_input("🔍 Cari WSID, Lokasi, Bulan, Status UK BDC, Tes Cash, atau Staff:", "")
    with col_m_select:
        selected_month_filter = st.selectbox("📅 Filter Khusus Bulan Tabel:", ["Semua Bulan"] + all_bulan)

    disp_df = filtered_df.copy()
    
    if selected_month_filter != "Semua Bulan":
        disp_df = disp_df[disp_df["BULAN"] == selected_month_filter]

    if search_kw:
        mask = (
            disp_df["WSID"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["LOKASI"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["BULAN"].astype(str).str.contains(search_kw, case=False, na=False) |
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

    # Display Columns on Main Table including BULAN
    cols_to_show = [
        "WSID", "BULAN", "LOK", "LOKASI", "Mesin", "TGL_INS", "TGL_REM", 
        "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR",
        "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", "REKON_SISLOK", "REVIEW_STOCK",
        "STAFF_1", "STAFF_2", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"
    ]
    cols_exist = [c for c in cols_to_show if c in formatted_df.columns]
    
    display_styled_df(formatted_df[cols_exist], ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"])

    st.markdown("---")
    st.markdown("### 👷 Rincian Tab Audit & Personel Staff per WSID Terminal")
    if not disp_df.empty:
        selected_wsid = st.selectbox("Pilih WSID Terminal untuk melihat Rincian Lengkap Audit:", disp_df["WSID"].unique())
        wsid_row = disp_df[disp_df["WSID"] == selected_wsid].iloc[0]
        
        tab_dt1, tab_dt2, tab_dt3, tab_dt4 = st.tabs(["💳 UK BDC & Tes Cash", "📦 Sislok & Review Stock", "👥 Petugas Staff & Driver", "📸 Foto Bukti Fisik"])
        
        with tab_dt1:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.write(f"**Periode Bulan:** 🗓️ {wsid_row.get('BULAN', '-')}")
                st.write(f"**WSID / Terminal:** {wsid_row['WSID']} ({wsid_row['Mesin']})")
                st.write(f"**Lokasi:** {wsid_row['LOKASI']}")
            with c2:
                st.write(f"**Uang Kembali / UK BDC:** {wsid_row.get('UK_BDC', '-')}")
                st.write(f"**Tes Cash Operasional:** {wsid_row.get('TEST_CASH', '-')}")
            with c3:
                st.write(f"**Status Cencon:** {wsid_row.get('CLOSE_OPEN_CENCON', '-')}")
                st.write(f"**Selisih Awal:** Rp {wsid_row.get('SEL_AWAL', 0)*1000:,.0f}")
                st.write(f"**Selisih Akhir:** Rp {wsid_row.get('SEL_AKHIR', 0)*1000:,.0f}")
                
        with tab_dt2:
            st.write(f"**Status Rekon Sislok:** {wsid_row.get('REKON_SISLOK', '-')}")
            st.write(f"**Rincian Review Stock Kas:** {wsid_row.get('REVIEW_STOCK', '-')}")
            st.write(f"**Catatan Lapangan:** {wsid_row.get('CATATAN_PROSES', '-')}")

        with tab_dt3:
            c_st1, c_st2 = st.columns(2)
            with c_st1:
                st.write(f"**Petugas 1:** 👤 {wsid_row.get('STAFF_1', '-')}")
                st.write(f"**Petugas 2:** 👤 {wsid_row.get('STAFF_2', '-')}")
                st.write(f"**Petugas 3:** 👤 {wsid_row.get('STAFF_3', '-')}")
            with c_st2:
                st.write(f"**Driver Pengawal:** 🚚 {wsid_row.get('DRIVER', '-')}")
                st.write(f"**Aktivitas Jam:** ⏱️ {wsid_row.get('ACTIVITY', '-')}")

        with tab_dt4:
            if selected_wsid in st.session_state.image_store:
                st.image(st.session_state.image_store[selected_wsid], caption=f"Bukti Fisik Rekonsiliasi WSID {selected_wsid}", width=450)
            else:
                st.info(f"💡 Belum ada foto bukti khusus yang diunggah untuk WSID {selected_wsid}.")

# ---------------------------------------------------------
# MODUL 3: CLOSE / OPEN CENCON & TES CASH
# ---------------------------------------------------------
elif menu == "💵 Close / Open Cencon & Tes Cash":
    st.subheader("💵 Pengawasan Close / Open Cencon & Tes Cash Operasional")
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
    st.subheader("📑 Monitoring & Registrasi Laporan EBOS BCA")
    df_eb = st.session_state.df_ebos.copy()
    if "TANGGAL" in df_eb.columns and pd.api.types.is_datetime64_any_dtype(df_eb["TANGGAL"]):
        df_eb["TANGGAL"] = df_eb["TANGGAL"].dt.strftime("%Y-%m-%d")
    display_styled_df(df_eb, ["NOMINAL_SELISIH"])

# ---------------------------------------------------------
# MODUL 6: REKON EJ (ELECTRONIC JOURNAL)
# ---------------------------------------------------------
elif menu == "💻 Rekon EJ (Electronic Journal)":
    st.subheader("💻 Rekonsiliasi Electronic Journal (EJ Audit Log)")
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
            image_bytes = uploaded_img.read()
            st.session_state.image_store[target_wsid] = image_bytes
            st.success(f"Foto bukti untuk WSID {target_wsid} berhasil diunggah!")

    with col_up2:
        st.markdown("### 🖼️ Preview Foto Bukti Tersimpan")
        view_wsid = st.selectbox("Pilih WSID untuk Pratinjau:", df_rekon["WSID"].unique(), key="preview_wsid")
        
        if view_wsid in st.session_state.image_store:
            st.image(st.session_state.image_store[view_wsid], caption=f"Bukti Fisik WSID {view_wsid}", use_container_width=True)
        else:
            st.info(f"Belum ada foto bukti yang diunggah untuk WSID {view_wsid}.")

# ---------------------------------------------------------
# MODUL 10: KELOLA DATA (CRUD OPERATIONS FULL)
# ---------------------------------------------------------
elif menu == "🛠️ Kelola Data (CRUD Operations)":
    st.subheader("🛠️ Manajemen Data Terpadu (Create, Read, Update, Delete)")
    
    table_crud = st.selectbox(
        "Pilih Tabel Operasional yang Ingin Dikelola:",
        ["Tabel Utama Rekonsiliasi", "Close/Open Cencon", "Uang Kembali (UK)", "Laporan EBOS", "Rekon EJ", "Sislok Stock Review", "Temuan Uang Kolong"]
    )
    
    st.markdown("---")
    
    if table_crud == "Tabel Utama Rekonsiliasi":
        curr_df = st.session_state.df_rekon
        st.markdown("### 📋 Data Rekonsiliasi Utama (Read & Update Direct)")
        
        crud_action = st.radio("Pilih Operasi CRUD:", ["👁️ Read & Live Edit", "➕ Create (Tambah Data)", "✏️ Update Record Specific", "🗑️ Delete Record"], horizontal=True)
        
        if crud_action == "👁️ Read & Live Edit":
            st.info("💡 Anda dapat mengedit isi sel langsung pada tabel di bawah, lalu klik 'Simpan Perubahan Tabel'.")
            edited_df = st.data_editor(curr_df, num_rows="dynamic", use_container_width=True)
            if st.button("💾 Simpan Perubahan Tabel Utama"):
                st.session_state.df_rekon = edited_df
                st.success("Tabel Rekonsiliasi Utama berhasil diperbarui!")
                safe_rerun()
                
        elif crud_action == "➕ Create (Tambah Data)":
            with st.form("crud_create_rekon"):
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    c_wsid = st.text_input("WSID Terminal", "Z99A")
                    c_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
                    c_lokasi = st.text_input("Nama Lokasi", "KCP MALANG KOTA")
                with c2:
                    c_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
                    c_bulan = st.selectbox("Periode Bulan", ["Juni 2026", "Juli 2026", "Agustus 2026", "September 2026"])
                    c_tgl_ins = st.date_input("Tanggal Pengisian (TGL_INS)")
                    c_tgl_rem = st.date_input("Tanggal Penarikan (TGL_REM)")
                with c3:
                    c_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=500000)
                    c_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=499500)
                    c_sel_awal = c_setor - c_cash_pos
                    st.info(f"Estimasi Selisih Awal: **{c_sel_awal:,.0f} (Ribu Rp)**")
                with c4:
                    c_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100)
                    c_uk_bdc = st.text_input("Status / Nominal UK BDC", "Rp 500,000 (UK Siclus)")
                    c_test_cash = st.text_input("Status Tes Cash", "Rp 100,000 (NON-BDC)")
                
                c5, c6 = st.columns(2)
                with c5:
                    c_cencon = st.selectbox("Status Cencon", ["Close", "Open", "Pending"])
                    c_sislok = st.text_input("Status Rekon Sislok", "Variance (-100)")
                    c_review_stock = st.text_input("Review Stock", "Sislok: 500,600 | Fisik: 500,500")
                with c6:
                    c_staff1 = st.text_input("Petugas 1", "BAYU OKTA PURWANTO")
                    c_driver = st.text_input("Driver Pengawal", "ASSYAVI ALIYULLOH M")
                    c_tanggapan = st.text_area("Tanggapan BCA", "Selisih Awal : -500\\nSelisih Akhir : -100")
                
                if st.form_submit_button("💾 [CREATE] Simpan Data Baru"):
                    new_r = {
                        "WSID": c_wsid, "LOK": c_lok, "LOKASI": c_lokasi, "Mesin": c_mesin,
                        "BULAN": c_bulan,
                        "TGL_INS": pd.to_datetime(c_tgl_ins), "TGL_REM": pd.to_datetime(c_tgl_rem),
                        "CASH_POS": c_cash_pos, "SETOR": c_setor, "SEL_AWAL": c_sel_awal, "SEL_AKHIR": c_sel_akhir,
                        "UK_BDC": c_uk_bdc, "TEST_CASH": c_test_cash, "CLOSE_OPEN_CENCON": c_cencon,
                        "REKON_SISLOK": c_sislok, "REVIEW_STOCK": c_review_stock,
                        "STAFF_1": c_staff1, "STAFF_2": "-", "STAFF_3": "-", "DRIVER": c_driver,
                        "ACTIVITY": f"{datetime.now().strftime('%d/%m/%y %H:%M')} - INPUT BARU",
                        "CATATAN_PROSES": "Data ditambahkan via CRUD", "TANGGAPAN_BCA": c_tanggapan
                    }
                    st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_r])], ignore_index=True)
                    st.success(f"Data WSID {c_wsid} berhasil ditambahkan!")
                    safe_rerun()
                    
        elif crud_action == "✏️ Update Record Specific":
            selected_idx = st.number_input("Pilih Index Baris yang Ingin Di-Update (0 s/d N):", min_value=0, max_value=max(len(curr_df)-1, 0), value=0)
            if not curr_df.empty:
                row_val = curr_df.iloc[selected_idx]
                st.write(f"**Mengubah Data Index {selected_idx} - WSID {row_val['WSID']} ({row_val['LOKASI']})**")
                
                with st.form("crud_update_rekon"):
                    u1, u2, u3 = st.columns(3)
                    with u1:
                        u_wsid = st.text_input("WSID", row_val["WSID"])
                        u_lokasi = st.text_input("Lokasi", row_val["LOKASI"])
                        u_bulan = st.selectbox("Periode Bulan", ["Juni 2026", "Juli 2026", "Agustus 2026", "September 2026"], index=0 if row_val.get("BULAN")=="Juni 2026" else 1)
                    with u2:
                        u_cash_pos = st.number_input("Cash Position (Ribu Rp)", value=int(row_val["CASH_POS"]))
                        u_setor = st.number_input("Setor (Ribu Rp)", value=int(row_val["SETOR"]))
                        u_sel_akhir = st.number_input("Selisih Akhir (Ribu Rp)", value=int(row_val["SEL_AKHIR"]))
                    with u3:
                        u_uk_bdc = st.text_input("Status UK BDC", str(row_val.get("UK_BDC", "-")))
                        u_test_cash = st.text_input("Tes Cash", str(row_val.get("TEST_CASH", "-")))
                        u_cencon = st.selectbox("Status Cencon", ["Close", "Open", "Pending"], index=0 if row_val.get("CLOSE_OPEN_CENCON")=="Close" else 1)
                    
                    if st.form_submit_button("✏️ [UPDATE] Simpan Perubahan"):
                        st.session_state.df_rekon.at[selected_idx, "WSID"] = u_wsid
                        st.session_state.df_rekon.at[selected_idx, "LOKASI"] = u_lokasi
                        st.session_state.df_rekon.at[selected_idx, "BULAN"] = u_bulan
                        st.session_state.df_rekon.at[selected_idx, "CASH_POS"] = u_cash_pos
                        st.session_state.df_rekon.at[selected_idx, "SETOR"] = u_setor
                        st.session_state.df_rekon.at[selected_idx, "SEL_AWAL"] = u_setor - u_cash_pos
                        st.session_state.df_rekon.at[selected_idx, "SEL_AKHIR"] = u_sel_akhir
                        st.session_state.df_rekon.at[selected_idx, "UK_BDC"] = u_uk_bdc
                        st.session_state.df_rekon.at[selected_idx, "TEST_CASH"] = u_test_cash
                        st.session_state.df_rekon.at[selected_idx, "CLOSE_OPEN_CENCON"] = u_cencon
                        st.success(f"Record index {selected_idx} berhasil diperbarui!")
                        safe_rerun()
                        
        elif crud_action == "🗑️ Delete Record":
            del_idx = st.number_input("Pilih Index Baris yang Ingin Dihapus:", min_value=0, max_value=max(len(curr_df)-1, 0), value=0)
            if not curr_df.empty:
                del_row = curr_df.iloc[del_idx]
                st.warning(f"⚠️ Apakah Anda yakin ingin menghapus data **WSID {del_row['WSID']} - {del_row['LOKASI']}** pada Index {del_idx}?")
                if st.button("🗑️ [DELETE] Konfirmasi Hapus Record Ini"):
                    st.session_state.df_rekon = st.session_state.df_rekon.drop(del_idx).reset_index(drop=True)
                    st.success("Record berhasil dihapus!")
                    safe_rerun()

    else:
        st.info(f"💡 Pengelolaan data untuk **{table_crud}** tersedia secara interaktif.")
        if table_crud == "Close/Open Cencon":
            st.session_state.df_cencon = st.data_editor(st.session_state.df_cencon, num_rows="dynamic", use_container_width=True)
        elif table_crud == "Uang Kembali (UK)":
            st.session_state.df_uk = st.data_editor(st.session_state.df_uk, num_rows="dynamic", use_container_width=True)
        elif table_crud == "Laporan EBOS":
            st.session_state.df_ebos = st.data_editor(st.session_state.df_ebos, num_rows="dynamic", use_container_width=True)
        elif table_crud == "Rekon EJ":
            st.session_state.df_ej = st.data_editor(st.session_state.df_ej, num_rows="dynamic", use_container_width=True)
        elif table_crud == "Sislok Stock Review":
            st.session_state.df_sislok = st.data_editor(st.session_state.df_sislok, num_rows="dynamic", use_container_width=True)
        elif table_crud == "Temuan Uang Kolong":
            st.session_state.df_kolong = st.data_editor(st.session_state.df_kolong, num_rows="dynamic", use_container_width=True)

# ---------------------------------------------------------
# MODUL 11: INPUT & TAMBAH DATA TERPADU
# ---------------------------------------------------------
elif menu == "➕ Input & Tambah Data Terpadu":
    st.subheader("📝 Input & Tambah Data Operasional Terpadu (Dengan Lampiran Gambar)")
    
    tab_f1, tab_f2, tab_f3, tab_f4, tab_f5, tab_f6, tab_f7 = st.tabs([
        "📋 Staff & Rekon Utama", "💵 Cencon & Tes Cash", "🔄 Uang Kembali (UK)", 
        "📑 Laporan EBOS", "💻 Rekon EJ Log", "📦 Sislok Stock Review", "🪙 Uang Kolong"
    ])
    
    with tab_f1:
        st.markdown("### 📋 Input Data Rekonsiliasi Utama & Staff")
        with st.form("form_terpadu_main"):
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            with col_f1:
                new_wsid = st.text_input("WSID Terminal", "Z88M")
                new_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
                new_lokasi = st.text_input("Lokasi Terminal", "PURWOSARI CRM 3")
            with col_f2:
                new_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
                new_bulan = st.selectbox("Periode Bulan", ["Juni 2026", "Juli 2026", "Agustus 2026", "September 2026"])
                new_tgl_ins = st.date_input("Tanggal Pengisian (TGL_INS)")
                new_tgl_rem = st.date_input("Tanggal Penarikan (TGL_REM)")
            with col_f3:
                new_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=400000)
                new_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=399500)
                new_sel_awal = new_setor - new_cash_pos
                st.info(f"Estimasi Selisih Awal: **{new_sel_awal:,.0f} (Ribu Rp)**")
            with col_f4:
                new_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100)
                new_uk_bdc = st.text_input("Status / Nominal UK BDC", "Rp 500,000 (UK Siclus)")
                new_test_cash = st.text_input("Status Tes Cash", "Rp 100,000 (NON-BDC)")

            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                new_cencon = st.selectbox("Status Cencon", ["Close", "Open", "Pending"])
                new_staff1 = st.text_input("Petugas 1", "BAYU OKTA PURWANTO")
            with col_s2:
                new_sislok = st.text_input("Status Rekon Sislok", "Variance (-100)")
                new_staff2 = st.text_input("Petugas 2", "AKHMAD RIZA MAULANA")
            with col_s3:
                new_review_stock = st.text_input("Review Stock", "Sislok: 400,000 | Fisik: 399,900")
                new_staff3 = st.text_input("Petugas 3", "YOYOK BUDI RAKHMAN")
            with col_s4:
                new_driver = st.text_input("Driver Pengawal", "ASSYAVI ALIYULLOH M (DRIVER)")
                new_activity = st.text_input("Aktivitas & Jam", f"{datetime.now().strftime('%d/%m/%y %H:%M')} - BONGKAR ISI")

            new_catatan = st.text_input("Catatan Lapangan", "Proses normal, UK d.100 x 1 lbr")
            new_tanggapan = st.text_area("Tanggapan BCA / Audit Log", f"Selisih Awal : {new_sel_awal}\\nUK : {abs(new_sel_awal - new_sel_akhir)}\\nSelisih Akhir : {new_sel_akhir}")

            if st.form_submit_button("💾 Simpan Rekonsiliasi Utama"):
                new_row = {
                    "WSID": new_wsid, "LOK": new_lok, "LOKASI": new_lokasi, "Mesin": new_mesin,
                    "BULAN": new_bulan,
                    "TGL_INS": pd.to_datetime(new_tgl_ins), "TGL_REM": pd.to_datetime(new_tgl_rem),
                    "CASH_POS": new_cash_pos, "SETOR": new_setor, "SEL_AWAL": new_sel_awal, "SEL_AKHIR": new_sel_akhir,
                    "UK_BDC": new_uk_bdc, "TEST_CASH": new_test_cash, "CLOSE_OPEN_CENCON": new_cencon,
                    "REKON_SISLOK": new_sislok, "REVIEW_STOCK": new_review_stock,
                    "STAFF_1": new_staff1, "STAFF_2": new_staff2, "STAFF_3": new_staff3,
                    "DRIVER": new_driver, "ACTIVITY": new_activity, "CATATAN_PROSES": new_catatan,
                    "TANGGAPAN_BCA": new_tanggapan
                }
                st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_row])], ignore_index=True)
                st.success(f"Data WSID {new_wsid} berhasil ditambahkan!")
                safe_rerun()

    with tab_f2:
        st.markdown("### 💵 Form Input Close / Open Cencon & Tes Cash")
        with st.form("form_cencon_terpadu"):
            c1, c2 = st.columns(2)
            with c1:
                c_wsid = st.text_input("WSID Terminal", "Z5UM")
                c_lokasi = st.text_input("Nama Lokasi", "CRM PURWOSARI 2")
                c_bulan = st.selectbox("Bulan Transaksi", ["Juni 2026", "Juli 2026", "Agustus 2026"])
                c_tgl = st.date_input("Tanggal Transaksi")
            with c2:
                c_jam = st.text_input("Jam Transaksi", "20:22")
                c_bdc = st.number_input("Nominal BDC (Rp)", value=0, step=10000)
                c_non_bdc = st.number_input("Nominal NON-BDC (Rp)", value=100000, step=10000)
                c_status = st.selectbox("Status Cencon", ["Close", "Open", "Pending"])
            c_ket = st.text_input("Keterangan Tes Cash", "Tes cash sesuai 100,000")
            
            if st.form_submit_button("💾 Simpan Record Cencon"):
                new_c = {"WSID": c_wsid, "LOKASI": c_lokasi, "BULAN": c_bulan, "TANGGAL": pd.to_datetime(c_tgl), "JAM": c_jam, "BDC": c_bdc, "NON_BDC": c_non_bdc, "STATUS": c_status, "KETERANGAN": c_ket}
                st.session_state.df_cencon = pd.concat([st.session_state.df_cencon, pd.DataFrame([new_c])], ignore_index=True)
                st.success("Data Cencon berhasil ditambahkan!")
                safe_rerun()

    with tab_f3:
        st.markdown("### 🔄 Form Input Uang Kembali (UK)")
        with st.form("form_uk_terpadu"):
            u1, u2 = st.columns(2)
            with u1:
                uk_wsid = st.text_input("WSID Terminal", "ZM16")
                uk_lokasi = st.text_input("Nama Lokasi", "ALFAMD INDRAGIRI PASURUAN")
                uk_bulan = st.selectbox("Bulan Klaim", ["Juni 2026", "Juli 2026", "Agustus 2026"])
                uk_tipe = st.selectbox("Tipe UK", ["UK Siclus", "UK TC", "UK BDC"])
            with u2:
                uk_tgl = st.date_input("Tanggal Klaim")
                uk_jam = st.text_input("Jam Transaksi", "13:20")
                uk_bdc = st.number_input("Nominal UK BDC (Rp)", value=0, step=50000)
                uk_non_bdc = st.number_input("Nominal UK Non-BDC (Rp)", value=100000, step=50000)
            uk_ket = st.text_input("Keterangan Rincian UK", "UK d.50 x 2 lbr")
            
            if st.form_submit_button("💾 Simpan Record UK"):
                tot_uk = uk_bdc + uk_non_bdc
                new_u = {"WSID": uk_wsid, "LOKASI": uk_lokasi, "BULAN": uk_bulan, "TANGGAL": pd.to_datetime(uk_tgl), "JAM": uk_jam, "TIPE_UK": uk_tipe, "BDC": uk_bdc, "NON_BDC": uk_non_bdc, "TOTAL_UK": tot_uk, "KETERANGAN": uk_ket}
                st.session_state.df_uk = pd.concat([st.session_state.df_uk, pd.DataFrame([new_u])], ignore_index=True)
                st.success("Record UK berhasil ditambahkan!")
                safe_rerun()

    with tab_f4:
        st.markdown("### 📑 Form Input Laporan EBOS")
        with st.form("form_ebos_terpadu"):
            e1, e2 = st.columns(2)
            with e1:
                e_no = st.text_input("No Tiket EBOS", f"EBOS-202607-00{len(st.session_state.df_ebos)+1}")
                e_wsid = st.text_input("WSID Terminal", "ZDA3")
                e_lokasi = st.text_input("Lokasi Terminal", "WINGS PROBOLINGGO")
            with e2:
                e_bulan = st.selectbox("Bulan Laporan", ["Juni 2026", "Juli 2026", "Agustus 2026"])
                e_tgl = st.date_input("Tanggal Laporan")
                e_nom = st.number_input("Nominal Selisih EBOS (Rp)", value=500000, step=50000)
                e_status = st.selectbox("Status Tiket", ["Open", "In Review", "Resolved", "Closed"])
            e_catatan = st.text_area("Catatan Laporan EBOS", "Selisih ebos dalam verifikasi dokumen")
            
            if st.form_submit_button("💾 Registrasi Tiket EBOS"):
                new_e = {"NO_LAPORAN": e_no, "WSID": e_wsid, "LOKASI": e_lokasi, "BULAN": e_bulan, "TANGGAL": pd.to_datetime(e_tgl), "TIPE_MESIN": "ITM", "NOMINAL_SELISIH": e_nom, "STATUS_EBOS": e_status, "CATATAN_EBOS": e_catatan}
                st.session_state.df_ebos = pd.concat([st.session_state.df_ebos, pd.DataFrame([new_e])], ignore_index=True)
                st.success("Tiket EBOS berhasil dicatat!")
                safe_rerun()

    with tab_f5:
        st.markdown("### 💻 Form Input Rekon EJ Log")
        with st.form("form_ej_terpadu"):
            j1, j2 = st.columns(2)
            with j1:
                j_wsid = st.text_input("WSID Terminal", "Z5UM")
                j_lokasi = st.text_input("Nama Lokasi", "PURWOSARI CRM 2")
                j_bulan = st.selectbox("Bulan EJ Log", ["Juni 2026", "Juli 2026", "Agustus 2026"])
            with j2:
                j_tgl = st.date_input("Tanggal Log EJ")
                j_jam = st.text_input("Jam Transaksi", "20:57")
                j_kartu = st.text_input("No Kartu / Rekening", "5379-XXXX-1029")
                j_nom = st.number_input("Nominal Transaksi EJ (Rp)", value=100000, step=50000)
                j_status = st.selectbox("Status Matching EJ", ["Matched", "Discrepancy - Short", "Discrepancy - Over"])
            j_catatan = st.text_area("Catatan Temuan EJ", "Tx Jam 20:57 dispenser d.100 x 1 lbr match")
            
            if st.form_submit_button("💾 Simpan Log EJ"):
                new_j = {"WSID": j_wsid, "LOKASI": j_lokasi, "BULAN": j_bulan, "TANGGAL_EJ": pd.to_datetime(j_tgl), "JAM_TX": j_jam, "NO_KARTU_REK": j_kartu, "NOMINAL_EJ": j_nom, "STATUS_EJ": j_status, "CATATAN_EJ": j_catatan}
                st.session_state.df_ej = pd.concat([st.session_state.df_ej, pd.DataFrame([new_j])], ignore_index=True)
                st.success("Record EJ berhasil disimpan!")
                safe_rerun()

    with tab_f6:
        st.markdown("### 📦 Form Input Sislok Stock Review")
        with st.form("form_sislok_terpadu"):
            s1, s2 = st.columns(2)
            with s1:
                s_wsid = st.text_input("WSID Terminal", "Z0X2")
                s_lokasi = st.text_input("Lokasi Terminal", "IDM SUDIMORO MALANG")
                s_bulan = st.selectbox("Bulan Audit Stock", ["Juni 2026", "Juli 2026", "Agustus 2026"])
                s_tgl = st.date_input("Tanggal Audit Stock")
            with s2:
                s_awal = st.number_input("Stok Sislok Awal (Ribu Rp)", value=600000, step=10000)
                s_masuk = st.number_input("Total Kas Masuk (Ribu Rp)", value=649850, step=10000)
                s_keluar = st.number_input("Total Kas Keluar (Ribu Rp)", value=649800, step=10000)
                s_sislok_akhir = s_awal + s_masuk - s_keluar
                s_fisik = st.number_input("Fisik Kas Actual (Ribu Rp)", value=600000, step=10000)
                s_selisih = s_fisik - s_sislok_akhir
            
            if st.form_submit_button("💾 Simpan Audit Sislok Stock"):
                new_s = {"WSID": s_wsid, "LOKASI": s_lokasi, "BULAN": s_bulan, "TANGGAL_AUDIT": pd.to_datetime(s_tgl), "STOK_SISLOK_AWAL": s_awal, "KAS_MASUK": s_masuk, "KAS_KELUAR": s_keluar, "STOK_SISLOK_AKHIR": s_sislok_akhir, "FISIK_KAS_ACTUAL": s_fisik, "SELISIH_STOK": s_selisih, "STATUS_REVIEW": "Balanced" if s_selisih==0 else "Variance Detected"}
                st.session_state.df_sislok = pd.concat([st.session_state.df_sislok, pd.DataFrame([new_s])], ignore_index=True)
                st.success("Audit Sislok berhasil disimpan!")
                safe_rerun()

    with tab_f7:
        st.markdown("### 🪙 Form Input Uang Kolong")
        with st.form("form_kolong_terpadu"):
            k1, k2 = st.columns(2)
            with k1:
                k_wsid = st.text_input("WSID Terminal", "Z5UM")
                k_lokasi = st.text_input("Nama Lokasi", "PURWOSARI CRM 2")
                k_bulan = st.selectbox("Bulan Temuan", ["Juni 2026", "Juli 2026", "Agustus 2026"])
                k_tgl = st.date_input("Tanggal Temuan")
            with k2:
                k_denom = st.selectbox("Denominasi Uang", ["100,000", "50,000", "20,000"])
                k_lembar = st.number_input("Jumlah Lembar", value=1, min_value=1)
                val_denom = 100000 if k_denom == "100,000" else (50000 if k_denom == "50,000" else 20000)
                k_total = val_denom * k_lembar
                k_posisi = st.selectbox("Lokasi Temuan Fisik", ["Kolong Dispenser", "Fascia Roll / Bawah", "Reject Box Chamber", "Transport Mechanism"])
            k_ket = st.text_area("Keterangan Fisik", "Ditemukan terselip saat bongkar isi kas")
            
            if st.form_submit_button("💾 Simpan Temuan Uang Kolong"):
                new_k = {"WSID": k_wsid, "LOKASI": k_lokasi, "BULAN": k_bulan, "TANGGAL_TEMUAN": pd.to_datetime(k_tgl), "DENOMINASI": k_denom, "LEMBAR": k_lembar, "TOTAL_RUPIAH": k_total, "LOKASI_TEMUAN": k_posisi, "KETERANGAN": k_ket}
                st.session_state.df_kolong = pd.concat([st.session_state.df_kolong, pd.DataFrame([new_k])], ignore_index=True)
                st.success("Temuan Uang Kolong berhasil dicatat!")
                safe_rerun()

# ---------------------------------------------------------
# MODUL 12: EKSPOR & IMPOR DATA EXCEL
# ---------------------------------------------------------
elif menu == "📁 Ekspor & Impor Data Excel":
    st.subheader("📥 Unduh Seluruh Workbook Laporan Rekonsiliasi Multi-Bulan (.xlsx)")
    
    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("### 📄 Unduh File Excel Multi-Sheet Complete")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            st.session_state.df_rekon.to_excel(writer, sheet_name='Rekon_Utama_MultiBulan', index=False)
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
