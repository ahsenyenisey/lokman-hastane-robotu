#!/bin/bash
# Konteyner açılınca çalışan betik:
# 1) Sanal ekranı (VNC) başlatır
# 2) Bu ekranda XFCE masaüstünü açar
# 3) noVNC ile ekranı tarayıcıya (port 6080) taşır
set -e

# Önceki çalıştırmadan kalan kilit dosyalarını temizle
rm -f /tmp/.X1-lock /tmp/.X11-unix/X1

# Sanal ekran :1 (şifresiz; port sadece Mac'inizin kendisine açık)
Xvnc :1 -geometry 1600x900 -depth 24 -SecurityTypes None -localhost yes &
sleep 2

# Masaüstü ortamı
startxfce4 > /tmp/xfce.log 2>&1 &

# Tarayıcı köprüsü: http://localhost:6080/vnc.html
echo "Masaüstü hazır: http://localhost:6080/vnc.html"
exec websockify --web /usr/share/novnc 6080 localhost:5901
