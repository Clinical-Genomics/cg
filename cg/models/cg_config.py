import logging
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from typing_extensions import Literal

from cg.apps.cgstats.stats import StatsAPI
from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.shipping import ShippingAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.vogue import VogueAPI
from cg.constants.priority import SlurmQos
from cg.store import Store

LOG = logging.getLogger(__name__)


class Sequencers(BaseModel):
    hiseqx: str
    hiseqga: str
    novaseq: str


class BackupConfig(BaseModel):
    root: Sequencers


class SlurmConfig(BaseModel):
    account: str
    mail_user: EmailStr
    conda_env: Optional[str]
    qos: SlurmQos = SlurmQos.LOW


class HousekeeperConfig(BaseModel):
    database: str
    root: str


class DemultiplexConfig(BaseModel):
    run_dir: str  # Base path to  un demultiplexed flowcells
    out_dir: str  # Base path to where the demultiplexed results lives
    slurm: SlurmConfig


class TrailblazerConfig(BaseModel):
    service_account: str
    service_account_auth_file: str
    host: str


class StatinaConfig(BaseModel):
    host: str


class CommonAppConfig(BaseModel):
    binary_path: str
    config_path: Optional[str]
    deploy_config: Optional[str]


class FluffyUploadConfig(BaseModel):
    user: str
    password: str
    host: str
    remote_path: str
    port: int


class FluffyConfig(CommonAppConfig):
    root_dir: str
    sftp: FluffyUploadConfig


class LimsConfig(BaseModel):
    host: str
    username: str
    password: str


class CrunchyConfig(BaseModel):
    cram_reference: str
    slurm: SlurmConfig


class MutaccAutoConfig(CommonAppConfig):
    padding: int = 300


class BalsamicConfig(CommonAppConfig):
    root: str
    balsamic_cache: str
    binary_path: str
    conda_env: str
    slurm: SlurmConfig


class MutantConfig(BaseModel):
    root: str
    binary_path: str
    conda_env: str


class MipConfig(BaseModel):
    conda_env: str
    mip_config: str
    pipeline: str
    root: str
    script: str


class CGStatsConfig(BaseModel):
    database: str
    root: str


class MicrosaltConfig(BaseModel):
    root: str
    queries_path: str
    binary_path: str
    conda_env: str


class GisaidConfig(CommonAppConfig):
    submitter: str
    log_dir: str
    logwatch_email: EmailStr
    upload_password: str
    upload_cid: str


class ShippingConfig(CommonAppConfig):
    host_config: str


class DataDeliveryConfig(BaseModel):
    destination_path: str
    covid_destination_path: str
    covid_source_path = str
    covid_report_path: str
    account: str
    base_path: str
    mail_user: str


class EmailBaseSettings(BaseModel):
    sender_email: EmailStr
    smtp_server: str


class FOHMConfig(BaseModel):
    host: str
    port: int
    key: str
    username: str
    valid_uploader: str
    email_sender: str
    email_recipient: str
    email_host: str


class ExternalConfig(BaseModel):
    hasta: str
    caesar: str


class CGConfig(BaseModel):
    database: str
    environment: Literal["production", "stage"] = "stage"
    madeline_exe: str
    bed_path: str
    delivery_path: str
    max_flowcells: Optional[int]
    email_base_settings: EmailBaseSettings

    # Base APIs that always should exist
    status_db_: Store = None
    housekeeper: HousekeeperConfig
    housekeeper_api_: HousekeeperAPI = None

    # App APIs that can be instantiated in CGConfig
    backup: BackupConfig = None
    cgstats: CGStatsConfig = None
    cg_stats_api_: StatsAPI = None
    chanjo: CommonAppConfig = None
    chanjo_api_: ChanjoAPI = None
    crunchy: CrunchyConfig = None
    crunchy_api_: CrunchyAPI = None
    data_delivery: DataDeliveryConfig = Field(None, alias="data-delivery")
    demultiplex: DemultiplexConfig = None
    demultiplex_api_: DemultiplexingAPI = None
    external: ExternalConfig = None
    genotype: CommonAppConfig = None
    genotype_api_: GenotypeAPI = None
    hermes: CommonAppConfig = None
    hermes_api_: HermesApi = None
    lims: LimsConfig = None
    lims_api_: LimsAPI = None
    loqusdb: CommonAppConfig = None
    loqusdb_api_: LoqusdbAPI = None
    loqusdb_wes: CommonAppConfig = Field(None, alias="loqusdb-wes")
    madeline_api_: MadelineAPI = None
    mutacc_auto: MutaccAutoConfig = Field(None, alias="mutacc-auto")
    mutacc_auto_api_: MutaccAutoAPI = None
    scout: CommonAppConfig = None
    scout_api_: ScoutAPI = None
    shipping: ShippingConfig = None
    shipping_api_: ShippingAPI = None
    trailblazer: TrailblazerConfig = None
    trailblazer_api_: TrailblazerAPI = None
    vogue: CommonAppConfig = None
    vogue_api_: VogueAPI = None

    # Meta APIs that will use the apps from CGConfig
    balsamic: BalsamicConfig = None
    statina: StatinaConfig = None
    fohm: Optional[FOHMConfig] = None
    fluffy: FluffyConfig = None
    microsalt: MicrosaltConfig = None
    gisaid: GisaidConfig = None
    mip_rd_dna: MipConfig = Field(None, alias="mip-rd-dna")
    mip_rd_rna: MipConfig = Field(None, alias="mip-rd-rna")
    mutant: MutantConfig = None

    # These are meta APIs that gets instantiated in the code
    meta_apis: dict = {}

    class Config:
        arbitrary_types_allowed = True
        fields = {
            "cg_stats_api_": "cg_stats_api",
            "chanjo_api_": "chanjo_api",
            "crunchy_api_": "crunchy_api",
            "demultiplex_api_": "demultiplex_api",
            "genotype_api_": "genotype_api",
            "hermes_api_": "hermes_api",
            "housekeeper_api_": "housekeeper_api",
            "lims_api_": "lims_api",
            "loqusdb_api_": "loqusdb_api",
            "madeline_api_": "madeline_api",
            "mutacc_auto_api_": "mutacc_auto_api",
            "scout_api_": "scout_api",
            "shipping_api_": "shipping_api",
            "status_db_": "status_db",
            "trailblazer_api_": "trailblazer_api",
            "vogue_api_": "vogue_api",
        }

    @property
    def chanjo_api(self) -> ChanjoAPI:
        api = self.__dict__.get("chanjo_api_")
        if api is None:
            LOG.debug("Instantiating chanjo api")
            api = ChanjoAPI(config=self.dict())
            self.chanjo_api_ = api
        return api

    @property
    def cg_stats_api(self) -> StatsAPI:
        api = self.__dict__.get("cg_stats_api_")
        if api is None:
            LOG.debug("Instantiating cg_stats api")
            api = StatsAPI(config=self.dict())
            self.cg_stats_api_ = api
        return api

    @property
    def crunchy_api(self) -> CrunchyAPI:
        api = self.__dict__.get("crunchy_api_")
        if api is None:
            LOG.debug("Instantiating crunchy api")
            api = CrunchyAPI(config=self.dict())
            self.crunchy_api_ = api
        return api

    @property
    def demultiplex_api(self) -> DemultiplexingAPI:
        demultiplex_api = self.__dict__.get("demultiplex_api_")
        if demultiplex_api is None:
            LOG.debug("Instantiating demultiplexing api")
            demultiplex_api = DemultiplexingAPI(config=self.dict())
            self.demultiplex_api_ = demultiplex_api
        return demultiplex_api

    @property
    def genotype_api(self) -> GenotypeAPI:
        api = self.__dict__.get("genotype_api_")
        if api is None:
            LOG.debug("Instantiating genotype api")
            api = GenotypeAPI(config=self.dict())
            self.genotype_api_ = api
        return api

    @property
    def hermes_api(self) -> HermesApi:
        hermes_api = self.__dict__.get("hermes_api_")
        if hermes_api is None:
            LOG.debug("Instantiating hermes api")
            hermes_api = HermesApi(config=self.dict())
            self.hermes_api_ = hermes_api
        return hermes_api

    @property
    def housekeeper_api(self) -> HousekeeperAPI:
        housekeeper_api = self.__dict__.get("housekeeper_api_")
        if housekeeper_api is None:
            LOG.debug("Instantiating housekeeper api")
            housekeeper_api = HousekeeperAPI(config=self.dict())
            self.housekeeper_api_ = housekeeper_api
        return housekeeper_api

    @property
    def lims_api(self) -> LimsAPI:
        api = self.__dict__.get("lims_api_")
        if api is None:
            LOG.debug("Instantiating lims api")
            api = LimsAPI(config=self.dict())
            self.lims_api_ = api
        return api

    @property
    def loqusdb_api(self) -> LoqusdbAPI:
        api = self.__dict__.get("loqusdb_api_")
        if api is None:
            LOG.debug("Instantiating loqusdb api")
            api = LoqusdbAPI(config=self.dict())
            self.loqusdb_api_ = api
        return api

    @property
    def madeline_api(self) -> MadelineAPI:
        api = self.__dict__.get("madeline_api_")
        if api is None:
            LOG.debug("Instantiating madeline api")
            api = MadelineAPI(config=self.dict())
            self.madeline_api_ = api
        return api

    @property
    def mutacc_auto_api(self) -> MutaccAutoAPI:
        api = self.__dict__.get("mutacc_auto_api_")
        if api is None:
            LOG.debug("Instantiating mutacc_auto api")
            api = MutaccAutoAPI(config=self.dict())
            self.mutacc_auto_api_ = api
        return api

    @property
    def scout_api(self) -> ScoutAPI:
        api = self.__dict__.get("scout_api_")
        if api is None:
            LOG.debug("Instantiating scout api")
            api = ScoutAPI(config=self.dict())
            self.scout_api_ = api
        return api

    @property
    def shipping_api(self) -> ShippingAPI:
        api = self.__dict__.get("shipping_api_")
        if api is None:
            LOG.debug("Instantiating shipping api")
            api = ShippingAPI(config=self.shipping.dict())
            self.shipping_api_ = api
        return api

    @property
    def status_db(self) -> Store:
        status_db = self.__dict__.get("status_db_")
        if status_db is None:
            LOG.debug("Instantiating status db")
            status_db = Store(self.database)
            self.status_db_ = status_db
        return status_db

    @property
    def trailblazer_api(self) -> TrailblazerAPI:
        api = self.__dict__.get("trailblazer_api_")
        if api is None:
            LOG.debug("Instantiating trailblazer api")
            api = TrailblazerAPI(config=self.dict())
            self.trailblazer_api_ = api
        return api

    @property
    def vogue_api(self) -> VogueAPI:
        api = self.__dict__.get("vogue_api_")
        if api is None:
            LOG.debug("Instantiating vogue api")
            api = VogueAPI(config=self.dict())
            self.vogue_api_ = api
        return api
