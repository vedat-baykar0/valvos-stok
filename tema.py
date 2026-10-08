# -*- coding: utf-8 -*-
"""
Valvos - Kurumsal arayüz teması.

Streamlit'in hazır şablon görüntüsünü (sağ üstteki hamburger menü, Deploy
butonu, alttaki "Made with Streamlit" yazısı, üstteki renkli çizgi) tamamen
gizler ve endüstriyel/ağırbaşlı bir renk paleti uygular.

Renk paleti tek yerden değiştirilir: aşağıdaki RENKLER sözlüğü.
"""

import streamlit as st

RENKLER = {
    "lacivert":    "#13233A",  # ana kurumsal renk (koyu çelik lacivert)
    "lacivert_ac": "#1E3557",
    "celik":       "#2E5C8A",  # vurgu / buton
    "celik_ac":    "#3C76AE",
    "turuncu":     "#C2410C",  # uyarı / tehlike (endüstriyel turuncu)
    "zemin":       "#F4F6F8",
    "kart":        "#FFFFFF",
    "cizgi":       "#D7DEE6",
    "yazi":        "#1B2733",
    "yazi_soluk":  "#5A6B7C",
    "yesil":       "#15803D",
    "kirmizi":     "#B91C1C",
}


def _css():
    r = RENKLER
    return f"""
<style>
/* ---------- 1) STREAMLIT ŞABLON İZLERİNİ GİZLE ---------- */
#MainMenu {{visibility: hidden; display: none;}}
header[data-testid="stHeader"] {{display: none !important;}}
[data-testid="stToolbar"] {{display: none !important;}}
[data-testid="stDecoration"] {{display: none !important;}}
[data-testid="stStatusWidget"] {{display: none !important;}}
.stDeployButton {{display: none !important;}}
[data-testid="stAppDeployButton"] {{display: none !important;}}
footer {{visibility: hidden; display: none;}}
.viewerBadge_container__1QSob, .viewerBadge_link__qRIco {{display: none !important;}}
a[href^="https://streamlit.io"] {{display: none !important;}}

/* Üstteki boşluğu kapat - sayfa tepeden başlasın */
.block-container {{
    padding-top: 1.6rem !important;
    padding-bottom: 2.5rem !important;
    max-width: 1500px;
}}

/* ---------- 2) GENEL ---------- */
html, body, [class*="st-"] {{ color: {r['yazi']}; }}
.stApp {{ background: {r['zemin']}; }}

h1 {{
    color: {r['lacivert']};
    font-weight: 700 !important;
    letter-spacing: -0.5px;
    border-bottom: 3px solid {r['celik']};
    padding-bottom: .45rem;
    margin-bottom: .2rem !important;
}}
h2, h3 {{ color: {r['lacivert_ac']}; font-weight: 650 !important; }}
h5 {{ color: {r['lacivert_ac']}; font-weight: 650 !important; }}

/* ---------- 3) SOL MENÜ (endüstriyel koyu panel) ---------- */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, {r['lacivert']} 0%, {r['lacivert_ac']} 100%);
    border-right: 1px solid {r['lacivert']};
}}
section[data-testid="stSidebar"] * {{ color: #E8EEF6 !important; }}
section[data-testid="stSidebar"] h1 {{
    color: #FFFFFF !important;
    border-bottom: 2px solid {r['celik_ac']};
    font-size: 1.7rem;
}}
/* Menü seçenekleri */
section[data-testid="stSidebar"] [role="radiogroup"] label {{
    padding: .40rem .55rem;
    border-radius: 6px;
    margin-bottom: 2px;
    transition: background .15s ease;
}}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: rgba(255,255,255,.09);
}}
/* Metrikler */
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{
    font-size: 1.35rem !important; color: #FFFFFF !important;
}}
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] {{
    font-size: .78rem !important; color: #A8BDD4 !important;
    text-transform: uppercase; letter-spacing: .4px;
}}
section[data-testid="stSidebar"] hr {{ border-color: rgba(255,255,255,.18); }}

/* ---------- 4) BUTONLAR ---------- */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {{
    border-radius: 6px;
    font-weight: 600;
    border: 1px solid {r['cizgi']};
    background: {r['kart']};
    color: {r['lacivert']};
    transition: all .15s ease;
}}
.stButton > button:hover, .stDownloadButton > button:hover {{
    border-color: {r['celik']};
    color: {r['celik']};
    box-shadow: 0 2px 6px rgba(19,35,58,.12);
}}
/* Ana işlem butonu (type="primary") */
.stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {{
    background: {r['celik']};
    border: 1px solid {r['celik']};
    color: #FFFFFF;
    box-shadow: 0 2px 5px rgba(46,92,138,.28);
}}
.stButton > button[kind="primary"]:hover {{
    background: {r['lacivert_ac']};
    border-color: {r['lacivert_ac']};
}}
.stButton > button:disabled {{ opacity: .45; }}

/* ---------- 5) TABLOLAR ---------- */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"] {{
    border: 1px solid {r['cizgi']};
    border-radius: 6px;
    overflow: hidden;
}}
[data-testid="stDataFrame"] thead tr th {{
    background: {r['lacivert']} !important;
    color: #FFFFFF !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: .74rem;
    letter-spacing: .4px;
}}

/* ---------- 6) METRİK KARTLARI ---------- */
div[data-testid="stMetric"] {{
    background: {r['kart']};
    border: 1px solid {r['cizgi']};
    border-left: 4px solid {r['celik']};
    border-radius: 6px;
    padding: .85rem 1rem;
    box-shadow: 0 1px 3px rgba(19,35,58,.06);
}}
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {{
    font-size: .76rem; font-weight: 600; color: {r['yazi_soluk']};
    text-transform: uppercase; letter-spacing: .4px;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    color: {r['lacivert']}; font-weight: 700;
}}

/* ---------- 7) SEKMELER ---------- */
.stTabs [data-baseweb="tab-list"] {{
    gap: 2px; border-bottom: 2px solid {r['cizgi']};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent; border-radius: 6px 6px 0 0;
    padding: .5rem 1.05rem; font-weight: 600; color: {r['yazi_soluk']};
}}
.stTabs [aria-selected="true"] {{
    background: {r['kart']}; color: {r['lacivert']} !important;
    border-bottom: 3px solid {r['celik']};
}}

/* ---------- 8) GİRDİ ALANLARI ---------- */
.stTextInput input, .stNumberInput input, .stTextArea textarea {{
    border-radius: 6px; border-color: {r['cizgi']};
}}
.stTextInput input:focus, .stNumberInput input:focus {{
    border-color: {r['celik']} !important;
    box-shadow: 0 0 0 2px rgba(46,92,138,.15) !important;
}}

/* ---------- 9) UYARI KUTULARI ---------- */
div[data-testid="stAlert"] {{ border-radius: 6px; border-left-width: 5px; }}

/* ---------- 10) EXPANDER (tehlikeli işlemler burada saklı) ---------- */
details, [data-testid="stExpander"] {{
    border: 1px solid {r['cizgi']} !important;
    border-radius: 6px !important;
    background: {r['kart']};
}}

/* ---------- 11) GİRİŞ (LOGIN) EKRANI ---------- */
.valvos-giris {{
    background: linear-gradient(135deg, {r['lacivert']} 0%, {r['celik']} 100%);
    border-radius: 10px;
    padding: 2.1rem 1.6rem 1.7rem;
    text-align: center;
    margin-bottom: 1.6rem;
    box-shadow: 0 8px 24px rgba(19,35,58,.22);
}}
.valvos-giris .marka {{
    color: #FFFFFF; font-size: 2.5rem; font-weight: 800;
    letter-spacing: 7px; margin: 0; line-height: 1.1;
}}
.valvos-giris .cizgi {{
    width: 62px; height: 3px; background: #FFFFFF;
    margin: .75rem auto .7rem; opacity: .65; border-radius: 2px;
}}
.valvos-giris .alt {{
    color: #CBDAEC; font-size: .82rem; margin: 0;
    text-transform: uppercase; letter-spacing: 2.2px;
}}
.valvos-dipnot {{
    text-align: center; color: {r['yazi_soluk']};
    font-size: .76rem; margin-top: 1.9rem;
    padding-top: .9rem; border-top: 1px solid {r['cizgi']};
}}
</style>
"""


def uygula():
    """CSS'i sayfaya enjekte eder. app.py en başta bir kez çağırır."""
    st.markdown(_css(), unsafe_allow_html=True)


def giris_basligi():
    """Login ekranının üstündeki kurumsal marka bloğu."""
    st.markdown(
        """
<div class="valvos-giris">
    <p class="marka">VALVOS</p>
    <div class="cizgi"></div>
    <p class="alt">Vana Üretim &amp; Stok Yönetim Sistemi</p>
</div>
""",
        unsafe_allow_html=True,
    )


def dipnot(metin):
    st.markdown(f'<div class="valvos-dipnot">{metin}</div>', unsafe_allow_html=True)
