import streamlit as st
import re

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
from PIL import Image
import os
import pickle

CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".app_data")
DATA_CACHE_FILE = os.path.join(CACHE_DIR, "rekon_data_cache.pkl")

def save_persistent_state(data_scopes, active_scope=None):
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        payload = {
            "data_scopes": data_scopes,
            "active_scope": active_scope,
            "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        with open(DATA_CACHE_FILE, "wb") as f:
            pickle.dump(payload, f)
    except Exception:
        pass

def load_persistent_state():
    if os.path.exists(DATA_CACHE_FILE):
        try:
            with open(DATA_CACHE_FILE, "rb") as f:
                return pickle.load(f)
        except Exception:
            return None
    return None

def get_query_param(key, default=None):
    try:
        if hasattr(st, "query_params") and key in st.query_params:
            val = st.query_params[key]
            return val if val else default
        elif hasattr(st, "experimental_get_query_params"):
            qp = st.experimental_get_query_params()
            if key in qp and qp[key]:
                return qp[key][0]
    except Exception:
        pass
    return default

def set_query_param(key, value):
    try:
        if hasattr(st, "query_params"):
            st.query_params[key] = str(value)
        elif hasattr(st, "experimental_set_query_params"):
            qp = st.experimental_get_query_params()
            qp[key] = [str(value)]
            st.experimental_set_query_params(**qp)
    except Exception:
        pass

def clear_query_params():
    try:
        if hasattr(st, "query_params"):
            st.query_params.clear()
        elif hasattr(st, "experimental_set_query_params"):
            st.experimental_set_query_params()
    except Exception:
        pass

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

def amount_color(value):
    numeric_value = safe_float(value)
    if numeric_value < 0:
        return "#E11D48"
    if numeric_value > 0:
        return "#047857"
    return "#64748B"

def is_identifier_column(column_name):
    normalized_name = re.sub(r"[^a-z0-9]+", "", str(column_name).lower())
    return normalized_name in {"no", "nomor", "idatm", "nomoratm"}

def is_insert_remove_date_column(column_name):
    normalized_name = re.sub(r"[^a-z0-9]+", "", str(column_name).lower())
    return normalized_name in {
        "tglins", "tglrem", "tanggalinsert", "tanggalremove",
        "tanggalinsertion", "tanggalremoval", "insertdate", "removedate"
    }

def is_remove_date_column(column_name):
    normalized_name = re.sub(r"[^a-z0-9]+", "", str(column_name).lower())
    return normalized_name in {"tglrem", "tanggalremove", "tanggalremoval", "removedate"}

def get_remove_date_series(df):
    for column in df.columns:
        if is_remove_date_column(column):
            return df[column]
    return pd.Series("-", index=df.index)

def convert_insert_remove_dates(df):
    converted_df = df.copy()
    for column in converted_df.columns:
        if is_insert_remove_date_column(column):
            converted_df[column] = pd.to_datetime(converted_df[column], dayfirst=True, errors="coerce")
    return converted_df

def month_from_remove_date(series):
    month_names = {
        1: "Januari", 2: "Februari", 3: "Maret", 4: "April", 5: "Mei", 6: "Juni",
        7: "Juli", 8: "Agustus", 9: "September", 10: "Oktober", 11: "November", 12: "Desember"
    }
    remove_dates = pd.to_datetime(series, dayfirst=True, errors="coerce")
    return remove_dates.map(
        lambda date_value: f"{month_names[date_value.month]} {date_value.year}"
        if pd.notna(date_value) else "-"
    )

def month_sort_key(month_value):
    month_numbers = {
        "januari": 1, "februari": 2, "maret": 3, "april": 4, "mei": 5, "juni": 6,
        "juli": 7, "agustus": 8, "september": 9, "oktober": 10, "november": 11, "desember": 12
    }
    parts = str(month_value).strip().lower().split()
    if len(parts) == 2 and parts[0] in month_numbers and parts[1].isdigit():
        return int(parts[1]), month_numbers[parts[0]]
    return (9999, 99)

def remove_duplicate_rekon_rows(df):
    if df.empty:
        return df
    hidden_columns = {
        "STAFF_1", "STAFF_2", "STAFF_3", "STAFF_LAINNYA", "DRIVER",
        "DAFTAR_STAFF_LENGKAP"
    }
    visible_columns = [column for column in df.columns if column not in hidden_columns]
    if not visible_columns:
        return df.drop_duplicates(keep="first").reset_index(drop=True)
    duplicate_check = df[visible_columns].copy()
    for column in visible_columns:
        duplicate_check[column] = duplicate_check[column].map(
            lambda value: "" if pd.isna(value) else str(value).strip().casefold()
        )
    return df.loc[~duplicate_check.duplicated(keep="first")].reset_index(drop=True)


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


# Helper SVG BCA Logo Generator
def get_abacus_logo_html(width=240, height=62):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 350 85" width="{width}" height="{height}" style="vertical-align: middle;">
    <defs>
        <linearGradient id="abacusGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#0A192F"/>
            <stop offset="50%" stop-color="#002B49"/>
            <stop offset="100%" stop-color="#00529C"/>
        </linearGradient>
        <linearGradient id="abacusGold" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#FBBF24"/>
            <stop offset="50%" stop-color="#F59E0B"/>
            <stop offset="100%" stop-color="#D97706"/>
        </linearGradient>
        <filter id="abacusGlow" x="-10%" y="-10%" width="120%" height="120%">
            <feDropShadow dx="0" dy="2" stdDeviation="3" flood-color="#000" flood-opacity="0.35"/>
        </filter>
    </defs>
    <rect width="350" height="85" rx="14" fill="url(#abacusGrad)" filter="url(#abacusGlow)"/>
    <rect x="2" y="2" width="346" height="81" rx="12" fill="none" stroke="url(#abacusGold)" stroke-width="1.5" stroke-opacity="0.8"/>
    <g transform="translate(18, 14)">
        <rect width="56" height="57" rx="12" fill="url(#abacusGold)"/>
        <!-- Stylized Abacus/A Cash Emblem -->
        <path d="M 28,10 L 46,46 L 38,46 L 33,30 L 23,30 L 18,46 L 10,46 Z M 28,18 L 25,25 L 31,25 Z" fill="#0A192F"/>
        <circle cx="28" cy="12" r="3" fill="#FFFFFF"/>
        <line x1="14" y1="38" x2="42" y2="38" stroke="#FFFFFF" stroke-width="2.5" stroke-linecap="round"/>
        <circle cx="20" cy="38" r="2.5" fill="#FBBF24"/>
        <circle cx="28" cy="38" r="2.5" fill="#FBBF24"/>
        <circle cx="36" cy="38" r="2.5" fill="#FBBF24"/>
    </g>
    <text x="88" y="46" font-family="'Plus Jakarta Sans', Arial, sans-serif" font-weight="900" font-size="28" fill="#FFFFFF" letter-spacing="2">ABACUS</text>
    <text x="89" y="65" font-family="'Plus Jakarta Sans', Arial, sans-serif" font-weight="800" font-size="11" fill="#FBBF24" letter-spacing="2">CASH SOLUTION • MALANG</text>
</svg>'''

def ensure_numeric_df(df):
    if df.empty:
        return df
    num_cols = ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "BDC", "NON_BDC", "TOTAL_UK", "NOMINAL_SELISIH", "NOMINAL_EJ", "STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR", "STOK_SISLOK_AKHIR", "FISIK_KAS_ACTUAL", "SELISIH_STOK", "LEMBAR", "TOTAL_RUPIAH"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.replace("Rp", "").str.strip(), errors="coerce").fillna(0)
    return df

# ---------------------------------------------------------
# Page Configuration & Styling (Abacus Malang Corporate Theme)
# ---------------------------------------------------------
st.set_page_config(
    page_title="Abacus Malang - Cash Reconciliation & Auto-Append Import System",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Executive Abacus Malang Branding & Data Display
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800;900&display=swap');

    :root {
        --navy: #002B49;
        --navy-deep: #001F3F;
        --blue: #00529C;
        --blue-bright: #0072CE;
        --gold: #F59E0B;
        --gold-bright: #FBBF24;
        --bg-page: #FFFFFF;
        --bg-card: #F9FAFB;
        --border: #E2E8F0;
        --border-light: #D9E3ED;
        --text-primary: #111827;
        --text-secondary: #374151;
        --text-muted: #6B7280;
        --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.06);
        --shadow-md: 0 4px 12px rgba(0, 0, 0, 0.08);
        --shadow-lg: 0 12px 32px rgba(0, 0, 0, 0.12);
        --shadow-xl: 0 24px 60px rgba(0, 0, 0, 0.18);
        --radius-sm: 8px;
        --radius-md: 14px;
        --radius-lg: 22px;
        --radius-xl: 28px;
        --font-display: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-sans: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        --font-mono: 'SF Mono', Monaco, 'Cascadia Code', monospace;
    }

    html, body, [class*="css"] {
        font-family: var(--font-sans);
        font-weight: 500;
        line-height: 1.6;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
        text-rendering: optimizeLegibility;
    }

    /* ---- Global Page Background ---- */
    .stApp {
        background: var(--bg-page);
    }
    .block-container {
        padding: 1.6rem 2rem 3rem 2rem;
        max-width: 100%;
    }

    /* ---- Executive Header ---- */
    .main-header {
        background: linear-gradient(135deg, var(--navy-deep) 0%, var(--navy) 40%, var(--blue) 100%);
        padding: 26px 32px;
        border-radius: var(--radius-lg);
        color: #FFFFFF;
        margin-bottom: 28px;
        box-shadow: var(--shadow-lg);
        border: 1px solid rgba(255, 255, 255, 0.08);
        position: relative;
        overflow: hidden;
    }
    .main-header::before {
        content: "";
        position: absolute;
        top: -60px;
        right: -60px;
        width: 220px;
        height: 220px;
        background: radial-gradient(circle, rgba(251, 191, 36, 0.14) 0%, rgba(251, 191, 36, 0) 70%);
        border-radius: 50%;
    }
    .main-header h1 {
        color: #FFFFFF !important;
        margin: 0 0 8px 0;
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -0.5px;
        position: relative;
        z-index: 1;
        font-family: var(--font-display);
    }
    .main-header p {
        color: rgba(225, 236, 255, 0.85) !important;
        margin: 0;
        font-size: 14px;
        font-weight: 500;
        position: relative;
        z-index: 1;
        letter-spacing: 0.1px;
    }
    .status-badge {
        background-color: rgba(251, 191, 36, 0.22);
        color: #FEF3C7;
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 700;
        display: inline-block;
        margin-top: 12px;
        letter-spacing: 0.8px;
        border: 1px solid rgba(251, 191, 36, 0.3);
        position: relative;
        z-index: 1;
    }

    /* ---- Card Box ---- */
    .card-box {
        background: var(--bg-card);
        border-radius: var(--radius-md);
        padding: 20px 22px;
        border: 1px solid var(--border);
        box-shadow: var(--shadow-sm);
        margin-bottom: 18px;
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    .card-box:hover {
        box-shadow: var(--shadow-md);
    }
    .month-badge {
        background: linear-gradient(135deg, var(--blue), var(--blue-bright));
        color: white;
        padding: 5px 12px;
        border-radius: 6px;
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .empty-banner {
        background: linear-gradient(135deg, #FFFBEB, #FEF3C7);
        border-left: 5px solid var(--gold);
        padding: 16px 22px;
        border-radius: var(--radius-sm);
        color: #92400E;
        margin-bottom: 22px;
        font-size: 14px;
        box-shadow: var(--shadow-sm);
    }
    /* ===== ELEGANT TABLE STYLING ===== */
    .stTable {
        font-size: 13px;
        border-collapse: separate;
        border-spacing: 0;
        width: 100%;
        border-radius: var(--radius-md);
        overflow: hidden;
        box-shadow: 0 4px 20px rgba(0, 43, 73, 0.08);
        border: 1px solid #E2E8F0;
    }
    .stTable thead tr th,
    [data-testid="stTable"] thead tr th,
    thead th {
        background: linear-gradient(135deg, #0A2540 0%, #00529C 55%, #0072CE 100%) !important;
        color: #FFFFFF !important;
        font-size: 10.5px !important;
        font-weight: 800 !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        padding: 14px 16px !important;
        border-bottom: 3px solid var(--gold) !important;
        white-space: nowrap;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .stTable tbody tr td,
    [data-testid="stTable"] tbody tr td,
    tbody td {
        padding: 11px 16px !important;
        font-size: 12.5px !important;
        color: var(--text-primary) !important;
        border-bottom: 1px solid #EDF2F7 !important;
        vertical-align: middle !important;
        transition: background 0.15s ease, transform 0.1s ease;
    }
    .stTable tbody tr:nth-child(odd) td,
    tbody tr:nth-child(odd) td {
        background: #FFFFFF !important;
    }
    .stTable tbody tr:nth-child(even) td,
    tbody tr:nth-child(even) td {
        background: #F5F9FF !important;
    }
    .stTable tbody tr:hover td,
    tbody tr:hover td {
        background: linear-gradient(90deg, #EFF6FF, #DBEAFE) !important;
        color: var(--navy) !important;
    }
    [data-testid="stDataFrame"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0, 43, 73, 0.08) !important;
        border: 1px solid #E2E8F0 !important;
    }
    [data-testid="stDataFrame"] th {
        background: linear-gradient(135deg, #0A2540 0%, #00529C 55%, #0072CE 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 10.5px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        padding: 13px 14px !important;
        border-bottom: 3px solid var(--gold) !important;
        white-space: nowrap;
    }
    [data-testid="stDataFrame"] td {
        font-size: 12.5px !important;
        padding: 10px 14px !important;
        border-bottom: 1px solid #EDF2F7 !important;
    }
    [data-testid="stDataFrame"] tbody tr:nth-child(even) {
        background: #F5F9FF !important;
    }
    [data-testid="stDataFrame"] tbody tr:hover {
        background: #EFF6FF !important;
    }
    [data-testid="stDataFrame"] [data-testid="stDataFrameRow"]:hover {
        background: #EFF6FF !important;
    }
    /* Scrollbar styling for tables */
    [data-testid="stDataFrame"] ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-track {
        background: #F1F5F9;
        border-radius: 4px;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb {
        background: #CBD5E1;
        border-radius: 4px;
    }
    [data-testid="stDataFrame"] ::-webkit-scrollbar-thumb:hover {
        background: #94A3B8;
    }
    /* Data editor styling */
    [data-testid="stDataEditor"] {
        border-radius: 12px !important;
        overflow: hidden !important;
        box-shadow: 0 4px 20px rgba(0, 43, 73, 0.08) !important;
        border: 1px solid #E2E8F0 !important;
    }
    [data-testid="stDataEditor"] th {
        background: linear-gradient(135deg, #0A2540 0%, #00529C 55%, #0072CE 100%) !important;
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 10.5px !important;
        letter-spacing: 1px !important;
        text-transform: uppercase !important;
        padding: 13px 14px !important;
        border-bottom: 3px solid var(--gold) !important;
    }

    /* ===== ELEGANT SIDEBAR / MENU STYLING ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #FFFFFF 0%, #F0F6FF 100%);
        border-right: 1px solid #CBD5E1;
        box-shadow: 2px 0 16px rgba(0, 43, 73, 0.07);
    }
    [data-testid="stSidebar"] .block-container {
        padding: 1.4rem 1rem 2.4rem 1rem;
    }
    .sidebar-brand {
        background: linear-gradient(145deg, var(--navy-deep) 0%, var(--blue) 100%);
        border-radius: var(--radius-md);
        padding: 22px 16px 18px 16px;
        color: #FFFFFF;
        box-shadow: 0 8px 24px rgba(0, 43, 73, 0.28);
        margin-bottom: 22px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .sidebar-brand::after {
        content: "";
        position: absolute;
        bottom: -30px;
        right: -30px;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(245, 158, 11, 0.18) 0%, transparent 70%);
        border-radius: 50%;
    }
    .sidebar-brand .brand-name {
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 3px;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
        font-family: var(--font-display);
    }
    .sidebar-brand .brand-subtitle {
        color: var(--gold-bright);
        font-size: 9.5px;
        font-weight: 800;
        letter-spacing: 2.5px;
        text-transform: uppercase;
        margin-top: 5px;
        opacity: 0.9;
    }
    .sidebar-section-label {
        color: #475569;
        font-size: 10.5px;
        font-weight: 800;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin: 26px 4px 12px 4px;
        padding: 0 4px 10px 4px;
        border-bottom: 2px solid #00529C;
        display: flex;
        align-items: center;
        gap: 6px;
        font-family: var(--font-display);
    }
    .sidebar-section-label::before {
        content: "";
        width: 4px;
        height: 4px;
        background: var(--gold);
        border-radius: 50%;
        display: inline-block;
    }
    .sidebar-session {
        background: #FFFFFF;
        border: 1px solid var(--border-light);
        border-left: 3px solid var(--blue-bright);
        border-radius: var(--radius-sm);
        padding: 13px 15px;
        color: var(--navy);
        font-size: 12.5px;
        line-height: 1.7;
        box-shadow: var(--shadow-sm);
        font-family: var(--font-sans);
    }
    .sidebar-session span {
        color: var(--text-muted);
        font-size: 10.5px;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    /* ===== SIDEBAR BRAND CARD (Logo + Live Pill) ===== */
    .sidebar-brand-card {
        background: linear-gradient(145deg, var(--navy-deep) 0%, var(--navy) 55%, var(--blue) 100%);
        border-radius: var(--radius-md);
        padding: 20px 16px 18px 16px;
        color: #FFFFFF;
        box-shadow: 0 8px 24px rgba(0, 43, 73, 0.28);
        margin-bottom: 20px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    .sidebar-brand-card::after {
        content: "";
        position: absolute;
        bottom: -30px;
        right: -30px;
        width: 100px;
        height: 100px;
        background: radial-gradient(circle, rgba(245, 158, 11, 0.18) 0%, transparent 70%);
        border-radius: 50%;
    }
    .sidebar-brand-logo {
        display: flex;
        justify-content: center;
        margin-bottom: 14px;
        position: relative;
        z-index: 1;
    }
    .sidebar-live-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: rgba(251, 191, 36, 0.18);
        border: 1px solid rgba(251, 191, 36, 0.3);
        color: #FEF3C7;
        font-size: 10px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        padding: 6px 14px;
        border-radius: 20px;
        position: relative;
        z-index: 1;
        font-family: var(--font-display);
    }
    .live-dot {
        width: 7px;
        height: 7px;
        background: #34D399;
        border-radius: 50%;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.5; transform: scale(0.85); }
    }

    /* ===== SIDEBAR PROFILE BOX ===== */
    .sidebar-profile-box {
        background: #FFFFFF;
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        padding: 16px;
        display: flex;
        align-items: center;
        gap: 12px;
        box-shadow: var(--shadow-sm);
        margin-bottom: 20px;
        font-family: var(--font-sans);
    }
    .profile-avatar {
        width: 46px;
        height: 46px;
        border-radius: 50%;
        background: linear-gradient(135deg, var(--blue), var(--blue-bright));
        color: #FFFFFF;
        font-size: 17px;
        font-weight: 800;
        display: flex;
        align-items: center;
        justify-content: center;
        flex-shrink: 0;
        box-shadow: 0 4px 12px rgba(0, 82, 156, 0.3);
        font-family: var(--font-display);
    }
    .profile-info {
        flex: 1;
        min-width: 0;
    }
    .profile-name {
        font-size: 14px;
        font-weight: 700;
        color: var(--navy);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        font-family: var(--font-display);
    }
    .profile-role-badge {
        display: inline-block;
        font-size: 10px;
        font-weight: 800;
        letter-spacing: 1px;
        padding: 4px 12px;
        border-radius: 12px;
        margin-top: 5px;
        text-transform: uppercase;
        font-family: var(--font-display);
    }
    .role-badge-admin {
        background: linear-gradient(135deg, #EF4444, #F97316);
        color: #FFFFFF;
    }
    .role-badge-user {
        background: linear-gradient(135deg, #3B82F6, #6366F1);
        color: #FFFFFF;
    }
    .role-badge-supervisor {
        background: linear-gradient(135deg, #10B981, #059669);
        color: #FFFFFF;
    }
    [data-testid="stSidebar"] [role="radiogroup"] {
        gap: 6px;
        display: flex;
        flex-direction: column;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label {
        border-radius: 10px !important;
        padding: 12px 16px !important;
        color: var(--text-secondary) !important;
        transition: all 0.25s ease !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        border: 1px solid #E2E8F0 !important;
        background: #FFFFFF !important;
        box-shadow: 0 2px 6px rgba(0, 0, 0, 0.04) !important;
        margin-bottom: 3px !important;
        position: relative;
        font-family: var(--font-sans);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:hover {
        background: linear-gradient(90deg, #F0F7FF, #E8F1FF) !important;
        color: var(--blue) !important;
        border-color: #93C5FD !important;
        transform: translateX(4px);
        box-shadow: 0 4px 12px rgba(0, 82, 156, 0.15) !important;
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
        background: linear-gradient(135deg, #0A2540 0%, #00529C 100%) !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: 1px solid #00529C !important;
        box-shadow: 0 4px 16px rgba(0, 82, 156, 0.3) !important;
        transform: translateX(2px);
    }
    [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked)::after {
        content: "▸";
        position: absolute;
        right: 12px;
        top: 50%;
        transform: translateY(-50%);
        color: var(--gold-bright);
        font-size: 12px;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        background: #FFFFFF;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
        margin-bottom: 6px;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary {
        font-weight: 700;
        color: var(--navy);
        font-size: 13px;
        padding: 4px 2px;
        font-family: var(--font-display);
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
        color: var(--blue);
    }
    [data-testid="stSidebar"] .stSelectbox > div > div {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
    }
    [data-testid="stSidebar"] .stSelectbox > div > div:hover {
        border-color: #93C5FD;
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        font-size: 12.5px;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
        color: var(--navy);
        transition: all 0.2s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: #F0F7FF;
        border-color: #93C5FD;
        color: var(--blue);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0, 82, 156, 0.12);
    }
    [data-testid="stSidebar"] .stMultiselect > div > div {
        border-radius: 8px;
        border: 1px solid #E2E8F0;
        background: #FFFFFF;
    }
    [data-testid="stSidebar"] .stMultiselect > div > div:hover {
        border-color: #93C5FD;
    }
    .access-hero {
        background: linear-gradient(135deg, var(--navy-deep), var(--blue));
        border-radius: var(--radius-md);
        padding: 24px 28px;
        color: #FFFFFF;
        margin-bottom: 24px;
        box-shadow: var(--shadow-lg);
        position: relative;
        overflow: hidden;
        font-family: var(--font-display);
    }
    .access-hero::before {
        content: "";
        position: absolute;
        top: -50px;
        right: -50px;
        width: 160px;
        height: 160px;
        background: radial-gradient(circle, rgba(251, 191, 36, 0.12) 0%, rgba(251, 191, 36, 0) 70%);
        border-radius: 50%;
    }
    .access-hero h1 {
        color: #FFFFFF !important;
        font-size: 28px;
        font-weight: 800;
        margin: 0;
        letter-spacing: -0.4px;
        position: relative;
        z-index: 1;
        font-family: var(--font-display);
    }
    .access-hero p {
        color: rgba(225, 236, 255, 0.88) !important;
        font-size: 14px;
        margin: 10px 0 0 0;
        position: relative;
        z-index: 1;
        font-weight: 500;
    }
    .access-role-card {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-left: 4px solid var(--gold);
        border-radius: var(--radius-sm);
        padding: 16px 20px;
        margin: 16px 0 20px 0;
        color: var(--text-secondary);
        font-size: 13px;
        box-shadow: var(--shadow-sm);
        font-family: var(--font-sans);
        line-height: 1.7;
    }
    .acs-summary-card {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-top: 4px solid var(--gold);
        border-radius: var(--radius-sm);
        padding: 20px 21px 19px 21px;
        min-height: 136px;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
        font-family: var(--font-sans);
    }
    .acs-summary-card:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    .acs-summary-month {
        color: var(--text-muted);
        font-size: 11.5px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        font-family: var(--font-display);
    }
    .acs-summary-label {
        color: var(--text-muted);
        font-size: 11px;
        margin-top: 20px;
        font-weight: 600;
        letter-spacing: 0.3px;
    }
    .acs-summary-value {
        color: #047857;
        font-size: 24px;
        font-weight: 800;
        line-height: 1.2;
        margin-top: 5px;
        overflow-wrap: anywhere;
        font-family: var(--font-display);
    }
    .acs-summary-meta {
        color: var(--text-muted);
        font-size: 10.5px;
        margin-top: 10px;
        font-weight: 500;
    }
    .access-matrix {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        padding: 20px 22px 14px 22px;
        box-shadow: var(--shadow-sm);
        font-family: var(--font-sans);
    }
    .st-key-access_matrix {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        padding: 20px 22px 16px 22px;
        box-shadow: var(--shadow-sm);
        font-family: var(--font-sans);
    }
    .access-header {
        color: var(--text-muted);
        font-size: 11px;
        font-weight: 800;
        letter-spacing: 1px;
        text-transform: uppercase;
        padding-bottom: 12px;
        border-bottom: 1px solid var(--border);
        font-family: var(--font-display);
    }
    .access-module {
        color: var(--navy);
        font-size: 13.5px;
        font-weight: 700;
        padding-top: 14px;
        font-family: var(--font-display);
    }

    /* ---- Streamlit Global Enhancements ---- */
    .stMetric {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        padding: 18px 20px;
        box-shadow: var(--shadow-sm);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
        font-family: var(--font-sans);
    }
    .stMetric:hover {
        box-shadow: var(--shadow-md);
        transform: translateY(-2px);
    }
    .stMetric > div > div > div[data-testid="stMetricLabel"] {
        color: var(--text-muted) !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.8px !important;
        text-transform: uppercase !important;
        font-family: var(--font-display);
    }
    .stMetric > div > div > div[data-testid="stMetricValue"] {
        color: var(--navy) !important;
        font-size: 26px !important;
        font-weight: 800 !important;
        font-family: var(--font-display);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 4px;
        background: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: var(--radius-sm) var(--radius-sm) 0 0;
        padding: 12px 20px;
        font-weight: 700;
        color: var(--text-secondary);
        transition: background-color 0.2s ease, color 0.2s ease;
        font-size: 13px;
        font-family: var(--font-display);
    }
    .stTabs [aria-selected="true"] {
        background: var(--blue);
        color: #FFFFFF !important;
    }
    .stExpander {
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        background: var(--bg-card);
        box-shadow: var(--shadow-sm);
    }
    .stExpander > summary {
        font-weight: 700;
        color: var(--navy);
        font-size: 14px;
        font-family: var(--font-display);
    }
    .stButton > button {
        border-radius: var(--radius-sm);
        font-weight: 700;
        letter-spacing: 0.3px;
        transition: transform 0.15s ease, box-shadow 0.15s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
    }
    .stButton[kind="secondary"] > button {
        background: #FFFFFF;
        border: 1.5px solid var(--border-light);
        color: var(--navy);
    }
    .stButton[kind="secondary"] > button:hover {
        background: #F1F5F9;
        border-color: var(--blue);
    }
    .stAlert {
        border-radius: var(--radius-sm);
        box-shadow: var(--shadow-sm);
    }
    .stSuccess {
        background: #ECFDF5;
        border: 1px solid #A7F3D0;
        border-radius: var(--radius-sm);
    }
    .stWarning {
        background: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: var(--radius-sm);
    }
    .stError {
        background: #FEF2F2;
        border: 1px solid #FECACA;
        border-radius: var(--radius-sm);
    }
    .stInfo {
        background: #EFF6FF;
        border: 1px solid #BFDBFE;
        border-radius: var(--radius-sm);
    }
    .stForm {
        background: var(--bg-card);
        border: 1px solid var(--border-light);
        border-radius: var(--radius-md);
        padding: 22px 24px;
        box-shadow: var(--shadow-sm);
    }
    .stSelectbox > div > div,
    .stMultiselect > div > div {
        border-radius: var(--radius-sm);
    }
    .stDateInput > div > div {
        border-radius: var(--radius-sm);
    }
    .stFileUploader {
        border: 2px dashed var(--border-light);
        border-radius: var(--radius-md);
        padding: 18px;
        background: #FAFBFC;
        transition: border-color 0.2s ease, background 0.2s ease;
    }
    .stFileUploader:hover {
        border-color: var(--blue);
        background: #F0F7FF;
    }
</style>
""", unsafe_allow_html=True)

# Login sederhana untuk aplikasi internal. Ganti kredensial ini sebelum deployment.
AUTH_USERS = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"},
    "supervisor": {"password": "supervisor123", "role": "supervisor"},
}

if "auth_users" not in st.session_state:
    st.session_state.auth_users = {username: account.copy() for username, account in AUTH_USERS.items()}
if "login_activity" not in st.session_state:
    st.session_state.login_activity = []

ACCESS_ACTIONS = ["Baca", "Tambah", "Edit", "Delete"]
ACCESS_MODULES = [
    "Dashboard Executive Overview",
    "BCA",
    "ATMI",
    "Tabel Utama",
    "Multi-Staff Operasional",
    "Close / Open Cencon",
    "UK TC, UK BDC & UK Siclus",
    "Laporan EBOS",
    "Rekon EJ",
    "Rekon Sislok",
    "Uang Kolong",
    "Galeri Foto Bukti",
    "Kelola Data (CRUD)",
    "Input & Tambah Data",
    "Ekspor & Impor Data Excel",
]

def create_default_permissions():
    permissions = {
        "admin": {module: {action: True for action in ACCESS_ACTIONS} for module in ACCESS_MODULES},
        "user": {module: {action: action == "Baca" for action in ACCESS_ACTIONS} for module in ACCESS_MODULES},
        "supervisor": {module: {action: True for action in ACCESS_ACTIONS} for module in ACCESS_MODULES},
    }
    return permissions

if "role_permissions" not in st.session_state:
    st.session_state.role_permissions = create_default_permissions()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = ""
if "role" not in st.session_state:
    st.session_state.role = ""

# Auto-restore session from URL query parameters on browser refresh (F5)
cached_user = get_query_param("user")
if cached_user and not st.session_state.authenticated:
    norm_cached_user = str(cached_user).strip().lower()
    if norm_cached_user in st.session_state.auth_users:
        st.session_state.authenticated = True
        st.session_state.username = norm_cached_user
        st.session_state.role = st.session_state.auth_users[norm_cached_user]["role"]

if not st.session_state.authenticated:
    # Dedicated Executive Corporate Login Styles
    st.markdown("""
    <style>
        /* Sembunyikan sidebar dan tombol collapse saat belum login */
        [data-testid="stSidebar"],
        [data-testid="collapsedControl"],
        section[data-testid="stSidebar"] {
            display: none !important;
        }

        /* Header transparan */
        header[data-testid="stHeader"] {
            background: transparent !important;
        }

        /* Latar belakang halaman login: Deep Navy Banking Mesh */
        .stApp {
            background: radial-gradient(ellipse at 50% 12%, #162E50 0%, #0B1B30 48%, #050D1A 100%) !important;
            min-height: 100vh;
        }

        /* Container login di tengah layar */
        .block-container {
            max-width: 1040px !important;
            padding-top: 3.2rem !important;
            padding-bottom: 2.8rem !important;
            padding-left: 1.5rem !important;
            padding-right: 1.5rem !important;
            margin: 0 auto !important;
        }

        /* Kartu Kiri: Brand & Info Sistem */
        .login-brand-wrapper {
            background: linear-gradient(155deg, #071936 0%, #002B49 48%, #004D8C 100%);
            border: 1px solid rgba(255, 255, 255, 0.14);
            border-radius: 22px;
            padding: 38px 34px;
            color: #FFFFFF;
            box-shadow: 0 24px 55px -12px rgba(0, 10, 25, 0.7);
            position: relative;
            overflow: hidden;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }

        .login-brand-wrapper::before {
            content: "";
            position: absolute;
            top: -85px;
            right: -85px;
            width: 240px;
            height: 240px;
            background: radial-gradient(circle, rgba(251, 191, 36, 0.18) 0%, rgba(251, 191, 36, 0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .login-brand-wrapper::after {
            content: "";
            position: absolute;
            bottom: -80px;
            left: -80px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(0, 114, 206, 0.22) 0%, rgba(0, 114, 206, 0) 70%);
            border-radius: 50%;
            pointer-events: none;
        }

        .brand-badge-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(251, 191, 36, 0.14);
            border: 1px solid rgba(251, 191, 36, 0.35);
            color: #FDE68A;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 10.5px;
            font-weight: 700;
            letter-spacing: 1.2px;
            text-transform: uppercase;
            margin-top: 14px;
            margin-bottom: 18px;
            width: fit-content;
        }

        .badge-dot-glow {
            width: 7px;
            height: 7px;
            background-color: #FBBF24;
            border-radius: 50%;
            box-shadow: 0 0 8px #FBBF24;
        }

        .brand-title-hero {
            font-size: 29px;
            font-weight: 800;
            line-height: 1.25;
            color: #FFFFFF;
            margin: 0 0 10px 0;
            letter-spacing: -0.4px;
        }

        .brand-gold-gradient {
            background: linear-gradient(135deg, #FDE68A 0%, #F59E0B 50%, #D97706 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        .brand-subtext {
            color: rgba(226, 238, 255, 0.85);
            font-size: 13px;
            line-height: 1.6;
            margin-bottom: 22px;
        }

        .features-pill-group {
            display: flex;
            flex-direction: column;
            gap: 10px;
            margin-bottom: 22px;
        }

        .feature-pill {
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(255, 255, 255, 0.06);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 9px 12px;
            border-radius: 11px;
            backdrop-filter: blur(6px);
        }

        .feature-icon-box {
            width: 28px;
            height: 28px;
            border-radius: 7px;
            background: rgba(251, 191, 36, 0.16);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 13px;
            flex-shrink: 0;
        }

        .feature-info b {
            color: #FFFFFF;
            font-size: 12px;
            display: block;
        }

        .feature-info span {
            color: rgba(226, 238, 255, 0.72);
            font-size: 10.5px;
        }

        .brand-meta-footer {
            border-top: 1px solid rgba(255, 255, 255, 0.12);
            padding-top: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            color: rgba(226, 238, 255, 0.65);
            font-size: 11px;
            font-weight: 500;
        }

        /* Kartu Kanan: Form Login */
        .st-key-login_form_card {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 22px !important;
            padding: 36px 34px 28px 34px !important;
            box-shadow: 0 24px 55px -12px rgba(0, 10, 25, 0.5) !important;
            height: 100% !important;
        }

        /* Reset border dan background stForm di kartu login */
        .st-key-login_form_card div[data-testid="stForm"],
        .st-key-login_form_card .stForm {
            border: none !important;
            padding: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            margin: 0 !important;
        }

        .form-top-header {
            display: flex;
            align-items: center;
            gap: 14px;
            margin-bottom: 20px;
        }

        .form-icon-emblem {
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: linear-gradient(135deg, #002B49, #00529C);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            box-shadow: 0 8px 18px rgba(0, 82, 156, 0.28);
            flex-shrink: 0;
        }

        .form-headline {
            font-size: 22px;
            font-weight: 800;
            color: #0F172A;
            margin: 0;
            letter-spacing: -0.4px;
        }

        .form-subhead {
            font-size: 12.5px;
            color: #64748B;
            margin-top: 3px;
        }

        /* Input Form */
        .st-key-login_form_card .stTextInput label {
            font-size: 12.5px !important;
            font-weight: 700 !important;
            color: #1E293B !important;
            margin-bottom: 4px !important;
        }

        .st-key-login_form_card .stTextInput input {
            background: #F8FAFC !important;
            border: 1.5px solid #CBD5E1 !important;
            border-radius: 10px !important;
            padding: 11px 14px !important;
            font-size: 13.5px !important;
            color: #0F172A !important;
            transition: all 0.2s ease !important;
        }

        .st-key-login_form_card .stTextInput input:focus {
            background: #FFFFFF !important;
            border-color: #00529C !important;
            box-shadow: 0 0 0 3.5px rgba(0, 82, 156, 0.15) !important;
            outline: none !important;
        }

        /* Tombol Submit Login */
        .st-key-login_form_card div[data-testid="stFormSubmitButton"] > button {
            background: linear-gradient(135deg, #002B49 0%, #00529C 100%) !important;
            color: #FFFFFF !important;
            font-weight: 700 !important;
            font-size: 14px !important;
            border-radius: 11px !important;
            border: 1px solid rgba(255, 255, 255, 0.15) !important;
            padding: 13px 20px !important;
            box-shadow: 0 8px 20px rgba(0, 43, 73, 0.25) !important;
            transition: all 0.2s ease !important;
            letter-spacing: 0.3px !important;
            margin-top: 8px !important;
        }

        .st-key-login_form_card div[data-testid="stFormSubmitButton"] > button:hover {
            background: linear-gradient(135deg, #001F3F 0%, #004080 100%) !important;
            box-shadow: 0 12px 26px rgba(0, 43, 73, 0.35) !important;
            transform: translateY(-2px) !important;
        }

        /* Divider Demo */
        .login-divider-line {
            display: flex;
            align-items: center;
            gap: 12px;
            margin: 20px 0 14px 0;
            color: #94A3B8;
            font-size: 10px;
            font-weight: 800;
            letter-spacing: 1.2px;
            text-transform: uppercase;
        }

        .login-divider-line::before,
        .login-divider-line::after {
            content: "";
            flex: 1;
            height: 1px;
            background: #E2E8F0;
        }

        /* Kartu Demo Grid */
        .demo-roles-container {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-bottom: 14px;
        }

        .demo-card-item {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 8px;
            text-align: center;
            transition: all 0.2s ease;
        }

        .demo-card-item:hover {
            border-color: #CBD5E1;
            background: #F1F5F9;
        }

        .role-tag {
            font-size: 9px;
            font-weight: 800;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
            margin-bottom: 4px;
        }

        .role-tag-admin { background: #FEE2E2; color: #991B1B; }
        .role-tag-spv { background: #FEF3C7; color: #92400E; }
        .role-tag-user { background: #E0F2FE; color: #075985; }

        .demo-user-name {
            font-size: 11.5px;
            font-weight: 700;
            color: #0F172A;
            line-height: 1.2;
        }

        .demo-user-pwd {
            font-size: 10px;
            color: #64748B;
            margin-top: 2px;
        }

        .login-footer-info {
            text-align: center;
            color: #94A3B8;
            font-size: 10.5px;
            line-height: 1.4;
        }

        @media (max-width: 820px) {
            .block-container {
                padding-top: 1.5rem !important;
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
            .brand-title-hero {
                font-size: 24px;
            }
            .st-key-login_form_card {
                padding: 26px 20px !important;
            }
            .login-brand-wrapper {
                padding: 28px 22px;
            }
            .demo-roles-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
    """, unsafe_allow_html=True)

    logo_svg = get_abacus_logo_html(width=220, height=54)
    login_brand_col, login_form_col = st.columns([1.1, 0.9], gap="medium")

    with login_brand_col:
        st.markdown(f"""
        <div class="login-brand-wrapper">
            <div>
                <div>{logo_svg}</div>
                <div class="brand-badge-pill">
                    <span class="badge-dot-glow"></span>
                    <span>SISTEM REKONSILIASI BCA MALANG</span>
                </div>
                <h1 class="brand-title-hero">
                    Akurasi Kas &<br><span class="brand-gold-gradient">Audit Terpadu</span>
                </h1>
                <p class="brand-subtext">
                    Platform rekonsiliasi kas terintegrasi untuk monitoring selisih ATM & CRM, pengelolaan kaset sislok, UK BDC, dan otomatisasi laporan operasional BCA.
                </p>
                <div class="features-pill-group">
                    <div class="feature-pill">
                        <div class="feature-icon-box">⚡</div>
                        <div class="feature-info">
                            <b>Auto-Append & Matching Instan</b>
                            <span>Pencocokan transaksi ATM/CRM dengan fisik cepat & akurat</span>
                        </div>
                    </div>
                    <div class="feature-pill">
                        <div class="feature-icon-box">🛡️</div>
                        <div class="feature-info">
                            <b>Audit Trail & Pelacakan Petugas</b>
                            <span>Pencatatan multi-staff, driver, dan validasi selisih harian</span>
                        </div>
                    </div>
                    <div class="feature-pill">
                        <div class="feature-icon-box">📊</div>
                        <div class="feature-info">
                            <b>Laporan Eksekutif & EBOS</b>
                            <span>Rekapitulasi otomatis, visualisasi tren & ekspor Excel rapi</span>
                        </div>
                    </div>
                </div>
            </div>
            <div class="brand-meta-footer">
                <span>🔒 256-Bit SSL Sesi Terenkripsi</span>
                <span>Abacus Cash Solution v2.9</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with login_form_col:
        with st.container(key="login_form_card"):
            st.markdown("""
            <div class="form-top-header">
                <div class="form-icon-emblem">🔐</div>
                <div>
                    <h2 class="form-headline">Masuk ke Sistem</h2>
                    <div class="form-subhead">Masukkan kredensial Anda untuk mengakses portal</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.form("login_form"):
                login_username = st.text_input("Username / ID Petugas", placeholder="Contoh: admin / user")
                login_password = st.text_input("Password", type="password", placeholder="Masukkan password")
                login_submit = st.form_submit_button("Masuk ke Sistem ➔", type="primary", use_container_width=True)

                if login_submit:
                    account = st.session_state.auth_users.get(login_username.strip().lower())
                    if account and account["password"] == login_password:
                        st.session_state.login_activity.append({
                            "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                            "Waktu": datetime.now().strftime("%H:%M:%S"),
                            "Username": login_username.strip().lower(),
                            "Role": account["role"].title(),
                            "Status": "Berhasil",
                        })
                        st.session_state.authenticated = True
                        st.session_state.username = login_username.strip().lower()
                        st.session_state.role = account["role"]
                        set_query_param("user", login_username.strip().lower())
                        safe_rerun()
                    else:
                        failed_account = st.session_state.auth_users.get(login_username.strip().lower())
                        st.session_state.login_activity.append({
                            "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                            "Waktu": datetime.now().strftime("%H:%M:%S"),
                            "Username": login_username.strip().lower() or "(kosong)",
                            "Role": failed_account["role"].title() if failed_account else "-",
                            "Status": "Gagal",
                        })
                        st.error("⚠️ Username atau password tidak valid.")

            st.markdown("""
            <div class="login-divider-line">Akses Cepat Demo</div>
            <div class="demo-roles-container">
                <div class="demo-card-item">
                    <span class="role-tag role-tag-admin">Admin</span>
                    <div class="demo-user-name">admin</div>
                    <div class="demo-user-pwd">admin123</div>
                </div>
                <div class="demo-card-item">
                    <span class="role-tag role-tag-spv">Supervisor</span>
                    <div class="demo-user-name">supervisor</div>
                    <div class="demo-user-pwd">supervisor123</div>
                </div>
                <div class="demo-card-item">
                    <span class="role-tag role-tag-user">Operator</span>
                    <div class="demo-user-name">user</div>
                    <div class="demo-user-pwd">user123</div>
                </div>
            </div>
            <div class="login-footer-info">
                Gunakan kredensial resmi untuk akses operasional. Hubungi administrator bila lupa kata sandi.
            </div>
            """, unsafe_allow_html=True)

    st.stop()

current_role = st.session_state.role
role_permissions = st.session_state.role_permissions

def has_permission(module, action):
    if current_role == "supervisor":
        return True
    return role_permissions.get(current_role, {}).get(module, {}).get(action, False)

can_manage_data = any(has_permission("Tabel Utama", action) for action in ["Tambah", "Edit", "Delete"])
can_add_data = has_permission("Input & Tambah Data", "Tambah")
can_edit_main = has_permission("Tabel Utama", "Edit")
can_add_main = has_permission("Tabel Utama", "Tambah")
can_delete_main = has_permission("Tabel Utama", "Delete")
can_manage_staff = any(has_permission("Multi-Staff Operasional", action) for action in ["Tambah", "Edit", "Delete"])
can_upload_photo = has_permission("Galeri Foto Bukti", "Tambah")
is_supervisor = current_role == "supervisor"

# ---------------------------------------------------------
# Empty Dataframe Creators & Default Loaders
# ---------------------------------------------------------
def create_empty_rekon():
    cols = ["WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_ABACUS"]
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
            "WSID": "Z5UM", "LOK": "ABACUS", "LOKASI": "PURWOSARI CRM 2", "Mesin": "O-CRM",
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
            "TANGGAPAN_ABACUS": "Selisih Awal : -600\nUK : 500\nSelisih Akhir : -100"
        },
        {
            "WSID": "Z5UM", "LOK": "ABACUS", "LOKASI": "CRM PURWOSARI 2", "Mesin": "O-CRM",
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
            "TANGGAPAN_ABACUS": "Tes cash ok"
        },
        {
            "WSID": "Z5UM", "LOK": "ABACUS", "LOKASI": "CRM PURWOSARI 2", "Mesin": "O-CRM",
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
            "TANGGAPAN_ABACUS": "Selesai audit"
        },
        {
            "WSID": "Z5UM", "LOK": "ABACUS", "LOKASI": "CRM PURWOSARI 2", "Mesin": "O-CRM",
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
            "TANGGAPAN_ABACUS": "Penyelesaian bongkar isi"
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
            "TANGGAPAN_ABACUS": "Selisih Awal : -3,350\nUK : 3,350\nKeluhan Nsb : -100 tgl 25/06 jam 13:20\nSelisih Akhir : -100"
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
            "TANGGAPAN_ABACUS": "Selisih Awal : -50\nSelisih Akhir : -50"
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

data_keys = [
    "df_rekon", "df_cencon", "df_uk", "df_ebos", "df_ej", "df_sislok", "df_kolong", "image_store"
]
cached_state = load_persistent_state()
if "data_scopes" not in st.session_state:
    if cached_state and "data_scopes" in cached_state and isinstance(cached_state["data_scopes"], dict):
        st.session_state.data_scopes = cached_state["data_scopes"]
        if "active_scope" in cached_state and cached_state["active_scope"]:
            st.session_state.active_data_scope = cached_state["active_scope"]
        cur_sc = st.session_state.get("active_data_scope", "BCA")
        for k in data_keys:
            if k in st.session_state.data_scopes.get(cur_sc, {}):
                st.session_state[k] = st.session_state.data_scopes[cur_sc][k]
    else:
        st.session_state.data_scopes = {
            "BCA": {key: st.session_state[key].copy() if hasattr(st.session_state[key], "copy") else dict(st.session_state[key]) for key in data_keys},
            "ATMI": {
                "df_rekon": create_empty_rekon(),
                "df_cencon": create_empty_cencon(),
                "df_uk": create_empty_uk(),
                "df_ebos": create_empty_ebos(),
                "df_ej": create_empty_ej(),
                "df_sislok": create_empty_sislok(),
                "df_kolong": create_empty_kolong(),
                "image_store": {},
            },
        }

if "active_data_scope" not in st.session_state:
    q_sc = get_query_param("scope")
    st.session_state.active_data_scope = q_sc if q_sc in ["BCA", "ATMI"] else "BCA"

cur_sc = st.session_state.active_data_scope
if cur_sc in st.session_state.data_scopes:
    for k in data_keys:
        if k in st.session_state.data_scopes[cur_sc]:
            st.session_state[k] = st.session_state.data_scopes[cur_sc][k]

if "export_columns_by_scope" not in st.session_state:
    st.session_state.export_columns_by_scope = {
        "BCA": list(st.session_state.df_rekon.columns),
        "ATMI": [],
    }

# Restore navigation from URL query params on page refresh
q_menu = get_query_param("menu")
q_group = get_query_param("group")
if q_group and "menu_group" not in st.session_state:
    st.session_state["menu_group"] = q_group
if q_menu and "nav_menu" not in st.session_state:
    st.session_state["nav_menu"] = q_menu

if "target_nav_menu" in st.session_state and st.session_state.target_nav_menu:
    st.session_state["nav_menu"] = st.session_state.target_nav_menu
    st.session_state.target_nav_menu = None
elif "nav_menu" not in st.session_state:
    st.session_state["nav_menu"] = "📋 Tabel Utama (Complete Audit)"

# Standardize Columns Security Check
def sanitize_df(df, required_cols):
    if df.empty:
        return pd.DataFrame(columns=required_cols)
    # Auto map TANGGAPAN_BCA to TANGGAPAN_ABACUS if present
    if "TANGGAPAN_BCA" in df.columns and "TANGGAPAN_ABACUS" not in df.columns:
        df.rename(columns={"TANGGAPAN_BCA": "TANGGAPAN_ABACUS"}, inplace=True)
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

    remove_dates = get_remove_date_series(df)
    if remove_dates.eq("-").all() and date_col in df.columns:
        remove_dates = df[date_col]
    df["BULAN"] = month_from_remove_date(remove_dates)
    return df

df_rekon = sanitize_df(st.session_state.df_rekon, [
    "WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", 
    "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", 
    "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", "STAFF_LAINNYA", 
    "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_ABACUS"
])

df_rekon = auto_fill_bulan(df_rekon, "TGL_REM")
df_rekon = remove_duplicate_rekon_rows(df_rekon)
st.session_state.df_rekon = df_rekon
st.session_state.data_scopes[st.session_state.active_data_scope]["df_rekon"] = df_rekon.copy()
save_persistent_state(st.session_state.data_scopes, st.session_state.active_data_scope)

# ---------------------------------------------------------
# Sidebar Navigation & Global Filters
# ---------------------------------------------------------
abacus_logo_sidebar = get_abacus_logo_html(width=190, height=46)
role_pill_class = f"role-badge-{current_role.lower()}"
user_initial = (st.session_state.username[:2] if st.session_state.username else "US").upper()

st.sidebar.markdown(f"""
<div class="sidebar-brand-card">
    <div class="sidebar-brand-logo">{abacus_logo_sidebar}</div>
    <div class="sidebar-live-pill">
        <span class="live-dot"></span>
        <span>SISTEM AKTIF • BCA MALANG</span>
    </div>
</div>
<div class="sidebar-profile-box">
    <div class="profile-avatar">{user_initial}</div>
    <div class="profile-info">
        <div class="profile-name">{st.session_state.username.title()}</div>
        <span class="profile-role-badge {role_pill_class}">{current_role.upper()}</span>
    </div>
</div>
""", unsafe_allow_html=True)
if st.sidebar.button("🚪 Logout Sesi", use_container_width=True):
    clear_query_params()
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.role = ""
    safe_rerun()

menu_options = [
    "📊 Dashboard Executive Overview",
    "🏢 ATMI",
    "📁 Ekspor & Impor Data Excel"
]
if is_supervisor:
    menu_options.insert(-1, "🔐 Hak Akses")
    menu_options.insert(-1, "🕘 Aktivitas Login")

menu_module_map = {
    "📊 Dashboard Executive Overview": "Dashboard Executive Overview",
    "🏦 BCA": "BCA",
    "🏢 ATMI": "ATMI",
    "📋 Tabel Utama (Complete Audit)": "Tabel Utama",
    "👥 Multi-Staff Operasional per WSID": "Multi-Staff Operasional",
    "💵 Close / Open Cencon & Tes Cash": "Close / Open Cencon",
    "🔄 UK TC, UK BDC & UK Siclus": "UK TC, UK BDC & UK Siclus",
    "📑 Laporan EBOS": "Laporan EBOS",
    "💻 Rekon EJ (Electronic Journal)": "Rekon EJ",
    "📦 Rekon Sislok & Review Stock": "Rekon Sislok",
    "🪙 Uang Kolong & Temuan Fisik": "Uang Kolong",
    "📸 Unggah & Galeri Foto Bukti": "Galeri Foto Bukti",
    "🛠️ Kelola Data (CRUD Operations)": "Kelola Data (CRUD)",
    "➕ Input & Tambah Data Terpadu": "Input & Tambah Data",
    "📁 Ekspor & Impor Data Excel": "Ekspor & Impor Data Excel",
    "🕘 Aktivitas Login": "Aktivitas Login",
}
if not is_supervisor:
    menu_options = [option for option in menu_options if has_permission(menu_module_map.get(option, ""), "Baca")]

operational_menu_options = [
    "📋 Tabel Utama (Complete Audit)",
    "👥 Multi-Staff Operasional per WSID",
    "💵 Close / Open Cencon & Tes Cash",
    "🔄 UK TC, UK BDC & UK Siclus",
    "📑 Laporan EBOS",
    "💻 Rekon EJ (Electronic Journal)",
    "📦 Rekon Sislok & Review Stock",
    "🪙 Uang Kolong & Temuan Fisik",
    "📸 Unggah & Galeri Foto Bukti",
]
if can_manage_data:
    operational_menu_options.append("🛠️ Kelola Data (CRUD Operations)")
if can_add_data:
    operational_menu_options.append("➕ Input & Tambah Data Terpadu")
if not is_supervisor:
    operational_menu_options = [option for option in operational_menu_options if has_permission(menu_module_map[option], "Baca")]

saved_menu = st.session_state.get("nav_menu")
top_menu_options = ["📊 Dashboard Executive Overview", "🏢 ATMI", "📁 Ekspor & Impor Data Excel"]
if is_supervisor:
    top_menu_options.append("🔐 Hak Akses")
    top_menu_options.append("🕘 Aktivitas Login")
if not is_supervisor:
    top_menu_options = [option for option in top_menu_options if has_permission(menu_module_map[option], "Baca")]
top_menu_options = ["🏦 BCA", "🏢 ATMI"] + [option for option in top_menu_options if option != "🏢 ATMI"]

st.sidebar.markdown('<div class="sidebar-section-label">Menu</div>', unsafe_allow_html=True)
saved_group = st.session_state.get("menu_group")
default_top_menu = saved_group if saved_group in top_menu_options else ("🏦 BCA" if saved_menu in operational_menu_options else saved_menu)
if default_top_menu not in top_menu_options:
    default_top_menu = top_menu_options[0]

selected_top_menu = st.sidebar.radio(
    "Menu utama",
    top_menu_options,
    index=top_menu_options.index(default_top_menu),
    key="top_menu"
)
if selected_top_menu in ["🏦 BCA", "🏢 ATMI"] and operational_menu_options:
    submenu_key = "bca_submenu" if selected_top_menu == "🏦 BCA" else "atmi_submenu"
    submenu_label = "Pilih menu BCA" if selected_top_menu == "🏦 BCA" else "Pilih menu ATMI"
    with st.sidebar.expander(selected_top_menu, expanded=True):
        selected_operational_menu = st.selectbox(
            submenu_label,
            operational_menu_options,
            index=operational_menu_options.index(saved_menu) if saved_menu in operational_menu_options else 0,
            label_visibility="collapsed",
            key=submenu_key
        )
else:
    selected_operational_menu = None
menu = selected_operational_menu if selected_top_menu in ["🏦 BCA", "🏢 ATMI"] and selected_operational_menu else selected_top_menu
st.session_state["menu_group"] = selected_top_menu
st.session_state["nav_menu"] = menu
# Persist menu selection to URL query params so it survives browser refresh (F5)
set_query_param("menu", menu)
set_query_param("group", selected_top_menu)

scope_by_menu = {"🏦 BCA": "BCA", "🏢 ATMI": "ATMI"}
requested_data_scope = scope_by_menu.get(selected_top_menu, st.session_state.active_data_scope)
if requested_data_scope != st.session_state.active_data_scope:
    st.session_state.data_scopes[st.session_state.active_data_scope] = {
        key: st.session_state[key].copy() if hasattr(st.session_state[key], "copy") else dict(st.session_state[key])
        for key in data_keys
    }
    for key in data_keys:
        stored_value = st.session_state.data_scopes[requested_data_scope][key]
        st.session_state[key] = stored_value.copy() if hasattr(stored_value, "copy") else dict(stored_value)
    st.session_state.active_data_scope = requested_data_scope
    safe_rerun()

active_data_scope = st.session_state.active_data_scope
st.sidebar.markdown('<div class="sidebar-section-label">Status Data</div>', unsafe_allow_html=True)
col_sb1, col_sb2 = st.sidebar.columns(2)
with col_sb1:
    if can_manage_data and st.sidebar.button("🗑️ Kosongkan Data", use_container_width=True):
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
    if can_manage_data and st.sidebar.button("🔄 Muat Default", use_container_width=True):
        st.session_state.df_rekon = load_default_rekon()
        st.sidebar.success("Data sampel default berhasil dimuat!")
        safe_rerun()

st.sidebar.markdown('<div class="sidebar-section-label">Filter Laporan</div>', unsafe_allow_html=True)

all_mesin = df_rekon["Mesin"].unique().tolist() if "Mesin" in df_rekon.columns and not df_rekon.empty else ["O-CRM", "ITM", "CRMHYO", "ACH"]
all_lok = df_rekon["LOK"].unique().tolist() if "LOK" in df_rekon.columns and not df_rekon.empty else ["ABACUS", "T"]
if active_data_scope == "ATMI" and not df_rekon.empty:
    atmi_remove_month = month_from_remove_date(get_remove_date_series(df_rekon))
    all_bulan = sorted(atmi_remove_month.unique().tolist(), key=month_sort_key)
else:
    atmi_remove_month = pd.Series(index=df_rekon.index, dtype="object")
    all_bulan = sorted(df_rekon["BULAN"].unique().tolist(), key=month_sort_key) if "BULAN" in df_rekon.columns and not df_rekon.empty else ["Juni 2026", "Juli 2026", "Agustus 2026"]

bulan_filter = st.sidebar.multiselect("📅 Filter Bulan Laporan:", options=all_bulan, default=all_bulan)
mesin_filter = st.sidebar.multiselect("📟 Tipe Mesin Terminal:", options=all_mesin, default=all_mesin)
lok_filter = st.sidebar.multiselect("🏢 Pengelola (LOK):", options=all_lok, default=all_lok)

if not df_rekon.empty:
    month_filter_values = atmi_remove_month if active_data_scope == "ATMI" else df_rekon["BULAN"]
    filtered_df = df_rekon[
        (df_rekon["Mesin"].isin(mesin_filter)) &
        (df_rekon["LOK"].isin(lok_filter)) &
        (month_filter_values.isin(bulan_filter))
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
            <h1>Abacus Malang - ATM Reconciliation & Integrated Operational System</h1>
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
def display_styled_df(df, num_cols, column_order=None):
    if df.empty:
        st.info("ℹ️ Tabel ini saat ini masih kosong. Silakan tambahkan data baru melalui menu Input Data atau Upload File Excel.")
        return
    display_df = df.reset_index(drop=True).copy()
    if column_order:
        ordered_columns = [column for column in column_order if column in display_df.columns]
        remaining_columns = [column for column in display_df.columns if column not in ordered_columns]
        display_df = display_df[ordered_columns + remaining_columns]
    styler = display_df.style.format({c: "{:,.0f}" for c in num_cols if c in display_df.columns})
    
    def highlight_neg(val):
        if isinstance(val, (int, float, np.number)) and val < 0:
            return 'color: #E11D48; font-weight: bold; background-color: #FFE4E6;'
        if isinstance(val, (int, float, np.number)) and val > 0:
            return 'color: #047857; font-weight: bold; background-color: #D1FAE5;'
        return ''
    
    if hasattr(styler, "map"):
        styled = styler.map(highlight_neg, subset=[c for c in num_cols if c in display_df.columns])
    else:
        styled = styler.applymap(highlight_neg, subset=[c for c in num_cols if c in display_df.columns])

    column_config = {}
    wide_columns = ["KETERANGAN", "CATATAN", "TANGGAPAN", "ACTIVITY", "REVIEW", "UK_BDC", "TEST_CASH"]
    for column in display_df.columns:
        if is_identifier_column(column):
            column_config[column] = st.column_config.TextColumn(column, width="small")
        elif column in num_cols:
            column_config[column] = st.column_config.NumberColumn(column, format="%,.0f", width="small")
        elif "TGL" in column.upper() or "TANGGAL" in column.upper():
            column_config[column] = st.column_config.TextColumn(column, width="small")
        elif any(keyword in column.upper() for keyword in wide_columns):
            column_config[column] = st.column_config.TextColumn(column, width="large")
        else:
            column_config[column] = st.column_config.TextColumn(column, width="medium")
    
    st.dataframe(
        styled,
        column_config=column_config,
        column_order=list(display_df.columns),
        hide_index=True,
        use_container_width=True,
        height=min(560, max(180, 68 + (len(display_df) * 36)))
    )

# ---------------------------------------------------------
# MODUL AKTIVITAS LOGIN
# ---------------------------------------------------------
if menu == "🕘 Aktivitas Login":
    st.markdown("""
    <div class="access-hero">
        <h1>🕘 Aktivitas Login</h1>
        <p>Pantau riwayat akses pengguna setiap hari.</p>
    </div>
    """, unsafe_allow_html=True)

    login_df = pd.DataFrame(st.session_state.login_activity)
    if login_df.empty:
        st.info("Belum ada aktivitas login yang tercatat.")
    else:
        login_df["Tanggal_dt"] = pd.to_datetime(login_df["Tanggal"], errors="coerce")
        activity_col1, activity_col2, activity_col3 = st.columns(3)
        with activity_col1:
            selected_activity_date = st.date_input("Tanggal", value=datetime.now().date())
        with activity_col2:
            activity_users = ["Semua"] + sorted(login_df["Username"].unique().tolist())
            selected_activity_user = st.selectbox("Username", activity_users)
        with activity_col3:
            activity_status = st.selectbox("Status", ["Semua", "Berhasil", "Gagal"])

        filtered_activity = login_df[login_df["Tanggal_dt"].dt.date == selected_activity_date]
        if selected_activity_user != "Semua":
            filtered_activity = filtered_activity[filtered_activity["Username"] == selected_activity_user]
        if activity_status != "Semua":
            filtered_activity = filtered_activity[filtered_activity["Status"] == activity_status]
        filtered_activity = filtered_activity.drop(columns=["Tanggal_dt"])

        metric_col1, metric_col2, metric_col3 = st.columns(3)
        metric_col1.metric("Total Aktivitas", len(filtered_activity))
        metric_col2.metric("Login Berhasil", int((filtered_activity["Status"] == "Berhasil").sum()))
        metric_col3.metric("Login Gagal", int((filtered_activity["Status"] == "Gagal").sum()))
        st.dataframe(filtered_activity, hide_index=True, use_container_width=True, height=360)
        st.download_button(
            "📥 Download Aktivitas Login CSV",
            data=filtered_activity.to_csv(index=False).encode("utf-8"),
            file_name=f"Aktivitas_Login_{selected_activity_date.strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# ---------------------------------------------------------
# MODUL HAK AKSES
# ---------------------------------------------------------
elif menu == "🔐 Hak Akses":
    st.markdown("""
    <div class="access-hero">
        <h1>🔐 Pusat Hak Akses</h1>
        <p>Kelola kewenangan pengguna berdasarkan modul dan jenis aktivitas.</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 👤 Manajemen Akun")
    account_summary = pd.DataFrame([
        {"Username": username, "Role": account["role"].title(), "Password": "••••••••"}
        for username, account in st.session_state.auth_users.items()
    ])
    st.dataframe(account_summary, hide_index=True, use_container_width=True)

    account_col1, account_col2 = st.columns(2)
    with account_col1:
        with st.form("add_account_form", clear_on_submit=True):
            st.markdown("**Tambah akun baru**")
            new_username = st.text_input("Username baru")
            new_password = st.text_input("Password baru", type="password")
            new_role = st.selectbox("Role akun", ["admin", "user", "supervisor"])
            add_account = st.form_submit_button("➕ Tambah Akun", use_container_width=True)
            if add_account:
                normalized_username = new_username.strip().lower()
                if not normalized_username or not new_password:
                    st.error("Username dan password wajib diisi.")
                elif normalized_username in st.session_state.auth_users:
                    st.error("Username sudah terdaftar.")
                else:
                    st.session_state.auth_users[normalized_username] = {
                        "password": new_password,
                        "role": new_role,
                    }
                    st.success(f"Akun {normalized_username} berhasil ditambahkan.")
                    safe_rerun()

    with account_col2:
        with st.form("update_account_form"):
            st.markdown("**Perbarui akun**")
            account_username = st.selectbox("Pilih username", list(st.session_state.auth_users.keys()))
            account_password = st.text_input("Password baru", type="password")
            account_role = st.selectbox("Role baru", ["admin", "user", "supervisor"], index=["admin", "user", "supervisor"].index(st.session_state.auth_users[account_username]["role"]))
            update_account = st.form_submit_button("💾 Simpan Akun", use_container_width=True)
            if update_account:
                if not account_password:
                    st.error("Password baru wajib diisi.")
                else:
                    st.session_state.auth_users[account_username] = {
                        "password": account_password,
                        "role": account_role,
                    }
                    st.success(f"Akun {account_username} berhasil diperbarui.")
                    safe_rerun()

    st.markdown("---")

    selected_access_role = st.selectbox("Role yang akan diatur", ["admin", "user"])
    role_description = {
        "admin": "Admin dapat diberikan kewenangan operasional untuk mengelola data.",
        "user": "User umumnya digunakan untuk pemantauan dan akses baca.",
    }
    st.markdown(f"<div class='access-role-card'><b>Role: {selected_access_role.title()}</b><br>{role_description[selected_access_role]}</div>", unsafe_allow_html=True)

    with st.container(key="access_matrix"):
        with st.form("access_control_form"):
            header_cols = st.columns([3.2, 1, 1, 1, 1])
            with header_cols[0]:
                st.markdown("**Modul**")
            for index, action in enumerate(ACCESS_ACTIONS, start=1):
                with header_cols[index]:
                    st.caption(action)

            access_values = {}
            for module in ACCESS_MODULES:
                cols = st.columns([3.2, 1, 1, 1, 1])
                with cols[0]:
                    st.markdown(f"<div class='access-module'>{module}</div>", unsafe_allow_html=True)
                for index, action in enumerate(ACCESS_ACTIONS, start=1):
                    with cols[index]:
                        access_values[(module, action)] = st.checkbox(
                            action,
                            value=role_permissions[selected_access_role][module][action],
                            key=f"access_{selected_access_role}_{module}_{action}",
                            label_visibility="collapsed"
                        )

            save_access = st.form_submit_button("💾 Simpan Perubahan Hak Akses", type="primary", use_container_width=True)
            if save_access:
                for (module, action), value in access_values.items():
                    role_permissions[selected_access_role][module][action] = value
                st.session_state.role_permissions = role_permissions
                st.success(f"Hak akses role {selected_access_role} berhasil disimpan.")
                safe_rerun()

    st.info("Supervisor selalu memiliki akses penuh dan tidak dapat dibatasi oleh pengaturan ini.")

# ---------------------------------------------------------
# MODUL 1: DASHBOARD EXECUTIVE OVERVIEW
# ---------------------------------------------------------
if menu == "🏦 BCA":
    st.subheader("🏦 Data BCA")
    st.caption("Tampilan data yang teridentifikasi sebagai BCA berdasarkan WSID atau lokasi.")
    bca_mask = (
        df_rekon["WSID"].astype(str).str.contains("BCA", case=False, na=False) |
        df_rekon["LOKASI"].astype(str).str.contains("BCA", case=False, na=False) |
        df_rekon["LOK"].astype(str).str.contains("BCA", case=False, na=False)
    ) if not df_rekon.empty else pd.Series(dtype=bool)
    bca_df = df_rekon[bca_mask] if not df_rekon.empty else df_rekon
    display_styled_df(bca_df, ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"])

elif menu == "🏢 ATMI":
    st.subheader("🏢 Data ATMI")
    st.caption("Tampilan data yang teridentifikasi sebagai ATMI berdasarkan WSID atau lokasi.")
    atmi_mask = (
        df_rekon["WSID"].astype(str).str.contains("ATMI", case=False, na=False) |
        df_rekon["LOKASI"].astype(str).str.contains("ATMI", case=False, na=False) |
        df_rekon["LOK"].astype(str).str.contains("ATMI", case=False, na=False)
    ) if not df_rekon.empty else pd.Series(dtype=bool)
    atmi_df = df_rekon[atmi_mask] if not df_rekon.empty else df_rekon
    display_styled_df(atmi_df, ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"])

elif menu == "📊 Dashboard Executive Overview":
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

    if can_upload_photo:
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
        is_atmi_summary = active_data_scope == "ATMI"
        summary_title = "### 📅 Ringkasan Beban ACS Per Bulan" if is_atmi_summary else "### 📅 Ringkasan Selisih Kas Per Bulan"
        st.markdown(summary_title)
        if "BULAN" in filtered_df.columns:
            bulan_list = sorted(filtered_df["BULAN"].unique().tolist(), key=month_sort_key)
            cols_m = st.columns(max(len(bulan_list), 1))

            beban_acs_column = next(
                (
                    column for column in filtered_df.columns
                    if re.sub(r"[^a-z0-9]+", "", str(column).lower()) == "bebanacs"
                ),
                None
            )
            
            for idx, b_name in enumerate(bulan_list):
                b_df = filtered_df[filtered_df["BULAN"] == b_name]
                b_count = len(b_df["WSID"].unique())
                if is_atmi_summary:
                    b_beban_acs = b_df[beban_acs_column].map(safe_float).sum() if beban_acs_column else 0
                
                with cols_m[idx % len(cols_m)]:
                    if is_atmi_summary:
                        beban_label = "Kolom tidak ditemukan" if not beban_acs_column else f"Rp {b_beban_acs:,.0f}"
                        beban_color = amount_color(b_beban_acs)
                        st.markdown(f"""
                        <div class="acs-summary-card">
                            <div class="acs-summary-month">🗓️ {b_name}</div>
                            <div class="acs-summary-label">Total Beban ACS</div>
                            <div class="acs-summary-value" style="color: {beban_color};">{beban_label}</div>
                            <div class="acs-summary-meta">{len(b_df)} baris data</div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        b_sel_awal = safe_float(b_df["SEL_AWAL"].sum()) * 1000
                        b_sel_akhir = safe_float(b_df["SEL_AKHIR"].sum()) * 1000
                        sel_awal_color = amount_color(b_sel_awal)
                        sel_akhir_color = amount_color(b_sel_akhir)
                        st.markdown(f"""
                        <div class="card-box" style="border-top: 4px solid #00529C;">
                            <span class="month-badge">🗓️ {b_name}</span>
                            <p style="margin-top: 8px; font-size: 13px; color: #475569;">Total Unit: <b>{b_count} Terminal</b></p>
                            <p style="margin: 0; font-size: 13px;">Selisih Awal: <b style="color: {sel_awal_color};">Rp {b_sel_awal:,.0f}</b></p>
                            <p style="margin: 0; font-size: 13px;">Selisih Akhir: <b style="color: {sel_akhir_color};">Rp {b_sel_akhir:,.0f}</b></p>
                        </div>
                        """, unsafe_allow_html=True)

    st.markdown("---")

    col_srch, col_m_select, col_mode = st.columns([2, 1, 1.2])
    with col_srch:
        search_kw = st.text_input("🔍 Cari WSID, Lokasi, Bulan, Status UK BDC, Tes Cash, atau Staff:", "")
    with col_m_select:
        selected_month_filter = st.selectbox("📅 Filter Khusus Bulan Tabel:", ["Semua Bulan"] + all_bulan)
    with col_mode:
        table_modes = ["👁️ Mode Format", "✏️ Mode Data Editor"] if can_edit_main else ["👁️ Mode Format"]
        table_mode = st.radio("🛠️ Mode Tampilan Tabel:", table_modes, horizontal=True)

    disp_df = filtered_df.copy()
    
    if selected_month_filter != "Semua Bulan" and not disp_df.empty:
        if active_data_scope == "ATMI":
            disp_df = disp_df[atmi_remove_month.loc[disp_df.index] == selected_month_filter]
        else:
            disp_df = disp_df[disp_df["BULAN"] == selected_month_filter]

    if search_kw and not disp_df.empty:
        search_masks = [disp_df[col].astype(str).str.contains(search_kw, case=False, na=False) for col in disp_df.columns]
        if search_masks:
            mask = pd.concat(search_masks, axis=1).any(axis=1)
            disp_df = disp_df[mask]

    disp_df["BULAN"] = month_from_remove_date(get_remove_date_series(disp_df))

    predefined_cols = [
        "WSID", "LOK", "LOKASI", "BULAN", "Mesin", "TGL_INS", "TGL_REM", 
        "CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR",
        "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", "REKON_SISLOK", "REVIEW_STOCK",
        "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_ABACUS"
    ]
    uploaded_columns = st.session_state.export_columns_by_scope.get("ATMI", [])
    if st.session_state.active_data_scope == "ATMI" and uploaded_columns:
        cols_exist = [column for column in uploaded_columns if column in disp_df.columns and column != "BULAN"]
        location_index = cols_exist.index("LOKASI") + 1 if "LOKASI" in cols_exist else len(cols_exist)
        cols_exist.insert(location_index, "BULAN")
    else:
        cols_exist = [c for c in predefined_cols if c in disp_df.columns] + [c for c in disp_df.columns if c not in predefined_cols]

    if table_mode == "👁️ Mode Format":
        display_styled_df(disp_df[cols_exist], ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR", "BDC", "NON_BDC", "TOTAL_UK", "NOMINAL_SELISIH", "STOK_SISLOK_AWAL", "KAS_MASUK", "KAS_KELUAR"], column_order=cols_exist)
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
    staff_source_df = disp_df.copy()
    if not staff_source_df.empty:
        st.markdown("---")
        with st.expander("👥 Rincian Semua Staff Operasional Per WSID (Multi-Staff View)", expanded=False):
            st.caption("Data rincian diambil langsung dari baris yang tampil pada Tabel Utama setelah filter diterapkan.")
            wsid_opt_main = [str(w) for w in staff_source_df["WSID"].unique().tolist()]
            sel_main_wsid = st.selectbox("Pilih WSID Terminal untuk Audit Staff:", wsid_opt_main, key="m_select_wsid_staff")
            
            sub_staff_df = staff_source_df[staff_source_df["WSID"].astype(str) == sel_main_wsid]
            st.info(f"Ditemukan **{len(sub_staff_df)} Log Petugas/Staff** terdaftar untuk WSID **{sel_main_wsid}**")
            
            staff_show_cols = ["WSID", "LOKASI", "BULAN", "STAFF_1", "STAFF_2", "STAFF_3", "STAFF_LAINNYA", "DRIVER", "TGL_INS", "TGL_REM", "ACTIVITY", "CATATAN_PROSES"]
            existing_s_cols = [c for c in staff_show_cols if c in sub_staff_df.columns]
            st.dataframe(sub_staff_df[existing_s_cols], use_container_width=True)

    if can_manage_data:
        st.markdown("---")
        st.markdown("### ⚙️ Panel Aksi Edit & Hapus Baris Data (Row Action Panel)")

    if can_manage_data and not disp_df.empty:
        action_tabs = []
        if can_edit_main:
            action_tabs.append("✏️ [UPDATE] Edit Record Baris Data")
        if can_delete_main:
            action_tabs.append("🗑️ [DELETE] Hapus Record Baris Data")
        if can_add_main:
            action_tabs.append("➕ [CREATE] Tambah Baris Baru")
        action_tabs = st.tabs(action_tabs)
        tab_act_u = action_tabs[0] if can_edit_main else None
        tab_act_d = action_tabs[1 if can_edit_main else 0] if can_delete_main else None
        tab_act_a = action_tabs[-1] if can_add_main else None
        
        wsid_list = [str(w) for w in disp_df["WSID"].unique().tolist()] if "WSID" in disp_df.columns else [str(i) for i in disp_df.index]
        
        if can_edit_main:
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
                        me_lok = st.selectbox("LOK", ["ABACUS", "T"], index=0 if str(row_val.get("LOK")) != "T" else 1)
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
                    me_tanggapan = st.text_area("Tanggapan Abacus Malang / Audit Log", value=str(row_val.get("TANGGAPAN_ABACUS", "")))
                    
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
                        st.session_state.df_rekon.at[e_idx, "TANGGAPAN_ABACUS"] = me_tanggapan
                        
                        st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, "TGL_REM")
                        st.session_state.upload_success_msg = f"🎉 Data WSID '{me_wsid}' berhasil diperbarui!"
                        safe_rerun()

        if can_delete_main:
            sel_d_wsid = st.selectbox("Pilih WSID Target yang Ingin Dihapus:", wsid_list, key="m_select_del_wsid")
            st.warning(f"⚠️ Apakah Anda yakin ingin menghapus seluruh data untuk WSID **{sel_d_wsid}**?")
            if st.button(f"🗑️ [DELETE] Konfirmasi Hapus Data WSID {sel_d_wsid}", type="primary", key="btn_confirm_del"):
                st.session_state.df_rekon = st.session_state.df_rekon[st.session_state.df_rekon["WSID"].astype(str) != sel_d_wsid].reset_index(drop=True)
                st.session_state.upload_success_msg = f"🗑️ Data WSID '{sel_d_wsid}' berhasil dihapus!"
                safe_rerun()

        if can_add_main:
            with st.form("form_main_add"):
                st.info("➕ Menambahkan Baris Rekonsiliasi Kas Baru ke Tabel Utama")
                a_col1, a_col2, a_col3, a_col4 = st.columns(4)
                with a_col1:
                    a_wsid = st.text_input("WSID Terminal", "")
                    a_lok = st.selectbox("LOK", ["ABACUS", "T"])
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
                a_tanggapan = st.text_area("Tanggapan Abacus Malang", "")
                
                sub_add_main = st.form_submit_button("➕ [CREATE] Simpan Baris Data Baru", type="primary")
                if sub_add_main and a_wsid:
                    new_main_row = {
                        "WSID": a_wsid, "LOK": a_lok, "LOKASI": a_lokasi, "Mesin": a_mesin,
                        "CASH_POS": a_cash_pos, "SETOR": a_setor, "SEL_AWAL": a_setor - a_cash_pos, "SEL_AKHIR": a_sel_akhir,
                        "UK_BDC": a_uk_bdc, "TEST_CASH": a_test_cash, "CLOSE_OPEN_CENCON": a_cencon,
                        "STAFF_1": a_staff1, "DRIVER": a_driver, "ACTIVITY": a_activity,
                        "CATATAN_PROSES": a_catatan, "TANGGAPAN_ABACUS": a_tanggapan,
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
                    if can_manage_data and st.button(f"🗑️ Hapus Foto WSID {sel_img_wsid}", key=f"del_img_{sel_img_wsid}"):
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
            if sub_add_s and can_manage_staff:
                first_row = staff_records.iloc[0] if not staff_records.empty else {}
                new_staff_row = {
                    "WSID": sel_s_wsid,
                    "LOK": first_row.get("LOK", "ABACUS"),
                    "LOKASI": first_row.get("LOKASI", "ABACUS MALANG"),
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
                    "TANGGAPAN_ABACUS": first_row.get("TANGGAPAN_ABACUS", "-")
                }
                st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, pd.DataFrame([new_staff_row])], ignore_index=True)
                st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, "TGL_REM")
                st.success(f"Log staff baru untuk WSID {sel_s_wsid} berhasil ditambahkan!")
                safe_rerun()
            elif sub_add_s:
                st.warning("Role ini hanya memiliki akses baca untuk modul staff.")
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
        if can_manage_data:
            st.markdown("### 📤 Unggah Foto Bukti Baru")
            target_wsid = st.text_input("Ketik WSID Target Foto:", "")
            uploaded_img = st.file_uploader("Unggah File Foto Bukti (PNG / JPG / JPEG):", type=["png", "jpg", "jpeg"])

            if uploaded_img is not None and target_wsid:
                image_bytes = uploaded_img.read()
                st.session_state.image_store[target_wsid] = image_bytes
                st.success(f"Foto bukti untuk WSID {target_wsid} berhasil diunggah!")
        else:
            st.info("Role user hanya dapat melihat foto bukti yang tersimpan.")

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
                i_lok = st.selectbox("LOK (Pengelola)", ["ABACUS", "T"])
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
            i_tanggapan = st.text_area("Tanggapan Abacus Malang", "")

            sub1 = st.form_submit_button("💾 Simpan Record Rekon Utama")
            if sub1:
                new_r = {
                    "WSID": i_wsid, "LOK": i_lok, "LOKASI": i_lokasi, "Mesin": i_mesin, "BULAN": i_bulan,
                    "TGL_INS": pd.to_datetime(i_tgl_ins), "TGL_REM": pd.to_datetime(i_tgl_rem),
                    "CASH_POS": i_cash_pos, "SETOR": i_setor, "SEL_AWAL": i_sel_awal, "SEL_AKHIR": i_sel_akhir,
                    "UK_BDC": i_uk_bdc, "TEST_CASH": i_test_cash, "CLOSE_OPEN_CENCON": "Close",
                    "REKON_SISLOK": "Balanced", "REVIEW_STOCK": f"Sislok: {i_cash_pos:,.0f} | Fisik: {i_setor:,.0f}",
                    "STAFF_1": i_staff1, "STAFF_2": i_staff2, "STAFF_3": i_staff3, "STAFF_LAINNYA": i_staff_extra,
                    "DRIVER": i_driver, "ACTIVITY": i_activity, "CATATAN_PROSES": i_catatan, "TANGGAPAN_ABACUS": i_tanggapan
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
    active_scope = st.session_state.active_data_scope
    export_rekon_df = st.session_state.df_rekon.copy()
    if active_scope == "ATMI":
        export_rekon_df = convert_insert_remove_dates(export_rekon_df)
    export_columns = st.session_state.export_columns_by_scope.get(active_scope, [])
    if active_scope == "ATMI" and not export_columns and not export_rekon_df.empty:
        export_columns = list(export_rekon_df.columns)
        st.session_state.export_columns_by_scope[active_scope] = export_columns
    if export_columns:
        export_columns = [column for column in export_columns if column in export_rekon_df.columns]
        export_rekon_df = export_rekon_df[export_columns]
    preview_rekon_df = export_rekon_df.copy()
    export_cencon_df = st.session_state.df_cencon.copy()
    export_uk_df = st.session_state.df_uk.copy()
    export_ebos_df = st.session_state.df_ebos.copy()
    export_ej_df = st.session_state.df_ej.copy()
    export_sislok_df = st.session_state.df_sislok.copy()
    export_kolong_df = st.session_state.df_kolong.copy()
    st.subheader(f"📥 Ekspor & Impor Data {active_scope}")
    st.caption(f"Semua proses di halaman ini hanya menggunakan data scope {active_scope}.")

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("### 📄 Unduh File Excel Multi-Sheet")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_rekon_df.to_excel(writer, sheet_name='Rekon_Utama_Staff', index=False)
            export_cencon_df.to_excel(writer, sheet_name='Tes_Cash_Cencon', index=False)
            export_uk_df.to_excel(writer, sheet_name='Uang_Kembali_UK', index=False)
            export_ebos_df.to_excel(writer, sheet_name='Laporan_EBOS', index=False)
            export_ej_df.to_excel(writer, sheet_name='Rekon_EJ', index=False)
            export_sislok_df.to_excel(writer, sheet_name='Sislok_Stock_Review', index=False)
            export_kolong_df.to_excel(writer, sheet_name='Temuan_Uang_Kolong', index=False)

        from openpyxl import load_workbook
        output.seek(0)
        workbook = load_workbook(output)
        for worksheet in workbook.worksheets:
            identifier_columns = {
                cell.column for cell in worksheet[1]
                if is_identifier_column(cell.value)
            }
            for header_cell in worksheet[1]:
                column_values = [
                    str(cell.value) for cell in worksheet[header_cell.column][1:]
                    if cell.value is not None
                ]
                header_name = str(header_cell.value or "")
                if is_identifier_column(header_name):
                    column_width = 14
                elif is_insert_remove_date_column(header_name):
                    column_width = 15
                elif "TGL" in header_name.upper() or "TANGGAL" in header_name.upper():
                    column_width = 15
                elif any(keyword in header_name.upper() for keyword in ["KETERANGAN", "CATATAN", "TANGGAPAN", "ACTIVITY", "REVIEW"]):
                    column_width = 34
                elif header_name in ["UK_BDC", "TEST_CASH"]:
                    column_width = 28
                else:
                    longest_value = max([len(header_name)] + [len(value) for value in column_values])
                    column_width = min(max(longest_value + 2, 12), 24)
                worksheet.column_dimensions[header_cell.column_letter].width = column_width
            for column_index in identifier_columns:
                for cells in worksheet.iter_cols(min_col=column_index, max_col=column_index, min_row=2):
                    for cell in cells:
                        cell.number_format = "General"
            for header_cell in worksheet[1]:
                if is_insert_remove_date_column(header_cell.value):
                    for cells in worksheet.iter_cols(min_col=header_cell.column, max_col=header_cell.column, min_row=2):
                        for cell in cells:
                            cell.number_format = "dd/mm/yyyy"
        formatted_output = io.BytesIO()
        workbook.save(formatted_output)
        formatted_output.seek(0)

        st.download_button(
            label=f"💾 Download Workbook {active_scope} (.xlsx)",
            data=formatted_output.getvalue(),
            file_name=f"Rekonsiliasi_{active_scope}_Abacus_Malang_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_ex2:
        st.markdown(f"### 📤 Upload Master Excel / CSV {active_scope}")
        
        if can_manage_data:
            import_mode = st.radio(
                "⚙️ Mode Import Data:",
                ["➕ Tambahkan & Akumulasikan Data Baru (Auto-Append)", "🔄 Ganti / Overwrite Seluruh Data"],
                index=0,
                horizontal=True,
                help="Modus 'Tambahkan & Akumulasikan Data Baru' otomatis menyimpan dan menggabungkan data dari setiap file yang diunggah ke dalam database tanpa menghapus data sebelumnya."
            )

            uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls / .csv) untuk memuat data:", type=["xlsx", "xls", "csv"])
        else:
            st.info("Role user hanya dapat mengunduh laporan. Import data memerlukan role admin atau supervisor.")
            uploaded_file = None
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    new_df = pd.read_csv(uploaded_file, dtype=str)
                else:
                    xl = pd.ExcelFile(uploaded_file)
                    if 'Rekon_Utama_Staff' in xl.sheet_names:
                        new_df = xl.parse('Rekon_Utama_Staff', dtype=str)
                    else:
                        new_df = xl.parse(0, dtype=str)

                    # Parse additional sheets if present
                    if 'Tes_Cash_Cencon' in xl.sheet_names:
                        c_df = xl.parse('Tes_Cash_Cencon', dtype=str)
                        if import_mode.startswith("➕") and not st.session_state.df_cencon.empty:
                            st.session_state.df_cencon = pd.concat([st.session_state.df_cencon, c_df], ignore_index=True)
                        else:
                            st.session_state.df_cencon = c_df

                    if 'Uang_Kembali_UK' in xl.sheet_names:
                        u_df = xl.parse('Uang_Kembali_UK', dtype=str)
                        if import_mode.startswith("➕") and not st.session_state.df_uk.empty:
                            st.session_state.df_uk = pd.concat([st.session_state.df_uk, u_df], ignore_index=True)
                        else:
                            st.session_state.df_uk = u_df

                    if 'Laporan_EBOS' in xl.sheet_names:
                        e_df = xl.parse('Laporan_EBOS', dtype=str)
                        if import_mode.startswith("➕") and not st.session_state.df_ebos.empty:
                            st.session_state.df_ebos = pd.concat([st.session_state.df_ebos, e_df], ignore_index=True)
                        else:
                            st.session_state.df_ebos = e_df

                    if 'Rekon_EJ' in xl.sheet_names:
                        j_df = xl.parse('Rekon_EJ', dtype=str)
                        if import_mode.startswith("➕") and not st.session_state.df_ej.empty:
                            st.session_state.df_ej = pd.concat([st.session_state.df_ej, j_df], ignore_index=True)
                        else:
                            st.session_state.df_ej = j_df

                    if 'Sislok_Stock_Review' in xl.sheet_names:
                        s_df = xl.parse('Sislok_Stock_Review', dtype=str)
                        if import_mode.startswith("➕") and not st.session_state.df_sislok.empty:
                            st.session_state.df_sislok = pd.concat([st.session_state.df_sislok, s_df], ignore_index=True)
                        else:
                            st.session_state.df_sislok = s_df

                    if 'Temuan_Uang_Kolong' in xl.sheet_names:
                        k_df = xl.parse('Temuan_Uang_Kolong', dtype=str)
                        if import_mode.startswith("➕") and not st.session_state.df_kolong.empty:
                            st.session_state.df_kolong = pd.concat([st.session_state.df_kolong, k_df], ignore_index=True)
                        else:
                            st.session_state.df_kolong = k_df

                imported_rekon_columns = list(new_df.columns)

                new_df = sanitize_df(new_df, [
                    "WSID", "LOK", "LOKASI", "Mesin", "BULAN", "TGL_INS", "TGL_REM", "CASH_POS", "SETOR", 
                    "SEL_AWAL", "SEL_AKHIR", "UK_BDC", "TEST_CASH", "CLOSE_OPEN_CENCON", 
                    "REKON_SISLOK", "REVIEW_STOCK", "STAFF_1", "STAFF_2", "STAFF_3", 
                    "DRIVER", "ACTIVITY", "CATATAN_PROSES", "TANGGAPAN_ABACUS"
                ])
                if active_scope == "ATMI":
                    new_df = convert_insert_remove_dates(new_df)
                new_df = auto_fill_bulan(new_df, date_col="TGL_REM")

                # Selalu gunakan struktur file terakhir agar preview dan ekspor ATMI identik.
                st.session_state.export_columns_by_scope[active_scope] = imported_rekon_columns

                if import_mode.startswith("➕") and not st.session_state.df_rekon.empty:
                    st.session_state.df_rekon = pd.concat([st.session_state.df_rekon, new_df], ignore_index=True)
                    st.session_state.df_rekon = auto_fill_bulan(st.session_state.df_rekon, date_col="TGL_REM")
                    st.session_state.upload_success_msg = f"🎉 File '{uploaded_file.name}' ({len(new_df)} baris) berhasil diunggah & otomatis tersimpan ditambahkan! Total data tersimpan sekarang: {len(st.session_state.df_rekon)} baris."
                else:
                    st.session_state.df_rekon = new_df
                    st.session_state.upload_success_msg = f"🎉 File '{uploaded_file.name}' ({len(new_df)} baris) berhasil diunggah dan disimpan di Tabel Utama!"

                if active_scope == "ATMI":
                    st.session_state.active_data_scope = "ATMI"
                    st.session_state.menu_group = "🏢 ATMI"
                st.session_state.target_nav_menu = "📋 Tabel Utama (Complete Audit)"
                safe_rerun()
            except Exception as e:
                st.error(f"Gagal memuat file: {e}")

    st.markdown("---")
    st.markdown(f"### 👁️ Preview Data Rekonsiliasi {active_scope}")
    st.caption(f"Preview ini sama dengan sheet `Rekon_Utama_Staff` pada workbook {active_scope}: {len(preview_rekon_df)} baris, {len(preview_rekon_df.columns)} kolom.")
    if preview_rekon_df.empty:
        st.dataframe(
            preview_rekon_df,
            column_order=list(preview_rekon_df.columns),
            hide_index=True,
            use_container_width=True,
            height=180
        )
    else:
        display_styled_df(
            preview_rekon_df,
            ["CASH_POS", "SETOR", "SEL_AWAL", "SEL_AKHIR"],
            column_order=export_columns
        )
