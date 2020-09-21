""" Trailblazer API for cg """ ""

import logging
from trailblazer.store import Store
from trailblazer.mip import files

LOG = logging.getLogger(__name__)


class TrailblazerAPI(Store):
    """Interface to Trailblazer for `cg`."""

    parse_sampleinfo = staticmethod(files.parse_sampleinfo)

    def __init__(self, config: dict):
        super(TrailblazerAPI, self).__init__(
            config["trailblazer"]["database"],
            families_dir=config["trailblazer"]["root"],
        )
        self.mip_config = config["trailblazer"]["mip_config"]
