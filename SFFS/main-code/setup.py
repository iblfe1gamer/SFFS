"""
SFFS setup.py — allows pip install -e . for development mode
"""
from setuptools import setup, find_packages

setup(
    name="sffs",
    version="1.0.0",
    description="Smart File Fortify System — Portable Secure File Encryption",
    author="Ibraheem Snineh, Karim Taha, Mazin Alsarahin",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "pycryptodome>=3.19.0",
        "cryptography>=41.0.0",
        "argon2-cffi>=23.1.0",
        "psutil>=5.9.0",
        "PyQt6>=6.6.0",
        "google-api-python-client>=2.108.0",
        "google-auth-oauthlib>=1.1.0",
        "google-auth-httplib2>=0.1.1",
    ],
    entry_points={
        "console_scripts": [
            "sffs=main-code.main:main",
        ],
    },
)
