""" Trailblazer API in cg """ ""

import logging
from trailblazer.store import Store

LOG = logging.getLogger(__name__)


class TrailblazerAPI(Store):
    """Interface to Trailblazer for `cg`."""

    def __init__(self, config: dict):
        super(TrailblazerAPI, self).__init__(
            config["trailblazer"]["database"],
            families_dir=config["trailblazer"]["root"],
        )
        self.mip_config = config["trailblazer"]["mip_config"]
