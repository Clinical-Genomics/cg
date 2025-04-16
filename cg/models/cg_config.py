import logging
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field
from typing_extensions import Literal

from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.demultiplex.sample_sheet.api import IlluminaSampleSheetService
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
from cg.clients.chanjo2.client import Chanjo2APIClient
from cg.clients.janus.api import JanusAPIClient
from cg.constants.observations import LoqusdbInstance
from cg.constants.priority import SlurmQos
from cg.meta.delivery.delivery import DeliveryAPI
from cg.services.analysis_service.analysis_service import AnalysisService
from cg.services.decompression_service.decompressor import Decompressor
from cg.services.deliver_files.factory import DeliveryServiceFactory
from cg.services.deliver_files.rsync.models import RsyncDeliveryConfig
from cg.services.deliver_files.rsync.service import DeliveryRsyncService
from cg.services.fastq_concatenation_service.fastq_concatenation_service import (
    FastqConcatenationService,
)
from cg.services.pdc_service.pdc_service import PdcService
from cg.services.run_devices.pacbio.data_storage_service.pacbio_store_service import (
    PacBioStoreService,
)
from cg.services.run_devices.pacbio.data_transfer_service.data_transfer_service import (
    PacBioDataTransferService,
)
from cg.services.run_devices.pacbio.housekeeper_service.pacbio_houskeeper_service import (
    PacBioHousekeeperService,
)
from cg.services.run_devices.pacbio.metrics_parser.metrics_parser import PacBioMetricsParser
from cg.services.run_devices.pacbio.post_processing_service import PacBioPostProcessingService
from cg.services.run_devices.pacbio.run_data_generator.pacbio_run_data_generator import (
    PacBioRunDataGenerator,
)
from cg.services.run_devices.pacbio.run_file_manager.run_file_manager import PacBioRunFileManager
from cg.services.run_devices.pacbio.run_validator.pacbio_run_validator import PacBioRunValidator
from cg.services.run_devices.run_names.pacbio import PacbioRunNamesService
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService
from cg.services.slurm_service.slurm_cli_service import SlurmCLIService
from cg.services.slurm_service.slurm_service import SlurmService
from cg.services.slurm_upload_service.slurm_upload_config import SlurmUploadConfig
from cg.services.slurm_upload_service.slurm_upload_service import SlurmUploadService
from cg.services.validate_file_transfer_service.validate_file_transfer_service import (
    ValidateFileTransferService,
)
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
    hours: int | None = None
    mail_user: EmailStr
    memory: int | None = None
    number_tasks: int | None = None
    conda_env: str | None = None
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


class IlluminaBackupConfig(BaseModel):
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


class ClientConfig(BaseModel):
    host: str


class TrailblazerConfig(BaseModel):
    service_account: str
    service_account_auth_file: str
    host: str


class StatinaConfig(BaseModel):
    host: str | None = None
    user: str
    key: str
    api_url: str
    upload_path: str
    auth_path: str


class CommonAppConfig(BaseModel):
    binary_path: str | None = None
    config_path: str | None = None
    container_mount_volume: str | None = None


class HermesConfig(CommonAppConfig):
    container_path: str


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


class NalloConfig(CommonAppConfig):
    binary_path: str | None = None
    compute_env: str
    conda_binary: str | None = None
    conda_env: str
    platform: str
    params: str
    config: str
    resources: str
    launch_directory: str
    workflow_bin_path: str
    profile: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str


class RarediseaseConfig(CommonAppConfig):
    binary_path: str | None = None
    compute_env: str
    conda_binary: str | None = None
    conda_env: str
    platform: str
    params: str
    config: str
    resources: str
    launch_directory: str
    workflow_bin_path: str
    profile: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str


class TomteConfig(CommonAppConfig):
    binary_path: str | None = None
    compute_env: str
    conda_binary: str | None = None
    conda_env: str
    platform: str
    params: str
    config: str
    resources: str
    workflow_bin_path: str
    profile: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str


class RnafusionConfig(CommonAppConfig):
    binary_path: str
    compute_env: str
    conda_binary: str | None = None
    conda_env: str
    platform: str
    params: str
    config: str
    resources: str
    launch_directory: str
    profile: str
    revision: str
    root: str
    slurm: SlurmConfig
    tower_workflow: str
    workflow_bin_path: str


class TaxprofilerConfig(CommonAppConfig):
    binary_path: str
    conda_binary: str | None = None
    conda_env: str
    compute_env: str
    platform: str
    params: str
    config: str
    resources: str
    workflow_bin_path: str
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
    account: str
    base_path: str
    covid_destination_path: str
    covid_report_path: str
    destination_path: str
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


class RunNamesServices(BaseModel):
    pacbio: PacbioRunNamesService
    model_config = ConfigDict(arbitrary_types_allowed=True)


class PostProcessingServices(BaseModel):
    pacbio: PacBioPostProcessingService
    model_config = ConfigDict(arbitrary_types_allowed=True)


class CGConfig(BaseModel):
    data_input: DataInput | None = None
    database: str
    delivery_path: str
    downsample: DownsampleConfig
    email_base_settings: EmailBaseSettings
    environment: Literal["production", "stage"] = "stage"
    madeline_exe: str
    max_flowcells: int | None = None
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
    illumina_backup_service: IlluminaBackupConfig | None = None
    chanjo: CommonAppConfig = None
    chanjo_api_: ChanjoAPI = None
    chanjo2: ClientConfig | None = None
    chanjo2_api_: Chanjo2APIClient | None = None
    crunchy: CrunchyConfig = None
    crunchy_api_: CrunchyAPI = None
    data_delivery: DataDeliveryConfig = Field(None, alias="data-delivery")
    data_flow: DataFlowConfig | None = None
    delivery_api_: DeliveryAPI | None = None
    delivery_rsync_service_: DeliveryRsyncService | None = None
    delivery_service_factory_: DeliveryServiceFactory | None = None
    demultiplex: DemultiplexConfig = None
    demultiplex_api_: DemultiplexingAPI = None
    encryption: Encryption | None = None
    external: ExternalConfig = None
    genotype: CommonAppConfig = None
    genotype_api_: GenotypeAPI = None
    gens: CommonAppConfig = None
    gens_api_: GensAPI = None
    hermes: HermesConfig = None
    hermes_api_: HermesApi = None
    janus: ClientConfig | None = None
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
    pdc_service_: PdcService | None = None
    post_processing_services_: PostProcessingServices | None = None
    pigz: CommonAppConfig | None = None
    run_names_services_: RunNamesServices | None = None
    sample_sheet_api_: IlluminaSampleSheetService | None = None
    scout: CommonAppConfig = None
    scout_38: CommonAppConfig = None
    scout_api_37_: ScoutAPI = None
    scout_api_38_: ScoutAPI = None
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
    nallo: NalloConfig | None = None
    raredisease: RarediseaseConfig | None = None
    rnafusion: RnafusionConfig | None = None
    statina: StatinaConfig | None = None
    taxprofiler: TaxprofilerConfig | None = None
    tomte: TomteConfig | None = None

    # These are meta APIs that gets instantiated in the code
    meta_apis: dict = {}

    model_config = ConfigDict(arbitrary_types_allowed=True)

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
    def chanjo2_api(self) -> Chanjo2APIClient:
        chanjo2_api = self.__dict__.get("chanjo2_api_")
        if chanjo2_api is None:
            LOG.debug("Instantiating Chanjo2 API")
            config: dict[str, Any] = self.dict()
            chanjo2_api = Chanjo2APIClient(base_url=config["chanjo2"]["host"])
            self.chanjo2_api_ = chanjo2_api
        return chanjo2_api

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
    def post_processing_services(self) -> PostProcessingServices:
        services = self.__dict__.get("post_processing_services_")
        if services is None:
            LOG.debug("Instantiating post-processing services")
            services = PostProcessingServices(
                pacbio=self.get_pacbio_post_processing_service(),
            )
            self.post_processing_services_ = services
        return services

    def get_pacbio_post_processing_service(self) -> PacBioPostProcessingService:
        LOG.debug("Instantiating PacBio post-processing service")
        run_data_generator = PacBioRunDataGenerator()
        file_manager = PacBioRunFileManager()
        run_validator = PacBioRunValidator(
            file_manager=file_manager,
            decompressor=Decompressor(),
            file_transfer_validator=ValidateFileTransferService(),
        )
        metrics_parser = PacBioMetricsParser(file_manager=file_manager)
        transfer_service = PacBioDataTransferService(metrics_service=metrics_parser)
        store_service = PacBioStoreService(
            store=self.status_db, data_transfer_service=transfer_service
        )
        hk_service = PacBioHousekeeperService(
            hk_api=self.housekeeper_api,
            file_manager=file_manager,
            metrics_parser=metrics_parser,
        )
        return PacBioPostProcessingService(
            run_validator=run_validator,
            run_data_generator=run_data_generator,
            hk_service=hk_service,
            store_service=store_service,
            sequencing_dir=self.run_instruments.pacbio.data_dir,
        )

    @property
    def pdc_service(self) -> PdcService:
        service = self.__dict__.get("pdc_service_")
        if service is None:
            LOG.debug("Instantiating PDC service")
            service = PdcService(binary_path=self.pdc.binary_path)
            self.pdc_service_ = service
        return service

    @property
    def run_names_services(self) -> RunNamesServices:
        services = self.run_names_services_
        if services is None:
            LOG.debug("Instantiating run directory names services")
            services = RunNamesServices(
                pacbio=PacbioRunNamesService(self.run_instruments.pacbio.data_dir)
            )
            self.run_names_services_ = services
        return services

    @property
    def sample_sheet_api(self) -> IlluminaSampleSheetService:
        sample_sheet_api = self.__dict__.get("sample_sheet_api_")
        if sample_sheet_api is None:
            LOG.debug("Instantiating sample sheet API")
            sample_sheet_api = IlluminaSampleSheetService(
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
        return AnalysisService(analysis_client=self.trailblazer_api, status_db=self.status_db)

    @property
    def scout_api_37(self) -> ScoutAPI:
        api = self.scout_api_37_
        if not api:
            LOG.debug("Instantiating scout api, genome build 37")
            api = ScoutAPI(scout_config=self.scout, slurm_upload_service=self.slurm_upload_service)
            self.scout_api_37_ = api
        return api

    @property
    def scout_api_38(self) -> ScoutAPI:
        api = self.scout_api_38_
        if api is None:
            LOG.debug("Instantiating scout api, genome build 38")
            api = ScoutAPI(
                scout_config=self.scout_38, slurm_upload_service=self.slurm_upload_service
            )
            self.scout_api_38_ = api
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

    @property
    def sequencing_qc_service(self) -> SequencingQCService:
        return SequencingQCService(self.status_db)

    @property
    def delivery_rsync_service(self) -> DeliveryRsyncService:
        service = self.delivery_rsync_service_
        if service is None:
            LOG.debug("Instantiating delivery rsync service")
            rsync_config = RsyncDeliveryConfig(**self.data_delivery.dict())
            service = DeliveryRsyncService(
                delivery_path=self.delivery_path,
                rsync_config=rsync_config,
                status_db=self.status_db,
            )
            self.delivery_rsync_service_ = service
        return service

    @property
    def delivery_service_factory(self) -> DeliveryServiceFactory:
        factory = self.delivery_service_factory_
        if not factory:
            LOG.debug("Instantiating delivery service factory")
            factory = DeliveryServiceFactory(
                store=self.status_db,
                lims_api=self.lims_api,
                hk_api=self.housekeeper_api,
                tb_service=self.trailblazer_api,
                rsync_service=self.delivery_rsync_service,
                analysis_service=self.analysis_service,
            )
            self.delivery_service_factory_ = factory
        return factory
