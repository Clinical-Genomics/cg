#!/usr/bin/env python
import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand

if sys.argv[-1] == "publish":
    os.system("python setup.py sdist bdist_wheel upload")
    sys.exit()


def parse_requirements(req_path="./requirements.txt"):
    """Recursively parse requirements from nested pip files."""
    install_requires = []
    with open(req_path, "r") as handle:
        # remove comments and empty lines
        lines = (line.strip() for line in handle if line.strip() and not line.startswith("#"))
        for line in lines:
            # check for nested requirements files
            if line.startswith("-r"):
                # recursively call this function
                install_requires += parse_requirements(req_path=line[3:])
            else:
                # add the line as a new requirement
                install_requires.append(line)
    return install_requires


# This is a plug-in for setuptools that will invoke py.test
# when you run python setup.py test
class PyTest(TestCommand):
    """Set up the py.test test runner."""

    def finalize_options(self):
        """Set options for the command line."""
        TestCommand.finalize_options(self)
        self.test_args = [
            "-W",
            "ignore::PendingDeprecationWarning",
            "-W",
            "ignore::DeprecationWarning",
        ]
        self.test_suite = True

    def run_tests(self):
        """Execute the test runner command."""
        # Import here, because outside the required eggs aren't loaded yet
        import pytest

        sys.exit(pytest.main(self.test_args))


setup(
    name="cg",
    version="12.1.4",
    description="Clinical Genomics command center.",
    author="Patrik Grenfeldt",
    author_email="patrik.grenfeldt@scilifelab.se",
    url="https://github.com/Clinical-Genomics/cg",
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(exclude=("tests*", "docs", "examples")),
    entry_points={"console_scripts": ["cg=cg.cli:base"]},
    install_requires=parse_requirements(),
    tests_require=parse_requirements("requirements-dev.txt"),
    cmdclass=dict(test=PyTest),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
