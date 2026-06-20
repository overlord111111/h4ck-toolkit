#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="h4ck-toolkit",
    version="1.0.0",
    description="Kit de ferramentas de segurança ofensiva para reconhecimento e scanning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Over",
    author_email="over.lord.hck@proton.me",
    url="https://github.com/overlord111111/h4ck-toolkit",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "colorama>=0.4.6",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "Intended Audience :: Information Technology",
        "Environment :: Console",
    ],
    entry_points={
        "console_scripts": [
            "h4ck-portscan=scanner.port_scanner:main",
            "h4ck-subfinder=recon.subdomain_finder:main",
            "h4ck-dirbrute=recon.dir_brute:main",
        ],
    },
)
