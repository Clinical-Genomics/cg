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
from cg.meta.backup.backup import SpringBackupAPI
from cg.meta.compress import CompressAPI
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.store import Store
from cg.meta.backup.pdc import PdcAPI


class MetaAPI:

    """MetaAPI class initializing all App APIs used within CG in non-conflicting manner"""

    def __init__(self, config: CGConfig):
        self.config = config
        self.chanjo_api: ChanjoAPI = config.chanjo_api
        self.crunchy_api: CrunchyAPI = config.crunchy_api
        self.genotype_api: GenotypeAPI = config.genotype_api
        self.hermes_api: HermesApi = config.hermes_api
        self.housekeeper_api: HousekeeperAPI = config.housekeeper_api
        self.lims_api: LimsAPI = config.lims_api
        self.madeline_api: MadelineAPI = config.madeline_api
        self.mutacc_auto_api: MutaccAutoAPI = config.mutacc_auto_api
        self.prepare_fastq_api: PrepareFastqAPI = PrepareFastqAPI(
            store=config.status_db,
            compress_api=CompressAPI(
                hk_api=config.housekeeper_api,
                crunchy_api=config.crunchy_api,
                demux_root=config.demultiplex.out_dir,
                backup_api=SpringBackupAPI(
                    encryption_api=SpringEncryptionAPI(
                        binary_path=config.dict()["encryption"]["binary_path"]
                    ),
                    hk_api=config.housekeeper_api,
                    pdc_api=PdcAPI(config.dict()["pdc"]["binary_path"]),
                ),
            ),
        )
        self.status_db: Store = config.status_db
        self.scout_api: ScoutAPI = config.scout_api
        self.trailblazer_api: TrailblazerAPI = config.trailblazer_api
