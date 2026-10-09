# -*- coding: utf-8 -*-
"""
Valvos - Stok Takip Sistemi (BOM / Ürün Reçetesi mantığı)

Çalıştırmak için:  streamlit run app.py
veya Windows'ta:   baslat.bat dosyasına çift tıkla
"""

import os
import time

import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Valvos | Stok Yönetimi",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
    # Streamlit'in hazır yardım/hata bildirim menülerini kaldır
    menu_items={"Get help": None, "Report a Bug": None, "About": None},
)


# Not: database.py, veritabanı adresini st.secrets["DATABASE_URL"] üzerinden
# kendisi okur. st.secrets'e dokunmak bir Streamlit komutu sayıldığı için bu
# import'lar set_page_config çağrısından SONRA gelmek zorundadır.
import bom            # noqa: E402
import database as db  # noqa: E402
import tema           # noqa: E402

tema.uygula()

# Veritabanını hazırla. kur_bir_kez() sonucu Streamlit tarafından
# önbelleklenir: şema kurulumu ve kalem tanımları her tıklamada DEĞİL,
# uygulama ömrü boyunca yalnızca bir kez çalışır (hız için kritik).
db.kur_bir_kez()


# ===========================================================================
# GİRİŞ (LOGIN) KAPISI — buradan geçmeden hiçbir ekrana erişilemez
# ===========================================================================

AZAMI_DENEME = 5          # bu kadar yanlış denemeden sonra
KILIT_SURESI = 60         # bu kadar saniye beklenir


def _giris_ekrani():
    """Giriş yapılmadıysa SADECE bu ekran gösterilir."""
    # Login ekranında sol menü hiç görünmesin
    st.markdown(
        "<style>section[data-testid='stSidebar']{display:none;}</style>",
        unsafe_allow_html=True,
    )

    bos_sol, orta, bos_sag = st.columns([1, 1.15, 1])
    with orta:
        tema.giris_basligi()

        kilit_bitis = st.session_state.get("kilit_bitis", 0)
        kalan = int(kilit_bitis - time.time())
        if kalan > 0:
            st.error(
                f"🔒 Çok fazla hatalı deneme yapıldı. "
                f"Lütfen **{kalan} saniye** bekleyin."
            )
            if st.button("Yenile", use_container_width=True):
                st.rerun()
            tema.dipnot("Valvos Vana Sanayi · Yetkisiz erişim yasaktır")
            return

        with st.form("giris_formu", clear_on_submit=False):
            kullanici_adi = st.text_input("Kullanıcı Adı", placeholder="admin")
            sifre = st.text_input("Şifre", type="password", placeholder="••••")
            gonder = st.form_submit_button(
                "🔓 GİRİŞ YAP", type="primary", use_container_width=True
            )

        if gonder:
            kullanici = db.kullanici_dogrula(kullanici_adi, sifre)
            if kullanici:
                st.session_state["kullanici"] = kullanici
                st.session_state["hatali_deneme"] = 0
                st.rerun()
            else:
                st.session_state["hatali_deneme"] = (
                    st.session_state.get("hatali_deneme", 0) + 1
                )
                kalan_hak = AZAMI_DENEME - st.session_state["hatali_deneme"]
                if kalan_hak <= 0:
                    st.session_state["kilit_bitis"] = time.time() + KILIT_SURESI
                    st.session_state["hatali_deneme"] = 0
                    st.rerun()
                st.error(
                    f"❌ Kullanıcı adı veya şifre hatalı. "
                    f"Kalan deneme hakkı: {kalan_hak}"
                )

        st.caption(
            "🎨 Aydınlık / karanlık tema: sağ üstteki **⋮** → **Settings** → "
            "**Theme**"
        )
        tema.dipnot("Valvos Vana Sanayi · Yetkisiz erişim yasaktır")


if "kullanici" not in st.session_state:
    _giris_ekrani()
    st.stop()          # <-- Giriş yapılmadıysa kodun gerisi HİÇ çalışmaz

KULLANICI = st.session_state["kullanici"]
YONETICI_MI = KULLANICI["rol"] == "yonetici"


# ---------------------------------------------------------------------------
# YARDIMCI FONKSİYONLAR
# ---------------------------------------------------------------------------

def parca_etiketi(p):
    return bom.parca_adi(p["kategori"], p["varyant"], p["dn"])


def bildirim_zili(kritikler):
    """Sağ üst köşedeki bildirim ikonu (🔔).

    Kritik seviyesi 0'dan büyük olup stoğu bu seviyeye inmiş kalemleri
    gösterir. Kritik seviyesi 0 olan kalemler takip edilmez, bu yüzden
    gereksiz uyarı çıkmaz.
    """
    adet = len(kritikler)
    etiket = f"🔔 ({adet})" if adet else "🔔"

    if adet:
        # Uyarı varken zil KIRMIZI görünür. Renk burada veriliyor çünkü
        # yalnızca uyarı olduğunda geçerli; tema.py sabit renk vermez.
        st.markdown(
            "<style>"
            '[data-testid="stPopoverButton"]{'
            "border-color:#DC4C4C !important;"
            "background:rgba(220,76,76,.16) !important;"
            "box-shadow:0 0 0 3px rgba(220,76,76,.14);"
            "}"
            "</style>",
            unsafe_allow_html=True,
        )

    with st.popover(etiket, use_container_width=True):
        if not adet:
            st.markdown("##### 🔔 Bildirimler")
            st.success("Kritik seviyenin altına düşen kalem yok.")
            st.caption(
                "Bir kalem için uyarı almak istiyorsanız **⚙️ Ayarlar** "
                "ekranından o kaleme 0'dan büyük bir kritik seviye girin."
            )
        else:
            st.markdown(f"##### 🔔 {adet} kalem kritik seviyede")
            st.caption("Stoğu kritik seviyeye inen kalemler — sipariş verilmeli:")
            for k in kritikler:
                st.markdown(
                    f"🔴 **{parca_etiketi(k)}**  \n"
                    f"&nbsp;&nbsp;&nbsp;&nbsp;Stok: **{k['stok']}** / "
                    f"Kritik seviye: **{k['kritik_seviye']}**"
                )
            st.caption(
                "Eşikleri **⚙️ Ayarlar > Kritik Stok Seviyeleri** "
                "ekranından değiştirebilirsiniz."
            )


def parcalar_df(kategori=None):
    # HIZ: her kategori sekmesi için ayrı sorgu atmak yerine TÜM liste bir kez
    # (önbellekten) okunup bellekte süzülür. Gösterge panelinde 6 sorgu yerine
    # 1 sorgu gider.
    kayitlar = db.parcalar()
    if kategori:
        kayitlar = [p for p in kayitlar if p["kategori"] == kategori]
    if not kayitlar:
        return pd.DataFrame()
    df = pd.DataFrame(kayitlar)
    df["Parça"] = df.apply(parca_etiketi, axis=1)
    df["Kategori"] = df["kategori"].map(bom.kategori_adi)
    df["Durum"] = df.apply(
        lambda r: "🔴 Kritik" if r["stok"] <= r["kritik_seviye"] else "🟢 Yeterli",
        axis=1,
    )
    return df


def indir_butonu(df, dosya_adi, etiket="⬇️ Excel/CSV olarak indir"):
    if df.empty:
        return
    st.download_button(
        etiket,
        data=df.to_csv(index=False, sep=";").encode("utf-8-sig"),
        file_name=dosya_adi,
        mime="text/csv",
    )


# ---------------------------------------------------------------------------
# KENAR ÇUBUĞU (MENÜ)
# ---------------------------------------------------------------------------

st.sidebar.title("🔧 VALVOS")
st.sidebar.caption("Vana Üretim & Stok Yönetimi")

_rol_etiketi = "Yönetici" if YONETICI_MI else "Kullanıcı"
st.sidebar.markdown(
    f"👤 **{KULLANICI['kullanici_adi']}** &nbsp;·&nbsp; `{_rol_etiketi}`"
)
if st.sidebar.button("🚪 Çıkış Yap", use_container_width=True):
    st.session_state.clear()
    st.rerun()
st.sidebar.divider()

# Menü içeriği role göre değişir: "Sistem Yönetimi" SADECE yöneticide görünür.
MENU = [
    "📊 Gösterge Paneli",
    "📥 Hammadde Girişi",
    "🏭 Ürün Çıkışı (Satış/Üretim)",
    "📜 Geçmiş / Kayıtlar",
    "⚙️ Ayarlar",
    "🔑 Şifre Değiştir",
]
if YONETICI_MI:
    MENU.append("🛡️ Sistem Yönetimi")

sayfa = st.sidebar.radio("Menü", MENU, label_visibility="collapsed")

_ozet = db.ozet()
st.sidebar.divider()
st.sidebar.metric("Toplam Hammadde Stoğu", f"{_ozet['toplam_stok']:,} adet".replace(",", "."))
st.sidebar.metric("Üretilen Vana", f"{_ozet['uretilen_adet']:,} adet".replace(",", "."))
if _ozet["kritik"]:
    st.sidebar.error(f"⚠️ {_ozet['kritik']} kalem kritik seviyede")
else:
    st.sidebar.success("Tüm stoklar yeterli")

# Tema seçimi Streamlit'in kendi menüsünde; koddan değiştirilemez, bu yüzden
# kullanıcıya nerede olduğu söylenir.
st.sidebar.divider()
st.sidebar.caption(
    "🎨 **Tema:** sağ üstteki **⋮** düğmesi → **Settings** → **Theme** "
    "bölümünden *Light* (aydınlık) veya *Dark* (karanlık) seçebilirsiniz. "
    "Yazılar her iki temada da okunur."
)

# ---------------------------------------------------------------------------
# ÜST ŞERİT — sağ üstte bildirim zili
# ---------------------------------------------------------------------------
# Kritik kalem listesi her ekranda gerekir (zil + gösterge paneli); tek yerde
# okunup paylaşılır, böylece aynı sorgu iki kez gitmez.
_kritikler = db.kritik_parcalar()

_bos, _ust_sag = st.columns([6, 1])
with _ust_sag:
    bildirim_zili(_kritikler)

# Fabrika şifresi hâlâ kullanılıyorsa her ekranda hatırlat
if KULLANICI.get("varsayilan_sifre"):
    st.warning(
        "🔐 **Hesabınız hâlâ fabrika şifresini (1234) kullanıyor.** "
        "Sistem internete açıkken bu güvenli değildir — soldaki menüden "
        "**🔑 Şifre Değiştir** ile yeni bir şifre belirleyin."
    )


# ===========================================================================
# 1) GÖSTERGE PANELİ
# ===========================================================================

if sayfa == "📊 Gösterge Paneli":
    st.title("📊 Gösterge Paneli")
    st.caption("Mevcut hammadde stokları — 5 ana kalem, çap ve tür bazında")

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Toplam Stok", f"{_ozet['toplam_stok']} adet")
    k2.metric("Kritik Kalem", _ozet["kritik"])
    k3.metric("Üretilen Vana", f"{_ozet['uretilen_adet']} adet")
    k4.metric("Üretim Kaydı", _ozet["uretim_kaydi"])

    kritikler = _kritikler          # üst şeritte zaten okundu
    if kritikler:
        with st.expander(f"⚠️ Kritik seviyedeki {len(kritikler)} kalem (sipariş verilmeli)", expanded=True):
            kdf = pd.DataFrame(kritikler)
            kdf["Parça"] = kdf.apply(parca_etiketi, axis=1)
            st.dataframe(
                kdf[["Parça", "stok", "kritik_seviye"]].rename(
                    columns={"stok": "Mevcut", "kritik_seviye": "Kritik Seviye"}
                ),
                use_container_width=True,
                hide_index=True,
            )

    st.divider()

    sekmeler = st.tabs(
        ["📋 Tüm Stoklar"] + [bom.kategori_adi(k) for k in bom.KATEGORI_SIRASI]
    )

    with sekmeler[0]:
        df = parcalar_df()
        sutun1, sutun2 = st.columns([1, 1])
        with sutun1:
            kat_filtre = st.multiselect(
                "Kategori filtresi",
                [bom.kategori_adi(k) for k in bom.KATEGORI_SIRASI],
            )
        with sutun2:
            dn_filtre = st.multiselect("Çap (DN) filtresi", bom.DN_LISTESI)

        gorunum = df.copy()
        if kat_filtre:
            gorunum = gorunum[gorunum["Kategori"].isin(kat_filtre)]
        if dn_filtre:
            gorunum = gorunum[gorunum["dn"].isin(dn_filtre)]
        if st.checkbox("Sadece stoğu olanları göster"):
            gorunum = gorunum[gorunum["stok"] > 0]

        tablo = gorunum[["Kategori", "varyant", "dn", "stok", "kritik_seviye", "Durum"]].rename(
            columns={
                "varyant": "Tür",
                "dn": "Çap (DN)",
                "stok": "Stok",
                "kritik_seviye": "Kritik Seviye",
            }
        )
        st.dataframe(tablo, use_container_width=True, hide_index=True, height=420)
        indir_butonu(tablo, "valvos_stok.csv")

    for i, kategori in enumerate(bom.KATEGORI_SIRASI, start=1):
        with sekmeler[i]:
            kdf = parcalar_df(kategori)
            pivot = kdf.pivot_table(
                index="dn", columns="varyant", values="stok", aggfunc="sum", fill_value=0
            )
            pivot.index.name = "Çap (DN)"
            if list(pivot.columns) == [bom.YOK]:
                pivot.columns = ["Stok (adet)"]
            pivot.columns.name = None
            st.markdown(f"**{bom.kategori_adi(kategori)}** — çap / tür kırılımı")
            st.dataframe(pivot, use_container_width=True)
            st.caption(f"Toplam: {int(kdf['stok'].sum())} adet")


# ===========================================================================
# 2) HAMMADDE GİRİŞİ
# ===========================================================================

elif sayfa == "📥 Hammadde Girişi":
    st.title("📥 Hammadde Girişi")
    st.caption("Tedarikçiden gelen malzemeyi stoka ekle veya sayım sonrası düzelt")

    sek1, sek2, sek3 = st.tabs(
        ["➕ Tek Kalem Girişi", "📦 Toplu Giriş (irsaliye)", "✏️ Sayım Düzeltme"]
    )

    # --- Tek kalem ---
    with sek1:
        if "son_giris" in st.session_state:
            st.success("✅ " + st.session_state.pop("son_giris"))

        c1, c2, c3, c4 = st.columns([2, 2, 1, 1])
        kategori_ad = c1.selectbox(
            "Parça", [bom.kategori_adi(k) for k in bom.KATEGORI_SIRASI]
        )
        kategori = next(
            k for k in bom.KATEGORI_SIRASI if bom.kategori_adi(k) == kategori_ad
        )
        varyantlar = bom.KATEGORILER[kategori][1]
        if varyantlar == [bom.YOK]:
            varyant = bom.YOK
            c2.text_input("Tür", value="Tür seçeneği yok", disabled=True)
        else:
            varyant = c2.selectbox("Tür", varyantlar)
        dn = c3.selectbox("Çap (DN)", bom.DN_LISTESI)
        adet = c4.number_input("Gelen Adet", min_value=1, max_value=100000, value=10, step=1)
        aciklama = st.text_input(
            "Açıklama (tedarikçi / irsaliye no — opsiyonel)",
            placeholder="Örn: Demir Döküm - İrs. 2024/581",
        )

        mevcut = db.parca_getir(kategori, varyant, dn)
        mevcut_stok = mevcut["stok"] if mevcut else 0
        st.info(
            f"**{bom.parca_adi(kategori, varyant, dn)}** — mevcut stok: "
            f"**{mevcut_stok} adet** → giriş sonrası: **{mevcut_stok + int(adet)} adet**"
        )

        if st.button("➕ Stoka Ekle", type="primary", use_container_width=True):
            try:
                yeni = db.stok_girisi(mevcut["id"], int(adet), aciklama)
                st.session_state["son_giris"] = (
                    f"Stoka {int(adet)} adet "
                    f"**{bom.parca_adi(kategori, varyant, dn)}** eklendi. "
                    f"Yeni stok: **{yeni} adet**"
                )
                st.rerun()
            except Exception as hata:
                st.error(f"Hata: {hata}")

    # --- Toplu giriş ---
    with sek2:
        st.caption(
            "Bir kategori seç, gelen adetleri **Gelen Adet** sütununa yaz ve kaydet. "
            "Sadece 0'dan büyük satırlar işlenir."
        )
        kategori_ad2 = st.selectbox(
            "Kategori", [bom.kategori_adi(k) for k in bom.KATEGORI_SIRASI], key="toplu_kat"
        )
        kategori2 = next(
            k for k in bom.KATEGORI_SIRASI if bom.kategori_adi(k) == kategori_ad2
        )
        tdf = parcalar_df(kategori2)
        duzenlenebilir = tdf[["id", "Parça", "stok"]].copy()
        duzenlenebilir["Gelen Adet"] = 0
        duzenlenebilir = duzenlenebilir.rename(columns={"stok": "Mevcut Stok"})

        sonuc = st.data_editor(
            duzenlenebilir,
            use_container_width=True,
            hide_index=True,
            height=420,
            disabled=["id", "Parça", "Mevcut Stok"],
            column_config={
                "id": None,
                "Gelen Adet": st.column_config.NumberColumn(
                    min_value=0, max_value=100000, step=1
                ),
            },
            key=f"editor_{kategori2}",
        )
        if "son_toplu" in st.session_state:
            st.success("✅ " + st.session_state.pop("son_toplu"))
        toplu_aciklama = st.text_input("İrsaliye / açıklama", key="toplu_aciklama")
        if st.button("💾 Toplu Girişi Kaydet", type="primary"):
            islenen = 0
            for _, satir in sonuc.iterrows():
                gelen = int(satir["Gelen Adet"] or 0)
                if gelen > 0:
                    db.stok_girisi(int(satir["id"]), gelen, toplu_aciklama)
                    islenen += 1
            if islenen:
                st.session_state["son_toplu"] = f"{islenen} kalem için giriş yapıldı."
                st.rerun()
            else:
                st.warning("Hiçbir satıra adet girilmemiş.")

    # --- Sayım düzeltme ---
    with sek3:
        st.caption(
            "Fiziksel sayım sonucu stok farklıysa doğru değeri buradan gir. "
            "Fark log'a **DÜZELTME** olarak kaydedilir."
        )
        if "son_duzeltme" in st.session_state:
            st.success("✅ " + st.session_state.pop("son_duzeltme"))
        tum = db.parcalar()
        secenekler = {parca_etiketi(p): p for p in tum}
        secim = st.selectbox("Parça", list(secenekler.keys()), key="duzelt_secim")
        hedef = secenekler[secim]
        c1, c2 = st.columns(2)
        c1.metric("Sistemdeki Stok", f"{hedef['stok']} adet")
        yeni_stok = c2.number_input(
            "Sayımda Bulunan (doğru) Adet",
            min_value=0,
            max_value=1000000,
            value=int(hedef["stok"]),
            step=1,
        )
        duzelt_aciklama = st.text_input("Düzeltme nedeni", key="duzelt_aciklama")
        if st.button("✏️ Stoğu Düzelt"):
            db.stok_duzeltme(hedef["id"], int(yeni_stok), duzelt_aciklama)
            st.session_state["son_duzeltme"] = (
                f"**{secim}** stoğu {hedef['stok']} → {int(yeni_stok)} olarak güncellendi."
            )
            st.rerun()


# ===========================================================================
# 3) ÜRÜN ÇIKIŞI (REÇETE DÜŞÜMÜ)
# ===========================================================================

elif sayfa == "🏭 Ürün Çıkışı (Satış/Üretim)":
    st.title("🏭 Ürün Çıkışı — Satış / Üretim")
    st.caption(
        "Vanayı seç, adedi gir. Onayladığında reçetedeki 5 hammadde otomatik düşülür."
    )

    c1, c2, c3, c4 = st.columns(4)
    dn = c1.selectbox("1️⃣ Çap (DN)", bom.DN_LISTESI, index=bom.DN_LISTESI.index(100))
    conta = c2.selectbox("2️⃣ Conta Türü", bom.CONTA_TURLERI)
    klepe = c3.selectbox("3️⃣ Klepe Türü", bom.KLEPE_TURLERI)
    kontrol = c4.selectbox("4️⃣ Kontrol Mekanizması", bom.KONTROL_TURLERI)

    c5, c6 = st.columns([1, 3])
    adet = c5.number_input("Adet", min_value=1, max_value=10000, value=1, step=1)
    musteri = c6.text_input("Müşteri / Sipariş No (opsiyonel)", placeholder="Örn: ACME A.Ş. - Sip. 1001")

    ad = bom.urun_adi(dn, conta, klepe, kontrol)
    kapasite = db.uretilebilir_adet(dn, conta, klepe, kontrol)

    st.divider()
    st.subheader(f"🔧 {ad}")
    if kapasite >= adet:
        st.success(f"✅ Mevcut stokla bu üründen en fazla **{kapasite} adet** üretilebilir.")
    elif kapasite > 0:
        st.warning(f"⚠️ Mevcut stokla en fazla **{kapasite} adet** üretilebilir ({adet} adet istendi).")
    else:
        st.error("❌ Bu konfigürasyon için stok yok. Önce hammadde girişi yapın.")

    durum = db.recete_durumu(dn, conta, klepe, kontrol, int(adet))
    rdf = pd.DataFrame(durum)
    rdf["Durum"] = rdf["yeterli"].map({True: "🟢 Yeterli", False: "🔴 YETERSİZ"})
    st.markdown("##### Ürün Reçetesi (BOM) — düşülecek hammaddeler")
    st.dataframe(
        rdf[["ad", "adet", "mevcut_stok", "kalan_stok", "eksik", "Durum"]].rename(
            columns={
                "ad": "Hammadde",
                "adet": "Gereken",
                "mevcut_stok": "Mevcut Stok",
                "kalan_stok": "İşlem Sonrası",
                "eksik": "Eksik",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    eksikler = [d for d in durum if not d["yeterli"]]
    st.divider()

    if eksikler:
        st.error(
            "Stok yetersiz olduğu için işlem yapılamaz. Eksik kalemler: "
            + ", ".join(f"**{d['ad']}** ({d['eksik']} adet)" for d in eksikler)
        )
        st.button("🚫 Stoktan Düş", disabled=True, use_container_width=True)
    else:
        onay = st.checkbox(
            f"**{adet} adet {ad}** ürettiğimi/sattığımı onaylıyorum — 5 kalem stoktan düşülecek."
        )
        if st.button(
            "✅ ONAYLA ve Stoktan Düş",
            type="primary",
            disabled=not onay,
            use_container_width=True,
        ):
            basarili, mesaj, detay = db.uretim_yap(
                dn, conta, klepe, kontrol, int(adet), musteri
            )
            if basarili:
                st.session_state["son_islem"] = {"mesaj": mesaj, "detay": detay}
                st.rerun()
            else:
                st.error(mesaj)
                if detay:
                    st.dataframe(pd.DataFrame(detay), use_container_width=True, hide_index=True)

    if "son_islem" in st.session_state:
        son = st.session_state.pop("son_islem")
        st.success("✅ " + son["mesaj"])
        st.balloons()
        st.markdown("##### Stoktan düşülen kalemler")
        st.dataframe(
            pd.DataFrame(son["detay"]).rename(
                columns={
                    "ad": "Hammadde",
                    "dusulen": "Düşülen",
                    "onceki_stok": "Önceki Stok",
                    "kalan_stok": "Kalan Stok",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )


# ===========================================================================
# 4) GEÇMİŞ / KAYITLAR
# ===========================================================================

elif sayfa == "📜 Geçmiş / Kayıtlar":
    st.title("📜 Geçmiş / Kayıtlar")

    sek1, sek2 = st.tabs(["🏭 Üretim & Satış Kayıtları", "🔄 Tüm Stok Hareketleri"])

    with sek1:
        if "son_iptal" in st.session_state:
            st.success("✅ " + st.session_state.pop("son_iptal"))
        kayitlar = db.uretimler(500)
        if not kayitlar:
            st.info("Henüz üretim/satış kaydı yok.")
        else:
            udf = pd.DataFrame(kayitlar)
            udf["Durum"] = udf["iptal"].map({0: "✅ Geçerli", 1: "🚫 İptal"})
            tablo = udf[
                ["id", "tarih", "urun_adi", "adet", "musteri", "Durum"]
            ].rename(
                columns={
                    "id": "No",
                    "tarih": "Tarih",
                    "urun_adi": "Ürün",
                    "adet": "Adet",
                    "musteri": "Müşteri",
                }
            )
            st.dataframe(tablo, use_container_width=True, hide_index=True, height=360)
            indir_butonu(tablo, "valvos_uretimler.csv")

            st.divider()
            st.markdown("##### Kayıt detayı / iptal")
            gecerli = [k for k in kayitlar if not k["iptal"]]
            if gecerli:
                etiketler = {
                    f"#{k['id']} — {k['tarih']} — {k['adet']} adet — {k['urun_adi']}": k
                    for k in gecerli
                }
                secim = st.selectbox("Kayıt seç", list(etiketler.keys()))
                secili = etiketler[secim]
                hdf = pd.DataFrame(db.hareketler(uretim_id=secili["id"]))
                if not hdf.empty:
                    hdf["Hammadde"] = hdf.apply(parca_etiketi, axis=1)
                    st.dataframe(
                        hdf[["Hammadde", "adet", "onceki_stok", "sonraki_stok"]].rename(
                            columns={
                                "adet": "Değişim",
                                "onceki_stok": "Önceki",
                                "sonraki_stok": "Sonraki",
                            }
                        ),
                        use_container_width=True,
                        hide_index=True,
                    )
                st.warning(
                    "İptal edilirse bu kayıtta düşülen hammaddeler stoka geri eklenir."
                )
                if st.checkbox(f"#{secili['id']} numaralı kaydı iptal etmek istiyorum"):
                    if st.button("🚫 Kaydı İptal Et ve Stoğu Geri Yükle"):
                        ok, mesaj = db.uretim_iptal(secili["id"])
                        if ok:
                            st.session_state["son_iptal"] = mesaj
                            st.rerun()
                        else:
                            st.error(mesaj)
            else:
                st.caption("İptal edilebilecek geçerli kayıt yok.")

    with sek2:
        hareket = db.hareketler(1000)
        if not hareket:
            st.info("Henüz stok hareketi yok.")
        else:
            hdf = pd.DataFrame(hareket)
            hdf["Hammadde"] = hdf.apply(parca_etiketi, axis=1)
            etiket_map = {
                "GIRIS": "📥 Giriş",
                "CIKIS": "📤 Çıkış (üretim)",
                "DUZELTME": "✏️ Düzeltme",
                "IPTAL": "🔙 İptal/Geri",
            }
            hdf["İşlem"] = hdf["tip"].map(etiket_map).fillna(hdf["tip"])

            tip_filtre = st.multiselect("İşlem türü filtresi", list(etiket_map.values()))
            gorunum = hdf if not tip_filtre else hdf[hdf["İşlem"].isin(tip_filtre)]

            tablo = gorunum[
                ["tarih", "İşlem", "Hammadde", "adet", "onceki_stok", "sonraki_stok", "uretim_id", "aciklama"]
            ].rename(
                columns={
                    "tarih": "Tarih",
                    "adet": "Değişim",
                    "onceki_stok": "Önceki",
                    "sonraki_stok": "Sonraki",
                    "uretim_id": "Üretim No",
                    "aciklama": "Açıklama",
                }
            )
            st.dataframe(tablo, use_container_width=True, hide_index=True, height=480)
            indir_butonu(tablo, "valvos_hareketler.csv")


# ===========================================================================
# 5) AYARLAR
# ===========================================================================

elif sayfa == "⚙️ Ayarlar":
    st.title("⚙️ Ayarlar")

    st.subheader("🔔 Kritik Stok Seviyeleri")
    st.caption(
        "Stok bu değere veya altına düştüğünde sağ üstteki 🔔 bildirim zilinde "
        "ve gösterge panelinde kırmızı uyarı çıkar. "
        "**0 = o kalem için uyarı istemiyorum** (varsayılan). "
        "Değiştirmek için hücreye yazıp kaydet'e basın."
    )
    kategori_ad = st.selectbox(
        "Kategori", [bom.kategori_adi(k) for k in bom.KATEGORI_SIRASI], key="ayar_kat"
    )
    kategori = next(k for k in bom.KATEGORI_SIRASI if bom.kategori_adi(k) == kategori_ad)
    adf = parcalar_df(kategori)
    tablo = adf[["id", "Parça", "stok", "kritik_seviye"]].rename(
        columns={"stok": "Mevcut Stok", "kritik_seviye": "Kritik Seviye"}
    )
    duzenlenen = st.data_editor(
        tablo,
        use_container_width=True,
        hide_index=True,
        height=400,
        disabled=["id", "Parça", "Mevcut Stok"],
        column_config={
            "id": None,
            "Kritik Seviye": st.column_config.NumberColumn(min_value=0, step=1),
        },
        key=f"ayar_editor_{kategori}",
    )
    if st.button("💾 Kritik Seviyeleri Kaydet", type="primary"):
        degisen = 0
        for (_, eski), (_, yeni) in zip(tablo.iterrows(), duzenlenen.iterrows()):
            if int(eski["Kritik Seviye"]) != int(yeni["Kritik Seviye"]):
                db.kritik_seviye_ayarla(int(yeni["id"]), int(yeni["Kritik Seviye"]))
                degisen += 1
        st.success(f"✅ {degisen} kalem güncellendi.") if degisen else st.info("Değişiklik yok.")

    st.divider()
    st.subheader("💾 Yedekleme")
    st.caption(f"Aktif veri kaynağı: `{db.veri_kaynagi()}`")
    if st.button("💾 Şimdi Yedek Al"):
        yol = db.yedek_al()
        st.success(f"✅ Yedek alındı: `{yol}`")

    st.divider()
    st.subheader("ℹ️ Sistem Bilgisi")
    st.markdown(
        f"""
- **Takip edilen kalem sayısı:** {len(db.parcalar())}
  (5 kategori × çap × tür — küçük cıvatalar takip edilmez)
- **Çaplar:** DN {", DN ".join(str(d) for d in bom.DN_LISTESI)}
- **Conta türleri:** {", ".join(bom.CONTA_TURLERI)}
- **Klepe türleri:** {", ".join(bom.KLEPE_TURLERI)}
- **Kontrol mekanizmaları:** {", ".join(bom.KONTROL_TURLERI)}
- **Reçete:** 1 vana = 1 Gövde + 1 Conta + 1 Klepe + 1 Mil + 1 Kontrol mekanizması

Yeni çap veya tür eklemek için `bom.py` dosyasındaki listelere yeni değeri yazıp
uygulamayı yeniden başlatmanız yeterli; yeni kalemler 0 stokla otomatik eklenir.
"""
    )


# ===========================================================================
# 6) ŞİFRE DEĞİŞTİR  (her kullanıcı kendi şifresini değiştirir)
# ===========================================================================

elif sayfa == "🔑 Şifre Değiştir":
    st.title("🔑 Şifre Değiştir")
    st.caption(f"Oturum: **{KULLANICI['kullanici_adi']}**")

    if "sifre_mesaji" in st.session_state:
        st.success("✅ " + st.session_state.pop("sifre_mesaji"))

    sol, sag = st.columns([1.2, 1])
    with sol:
        with st.form("sifre_formu", clear_on_submit=True):
            mevcut = st.text_input("Mevcut Şifreniz", type="password")
            yeni1 = st.text_input("Yeni Şifre", type="password")
            yeni2 = st.text_input("Yeni Şifre (tekrar)", type="password")
            kaydet = st.form_submit_button(
                "🔑 Şifreyi Güncelle", type="primary", use_container_width=True
            )

        if kaydet:
            if yeni1 != yeni2:
                st.error("❌ Yeni şifreler birbiriyle aynı değil.")
            elif yeni1 == db.VARSAYILAN_SIFRE:
                st.error("❌ Fabrika şifresini (1234) yeniden kullanamazsınız.")
            else:
                ok, mesaj = db.sifre_degistir(KULLANICI["id"], yeni1, eski_sifre=mevcut)
                if ok:
                    # Oturumdaki "fabrika şifresi" uyarısını kaldır
                    KULLANICI["varsayilan_sifre"] = False
                    st.session_state["kullanici"] = KULLANICI
                    st.session_state["sifre_mesaji"] = mesaj
                    st.rerun()
                else:
                    st.error("❌ " + mesaj)

    with sag:
        st.info(
            "**Şifre kuralları**\n\n"
            "- En az 4 karakter\n"
            "- Fabrika şifresi (1234) kullanılamaz\n\n"
            "Şifreniz veritabanında **geri çevrilemez biçimde (hash)** saklanır; "
            "sunucuya erişen biri bile şifreyi okuyamaz.\n\n"
            "Şifrenizi unutursanız **admin** hesabından *Sistem Yönetimi* "
            "ekranından sıfırlanabilir."
        )


# ===========================================================================
# 7) SİSTEM YÖNETİMİ  (SADECE rol = yonetici)
# ===========================================================================

elif sayfa == "🛡️ Sistem Yönetimi":
    # Güvenlik: menüde görünmese de ikinci kez rol kontrolü yapılır
    if not YONETICI_MI:
        st.error("⛔ Bu sayfaya erişim yetkiniz yok.")
        st.stop()

    st.title("🛡️ Sistem Yönetimi")
    st.caption("Bu ekran yalnızca **yönetici** rolündeki hesaplara açıktır.")

    y_sek1, y_sek2, y_sek3 = st.tabs(
        ["👥 Kullanıcılar", "💾 Yedekler", "☢️ Tehlikeli İşlemler"]
    )

    # --- Kullanıcı yönetimi ---
    with y_sek1:
        if "kadmin_mesaji" in st.session_state:
            st.success("✅ " + st.session_state.pop("kadmin_mesaji"))

        kullanicilar = db.kullanicilar_listesi()
        kdf = pd.DataFrame(kullanicilar)
        kdf["Rol"] = (
            kdf["rol"]
            .map({"yonetici": "🛡️ Yönetici", "kullanici": "👤 Kullanıcı"})
            .fillna(kdf["rol"])
        )
        st.dataframe(
            kdf[["id", "kullanici_adi", "Rol", "son_giris"]].rename(
                columns={
                    "id": "No",
                    "kullanici_adi": "Kullanıcı Adı",
                    "son_giris": "Son Giriş",
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

        st.divider()
        ek1, ek2 = st.columns(2)

        with ek1:
            st.markdown("##### ➕ Yeni Kullanıcı Ekle")
            with st.form("kullanici_ekle", clear_on_submit=True):
                yeni_ad = st.text_input("Kullanıcı Adı")
                yeni_sifre = st.text_input("Şifre", type="password")
                yeni_rol = st.selectbox(
                    "Rol",
                    ["kullanici", "yonetici"],
                    format_func=lambda r: (
                        "👤 Kullanıcı" if r == "kullanici" else "🛡️ Yönetici"
                    ),
                )
                if st.form_submit_button(
                    "➕ Ekle", type="primary", use_container_width=True
                ):
                    ok, mesaj = db.kullanici_ekle(yeni_ad, yeni_sifre, yeni_rol)
                    if ok:
                        st.session_state["kadmin_mesaji"] = mesaj
                        st.rerun()
                    else:
                        st.error("❌ " + mesaj)

        with ek2:
            st.markdown("##### 🔄 Başkasının Şifresini Sıfırla")
            hedefler = {
                "%s (%s)" % (k["kullanici_adi"], k["rol"]): k for k in kullanicilar
            }
            s_secim = st.selectbox(
                "Kullanıcı", list(hedefler.keys()), key="sifirla_hedef"
            )
            s_yeni = st.text_input("Yeni şifre", type="password", key="sifirla_sifre")
            if st.button("🔄 Şifreyi Sıfırla", use_container_width=True):
                ok, mesaj = db.sifre_degistir(hedefler[s_secim]["id"], s_yeni)
                if ok:
                    st.session_state["kadmin_mesaji"] = (
                        "%s kullanıcısının şifresi değiştirildi."
                        % hedefler[s_secim]["kullanici_adi"]
                    )
                    st.rerun()
                else:
                    st.error("❌ " + mesaj)

            st.markdown("##### 🗑️ Kullanıcı Sil")
            silinebilir = {
                "%s (%s)" % (k["kullanici_adi"], k["rol"]): k
                for k in kullanicilar
                if k["id"] != KULLANICI["id"]
            }
            if silinebilir:
                d_secim = st.selectbox("Silinecek kullanıcı", list(silinebilir.keys()))
                if st.button("🗑️ Sil", use_container_width=True):
                    ok, mesaj = db.kullanici_sil(
                        silinebilir[d_secim]["id"], isteyen_id=KULLANICI["id"]
                    )
                    if ok:
                        st.session_state["kadmin_mesaji"] = mesaj
                        st.rerun()
                    else:
                        st.error("❌ " + mesaj)
            else:
                st.caption("Silinebilecek başka kullanıcı yok.")

    # --- Yedekler ---
    with y_sek2:
        st.markdown("##### 💾 Veritabanı Yedeği")
        st.caption(f"Aktif veri kaynağı: `{db.veri_kaynagi()}`")
        if st.button("💾 Şimdi Yedek Al", type="primary"):
            st.success(f"✅ Yedek alındı: `{db.yedek_al()}`")

        yedek_klasoru = db.yedek_klasoru()
        dosyalar = (
            sorted(os.listdir(yedek_klasoru), reverse=True)
            if os.path.isdir(yedek_klasoru)
            else []
        )
        if dosyalar:
            st.markdown("##### Mevcut yedekler")
            ydf = pd.DataFrame(
                [
                    {
                        "Dosya": d,
                        "Boyut (KB)": round(
                            os.path.getsize(os.path.join(yedek_klasoru, d)) / 1024, 1
                        ),
                    }
                    for d in dosyalar[:30]
                ]
            )
            st.dataframe(ydf, use_container_width=True, hide_index=True)
            with open(os.path.join(yedek_klasoru, dosyalar[0]), "rb") as f:
                st.download_button(
                    "⬇️ En son yedeği bilgisayarıma indir",
                    data=f.read(),
                    file_name=dosyalar[0],
                    mime="application/octet-stream",
                )
        else:
            st.info("Henüz yedek alınmamış.")

    # --- Tehlikeli işlemler ---
    with y_sek3:
        st.markdown("##### ☢️ Geri Alınamaz İşlemler")
        st.caption(
            "Bu bölümdeki işlemler kalıcıdır. Normal kullanımda buraya "
            "girmeniz gerekmez."
        )

        with st.expander("🔴 Tüm Veritabanını Sıfırla — dikkatli olun", expanded=False):
            st.error(
                "**Bu işlem şunları SİLER:**\n"
                "- Tüm üretim / satış kayıtları\n"
                "- Tüm stok hareket geçmişi\n"
                "- Tüm hammadde stok adetleri (hepsi 0 olur)\n\n"
                "**Korunanlar:** kullanıcı hesapları, çap/tür tanımları ve "
                "kritik stok seviyeleri.\n\n"
                "Silmeden hemen önce otomatik olarak bir yedek alınır."
            )
            o1, o2, o3 = st.columns(3)
            o1.metric("Silinecek Üretim Kaydı", _ozet["uretim_kaydi"])
            o2.metric("Sıfırlanacak Stok", f"{_ozet['toplam_stok']} adet")
            o3.metric("Hareket Kaydı", db.hareket_sayisi())

            onay_metni = st.text_input(
                "İşlemi onaylamak için aşağıdaki kutuya büyük harflerle "
                "**SİL** yazın:",
                key="sifirla_onay",
                placeholder="SİL",
            )
            dogru = onay_metni.strip().upper() in ("SİL", "SIL")
            if not dogru and onay_metni.strip():
                st.warning("Onay metni hatalı. Tam olarak **SİL** yazmalısınız.")

            if st.button(
                "☢️ VERİTABANINI KALICI OLARAK SIFIRLA",
                disabled=not dogru,
                use_container_width=True,
            ):
                st.session_state["sifirlama_yedegi"] = db.veritabani_sifirla()
                st.rerun()

        if "sifirlama_yedegi" in st.session_state:
            yedek = st.session_state.pop("sifirlama_yedegi")
            st.success(
                "✅ Veritabanı sıfırlandı. Silmeden önce alınan yedek: "
                f"`{yedek}`\n\nYanlışlıkla sıfırladıysanız bu yedeği "
                "**💾 Yedekler** sekmesinden indirip içeriğini veritabanı "
                "sağlayıcınızın SQL Editor ekranına yapıştırarak geri yükleyebilirsiniz."
            )
