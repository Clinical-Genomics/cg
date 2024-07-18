"""Coverage analysis API for human clinical sequencing data."""

import logging

LOG = logging.getLogger(__name__)


class Chanjo2APIClient:
    """
    Chanjo2 API to communicate with a d4tools software in order to return coverage and
    coverage completeness over genomic intervals.
    """

    def __init__(self, config: dict[str, str]):
        self.host = config["chanjo2"]["host"]
