# LOKMAN – Hastane Koridoru Malzeme Taşıma Robotu

**BIMU4101 – Introduction to Mobile Robotics · Ara Sınav Projesi**

LOKMAN, hastane koridorlarında ilaç, numune tüpü ve steril malzeme taşımak için tasarladığımız diferansiyel sürüşlü bir mobil robot. Robotu URDF/Xacro ile sıfırdan modelledik, kendi hazırladığımız bir hastane koridoru dünyasında Gazebo ile simüle ettik ve ROS 2 ile kontrol ediyoruz.

İsmini Anadolu'daki şifacı figürü *Lokman Hekim*'den aldık.

<p align="center">
  <img src="docs/img/robot_yakin.png" width="700" alt="LOKMAN robotu Gazebo'da">
</p>

## Ekip

| Üye | Öğrenci no | Sensör sorumluluğu | Diğer katkılar |
|---|---|---|---|
| Ahsen Yenisey | 1306230123 | 2D LiDAR | Docker ortamı, robot modeli, diferansiyel sürüş, dünya, launch, ok tuşlu sürüş |
| İsa Şebib | 1306220177 | Kamera, IMU | Davranış düğümü (SEYİR / YAVAŞLA / KAÇIN, IMU yük koruma) |
| Hüseyin Atay | 1306230081 | Bumper (ek sensör) | GERİ ÇEKİL kuralı, rapor, demo videosu |

## Neden böyle bir robot?

Hastanelerde hemşirelerin vardiya boyunca önemli bir zamanı eczane, servis ve laboratuvar arasında malzeme taşımakla geçiyor. LOKMAN'ın görevi bu taşıma işini üstlenmek ve bunu yaparken koridordaki insanlara, sedyelere ve tekerlekli sandalyelere çarpmamak.

Tasarım kararlarını hep koridor ortamından yola çıkarak verdik:

- **Dar gövde (44 cm) ve yerinde dönebilme:** Kapılardan geçer, asansörde dönebilir.
- **Yarım daire şeklinde burun:** Çarpma anında keskin köşe yok. Duvara sürtünürse takılmadan kayar.
- **Alçağa yerleştirilmiş LiDAR (33 cm):** Sedye ayakları ve tekerlekli sandalye gibi alçak engelleri görebilsin diye.
- **Bel hizasında çekmeceler:** Hemşire eğilmeden yük koyup alabilsin diye.
- **Maksimum 0,4 m/s hız:** İnsan yürüyüşünden belirgin şekilde yavaş.

Bütün ölçüler, renkler ve sensör konumları gerekçeleriyle birlikte [`docs/tasarim.md`](docs/tasarim.md) dosyasında.

## Simülasyon dünyası

L şeklinde, 2,4 m genişliğinde bir hastane koridoru hazırladık. İçinde ıslak zemin levhası, sedye, devrik bir tabure, tekerlekli sandalye, bekleme sıraları, ayakta duran bir hemşire ve hemşire bankosu var. Bütün modeller basit geometrik şekillerden kendimiz oluşturduk, hazır model kullanmadık.

<p align="center">
  <img src="docs/img/dunya_genel.png" width="700" alt="Hastane koridoru dünyası">
</p>

Engelleri bilerek seçtik. Örneğin **sedyenin** yalnızca ince ayakları LiDAR'ın tarama yüksekliğine denk geliyor. **Devrik tabure** ise 20 cm yüksekliğinde, yani LiDAR'ın tarama düzleminin altında kalıyor. LiDAR onu göremiyor, bu yüzden bumper sensörüne ihtiyaç var.

## Sensörler

| Sensör | Konum | ROS 2 topic | Mesaj tipi | Görselleştirme |
|---|---|---|---|---|
| 2D LiDAR | Burnun üstü, yerden 0,33 m | `/scan` | `sensor_msgs/msg/LaserScan` | RViz |
| Kamera | Kabinin ön üstü, 0,86 m, 15° aşağı eğik | `/kamera/image_raw` | `sensor_msgs/msg/Image` | rqt_image_view, RViz |
| IMU | Gövde merkezi, tahrik aksının üstü (0,13 m) | `/imu` | `sensor_msgs/msg/Imu` | rqt_plot |
| Bumper | Burnu saran tampon, 0,05–0,11 m | `/bumper` | `ros_gz_interfaces/msg/Contacts` | zaman grafiği, terminal |

Kamera ayrıca `/kamera/camera_info` (`sensor_msgs/msg/CameraInfo`) yayınlıyor. Davranış düğümü bumper temasını görselleştirmek için `/lokman/bumper_temas` (`std_msgs/msg/Bool`) topic'ine de yayın yapıyor.

<p align="center">
  <img src="docs/img/rviz_lidar_kamera.png" width="800" alt="RViz: LiDAR noktaları ve kamera görüntüsü">
</p>

*RViz görüntüsü: Kırmızı noktalar LiDAR'ın gördüğü duvarlar ve engeller, sol alttaki panel ise kamera görüntüsü.*

<p align="center">
  <img src="docs/img/kamera_goruntusu.png" width="480" alt="Robotun kamerasından koridor">
</p>

*Robotun kamerasından görünen koridor.*

<p align="center">
  <img src="docs/img/bumper_temas.png" width="700" alt="Bumper'ın devrik tabureye teması">
</p>

*Devrik tabure LiDAR'ın tarama düzleminin altında kalıyor. Robot ona çarptığında bumper temas algılıyor.*

<p align="center">
  <img src="docs/img/bumper_grafik.png" width="700" alt="Bumper teması ve hız komutu grafiği">
</p>

*Üstte bumper temasları, altta `/cmd_vel` hız komutu. Her temastan hemen sonra hız −0,1 m/s'ye iniyor (geri çekilme).*

## Davranış düğümü: kibar koridor sürüşü

`kibar_surus` düğümü LiDAR, IMU ve bumper verisine göre karar veren öncelikli bir durum makinesi. Sensör geri çağırmaları yalnızca en son veriyi saklıyor, kararı saniyede 10 kez çalışan bir zamanlayıcı veriyor. Kurallar yukarıdan aşağı kontrol ediliyor, ilk tutan kural uygulanıyor:

| Öncelik | Durum | Koşul | Hareket |
|---|---|---|---|
| 1 | GERİ ÇEKİL | Bumper temas etti | 1,5 s geri (−0,1 m/s), sonra 1 s boş tarafa dönüş (0,8 rad/s) |
| 2 | KAÇIN | Önde engel ≤ 0,5 m (çıkış > 0,8 m) | Dur, daha boş tarafa yerinde dön |
| 3 | YAVAŞLA | Önde engel 0,5–1,0 m | Hız mesafeyle orantılı düşer (en az 0,08 m/s) |
| 4 | SEYİR | Önde engel > 1,0 m | 0,35 m/s, koridorun ortasında kal |
| + | YÜK KORUMA | IMU yatay ivmesi > 2,0 m/s² | 2 s boyunca hız yarıya iner |

LiDAR verisi 0,5 s'den eskiyse robot durur. Düğüm kapatılırken robota son olarak "dur" komutu gönderilir. Eşiklerin hepsi `kibar_surus.py` dosyasının başında, ölçüm gerekçeleriyle birlikte tanımlı.

<p align="center">
  <img src="docs/img/geri_cekil_log.png" width="700" alt="GERİ ÇEKİL durum geçişleri">
</p>

*Bumper teması sırasında durum geçişleri: SEYİR → GERİ ÇEKİL → SEYİR.*

## Kurulum

Proje **ROS 2 Lyrical** ve **Gazebo Jetty** ile çalışıyor (Ubuntu 26.04). Herkesin bilgisayarında aynı ortamın olması için her şeyi bir Docker konteynerinin içinde çalıştırıyoruz. Gazebo ve RViz pencereleri tarayıcıdan (noVNC) açılıyor. Yani bilgisayarınıza ROS kurmanız gerekmiyor.

### Gerekenler

- **macOS:** [OrbStack](https://orbstack.dev) (veya Docker Desktop)
- **Windows:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (WSL 2 ile)
- Git

### Adımlar

```bash
git clone https://github.com/ahsenyenisey/lokman-hastane-robotu.git
cd lokman-hastane-robotu
```

**macOS / Linux:**
```bash
./baslat.sh
```

**Windows (PowerShell):**
```powershell
.\baslat.ps1
```

İlk çalıştırmada Docker imajı derleniyor. İnternet hızına göre 10–20 dakika sürebilir. Sonraki açılışlar birkaç saniye sürer. İşlem bitince tarayıcıda masaüstü açılır. Açılmazsa şu adrese gidin: http://localhost:6080/vnc.html

Tarayıcıdaki masaüstünde bir terminal açıp (**Applications → Terminal Emulator**) çalışma alanını derleyin. Bunu sadece ilk seferde ve kod değiştiğinde yapmanız yeterli:
```bash
cd /ws/ros2_ws
colcon build --symlink-install
source install/setup.bash
```

## Çalıştırma

**Simülasyon (Gazebo + robot + RViz tek komutla):**
```bash
ros2 launch lokman_gazebo lokman.launch.py
```

Ek seçenekler:
```bash
ros2 launch lokman_gazebo lokman.launch.py dunya:=empty.sdf          # boş dünyada test
ros2 launch lokman_gazebo lokman.launch.py x:=8.0 y:=0.0 yaw:=1.57   # başlangıç konumu
```

**Robotu ok tuşlarıyla sürmek** (ikinci bir terminalde):
```bash
ros2 run lokman_behavior ok_tuslari
```
↑ ↓ ← → ile sürülür, boşluk tuşu durdurur, `q` çıkar. Tuşu bırakınca robot kendiliğinden durur.

**Robotu kendi başına sürmek** (davranış düğümü, ikinci bir terminalde):
```bash
ros2 run lokman_behavior kibar_surus
ros2 topic echo /lokman/durum            # robotun anlık durumu
```

**Sensör verilerini kontrol etmek:**
```bash
ros2 topic list                          # bütün topic'ler
ros2 topic hz /scan                      # LiDAR yayın hızı
ros2 topic echo /scan --once             # tek bir LiDAR mesajı
ros2 run rqt_image_view rqt_image_view   # kamera görüntüsü
ros2 run rqt_plot rqt_plot               # IMU (topic pencereden eklenir)
ros2 topic echo /bumper                  # bumper temasları
```

Simülasyonu kapatmak için launch komutunu çalıştırdığınız terminalde **Ctrl+C**'ye basın. Ortamı tamamen kapatmak için ana bilgisayarda `./durdur.sh` (Windows'ta `.\durdur.ps1`) çalıştırın.

## Proje yapısı

```
.
├── docker/                    # Docker ortamı (Ubuntu 26.04 + ROS 2 Lyrical + Gazebo Jetty + noVNC)
├── docker-compose.yml
├── baslat.sh / baslat.ps1     # ortamı başlatır
├── durdur.sh / durdur.ps1     # ortamı durdurur
├── terminal.sh / terminal.ps1 # konteynerin içinde terminal açar
├── docs/
│   ├── tasarim.md             # tasarım kararları ve gerekçeleri
│   └── img/                   # ekran görüntüleri
└── ros2_ws/src/
    ├── lokman_description/    # robot modeli (URDF/Xacro) ve RViz ayarı
    │   └── urdf/
    │       ├── lokman.urdf.xacro    # ana model dosyası
    │       ├── ortak.xacro          # renkler, eylemsizlik formülleri
    │       ├── chassis.xacro        # gövde, kabin, tekerlekler, caster'lar
    │       ├── surus.gazebo.xacro   # diferansiyel sürüş eklentisi
    │       └── lidar / camera / imu / bumper .xacro   # her sensör ayrı dosyada
    ├── lokman_gazebo/         # dünya, launch dosyası, Gazebo↔ROS köprü ayarları
    │   ├── worlds/hastane_koridoru.sdf
    │   ├── launch/lokman.launch.py
    │   └── config/kopru*.yaml
    └── lokman_behavior/       # Python düğümleri
        └── lokman_behavior/
            ├── ok_tuslari.py        # ok tuşlarıyla elle sürüş
            └── kibar_surus.py       # sensör tabanlı davranış düğümü
```

## Hareket sistemi

Diferansiyel sürüş kullanıyoruz. İki tahrikli tekerlek gövdenin ortasında aynı aks üzerinde duruyor, önde ve arkada birer sarhoş teker (caster) var. Bu sayede robot kendi ekseni etrafında dönebiliyor. Gazebo'nun `DiffDrive` eklentisi `/cmd_vel` topic'inden gelen hız komutunu teker hızlarına çeviriyor:

```
v_sol = v − ω · L/2
v_sağ = v + ω · L/2        (L = 0,36 m teker aralığı)
```

Ani kalkış ve frenlerde taşınan yük sarsılmasın diye eklentiye ivme sınırı da koyduk (0,8 m/s²).

## Bilinen sorunlar

- Konteynerde ekran kartı olmadığı için Gazebo görüntüyü işlemciyle çiziyor. Bu yüzden biraz yavaş çalışabilir. Varsayılan render motoru (Ogre2) bu durumda pencerenin donmasına yol açtığı için launch dosyasında daha hafif olan **Ogre1** motorunu seçtik.
- Ekran kartı olmadığı için sensörler hedef yayın hızlarının %85–90'ında çalışıyor. Davranış 10 Hz'de karar verdiği için bu fark davranışı etkilemiyor.
- Devrik tabure LiDAR'ın altında kaldığı için robot geri çekildikten sonra onu yine göremiyor ve aynı engele birkaç kez temas edebiliyor.
- RViz'de robot modeli gri görünüyor (renkler yalnızca Gazebo'da görünüyor). Bu durum yazılımsal çizimle ilgili ve işlevi etkilemiyor.

## Durum

- [x] Docker tabanlı geliştirme ortamı
- [x] Robot modeli ve diferansiyel sürüş
- [x] Hastane koridoru dünyası ve tek launch dosyası
- [x] Ok tuşlarıyla sürüş
- [x] Sensörler: LiDAR, kamera, IMU, bumper
- [x] Sensör tabanlı davranış düğümü ("kibar koridor sürüşü")
- [x] Rapor ve sunum
