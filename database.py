# -*- coding: utf-8 -*-
"""
Valvos - Veri katmanı (PostgreSQL).

Arayüz (app.py) sadece bu dosyadaki fonksiyonları çağırır; hiçbir yerde ham
SQL yazmaz. Bütün veriler bulutta bir PostgreSQL veritabanında tutulur, bu
yüzden hem evden hem ofisten aynı stok görülür ve Streamlit Cloud uygulamayı
yeniden başlattığında veri SİLİNMEZ.

Bağlantı adresi koda yazılmaz; şu sırayla aranır:
  1) DATABASE_URL ortam değişkeni   (testler / sunucu kurulumları için)
  2) st.secrets["DATABASE_URL"]     (Streamlit Cloud > Secrets veya
                                     yerelde .streamlit/secrets.toml)

Üretim düşümü tek bir transaction içinde yapılır ve ilgili stok satırları
SELECT ... FOR UPDATE ile kilitlenir: 5 hammaddeden biri bile yetersizse
HİÇBİR düşüm gerçekleşmez, iki kişi aynı anda işlem yaparsa stok eksiye
düşmez.
"""

import hashlib
import hmac
import os
import threading
import time
from contextlib import contextmanager
from datetime import datetime

import psycopg
from psycopg.rows import dict_row

import bom


# ---------------------------------------------------------------------------
# BAĞLANTI ADRESİ
# ---------------------------------------------------------------------------

class BaglantiAyariYok(RuntimeError):
    """DATABASE_URL hiçbir yerde bulunamadığında atılır."""


def _adres():
    """Veritabanı adresini ortam değişkeninden veya st.secrets'ten okur.

    İlk bağlantı anında çağrılır (import sırasında değil); böylece
    st.secrets'e erişim Streamlit'in set_page_config çağrısından sonra olur.
    """
    url = (os.environ.get("DATABASE_URL") or "").strip()
    if url:
        return url

    try:
        import streamlit as st

        url = str(st.secrets["DATABASE_URL"]).strip()
    except Exception:
        url = ""

    if not url:
        raise BaglantiAyariYok(
            "Veritabanı adresi (DATABASE_URL) bulunamadı.\n\n"
            "Streamlit Cloud'da:  uygulama ayarları > Secrets bölümüne\n"
            '    DATABASE_URL = "postgresql://..."\n'
            "satırını ekleyin.\n\n"
            "Kendi bilgisayarınızda:  proje klasöründe\n"
            "    .streamlit/secrets.toml\n"
            "dosyasını oluşturup aynı satırı içine yazın.\n"
            "Ayrıntılı anlatım README.md dosyasındadır."
        )
    return url


def veri_kaynagi():
    """Ekranda gösterilecek, şifre İÇERMEYEN veritabanı açıklaması."""
    try:
        url = _adres()
    except BaglantiAyariYok:
        return "Veritabanı adresi tanımlı değil"
    # postgresql://kullanici:SIFRE@sunucu/veritabani?... -> sunucu/veritabani
    kalan = url.split("@")[-1].split("?")[0]
    return "PostgreSQL (bulut): %s" % kalan


def _simdi():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# ---------------------------------------------------------------------------
# TEK PAYLAŞILAN BAĞLANTI
# ---------------------------------------------------------------------------
# Streamlit her tıklamada script'i baştan çalıştırır. Her seferinde yeni bir
# bulut bağlantısı açmak çok yavaş olurdu (TLS el sıkışması + veritabanının
# uykudan uyanması). Bu yüzden tek bağlantı açılır ve kilitle sırayla
# kullanılır. Bağlantı koparsa (ücretsiz planlarda veritabanı 5 dakika
# işlem olmazsa uyur) kendiliğinden yeniden kurulur.

_kilit = threading.RLock()
_conn = None


def _canli_baglanti():
    global _conn
    if _conn is not None and not _conn.closed:
        try:
            _conn.rollback()
            _conn.execute("SELECT 1")
            return _conn
        except Exception:
            try:
                _conn.close()
            except Exception:
                pass
            _conn = None

    # Ücretsiz planlarda veritabanı işlem olmadığında uykuya geçer. Uyanırken
    # ilk bağlantı denemesi zaman aşımına uğrayabildiği için birkaç kez,
    # araya kısa bekleme koyarak deniyoruz; kullanıcı hata görmesin.
    son_hata = None
    for deneme in range(3):
        try:
            _conn = _yeni_baglanti()
            return _conn
        except psycopg.OperationalError as hata:
            son_hata = hata
            if deneme < 2:
                time.sleep(1.5 * (deneme + 1))
    raise son_hata


def _yeni_baglanti():
    conn = psycopg.connect(
        _adres(),
        row_factory=dict_row,
        connect_timeout=10,
        autocommit=False,
        # Veritabanı uykudan uyanırken bağlantı düşmesin
        keepalives=1,
        keepalives_idle=30,
        # Neon ve Supabase'in bağlantı havuzları (PgBouncer) "prepared
        # statement" özelliğini her modda desteklemez; kapatıyoruz ki
        # uygulama her iki sağlayıcıda da sorunsuz çalışsın.
        prepare_threshold=None,
    )

    # Tabloların arandığı şemayı açıkça sabitle.
    # Bağlantı havuzu kullanılan kurulumlarda (Neon/Supabase pooler), başka
    # bir istemcinin çalıştırdığı "SET search_path" paylaşılan sunucu
    # bağlantısında kalabilir ve uygulamaya "tablo bulunamadı" hatası olarak
    # yansır. Bunu her bağlantıda baştan ayarlayarak bağışık hale getiriyoruz.
    conn.execute("SET search_path TO public")
    conn.commit()
    return conn


@contextmanager
def baglanti():
    """Tüm veritabanı işlemleri bu blok içinde yapılır.

    Blok hatasız biterse açık kalan okuma işlemi temizce kapatılır; hata
    olursa yapılan her şey geri alınır (rollback).
    """
    with _kilit:
        conn = _canli_baglanti()
        try:
            yield Islem(conn)
            conn.rollback()
        except Exception:
            try:
                conn.rollback()
            except Exception:
                pass
            raise


class Islem:
    """psycopg bağlantısının üzerine ince bir sarmalayıcı.

    database.py içinde SQL'ler "?" yer tutucusu ile yazılır; PostgreSQL "%s"
    beklediği için çeviri burada yapılır. Böylece sorgular okunaklı kalır ve
    değerler ASLA SQL metnine gömülmez (SQL injection koruması).
    """

    def __init__(self, conn):
        self._conn = conn

    def execute(self, sql, args=None):
        imlec = self._conn.cursor()
        if args:
            # Değerler SQL metnine gömülmez, parametre olarak gönderilir
            imlec.execute(sql.replace("?", "%s"), args)
        else:
            # Parametre yoksa sorgu olduğu gibi gider; böylece SQL içindeki
            # yüzde işaretleri (örn. LIKE 'A%') yer tutucu sanılmaz.
            imlec.execute(sql)
        return imlec

    def coklu_execute(self, sql, args_listesi):
        imlec = self._conn.cursor()
        imlec.executemany(sql.replace("?", "%s"), list(args_listesi))
        return imlec

    def betik(self, sql_metni):
        """Birden fazla CREATE ifadesini sırayla çalıştırır."""
        for parca in sql_metni.split(";"):
            if parca.strip():
                self.execute(parca)

    def ekle_ve_id(self, sql, args=()):
        """INSERT yapar ve oluşan kaydın id'sini döndürür."""
        return self.execute(sql + " RETURNING id", args).fetchone()["id"]

    # --- İşlem (transaction) yönetimi ------------------------------------
    def islem_basla(self):
        """Yazma işlemi başlat (psycopg bağlantısı zaten örtük işlem açar)."""

    def islem_bitir(self):
        self._conn.commit()

    def islem_geri_al(self):
        try:
            self._conn.rollback()
        except Exception:
            pass

    # --- Satır kilidi -----------------------------------------------------
    def kilit(self):
        """Stok okunurken satırı kilitleyen SQL eki.

        İki kişi aynı anda aynı parçayı düşmeye çalışırsa stoğun iki kez
        harcanmasını (double-spend) engeller.
        """
        return " FOR UPDATE"


# ---------------------------------------------------------------------------
# ŞEMA
# ---------------------------------------------------------------------------

SEMA = """
CREATE TABLE IF NOT EXISTS parcalar (
    id            SERIAL  PRIMARY KEY,
    kategori      TEXT    NOT NULL,
    varyant       TEXT    NOT NULL,
    dn            INTEGER NOT NULL,
    stok          INTEGER NOT NULL DEFAULT 0,
    kritik_seviye INTEGER NOT NULL DEFAULT 5,
    UNIQUE (kategori, varyant, dn)
);

CREATE TABLE IF NOT EXISTS uretimler (
    id        SERIAL  PRIMARY KEY,
    tarih     TEXT    NOT NULL,
    urun_adi  TEXT    NOT NULL,
    dn        INTEGER NOT NULL,
    conta     TEXT    NOT NULL,
    klepe     TEXT    NOT NULL,
    kontrol   TEXT    NOT NULL,
    adet      INTEGER NOT NULL,
    musteri   TEXT    NOT NULL DEFAULT '',
    aciklama  TEXT    NOT NULL DEFAULT '',
    iptal     INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS hareketler (
    id           SERIAL  PRIMARY KEY,
    tarih        TEXT    NOT NULL,
    tip          TEXT    NOT NULL,
    parca_id     INTEGER NOT NULL REFERENCES parcalar(id),
    adet         INTEGER NOT NULL,
    onceki_stok  INTEGER NOT NULL,
    sonraki_stok INTEGER NOT NULL,
    uretim_id    INTEGER REFERENCES uretimler(id),
    aciklama     TEXT    NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS kullanicilar (
    id            SERIAL  PRIMARY KEY,
    kullanici_adi TEXT    NOT NULL,
    sifre         TEXT    NOT NULL,
    rol           TEXT    NOT NULL DEFAULT 'kullanici',
    son_giris     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_kullanici_adi
    ON kullanicilar (LOWER(kullanici_adi));
CREATE INDEX IF NOT EXISTS ix_hareket_tarih  ON hareketler(tarih DESC);
CREATE INDEX IF NOT EXISTS ix_hareket_uretim ON hareketler(uretim_id);
CREATE INDEX IF NOT EXISTS ix_uretim_tarih   ON uretimler(tarih DESC)
"""


def kur():
    """Tabloları oluşturur ve bom.py'de tanımlı eksik kalemleri 0 stokla ekler.

    Her açılışta güvenle çağrılabilir; mevcut stokları ASLA bozmaz.
    """
    with baglanti() as conn:
        conn.betik(SEMA)
        conn.islem_basla()
        conn.coklu_execute(
            "INSERT INTO parcalar (kategori, varyant, dn, stok)"
            " VALUES (?, ?, ?, 0) ON CONFLICT DO NOTHING",
            bom.tum_parca_tanimlari(),
        )
        conn.islem_bitir()

    _varsayilan_kullanicilar()


# ---------------------------------------------------------------------------
# KULLANICILAR / GİRİŞ
# ---------------------------------------------------------------------------

VARSAYILAN_SIFRE = "1234"

# İlk kurulumda oluşturulacak hesaplar: (kullanıcı adı, şifre, rol)
ILK_KULLANICILAR = [
    ("admin", VARSAYILAN_SIFRE, "yonetici"),
    ("valvos", VARSAYILAN_SIFRE, "kullanici"),
]

_PBKDF2_DONGU = 200_000


def _sifre_hashle(sifre, tuz=None):
    """Şifreyi geri döndürülemez şekilde hash'ler (düz metin saklanmaz)."""
    tuz = tuz or os.urandom(16).hex()
    ozet = hashlib.pbkdf2_hmac(
        "sha256", sifre.encode("utf-8"), bytes.fromhex(tuz), _PBKDF2_DONGU
    )
    return "pbkdf2_sha256$%d$%s$%s" % (_PBKDF2_DONGU, tuz, ozet.hex())


def _sifre_dogru_mu(sifre, kayitli):
    """Girilen şifre, veritabanındaki hash ile uyuşuyor mu."""
    try:
        _, dongu, tuz, ozet = kayitli.split("$")
        yeni = hashlib.pbkdf2_hmac(
            "sha256", sifre.encode("utf-8"), bytes.fromhex(tuz), int(dongu)
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(yeni.hex(), ozet)


def _varsayilan_kullanicilar():
    """admin ve valvos hesaplarını yoksa oluşturur (varsa dokunmaz).

    Hash hesaplamak pahalı bir işlem olduğu için önce hesabın var olup
    olmadığına bakılır; aksi halde her ekran yenilemesinde boşa zaman harcanır.
    """
    with baglanti() as conn:
        mevcut = {
            r["kullanici_adi"].lower()
            for r in conn.execute("SELECT kullanici_adi FROM kullanicilar").fetchall()
        }
        eksikler = [u for u in ILK_KULLANICILAR if u[0].lower() not in mevcut]
        if not eksikler:
            return
        conn.islem_basla()
        for kullanici_adi, sifre, rol in eksikler:
            conn.execute(
                "INSERT INTO kullanicilar (kullanici_adi, sifre, rol)"
                " VALUES (?, ?, ?) ON CONFLICT DO NOTHING",
                (kullanici_adi, _sifre_hashle(sifre), rol),
            )
        conn.islem_bitir()


def kullanici_dogrula(kullanici_adi, sifre):
    """Giriş denemesi. Doğruysa kullanıcı bilgisini, yanlışsa None döndürür."""
    kullanici_adi = (kullanici_adi or "").strip()
    if not kullanici_adi or not sifre:
        return None
    with baglanti() as conn:
        r = conn.execute(
            "SELECT * FROM kullanicilar WHERE LOWER(kullanici_adi) = LOWER(?)",
            (kullanici_adi,),
        ).fetchone()
        if r is None or not _sifre_dogru_mu(sifre, r["sifre"]):
            return None
        conn.islem_basla()
        conn.execute(
            "UPDATE kullanicilar SET son_giris = ? WHERE id = ?", (_simdi(), r["id"])
        )
        conn.islem_bitir()
        return {
            "id": r["id"],
            "kullanici_adi": r["kullanici_adi"],
            "rol": r["rol"],
            # Şifre hâlâ fabrika ayarı mı? Arayüzde uyarı göstermek için.
            "varsayilan_sifre": _sifre_dogru_mu(VARSAYILAN_SIFRE, r["sifre"]),
        }


def kullanicilar_listesi():
    with baglanti() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT id, kullanici_adi, rol, son_giris FROM kullanicilar"
                " ORDER BY rol, kullanici_adi"
            ).fetchall()
        ]


def sifre_degistir(kullanici_id, yeni_sifre, eski_sifre=None):
    """Şifre değiştirir. eski_sifre verilirse önce doğruluğu kontrol edilir."""
    if len(yeni_sifre or "") < 4:
        return False, "Yeni şifre en az 4 karakter olmalı."
    with baglanti() as conn:
        conn.islem_basla()
        r = conn.execute(
            "SELECT sifre FROM kullanicilar WHERE id = ?" + conn.kilit(),
            (kullanici_id,),
        ).fetchone()
        if r is None:
            conn.islem_geri_al()
            return False, "Kullanıcı bulunamadı."
        if eski_sifre is not None and not _sifre_dogru_mu(eski_sifre, r["sifre"]):
            conn.islem_geri_al()
            return False, "Mevcut şifre yanlış."
        conn.execute(
            "UPDATE kullanicilar SET sifre = ? WHERE id = ?",
            (_sifre_hashle(yeni_sifre), kullanici_id),
        )
        conn.islem_bitir()
    return True, "Şifre güncellendi."


def kullanici_ekle(kullanici_adi, sifre, rol):
    kullanici_adi = (kullanici_adi or "").strip()
    if len(kullanici_adi) < 3:
        return False, "Kullanıcı adı en az 3 karakter olmalı."
    if len(sifre or "") < 4:
        return False, "Şifre en az 4 karakter olmalı."
    if rol not in ("yonetici", "kullanici"):
        return False, "Geçersiz rol."
    with baglanti() as conn:
        conn.islem_basla()
        var = conn.execute(
            "SELECT 1 FROM kullanicilar WHERE LOWER(kullanici_adi) = LOWER(?)",
            (kullanici_adi,),
        ).fetchone()
        if var:
            conn.islem_geri_al()
            return False, "Bu kullanıcı adı zaten kayıtlı."
        conn.execute(
            "INSERT INTO kullanicilar (kullanici_adi, sifre, rol) VALUES (?, ?, ?)",
            (kullanici_adi, _sifre_hashle(sifre), rol),
        )
        conn.islem_bitir()
    return True, "'%s' kullanıcısı eklendi." % kullanici_adi


def kullanici_sil(kullanici_id, isteyen_id=None):
    """Kullanıcı siler. Kendini veya son yöneticiyi silmeye izin verilmez."""
    if isteyen_id is not None and int(kullanici_id) == int(isteyen_id):
        return False, "Kendi hesabınızı silemezsiniz."
    with baglanti() as conn:
        conn.islem_basla()
        r = conn.execute(
            "SELECT kullanici_adi, rol FROM kullanicilar WHERE id = ?" + conn.kilit(),
            (kullanici_id,),
        ).fetchone()
        if r is None:
            conn.islem_geri_al()
            return False, "Kullanıcı bulunamadı."
        if r["rol"] == "yonetici":
            kalan = conn.execute(
                "SELECT COUNT(*) AS adet FROM kullanicilar"
                " WHERE rol = 'yonetici' AND id <> ?",
                (kullanici_id,),
            ).fetchone()["adet"]
            if kalan == 0:
                conn.islem_geri_al()
                return False, "Son yönetici hesabı silinemez — sisteme giremezsiniz."
        conn.execute("DELETE FROM kullanicilar WHERE id = ?", (kullanici_id,))
        conn.islem_bitir()
    return True, "'%s' kullanıcısı silindi." % r["kullanici_adi"]


# ---------------------------------------------------------------------------
# SIFIRLAMA (sadece yönetici)
# ---------------------------------------------------------------------------

def veritabani_sifirla():
    """TÜM stok, üretim ve hareket kayıtlarını siler; stokları 0'a çeker.

    Kullanıcı hesaplarına DOKUNMAZ (yoksa sisteme giriş yapılamaz hale gelir).
    Silmeden önce otomatik yedek alır ve yedeğin yolunu döndürür.
    """
    yedek = yedek_al()
    with baglanti() as conn:
        conn.islem_basla()
        conn.execute("DELETE FROM hareketler")
        conn.execute("DELETE FROM uretimler")
        conn.execute("UPDATE parcalar SET stok = 0")
        conn.execute("ALTER SEQUENCE hareketler_id_seq RESTART WITH 1")
        conn.execute("ALTER SEQUENCE uretimler_id_seq RESTART WITH 1")
        conn.islem_bitir()
    return yedek


# ---------------------------------------------------------------------------
# OKUMA
# ---------------------------------------------------------------------------

def parcalar(kategori=None, dn=None):
    """Hammadde listesi (stok durumu ile)."""
    sql = "SELECT * FROM parcalar WHERE 1=1"
    args = []
    if kategori:
        sql += " AND kategori = ?"
        args.append(kategori)
    if dn:
        sql += " AND dn = ?"
        args.append(dn)
    sql += " ORDER BY kategori, varyant, dn"
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def parca_getir(kategori, varyant, dn):
    with baglanti() as conn:
        r = conn.execute(
            "SELECT * FROM parcalar WHERE kategori=? AND varyant=? AND dn=?",
            (kategori, varyant, dn),
        ).fetchone()
        return dict(r) if r else None


def kritik_parcalar():
    """Stoğu kritik seviyenin altına düşmüş kalemler."""
    with baglanti() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM parcalar WHERE stok <= kritik_seviye "
                "ORDER BY (stok - kritik_seviye), kategori, dn"
            ).fetchall()
        ]


def uretimler(limit=200):
    with baglanti() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM uretimler ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        ]


def hareketler(limit=500, uretim_id=None):
    sql = (
        "SELECT h.*, p.kategori, p.varyant, p.dn "
        "FROM hareketler h JOIN parcalar p ON p.id = h.parca_id"
    )
    args = []
    if uretim_id is not None:
        sql += " WHERE h.uretim_id = ?"
        args.append(uretim_id)
    sql += " ORDER BY h.id DESC LIMIT ?"
    args.append(limit)
    with baglanti() as conn:
        return [dict(r) for r in conn.execute(sql, args).fetchall()]


def ozet():
    """Gösterge paneli üst satırı için toplam sayılar."""
    with baglanti() as conn:
        toplam_stok = conn.execute(
            "SELECT COALESCE(SUM(stok), 0) AS deger FROM parcalar"
        ).fetchone()["deger"]
        kritik = conn.execute(
            "SELECT COUNT(*) AS deger FROM parcalar WHERE stok <= kritik_seviye"
        ).fetchone()["deger"]
        uretim_adet = conn.execute(
            "SELECT COALESCE(SUM(adet), 0) AS deger FROM uretimler WHERE iptal = 0"
        ).fetchone()["deger"]
        uretim_kayit = conn.execute(
            "SELECT COUNT(*) AS deger FROM uretimler WHERE iptal = 0"
        ).fetchone()["deger"]
    return {
        "toplam_stok": int(toplam_stok),
        "kritik": int(kritik),
        "uretilen_adet": int(uretim_adet),
        "uretim_kaydi": int(uretim_kayit),
    }


# ---------------------------------------------------------------------------
# YAZMA — HAMMADDE GİRİŞİ / DÜZELTME
# ---------------------------------------------------------------------------

def stok_girisi(parca_id, adet, aciklama=""):
    """Stoka mal girişi (örn. 'Stoka 50 adet DN 100 Gövde eklendi')."""
    if adet < 1:
        raise ValueError("Giriş adedi en az 1 olmalıdır.")
    with baglanti() as conn:
        conn.islem_basla()
        r = conn.execute(
            "SELECT stok FROM parcalar WHERE id = ?" + conn.kilit(), (parca_id,)
        ).fetchone()
        if r is None:
            conn.islem_geri_al()
            raise ValueError("Parça bulunamadı.")
        onceki = r["stok"]
        sonraki = onceki + adet
        conn.execute("UPDATE parcalar SET stok = ? WHERE id = ?", (sonraki, parca_id))
        conn.execute(
            "INSERT INTO hareketler (tarih, tip, parca_id, adet, onceki_stok,"
            " sonraki_stok, aciklama) VALUES (?, 'GIRIS', ?, ?, ?, ?, ?)",
            (_simdi(), parca_id, adet, onceki, sonraki, aciklama),
        )
        conn.islem_bitir()
    return sonraki


def stok_duzeltme(parca_id, yeni_stok, aciklama=""):
    """Sayım sonrası stoğu doğrudan belirli bir değere eşitler."""
    if yeni_stok < 0:
        raise ValueError("Stok negatif olamaz.")
    with baglanti() as conn:
        conn.islem_basla()
        r = conn.execute(
            "SELECT stok FROM parcalar WHERE id = ?" + conn.kilit(), (parca_id,)
        ).fetchone()
        if r is None:
            conn.islem_geri_al()
            raise ValueError("Parça bulunamadı.")
        onceki = r["stok"]
        conn.execute("UPDATE parcalar SET stok = ? WHERE id = ?", (yeni_stok, parca_id))
        conn.execute(
            "INSERT INTO hareketler (tarih, tip, parca_id, adet, onceki_stok,"
            " sonraki_stok, aciklama) VALUES (?, 'DUZELTME', ?, ?, ?, ?, ?)",
            (_simdi(), parca_id, yeni_stok - onceki, onceki, yeni_stok, aciklama),
        )
        conn.islem_bitir()
    return yeni_stok


def kritik_seviye_ayarla(parca_id, seviye):
    if seviye < 0:
        raise ValueError("Kritik seviye negatif olamaz.")
    with baglanti() as conn:
        conn.islem_basla()
        conn.execute(
            "UPDATE parcalar SET kritik_seviye = ? WHERE id = ?", (seviye, parca_id)
        )
        conn.islem_bitir()


# ---------------------------------------------------------------------------
# YAZMA — ÜRÜN ÇIKIŞI (REÇETE DÜŞÜMÜ)
# ---------------------------------------------------------------------------

def uretilebilir_adet(dn, conta, klepe, kontrol):
    """Mevcut stokla bu konfigürasyondan en fazla kaç adet üretilebilir."""
    kalemler = bom.recete(dn, conta, klepe, kontrol, 1)
    stoklar = []
    with baglanti() as conn:
        for k in kalemler:
            r = conn.execute(
                "SELECT stok FROM parcalar WHERE kategori=? AND varyant=? AND dn=?",
                (k["kategori"], k["varyant"], k["dn"]),
            ).fetchone()
            stoklar.append(r["stok"] if r else 0)
    return max(0, min(stoklar)) if stoklar else 0


def recete_durumu(dn, conta, klepe, kontrol, adet):
    """Düşüm yapmadan önce reçeteyi ve stok yeterliliğini gösterir."""
    kalemler = bom.recete(dn, conta, klepe, kontrol, adet)
    sonuc = []
    with baglanti() as conn:
        for k in kalemler:
            r = conn.execute(
                "SELECT id, stok FROM parcalar WHERE kategori=? AND varyant=? AND dn=?",
                (k["kategori"], k["varyant"], k["dn"]),
            ).fetchone()
            mevcut = r["stok"] if r else 0
            kayit = dict(k)
            kayit.update(
                {
                    "parca_id": r["id"] if r else None,
                    "mevcut_stok": mevcut,
                    "kalan_stok": mevcut - k["adet"],
                    "yeterli": mevcut >= k["adet"],
                    "eksik": max(0, k["adet"] - mevcut),
                }
            )
            sonuc.append(kayit)
    return sonuc


def uretim_yap(dn, conta, klepe, kontrol, adet, musteri="", aciklama=""):
    """Satış/üretim kaydı açar ve 5 hammaddeyi reçeteye göre stoktan düşer.

    TEK TRANSACTION: biri bile yetersizse hiçbir düşüm yapılmaz.
    Dönüş: (başarılı: bool, mesaj: str, detay: list)
    """
    kalemler = bom.recete(dn, conta, klepe, kontrol, adet)
    ad = bom.urun_adi(dn, conta, klepe, kontrol)
    tarih = _simdi()

    with baglanti() as conn:
        conn.islem_basla()

        # 1) Tüm kalemleri (satır kilidiyle) okuyup yeterlilik kontrolü yap
        satirlar = []
        eksikler = []
        for k in kalemler:
            r = conn.execute(
                "SELECT id, stok FROM parcalar WHERE kategori=? AND varyant=? AND dn=?"
                + conn.kilit(),
                (k["kategori"], k["varyant"], k["dn"]),
            ).fetchone()
            if r is None:
                conn.islem_geri_al()
                return False, "Tanımsız hammadde kalemi: " + k["ad"], []
            if r["stok"] < k["adet"]:
                eksikler.append(
                    {
                        "ad": k["ad"],
                        "gereken": k["adet"],
                        "mevcut": r["stok"],
                        "eksik": k["adet"] - r["stok"],
                    }
                )
            satirlar.append((r["id"], r["stok"], k))

        if eksikler:
            conn.islem_geri_al()
            return False, "Stok yetersiz — hiçbir düşüm yapılmadı.", eksikler

        # 2) Üretim kaydı
        uretim_id = conn.ekle_ve_id(
            "INSERT INTO uretimler (tarih, urun_adi, dn, conta, klepe, kontrol,"
            " adet, musteri, aciklama) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (tarih, ad, dn, conta, klepe, kontrol, adet, musteri, aciklama),
        )

        # 3) Düşüm + log
        detay = []
        for parca_id, onceki, k in satirlar:
            sonraki = onceki - k["adet"]
            conn.execute(
                "UPDATE parcalar SET stok = ? WHERE id = ?", (sonraki, parca_id)
            )
            conn.execute(
                "INSERT INTO hareketler (tarih, tip, parca_id, adet, onceki_stok,"
                " sonraki_stok, uretim_id, aciklama)"
                " VALUES (?, 'CIKIS', ?, ?, ?, ?, ?, ?)",
                (tarih, parca_id, -k["adet"], onceki, sonraki, uretim_id, ad),
            )
            detay.append(
                {
                    "ad": k["ad"],
                    "dusulen": k["adet"],
                    "onceki_stok": onceki,
                    "kalan_stok": sonraki,
                }
            )

        conn.islem_bitir()

    return True, "%d adet '%s' kaydedildi, 5 kalem stoktan düşüldü." % (adet, ad), detay


def uretim_iptal(uretim_id):
    """Yanlış girilen bir üretimi geri alır; düşülen hammaddeleri stoka ekler."""
    with baglanti() as conn:
        conn.islem_basla()
        u = conn.execute(
            "SELECT * FROM uretimler WHERE id = ?" + conn.kilit(), (uretim_id,)
        ).fetchone()
        if u is None:
            conn.islem_geri_al()
            return False, "Üretim kaydı bulunamadı."
        if u["iptal"]:
            conn.islem_geri_al()
            return False, "Bu kayıt zaten iptal edilmiş."

        cikislar = conn.execute(
            "SELECT parca_id, adet FROM hareketler "
            "WHERE uretim_id = ? AND tip = 'CIKIS'",
            (uretim_id,),
        ).fetchall()

        tarih = _simdi()
        for c in cikislar:
            geri = -c["adet"]  # CIKIS negatif kaydedilmişti
            onceki = conn.execute(
                "SELECT stok FROM parcalar WHERE id = ?" + conn.kilit(),
                (c["parca_id"],),
            ).fetchone()["stok"]
            sonraki = onceki + geri
            conn.execute(
                "UPDATE parcalar SET stok = ? WHERE id = ?", (sonraki, c["parca_id"])
            )
            conn.execute(
                "INSERT INTO hareketler (tarih, tip, parca_id, adet, onceki_stok,"
                " sonraki_stok, uretim_id, aciklama)"
                " VALUES (?, 'IPTAL', ?, ?, ?, ?, ?, ?)",
                (
                    tarih,
                    c["parca_id"],
                    geri,
                    onceki,
                    sonraki,
                    uretim_id,
                    "#%d iptal: %s" % (uretim_id, u["urun_adi"]),
                ),
            )

        conn.execute("UPDATE uretimler SET iptal = 1 WHERE id = ?", (uretim_id,))
        conn.islem_bitir()

    return True, "#%d iptal edildi, hammaddeler stoka geri eklendi." % uretim_id


# ---------------------------------------------------------------------------
# YEDEKLEME
# ---------------------------------------------------------------------------

# Yedeğe alınacak tablolar (sıra önemli: önce parcalar, sonra ona bağlı olanlar)
_YEDEK_TABLOLARI = [
    ("parcalar", ["id", "kategori", "varyant", "dn", "stok", "kritik_seviye"]),
    (
        "uretimler",
        ["id", "tarih", "urun_adi", "dn", "conta", "klepe", "kontrol", "adet",
         "musteri", "aciklama", "iptal"],
    ),
    (
        "hareketler",
        ["id", "tarih", "tip", "parca_id", "adet", "onceki_stok", "sonraki_stok",
         "uretim_id", "aciklama"],
    ),
    ("kullanicilar", ["id", "kullanici_adi", "sifre", "rol", "son_giris"]),
]


def yedek_klasoru():
    klasor = os.path.join(os.path.dirname(os.path.abspath(__file__)), "yedekler")
    os.makedirs(klasor, exist_ok=True)
    return klasor


def _yeni_yedek_yolu():
    """Kullanılmamış bir yedek dosya adı üretir.

    Dosya adı saniye hassasiyetinde olduğu için aynı saniye içinde iki yedek
    alınırsa (örn. sıfırlama otomatik yedek alırken) adlar çakışabilir;
    bu durumda sonuna -2, -3 ... eklenir.
    """
    klasor = yedek_klasoru()
    taban = "valvos_yedek_%s" % datetime.now().strftime("%Y%m%d_%H%M%S")
    hedef = os.path.join(klasor, taban + ".sql")
    sayac = 2
    while os.path.exists(hedef):
        hedef = os.path.join(klasor, "%s-%d.sql" % (taban, sayac))
        sayac += 1
    return hedef


def _sql_degeri(deger):
    """Python değerini SQL metnine güvenle gömülebilir hale getirir."""
    if deger is None:
        return "NULL"
    if isinstance(deger, bool):
        return "1" if deger else "0"
    if isinstance(deger, (int, float)):
        return str(deger)
    return "'" + str(deger).replace("'", "''") + "'"


def yedek_al():
    """Tüm verileri geri yüklenebilir bir .sql dosyasına yazar.

    Dosya, veritabanı sağlayıcınızın (Neon / Supabase) SQL Editor ekranına
    yapıştırılıp çalıştırıldığında verileri aynen geri yükler. Yönetim
    ekranından tek dosya olarak indirilebilir.
    """
    hedef = _yeni_yedek_yolu()
    satir_sayisi = 0

    with baglanti() as conn, open(hedef, "w", encoding="utf-8") as dosya:
        dosya.write("-- Valvos stok sistemi yedeği\n")
        dosya.write("-- Alındığı tarih: %s\n" % _simdi())
        dosya.write("-- Kaynak: %s\n" % veri_kaynagi())
        dosya.write(
            "--\n"
            "-- GERİ YÜKLEME: Bu dosyanın tamamını veritabanı sağlayıcınızın\n"
            "-- SQL Editor ekranına yapıştırıp çalıştırın. Mevcut kayıtların\n"
            "-- üzerine yazar.\n\n"
        )
        dosya.write("BEGIN;\n\n")
        # Tabloları ters sırada boşalt (yabancı anahtar kısıtı için)
        for tablo, _ in reversed(_YEDEK_TABLOLARI):
            dosya.write("DELETE FROM %s;\n" % tablo)
        dosya.write("\n")

        for tablo, kolonlar in _YEDEK_TABLOLARI:
            satirlar = conn.execute(
                "SELECT %s FROM %s ORDER BY id" % (", ".join(kolonlar), tablo)
            ).fetchall()
            dosya.write("-- %s (%d kayıt)\n" % (tablo, len(satirlar)))
            for r in satirlar:
                dosya.write(
                    "INSERT INTO %s (%s) VALUES (%s);\n"
                    % (
                        tablo,
                        ", ".join(kolonlar),
                        ", ".join(_sql_degeri(r[k]) for k in kolonlar),
                    )
                )
                satir_sayisi += 1
            dosya.write("\n")

        # id sayaçlarını en büyük id'nin üstüne taşı
        dosya.write("-- Kimlik sayaçlarını güncelle\n")
        for tablo, _ in _YEDEK_TABLOLARI:
            dosya.write(
                "SELECT setval('%s_id_seq',"
                " COALESCE((SELECT MAX(id) FROM %s), 1));\n" % (tablo, tablo)
            )
        dosya.write("\nCOMMIT;\n")

    return hedef
