import logging

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI

LOG = logging.getLogger(__name__)


class UploadGenotypesAPI(object):
    """Genotype upload API."""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        gt_api: GenotypeAPI,
    ):
        LOG.info("Initializing UploadGenotypesAPI")
        self.hk = hk_api
        self.gt = gt_api
