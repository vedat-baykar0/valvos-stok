# -*- coding: utf-8 -*-
"""
Valvos - Ürün Reçetesi (BOM) tanımları.

Bu dosya SADECE iş kurallarını içerir; veritabanı veya arayüz bilgisi yoktur.
Yeni bir çap / conta türü eklemek istersen tek yapman gereken aşağıdaki
listelere yeni değeri yazmaktır. Uygulama ilk açılışta eksik parçaları
otomatik olarak stok tablosuna 0 adet ile ekler.
"""

# ---------------------------------------------------------------------------
# VARYASYONLAR
# ---------------------------------------------------------------------------

DN_LISTESI = [40, 50, 65, 80, 100, 125, 150, 200, 250, 300]

CONTA_TURLERI = ["EPDM", "Viton", "Teflon", "NBR"]

KLEPE_TURLERI = ["Nikel", "Paslanmaz", "316"]

KONTROL_TURLERI = ["Kol", "Pnömatik Aktüatör", "Elektrikli Aktüatör"]

# Varyantı olmayan kalemler (Gövde, Mil) için kullanılan yer tutucu.
YOK = "-"

# ---------------------------------------------------------------------------
# KATEGORİLER
# ---------------------------------------------------------------------------

# kategori kodu -> (ekranda görünen ad, o kategorinin varyant listesi)
KATEGORILER = {
    "GOVDE":   ("Gövde",               [YOK]),
    "CONTA":   ("Conta",               CONTA_TURLERI),
    "KLEPE":   ("Klepe",               KLEPE_TURLERI),
    "MIL":     ("Mil",                 [YOK]),
    "KONTROL": ("Kontrol Mekanizması", KONTROL_TURLERI),
}

KATEGORI_SIRASI = ["GOVDE", "CONTA", "KLEPE", "MIL", "KONTROL"]


def kategori_adi(kategori: str) -> str:
    return KATEGORILER.get(kategori, (kategori, []))[0]


def parca_adi(kategori: str, varyant: str, dn: int) -> str:
    """Örn: ('CONTA', 'EPDM', 100) -> 'DN 100 EPDM Conta'"""
    if varyant == YOK:
        return f"DN {dn} {kategori_adi(kategori)}"
    if kategori == "KONTROL":
        # 'DN 100 Pnömatik Aktüatör' / 'DN 100 Kol'
        return f"DN {dn} {varyant}"
    return f"DN {dn} {varyant} {kategori_adi(kategori)}"


def tum_parca_tanimlari():
    """Sistemin takip ettiği bütün hammadde kalemlerini üretir.

    Dönüş: [(kategori, varyant, dn), ...]
    """
    tanimlar = []
    for kategori in KATEGORI_SIRASI:
        _, varyantlar = KATEGORILER[kategori]
        for varyant in varyantlar:
            for dn in DN_LISTESI:
                tanimlar.append((kategori, varyant, dn))
    return tanimlar


# ---------------------------------------------------------------------------
# ÜRÜN ADI ve REÇETE
# ---------------------------------------------------------------------------

def urun_adi(dn: int, conta: str, klepe: str, kontrol: str) -> str:
    """Örn: 'DN 100 Nikel Klepeli EPDM Contalı Kelebek Vana - Kol'"""
    return (
        f"DN {dn} {klepe} Klepeli {conta} Contalı Kelebek Vana - {kontrol}"
    )


def recete(dn: int, conta: str, klepe: str, kontrol: str, adet: int = 1):
    """Bir vana konfigürasyonunun hammadde reçetesini döndürür.

    1 adet vana = 1 Gövde + 1 Conta + 1 Klepe + 1 Mil + 1 Kontrol mekanizması
    (Kontrol mekanizması Kol veya seçilen Aktüatör olabilir.)

    Dönüş: [{'kategori':..., 'varyant':..., 'dn':..., 'adet':...}, ...]
    """
    if dn not in DN_LISTESI:
        raise ValueError(f"Geçersiz çap: DN {dn}")
    if conta not in CONTA_TURLERI:
        raise ValueError(f"Geçersiz conta türü: {conta}")
    if klepe not in KLEPE_TURLERI:
        raise ValueError(f"Geçersiz klepe türü: {klepe}")
    if kontrol not in KONTROL_TURLERI:
        raise ValueError(f"Geçersiz kontrol mekanizması: {kontrol}")
    if adet < 1:
        raise ValueError("Adet en az 1 olmalıdır.")

    kalemler = [
        ("GOVDE",   YOK,     1),
        ("CONTA",   conta,   1),
        ("KLEPE",   klepe,   1),
        ("MIL",     YOK,     1),
        ("KONTROL", kontrol, 1),
    ]

    return [
        {
            "kategori": kategori,
            "varyant": varyant,
            "dn": dn,
            "adet": birim_adet * adet,
            "ad": parca_adi(kategori, varyant, dn),
        }
        for kategori, varyant, birim_adet in kalemler
    ]
