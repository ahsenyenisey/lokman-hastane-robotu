"""
Boş dünya test launch dosyası (Aşama 2).

Tek komutla şunları başlatır:
  1) Gazebo (boş dünya)
  2) robot_state_publisher: Xacro modelini okuyup /robot_description ve
     parçalar arası TF'leri yayınlar
  3) Robotu Gazebo'ya ekleme (spawn)
  4) ros_gz_bridge: Gazebo <-> ROS 2 topic köprüsü
  5) RViz

Çalıştırma:  ros2 launch lokman_gazebo bos_dunya.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    desc_pkg = get_package_share_directory('lokman_description')
    gz_pkg = get_package_share_directory('lokman_gazebo')
    ros_gz_sim_pkg = get_package_share_directory('ros_gz_sim')

    xacro_dosyasi = os.path.join(desc_pkg, 'urdf', 'lokman.urdf.xacro')
    rviz_ayari = os.path.join(desc_pkg, 'rviz', 'lokman.rviz')
    kopru_ayari = os.path.join(gz_pkg, 'config', 'kopru.yaml')

    # Xacro'yu çalıştırıp düz URDF metnine çeviriyoruz
    robot_description = ParameterValue(Command(['xacro ', xacro_dosyasi]), value_type=str)

    # 1) Gazebo
    #   -r                     : açılır açılmaz simülasyonu başlat (Play'e basmaya gerek yok)
    #   --render-engine ogre   : Hafif render motoru (Ogre1). Konteynerde ekran kartı yok,
    #                            görüntüyü işlemci çiziyor; varsayılan Ogre2 bu durumda çok
    #                            ağır kalıyor ve Gazebo penceresi donuyor.
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(ros_gz_sim_pkg, 'launch', 'gz_sim.launch.py')),
        launch_arguments={'gz_args': '-r empty.sdf --render-engine ogre'}.items(),
    )

    # 2) robot_state_publisher
    rsp = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description,
                     'use_sim_time': True}],
        output='screen',
    )

    # 3) Spawn: /robot_description topic'indeki modeli "lokman" adıyla Gazebo'ya ekle
    spawn = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-topic', 'robot_description', '-name', 'lokman', '-z', '0.01'],
        output='screen',
    )

    # 4) Köprü
    kopru = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        parameters=[{'config_file': kopru_ayari, 'use_sim_time': True}],
        output='screen',
    )

    # 5) RViz
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        arguments=['-d', rviz_ayari],
        parameters=[{'use_sim_time': True}],
        output='screen',
    )

    return LaunchDescription([gazebo, rsp, spawn, kopru, rviz])
