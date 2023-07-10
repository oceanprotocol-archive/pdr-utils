#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2023 Ocean Protocol Foundation
# SPDX-License-Identifier: Apache-2.0
#
from setuptools import find_packages, setup

# Installed by pip install ocean-provider
# or pip install -e .
install_requirements = [
    "enforce_typing",
    "pylint",
    "bumpversion",
]

# Required to run setup.py:
setup_requirements = ["pytest-runner"]

setup(
    author="oceanprotocol",
    author_email="devops@oceanprotocol.com",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.8",
    ],
    description="Predictoor utils lib.",
    install_requires=install_requirements,
    name="pdr-utils",
    license="Apache Software License 2.0",
    include_package_data=True,
    packages=find_packages(
        include=[
            "pdr_utils",
        ]
    ),
    setup_requires=setup_requirements,
    test_suite="tests",
    url="https://github.com/oceanprotocol/pdr-utils",
    # fmt: off
    # bumpversion needs single quotes
    version='0.0.1',
    # fmt: on
    zip_safe=False,
)
