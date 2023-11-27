import logging

from pydantic.v1 import BaseModel, EmailStr, Field
from typing_extensions import Literal

from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.gens import GensAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.loqus import LoqusdbAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.constants.observations import LoqusdbInstance
from cg.constants.priority import SlurmQos
from cg.meta.backup.pdc import PdcAPI
from cg.store import Store
from cg.store.database import initialize_database

LOG = logging.getLogger(__name__)


class Sequencers(BaseModel):
    hiseqx: str
    hiseqga: str
    novaseq: str


class SlurmConfig(BaseModel):
    account: str
    hours: int | None
    mail_user: EmailStr
    memory: int | None
    number_tasks: int | None
    conda_env: str | None
    qos: SlurmQos = SlurmQos.LOW


class Encryption(BaseModel):
    encryption_dir: str
    binary_path: str


class PDCArchivingDirectory(BaseModel):
    current: str
    nas: str
    pre_nas: str


class DataInput(BaseModel):
    input_dir_path: str


class BackupConfig(BaseModel):
    pdc_archiving_directory: PDCArchivingDirectory
    slurm_flow_cell_encryption: SlurmConfig


class HousekeeperConfig(BaseModel):
    database: str
    root: str


class DemultiplexConfig(BaseModel):
    slurm: SlurmConfig


class TrailblazerConfig(BaseModel):
    service_account: str
    service_account_auth_file: str
    host: str


class StatinaConfig(BaseModel):
    host: str | None
    user: str
    key: str
    api_url: str
    upload_path: str
    auth_path: str


class CommonAppConfig(BaseModel):
    binary_path: str
    config_path: str | None


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
    conda_binary: str | None = None
    cram_reference: str
    slurm: SlurmConfig


class MutaccAutoConfig(CommonAppConfig):
    padding: int = 300


class BalsamicConfig(CommonAppConfig):
    balsamic_cache: str
    bed_path: str
    binary_path: str
    conda_env: str
    loqusdb_path: str
    pon_path: str
    root: str
    slurm: SlurmConfig
    swegen_path: str


class MutantConfig(BaseModel):
    binary_path: str
    conda_binary: str | None = None
    conda_env: str
    root: str


class MipConfig(BaseModel):
    conda_binary: str | None = None
    conda_env: str
    mip_config: str
    pipeline: str
    root: str
    script: str


class RnafusionConfig(CommonAppConfig):
    root: str
    references: str
    binary_path: str
    pipeline_path: str
    conda_env: str
    compute_env: str
    profile: str
    conda_binary: str | None = None
    launch_directory: str
    revision: str
    slurm: SlurmConfig
    tower_binary_path: str
    tower_pipeline: str


class TaxprofilerConfig(CommonAppConfig):
    root: str
    binary_path: str
    conda_env: str
    profile: str
    pipeline_path: str
    revision: str
    conda_binary: str | None = None
    hostremoval_reference: str
    databases: str
    slurm: SlurmConfig
    tower_binary_path: str
    tower_pipeline: str


class MicrosaltConfig(BaseModel):
    binary_path: str
    conda_binary: str | None = None
    conda_env: str
    queries_path: str
    root: str


class GisaidConfig(CommonAppConfig):
    submitter: str
    log_dir: str
    logwatch_email: EmailStr
    upload_password: str
    upload_cid: str


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


class DataFlowConfig(BaseModel):
    database_name: str
    user: str
    password: str
    url: str
    local_storage: str
    archive_repository: str


class CGConfig(BaseModel):
    database: str
    delivery_path: str
    demultiplexed_flow_cells_dir: str
    downsample_dir: str
    downsample_script: str
    email_base_settings: EmailBaseSettings
    environment: Literal["production", "stage"] = "stage"
    flow_cells_dir: str
    madeline_exe: str
    max_flowcells: int | None
    data_input: DataInput | None = None
    # Base APIs that always should exist
    status_db_: Store = None
    housekeeper: HousekeeperConfig
    housekeeper_api_: HousekeeperAPI = None

    # App APIs that can be instantiated in CGConfig
    backup: BackupConfig = None
    chanjo: CommonAppConfig = None
    chanjo_api_: ChanjoAPI = None
    crunchy: CrunchyConfig = None
    crunchy_api_: CrunchyAPI = None
    data_delivery: DataDeliveryConfig = Field(None, alias="data-delivery")
    data_flow_config: DataFlowConfig | None = None
    demultiplex: DemultiplexConfig = None
    demultiplex_api_: DemultiplexingAPI = None
    encryption: Encryption | None = None
    external: ExternalConfig = None
    genotype: CommonAppConfig = None
    genotype_api_: GenotypeAPI = None
    gens: CommonAppConfig = None
    gens_api_: GensAPI = None
    hermes: CommonAppConfig = None
    hermes_api_: HermesApi = None
    lims: LimsConfig = None
    lims_api_: LimsAPI = None
    loqusdb: CommonAppConfig = Field(None, alias=LoqusdbInstance.WGS.value)
    loqusdb_api_: LoqusdbAPI = None
    loqusdb_wes: CommonAppConfig = Field(None, alias=LoqusdbInstance.WES.value)
    loqusdb_somatic: CommonAppConfig = Field(None, alias=LoqusdbInstance.SOMATIC.value)
    loqusdb_tumor: CommonAppConfig = Field(None, alias=LoqusdbInstance.TUMOR.value)
    madeline_api_: MadelineAPI = None
    mutacc_auto: MutaccAutoConfig = Field(None, alias="mutacc-auto")
    mutacc_auto_api_: MutaccAutoAPI = None
    pigz: CommonAppConfig | None = None
    pdc: CommonAppConfig | None = None
    pdc_api_: PdcAPI | None
    scout: CommonAppConfig = None
    scout_api_: ScoutAPI = None
    tar: CommonAppConfig | None = None
    trailblazer: TrailblazerConfig = None
    trailblazer_api_: TrailblazerAPI = None

    # Meta APIs that will use the apps from CGConfig
    balsamic: BalsamicConfig = None
    statina: StatinaConfig = None
    fohm: FOHMConfig | None = None
    fluffy: FluffyConfig = None
    microsalt: MicrosaltConfig = None
    gisaid: GisaidConfig = None
    mip_rd_dna: MipConfig = Field(None, alias="mip-rd-dna")
    mip_rd_rna: MipConfig = Field(None, alias="mip-rd-rna")
    mutant: MutantConfig = None
    rnafusion: RnafusionConfig = Field(None, alias="rnafusion")
    taxprofiler: TaxprofilerConfig = Field(None, alias="taxprofiler")

    # These are meta APIs that gets instantiated in the code
    meta_apis: dict = {}

    class Config:
        arbitrary_types_allowed = True
        fields = {
            "chanjo_api_": "chanjo_api",
            "crunchy_api_": "crunchy_api",
            "demultiplex_api_": "demultiplex_api",
            "genotype_api_": "genotype_api",
            "gens_api_": "gens_api",
            "hermes_api_": "hermes_api",
            "housekeeper_api_": "housekeeper_api",
            "lims_api_": "lims_api",
            "loqusdb_api_": "loqusdb_api",
            "madeline_api_": "madeline_api",
            "mutacc_auto_api_": "mutacc_auto_api",
            "pdc_api_": "pdc_api",
            "scout_api_": "scout_api",
            "status_db_": "status_db",
            "trailblazer_api_": "trailblazer_api",
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
            demultiplex_api = DemultiplexingAPI(
                config=self.dict(), housekeeper_api=self.housekeeper_api
            )
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
    def gens_api(self) -> GensAPI:
        """Returns Gens API after making sure it has been instantiated."""
        api = self.__dict__.get("gens_api_")
        if api is None:
            LOG.debug("Instantiating gens api")
            api = GensAPI(config=self.dict())
            self.gens_api_ = api
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
            api: LoqusdbAPI = LoqusdbAPI(
                binary_path=self.loqusdb.binary_path, config_path=self.loqusdb.config_path
            )
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
    def pdc_api(self) -> PdcAPI:
        api = self.__dict__.get("pdc_api_")
        if api is None:
            LOG.debug("Instantiating PDC api")
            api = PdcAPI(binary_path=self.pdc.binary_path)
            self.pdc_api_ = api
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
    def status_db(self) -> Store:
        status_db = self.__dict__.get("status_db_")
        if status_db is None:
            LOG.debug("Instantiating status db")
            initialize_database(self.database)
            status_db = Store()
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
