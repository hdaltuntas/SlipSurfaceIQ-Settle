---
title: "SlipSurface IQ Settle teori"
description: "SlipSurface IQ Settle teorisi: gerilme yayılımı, anlık, konsolidasyon ve ikincil oturma, zaman eğrileri, kaynaklar."
---

# SlipSurface IQ Settle — teori

SlipSurface IQ Settle'ın ne hesapladığı ve yöntemin nerede geçerliliğini yitirdiği. `z` derinliği zemin
yüzeyinden, `z_b = z − Df` ise temel tabanından ölçülür.

## 1. Yerinde gerilmeler

σv0(z) = su seviyesinin üstünde Σ γ·Δz, altında Σ γsat·Δz; yeraltı su seviyesinin altında u0 = γw·(z − z_w);
σ'v0 = σv0 − u0. Son tabaka, yalnızca gerilme hesabı için, profilin altında devam ediyormuş gibi alınır. Kohezyonlu bir
tabakada σ'p = OCR·σ'v0 (OCR tabaka başına sabit; OCR < 1 desteklenmez, uyarıyla 1 alınır).

## 2. Net basınç

Kazılan zemin yükü düşülüyorsa q_net = q − σv0(Df), düşülmüyorsa q. Boşluk suyu basınçları dengelendiğinde efektif gerilme
değişimi toplam gerilme değişimine eşittir; bu yüzden aynı q_net hem elastik hem konsolidasyon oturmasını doğurur. Sıfır
veya negatif q_net, dengelenmiş (kompanse) bir temeldir: oturma olmaz.

## 3. Gerilme artışı

**Dikdörtgen** — a × b alanının köşesi altında Boussinesq çözümünün Newmark integrasyonu, m = a/z, n = b/z:

    I = 1/(4π) · [ 2mn√(m²+n²+1)/(m²+n²+1+m²n²) · (m²+n²+2)/(m²+n²+1)
                   + atan2(2mn√(m²+n²+1), m²+n²+1−m²n²) ]

`atan2`, ders kitabı formülünün π ekleyerek düzelttiği kolu alır. Plandaki herhangi bir nokta (içte, kenarda ya da dışta),
dört köşe dikdörtgeninin işaretli toplamıdır.

**Şerit** — Δσ/q = [θ₁ − θ₂ + sinθ₁cosθ₁ − sinθ₂cosθ₂]/π, θ = atan((x ± B/2)/z).

**Daire** — Boussinesq çözümü yarıçap boyunca integre edilince
Δσ/q = (1/2π) ∮ [g(r₁) − g(r₂)] dθ kalır; g(r) = z³/(z² + r²)^{3/2}, r₁ ve r₂ noktadan θ yönünde çıkan ışının daireye
girdiği ve çıktığı uzaklıklardır. Daire için ikisi de açıktır; integral bir boyutludur ve sayısal integrasyon hassasiyetince
(720 adım) kesindir; merkezde kapalı form 1 − (z²/(z²+R²))^{3/2} kullanılır.

**2:1** — q·B·L/((B+z)(L+z)), q·B/(B+z), q·D²/(D+z)²: genişletilmiş alan üzerinde ortalama; her noktada aynıdır, bu yüzden
2:1 altında konsolidasyon oturması plan boyunca değişmez.

**Dolgu** — zemin yüzeyinde uzun bir dolgu: mahya genişliği b, yükseklik H, şev açıları β_L, β_R, birim hacim ağırlık γ. Yük,
mahya altında p(x) = γH'dir ve şev uzunlukları H/tan β boyunca doğrusal olarak sıfıra düşer. p = A + Bξ olan bir parça için
Flamant çizgi yükü 2p z³/(π((ξ−x)² + z²)²), u = ξ − x ile integre edilince

    Δσ = (A + Bx)·[atan(u/z) + uz/(u² + z²)]/π − B·z³/(π(u² + z²))

parçanın uçları arasında verilir; dolgu üç parçasının toplamıdır, böylece gerilme her noktada kesindir (düzlem şekil değiştirme).
2:1 altında dolgu, aynı yükün düzgün şeridi ile değiştirilir; genişliği b + (run_L + run_R)/2'dir. Değerlendirme noktaları
mahya merkezi, mahya kenarı, (sağ) şevin ortası ve şev topuğudur. Elastik oturma, düzlem şekil değiştirmedeki Steinbrenner
şeritlerini üst üste bindirir: mahya bir şerit, her şev yükü ortalarında taşıyan 16 dilim (%0,2'ye yakınsar). Dolgu esnektir;
Schmertmann'ın temel diyagramı uygulanmaz ve açısal distorsiyon kontrol edilmez. Dolgunun kendi sıkışması, drenajsız yanal
yayılma ve stabilite programın dışındadır.

## 4. Etki derinliği

Taban altındaki profil alt tabakalara bölünür (varsayılan 0,25 m). Oturma, merkezdeki Δσ'nın hâlâ σ'v0'ın seçilen oranına
(varsayılan 0,1; 0 tüm profili toplar) eşit ya da daha büyük olduğu en derin alt tabakanın tabanına kadar toplanır. Profilin
tabanı sıkışmaz kabul edilir; tabandaki Δσ hâlâ ≥ 0,1·σ'v0 ise program uyarır.

## 5. Anlık oturma

**Elastik (Steinbrenner).** Rijit tabana oturan H kalınlığındaki elastik bir tabaka üzerindeki esnek a × b dikdörtgeninin köşesi
altında, M = L/B, N = H/B (B kısa kenar):

    s = q·B/E · [ (1 − ν²)·F1 + (1 − ν − 2ν²)·F2 ]
    F1 = (A0 + A1)/π,   F2 = N/(2π)·atan(A2)
    A0 = M·ln[(1+√(M²+1))·√(M²+N²) / (M·(1+√(M²+N²+1)))]
    A1 = ln[(M+√(M²+1))·√(1+N²) / (M+√(M²+N²+1))]
    A2 = M / (N·√(M²+N²+1))

Taban altında z₁ ile z₂ arasındaki bir tabakanın oturması, parantezin iki derinlikteki farkının q/E katıdır (tabakalı yöntem);
her tabaka kendi E ve ν değerini kullanır ve herhangi bir nokta dört köşeden üst üste bindirilir. Şerit, 200 B uzunluğunda bir
dikdörtgendir; daire, aynı alanlı karedir ve noktaları yarı genişliğin aynı oranına yerleştirilir. Kil tabakaları drenajsız E
ve ν (≈ 0,5) değerlerini kullanır; bu da konsolidasyondan önce gelen drenajsız distorsiyon oturmasını verir.

**Schmertmann vd. (1978)**, yalnızca granüler tabakalar:

    s = C1·C2·q_net·Σ (Iz/E)·Δz
    C1 = 1 − 0.5·σ'v0(Df)/q_net ≥ 0.5,   C2 = 1 + 0.2·log10(t/0.1 yıl)
    Izp = 0.5 + 0.1·√(q_net/σ'vp),   σ'vp tepe noktası derinliğinde

Etki diyagramı, L/B = 1 için tabanda Iz = 0,1'den B/2'de Izp'ye ve 2B'de sıfıra; L/B ≥ 10 için 0,2'den B'de Izp'ye ve 4B'de
sıfıra uzanır, aradaki L/B değerleri için doğrusal enterpolasyon yapılır. Sonuç temelin oturmasıdır; diğer noktalarda, aynı
granüler alt tabakaların o noktadaki elastik oturmasının merkezdekine oranıyla ölçeklenir. E doğrudan girilir (Schmertmann,
eksenel simetrik yükleme için E = 2,5·qc, düzlem şekil değiştirme için 3,5·qc önerir).

## 6. Birincil konsolidasyon

Her kil alt tabakası için, her değerlendirme noktasında, σ'f = σ'v0 + Δσ ile:

    Δe = Cr·log10(min(σ'f, σ'p)/σ'v0) + Cc·log10(max(σ'f, σ'p)/σ'p)
    s  = Σ Δe/(1 + e0) · Δz

Skempton–Bjerrum düzeltmesi uygulanmaz; bir boyutlu değer, dar bir temel altındaki aşırı konsolide kil için güvenli
tarafta kalır.

**Hacimsel sıkışma katsayılarıyla.** Kil, bunun yerine mv ve mv,ur [m²/MN] ile — bakir ve
boşaltma–yeniden yükleme kollarının eğimiyle — tanımlanabilir:

    ε = mv,ur·(min(σ'f, σ'p) − σ'v0) + mv·max(σ'f − σ'p, 0)
    s = Σ ε · Δz

OCR = 1 (σ'p = σ'v0) iken bu klasik s = Σ mv·Δσ'·Δz bağıntısıdır. mv gerilme düzeyine
bağlıdır; tabakanın gerçekten gördüğü gerilme aralığında (σ'v0'dan σ'v0 + Δσ'ya) ölçülen
değer olmalıdır.

**Sıkışmaz birimler.** Kaya ya da sıkışmaz kabul edilen herhangi bir birim ani, birincil ve
ikincil oturma almaz. Ağırlığı yerinde gerilmelerde yine sayılır; içindeki ve altındaki
gerilme artışı yine homojen yarı sonsuz ortamınkidir (rijit tabakanın gerilmeyi yoğunlaştırma
ya da yayma etkisi modellenmez). E = 0 verilen kile ani oturma verilmez — yalnız konsolidasyon.

## 7. Zaman

Düzgün başlangıç aşırı boşluk suyu basıncı için Terzaghi'nin ortalama konsolidasyon derecesi,
U = 1 − Σ 2/M²·exp(−M²Tv), M = π(2m+1)/2; Tv < 10⁻³ için √(4Tv/π); Tv = cv·t/H_dr², çift drenajda H_dr = H/2, tek drenajda H;
H taban altındaki tabakanın kalınlığıdır. Tv(U) ikiye bölme ile bulunur, böylece U(Tv(U)) = U tam olarak sağlanır. Her kil
tabakası bağımsız olarak konsolide olur; ortak drenaj sınırı üzerinden tabakalar arasındaki etkileşim yok sayılır. cv'si olmayan
kilin hemen konsolide olduğu varsayılır.

## 8. İkincil sıkışma

Birincil konsolidasyonun sonundan (U = %95, t_p) tasarım ömrüne kadar:
s = Cα/(1 + e0)·Δz·log10(t/t_p). Cα/Cc bir zemin sabiti olduğundan (Mesri), σ'f değeri σ'p'nin altında kaldığı yerde kil
yeniden sıkışma doğrusu boyunca sünme yapar ve onun yerine Cα·Cr/Cc kullanılır. (1 + e_p) için e0 kullanılır. mv ile tanımlanan kil doğrudan Cαε = Cα/(1 + e0) oranını kullanır,
s = Cαε·Δz·log10(t/t_p); σ'p'nin altında mv,ur/mv oranında azaltılır.

## 9. Rijit temel, distorsiyon, kontroller

Rijit bir temel, karakteristik noktasının oturması kadar düzgün oturur (Grasshoff: dikdörtgen veya şeritte merkezden yarı
genişliklerin 0,74'ü, dairede 0,845·R). Esnek bir temelin açısal distorsiyonu β = |s_merkez − s_kenar| / (B/2)'dir (daire için R);
rijit temelde kontrol edilmez. Belirleyici noktanın (merkez veya karakteristik nokta) toplam oturması ve β, izin verilen
değerlerle karşılaştırılır.

## 10. Çalışmalar

Girdiler aralık (LHS / Monte Carlo'da düzgün, tek-tek taramada n eşit aralıklı nokta) veya dağılım (normal; verilen ortalama ve
değişim katsayısıyla log-normal; ortalama ± √3·σ üzerinde düzgün) olarak değişir. Aşılma olasılıkları P = k/n, Wilson %95 aralığı
taşır; β = −Φ⁻¹(P), hiçbir şey aşılmadıysa "> −Φ⁻¹(3/n)" olarak verilir. Duyarlılıklar Spearman sıra korelasyonlarıdır.
