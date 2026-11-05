"""
KİBAR KORİDOR SÜRÜŞÜ – LOKMAN'ın sensör tabanlı davranış düğümü.

Kullanım:  ros2 run lokman_behavior kibar_surus
           (simülasyon açıkken; ok_tuslari düğümü KAPALI olmalı, ikisi aynı
            anda /cmd_vel'e yazarsa robot iki komut arasında kalır)

Yazarlar:  İsa Şebib   – LiDAR kuralları (SEYİR / YAVAŞLA / KAÇIN), IMU yük koruma
           Hüseyin Atay – Bumper refleksi (GERİ ÇEKİL)

GİRDİLER (abonelikler)
  /scan    sensor_msgs/msg/LaserScan   LiDAR: 240 ışın, -120° … +120°
  /imu     sensor_msgs/msg/Imu         IMU: ivme + açısal hız, ~100 Hz
  /bumper  ros_gz_interfaces/Contacts  Bumper (Hüseyin ekleyecek)

ÇIKTILAR (yayınlar)
  /cmd_vel       geometry_msgs/msg/Twist  Hız komutu (linear.x m/s, angular.z rad/s)
  /lokman/durum  std_msgs/msg/String      O anki durum (demoda izlemek için)

KARAR KURALI (öncelik sırasıyla, ilk tutan kural uygulanır)
  🔴 GERİ ÇEKİL  bumper temas etti           → geri git, sonra boş tarafa dön   [Hüseyin]
  🟠 KAÇIN       önde engel ≤ 0.50 m         → dur, daha boş tarafa yerinde dön
  🟡 YAVAŞLA     önde engel 0.50 – 1.00 m    → hızı mesafeyle orantılı düşür,
                                               boş tarafa hafifçe yönel
  🟢 SEYİR       önde 1.00 m içinde engel yok → 0.35 m/s ilerle, koridorda ortalan
  🟣 YÜK KORUMA  (IMU) yatay ivme > 2.0 m/s² → 2 s boyunca hızı yarıya indir
                 Bu bir "durum" değil, hangi durumda olursak olalım en sonda
                 hesaplanan hıza uygulanan bir ÇARPAN.
"""
import math
import signal

import rclpy
from geometry_msgs.msg import Twist
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from sensor_msgs.msg import Imu, LaserScan
from std_msgs.msg import String

# =====================================================================
# EŞİKLER VE AYARLAR (sunumda anlatılacak sayılar burada)
# =====================================================================

# --- Hızlar ---
SEYIR_HIZI = 0.35        # m/s: boş koridorda ileri hız (DiffDrive sınırı 0.40)
EN_DUSUK_HIZ = 0.08      # m/s: YAVAŞLA'da bundan yavaş gitme (robot dursa bile
                         #      "takılıp kaldı" sanılmasın, engele yine de yaklaşsın)
KACIS_DONUS_HIZI = 0.8   # rad/s: KAÇIN'da yerinde dönme hızı

# --- LiDAR mesafe eşikleri ---
YAVASLA_MESAFE = 1.0     # m: ön sektörde engel bundan yakınsa yavaşla
KACIN_MESAFE = 0.5       # m: ön sektörde engel bundan yakınsa dur ve dön
KACIN_CIKIS_MESAFE = 0.8  # m: KAÇIN'dan çıkmak için önün en az bu kadar açılması
                          #    gerekir (histerezis). Giriş ve çıkış eşiği aynı
                          #    olsaydı robot 0.50 m sınırında KAÇIN ↔ YAVAŞLA
                          #    arasında titrerdi.

# --- Koridorda ortalanma (SEYİR ve YAVAŞLA'da) ---
# Robot sol ve sağ duvara olan uzaklığı karşılaştırır, boş tarafa hafifçe
# yönelir. Böylece duvara çapraz yaklaşıp duvar dibinde sürünmez, köşelerde de
# açık tarafa doğru döner. Uzak mesafeler 2 m'de kesilir: koridorun 2.4 m'lik
# genişliğinde ortadaki robot iki yanda ~1.2 m görür, açık bir kapı ya da
# koridorun devamı tek başına robotu oraya savurmaz.
ORTALAMA_KAZANCI = 0.4   # rad/s / m: iki yan arasındaki 1 m'lik farka verilen dönüş
ORTALAMA_SINIRI = 0.3    # rad/s: ortalanma için en fazla bu kadar dön
YAN_MESAFE_TAVANI = 2.0  # m: yan ortalamada bundan uzak ölçümler 2 m sayılır

# --- Yan güvenlik ---
# LiDAR robotun orta çizgisinde; gövdenin yan kenarı LiDAR'dan ~0.22 m uzakta.
# Yanda bir şey 0.35 m'den yakınsa (gövde kenarına ~13 cm) ortalanmayı bırak,
# o taraftan uzaklaşacak şekilde dön. Yoksa robot ince engellere (hemşire
# bacağı, sedye ayağı) yandan sürtünüp sıkışabiliyor.
YAN_GUVENLIK_MESAFE = 0.35  # m
YAN_KACIS_DONUSU = 0.5      # rad/s

# --- LiDAR sektörleri (derece; 0° = tam ön, + = sol, - = sağ) ---
ON_SEKTOR = (-30.0, 30.0)     # robotun önü: ±30° (gövde 0.44 m; 0.5 m ileride
                              #   ±30° yaklaşık ±0.29 m'lik bir şeridi tarar)
SOL_SEKTOR = (30.0, 120.0)    # sol taraf (LiDAR'ın görüşünün sonuna kadar)
SAG_SEKTOR = (-120.0, -30.0)  # sağ taraf
# Not: Yan sektörler önce 30°–90° idi. Testte robot, LiDAR'a göre ~98°'de duran
# hemşire bacağını hiçbir sektörde görmedi, yanından sürtünüp sıkıştı.
# Artık LiDAR'ın gördüğü her açı bir sektörde.

# --- IMU yük koruma ---
YUK_IVME_ESIGI = 2.0     # m/s²: yatay ivme bunu aşarsa yük sarsılıyor say.
                         # Simülasyonda ölçülen değerler:
                         #   dururken ~0.06 | hızlanırken ~0.84 (DiffDrive ivme
                         #   sınırı 0.8) | yavaşlarken ~1.5 (fren sınırı 1.5)
                         #   ani dönüşe başlama 2.4–4.0 | çarpma ~6.5
                         # Yani normal kalkış ve frenler eşiğin altında kalır,
                         # sadece gerçek sarsıntılar (çarpma, sert manevra) tetikler.
                         # Eşik 1.5'in altında olsaydı her fren tetiklerdi; yük
                         # koruma da hızı yarıya indirerek yeni bir fren
                         # yaratacağı için kendi kendini sonsuza kadar uzatırdı.
YUK_KORUMA_SURESI = 2.0  # s: eşik aşılınca bu süre boyunca yavaş git
YUK_KORUMA_CARPANI = 0.5 # hızın kaçla çarpılacağı (0.5 = yarı hız)

# --- Güvenlik ---
KONTROL_HIZI = 10.0      # Hz: karar döngüsü saniyede kaç kez çalışır
SCAN_ZAMAN_ASIMI = 0.5   # s: bu süredir LiDAR verisi gelmediyse DUR
                         #    (sensörü görmeyen robot kör sürmesin)


class KibarSurus(Node):

    def __init__(self):
        # use_sim_time: Gazebo'nun saatini kullan (zaman aşımları simülasyon
        # saatine göre hesaplanır; simülasyon yavaşlarsa kurallar da tutarlı kalır)
        super().__init__('kibar_surus',
                         parameter_overrides=[Parameter('use_sim_time', value=True)])

        # --- Abonelikler ---
        # Sensör verisi için "best effort" QoS: arada kaybolan bir ölçüm sorun
        # değil, önemli olan en güncel ölçüm.
        self.create_subscription(LaserScan, '/scan', self.scan_geldi,
                                 qos_profile_sensor_data)
        self.create_subscription(Imu, '/imu', self.imu_geldi,
                                 qos_profile_sensor_data)
        # GERİ ÇEKİL: Hüseyin buraya /bumper aboneliğini ekleyecek
        # (ros_gz_interfaces/msg/Contacts).

        # --- Yayıncılar ---
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)
        self.durum_pub = self.create_publisher(String, '/lokman/durum', 10)

        # --- Sensörlerden gelen en son bilgiler ---
        self.son_scan = None          # en son LaserScan mesajı
        self.son_scan_zamani = None   # ne zaman geldi
        self.yuk_koruma_bitis = None  # yük koruma ne zamana kadar sürecek
        self.son_ivme = 0.0           # en son yatay ivme (log için)

        # GERİ ÇEKİL: Hüseyin dolduracak. Bumper temas edince True olacak.
        self.bumper_temas = False

        # --- Durum makinesi ---
        self.durum = 'BASLANGIC'
        self.kacis_yonu = 0.0  # KAÇIN'a girerken seçilen dönüş yönü (+1 sol, -1 sağ)

        self.create_timer(1.0 / KONTROL_HIZI, self.karar_ver)
        self.get_logger().info('Kibar sürüş başladı. LiDAR ve IMU bekleniyor...')

    # =================================================================
    # Sensör geri çağırmaları: sadece veriyi saklar, kararı karar_ver() verir
    # =================================================================

    def scan_geldi(self, msg: LaserScan):
        self.son_scan = msg
        self.son_scan_zamani = self.get_clock().now()

    def imu_geldi(self, msg: Imu):
        # Yatay ivme: ileri-geri (x) ve sağa-sola (y) ivmenin bileşkesi.
        # z eksenini katmıyoruz, çünkü orada hep yerçekimi (~9.8) var.
        ax = msg.linear_acceleration.x
        ay = msg.linear_acceleration.y
        self.son_ivme = math.sqrt(ax * ax + ay * ay)

        if self.son_ivme > YUK_IVME_ESIGI:
            simdi = self.get_clock().now()
            # Zaten yük korumadaysak süreyi uzat, değilsek başlat
            if not self.yuk_korumada(simdi):
                self.get_logger().warning(
                    f'🟣 YÜK KORUMA: sarsıntı {self.son_ivme:.2f} m/s² '
                    f'(eşik {YUK_IVME_ESIGI}) → {YUK_KORUMA_SURESI:.0f} s yarı hız')
            self.yuk_koruma_bitis = simdi + Duration(seconds=YUK_KORUMA_SURESI)

    # =================================================================
    # Yardımcılar
    # =================================================================

    def sektor_mesafeleri(self, scan: LaserScan, aci_araligi):
        """Verilen açı aralığındaki (derece) geçerli LiDAR mesafelerini döndürür.

        LaserScan'de ranges[i], (angle_min + i * angle_increment) açısındaki
        mesafedir. Açıdan indekse:  i = (açı - angle_min) / angle_increment
        """
        bas = math.radians(aci_araligi[0])
        son = math.radians(aci_araligi[1])
        i_bas = max(0, int((bas - scan.angle_min) / scan.angle_increment))
        i_son = min(len(scan.ranges) - 1,
                    int((son - scan.angle_min) / scan.angle_increment))

        mesafeler = []
        for r in scan.ranges[i_bas:i_son + 1]:
            if math.isnan(r):
                continue                   # bozuk ölçüm: atla
            if math.isinf(r) or r > scan.range_max:
                r = scan.range_max         # inf = "menzil içinde engel yok"
            if r < scan.range_min:
                continue                   # sensörün ölçemeyeceği kadar yakın: güvenilmez
            mesafeler.append(r)
        return mesafeler

    def ortalanma_donusu(self, sol, sag):
        """Sol taraf daha boşsa + (sola), sağ taraf daha boşsa - (sağa) dönüş hızı."""
        if not sol or not sag:
            return 0.0
        # Önce yan güvenlik: bir yanda çok yakın bir şey varsa ondan uzaklaş
        sol_min, sag_min = min(sol), min(sag)
        if min(sol_min, sag_min) < YAN_GUVENLIK_MESAFE:
            return -YAN_KACIS_DONUSU if sol_min < sag_min else YAN_KACIS_DONUSU
        # Yoksa iki yanın ortalamasını eşitlemeye çalış (koridorun ortasında kal)
        sol_ort = sum(min(r, YAN_MESAFE_TAVANI) for r in sol) / len(sol)
        sag_ort = sum(min(r, YAN_MESAFE_TAVANI) for r in sag) / len(sag)
        w = ORTALAMA_KAZANCI * (sol_ort - sag_ort)
        return max(-ORTALAMA_SINIRI, min(ORTALAMA_SINIRI, w))

    def yuk_korumada(self, simdi):
        return self.yuk_koruma_bitis is not None and simdi < self.yuk_koruma_bitis

    def durum_degistir(self, yeni, aciklama):
        if yeni != self.durum:
            self.get_logger().info(f'{self.durum} → {yeni} ({aciklama})')
            self.durum = yeni

    def gonder(self, v, w):
        msg = Twist()
        msg.linear.x = float(v)
        msg.angular.z = float(w)
        self.cmd_pub.publish(msg)

    # =================================================================
    # KARAR DÖNGÜSÜ (saniyede 10 kez)
    # =================================================================

    def karar_ver(self):
        simdi = self.get_clock().now()

        # --- Güvenlik: LiDAR verisi yoksa ya da eskidiyse dur ---
        if self.son_scan is None or \
                (simdi - self.son_scan_zamani).nanoseconds * 1e-9 > SCAN_ZAMAN_ASIMI:
            self.durum_degistir('BEKLE', 'LiDAR verisi yok')
            self.gonder(0.0, 0.0)
            self.durum_pub.publish(String(data=self.durum))
            return

        # --- 🔴 GERİ ÇEKİL (en yüksek öncelik) ---
        # GERİ ÇEKİL: Hüseyin ekleyecek.
        # if self.bumper_temas ... : geri git, sonra boş tarafa dön; return

        # --- LiDAR: ön, sol ve sağ sektörler ---
        on = self.sektor_mesafeleri(self.son_scan, ON_SEKTOR)
        sol = self.sektor_mesafeleri(self.son_scan, SOL_SEKTOR)
        sag = self.sektor_mesafeleri(self.son_scan, SAG_SEKTOR)
        on_en_yakin = min(on) if on else self.son_scan.range_max

        # KAÇIN'dayken çıkış eşiği daha büyük (histerezis), değilken giriş eşiği
        kacin_esigi = KACIN_CIKIS_MESAFE if self.durum == 'KACIN' else KACIN_MESAFE

        if on_en_yakin <= kacin_esigi:
            # --- 🟠 KAÇIN ---
            if self.durum != 'KACIN':
                # Yönü sadece KAÇIN'a GİRERKEN seç ve çıkana kadar koru.
                # Her döngüde yeniden seçseydik robot iki taraf arasında titreyebilirdi.
                sol_ort = sum(sol) / len(sol) if sol else 0.0
                sag_ort = sum(sag) / len(sag) if sag else 0.0
                self.kacis_yonu = 1.0 if sol_ort >= sag_ort else -1.0
                taraf = 'sola' if self.kacis_yonu > 0 else 'sağa'
                self.durum_degistir(
                    'KACIN', f'önde {on_en_yakin:.2f} m; sol ort {sol_ort:.2f}, '
                             f'sağ ort {sag_ort:.2f} → {taraf} dön')
            v, w = 0.0, KACIS_DONUS_HIZI * self.kacis_yonu

        elif on_en_yakin <= YAVASLA_MESAFE:
            # --- 🟡 YAVAŞLA: hız mesafeyle doğrusal düşer ---
            # 1.0 m'de SEYIR_HIZI, 0.5 m'de 0; ama EN_DUSUK_HIZ'ın altına inmez.
            oran = (on_en_yakin - KACIN_MESAFE) / (YAVASLA_MESAFE - KACIN_MESAFE)
            v = max(EN_DUSUK_HIZ, SEYIR_HIZI * oran)
            w = self.ortalanma_donusu(sol, sag)  # yavaşlarken boş tarafa yönel
            self.durum_degistir('YAVASLA', f'önde {on_en_yakin:.2f} m')

        else:
            # --- 🟢 SEYİR ---
            v = SEYIR_HIZI
            w = self.ortalanma_donusu(sol, sag)  # koridorun ortasında kal
            self.durum_degistir('SEYIR', f'önde {on_en_yakin:.2f} m, yol açık')

        # --- 🟣 YÜK KORUMA: hangi durumda olursak olalım hızı yarıya indir ---
        yuk_koruma = self.yuk_korumada(simdi)
        if yuk_koruma:
            v *= YUK_KORUMA_CARPANI
            w *= YUK_KORUMA_CARPANI

        self.gonder(v, w)
        self.durum_pub.publish(
            String(data=self.durum + (' + YUK_KORUMA' if yuk_koruma else '')))

    def dur(self):
        self.gonder(0.0, 0.0)


def kapat_sinyali(signum, frame):
    raise KeyboardInterrupt


def main():
    # ROS'un kendi Ctrl+C işleyicisini kapatıyoruz: o, Ctrl+C gelince bağlantıyı
    # hemen kapattığı için robota son "DUR" komutunu gönderemiyorduk.
    # Onun yerine Ctrl+C (SIGINT) ve kapatma (SIGTERM) sinyallerini kendimiz
    # yakalıyoruz. Bunu açıkça yapmak gerekiyor: arka planda başlatılan
    # programlarda Ctrl+C varsayılan olarak yok sayılıyor.
    signal.signal(signal.SIGINT, kapat_sinyali)
    signal.signal(signal.SIGTERM, kapat_sinyali)
    rclpy.init(signal_handler_options=SignalHandlerOptions.NO)
    dugum = KibarSurus()
    try:
        rclpy.spin(dugum)
    except KeyboardInterrupt:
        pass
    finally:
        # Ctrl+C ile kapatınca robot son komutla gitmeye devam etmesin
        dugum.dur()
        dugum.get_logger().info('Kibar sürüş durduruldu, robota DUR gönderildi.')
        dugum.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
