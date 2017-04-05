#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
about = {}
with open(os.path.join(here, 'cg', 'version.py')) as in_handle:
    exec(in_handle.read(), about)

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel upload")
    sys.exit()


setup(
    name='cg',
    version=about['__version__'],
    description='Glue CLI for Clinical Genomics apps.',
    author='Robin Andeer',
    author_email='robin.andeer@scilifelab.se',
    url='https://github.com/Clinical-Genomics/cg',
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(exclude=('tests*', 'docs', 'examples')),
    entry_points={
        'console_scripts': ['cg=cg:cli'],
    },
    install_requires=[
        'Click>=6.7',
        'click_completion',
        'crayons',
        'ruamel.yaml',
        'pymongo',
        'coloredlogs',
        'trailblazer',
        'scout-browser',
        'pymysql',
    ],
    classifiers=[
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
    ],
)
