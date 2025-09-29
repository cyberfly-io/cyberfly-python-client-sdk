from setuptools import setup, find_packages
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()
setup(
    name='cyberfly-client-sdk',
    version='0.2',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests',
        'pypact-lang',
        'rule_engine',
        'python-socketio[client]',
        'sensor-library-python>=0.2.0'
    ],
    extras_require={
        'sensors': [
            'sensor-library-python>=0.2.0'
        ]
    },
    entry_points={
        'console_scripts': [
            'cyberfly-device=cyberflySdk.device_manager:main',
        ],
    },
    url='https://github.com/cyberfly-io/cyberfly-python-client-sdk',
    long_description=long_description,
    long_description_content_type='text/markdown'
)