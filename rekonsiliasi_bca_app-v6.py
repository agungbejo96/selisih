import os

v6_code = '''import streamlit as st

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
    page_title="Sistem Rekonsiliasi Kas BCA + Staff & Audit Operational",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Executive BCA Branding & Responsive Layout
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
            "STAFF_1": "BAYU OKTA PURWANTO", "STAFF_2": "AKHMAD RIZA MAULANA",
            "STAFF_3": "MUHAMMAD RIZAL MUZAKHI", "DRIVER": "ASSYAVI ALIYULLOH M",
            "ACTIVITY": "29/06/26 19:51 - BONGKAR ISI",
            "CATATAN_PROSES": "Proses normal, UK d.100 x 1 lbr",
            "TANGGAPAN_BCA": "Selisih Awal : -600\\nUK : 500\\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZM16", "LOK": "T", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "Mesin": "ITM",
            "TGL_INS": "2026-06-25", "TGL_REM": "2026-07-07", "CASH_POS": 342500, "SETOR": 339150,
            "SEL_AWAL": -3350, "SEL_AKHIR": -100,
            "STAFF_1": "YOYOK BUDI RAKHMAN", "STAFF_2": "ADAM REYHAN HERLAMBANG",
            "STAFF_3": "EEND MUHAIRIZ ATHA", "DRIVER": "SGI VENDOR",
            "ACTIVITY": "25/06/26 21:34 - PENGISIAN KAS",
            "CATATAN_PROSES": "UK d.50 x 67 lbr, Keluhan nasabah teridentifikasi",
            "TANGGAPAN_BCA": "Selisih Awal : -3,350\\nUK : 3,350\\nKeluhan Nsb : -100 tgl 25/06 jam 13:20\\nSelisih Akhir : -100"
        },
        {
            "WSID": "Z0X2", "LOK": "T", "LOKASI": "IDM SUDIMORO MALANG", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-04", "TGL_REM": "2026-07-10", "CASH_POS": 649850, "SETOR": 649800,
            "SEL_AWAL": -50, "SEL_AKHIR": -50,
            "STAFF_1": "BAMBANG HERMANTO", "STAFF_2": "DEDI KURNIAWAN",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER 02",
            "ACTIVITY": "04/07/26 18:30 - BONGKAR ISI",
            "CATATAN_PROSES": "Sesuai selisih fisik -50",
            "TANGGAPAN_BCA": "Selisih Awal : -50\\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZDA3", "LOK": "T", "LOKASI": "WINGS PROBOLINGGO", "Mesin": "ITM",
            "TGL_INS": "2026-07-09", "TGL_REM": "2026-07-11", "CASH_POS": 576950, "SETOR": 602500,
            "SEL_AWAL": 25550, "SEL_AKHIR": -50,
            "STAFF_1": "RIZKY PRATAMA", "STAFF_2": "FAJAR SHODIQ",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER 05",
            "ACTIVITY": "09/07/26 10:15 - KOREKSI ADM",
            "CATATAN_PROSES": "Koreksi Administrasi -25,600",
            "TANGGAPAN_BCA": "Selisih Awal : 25,550\\nKoreksi Adm : -25,600\\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZB3X", "LOK": "T", "LOKASI": "PT ANEKA TUNA INDONESIA", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-09", "TGL_REM": "2026-07-12", "CASH_POS": 359200, "SETOR": 372100,
            "SEL_AWAL": 12900, "SEL_AKHIR": -100,
            "STAFF_1": "AGUS SETIAWAN", "STAFF_2": "HENDRA WIJAYA",
            "STAFF_3": "-", "DRIVER": "DRIVER VENDOR",
            "ACTIVITY": "09/07/26 14:20 - AUDIT CASH",
            "CATATAN_PROSES": "Multiple claim keluhan nasabah tgl 11/07",
            "TANGGAPAN_BCA": "Selisih Awal : 12,900\\nKeluhan Nsb : -2,500 tgl 11/07 jam 12:14\\n-2,500 tgl 11/07 jam 12:13\\n-2,500 tgl 11/07 jam 12:11\\n-500 tgl 11/07 jam 10:33\\n-2,500 tgl 11/07 jam 09:17\\n-2,500 tgl 11/07 jam 15:02\\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZK82", "LOK": "T", "LOKASI": "IDM WARUNGDOWO PASURUAN", "Mesin": "O-CRM",
            "TGL_INS": "2026-07-15", "TGL_REM": "2026-07-18", "CASH_POS": 360750, "SETOR": 356500,
            "SEL_AWAL": -4250, "SEL_AKHIR": -50,
            "STAFF_1": "EKO PURWANTO", "STAFF_2": "ARIS MUNANDAR",
            "STAFF_3": "-", "DRIVER": "SGI DRIVER 01",
            "ACTIVITY": "15/07/26 19:25 - REKONSILIASI",
            "CATATAN_PROSES": "UK : 5,400 & Keluhan Nsb : -1,200",
            "TANGGAPAN_BCA": "Selisih Awal : -4,250\\nKeluhan Nsb : -1,200 tgl 15/07 jam 19:25\\nUK : 5,400\\nSelisih Akhir : -50"
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
            # Look for case-insensitive match
            matches = [c for c in df.columns if c.strip().lower() == col.strip().lower()]
            if matches:
                df.rename(columns={matches[0]: col}, inplace=True)
            else:
                df[col] = "-"
    return df

df_rekon = sanitize_df(st.session_state.df_rekon, ["WSID", "LOK", "LOKASI", "Mesin", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"])

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Bank_Central_Asia_logo.svg", width=180)
st.sidebar.title("Navigasi Operasional BCA")

menu = st.sidebar.radio(
    "Pilih Modul / Tabel:",
    [
        "📊 Dashboard Executive Overview",
        "📋 Tabel Utama & Input Staff Operasional",
        "💵 Close / Open Cencon & Tes Cash",
        "🔄 UK TC, UK BDC & UK Siclus",
        "📑 Laporan EBOS",
        "💻 Rekon EJ (Electronic Journal)",
        "📦 Rekon Sislok & Review Stock",
        "🪙 Uang Kolong & Temuan Fisik",
        "📸 Unggah & Galeri Foto Bukti",
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
            <p>Sistem Pengawasan Rekonsiliasi Kas, Audit Staff, Uang Kolong, EBOS, EJ, Sislok Stock & Bukti Fisik Foto</p>
        </div>
        <div style="text-align: right;">
            <span class="status-badge">🟢 LIVE RECONCILIATION</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Helper for Safe Formatting in Streamlit Dataframe
# ---------------------------------------------------------
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
# MODUL 2: TABEL UTAMA & INPUT STAFF OPERASIONAL
# ---------------------------------------------------------
elif menu == "📋 Tabel Utama & Input Staff Operasional":
    st.subheader("📋 Rekonsiliasi Utama & Log Petugas/Staff Operasional (Matching source ost.png)")

    search_kw = st.text_input("🔍 Cari WSID, Lokasi, Nama Staff, atau Petugas Driver:", "")
    
    disp_df = filtered_df.copy()
    if search_kw:
        mask = (
            disp_df["WSID"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["LOKASI"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["STAFF_1"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["STAFF_2"].astype(str).str.contains(search_kw, case=False, na=False) |
            disp_df["DRIVER"].astype(str).str.contains(search_kw, case=False, na=False)
        )
        disp_df = disp_df[mask]

    formatted_df = disp_df.copy()
    if "TGL_INS" in formatted_df.columns and pd.api.types.is_datetime64_any_dtype(formatted_df["TGL_INS"]):
        formatted_df["TGL_INS"] = formatted_df["TGL_INS"].dt.strftime("%Y-%m-%d")
    if "TGL_REM" in formatted_df.columns and pd.api.types.is_datetime64_any_dtype(formatted_df["TGL_REM"]):
        formatted_df["TGL_REM"] = formatted_df["TGL_REM"].dt.strftime("%Y-%m-%d")

    # Display Styled Main Table
    cols_to_show = ["WSID", "LOK", "LOKASI", "Mesin", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_BCA"]
    cols_exist = [c for c in cols_to_show if c in formatted_df.columns]
    
    display_styled_df(formatted_df[cols_exist], ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"])

    st.markdown("---")
    st.markdown("### 👷 Detail Personel & Log Kerja Petugas per WSID")
    selected_wsid = st.selectbox("Pilih WSID untuk melihat rincian Petugas Staff & Bukti:", disp_df["WSID"].unique())
    
    wsid_row = disp_df[disp_df["WSID"] == selected_wsid].iloc[0]
    
    c_st1, c_st2, c_st3 = st.columns(3)
    with c_st1:
        st.write(f"**WSID / Terminal:** {wsid_row['WSID']} ({wsid_row['Mesin']})")
        st.write(f"**Lokasi:** {wsid_row['LOKASI']}")
        st.write(f"**Pengelola (LOK):** {wsid_row['LOK']}")
    with c_st2:
        st.write(f"**Petugas 1:** 👤 {wsid_row.get('STAFF_1', '-')}")
        st.write(f"**Petugas 2:** 👤 {wsid_row.get('STAFF_2', '-')}")
        st.write(f"**Petugas 3:** 👤 {wsid_row.get('STAFF_3', '-')}")
    with c_st3:
        st.write(f"**Driver Pengawal:** 🚚 {wsid_row.get('DRIVER', '-')}")
        st.write(f"**Aktivitas Jam:** ⏱️ {wsid_row.get('ACTIVITY', '-')}")
        st.write(f"**Catatan Lapangan:** 📝 {wsid_row.get('CATATAN_PROSES', '-')}")

    # Check if there is uploaded evidence image for this WSID
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
    st.write("Modul pemantauan penyeimbangan tes cash operasional (BDC vs NON-BDC).")

    df_cen = st.session_state.df_cencon.copy()
    if "TANGGAL" in df_cen.columns and pd.api.types.is_datetime64_any_dtype(df_cen["TANGGAL"]):
        df_cen["TANGGAL"] = df_cen["TANGGAL"].dt.strftime("%Y-%m-%d")

    display_styled_df(df_cen, ["BDC", "NON_BDC"])

    st.markdown("---")
    st.markdown("### ➕ Input Record Close / Open Cencon Baru")
    with st.form("form_cencon"):
        c_c1, c_c2, c_c3, c_c4 = st.columns(4)
        with c_c1:
            c_wsid = st.text_input("WSID Terminal", "Z5UM")
            c_lokasi = st.text_input("Nama Lokasi", "CRM PURWOSARI 2")
        with c_c2:
            c_tgl = st.date_input("Tanggal Transaksi")
            c_jam = st.text_input("Jam (HH:MM)", "20:22")
        with c_c3:
            c_bdc = st.number_input("Nominal BDC (Rp)", value=0, step=10000)
            c_non_bdc = st.number_input("Nominal NON-BDC (Rp)", value=100000, step=10000)
        with c_c4:
            c_status = st.selectbox("Status Cencon", ["Close", "Open", "Pending"])
            c_ket = st.text_input("Keterangan Tes Cash", "Tes cash sesuai 100,000")

        c_submit = st.form_submit_button("💾 Simpan Data Cencon")
        if c_submit:
            new_c = {
                "WSID": c_wsid, "LOKASI": c_lokasi, "TANGGAL": pd.to_datetime(c_tgl),
                "JAM": c_jam, "BDC": c_bdc, "NON_BDC": c_non_bdc,
                "STATUS": c_status, "KETERANGAN": c_ket
            }
            st.session_state.df_cencon = pd.concat([st.session_state.df_cencon, pd.DataFrame([new_c])], ignore_index=True)
            st.success("Data Cencon berhasil ditambahkan!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 4: UK TC, UK BDC & UK SICLUS
# ---------------------------------------------------------
elif menu == "🔄 UK TC, UK BDC & UK Siclus":
    st.subheader("🔄 Audit Uang Kembali (UK TC, UK BDC, UK Siclus)")
    st.write("Pencatatan klaim pengembalian uang (Uang Kembali / UK) akibat selisih kas atau keluhan nasabah.")

    df_u = st.session_state.df_uk.copy()
    if "TANGGAL" in df_u.columns and pd.api.types.is_datetime64_any_dtype(df_u["TANGGAL"]):
        df_u["TANGGAL"] = df_u["TANGGAL"].dt.strftime("%Y-%m-%d")

    display_styled_df(df_u, ["BDC", "NON_BDC", "TOTAL_UK"])

    st.markdown("---")
    st.markdown("### ➕ Input Klaim Uang Kembali (UK) Baru")
    with st.form("form_uk"):
        u_1, u_2, u_3, u_4 = st.columns(4)
        with u_1:
            uk_wsid = st.text_input("WSID Terminal", "ZM16")
            uk_lokasi = st.text_input("Nama Lokasi", "ALFAMD INDRAGIRI PASURUAN")
        with u_2:
            uk_tipe = st.selectbox("Tipe UK", ["UK Siclus", "UK TC", "UK BDC"])
            uk_tgl = st.date_input("Tanggal Klaim")
        with u_3:
            uk_jam = st.text_input("Jam Transaksi", "13:20")
            uk_bdc = st.number_input("Nominal UK BDC (Rp)", value=0, step=50000)
        with u_4:
            uk_non_bdc = st.number_input("Nominal UK Non-BDC (Rp)", value=100000, step=50000)
            uk_ket = st.text_input("Keterangan Rincian UK", "UK d.50 x 2 lbr")

        uk_submit = st.form_submit_button("💾 Simpan Record UK")
        if uk_submit:
            tot_uk = uk_bdc + uk_non_bdc
            new_u = {
                "WSID": uk_wsid, "LOKASI": uk_lokasi, "TANGGAL": pd.to_datetime(uk_tgl),
                "JAM": uk_jam, "TIPE_UK": uk_tipe, "BDC": uk_bdc, "NON_BDC": uk_non_bdc,
                "TOTAL_UK": tot_uk, "KETERANGAN": uk_ket
            }
            st.session_state.df_uk = pd.concat([st.session_state.df_uk, pd.DataFrame([new_u])], ignore_index=True)
            st.success("Record UK berhasil ditambahkan!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 5: LAPORAN EBOS
# ---------------------------------------------------------
elif menu == "📑 Laporan EBOS":
    st.subheader("📑 Monitoring & Registrasi Laporan EBOS")
    st.write("Sistem pencatatan laporan insiden dan selisih kas pada aplikasi EBOS sistem BCA.")

    df_eb = st.session_state.df_ebos.copy()
    if "TANGGAL" in df_eb.columns and pd.api.types.is_datetime64_any_dtype(df_eb["TANGGAL"]):
        df_eb["TANGGAL"] = df_eb["TANGGAL"].dt.strftime("%Y-%m-%d")

    display_styled_df(df_eb, ["NOMINAL_SELISIH"])

    st.markdown("---")
    st.markdown("### ➕ Registrasi Tiket Laporan EBOS Baru")
    with st.form("form_ebos"):
        e_1, e_2, e_3 = st.columns(3)
        with e_1:
            e_no = st.text_input("No Tiket EBOS", f"EBOS-202607-00{len(st.session_state.df_ebos)+1}")
            e_wsid = st.text_input("WSID Terminal", "ZDA3")
            e_lokasi = st.text_input("Lokasi Terminal", "WINGS PROBOLINGGO")
        with e_2:
            e_tgl = st.date_input("Tanggal Laporan")
            e_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
            e_nom = st.number_input("Nominal Selisih EBOS (Rp)", value=500000, step=50000)
        with e_3:
            e_status = st.selectbox("Status Tiket", ["Open", "In Review", "Resolved", "Closed"])
            e_catatan = st.text_area("Catatan Laporan EBOS", "Selisih ebos dalam verifikasi dokumen")

        ebos_submit = st.form_submit_button("💾 Registrasi Tiket EBOS")
        if ebos_submit:
            new_e = {
                "NO_LAPORAN": e_no, "WSID": e_wsid, "LOKASI": e_lokasi,
                "TANGGAL": pd.to_datetime(e_tgl), "TIPE_MESIN": e_mesin,
                "NOMINAL_SELISIH": e_nom, "STATUS_EBOS": e_status, "CATATAN_EBOS": e_catatan
            }
            st.session_state.df_ebos = pd.concat([st.session_state.df_ebos, pd.DataFrame([new_e])], ignore_index=True)
            st.success(f"Tiket {e_no} berhasil dicatat!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 6: REKON EJ (ELECTRONIC JOURNAL)
# ---------------------------------------------------------
elif menu == "💻 Rekon EJ (Electronic Journal)":
    st.subheader("💻 Rekonsiliasi Electronic Journal (EJ Audit)")
    st.write("Verifikasi log transaksi pita elektronik (Electronic Journal) mesin terhadap saldo fisik.")

    df_j = st.session_state.df_ej.copy()
    if "TANGGAL_EJ" in df_j.columns and pd.api.types.is_datetime64_any_dtype(df_j["TANGGAL_EJ"]):
        df_j["TANGGAL_EJ"] = df_j["TANGGAL_EJ"].dt.strftime("%Y-%m-%d")

    display_styled_df(df_j, ["NOMINAL_EJ"])

    st.markdown("---")
    st.markdown("### ➕ Input Log Rekon EJ Baru")
    with st.form("form_ej"):
        j_1, j_2, j_3 = st.columns(3)
        with j_1:
            j_wsid = st.text_input("WSID Terminal", "Z5UM")
            j_lokasi = st.text_input("Nama Lokasi", "PURWOSARI CRM 2")
            j_tgl = st.date_input("Tanggal Log EJ")
        with j_2:
            j_jam = st.text_input("Jam Transaksi", "20:57")
            j_kartu = st.text_input("No Kartu / Rekening", "5379-XXXX-1029")
            j_nom = st.number_input("Nominal Transaksi EJ (Rp)", value=100000, step=50000)
        with j_3:
            j_status = st.selectbox("Status Matching EJ", ["Matched", "Discrepancy - Short", "Discrepancy - Over"])
            j_catatan = st.text_area("Catatan Temuan EJ", "Tx Jam 20:57 dispenser d.100 x 1 lbr match")

        ej_submit = st.form_submit_button("💾 Simpan Record EJ")
        if ej_submit:
            new_j = {
                "WSID": j_wsid, "LOKASI": j_lokasi, "TANGGAL_EJ": pd.to_datetime(j_tgl),
                "JAM_TX": j_jam, "NO_KARTU_REK": j_kartu, "NOMINAL_EJ": j_nom,
                "STATUS_EJ": j_status, "CATATAN_EJ": j_catatan
            }
            st.session_state.df_ej = pd.concat([st.session_state.df_ej, pd.DataFrame([new_j])], ignore_index=True)
            st.success("Record Log EJ berhasil disimpan!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 7: REKON SISLOK & REVIEW STOCK
# ---------------------------------------------------------
elif menu == "📦 Rekon Sislok & Review Stock":
    st.subheader("📦 Rekonsiliasi Sistem Lokasi (Sislok) & Review Stock Kas")
    st.write("Audit komparasi antara saldo stok kas pada Sistem Lokasi (Sislok) dengan hasil penghitungan kas fisik.")

    df_s = st.session_state.df_sislok.copy()
    if "TANGGAL_AUDIT" in df_s.columns and pd.api.types.is_datetime64_any_dtype(df_s["TANGGAL_AUDIT"]):
        df_s["TANGGAL_AUDIT"] = df_s["TANGGAL_AUDIT"].dt.strftime("%Y-%m-%d")

    display_styled_df(df_s, ["STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR", "STOK_SISLOK_AKHIR", "FISIK_KAS_ACTUAL", "SELISIH_STOK"])

    st.markdown("---")
    st.markdown("### ➕ Input Review Stock Sislok Baru")
    with st.form("form_sislok"):
        s_1, s_2, s_3 = st.columns(3)
        with s_1:
            s_wsid = st.text_input("WSID Terminal", "Z0X2")
            s_lokasi = st.text_input("Lokasi Terminal", "IDM SUDIMORO MALANG")
            s_tgl = st.date_input("Tanggal Audit Stock")
        with s_2:
            s_awal = st.number_input("Stok Sislok Awal (Ribu Rp)", value=600000, step=10000)
            s_masuk = st.number_input("Total Kas Masuk (Ribu Rp)", value=649850, step=10000)
            s_keluar = st.number_input("Total Kas Keluar (Ribu Rp)", value=649800, step=10000)
        with s_3:
            s_sislok_akhir = s_awal + s_masuk - s_keluar
            st.info(f"Stok Sislok Akhir Terkalkulasi: **Rp {s_sislok_akhir:,.0f} (Ribu Rp)**")
            s_fisik = st.number_input("Fisik Kas Actual (Ribu Rp)", value=600000, step=10000)
            s_selisih = s_fisik - s_sislok_akhir
            s_status = "Balanced" if s_selisih == 0 else "Variance Detected"

        sislok_submit = st.form_submit_button("💾 Simpan Audit Stock Sislok")
        if sislok_submit:
            new_s = {
                "WSID": s_wsid, "LOKASI": s_lokasi, "TANGGAL_AUDIT": pd.to_datetime(s_tgl),
                "STOK_SISLOK_AWAL": s_awal, "KAS_MASUK": s_masuk, "KAS_KELUAR": s_keluar,
                "STOK_SISLOK_AKHIR": s_sislok_akhir, "FISIK_KAS_ACTUAL": s_fisik,
                "SELISIH_STOK": s_selisih, "STATUS_REVIEW": s_status
            }
            st.session_state.df_sislok = pd.concat([st.session_state.df_sislok, pd.DataFrame([new_s])], ignore_index=True)
            st.success("Audit Sislok berhasil diperbarui!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 8: UANG KOLONG & TEMUAN FISIK
# ---------------------------------------------------------
elif menu == "🪙 Uang Kolong & Temuan Fisik":
    st.subheader("🪙 Pencatatan Uang Kolong & Temuan Fisik Terselip")
    st.write("Modul pengawasan temuan uang tunai yang terselip/nyangkut di kolong dispenser, fascia, atau reject box mesin.")

    df_k = st.session_state.df_kolong.copy()
    if "TANGGAL_TEMUAN" in df_k.columns and pd.api.types.is_datetime64_any_dtype(df_k["TANGGAL_TEMUAN"]):
        df_k["TANGGAL_TEMUAN"] = df_k["TANGGAL_TEMUAN"].dt.strftime("%Y-%m-%d")

    display_styled_df(df_k, ["LEMBAR", "TOTAL_RUPIAH"])

    st.markdown("---")
    st.markdown("### ➕ Form Pencatatan Temuan Uang Kolong Baru")
    with st.form("form_kolong"):
        k_1, k_2, k_3 = st.columns(3)
        with k_1:
            k_wsid = st.text_input("WSID Terminal", "Z5UM")
            k_lokasi = st.text_input("Nama Lokasi", "PURWOSARI CRM 2")
            k_tgl = st.date_input("Tanggal Temuan")
        with k_2:
            k_denom = st.selectbox("Denominasi Uang", ["100,000", "50,000", "20,000"])
            k_lembar = st.number_input("Jumlah Lembar", value=1, min_value=1)
            val_denom = 100000 if k_denom == "100,000" else (50000 if k_denom == "50,000" else 20000)
            k_total = val_denom * k_lembar
            st.info(f"Total Nominal Temuan: **Rp {k_total:,.0f}**")
        with k_3:
            k_posisi = st.selectbox("Lokasi Temuan Fisik", ["Kolong Dispenser", "Fascia Roll / Bawah", "Reject Box Chamber", "Transport Mechanism"])
            k_ket = st.text_area("Keterangan Fisik", "Ditemukan terselip saat bongkar isi kas")

        kolong_submit = st.form_submit_button("💾 Simpan Temuan Uang Kolong")
        if kolong_submit:
            new_k = {
                "WSID": k_wsid, "LOKASI": k_lokasi, "TANGGAL_TEMUAN": pd.to_datetime(k_tgl),
                "DENOMINASI": k_denom, "LEMBAR": k_lembar, "TOTAL_RUPIAH": k_total,
                "LOKASI_TEMUAN": k_posisi, "KETERANGAN": k_ket
            }
            st.session_state.df_kolong = pd.concat([st.session_state.df_kolong, pd.DataFrame([new_k])], ignore_index=True)
            st.success("Temuan Uang Kolong berhasil dicatat!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 9: UNGGAH & GALERI FOTO BUKTI
# ---------------------------------------------------------
elif menu == "📸 Unggah & Galeri Foto Bukti":
    st.subheader("📸 Galeri & Unggah Lampiran Foto Bukti Fisik")
    st.write("Fitur untuk mengunggah dan melampirkan foto papan catatan kas, foto uang kolong, atau bukti struk fisik ke dalam tabel rekonsiliasi.")

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
# MODUL 10: INPUT & TAMBAH DATA TERPADU
# ---------------------------------------------------------
elif menu == "➕ Input & Tambah Data Terpadu":
    st.subheader("📝 Input Data Rekonsiliasi & Staff Lengkap")

    with st.form("form_tambah_terpadu"):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            new_wsid = st.text_input("WSID Terminal", "Z88M")
            new_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
            new_lokasi = st.text_input("Lokasi Terminal", "PURWOSARI CRM 3")
        with col_f2:
            new_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
            new_tgl_ins = st.date_input("Tanggal Pengisian (TGL_INS)")
            new_tgl_rem = st.date_input("Tanggal Penarikan (TGL_REM)")
        with col_f3:
            new_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=400000)
            new_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=399500)
            new_sel_awal = new_setor - new_cash_pos
            st.info(f"Estimasi Selisih Awal: **{new_sel_awal:,.0f} (Ribu Rp)**")
        with col_f4:
            new_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100)
            new_activity = st.text_input("Aktivitas & Jam", f"{datetime.now().strftime('%d/%m/%y %H:%M')} - BONGKAR ISI")

        st.markdown("#### 👥 Petugas / Staff Operasional & Driver")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            new_staff1 = st.text_input("Petugas 1", "BAYU OKTA PURWANTO")
        with col_s2:
            new_staff2 = st.text_input("Petugas 2", "AKHMAD RIZA MAULANA")
        with col_s3:
            new_staff3 = st.text_input("Petugas 3", "YOYOK BUDI RAKHMAN")
        with col_s4:
            new_driver = st.text_input("Driver Pengawal", "ASSYAVI ALIYULLOH M (DRIVER)")

        new_catatan = st.text_input("Catatan Lapangan", "Proses normal, UK d.100 x 1 lbr")
        new_tanggapan = st.text_area("Tanggapan BCA / Audit Log", f"Selisih Awal : {new_sel_awal}\\nUK : {abs(new_sel_awal - new_sel_akhir)}\\nSelisih Akhir : {new_sel_akhir}")

        submitted = st.form_submit_button("💾 Simpan Transaksi Lengkap")

        if submitted:
            new_row = {
                "WSID": new_wsid, "LOK": new_lok, "LOKASI": new_lokasi, "Mesin": new_mesin,
                "TGL_INS": pd.to_datetime(new_tgl_ins), "TGL_REM": pd.to_datetime(new_tgl_rem),
                "CASH_POS": new_cash_pos, "SETOR": new_setor, "SEL_AWAL": new_sel_awal, "SEL_AKHIR": new_sel_akhir,
                "STAFF_1": new_staff1, "STAFF_2": new_staff2, "STAFF_3": new_staff3,
                "DRIVER": new_driver, "ACTIVITY": new_activity, "CATATAN_PROSES": new_catatan,
                "TANGGAPAN_BCA": new_tanggapan
            }
            st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"Data WSID {new_wsid} berhasil ditambahkan!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 11: EKSPOR & IMPOR DATA EXCEL
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
'''

with open("/workspace/scratch/generate_v6.py", "w", encoding="utf-8") as f:
    f.write(v6_code)

print("generate_v6.py written.")
