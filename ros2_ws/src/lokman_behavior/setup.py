from setuptools import setup

package_name = 'lokman_behavior'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Ahsen Yenisey',
    maintainer_email='ahsenyeuisei@gmail.com',
    description='LOKMAN davranış düğümleri',
    license='MIT',
    entry_points={
        'console_scripts': [
            # ros2 run lokman_behavior ok_tuslari
            'ok_tuslari = lokman_behavior.ok_tuslari:main',
        ],
    },
)
