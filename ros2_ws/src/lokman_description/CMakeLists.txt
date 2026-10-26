cmake_minimum_required(VERSION 3.10)
project(lokman_description)

find_package(ament_cmake REQUIRED)

# Model, RViz ve launch dosyalarını kurulum klasörüne kopyala
install(DIRECTORY urdf rviz launch
  DESTINATION share/${PROJECT_NAME})

ament_package()
