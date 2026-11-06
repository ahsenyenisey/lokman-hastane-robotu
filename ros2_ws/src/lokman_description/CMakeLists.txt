cmake_minimum_required(VERSION 3.10)
project(lokman_description)

find_package(ament_cmake REQUIRED)

# Model ve RViz dosyalarını kurulum klasörüne kopyala
install(DIRECTORY urdf rviz
  DESTINATION share/${PROJECT_NAME})

ament_package()
