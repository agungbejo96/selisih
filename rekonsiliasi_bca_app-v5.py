import streamlit as st

def safe_rerun():
    if hasattr(st, "rerun"):
        st.rerun()
    elif hasattr(st, "experimental_rerun"):
        st.experimental_rerun()

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# ---------------------------------------------------------
# Page Configuration & Elegant Theme Settings
# ---------------------------------------------------------
st.set_page_config(
    page_title="BCA ATM Reconciliation Portal",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Modern CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #F8FAFC;
        color: #1E293B;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 3rem;
        max-width: 96%;
    }

    /* Header Banner Styling */
    .hero-banner {
        background: linear-gradient(135deg, #002B49 0%, #00529C 60%, #0072CE 100%);
        padding: 28px 36px;
        border-radius: 16px;
        color: white;
        margin-bottom: 28px;
        box-shadow: 0 10px 25px -5px rgba(0, 82, 156, 0.25);
        position: relative;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .hero-banner::after {
        content: "";
        position: absolute;
        top: -50%;
        right: -10%;
        width: 350px;
        height: 350px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, rgba(255,255,255,0) 70%);
        border-radius: 50%;
    }
    .hero-title {
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin: 0;
        color: #FFFFFF;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        font-size: 14px;
        color: #CBD5E1;
        margin-top: 6px;
        font-weight: 400;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(8px);
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        letter-spacing: 0.5px;
        border: 1px solid rgba(255, 255, 255, 0.2);
    }

    /* Metric Card Styling */
    .metric-card-box {
        background: #FFFFFF;
        border-radius: 14px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .metric-card-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 20px rgba(0, 0, 0, 0.06);
    }
    .metric-label {
        font-size: 12px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 22px;
        font-weight: 800;
        color: #0F172A;
    }
    .metric-sub {
        font-size: 12px;
        font-weight: 500;
        margin-top: 4px;
    }
    .sub-red { color: #E11D48; }
    .sub-green { color: #059669; }
    .sub-blue { color: #0284C7; }

    /* Custom Badges */
    .badge-bca {
        background-color: #00529C;
        color: #FFFFFF;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }
    .badge-vendor {
        background-color: #059669;
        color: #FFFFFF;
        padding: 3px 10px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #FFFFFF;
        border-right: 1px solid #E2E8F0;
    }
    
    /* Section Headers */
    .section-title {
        font-size: 18px;
        font-weight: 700;
        color: #0F172A;
        margin-bottom: 16px;
        display: flex;
        align-items: center;
        gap: 8px;
        border-bottom: 2px solid #E2E8F0;
        padding-bottom: 8px;
    }

    /* Audit Log Card */
    .audit-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        padding: 20px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.02);
    }
    .audit-line-uk {
        background-color: #F0FDF4;
        border-left: 4px solid #16A34A;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #15803D;
        font-weight: 600;
    }
    .audit-line-keluhan {
        background-color: #FFF1F2;
        border-left: 4px solid #E11D48;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #BE123C;
        font-weight: 600;
    }
    .audit-line-koreksi {
        background-color: #EFF6FF;
        border-left: 4px solid #2563EB;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #1D4ED8;
        font-weight: 600;
    }
    .audit-line-default {
        background-color: #F8FAFC;
        border-left: 4px solid #94A3B8;
        padding: 10px 14px;
        border-radius: 6px;
        margin-bottom: 8px;
        font-size: 13px;
        color: #475569;
        font-weight: 500;
    }

    /* Hide default streamlit branding clutter */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Smart Data Sanitizer (Handles column variation robustly)
# ---------------------------------------------------------
def sanitize_columns(df_raw):
    df_clean = df_raw.copy()
    col_mapping = {}
    for col in df_clean.columns:
        c_upper = str(col).strip().upper().replace(" ", "_").replace("-", "_")
        if c_upper in ["WSID", "ID_WSID", "TERMINAL"]:
            col_mapping[col] = "WSID"
        elif c_upper in ["LOK", "PENGELOLA", "LOK_PENGELOLA"]:
            col_mapping[col] = "LOK"
        elif c_upper in ["LOKASI", "NAMA_LOKASI", "BRANCH", "LOKASI_MESIN"]:
            col_mapping[col] = "LOKASI"
        elif c_upper in ["MESIN", "TIPE_MESIN", "TYPE_MESIN", "MESIN_TIPE"]:
            col_mapping[col] = "Mesin"
        elif c_upper in ["TGL_INS", "TGL_INSERT", "TANGGAL_INS", "TANGGAL_INSERT"]:
            col_mapping[col] = "TGL_INS"
        elif c_upper in ["TGL_REM", "TGL_REMOVAL", "TANGGAL_REM", "TANGGAL_REMOVAL"]:
            col_mapping[col] = "TGL_REM"
        elif c_upper in ["CASH_POS", "CASHPOS", "CASH_POSITION", "POSISI_KAS"]:
            col_mapping[col] = "CASH_POS"
        elif c_upper in ["SETOR", "DISETOR", "REALISASI_SETOR", "JUMLAH_SETOR"]:
            col_mapping[col] = "SETOR"
        elif c_upper in ["SEL_AWAL", "SELISIH_AWAL", "VAR_AWAL"]:
            col_mapping[col] = "SEL_AWAL"
        elif c_upper in ["SEL_AKHIR", "SELISIH_AKHIR", "VAR_AKHIR"]:
            col_mapping[col] = "SEL_AKHIR"
        elif c_upper in ["TANGGAPAN_BCA", "TANGGAPAN", "CATATAN_BCA", "REMARKS"]:
            col_mapping[col] = "TANGGAPAN_BCA"
            
    df_clean = df_clean.rename(columns=col_mapping)
    
    # Required default fallback columns
    required_defaults = {
        "WSID": "UNKNOWN",
        "LOK": "BCA",
        "LOKASI": "LOKASI TIDAK TERDAFTAR",
        "Mesin": "O-CRM",
        "TGL_INS": "2026-07-01",
        "TGL_REM": "2026-07-05",
        "CASH_POS": 0,
        "SETOR": 0,
        "SEL_AWAL": 0,
        "SEL_AKHIR": 0,
        "TANGGAPAN_BCA": "Belum ada tanggapan"
    }
    for req_col, default_val in required_defaults.items():
        if req_col not in df_clean.columns:
            df_clean[req_col] = default_val

    # Ensure datetime format
    df_clean["TGL_INS"] = pd.to_datetime(df_clean["TGL_INS"], errors='coerce').fillna(pd.to_datetime("2026-07-01"))
    df_clean["TGL_REM"] = pd.to_datetime(df_clean["TGL_REM"], errors='coerce').fillna(pd.to_datetime("2026-07-05"))
    
    # Ensure numeric types
    for num_col in ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"]:
        df_clean[num_col] = pd.to_numeric(df_clean[num_col], errors='coerce').fillna(0)

    return df_clean

# ---------------------------------------------------------
# Initial Data Grounded in Source: juli.png
# ---------------------------------------------------------
def load_default_data():
    raw_data = [
        {
            "WSID": "Z5UM", "LOK": "BCA", "LOKASI": "PURWOSARI CRM 2", "Mesin": "O-CRM",
            "TGL_INS": "2026-06-29", "TGL_REM": "2026-07-03", "CASH_POS": 317400, "SETOR": 316800,
            "SEL_AWAL": -600, "SEL_AKHIR": -100,
            "TANGGAPAN_BCA": "Selisih Awal : -600\nUK : 500\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZM16", "LOK": "T", "LOKASI": "ALFAMD INDRAGIRI PASURUAN", "Mesin": "ITM",
            "TGL_INS": "2026-06-25", "TGL_REM": "2026-07-07", "CASH_POS": 342500, "SETOR": 339150,
            "SEL_AWAL": -3350, "SEL_AKHIR": -100,
            "TANGGAPAN_BCA": "Selisih Awal : -3,350\nUK : 3,350\nKeluhan Nsb : -100 tgl 25/06 jam 13:20\nSelisih Akhir : -100"
        },
        {
            "WSID": "Z0X2", "LOK": "T", "LOKASI": "IDM SUDIMORO MALANG", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-04", "TGL_REM": "2026-07-10", "CASH_POS": 649850, "SETOR": 649800,
            "SEL_AWAL": -50, "SEL_AKHIR": -50,
            "TANGGAPAN_BCA": "Selisih Awal : -50\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZDA3", "LOK": "T", "LOKASI": "WINGS PROBOLINGGO", "Mesin": "ITM",
            "TGL_INS": "2026-07-09", "TGL_REM": "2026-07-11", "CASH_POS": 576950, "SETOR": 602500,
            "SEL_AWAL": 25550, "SEL_AKHIR": -50,
            "TANGGAPAN_BCA": "Selisih Awal : 25,550\nKoreksi Adm : -25,600\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZB3X", "LOK": "T", "LOKASI": "PT ANEKA TUNA INDONESIA", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-09", "TGL_REM": "2026-07-12", "CASH_POS": 359200, "SETOR": 372100,
            "SEL_AWAL": 12900, "SEL_AKHIR": -100,
            "TANGGAPAN_BCA": "Selisih Awal : 12,900\nKeluhan Nsb : -2,500 tgl 11/07 jam 12:14\n-2,500 tgl 11/07 jam 12:13\n-2,500 tgl 11/07 jam 12:11\n-500 tgl 11/07 jam 10:33\n-2,500 tgl 11/07 jam 09:17\n-2,500 tgl 11/07 jam 15:02\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZH9M", "LOK": "BCA", "LOKASI": "KRAKSAAN", "Mesin": "ITM",
            "TGL_INS": "2026-07-12", "TGL_REM": "2026-07-15", "CASH_POS": 679350, "SETOR": 679150,
            "SEL_AWAL": -200, "SEL_AKHIR": -100,
            "TANGGAPAN_BCA": "Selisih Awal : -200\nKoreksi Adm : -100\nUK : 200\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZQ8Y", "LOK": "T", "LOKASI": "ALFAMD MERTOJOYO MALANG", "Mesin": "ACH",
            "TGL_INS": "2026-07-01", "TGL_REM": "2026-07-17", "CASH_POS": 668650, "SETOR": 668500,
            "SEL_AWAL": -150, "SEL_AKHIR": -50,
            "TANGGAPAN_BCA": "Selisih Awal : -150\nKeluhan Nsb : -50 tgl 13/07 jam 15:19\nUK : 150\nSelisih Akhir : -50"
        },
        {
            "WSID": "Z0V1", "LOK": "T", "LOKASI": "ALFA KEPANJEN", "Mesin": "O-CRM",
            "TGL_INS": "2026-07-16", "TGL_REM": "2026-07-18", "CASH_POS": 144600, "SETOR": 144550,
            "SEL_AWAL": -50, "SEL_AKHIR": -50,
            "TANGGAPAN_BCA": "Selisih Awal : -50\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZK82", "LOK": "T", "LOKASI": "IDM WARUNGDOWO PASURUAN", "Mesin": "O-CRM",
            "TGL_INS": "2026-07-15", "TGL_REM": "2026-07-18", "CASH_POS": 360750, "SETOR": 356500,
            "SEL_AWAL": -4250, "SEL_AKHIR": -50,
            "TANGGAPAN_BCA": "Selisih Awal : -4,250\nKeluhan Nsb : -1,200 tgl 15/07 jam 19:25\nUK : 5,400\nSelisih Akhir : -50"
        },
        {
            "WSID": "ZK66", "LOK": "T", "LOKASI": "ALFA PAKIS MALANG", "Mesin": "O-CRM",
            "TGL_INS": "2026-07-18", "TGL_REM": "2026-07-20", "CASH_POS": 602500, "SETOR": 602050,
            "SEL_AWAL": -450, "SEL_AKHIR": -50,
            "TANGGAPAN_BCA": "Selisih Awal : -450\nUK : 400\nSelisih Akhir : -50"
        },
        {
            "WSID": "Z1ZP", "LOK": "T", "LOKASI": "IDM HYBRID PB SUDIRMAN", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-17", "TGL_REM": "2026-07-21", "CASH_POS": 499300, "SETOR": 499000,
            "SEL_AWAL": -300, "SEL_AKHIR": -100,
            "TANGGAPAN_BCA": "Selisih Awal : -300\nUK : 200\nSelisih Akhir : -100"
        },
        {
            "WSID": "ZPQ8", "LOK": "T", "LOKASI": "IDM DONOMULYO MALANG", "Mesin": "CRMHYO",
            "TGL_INS": "2026-07-14", "TGL_REM": "2026-07-23", "CASH_POS": 185100, "SETOR": 182200,
            "SEL_AWAL": -2900, "SEL_AKHIR": -200,
            "TANGGAPAN_BCA": "Selisih Awal : -2,900\nUK : 2,700\nSelisih Akhir : -200"
        }
    ]
    df = pd.DataFrame(raw_data)
    return sanitize_columns(df)

if "df_rekon" not in st.session_state:
    st.session_state.df_rekon = load_default_data()

df = sanitize_columns(st.session_state.df_rekon)

# ---------------------------------------------------------
# Sidebar Navigation & Filter Section
# ---------------------------------------------------------
st.sidebar.markdown("""
<div style="text-align: center; padding: 10px 0 20px 0;">
    <h2 style="color: #00529C; margin:0; font-weight:800; font-size:22px;">🏦 BCA PORTAL</h2>
    <p style="color: #64748B; font-size: 11px; margin:2px 0 0 0; font-weight: 600;">ATM & CASH RECONCILIATION</p>
</div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "MENU UTAMA",
    [
        "📊 Executive Dashboard",
        "📋 Tabel Rekonsiliasi Kas",
        "➕ Input Transaksi Baru",
        "🔍 Audit Tanggapan BCA",
        "📁 Kelola File Data"
    ]
)

st.sidebar.markdown("<br><hr style='margin: 10px 0; border-color: #E2E8F0;'><h4 style='font-size:13px; font-weight:700; color:#475569;'>🔍 FILTER GLOBAL DATA</h4>", unsafe_allow_html=True)

opt_mesin = list(df["Mesin"].dropna().unique())
mesin_filter = st.sidebar.multiselect("Tipe Mesin Terminal:", options=opt_mesin, default=opt_mesin)

opt_lok = list(df["LOK"].dropna().unique())
lok_filter = st.sidebar.multiselect("Pengelola (LOK):", options=opt_lok, default=opt_lok)

filtered_df = df[(df["Mesin"].isin(mesin_filter)) & (df["LOK"].isin(lok_filter))]

st.sidebar.markdown("<br><div style='background-color:#F1F5F9; padding:12px; border-radius:8px; font-size:11px; color:#64748B;'><strong>Info Operasional:</strong><br>Seluruh data nominal dikalkulasikan secara otomatis dari sistem rekonsiliasi kas pusat.</div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Header Hero Banner
# ---------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <div>
            <div class="hero-title">
                🏦 BCA Cash Variance & Reconciliation System
            </div>
            <div class="hero-subtitle">
                Portal Pengawasan Kas Operasional Terminal ATM, CRM, ITM, dan ACH Wilayah
            </div>
        </div>
        <div class="hero-badge">
            LIVE MONITORING
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MODUL 1: EXECUTIVE DASHBOARD
# ---------------------------------------------------------
if menu == "📊 Executive Dashboard":
    st.markdown('<div class="section-title">📊 Key Performance Indicators (KPI)</div>', unsafe_allow_html=True)

    col1, col2, col3, col4, col5 = st.columns(5)
    
    tot_terminal = len(filtered_df)
    tot_pos = filtered_df["CASH_POS"].sum() * 1000
    tot_setor = filtered_df["SETOR"].sum() * 1000
    tot_sel_awal = filtered_df["SEL_AWAL"].sum() * 1000
    tot_sel_akhir = filtered_df["SEL_AKHIR"].sum() * 1000

    with col1:
        st.markdown(f"""
        <div class="metric-card-box">
            <div class="metric-label">TOTAL TERMINAL</div>
            <div class="metric-value">{tot_terminal} <span style="font-size:14px; font-weight:600; color:#64748B;">Unit</span></div>
            <div class="metric-sub sub-blue">Active Managed</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card-box">
            <div class="metric-label">CASH POSITION SISTEM</div>
            <div class="metric-value">Rp {tot_pos/1e6:,.1f}M</div>
            <div class="metric-sub sub-blue">Total Saldo Terpencet</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card-box">
            <div class="metric-label">REALISASI SETOR</div>
            <div class="metric-value">Rp {tot_setor/1e6:,.1f}M</div>
            <div class="metric-sub sub-green">Total Kas Disetor</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        sub_class = "sub-red" if tot_sel_awal < 0 else "sub-green"
        st.markdown(f"""
        <div class="metric-card-box">
            <div class="metric-label">SELISIH AWAL</div>
            <div class="metric-value" style="color:{'#E11D48' if tot_sel_awal < 0 else '#059669'};">Rp {tot_sel_awal/1e3:,.0f}K</div>
            <div class="metric-sub {sub_class}">Sebelum Resolution</div>
        </div>
        """, unsafe_allow_html=True)

    with col5:
        sub_class = "sub-red" if tot_sel_akhir < 0 else "sub-green"
        st.markdown(f"""
        <div class="metric-card-box">
            <div class="metric-label">SELISIH AKHIR AUDIT</div>
            <div class="metric-value" style="color:{'#E11D48' if tot_sel_akhir < 0 else '#059669'};">Rp {tot_sel_akhir/1e3:,.0f}K</div>
            <div class="metric-sub {sub_class}">Net Unresolved</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Interactive Visualizations Section
    col_g1, col_g2 = st.columns([1.6, 1])

    with col_g1:
        st.markdown('<div class="section-title">📈 Perbandingan Cash Position vs Realisasi Setor per WSID</div>', unsafe_allow_html=True)
        
        fig_bar = go.Figure()
        fig_bar.add_trace(go.Bar(
            x=filtered_df["WSID"],
            y=filtered_df["CASH_POS"],
            name="Cash Position (Sistem)",
            marker_color="#00529C",
            hovertemplate="WSID %{x}<br>Cash Pos: Rp %{y:,.0f} Ribu<extra></extra>"
        ))
        fig_bar.add_trace(go.Bar(
            x=filtered_df["WSID"],
            y=filtered_df["SETOR"],
            name="Realisasi Setor",
            marker_color="#00A3E0",
            hovertemplate="WSID %{x}<br>Setor: Rp %{y:,.0f} Ribu<extra></extra>"
        ))
        fig_bar.update_layout(
            barmode="group",
            margin=dict(l=20, r=20, t=20, b=20),
            height=340,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False, title="WSID Terminal"),
            yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Nominal (x1.000 Rp)")
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_g2:
        st.markdown('<div class="section-title">🍰 Sebaran Tipe Mesin</div>', unsafe_allow_html=True)
        mesin_counts = filtered_df["Mesin"].value_counts().reset_index()
        mesin_counts.columns = ["Tipe Mesin", "Jumlah"]

        fig_pie = px.pie(
            mesin_counts,
            names="Tipe Mesin",
            values="Jumlah",
            hole=0.5,
            color_discrete_sequence=["#00529C", "#00A3E0", "#059669", "#D97706"]
        )
        fig_pie.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            height=340,
            paper_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", yanchor="bottom", y=-0.1)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    # Secondary Chart
    st.markdown('<div class="section-title">⚠️ Magnitude Selisih Awal vs Selisih Akhir per WSID</div>', unsafe_allow_html=True)
    fig_var = go.Figure()
    fig_var.add_trace(go.Bar(
        x=filtered_df["WSID"],
        y=filtered_df["SEL_AWAL"],
        name="Selisih Awal",
        marker_color="#E11D48",
        hovertemplate="WSID %{x}<br>Selisih Awal: Rp %{y:,.0f} Ribu<extra></extra>"
    ))
    fig_var.add_trace(go.Bar(
        x=filtered_df["WSID"],
        y=filtered_df["SEL_AKHIR"],
        name="Selisih Akhir Audit",
        marker_color="#0F172A",
        hovertemplate="WSID %{x}<br>Selisih Akhir: Rp %{y:,.0f} Ribu<extra></extra>"
    ))
    fig_var.update_layout(
        barmode="group",
        margin=dict(l=20, r=20, t=20, b=20),
        height=300,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        xaxis=dict(showgrid=False, title="WSID Terminal"),
        yaxis=dict(showgrid=True, gridcolor="#F1F5F9", title="Nominal Selisih (x1.000 Rp)")
    )
    st.plotly_chart(fig_var, use_container_width=True)

# ---------------------------------------------------------
# MODUL 2: TABEL REKONSILIASI KAS
# ---------------------------------------------------------
elif menu == "📋 Tabel Rekonsiliasi Kas":
    st.markdown('<div class="section-title">📋 Laporan Detail Rekonsiliasi Kas ATM & CRM</div>', unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([3, 1])
    with col_s1:
        search_kw = st.text_input("🔎 Cari berdasarkan WSID atau Nama Lokasi:", "", placeholder="Ketik kata kunci...")
    with col_s2:
        st.write("")
        st.write("")
        st.caption(f"Menampilkan **{len(filtered_df)}** data terfilter")

    if search_kw:
        display_df = filtered_df[
            filtered_df["WSID"].astype(str).str.contains(search_kw, case=False, na=False) |
            filtered_df["LOKASI"].astype(str).str.contains(search_kw, case=False, na=False)
        ]
    else:
        display_df = filtered_df.copy()

    # Formatted DataFrame display
    formatted_df = display_df.copy()
    formatted_df["TGL_INS"] = pd.to_datetime(formatted_df["TGL_INS"]).dt.strftime("%Y-%m-%d")
    formatted_df["TGL_REM"] = pd.to_datetime(formatted_df["TGL_REM"]).dt.strftime("%Y-%m-%d")

    styler = formatted_df.style.format({
        "CASH_POS": "{:,.0f}",
        "SETOR": "{:,.0f}",
        "SEL_AWAL": "{:,.0f}",
        "SEL_AKHIR": "{:,.0f}"
    })

    # Backward and forward compatible styling logic
    highlight_style = lambda v: 'color: #E11D48; font-weight: 700; background-color: #FFF1F2;' if isinstance(v, (int, float)) and v < 0 else ('color: #059669; font-weight: 700;' if isinstance(v, (int, float)) and v > 0 else '')
    
    if hasattr(styler, "map"):
        styler = styler.map(highlight_style, subset=["SEL_AWAL", "SEL_AKHIR"])
    elif hasattr(styler, "applymap"):
        styler = styler.applymap(highlight_style, subset=["SEL_AWAL", "SEL_AKHIR"])

    st.dataframe(
        styler,
        use_container_width=True,
        height=520
    )

    st.info("💡 **Catatan Nominal:** Seluruh nilai pecahan angka kas (CASH_POS, SETOR, SEL_AWAL, SEL_AKHIR) disajikan dalam **ribuan Rupiah (x1.000)** sesuai standar laporan fisik BCA.")

# ---------------------------------------------------------
# MODUL 3: INPUT TRANSAKSI BARU
# ---------------------------------------------------------
elif menu == "➕ Input Transaksi Baru":
    st.markdown('<div class="section-title">➕ Form Entri Data Rekonsiliasi Terminal</div>', unsafe_allow_html=True)

    with st.form("form_tambah_data"):
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            new_wsid = st.text_input("WSID Terminal", "Z88M")
            new_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
            new_lokasi = st.text_input("Nama Lokasi / Cabang", "KCP MALANG SULAWESI")
        with col_f2:
            new_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
            new_tgl_ins = st.date_input("Tanggal Insert (TGL_INS)")
            new_tgl_rem = st.date_input("Tanggal Removal (TGL_REM)")
        with col_f3:
            new_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=500000, step=100)
            new_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=499500, step=100)
            new_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100, step=50)

        new_sel_awal = new_setor - new_cash_pos
        st.markdown(f"""
        <div style="background-color:#F0F9FF; border-left:4px solid #0284C7; padding:12px; border-radius:6px; margin: 10px 0;">
            <strong>Kalkulasi Estimasi Selisih Awal:</strong> <span style="font-size:16px; font-weight:800; color:{'#E11D48' if new_sel_awal < 0 else '#059669'};">Rp {new_sel_awal:,.0f} (x1.000)</span>
        </div>
        """, unsafe_allow_html=True)

        new_tanggapan = st.text_area("Tanggapan BCA / Catatan Audit Resolution", f"Selisih Awal : {new_sel_awal:,}\nUK : {abs(new_sel_awal - new_sel_akhir):,}\nSelisih Akhir : {new_sel_akhir:,}")

        submitted = st.form_submit_button("💾 Simpan Data Rekonsiliasi Baru", use_container_width=True)

        if submitted:
            new_row = {
                "WSID": new_wsid,
                "LOK": new_lok,
                "LOKASI": new_lokasi,
                "Mesin": new_mesin,
                "TGL_INS": pd.to_datetime(new_tgl_ins),
                "TGL_REM": pd.to_datetime(new_tgl_rem),
                "CASH_POS": new_cash_pos,
                "SETOR": new_setor,
                "SEL_AWAL": new_sel_awal,
                "SEL_AKHIR": new_sel_akhir,
                "TANGGAPAN_BCA": new_tanggapan
            }
            st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_row])], ignore_index=True)
            st.success(f"✅ Data Terminal WSID {new_wsid} berhasil disimpan ke database session!")
            safe_rerun()

# ---------------------------------------------------------
# MODUL 4: AUDIT TANGGAPAN BCA
# ---------------------------------------------------------
elif menu == "🔍 Audit Tanggapan BCA":
    st.markdown('<div class="section-title">🔍 Audit Tanggapan & Resolution Trace BCA</div>', unsafe_allow_html=True)

    wsid_list = list(filtered_df["WSID"].unique())
    if len(wsid_list) == 0:
        st.warning("Tidak ada data terminal yang sesuai dengan filter.")
    else:
        selected_wsid = st.selectbox("Pilih WSID Terminal untuk Penelusuran Detail:", wsid_list)
        wsid_row = filtered_df[filtered_df["WSID"] == selected_wsid].iloc[0]

        st.markdown(f"""
        <div class="audit-card">
            <div style="display:flex; justify-content:space-between; align-items:center; border-bottom:1px solid #E2E8F0; padding-bottom:12px; margin-bottom:16px;">
                <div>
                    <h3 style="margin:0; color:#00529C; font-weight:800;">WSID: {wsid_row['WSID']} - {wsid_row['LOKASI']}</h3>
                    <p style="margin:2px 0 0 0; font-size:12px; color:#64748B;">Tipe Mesin: <strong>{wsid_row['Mesin']}</strong> | Pengelola (LOK): <strong>{wsid_row['LOK']}</strong></p>
                </div>
                <div>
                    <span class="badge-bca">PERIODE OPERASIONAL</span>
                </div>
            </div>
            <div style="display:grid; grid-template-columns: repeat(4, 1fr); gap:12px; margin-bottom:20px;">
                <div style="background:#F8FAFC; padding:10px; border-radius:8px;">
                    <div style="font-size:11px; color:#64748B; font-weight:700;">TGL INSERT</div>
                    <div style="font-size:14px; font-weight:700; color:#0F172A;">{pd.to_datetime(wsid_row['TGL_INS']).strftime('%d %b %Y')}</div>
                </div>
                <div style="background:#F8FAFC; padding:10px; border-radius:8px;">
                    <div style="font-size:11px; color:#64748B; font-weight:700;">TGL REMOVAL</div>
                    <div style="font-size:14px; font-weight:700; color:#0F172A;">{pd.to_datetime(wsid_row['TGL_REM']).strftime('%d %b %Y')}</div>
                </div>
                <div style="background:#F8FAFC; padding:10px; border-radius:8px;">
                    <div style="font-size:11px; color:#64748B; font-weight:700;">SELISIH AWAL</div>
                    <div style="font-size:14px; font-weight:700; color:{'#E11D48' if wsid_row['SEL_AWAL'] < 0 else '#059669'};">Rp {wsid_row['SEL_AWAL']*1000:,.0f}</div>
                </div>
                <div style="background:#F8FAFC; padding:10px; border-radius:8px;">
                    <div style="font-size:11px; color:#64748B; font-weight:700;">SELISIH AKHIR</div>
                    <div style="font-size:14px; font-weight:700; color:{'#E11D48' if wsid_row['SEL_AKHIR'] < 0 else '#059669'};">Rp {wsid_row['SEL_AKHIR']*1000:,.0f}</div>
                </div>
            </div>
            <h4 style="font-size:14px; font-weight:700; color:#0F172A; margin-bottom:10px;">📜 Chronological Audit Log (Tanggapan Operasional BCA):</h4>
        """, unsafe_allow_html=True)

        tanggapan_lines = str(wsid_row["TANGGAPAN_BCA"]).split("\n")
        for line in tanggapan_lines:
            line_str = line.strip()
            if not line_str:
                continue
            if "UK" in line_str or "Pengembalian" in line_str:
                st.markdown(f'<div class="audit-line-uk">✅ {line_str}</div>', unsafe_allow_html=True)
            elif "Keluhan" in line_str:
                st.markdown(f'<div class="audit-line-keluhan">⚠️ {line_str}</div>', unsafe_allow_html=True)
            elif "Koreksi" in line_str:
                st.markdown(f'<div class="audit-line-koreksi">ℹ️ {line_str}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="audit-line-default">🔹 {line_str}</div>', unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------------------------
# MODUL 5: KELOLA FILE DATA (EKSPOR / IMPOR)
# ---------------------------------------------------------
elif menu == "📁 Kelola File Data":
    st.markdown('<div class="section-title">📁 Kelola File Data & Backup Laporan</div>', unsafe_allow_html=True)

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:20px; border-radius:12px;">
            <h3 style="color:#00529C; font-size:16px; margin:0 0 10px 0;">📥 Unduh Laporan Excel Terkini</h3>
            <p style="font-size:13px; color:#64748B;">Ekspor seluruh database rekonsiliasi yang tampil ke dalam format file Microsoft Excel (.xlsx).</p>
        </div>
        """, unsafe_allow_html=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df = st.session_state.df_rekon.copy()
            export_df["TGL_INS"] = pd.to_datetime(export_df["TGL_INS"]).dt.strftime("%Y-%m-%d")
            export_df["TGL_REM"] = pd.to_datetime(export_df["TGL_REM"]).dt.strftime("%Y-%m-%d")
            export_df.to_excel(writer, sheet_name='Rekonsiliasi_BCA', index=False)

        st.download_button(
            label="💾 Download File Excel (.xlsx)",
            data=output.getvalue(),
            file_name=f"Laporan_Rekonsiliasi_BCA_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with col_ex2:
        st.markdown("""
        <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:20px; border-radius:12px; margin-bottom:10px;">
            <h3 style="color:#00529C; font-size:16px; margin:0 0 10px 0;">📤 Upload File Data Baru</h3>
            <p style="font-size:13px; color:#64748B;">Unggah berkas Excel (.xlsx / .xls) atau CSV baru untuk mengganti database kerja.</p>
        </div>
        """, unsafe_allow_html=True)

        uploaded_file = st.file_uploader("Pilih Berkas Excel/CSV Data Rekonsiliasi:", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    new_df = pd.read_csv(uploaded_file)
                else:
                    new_df = pd.read_excel(uploaded_file)

                st.session_state.df_rekon = sanitize_columns(new_df)
                st.success("✅ File berhasil diunggah & disinkronisasi ke dalam sistem portal!")
                safe_rerun()
            except Exception as e:
                st.error(f"❌ Gagal memuat file: {e}")
