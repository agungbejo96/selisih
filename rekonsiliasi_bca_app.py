import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import io

# ---------------------------------------------------------
# Page Configuration & Styling
# ---------------------------------------------------------
st.set_page_config(
    page_title="Sistem Rekonsiliasi Kas BCA",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for BCA Branding
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #00529C 0%, #003366 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        color: white;
        margin: 0;
        font-size: 28px;
        font-weight: 700;
    }
    .main-header p {
        color: #E0E0E0;
        margin: 5px 0 0 0;
        font-size: 14px;
    }
    .metric-card {
        background-color: #FFFFFF;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #00529C;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stTable {
        font-size: 13px;
    }
    .badge-bca {
        background-color: #00529C;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .badge-vendor {
        background-color: #2E7D32;
        color: white;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Initial Data Load (Based on Grounding Source: juli.png)
# ---------------------------------------------------------
def load_default_data():
    data = [
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
    df = pd.DataFrame(data)
    df["TGL_INS"] = pd.to_datetime(df["TGL_INS"])
    df["TGL_REM"] = pd.to_datetime(df["TGL_REM"])
    return df

if "df_rekon" not in st.session_state:
    st.session_state.df_rekon = load_default_data()

df = st.session_state.df_rekon

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/5/5c/Bank_Central_Asia_logo.svg", width=180)
st.sidebar.title("Menu Utama")

menu = st.sidebar.radio(
    "Navigasi Modul:",
    [
        "📊 Dashboard Overview",
        "📋 Tabel Rekonsiliasi Kas",
        "➕ Tambah / Edit Transaksi",
        "🔍 Analisis Tanggapan BCA",
        "📁 Ekspor & Impor Data"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filter Global")
mesin_filter = st.sidebar.multiselect("Tipe Mesin:", options=df["Mesin"].unique(), default=df["Mesin"].unique())
lok_filter = st.sidebar.multiselect("Pengelola (LOK):", options=df["LOK"].unique(), default=df["LOK"].unique())

filtered_df = df[(df["Mesin"].isin(mesin_filter)) & (df["LOK"].isin(lok_filter))]

# ---------------------------------------------------------
# Header Area
# ---------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>BCA ATM Reconciliation & Cash Variance System</h1>
    <p>Sistem Pengawasan Rekonsiliasi Kas, Pemantauan Selisih, dan Auditing Tanggapan Mesin ATM / CRM / ITM / ACH</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# MODUL 1: DASHBOARD OVERVIEW
# ---------------------------------------------------------
if menu == "📊 Dashboard Overview":
    st.subheader("📌 Ringkasan Eksekutif Rekonsiliasi Kas")

    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Terminal", f"{len(filtered_df)} Mesin")
    with col2:
        tot_pos = filtered_df["CASH_POS"].sum() * 1000
        st.metric("Total Cash Position", f"Rp {tot_pos:,.0f}")
    with col3:
        tot_setor = filtered_df["SETOR"].sum() * 1000
        st.metric("Total Kas Disetor", f"Rp {tot_setor:,.0f}")
    with col4:
        tot_awal = filtered_df["SEL_AWAL"].sum() * 1000
        st.metric("Total Selisih Awal", f"Rp {tot_awal:,.0f}", delta_color="inverse")
    with col5:
        tot_akhir = filtered_df["SEL_AKHIR"].sum() * 1000
        st.metric("Total Selisih Akhir", f"Rp {tot_akhir:,.0f}", delta_color="inverse")

    st.markdown("---")

    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📈 Perbandingan Cash Position vs Setor Realita")
        fig_bar = px.bar(
            filtered_df,
            x="WSID",
            y=["CASH_POS", "SETOR"],
            barmode="group",
            title="Posisi Kas Sistem (CASH_POS) vs Kas Disetor (SETOR) (dalam ribuan Rp)",
            labels={"value": "Jumlah (Ribu Rp)", "variable": "Kategori"},
            color_discrete_map={"CASH_POS": "#00529C", "SETOR": "#2E7D32"}
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col_right:
        st.subheader("📉 Distribusi Selisih Awal vs Selisih Akhir")
        fig_diff = go.Figure()
        fig_diff.add_trace(go.Bar(
            x=filtered_df["WSID"],
            y=filtered_df["SEL_AWAL"],
            name="Selisih Awal",
            marker_color="#D32F2F"
        ))
        fig_diff.add_trace(go.Bar(
            x=filtered_df["WSID"],
            y=filtered_df["SEL_AKHIR"],
            name="Selisih Akhir",
            marker_color="#F57C00"
        ))
        fig_diff.update_layout(
            title="Selisih Awal vs Selisih Akhir per WSID (dalam ribuan Rp)",
            barmode="group",
            xaxis_title="WSID",
            yaxis_title="Nilai Selisih (Ribu Rp)"
        )
        st.plotly_chart(fig_diff, use_container_width=True)

    col_bottom1, col_bottom2 = st.columns(2)
    with col_bottom1:
        st.subheader("🤖 Proporsi Tipe Mesin")
        fig_pie = px.pie(
            filtered_df,
            names="Mesin",
            title="Persentase Sebaran Tipe Mesin (CRMHYO, ITM, O-CRM, ACH)",
            color_discrete_sequence=px.colors.qualitative.Set2
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_bottom2:
        st.subheader("🏢 Sebaran Lokasi Pengelola (LOK)")
        fig_lok = px.pie(
            filtered_df,
            names="LOK",
            title="BCA vs Vendor Internal/External (T)",
            color_discrete_map={"BCA": "#00529C", "T": "#F57C00"}
        )
        st.plotly_chart(fig_lok, use_container_width=True)

# ---------------------------------------------------------
# MODUL 2: TABEL REKONSILIASI KAS
# ---------------------------------------------------------
elif menu == "📋 Tabel Rekonsiliasi Kas":
    st.subheader("📄 Rincian Laporan Selisih Kas Operasional ATM/CRM")

    search_kw = st.text_input("🔍 Cari berdasarkan WSID atau Lokasi:", "")
    if search_kw:
        display_df = filtered_df[
            filtered_df["WSID"].str.contains(search_kw, case=False, na=False) |
            filtered_df["LOKASI"].str.contains(search_kw, case=False, na=False)
        ]
    else:
        display_df = filtered_df.copy()

    # Format dataframe display
    formatted_df = display_df.copy()
    formatted_df["TGL_INS"] = formatted_df["TGL_INS"].dt.strftime("%Y-%m-%d")
    formatted_df["TGL_REM"] = formatted_df["TGL_REM"].dt.strftime("%Y-%m-%d")

    # Display Dataframe with high precision styling
    st.dataframe(
        formatted_df.style.format({
            "CASH_POS": "{:,.0f}",
            "SETOR": "{:,.0f}",
            "SEL_AWAL": "{:,.0f}",
            "SEL_AKHIR": "{:,.0f}"
        }).applymap(
            lambda v: 'color: red; font-weight: bold;' if isinstance(v, (int, float)) and v < 0 else '',
            subset=["SEL_AWAL", "SEL_AKHIR"]
        ),
        use_container_width=True,
        height=500
    )

    st.caption("Catatan: Angka tunai CASH_POS, SETOR, SEL_AWAL, dan SEL_AKHIR disajikan dalam nominal ribuan Rupiah (x1.000).")

# ---------------------------------------------------------
# MODUL 3: TAMBAH / EDIT TRANSAKSI
# ---------------------------------------------------------
elif menu == "➕ Tambah / Edit Transaksi":
    st.subheader("📝 Input Data Rekonsiliasi Kas Baru")

    with st.form("form_tambah_data"):
        col_f1, col_f2, col_f3, col_f4 = st.columns(4)
        with col_f1:
            new_wsid = st.text_input("WSID Terminal", "Z99X")
            new_lok = st.selectbox("LOK (Pengelola)", ["BCA", "T"])
        with col_f2:
            new_lokasi = st.text_input("Lokasi / Branch", "KCP MALANG KOTA")
            new_mesin = st.selectbox("Tipe Mesin", ["O-CRM", "ITM", "CRMHYO", "ACH"])
        with col_f3:
            new_tgl_ins = st.date_input("Tanggal Pengisian (TGL_INS)")
            new_tgl_rem = st.date_input("Tanggal Penarikan (TGL_REM)")
        with col_f4:
            new_cash_pos = st.number_input("Cash Position Sistem (Ribu Rp)", value=500000)
            new_setor = st.number_input("Total Disetor Aktual (Ribu Rp)", value=499500)

        new_sel_awal = new_setor - new_cash_pos
        st.info(f"💡 Estimasi Selisih Awal Terkalkulasi: **{new_sel_awal:,.0f} (Ribu Rp)**")

        col_f5, col_f6 = st.columns(2)
        with col_f5:
            new_sel_akhir = st.number_input("Selisih Akhir Audit (Ribu Rp)", value=-100)
        with col_f6:
            new_tanggapan = st.text_area("Tanggapan BCA / Catatan Audit", f"Selisih Awal : {new_sel_awal}\nUK : {abs(new_sel_awal - new_sel_akhir)}\nSelisih Akhir : {new_sel_akhir}")

        submitted = st.form_submit_button("💾 Simpan Data Rekonsiliasi")

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
            st.success(f"Data WSID {new_wsid} berhasil ditambahkan!")
            st.experimental_rerun()

# ---------------------------------------------------------
# MODUL 4: ANALISIS TANGGAPAN BCA
# ---------------------------------------------------------
elif menu == "🔍 Analisis Tanggapan BCA":
    st.subheader("🕵️ Audit Log & Tanggapan Operasional BCA")

    selected_wsid = st.selectbox("Pilih WSID untuk melihat rincian tanggapan BCA:", filtered_df["WSID"].unique())
    wsid_data = filtered_df[filtered_df["WSID"] == selected_wsid].iloc[0]

    st.markdown(f"### Detail Terminal: **{wsid_data['WSID']}** - {wsid_data['LOKASI']}")

    col_info1, col_info2, col_info3 = st.columns(3)
    with col_info1:
        st.write(f"**Pengelola (LOK):** {wsid_data['LOK']}")
        st.write(f"**Tipe Mesin:** {wsid_data['Mesin']}")
    with col_info2:
        st.write(f"**Tgl Insert:** {wsid_data['TGL_INS'].strftime('%Y-%m-%d')}")
        st.write(f"**Tgl Removal:** {wsid_data['TGL_REM'].strftime('%Y-%m-%d')}")
    with col_info3:
        st.write(f"**Selisih Awal:** Rp {wsid_data['SEL_AWAL']*1000:,.0f}")
        st.write(f"**Selisih Akhir:** Rp {wsid_data['SEL_AKHIR']*1000:,.0f}")

    st.markdown("#### 📜 Rincian Audit Tanggapan BCA:")
    tanggapan_lines = wsid_data["TANGGAPAN_BCA"].split("\n")
    for line in tanggapan_lines:
        if "UK" in line or "Pengembalian" in line:
            st.success(f"✅ {line}")
        elif "Keluhan" in line:
            st.warning(f"⚠️ {line}")
        elif "Koreksi" in line:
            st.info(f"ℹ️ {line}")
        else:
            st.write(f"🔹 {line}")

# ---------------------------------------------------------
# MODUL 5: EKSPOR & IMPOR DATA
# ---------------------------------------------------------
elif menu == "📁 Ekspor & Impor Data":
    st.subheader("📥 Unduh Laporan atau Unggah File Rekonsiliasi Baru")

    col_ex1, col_ex2 = st.columns(2)

    with col_ex1:
        st.markdown("### 📄 Unduh Data Terkini (.xlsx)")
        st.write("Klik tombol di bawah untuk mengunduh seluruh data rekonsiliasi kas ini ke format Microsoft Excel.")

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            export_df = st.session_state.df_rekon.copy()
            export_df["TGL_INS"] = export_df["TGL_INS"].dt.strftime("%Y-%m-%d")
            export_df["TGL_REM"] = export_df["TGL_REM"].dt.strftime("%Y-%m-%d")
            export_df.to_excel(writer, sheet_name='Rekonsiliasi_BCA', index=False)

        st.download_button(
            label="💾 Download File Excel (.xlsx)",
            data=output.getvalue(),
            file_name=f"Laporan_Rekonsiliasi_BCA_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with col_ex2:
        st.markdown("### 📤 Upload File Excel Baru")
        uploaded_file = st.file_uploader("Pilih file Excel (.xlsx / .xls) data rekonsiliasi:", type=["xlsx", "xls", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    new_df = pd.read_csv(uploaded_file)
                else:
                    new_df = pd.read_excel(uploaded_file)

                st.session_state.df_rekon = new_df
                st.success("File berhasil dimuat ke dalam aplikasi!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Gagal memuat file: {e}")
