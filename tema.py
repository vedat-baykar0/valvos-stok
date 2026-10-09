# -*- coding: utf-8 -*-
"""
Valvos - Kurumsal arayüz teması (Premium / Light + Dark uyumlu).

TASARIM KURALI — buraya yeni CSS eklerken mutlaka uyun:

  Bu dosya ASLA sabit bir yazı rengi veya sabit bir arka plan rengi vermez.
  Yazı rengini ve zemini Streamlit'in kendi teması belirler (sağ üstteki
  ⋮ menüsü > Settings > Theme: Light / Dark / Use system setting).
  Dolayısıyla kullanıcı hangi temayı seçerse seçsin yazılar ve sayılar
  her zaman okunur kalır.

  Zemin/çerçeve gerektiğinde `rgba(128,128,128,...)` gibi NÖTR saydam
  katmanlar kullanılır: bu katman beyaz zeminde hafif gri, koyu zeminde
  hafif aydınlık görünür — iki temada da doğru çalışır.

  Renk sadece VURGU için kullanılır (çizgi, kenarlık, ikon, başlık altı):
  aşağıdaki RENKLER sözlüğündeki tonlar hem beyaz hem koyu zeminde
  okunacak şekilde seçilmiştir.
"""

import streamlit as st

# Vurgu renkleri — hepsi beyaz VE koyu zeminde okunur orta tonlardır.
RENKLER = {
    "vurgu":        "#3D7EBF",   # Valvos çelik mavisi — çizgi/kenarlık/başlık
    # Dolgu tonu AYRI: üstüne beyaz yazı bindiğinde (ana buton) kontrast
    # 4.5'in altına düşmesin diye bir tık koyu. #3D7EBF ile beyaz 4.26,
    # #3574AC ile 4.95 (WCAG normal yazı eşiği 4.5).
    "vurgu_dolgu":  "#3574AC",
    "vurgu_ac":     "#5B9BD5",
    "vurgu_koyu":   "#2E5C8A",
    "marka_koyu":   "#13233A",   # sadece giriş ekranının kendi zemininde
    "basari":       "#2E9E63",
    "uyari":        "#D98324",
    "tehlike":      "#DC4C4C",
}

# Nötr saydam katmanlar (iki temada da çalışır)
_KART = "rgba(128,128,128,.07)"
_KART_KOYU = "rgba(128,128,128,.12)"
# Kenarlık: .28 beyaz zeminde çok soluk kalıyordu (kontrast 1.38), .40 ile
# kutular iki temada da belirgin.
_CIZGI = "rgba(128,128,128,.40)"
_CIZGI_SOLUK = "rgba(128,128,128,.16)"


def _govde():
    """Sadece CSS kuralları (<style> etiketi olmadan)."""
    r = RENKLER
    return f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* =======================================================================
   0) ÖLÇEK — bütün arayüzü büyüt
   Streamlit ölçülerini "rem" ile verir; kök font boyutunu büyütmek
   yazıları, kutuları ve boşlukları birlikte ferahlatır.
   ======================================================================= */
html {{ font-size: 17px; }}

html, body, button, input, select, textarea,
[class*="st-"], [class*="css-"] {{
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 Roboto, 'Helvetica Neue', Arial, sans-serif !important;
    -webkit-font-smoothing: antialiased;
}}

/* =======================================================================
   1) ŞABLON İZLERİ
   Üstteki şerit GİZLENMEZ: kullanıcının ⋮ > Settings menüsünden kendi
   temasını (Light / Dark) seçebilmesi gerekiyor. Sadece bize ait olmayan
   "Deploy", durum rozeti ve renkli çizgi kaldırılır.
   ======================================================================= */
header[data-testid="stHeader"] {{
    background: transparent !important;
    height: 2.6rem;
}}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stStatusWidget"] {{ display: none !important; }}
.stDeployButton, [data-testid="stAppDeployButton"] {{ display: none !important; }}
footer {{ visibility: hidden; display: none; }}
.viewerBadge_container__1QSob, .viewerBadge_link__qRIco {{ display: none !important; }}
a[href^="https://streamlit.io"] {{ display: none !important; }}

.block-container {{
    padding-top: 2.4rem !important;
    padding-bottom: 3rem !important;
    max-width: 1500px;
}}

/* =======================================================================
   2) TİPOGRAFİ — yazılar daha büyük ve okunaklı
   (renk verilmez; Streamlit temasından gelir)
   ======================================================================= */
h1 {{
    font-weight: 800 !important;
    font-size: 2.1rem !important;
    letter-spacing: -.6px;
    padding-bottom: .5rem;
    margin-bottom: .25rem !important;
    border-bottom: 3px solid {r['vurgu']};
}}
h2 {{ font-weight: 700 !important; font-size: 1.6rem !important; }}
h3 {{ font-weight: 700 !important; font-size: 1.35rem !important; }}
h4, h5 {{ font-weight: 700 !important; font-size: 1.15rem !important; }}

[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li {{
    font-size: 1.02rem;
    line-height: 1.65;
}}
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] {{
    font-size: .92rem !important;
    opacity: .78;
}}

/* Widget etiketleri (Parça, Tür, Çap ... ) */
[data-testid="stWidgetLabel"] p,
.stCheckbox label p, .stRadio label p {{
    font-size: 1.02rem !important;
    font-weight: 600 !important;
}}

/* =======================================================================
   3) SOL MENÜ
   Koyu panel ZORLAMASI kaldırıldı (beyaz temada yazıları görünmez
   yapıyordu). Yerine her iki temada çalışan saydam vurgu katmanı.
   ======================================================================= */
section[data-testid="stSidebar"] {{
    background: linear-gradient(180deg,
        rgba(61,126,191,.10) 0%,
        rgba(128,128,128,.07) 100%);
    border-right: 1px solid {_CIZGI_SOLUK};
}}
section[data-testid="stSidebar"] h1 {{
    font-size: 1.85rem !important;
    letter-spacing: 1.5px;
    color: {r['vurgu']} !important;
    border-bottom: 2px solid {_CIZGI};
}}
section[data-testid="stSidebar"] hr {{ border-color: {_CIZGI_SOLUK}; }}

/* Menü seçenekleri — tıklaması kolay, büyük satırlar */
section[data-testid="stSidebar"] [role="radiogroup"] {{ gap: .15rem; }}
section[data-testid="stSidebar"] [role="radiogroup"] label {{
    padding: .5rem .6rem;
    border-radius: 8px;
    border: 1px solid transparent;
    transition: background .15s ease, border-color .15s ease;
}}
section[data-testid="stSidebar"] [role="radiogroup"] label p {{
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}}
section[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: rgba(61,126,191,.14);
    border-color: {_CIZGI_SOLUK};
}}

section[data-testid="stSidebar"] [data-testid="stMetricValue"] {{
    font-size: 1.5rem !important;
}}
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] p {{
    font-size: .8rem !important;
    text-transform: uppercase;
    letter-spacing: .5px;
    opacity: .8;
}}

/* =======================================================================
   4) BUTONLAR
   ======================================================================= */
.stButton > button, .stDownloadButton > button,
.stFormSubmitButton > button, [data-testid="stPopoverButton"] {{
    border-radius: 9px;
    padding: .5rem 1.05rem;
    font-weight: 600;
    border: 1px solid {_CIZGI};
    background: {_KART};
    transition: all .15s ease;
}}
.stButton > button p, .stDownloadButton > button p,
.stFormSubmitButton > button p, [data-testid="stPopoverButton"] p {{
    font-size: 1.02rem !important;
    font-weight: 600 !important;
}}
.stButton > button:hover, .stDownloadButton > button:hover,
.stFormSubmitButton > button:hover,
[data-testid="stPopoverButton"]:hover {{
    border-color: {r['vurgu']};
    background: rgba(61,126,191,.12);
    transform: translateY(-1px);
}}
/* Ana işlem butonu */
.stButton > button[kind="primary"],
.stFormSubmitButton > button[kind="primary"] {{
    background: {r['vurgu_dolgu']};
    border: 1px solid {r['vurgu_dolgu']};
    color: #FFFFFF !important;
    box-shadow: 0 2px 10px rgba(61,126,191,.32);
}}
.stButton > button[kind="primary"] p,
.stFormSubmitButton > button[kind="primary"] p {{ color: #FFFFFF !important; }}
.stButton > button[kind="primary"]:hover,
.stFormSubmitButton > button[kind="primary"]:hover {{
    background: {r['vurgu_koyu']};
    border-color: {r['vurgu_koyu']};
}}
.stButton > button:disabled {{ opacity: .45; }}

/* =======================================================================
   5) GİRDİ ALANLARI ve SEÇİM KUTULARI (en çok tıklanan yerler)
   ======================================================================= */
.stTextInput input, .stNumberInput input, .stTextArea textarea,
.stDateInput input {{
    font-size: 1.05rem !important;
    padding: .5rem .7rem !important;
}}
.stTextInput input:focus, .stNumberInput input:focus,
.stTextArea textarea:focus {{
    box-shadow: 0 0 0 2px rgba(61,126,191,.28) !important;
}}

/* Selectbox / multiselect — kapalı hâli */
[data-baseweb="select"] {{ font-size: 1.05rem !important; }}
[data-baseweb="select"] > div {{
    min-height: 2.9rem;
    border-radius: 9px !important;
    border-color: {_CIZGI} !important;
}}
[data-baseweb="select"] div[value], [data-baseweb="select"] span,
[data-baseweb="select"] input {{
    font-size: 1.05rem !important;
    font-weight: 500;
}}
[data-baseweb="select"]:hover > div {{ border-color: {r['vurgu']} !important; }}

/* Selectbox — açılan liste: satırlar büyük ve ferah */
[data-baseweb="popover"] [role="option"],
[data-baseweb="popover"] li {{
    font-size: 1.05rem !important;
    padding-top: .55rem !important;
    padding-bottom: .55rem !important;
}}
[data-baseweb="menu"] {{ border-radius: 10px; }}

/* Çoklu seçim etiketleri */
[data-baseweb="tag"] {{ font-size: .95rem !important; border-radius: 6px; }}

/* Sayı girişi +/- düğmeleri biraz büyütülür */
.stNumberInput button {{ min-width: 2.2rem; }}

/* Vurgu rengini sabitle: kullanıcı yerleşik "Dark"/"Light" temasını seçtiğinde
   config.toml'daki primaryColor devre dışı kalır; onay kutusu / seçenek
   düğmesi Valvos mavisi yerine Streamlit'in varsayılan rengine döner.
   Aşağıdaki kurallar hangi tema seçilirse seçilsin maviyi korur. */
* {{ accent-color: {r['vurgu']}; }}
[data-baseweb="checkbox"] span[aria-checked="true"],
[data-baseweb="checkbox"] div[data-checked="true"],
[data-baseweb="radio"] div[aria-checked="true"] > div:first-child {{
    background-color: {r['vurgu']} !important;
    border-color: {r['vurgu']} !important;
}}
[data-testid="stSlider"] [role="slider"] {{ background-color: {r['vurgu']} !important; }}
[data-baseweb="select"] > div:focus-within {{
    border-color: {r['vurgu']} !important;
    box-shadow: 0 0 0 2px rgba(61,126,191,.28) !important;
}}

/* =======================================================================
   6) TABLOLAR
   Not: st.dataframe hücre metnini tuvale (canvas) çizdiği için hücre
   yazı boyutu CSS ile değiştirilemez; bu yüzden tablolar daha ferah
   çerçeve, yuvarlak köşe ve daha yüksek satırlarla okunur kılındı.
   ======================================================================= */
[data-testid="stDataFrame"], [data-testid="stDataFrameResizable"],
[data-testid="stDataEditor"] {{
    border: 1px solid {_CIZGI_SOLUK};
    border-radius: 10px;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
}}
[data-testid="stTable"] td, [data-testid="stTable"] th {{
    font-size: 1rem !important;
    padding: .55rem .7rem !important;
}}

/* =======================================================================
   7) METRİK KARTLARI
   ======================================================================= */
div[data-testid="stMetric"] {{
    background: {_KART};
    border: 1px solid {_CIZGI_SOLUK};
    border-left: 4px solid {r['vurgu']};
    border-radius: 10px;
    padding: .9rem 1.1rem;
    box-shadow: 0 1px 3px rgba(0,0,0,.06);
    transition: box-shadow .15s ease, transform .15s ease;
}}
div[data-testid="stMetric"]:hover {{
    box-shadow: 0 4px 14px rgba(0,0,0,.10);
    transform: translateY(-1px);
}}
div[data-testid="stMetric"] [data-testid="stMetricLabel"] p {{
    font-size: .86rem !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: .5px;
    opacity: .75;
}}
div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
    font-size: 2rem !important;
    font-weight: 700 !important;
}}

/* =======================================================================
   8) SEKMELER
   ======================================================================= */
.stTabs [data-baseweb="tab-list"] {{
    gap: .2rem;
    border-bottom: 2px solid {_CIZGI_SOLUK};
}}
.stTabs [data-baseweb="tab"] {{
    background: transparent;
    border-radius: 9px 9px 0 0;
    padding: .55rem 1.1rem;
}}
.stTabs [data-baseweb="tab"] p {{
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}}
.stTabs [data-baseweb="tab"]:hover {{ background: rgba(128,128,128,.10); }}
.stTabs [aria-selected="true"] {{
    background: {_KART_KOYU};
    border-bottom: 3px solid {r['vurgu']};
}}

/* =======================================================================
   9) UYARI KUTULARI / BİLDİRİM / EXPANDER
   ======================================================================= */
div[data-testid="stAlert"] {{
    border-radius: 10px;
    border-left-width: 5px;
}}
div[data-testid="stAlert"] p {{ font-size: 1.02rem !important; }}

details, [data-testid="stExpander"] {{
    border: 1px solid {_CIZGI_SOLUK} !important;
    border-radius: 10px !important;
    background: {_KART};
}}
[data-testid="stExpander"] summary p {{
    font-size: 1.05rem !important;
    font-weight: 600 !important;
}}

/* Bildirim kutusu (st.popover içeriği) */
[data-testid="stPopoverBody"] {{
    border-radius: 12px;
    min-width: 22rem;
}}

/* Bildirim zili — sağ üstte yuvarlak, dikkat çeken ama sade ikon.
   Uygulamada tek popover olduğu için doğrudan hedeflenebilir. */
[data-testid="stPopoverButton"] {{
    border-radius: 999px !important;
    padding: .4rem 1rem !important;
}}
[data-testid="stPopoverButton"] p {{
    font-size: 1.2rem !important;
    line-height: 1.2 !important;
}}

/* =======================================================================
   10) GİRİŞ (LOGIN) EKRANI
   Kendi koyu zemini olan kapalı bir blok; beyaz yazı burada güvenli.
   ======================================================================= */
.valvos-giris {{
    background: linear-gradient(135deg, {r['marka_koyu']} 0%, {r['vurgu']} 100%);
    border-radius: 14px;
    padding: 2.3rem 1.7rem 1.9rem;
    text-align: center;
    margin-bottom: 1.7rem;
    box-shadow: 0 10px 30px rgba(19,35,58,.28);
}}
.valvos-giris .marka {{
    color: #FFFFFF; font-size: 2.6rem; font-weight: 800;
    letter-spacing: 8px; margin: 0; line-height: 1.1;
}}
.valvos-giris .cizgi {{
    width: 64px; height: 3px; background: #FFFFFF;
    margin: .8rem auto .75rem; opacity: .7; border-radius: 2px;
}}
.valvos-giris .alt {{
    color: #D4E2F2; font-size: .86rem; margin: 0;
    text-transform: uppercase; letter-spacing: 2.4px;
}}
.valvos-dipnot {{
    text-align: center; opacity: .65;
    font-size: .85rem; margin-top: 2rem;
    padding-top: 1rem; border-top: 1px solid {_CIZGI_SOLUK};
}}
"""


def _css():
    """CSS'i Streamlit'e güvenle verilebilecek tek bir <style> bloğuna sarar.

    DİKKAT — buraya <link>, <script> vb. BAŞKA bir etiket EKLEMEYİN:

    Streamlit, st.markdown içeriğini CommonMark kurallarıyla işler. Orada
    <style> ayrıcalıklı bir etikettir: blok </style> görülene kadar olduğu
    gibi aktarılır. <link> ise öyle değil — onunla başlayan HTML bloğu İLK BOŞ
    SATIRDA kapanır ve geri kalan CSS artık HTML sayılmayıp ekrana düz yazı
    olarak basılır (giriş ekranında CSS metninin görünmesinin sebebi buydu).

    Bu yüzden: yazı tipi <link> ile değil CSS'in ilk satırındaki @import ile
    yükleniyor, <style> bloğun en başında duruyor ve ekstra güvenlik olarak
    boş satırlar temizlenip her şey tek parça gönderiliyor.
    """
    satirlar = [s for s in _govde().splitlines() if s.strip()]
    return "<style>" + "\n".join(satirlar) + "</style>"


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
