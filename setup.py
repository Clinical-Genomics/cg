#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel upload")
    sys.exit()


setup(
    name='cg',
    version='1.0.0-beta1',
    description='Glue CLI for Clinical Genomics apps.',
    author='Robin Andeer',
    author_email='robin.andeer@scilifelab.se',
    url='https://github.com/Clinical-Genomics/cg',
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(exclude=('tests*', 'docs', 'examples')),
    entry_points={
        'console_scripts': ['cg=cg.cli:base'],
    },
    install_requires=[
        'click>=6.7',
        'ruamel.yaml',
        'trailblazer',
        'housekeeper',
        'coloredlogs',
        'petname',
        'genologics',
        'chanjo',
        'genotype',
        'loqusdb',
        'scout-browser',
        'flask',
        'flask_cors',
        'flask_alchy',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
