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
from cg.clients.chanjo2.client import Chanjo2APIClient
from cg.meta.backup.backup import SpringBackupAPI
from cg.meta.compress import CompressAPI
from cg.meta.delivery.delivery import DeliveryAPI
from cg.meta.encryption.encryption import SpringEncryptionAPI
from cg.meta.workflow.prepare_fastq import PrepareFastqAPI
from cg.models.cg_config import CGConfig
from cg.services.pdc_service.pdc_service import PdcService
from cg.store.store import Store


class MetaAPI:
    """MetaAPI class initializing all App APIs used within CG in non-conflicting manner"""

    def __init__(self, config: CGConfig):
        self.chanjo_api: ChanjoAPI = config.chanjo_api
        self.chanjo2_api: Chanjo2APIClient = config.chanjo2_api
        self.config = config
        self.crunchy_api: CrunchyAPI = config.crunchy_api
        self.delivery_api: DeliveryAPI = config.delivery_api
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
                demux_root=config.run_instruments.illumina.demultiplexed_runs_dir,
                backup_api=SpringBackupAPI(
                    encryption_api=SpringEncryptionAPI(
                        binary_path=config.dict()["encryption"]["binary_path"]
                    ),
                    hk_api=config.housekeeper_api,
                    pdc_service=PdcService(config.dict()["pdc"]["binary_path"]),
                ),
            ),
        )
        self.scout_api_37: ScoutAPI = config.scout_api_37
        self.scout_api_38: ScoutAPI = config.scout_api_38
        self.status_db: Store = config.status_db
        self.trailblazer_api: TrailblazerAPI = config.trailblazer_api
