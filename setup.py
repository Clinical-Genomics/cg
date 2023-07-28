"""Description of the CG package"""

import io
import os

from setuptools import find_packages, setup

NAME = "cg"
DESCRIPTION = "Clinical Genomics command center"
URL = "https://github.com/Clinical-Genomics/cg"
EMAIL = "support@clinicalgenomics.se"
AUTHOR = "Clinical Genomics"
REQUIRES_PYTHON = ">=3.6.0"

HERE = os.path.abspath(os.path.dirname(__file__))


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


# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(HERE, "README.md"), encoding="utf-8") as f:
        LONG_DESCRIPTION = "\n" + f.read()
except FileNotFoundError:
    LONG_DESCRIPTION = DESCRIPTION

setup(
    name=NAME,
    version="40.2.3",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    long_description_content_type="text/markdown",
    author=AUTHOR,
    author_email=EMAIL,
    url=URL,
    include_package_data=True,
    zip_safe=False,
    packages=find_packages(exclude=("tests*", "docs", "examples")),
    entry_points={"console_scripts": ["cg=cg.cli:base"]},
    install_requires=parse_requirements(),
    tests_require=parse_requirements("requirements-dev.txt"),
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
)
