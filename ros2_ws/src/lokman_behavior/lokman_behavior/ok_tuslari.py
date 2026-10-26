"""
Ok tuşlarıyla LOKMAN'ı sürme düğümü.

Kullanım:  ros2 run lokman_behavior ok_tuslari

  ↑ / ↓   : ileri / geri
  ← / →   : yerinde sola / sağa dön
  boşluk  : dur
  q       : çıkış

Tuşa BASILI TUTTUĞUNUZ sürece robot hareket eder, bırakınca durur
("ölü adam" güvenliği: kısa süre tuş gelmezse hız sıfırlanır).

Çıktı: /cmd_vel (geometry_msgs/msg/Twist)
"""
import select
import sys
import termios
import tty

import rclpy
from geometry_msgs.msg import Twist
from rclpy.node import Node

ILERI_HIZ = 0.3     # m/s  (DiffDrive sınırı 0.4)
DONUS_HIZI = 0.8    # rad/s
TUS_ZAMAN_ASIMI = 0.6  # s: bu süre tuş gelmezse dur

# Terminal ok tuşlarını 3 karakterlik kaçış dizisi olarak gönderir: ESC [ A/B/C/D
OK_TUSLARI = {
    'A': (ILERI_HIZ, 0.0),     # ↑
    'B': (-ILERI_HIZ, 0.0),    # ↓
    'C': (0.0, -DONUS_HIZI),   # → (saat yönü = negatif açısal hız)
    'D': (0.0, DONUS_HIZI),    # ←
}


class OkTuslari(Node):
    def __init__(self):
        super().__init__('ok_tuslari')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)

    def gonder(self, v, w):
        msg = Twist()
        msg.linear.x = v
        msg.angular.z = w
        self.pub.publish(msg)


def tus_oku(zaman_asimi):
    """Zaman aşımı içinde bir tuş gelirse onu döndürür, gelmezse None."""
    hazir, _, _ = select.select([sys.stdin], [], [], zaman_asimi)
    if not hazir:
        return None
    c = sys.stdin.read(1)
    if c == '\x1b':  # ok tuşu kaçış dizisi
        return sys.stdin.read(2)[-1]
    return c


def main():
    rclpy.init()
    dugum = OkTuslari()
    eski_ayar = termios.tcgetattr(sys.stdin)
    print(__doc__)
    try:
        tty.setcbreak(sys.stdin.fileno())  # tuşları Enter beklemeden oku
        while rclpy.ok():
            tus = tus_oku(TUS_ZAMAN_ASIMI)
            if tus == 'q':
                break
            v, w = OK_TUSLARI.get(tus, (0.0, 0.0))  # başka tuş / zaman aşımı → dur
            dugum.gonder(v, w)
    finally:
        dugum.gonder(0.0, 0.0)
        termios.tcsetattr(sys.stdin, termios.TCSADRAIN, eski_ayar)
        dugum.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
