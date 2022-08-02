# cg
![Build Status - Github][gh-actions-badge]
[![Coverage Status][coveralls-image]][coveralls-url]
[![GitHub issues-closed][closed-issues-img]][closed-issues-url]
[![Average time to resolve an issue][ismaintained-resolve-img]][ismaintained-resolve-url]
[![Percentage of issues still open][ismaintained-open-rate-img]][ismaintained-open-rate-url]
[![CodeFactor][codefactor-badge]][codefactor-url]
[![Code style: black][black-image]][black-url]


`cg` stands for _Clinical Genomics_; a clinical sequencing platform under [SciLifeLab][scilife]

In this context, `cg` provides the interface between these tools to facilitate automation and other necessary cross-talk. It also exposes some APIs:

- HTTP REST for powering the web portal: [clinical.scilifelab.se][portal]
- CLI for interactions on the command line

### Contributing

Please check out our [guide for contributing to cg](CONTRIBUTING.md)

## Installation

Cg written in Python 3.6+ and is available on the [Python Package Index][pypi] (PyPI).

```bash
pip install cg
```

If you would like to install the latest development version:

```bash
git clone https://github.com/Clinical-Genomics/cg
cd cg
```
To install CG either use pipenv (as described in contributing) and run
```
pipenv install -e .
```

or (without pipenv)

```
pip install -r requirements-dev.txt --editable .
```


[portal]: https://clinical.scilifelab.se/
[trailblazer]: https://github.com/Clinical-Genomics/trailblazer
[housekeeper]: https://github.com/Clinical-Genomics/housekeeper
[genotype]: https://github.com/Clinical-Genomics/genotype
[scilife]: https://www.scilifelab.se/
[pypi]: https://pypi.org/


[black]: https://black.readthedocs.io/en/stable/

<!-- badges -->

[coveralls-url]: https://coveralls.io/github/Clinical-Genomics/cg
[coveralls-image]: https://coveralls.io/repos/github/Clinical-Genomics/cg/badge.svg?branch=master

[gh-actions-badge]: https://github.com/Clinical-Genomics/cg/workflows/Tests%20and%20coveralls/badge.svg
[closed-issues-img]: https://img.shields.io/github/issues-closed/Clinical-Genomics/cg.svg
[closed-issues-url]: https://GitHub.com/Clinical-Genomics/cg/issues?q=is%3Aissue+is%3Aclosed
[ismaintained-resolve-img]: http://isitmaintained.com/badge/resolution/Clinical-Genomics/cg.svg
[ismaintained-resolve-url]: http://isitmaintained.com/project/Clinical-Genomics/cg
[ismaintained-open-rate-img]: http://isitmaintained.com/badge/open/Clinical-Genomics/cg.svg
[ismaintained-open-rate-url]: http://isitmaintained.com/project/Clinical-Genomics/cg
[codefactor-badge]: https://www.codefactor.io/repository/github/clinical-genomics/cg/badge
[codefactor-url]: https://www.codefactor.io/repository/github/clinical-genomics/cg
[black-image]: https://img.shields.io/badge/code%20style-black-000000.svg
[black-url]: https://github.com/psf/black
