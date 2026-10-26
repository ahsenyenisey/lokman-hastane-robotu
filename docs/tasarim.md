# LOKMAN – Hastane Koridoru Malzeme Taşıma Robotu
### Aşama 1 · Tasarım Kararları ve Gerekçeleri

> Bu doküman raporun "Görev ve Tasarım" bölümünün ham hâlidir. Her kararın yanında **neden** öyle yaptığımız yazıyor; sunumda hocanın "neden?" sorularına cevaplar buradadır.

---

## 1. Görev ve senaryo

**İsim:** LOKMAN — Anadolu geleneğindeki şifacı figürü *Lokman Hekim*'den. Hastane bağlamına uyan, akılda kalan ve bize ait bir isim.

**Problem:** Hastanelerde hemşireler vardiya boyunca zamanlarının ciddi bir kısmını eczane ↔ servis ↔ laboratuvar arasında malzeme taşımaya harcıyor. Bu, hasta başında geçmesi gereken zamandan çalınıyor.

**LOKMAN'ın görevi:** Kilitli çekmecelerinde ilaç, numune tüpü veya steril malzeme taşıyarak hastane koridorunda **insanlara, sedyelere ve tekerlekli sandalyelere çarpmadan** ilerlemek.

**Koridor ortamını zor yapan şeyler (ve tasarımı yönlendiren şey bunlar):**

| Ortamın özelliği | Tasarıma etkisi |
|---|---|
| Dar koridorlar, kapılar, asansörler | Dar gövde, **yerinde dönebilme** |
| Hareketli insanlar, yaşlılar, çocuklar | Düşük hız, yaklaştıkça **kademeli yavaşlama**, yumuşak ön burun |
| Alçak engeller (sedye ayağı, tekerlekli sandalye ayaklığı) | LiDAR'ın **alçağa** yerleştirilmesi |
| LiDAR'ın kaçırabileceği şeyler (cam kapı, çok alçak cisim) | Son savunma hattı olarak **bumper** |
| Taşınan yük hassas (ilaç şişesi, kan tüpü) | **IMU** ile sarsıntı ve eğim takibi |
| Hemşirenin robota yük koyup alması | Çekmecelerin **bel hizasında** olması |

---

## 2. Hareket sistemi: Diferansiyel sürüş, **orta akslı**

```
        ÜSTTEN GÖRÜNÜM (ön taraf sağda →)

            ┌───────────────────╮
            │                    ╲
   caster ○ │   ▐█▌ sol teker     ╲     ← yarım daire burun
   (arka)   │         ✚ IMU        │ ◉ LiDAR     ═══ bumper
            │   ▐█▌ sağ teker     ╱
            │                    ╱   ○ caster (ön)
            └───────────────────╯
```

- **İki tahrikli tekerlek gövdenin ortasında (aynı aks üzerinde), önde ve arkada birer sarhoş teker (caster).**
- **Gerekçe 1 – Yerinde dönüş:** Tahrik aksı gövde merkezine yakın olduğundan robot kendi ekseni etrafında döner. Dönerken süpürdüğü daire en küçük olur (çap ≈ 0,74 m). Dar koridorda ve asansörde manevra için bu kritik.
- **Gerekçe 2 – Neden skid-steer değil?** Dört tahrikli kaygan dönüş, hastane zemininde (PVC/epoksi) lastik izi bırakır, gürültülüdür ve daha çok enerji harcar. Diferansiyel sürüş daha sessiz ve verimli. Hastane için sessizlik bir gereksinim.
- **Gerekçe 3 – İki caster:** Tek caster'lı üç tekerlek düzeninde ağırlık merkezi kenara kayınca robot devrilmeye yatkın olur. Üstte bir çekmece kabini taşıdığımız için **ön + arka caster** ile dört temas noktası seçtik.
- **Tekerlekler gövdenin içinde (çamurluk içinde):** Dışarı taşan teker, koridordaki bir ayağı veya sedye tekerini sıkıştırabilir. İç tekerlek bu yüzden bir güvenlik kararı.
- **ROS/Gazebo karşılığı:** Gazebo'nun `DiffDrive` sistemi. `/cmd_vel` (`geometry_msgs/Twist`) komutunu alır, `/odom` yayınlar.

---

## 3. Ölçüler

| Parametre | Değer | Gerekçe |
|---|---|---|
| Genişlik | **0,44 m** | Standart bir hastane kapısından (yaklaşık 0,9 m) rahatça geçer. Koridorda bir insan veya sedye yanından geçebilir. |
| Toplam uzunluk | **0,62 m** (0,40 m kasa + 0,22 m yarım daire burun) | Standart bir asansöre girip içinde dönebilir. |
| Toplam yükseklik | **~0,95 m** | Çekmeceler bel hizasında, hemşire eğilmeden yük koyar ve alır (ergonomi). |
| Tekerlek yarıçapı / genişliği | **0,08 m / 0,04 m** | Asansör eşiği ve kapı geçişleri için yeterli büyüklükte. Daha büyük teker, gövdeyi yükseltip ağırlık merkezini yukarı taşırdı. |
| Tekerlek aralığı (merkezden merkeze) | **0,36 m** | Tekerlekler gövde içinde kalırken yan yana devrilmeye karşı en geniş taban. |
| Yerden açıklık | **0,04 m** | Eşik geçişi için yeterli, aynı zamanda alçak gövde. |
| Kütle | Taban 18 kg (bataryalar burada), kabin 6 kg | **Ağır kısım altta**, böylece ağırlık merkezi alçalır ve ani duruşta devrilme riski azalır. |
| Maksimum hız | **0,4 m/s** | İnsan yürüyüşü yaklaşık 1,2 m/s. Kalabalık ortamda robot insandan belirgin şekilde yavaş olmalı, yaklaşanlar onu kolayca fark edip yön değiştirebilmeli. |

---

## 4. Görünüm: neden böyle görünüyor?

Her görsel karar bir işlevden geliyor.

| Öğe | Görünüm | Gerekçe |
|---|---|---|
| **Gövde** | Mat beyaz | Hastane hijyeni: kir hemen görünür, dezenfektanla silinir. |
| **Ön burun** | Yarım daire (keskin köşe yok) | Çarpma anında insana nokta temas yerine yayılan temas. Ayrıca robot duvar veya kapı kasasına sürtünürse kenarından kayar, takılmaz. |
| **Arka yüz** | Düz | Şarj istasyonuna yaslanma (docking) yüzeyi. |
| **Şerit** | Gövdeyi çevreleyen turkuaz bant | Sağlık temalı ama göz yormayan bir renk. Koridorda uzaktan "bu bir hastane cihazı" diye okunur. |
| **Bumper** | Turuncu, burun boyunca uzanan bir şerit | Görülebilirlik rengi. İnsanlar robotun "çarpma kenarını" sezgisel olarak görür. |
| **Kabin** | İki çekmeceli, kulplu, hafif gri | Çekmece = kilitlenebilir bölmeler (ilaç güvenliği). İki bölme: biri ilaç, biri numune (karışma önlenir). |
| **Durum feneri** | Kabinin üstünde yeşil bir halka | Uzaktan görülen durum ışığı. Gerçek sistemde yeşil = seyir, sarı = yavaşlıyor, kırmızı = durdu anlamına gelir. |
| **Kırmızı haç YOK** | — | Bilinçli bir karar: Kızılhaç/Kızılay amblemi uluslararası hukukla korunuyor ve rastgele cihazlarda kullanılamaz. Turkuaz bant bu yüzden seçildi. |

---

## 5. Sensörler ve yerleşimleri

| Sensör | Sorumlu | Konum (`base_link`'e göre) | Teknik ayar | Neden **orada**? |
|---|---|---|---|---|
| **2D LiDAR** | [SORUMLU ÜYE] | Burnun üstünde, önde, **~0,33 m yükseklikte** | 270° tarama, 0,12–8 m menzil, 10 Hz | **Alçakta**, çünkü koridordaki tehlikeli engeller (sedye ayağı, tekerlekli sandalye ayaklığı, bir çocuk) alçak. 1 m yüksekteki bir LiDAR bunları görmez. **270°**, çünkü arkası kabinle kapalı. Robot zaten ileri gidiyor ve 270° yanları da kapsıyor. |
| **Kamera** | [SORUMLU ÜYE] | Kabinin ön üst kısmında, **~0,85 m yükseklikte, 15° aşağı eğik** | 640×480, 15 Hz | Bu yükseklikte hem önündeki zemini hem de duvardaki oda/kapı numaralarını görür. Aşağı eğim, 1,5 m ilerisindeki zemini de görüş alanına alır. 15 Hz, yazılımsal render altında akıcı çalışmak için bir uzlaşı. |
| **IMU** | [SORUMLU ÜYE] | **Gövdenin tam merkezinde, tahrik aksının üstünde** | 100 Hz, ivme + açısal hız + yönelim | Robot yerinde dönerken dönme merkezi burası. Bu noktada merkezkaç ivmesi en düşük olur. IMU böylece dönüşten değil **gerçek sarsıntı ve eğimden** kaynaklanan veriyi ölçer. Bu sarsıntı, taşınan ilacın maruz kaldığı sarsıntının ta kendisi. |
| **Bumper (temas)** | **Ortak** | Burun boyunca, **yerden 0,05–0,11 m** | Temas olayı | LiDAR'ın **kör kaldığı durumlar** için son savunma hattı: tarama düzleminin altında kalan alçak cisimler ve gerçek hayatta cam kapı veya ayna gibi lazerin geçip gittiği yüzeyler. |

**Sensörlerin birbirini tamamlaması (sunumda vurgulanacak):**
**LiDAR uzağı görür → yavaşlar ve kaçınır. Bumper LiDAR'ın kaçırdığını yakalar → geri çekilir. IMU yükün ne yaşadığını ölçer. Kamera insan gözüyle bakar → görselleştirme ve işaret tanıma.**

---

## 6. Davranış: "Kibar koridor sürüşü" (Aşama 5'te yazılacak)

Sıradan "engel görünce dön" yerine, **hastane görgüsüne uygun** bir durum makinesi:

| Durum | Ne zaman? | Ne yapar? |
|---|---|---|
| 🟢 **SEYİR** | Önde 1,0 m içinde engel yok | 0,4 m/s ile ilerler |
| 🟡 **YAVAŞLA** | Ön sektörde en yakın engel 0,5–1,0 m arası | Hızı mesafeyle **orantılı** düşürür. İnsan aniden önüne çıkarsa robot sert fren yapmaz. |
| 🟠 **KAÇIN** | Engel 0,5 m'den yakın | Durur, **sol ve sağ sektörlerden hangisi daha boşsa** o tarafa yerinde döner |
| 🔴 **GERİ ÇEKİL** | Bumper temas algıladı | Hemen durur, ~1,5 s yavaşça geri gider, sonra boş tarafa döner |
| 🟣 **YÜK KORUMA** (IMU) | IMU'nun ölçtüğü yatay ivme 2,0 m/s² eşiğini aşarsa | Hız 2 saniye boyunca yarıya düşürülür, böylece yük sarsılmaz. Bu kural diğer durumların **üstüne** uygulanır. |

- **IMU'nun karar kuralı tek cümleyle:** *"Yük sarsılıyorsa yavaşla."* Ani fren, kalkış veya çarpma IMU'da ivme sıçraması olarak görünür. Robot bunu görünce 2 saniye boyunca yarı hızla devam eder. Böylece IMU yalnızca görselleştirilmekle kalmaz, davranışı da doğrudan etkiler.
- Karar kuralının tamamı kodda Türkçe yorumlarla açıklanacak.

---

## 7. Gazebo dünyası (Aşama 3'te yapılacak)

**Bir hastane katının koridoru:**
- L şeklinde, ~2,4 m genişliğinde bir koridor ve yanlarda hasta odası kapıları
- Engeller: koridora park edilmiş bir **sedye**, bir **tekerlekli sandalye**, **bekleme sandalyeleri**, ayakta duran bir **insan** (basit bir silüet), bir **hemşire bankosu**
- Tümü basit geometrik şekillerden yapılacak. İnternetten model indirmeye gerek kalmaz, yazılımsal render altında hızlı çalışır ve tamamen bize ait olur.

---

## 8. Yazılım paketleri

| Paket | İçerik |
|---|---|
| `lokman_description` | Robot modeli: `lokman.urdf.xacro`, `chassis.xacro`, `lidar.xacro`, `camera.xacro`, `imu.xacro`, `bumper.xacro` ve RViz ayarı |
| `lokman_gazebo` | Hastane dünyası (`.sdf`), `ros_gz_bridge` ayarları, **tek launch dosyası** |
| `lokman_behavior` | Python davranış düğümü (`kibar_surus` düğümü) |

**Commit sorumlulukları:**
- `lidar.xacro` → [SORUMLU ÜYE]
- `camera.xacro` → [SORUMLU ÜYE]
- `imu.xacro` → [SORUMLU ÜYE]
- `bumper.xacro` → ortak (üçünüz de katkı verebilirsiniz)
- Diğer dosyalar → repo sahibi
