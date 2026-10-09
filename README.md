# Valvos — Stok Takip Sistemi (BOM / Ürün Reçetesi)

Vana üretimi için hammadde stok takibi. Bir vana satıldığında/üretildiğinde
reçetedeki **5 ana kalem otomatik olarak stoktan düşer**.

Sistem **bulut tabanlıdır**: veriler internetteki bir PostgreSQL
veritabanında tutulur. Bu sayede

- babanız ofisten, siz evden **aynı stoğu** görürsünüz,
- bilgisayarınız kapalıyken de sistem çalışır,
- Streamlit uygulamayı yeniden başlattığında **veriler silinmez**.

```
   Babanız (ofis)  ──┐
                     ├──►  Streamlit Cloud  ──►  PostgreSQL (Neon)
   Siz (ev)        ──┘      [uygulama]            [VERİLER BURADA]
                              ücretsiz              ücretsiz
```

> **Önemli:** Program artık kendi başına, veritabanı olmadan çalışmaz.
> Önce aşağıdaki **ADIM 1**'i yapıp bir veritabanı adresi almanız gerekir.
> Adres hem internetteki kurulumda hem kendi bilgisayarınızda kullanılır;
> ikisi de **aynı** veritabanına bağlanır, yani stok tek yerde tutulur.

---

## İçindekiler

- [ADIM 1 — Ücretsiz veritabanı aç ve adresi al](#adim-1--ücretsiz-veritabanı-aç-ve-adresi-al) *(~10 dk)*
- [ADIM 2 — Kendi bilgisayarında çalıştır (`secrets.toml`)](#adim-2--kendi-bilgisayarında-çalıştır) *(~5 dk)*
- [ADIM 3 — İnternete aç (GitHub + Streamlit Cloud)](#adim-3--i̇nternete-aç) *(~25 dk)*
- [ADIM 4 — İlk iş: şifreleri değiştir](#adim-4--i̇lk-iş-şifreleri-değiştir)
- [Sistem nasıl çalışıyor?](#sistem-nasıl-çalışıyor)
- [Günlük kullanım](#günlük-kullanım)
- [Sorun giderme](#sorun-giderme)

---

# ADIM 1 — Ücretsiz veritabanı aç ve adresi al

Burada amacınız tek bir şey: **uzun bir adres (DATABASE_URL) elde etmek.**
Şuna benzeyen bir metin:

```
postgresql://neondb_owner:npg_AbC123xyz@ep-cool-sun-12345678.eu-central-1.aws.neon.tech/neondb?sslmode=require
```

Bu adres veritabanınızın kapı anahtarıdır. **Kimseyle paylaşmayın.**

### Hangi sağlayıcı? → Neon öneriyorum

Siz Supabase'den bahsetmiştiniz; ikisi de ücretsiz ve ikisi de PostgreSQL,
program her ikisiyle de çalışır. Yine de **Neon öneriyorum**, çünkü:

> **Supabase ücretsiz planı, projeyi 1 hafta işlem görmezse tamamen askıya
> alıyor** ve askıya alınan projeyi panelden elle yeniden başlatmanız gerekiyor.
> Atölye bir hafta sisteme girmezse, babanız salı sabahı linke bastığında
> uygulama çalışmaz. Neon ise sadece işlemciyi uyutur, **veri yerinde kalır**
> ve ilk sorguda yarım saniyede uyanır.

Supabase ile devam etmek isterseniz [aşağıdaki Supabase bölümü](#supabase-ile-yapmak-i̇sterseniz)
farkları anlatıyor.

### Neon ile adım adım

1. Tarayıcıdan **https://console.neon.tech** adresine gidin.
2. **Sign up** → Google veya GitHub hesabınızla girin (en kolayı Google).
   Kredi kartı istenmez.
3. Karşınıza proje oluşturma ekranı gelir. Şöyle doldurun:
   - **Project name:** `valvos`
   - **Postgres version:** varsayılan kalsın
   - **Region:** listeden **Europe** yazan birini seçin (örn. *Frankfurt*).
     Türkiye'ye yakın olanı programı hızlandırır.
4. **Create project** düğmesine basın.
5. Proje açılınca sayfanın üstünde **Connect** düğmesi vardır, ona basın.
   Açılan pencerede uzun adres görünür.
6. ⚠️ **Bu pencerede iki şeyi kontrol edin:**
   - **Connection pooling** anahtarı **KAPALI** olmalı. Kapalı olduğunda
     adreste **`-pooler`** kelimesi **geçmez**:
     ✅ `...@ep-cool-sun-12345678.eu-central-1...`
     ❌ `...@ep-cool-sun-12345678-pooler.eu-central-1...`

     > *Neden?* Program veritabanına tek bir kalıcı bağlantı açtığı için
     > bağlantı havuzuna ihtiyaç duymaz. Havuzlu adres ise bazı ayarları
     > bağlantılar arasında karıştırabiliyor ve "tablo bulunamadı" gibi
     > tuhaf hatalara yol açabiliyor. Havuzsuz adres bu riski ortadan
     > kaldırır. (Yanlışlıkla havuzlu adresi yazarsanız program yine
     > çalışır, bu sadece daha güvenli olanı.)
   - Adreste **`?sslmode=require`** bulunmalı. Yoksa elle ekleyin.
     (Sonunda `&channel_binding=require` de olabilir, kalması sorun değil.)
7. Adresin yanındaki **kopyala** simgesine basın.
8. Masaüstünde Not Defteri açıp adresi yapıştırın ve
   `neon-adres.txt` olarak kaydedin. Birkaç kez kullanacaksınız.

✅ **ADIM 1 bitti.** Veritabanınız hazır ve boş. Tabloları program kendisi
oluşturacak, siz SQL yazmayacaksınız.

### Supabase ile yapmak isterseniz

1. **https://supabase.com** → **Start your project** → GitHub ile girin.
2. **New project** → Name: `valvos`, güçlü bir **Database Password** belirleyin
   (bunu kaydedin, bir daha gösterilmez), **Region:** Frankfurt → **Create**.
3. Proje hazır olunca üstteki **Connect** düğmesine basın.
4. **Connection string** bölümünde **Session pooler** sekmesini seçin ve
   adresi kopyalayın. **Transaction pooler'ı seçmeyin** — o modda ayarlar
   bağlantılar arasında karışabiliyor.
5. Adresin içindeki `[YOUR-PASSWORD]` yazan yeri, 2. adımda belirlediğiniz
   şifre ile değiştirin.
6. Askıya alma sorununu azaltmak için sisteme **haftada en az bir kez** girin.

---

# ADIM 2 — Kendi bilgisayarında çalıştır

Programı internete açmadan önce kendi bilgisayarınızda deneyin.
Streamlit, gizli bilgileri `secrets.toml` adlı bir dosyadan okur.

1. Proje klasörünü açın:
   `C:\Users\vedat\OneDrive\Desktop\valvos BOM`
2. İçindeki **`.streamlit`** klasörüne girin. İçinde
   **`secrets.toml.ornek`** dosyasını göreceksiniz.
3. Bu dosyayı **kopyalayıp aynı klasöre yapıştırın** (sağ tık → Kopyala,
   sonra sağ tık → Yapıştır).
4. Oluşan kopyanın adını **`secrets.toml`** olarak değiştirin.
   > Dosya adının sonu `.ornek` **olmayacak**. Windows uzantıları gizliyorsa
   > Dosya Gezgini'nde *Görünüm → Dosya adı uzantıları* kutusunu işaretleyin.
5. `secrets.toml` dosyasına **sağ tık → Birlikte aç → Not Defteri**.
6. İçindeki `DATABASE_URL = "..."` satırını silip, ADIM 1'de kaydettiğiniz
   adresi tırnaklar arasına yazın. Dosyanın tamamı şöyle görünmeli:

   ```toml
   DATABASE_URL = "postgresql://neondb_owner:npg_AbC123xyz@ep-cool-sun-12345678.eu-central-1.aws.neon.tech/neondb?sslmode=require"
   ```

   Dikkat edilecekler:
   - `DATABASE_URL` tam olarak böyle, büyük harfle yazılmalı
   - Adres **çift tırnak içinde** olmalı
   - Satırda başka hiçbir şey olmamalı, `#` ile başlayan satırlar kalabilir

7. **Kaydet** (Ctrl+S) ve Not Defteri'ni kapatın.
8. Proje klasöründeki **`baslat.bat`** dosyasına çift tıklayın.
   İlk çalıştırmada gerekli kütüphaneler kurulur (1–2 dakika), sonra
   tarayıcıda **Valvos giriş ekranı** açılır.

İlk açılışta iki hesap otomatik oluşur:

| Kullanıcı | Şifre | Rol | Kim için |
|---|---|---|---|
| `admin` | `1234` | yonetici | Siz (Sistem Yönetimi sekmesini görür) |
| `valvos` | `1234` | kullanici | Babanız (yönetim sekmesini görmez) |

✅ **ADIM 2 bitti.** Giriş yapıp gezebilirsiniz. Girdiğiniz stoklar buluttaki
veritabanına yazılır, yani ADIM 3'ten sonra internetten de aynı veriyi
göreceksiniz.

> 🔒 **`secrets.toml` dosyasını asla kimseye göndermeyin ve GitHub'a
> yüklemeyin.** Projedeki `.gitignore` dosyası bunu zaten engelliyor.

---

# ADIM 3 — İnternete aç

## 3a) Dosyaları GitHub'a yükle

Streamlit Cloud programı GitHub'dan okur. GitHub ücretsiz bir dosya deposudur.

1. **https://github.com** → **Sign up** ile hesap açın (varsa **Sign in**).
2. Sağ üstteki **+** → **New repository**.
3. Formu doldurun:
   - **Repository name:** `valvos-stok`
   - 🔒 **Private** seçeneğini işaretleyin *(Public değil!)*
   - Diğer kutulara dokunmayın
4. **Create repository**.
5. Açılan sayfada **uploading an existing file** bağlantısına basın
   (veya **Add file → Upload files**).
6. Bilgisayarınızda `valvos BOM` klasörünü açın ve şu **5 dosyayı** seçip
   tarayıcı penceresine sürükleyin:

   ```
   app.py
   bom.py
   database.py
   tema.py
   requirements.txt
   ```

   > ❌ **ŞUNLARI YÜKLEMEYİN:**
   > `secrets.toml` (şifreniz içinde!), `yedekler` klasörü,
   > `__pycache__` klasörü, `baslat.bat`, `.db` uzantılı dosyalar.

7. Sayfanın altındaki yeşil **Commit changes** düğmesine basın.

### Tema dosyasını ekleyin (renkler için)

1. Depo sayfasında **Add file → Create new file**.
2. Dosya adı kutusuna **tam olarak** şunu yazın (eğik çizgi dahil):

   ```
   .streamlit/config.toml
   ```

   Eğik çizgiyi yazdığınız anda GitHub klasörü kendisi oluşturur.
3. Alttaki büyük metin alanına şunu yapıştırın:

   ```toml
   [theme]
   primaryColor = "#3D7EBF"
   font = "sans serif"

   [client]
   toolbarMode = "viewer"
   showErrorDetails = false

   [browser]
   gatherUsageStats = false
   ```

   > **Neden zemin ve yazı rengi yazılmıyor?**
   > Burada sadece vurgu rengi sabitlenir. Zemin ile yazı rengini
   > Streamlit'in kendi teması belirler; böylece uygulamayı açan kişi
   > sağ üstteki **⋮ → Settings → Theme** menüsünden **Light** (açık) veya
   > **Dark** (koyu) temayı kendisi seçebilir ve yazılar her iki temada da
   > okunur kalır. `toolbarMode` da bu yüzden `"minimal"` değil `"viewer"`:
   > `minimal` yapılırsa ⋮ menüsü kaybolur ve tema seçimi imkânsız hâle gelir.

4. **Commit changes**.

Depoda toplam **6 dosya** olmalı. `secrets.toml` **olmamalı** — kontrol edin.

## 3b) Streamlit Cloud'da yayına al

1. **https://share.streamlit.io** adresine gidin.
2. **Continue with GitHub** ile girin ve istenen izinleri verin.
   Depo *Private* olduğu için özel depolara erişim iznini de onaylamanız
   gerekir (**Connect GitHub account**).
3. Sağ üstte **Create app** düğmesine basın.
4. Mevcut bir depodan kurulum seçeneğini seçip formu doldurun:
   - **Repository:** `kullanıcı-adınız/valvos-stok`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **App URL:** istediğiniz adı yazın, örn. `valvos-stok`
     → adresiniz `https://valvos-stok.streamlit.app` olur
5. ⚠️ **Deploy'a basmadan önce** formun altındaki
   **Advanced settings…** bağlantısına basın:

   - **Python version:** `3.12` seçin
   - **Secrets** kutusuna, ADIM 1'de kaydettiğiniz adresi şu şekilde
     yapıştırın:

     ```toml
     DATABASE_URL = "postgresql://neondb_owner:npg_AbC123xyz@ep-cool-sun-12345678.eu-central-1.aws.neon.tech/neondb?sslmode=require"
     ```

     > Bu kutu, bilgisayarınızdaki `secrets.toml` dosyasının bulut
     > karşılığıdır — içeriği **birebir aynıdır**. Şifreniz GitHub'a değil,
     > sadece buraya girilir ve kimse göremez.

   - **Save** / kaydet.
6. **Deploy!** düğmesine basın.
7. 2–5 dakika kurulum ekranı akar, sonunda **Valvos giriş ekranı** açılır.

✅ **Linkiniz hazır:** `https://valvos-stok.streamlit.app`
Bu linki babanıza gönderin. Bilgisayarınız kapalı olsa bile çalışır.

### Secrets'ı sonradan değiştirmek

Uygulama sayfasında sağ alttaki **Manage app** → üç nokta → **Settings** →
**Secrets**. Değiştirdikten sonra **Reboot app** yapın.

---

# ADIM 4 — İlk iş: şifreleri değiştir

Link artık internette ve şifreler hâlâ `1234`.

1. Linke girin, `admin` / `1234` ile giriş yapın.
2. Üstte kırmızı uyarı göreceksiniz. Menü → **🔑 Şifre Değiştir** →
   yeni ve güçlü bir şifre belirleyin.
3. Menü → **🛡️ Sistem Yönetimi → 👥 Kullanıcılar** →
   *"Başkasının Şifresini Sıfırla"* bölümünden `valvos` hesabına da yeni bir
   şifre verin ve bunu babanıza iletin.

> Streamlit Cloud'da uygulamanın adresi herkese açıktır, ancak **giriş
> ekranını geçmeden hiçbir veri görünmez.** Asıl koruma sizin şifrenizdir —
> bu yüzden `1234` ile bırakmayın.
>
> Ek güvenlik isterseniz: **Manage app → Settings → Sharing** ile uygulamayı
> yalnızca belirli e-posta adreslerine açabilirsiniz (ücretsiz planda 1 adet
> özel uygulama hakkınız var).

Son olarak stokları girin: **📥 Hammadde Girişi → 📦 Toplu Giriş** ekranından
kategori seçip eldeki adetleri tek tabloda girmek en hızlı yoldur.

---

# Sistem nasıl çalışıyor?

## Takip edilen 5 ana kalem

Küçük cıvata, somun vb. **takip edilmez.** Sadece:

| Kalem | Türler |
|---|---|
| **Gövde** | (tür yok) |
| **Conta** | EPDM, Viton, Teflon, NBR |
| **Klepe** | Nikel, Paslanmaz, 316 |
| **Mil** | (tür yok) |
| **Kontrol Mekanizması** | Kol, Pnömatik Aktüatör, Elektrikli Aktüatör |

**Çaplar:** DN 40, 50, 65, 80, 100, 125, 150, 200, 250, 300

Her kalem **çap bazında ayrı** takip edilir (DN 100 EPDM Conta ile DN 200 EPDM
Conta farklı stok kalemleridir) — toplam 120 kalem.

## Ürün reçetesi (BOM)

**1 adet vana = 1 Gövde + 1 Conta + 1 Klepe + 1 Mil + 1 Kontrol Mekanizması**
(hepsi seçilen çaptan)

Örnek: *DN 100 Nikel Klepeli EPDM Contalı Kelebek Vana — 1 Adet* onaylandığında:

- 1 × DN 100 Gövde
- 1 × DN 100 EPDM Conta
- 1 × DN 100 Nikel Klepe
- 1 × DN 100 Mil
- 1 × DN 100 Kol

Ürün **Pnömatik/Elektrikli Aktüatörlü** seçilirse Kol yerine o aktüatör düşer.

**Güvenlik kuralı:** 5 kalemden biri bile yetersizse **hiçbir düşüm yapılmaz**
ve hangi parçadan kaç adet eksik olduğu ekranda yazar. Yarım düşüm oluşmaz.
Siz ve babanız aynı anda son parçayı düşmeye kalkarsanız yalnızca biri geçer.

## Ekranlar

| Ekran | Ne işe yarar | Kim görür |
|---|---|---|
| 📊 **Gösterge Paneli** | Mevcut stoklar, çap/tür tabloları, kritik stok uyarısı, CSV indirme | Herkes |
| 📥 **Hammadde Girişi** | *Tek Kalem:* "50 adet DN 100 Gövde geldi". *Toplu Giriş:* bir irsaliyenin tamamı. *Sayım Düzeltme:* fiziksel sayım farkı | Herkes |
| 🏭 **Ürün Çıkışı** | Vanayı açılır menülerden seç, adet gir; onaydan önce reçete ve kalan stok önizlemesi | Herkes |
| 📜 **Geçmiş** | Hangi tarihte ne satıldı, hangi parçadan ne düştü. Yanlış kayıt **iptal** edilip stok geri yüklenir | Herkes |
| ⚙️ **Ayarlar** | Kritik stok seviyeleri, yedek alma | Herkes |
| 🔑 **Şifre Değiştir** | Kendi şifresini değiştirir | Herkes |
| 🛡️ **Sistem Yönetimi** | Kullanıcı ekle/sil, şifre sıfırla, yedekler, veritabanını sıfırla | **Sadece yonetici** |

## Dosya yapısı

```
valvos BOM/
├── baslat.bat             ← ÇİFT TIKLA (kendi bilgisayarında çalıştırmak için)
├── app.py                 ← Arayüz (ekranlar, giriş kapısı)
├── bom.py                 ← Reçete kuralları + çap/tür listeleri
├── database.py            ← PostgreSQL: stok, kullanıcılar, loglar
├── tema.py                ← Kurumsal görünüm (CSS)
├── requirements.txt       ← Gerekli kütüphaneler
├── .gitignore             ← GitHub'a gitmeyecek dosyalar
├── .streamlit/
│   ├── config.toml        ← Renk teması, hazır menüleri kapatma
│   ├── secrets.toml.ornek ← Örnek (bunu kopyalayıp secrets.toml yapın)
│   └── secrets.toml       ← SİZİN ADRESİNİZ — gizli, GitHub'a gitmez
└── yedekler/              ← "Yedek Al" ile oluşan .sql dosyaları
```

**Mimari:** `app.py` (arayüz) → `database.py` (iş kuralları ve PostgreSQL) →
`bom.py` (reçete kuralları, veritabanı bilmez). `tema.py` sadece görünüm.

---

# Günlük kullanım

**Program ilk açılışta yavaş mı?**
Normaldir. Streamlit Cloud, 12 saat kimse girmezse uygulamayı uyutur; ilk
ziyaret onu uyandırır (10–30 saniye). Neon da 5 dakika işlem olmazsa uyur ve
ilk sorguda yarım saniyede uyanır. Veriler kaybolmaz; bağlantı koparsa
program kendini yeniden bağlar.

**Yeni bir çap veya conta türü eklemek istiyorum.**
GitHub'da `bom.py` dosyasını açın → kalem simgesine basın → ilgili listeye
değeri ekleyin → **Commit changes**. Streamlit Cloud değişikliği görüp
uygulamayı kendisi yeniden kurar.

```python
DN_LISTESI = [40, 50, 65, 80, 100, 125, 150, 200, 250, 300, 350]
CONTA_TURLERI = ["EPDM", "Viton", "Teflon", "NBR", "Silikon"]
```

Yeni kalemler 0 stokla otomatik oluşur, mevcut stoklar bozulmaz.
(Aynı değişikliği kendi bilgisayarınızdaki `bom.py` dosyasında da yapın ki
iki kopya aynı kalsın.)

**Yedek nasıl alırım?**
Menü → **🛡️ Sistem Yönetimi → 💾 Yedekler → "Şimdi Yedek Al"**, ardından
**"En son yedeği bilgisayarıma indir"**. İnen `.sql` dosyası tüm verinin tek
dosyalık kopyasıdır. Ayda bir indirip saklamanız yeterli.

**Yedeği nasıl geri yüklerim?**
Neon panelinde sol menüden **SQL Editor** → inen `.sql` dosyasını Not
Defteri ile açıp **tamamını** kopyalayın → editöre yapıştırıp **Run**.
Dosya mevcut kayıtların üzerine yazar.

**Yanlış ürün çıkışı yaptım.**
Geçmiş → Üretim Kayıtları → kaydı seçin → *"Kaydı İptal Et"*. Düşülen
5 hammadde stoka geri eklenir; kayıt silinmez, "İptal" olarak işaretlenir.

**Stok yetersiz diyor ama üretmem gerekiyor.**
Sistem bilinçli olarak negatif stoğa izin vermez. Malzeme gerçekten varsa
Hammadde Girişi → **Sayım Düzeltme** ile doğru miktarı girin.

**Veritabanını sıfırlamak istiyorum.**
Sadece `admin` yapabilir: 🛡️ Sistem Yönetimi → ☢️ Tehlikeli İşlemler →
kutuyu açın → onay alanına **SİL** yazın. Silmeden hemen önce otomatik yedek
alınır; kullanıcı hesapları ve çap/tür tanımları korunur.

**Veritabanı adresim sızdı, ne yapmalıyım?**
Neon panelinden şifreyi yenileyin (**Roles → Reset password**), sonra yeni
adresi iki yere de yazın: Streamlit Cloud **Settings → Secrets** (sonra
**Reboot app**) ve bilgisayarınızdaki `.streamlit/secrets.toml`.

---

# Sorun giderme

| Belirti | Sebep / Çözüm |
|---|---|
| **"Veritabanı adresi (DATABASE_URL) bulunamadı"** | Bilgisayarda: `.streamlit/secrets.toml` yok veya adı `secrets.toml.ornek` kalmış. İnternette: Advanced settings → Secrets boş. ADIM 2 / 3b'yi kontrol edin. |
| `baslat.bat` "DIKKAT: Veritabani adresi tanimli degil" diyor | Aynı sebep — `secrets.toml` dosyasını oluşturmanız gerekiyor. |
| **"could not connect to server" / "connection timeout"** | Adres eksik/bozuk ya da sonundaki `?sslmode=require` silinmiş. Neon'dan adresi yeniden kopyalayın. Program bağlanmayı 3 kez dener, yine olmazsa bu hatayı verir. |
| **"password authentication failed"** | Supabase kullanıyorsanız adresteki `[YOUR-PASSWORD]` yerine gerçek şifreyi yazmayı atlamış olabilirsiniz. |
| Kurulumda `ModuleNotFoundError` | `requirements.txt` GitHub'a yüklenmemiş. ADIM 3a'yı kontrol edin. |
| "Error installing requirements" | Advanced settings'te Python sürümü `3.12` seçilmemiş olabilir. |
| Girişte "şifre hatalı" ama şifre doğru | 5 hatalı denemeden sonra 60 saniye kilit devreye girer; bir dakika bekleyin. |
| Babamın şifresini unuttuk | `admin` ile girip 🛡️ Sistem Yönetimi'nden sıfırlayın. |
| **`admin` şifresini de unuttuk** | Neon panelinde **SQL Editor**'ü açıp şunu çalıştırın:<br>`DELETE FROM kullanicilar WHERE LOWER(kullanici_adi)='admin';`<br>Sayfayı yenileyin: `admin` hesabı `1234` şifresiyle yeniden oluşur. Girip şifreyi hemen değiştirin. |
| Sayfa "Oh no. Error running app" | **Manage app → Logs** kısmındaki son satırlar sebebi gösterir. |
| Supabase'de uygulama bir süre sonra açılmıyor | Ücretsiz plan projeyi 1 hafta işlem görmezse askıya alıyor. Supabase panelinden **Restore project** yapın; kalıcı çözüm için Neon'a geçin. |

---

## Teknik notlar

- **Şifreler:** PBKDF2-SHA256, 200.000 tur, kullanıcıya özel tuz. Düz metin
  şifre hiçbir yerde saklanmaz; `kullanicilar.sifre` kolonunda yalnızca hash
  durur.
- **Stok tutarlılığı:** Üretim düşümü tek bir transaction içinde yapılır ve
  ilgili satırlar `SELECT ... FOR UPDATE` ile kilitlenir. Bir kalem bile
  yetersizse işlem tamamen geri alınır (`ROLLBACK`); eş zamanlı iki işlemde
  stok eksiye düşmez.
- **SQL güvenliği:** Tüm değerler parametre olarak gönderilir, SQL metnine
  gömülmez.
- **Bağlantı yönetimi:** Tek bir bulut bağlantısı paylaşılır ve koparsa
  kendiliğinden yenilenir. Havuzlayıcı (PgBouncer) uyumluluğu için otomatik
  "prepared statement" kullanımı kapatılmıştır — program hem Neon hem
  Supabase ile çalışır.
- **Oturum:** Giriş bilgisi tarayıcı sekmesinin oturumunda tutulur; sekmeyi
  kapatıp açınca tekrar giriş istenir (kasıtlı).
