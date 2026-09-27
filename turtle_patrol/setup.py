from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'turtle_patrol'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='brian',
    maintainer_email='153433261+Brianlinn@users.noreply.github.com',
    description='ROS 2 action server and client for polygon patrols in turtlesim.',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'patrol_controller = turtle_patrol.patrol_controller:main',
            'square_patrol_action_server = turtle_patrol.square_patrol_action_server:main',
            'square_patrol_action_client = turtle_patrol.square_patrol_action_client:main',
        ],
    },
)
