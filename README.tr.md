[English](README.md) | **Türkçe**

# SlipSurfaceIQ Settle

**Sığ temellerin ve dolguların oturma analizi, masaüstü arayüzüyle — sürüm 2026.1.0**

[![CI](https://github.com/hdaltuntas/SlipSurfaceIQ-Settle/actions/workflows/ci.yml/badge.svg)](https://github.com/hdaltuntas/SlipSurfaceIQ-Settle/actions/workflows/ci.yml)

SlipSurfaceIQ Settle, tabakalı bir zemin profili üzerindeki dikdörtgen, şerit ya da dairesel
bir temelin — ya da tepe genişliği, yüksekliği ve şev açılarıyla verilen bir dolgunun —
**ne kadar** ve **ne hızla** oturacağını hesaplar:

1. **Gerilmeler** — yerinde σv0, u0, σ'v0 ve σ'p; temel altındaki gerilme artışı Boussinesq
   (Newmark dikdörtgen, şerit ve daire çözümleri) ya da 2:1 yayılma ile; merkez, karakteristik
   nokta, uzun kenar ortası ve köşede; dolgu altında yamuk yük için kesin çözümle tepe ortası,
   tepe kenarı, şev ortası ve şev topuğunda.
2. **Ani oturma** — tüm tabakalarda tabakalı elastik (Steinbrenner) ya da granüler
   tabakalarda Schmertmann (1978).
3. **Konsolidasyon** — kil tabakalarının Cc, Cr, e0 ve σ'p ile birincil oturması; Cα ile
   tasarım ömrüne kadar ikincil sıkışma.
4. **Zaman** — Terzaghi tek boyutlu konsolidasyonu, her kil tabakası kendi başına drene;
   t50, t90 ve zaman–oturma eğrisi.
5. **Kontroller** — toplam oturma ve açısal distorsiyon, izin verilen değerlere karşı.

Bunun üzerine bir **parametrik veya güvenilirlik çalışması** istenen girdiyi — bir aralık
ya da bir dağılım olarak — tarar; duyarlılıkları ve izin verilen oturmanın veya
distorsiyonun aşılma olasılığını, güven aralığı ve güvenilirlik indeksi β ile raporlar.

[SlipSurfaceIQ LE](https://github.com/hdaltuntas/SlipSurfaceIQ-LE)'nin masaüstü kardeşidir
ve onunla aynı görünümü paylaşır: aynı iş akışı çubuğu, paneller, ikonlar, temalar ve yazı
tipleri. Her etiket, sonuç, şekil ve rapor **Türkçe ve İngilizce**dir; dil, yapılan iş
kaybolmadan istendiği an değiştirilir.

> **Mühendislik uyarısı.** SlipSurfaceIQ Settle hiçbir garanti olmaksızın sunulur. Sonuçlar
> tamamen girilen zemin parametrelerine, yüklere ve yeraltı suyuna bağlıdır. Sonuçları
> mühendislik muhakemesiyle ve gerektiğinde bağımsız hesaplarla doğrulayın.

## Ekran görüntüleri

| Kesit ve gerilme soğanı | Sonuç özeti |
|---|---|
| ![Kesit](docs/screenshots/section_tr.png) | ![Özet](docs/screenshots/summary_tr.png) |

| Yumuşak kil üzerinde dolgu | cv için tek tek tarama |
|---|---|
| ![Dolgu](docs/screenshots/embankment_tr.png) | ![Tarama](docs/screenshots/study_oat_tr.png) |

| Malzeme tanımı: mv ile kil | Zemin profili: malzemeler ve tabakalar |
|---|---|
| ![Malzemeler](docs/screenshots/materials_tr.png) | ![Zemin profili](docs/screenshots/soil_tr.png) |

## Kurulum ve çalıştırma

**Kurulum paketleri** (Python gerekmez): Windows MSI, Ubuntu DEB, Fedora / openSUSE RPM ve
Arch Linux paketleri her [sürüme](https://github.com/hdaltuntas/SlipSurfaceIQ-Settle/releases)
eklenir; ayrıntı [packaging/README.md](packaging/README.md) dosyasındadır.

**Kaynaktan**, Python 3.10 veya üstüyle:

```bash
run_windows.bat            # Windows: .venv oluşturur, paketleri kurar, başlatır
./run_linux_mac.sh         # Linux / macOS: aynısı
```

ya da elle:

```bash
pip install -r requirements.txt
python main.py                                   # pencere
python main.py slipsurface/settle/examples/strip_on_sand.settle
python main.py --check                           # bağımlılık kontrolü, pencere açmaz
```

`main.py` kendi klasörünü içe aktarma yolunun başına koyar; kurulum gerekmez ve dosya bir
IDE'de (Thonny, Spyder, VS Code …) açılıp çalıştırılabilir. Kurmak da mümkündür:
`pip install ".[docx,xlsx]"` ile `slipsurface-settle` komutu gelir.

## Tipik bir iş akışı

Üstteki iş akışı çubuğu adımları sırayla gezer; her adım girdilerini soldaki panelde,
en kullanışlı görünümünü ortada açar.

1. **Proje** — başlık ve hesabı yapan (rapor başlığında görünür).
2. **Temel / Dolgu** — şekil, boyutlar, temel derinliği Df, taban basıncı q (ya da dolgu
   geometrisi ve birim hacim ağırlığı) ve su tablası. Yalnız seçilen şekle uyan girdiler
   gösterilir.
3. **Zemin Profili** — yüzeyden aşağı tabakalar; her biri bir malzeme, bir kalınlık ve
   kil için drenaj. Malzemelerin kendisi **Özellikler › Malzemeleri Tanımla…** (Ctrl+M)
   penceresinde tanımlanır: granüler, kohezyonlu ya da sıkışmaz (kaya vb.). Kohezyonlu
   malzeme ya sıkışma indisleriyle (Cc, Cr, e0) ya da hacimsel sıkışma katsayılarıyla
   (mv, mv,ur) tanımlanır; OCR, cv ve ikincil sıkışma ile birlikte.
4. **Seçenekler** — gerilme dağılımı, ani oturma yöntemi, esnek ya da rijit temel, alt
   tabaka kalınlığı, etki derinliği, tasarım ömrü, krip; izin verilen oturma ve
   distorsiyon.
5. **Sonuçlar** — kontrolleriyle özet kartları, tam metin çıktısı ve yedi şekil.
6. **Çalışma** — soldaki panelde örnekleme yöntemi, örnek sayısı ve tohum;
   **Özellikler › Çalışma Değişkenleri…** (Ctrl+K) penceresinde değişkenler (bir aralık
   ya da dağılımla bir girdi); sonuçlar tarama, histogram, saçılım ya da tornado grafiği,
   özet ve örnek tablosu olarak.

Analiz birkaç milisaniye sürdüğünden sonuçlar ve şekiller girdideki her değişikliği izler.
Yalnız **F5** ile hesaplamak için **Analiz › Otomatik yeniden hesapla**'yı kapatın; eskiyen
sonuçlar o zaman işaretlenir. Çalışma arka planda, ilerleme çubuğuyla yürür; **Esc** iptal
eder.

| Tuş | İşlem |
|---|---|
| F5 | Hesapla |
| F6 | Çalışmayı başlat |
| Esc | Çalışmayı iptal et |
| Ctrl+N / O / S | Yeni / aç / kaydet |
| Ctrl+M / Ctrl+K | Malzemeleri / çalışma değişkenlerini tanımla |
| Ctrl+Z / Ctrl+Y | Her girdide geri al / yinele |
| Ctrl+P | PDF rapor |
| Ctrl+E | Geçerli şekli dışa aktar (PNG, SVG, PDF) |
| F1 | Teori kılavuzu |

## Hesaplananlar

Yöntemlerin özeti İngilizce [README](README.md#what-it-computes) dosyasında, türetmeler ve
sınırları [docs/theory.tr.md](docs/theory.tr.md) dosyasındadır.

## Şekiller ve raporlar

Boussinesq gerilme soğanıyla kesit · derinlikle gerilmeler (σ'v0, σ'v0 + Δσ, σ'p ve etki
derinliği ölçütü) · Schmertmann Iz ile etki katsayıları · derinlikle birikimli oturma ·
zaman–oturma eğrisi · noktalarda oturma bileşenleri · kesit boyunca oturma. Her şekil
yakınlaştırılır, kaydırılır ve dışa aktarılır.

**Dosya › Rapor**, girdileri, gerilmeleri, her noktada ve her tabakada oturmayı,
Schmertmann katsayılarını, konsolidasyon sürelerini, kontrolleri, şekilleri, uyarıları,
yöntem notlarını ve — çalıştırıldıysa — çalışmayı içeren PDF, tek dosyalık HTML ya da Word
raporu arayüzün dilinde yazar.

## Proje dosyaları (`.settle`) ve komut satırı

Proje, girdileri ve çalışma tanımını tutan bir JSON dosyasıdır; dosyada olmayan değerler
varsayılanını korur. Aynı dosya pencere açmadan da çalışır:

```bash
python main.py example -o proje.settle             # başlangıç projesi
python main.py run proje.settle -o rapor.pdf       # hesapla, yazdır, rapor yaz
python main.py study proje.settle -o ornekler.csv  # çalışmayı yürüt, örnekleri yaz
```

## Geliştirme

```bash
pip install -r requirements-dev.txt
pytest -q
ruff check . && ruff format --check .
```

## Lisans

© 2026 Hasan Deniz Altuntaş — [GNU AGPL v3 veya sonrası](LICENSE). Garanti verilmez.
