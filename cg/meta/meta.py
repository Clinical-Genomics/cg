from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.vogue import VogueAPI
from cg.meta.compress import CompressAPI
from cg.meta.upload.mutacc import UploadToMutaccAPI
from cg.meta.upload.vogue import UploadVogueAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.store import Store


class MetaAPI:

    """MetaAPI class initializing all complex API used within CG in non-conflicting manner"""

    def __init__(self, config: CGConfig):
        self.config = config
        self.housekeeper_api = config.housekeeper_api
        self.trailblazer_api = config.trailblazer_api
        self.status_db = config.status_db
        self.lims_api = config.lims_api
        self.hermes_api = config.hermes_api
        self.scout_api = config.scout_api
        self.vogue_api = config.vogue_api
        self.crunchy_api = config.crunchy_api
        self.madeline_api = config.madeline_api
        self.mutacc_auto_api = config.mutacc_auto_api
        self.genotype_api = config.genotype_api
        self.chanjo_api = config.chanjo_api
        self.prepare_fastq_api = PrepareFastqAPI(
            store=self.status_db,
            compress_api=CompressAPI(hk_api=self.housekeeper_api, crunchy_api=self.crunchy_api),
        )
        self.mutacc_upload_api = UploadToMutaccAPI(
            scout_api=self.scout_api, mutacc_auto_api=self.mutacc_auto_api
        )
        self.upload_vogue_api = UploadVogueAPI(
            genotype_api=self.genotype_api,
            vogue_api=self.vogue_api,
            store=self.status_db,
        )
