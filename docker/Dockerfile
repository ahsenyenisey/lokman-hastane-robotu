# =====================================================================
# BIMU4101 Mobil Robot Projesi - Geliştirme Ortamı
# ---------------------------------------------------------------------
# Taban imaj: Resmi ROS 2 Lyrical imajı (Ubuntu 26.04 "Resolute").
# Apple Silicon (arm64) için de resmi olarak yayınlanıyor.
# Bunun üzerine:
#   - Gazebo Jetty (ros-lyrical-ros-gz ile birlikte gelir)
#   - RViz2, xacro ve diğer ROS araçları
#   - Tarayıcıdan erişilen bir masaüstü (XFCE + TigerVNC + noVNC)
# kuruyoruz.
# =====================================================================
FROM ros:lyrical-ros-base-resolute

# apt kurulumları sırasında soru sormasın (saat dilimi vb.)
ENV DEBIAN_FRONTEND=noninteractive

# ---- 1) ROS 2 + Gazebo paketleri ----
# ros-lyrical-ros-gz           : Gazebo Jetty + ROS<->Gazebo köprüsü (ros_gz_bridge, ros_gz_sim)
# ros-lyrical-rviz2            : 3B görselleştirme aracı
# ros-lyrical-xacro            : Xacro dosyalarını URDF'e çevirir
# ros-lyrical-robot-state-publisher : Robotun parça konumlarını (TF) yayınlar
# ros-lyrical-joint-state-publisher-gui : Eklemleri elle oynatma aracı (test için)
# ros-lyrical-teleop-twist-keyboard : Klavyeyle robot sürme
# ros-lyrical-rqt-image-view / rqt-plot : Kamera görüntüsü ve grafik çizimi
RUN apt-get update && apt-get install -y --no-install-recommends \
        ros-lyrical-ros-gz \
        ros-lyrical-rviz2 \
        ros-lyrical-xacro \
        ros-lyrical-robot-state-publisher \
        ros-lyrical-joint-state-publisher-gui \
        ros-lyrical-teleop-twist-keyboard \
        ros-lyrical-rqt-image-view \
        ros-lyrical-rqt-plot \
        python3-colcon-common-extensions \
    && rm -rf /var/lib/apt/lists/*

# ---- 2) Tarayıcıdan erişilen masaüstü ----
# xfce4                  : Hafif bir masaüstü ortamı
# tigervnc-standalone-server : Sanal ekran (VNC sunucusu)
# novnc + websockify     : VNC ekranını tarayıcıya taşır (http://localhost:6080)
# mesa-utils, libgl1-mesa-dri : Yazılımsal OpenGL (ekran kartı olmadan 3B çizim)
# x11-apps, imagemagick, wmctrl : Rapor için ekran görüntüsü alma ve pencere yönetimi
RUN apt-get update && apt-get install -y --no-install-recommends \
        xfce4 xfce4-terminal dbus-x11 \
        tigervnc-standalone-server \
        novnc websockify \
        mesa-utils libgl1-mesa-dri \
        nano less \
        x11-apps imagemagick wmctrl \
    && rm -rf /var/lib/apt/lists/*

# ---- 3) Ortam değişkenleri ----
# DISPLAY=:1               : Grafik programlar sanal ekran 1'e çizsin
# LIBGL_ALWAYS_SOFTWARE=1  : Konteynerde GPU yok, OpenGL'i CPU ile yap
ENV DISPLAY=:1 \
    LIBGL_ALWAYS_SOFTWARE=1 \
    ROS_DISTRO=lyrical

# Her yeni terminal açıldığında ROS ortamı otomatik yüklensin.
# Çalışma alanı derlenmişse (install/ klasörü varsa) o da yüklensin.
RUN echo 'source /opt/ros/lyrical/setup.bash' >> /root/.bashrc && \
    echo '[ -f /ws/ros2_ws/install/setup.bash ] && source /ws/ros2_ws/install/setup.bash' >> /root/.bashrc && \
    echo 'cd /ws' >> /root/.bashrc

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

WORKDIR /ws
EXPOSE 6080
ENTRYPOINT ["/entrypoint.sh"]
