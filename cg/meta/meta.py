from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.vogue import VogueAPI
from cg.meta.compress import CompressAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.store import Store


class MetaAPI:

    """MetaAPI class initializing all complex API used within CG in non-conflicting manner"""

    def __init__(self, config: dict):
        self.config = config or {}
        self.housekeeper_api = HousekeeperAPI(self.config)
        self.trailblazer_api = TrailblazerAPI(self.config)
        self.status_db = Store(self.config["database"])
        self.lims_api = LimsAPI(self.config)
        self.hermes_api = HermesApi(self.config)
        self.scout_api = ScoutAPI(self.config)
        self.vogue_api = VogueAPI(self.config)
        self.crunchy_api = CrunchyAPI(self.config)
        self.madeline_api = MadelineAPI(self.config)
        self.genotype_api = GenotypeAPI(self.config)
        self.chanjo_api = ChanjoAPI(self.config)
        self.prepare_fastq_api = PrepareFastqAPI(
            store=self.status_db,
            compress_api=CompressAPI(hk_api=self.housekeeper_api, crunchy_api=self.crunchy_api),
        )
