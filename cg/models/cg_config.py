import logging
from pathlib import Path

from pydantic.v1 import BaseModel, EmailStr, Field
from typing_extensions import Literal

from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.api import SampleSheetAPI
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
from cg.clients.arnold.api import ArnoldAPIClient
from cg.clients.janus.api import JanusAPIClient
from cg.constants.observations import LoqusdbInstance
from cg.constants.priority import SlurmQos
from cg.meta.backup.pdc import PdcAPI
from cg.meta.delivery.delivery import DeliveryAPI
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.slurm_service.slurm_cli_service import SlurmCLIService
from cg.services.slurm_service.slurm_service import SlurmService
from cg.services.slurm_upload_service.slurm_upload_config import SlurmUploadConfig
from cg.services.slurm_upload_service.slurm_upload_service import SlurmUploadService
from cg.store.database import initialize_database
from cg.store.store import Store

LOG = logging.getLogger(__name__)


class Sequencers(BaseModel):
    hiseqx: str
    hiseqga: str
    novaseq: str


class ArnoldConfig(BaseModel):
    api_url: str


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


class DownsampleConfig(BaseModel):
    downsample_dir: str
    downsample_script: str
    account: str


class JanusConfig(BaseModel):
    host: str


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
    binary_path: str | None
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
    cadd_path: str
    conda_binary: str
    conda_env: str
    genome_interval_path: str
    gens_coverage_female_path: str
    gens_coverage_male_path: str
    gnomad_af5_path: str
    loqusdb_path: str
    pon_path: str
    root: str
    sentieon_licence_path: str
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
    workflow: str
    root: str
    script: str


class RarediseaseConfig(CommonAppConfig):
    binary_path: str | None = None
    compute_env: str
    conda_binary: str | None = None
    conda_env: str
    config_platform: str
    config_params: str
    config_resources: str
    launch_directory: str
    workflow_path: str
    profile: str
    references: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str


class TomteConfig(CommonAppConfig):
    binary_path: str | None = None
    compute_env: str
    conda_binary: str | None = None
    conda_env: str
    config_platform: str
    config_params: str
    config_resources: str
    workflow_path: str
    profile: str
    references: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str


class RnafusionConfig(CommonAppConfig):
    root: str
    references: str
    binary_path: str
    workflow_path: str
    conda_env: str
    compute_env: str
    profile: str
    conda_binary: str | None = None
    launch_directory: str
    revision: str
    slurm: SlurmConfig
    tower_workflow: str


class TaxprofilerConfig(CommonAppConfig):
    binary_path: str
    conda_binary: str | None = None
    conda_env: str
    compute_env: str
    databases: str
    hostremoval_reference: str
    workflow_path: str
    profile: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str


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


class PacbioConfig(BaseModel):
    data_dir: str
    systemd_trigger_dir: str


class OxfordNanoporeConfig(BaseModel):
    data_dir: str
    systemd_trigger_dir: str


class IlluminaConfig(BaseModel):
    sequencing_runs_dir: str
    demultiplexed_runs_dir: str


class RunInstruments(BaseModel):
    pacbio: PacbioConfig
    nanopore: OxfordNanoporeConfig
    illumina: IlluminaConfig


class CGConfig(BaseModel):
    data_input: DataInput | None = None
    database: str
    delivery_path: str
    downsample: DownsampleConfig
    email_base_settings: EmailBaseSettings
    environment: Literal["production", "stage"] = "stage"
    madeline_exe: str
    max_flowcells: int | None
    nanopore_data_directory: str
    run_instruments: RunInstruments
    sentieon_licence_server: str
    tower_binary_path: str

    # Base APIs that always should exist
    housekeeper: HousekeeperConfig
    housekeeper_api_: HousekeeperAPI = None
    status_db_: Store | None = None

    # App APIs that can be instantiated in CGConfig
    arnold: ArnoldConfig | None = None
    arnold_api_: ArnoldAPIClient | None = None
    backup: BackupConfig = None
    chanjo: CommonAppConfig = None
    chanjo_api_: ChanjoAPI = None
    crunchy: CrunchyConfig = None
    crunchy_api_: CrunchyAPI = None
    data_delivery: DataDeliveryConfig = Field(None, alias="data-delivery")
    data_flow: DataFlowConfig | None = None
    delivery_api_: DeliveryAPI | None = None
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
    janus: JanusConfig | None = None
    janus_api_: JanusAPIClient | None = None
    lims: LimsConfig = None
    lims_api_: LimsAPI = None
    loqusdb: CommonAppConfig = Field(None, alias=LoqusdbInstance.WGS.value)
    loqusdb_api_: LoqusdbAPI = None
    loqusdb_somatic: CommonAppConfig = Field(None, alias=LoqusdbInstance.SOMATIC.value)
    loqusdb_tumor: CommonAppConfig = Field(None, alias=LoqusdbInstance.TUMOR.value)
    loqusdb_wes: CommonAppConfig = Field(None, alias=LoqusdbInstance.WES.value)
    madeline_api_: MadelineAPI = None
    mutacc_auto: MutaccAutoConfig = Field(None, alias="mutacc-auto")
    mutacc_auto_api_: MutaccAutoAPI = None
    pdc: CommonAppConfig | None = None
    pdc_api_: PdcAPI | None
    pigz: CommonAppConfig | None = None
    sample_sheet_api_: SampleSheetAPI | None = None
    scout: CommonAppConfig = None
    scout_api_: ScoutAPI = None
    tar: CommonAppConfig | None = None
    trailblazer: TrailblazerConfig = None
    trailblazer_api_: TrailblazerAPI = None

    # Meta APIs that will use the apps from CGConfig
    balsamic: BalsamicConfig | None = None
    fluffy: FluffyConfig | None = None
    fohm: FOHMConfig | None = None
    gisaid: GisaidConfig | None = None
    microsalt: MicrosaltConfig | None = None
    mip_rd_dna: MipConfig | None = Field(None, alias="mip-rd-dna")
    mip_rd_rna: MipConfig | None = Field(None, alias="mip-rd-rna")
    mutant: MutantConfig | None = None
    raredisease: RarediseaseConfig | None = None
    rnafusion: RnafusionConfig | None = None
    statina: StatinaConfig | None = None
    taxprofiler: TaxprofilerConfig | None = None
    tomte: TomteConfig | None = None

    # These are meta APIs that gets instantiated in the code
    meta_apis: dict = {}

    class Config:
        arbitrary_types_allowed = True
        fields = {
            "arnold_api_": "arnold_api",
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
            "janus_api_": "janus_api",
        }

    @property
    def arnold_api(self) -> ArnoldAPIClient:
        api = self.__dict__.get("arnold_api_")
        if api is None:
            LOG.debug("Instantiating arnold api")
            api = ArnoldAPIClient(config=self.dict())
            self.arnold_api_ = api
        return api

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
    def janus_api(self) -> JanusAPIClient:
        janus_api = self.__dict__.get("janus_api_")
        if janus_api is None:
            LOG.debug("Instantiating janus api")
            janus_api = JanusAPIClient(config=self.dict())
            self.janus_api_ = janus_api
        return janus_api

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
    def sample_sheet_api(self) -> SampleSheetAPI:
        sample_sheet_api = self.__dict__.get("sample_sheet_api_")
        if sample_sheet_api is None:
            LOG.debug("Instantiating sample sheet API")
            sample_sheet_api = SampleSheetAPI(
                flow_cell_dir=self.run_instruments.illumina.sequencing_runs_dir,
                hk_api=self.housekeeper_api,
                lims_api=self.lims_api,
            )
            self.sample_sheet_api_ = sample_sheet_api
        return sample_sheet_api

    @property
    def slurm_service(self) -> SlurmService:
        return SlurmCLIService()

    @property
    def slurm_upload_service(self) -> SlurmUploadService:
        slurm_upload_config = SlurmUploadConfig(
            email=self.data_delivery.mail_user,
            account=self.data_delivery.account,
            log_dir=self.data_delivery.base_path,
        )
        return SlurmUploadService(
            slurm_service=self.slurm_service,
            trailblazer_api=self.trailblazer_api,
            config=slurm_upload_config,
        )

    @property
    def analysis_service(self) -> AnalysisService:
        return AnalysisService(analysis_client=self.trailblazer_api)

    @property
    def scout_api(self) -> ScoutAPI:
        api = self.__dict__.get("scout_api_")
        if api is None:
            LOG.debug("Instantiating scout api")
            api = ScoutAPI(config=self.dict(), slurm_upload_service=self.slurm_upload_service)
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

    @property
    def fastq_concatenation_service(self) -> FastqConcatenationService:
        return FastqConcatenationService()

    @property
    def delivery_api(self) -> DeliveryAPI:
        api = self.__dict__.get("delivery_api_")
        if api is None:
            LOG.debug("Instantiating delivery api")
            api = DeliveryAPI(
                delivery_path=Path(self.delivery_path),
                fastq_concatenation_service=self.fastq_concatenation_service,
                housekeeper_api=self.housekeeper_api,
                store=self.status_db,
            )
            self.delivery_api_ = api
        return api
