#!/usr/bin/env python3
"""
Setup script for SuperSID Pro
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
README = Path("README.md").read_text(encoding="utf-8")

# Read requirements
REQUIREMENTS = Path("requirements. txt").read_text(encoding="utf-8"). splitlines()

setup(
    name="supersid-pro",
    version="1. 0.0",
    description="Professional Solar Radio Telescope Monitoring Software",
    long_description=README,
    long_description_content_type="text/markdown",
    author="Observatory Software Solutions",
    author_email="support@observatorysoftware.com",
    url="https://github.com/alearecuest/SuperSID_Pro",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    include_package_data=True,
    install_requires=REQUIREMENTS,
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: Commercial License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3. 9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Astronomy",
        "Topic :: Scientific/Engineering :: Physics",
    ],
    entry_points={
        "console_scripts": [
            "supersid-pro=main:main",
        ],
    },
    package_data={
        "": ["assets/*", "config/*"],
    },
)