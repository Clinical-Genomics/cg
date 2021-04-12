import logging
from typing import Optional

from cg.apps.coverage import ChanjoAPI
from cg.apps.crunchy import CrunchyAPI
from cg.apps.demultiplex.demultiplex_api import DemultiplexingAPI
from cg.apps.gt import GenotypeAPI
from cg.apps.hermes.hermes_api import HermesApi
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.apps.lims import LimsAPI
from cg.apps.madeline.api import MadelineAPI
from cg.apps.mutacc_auto import MutaccAutoAPI
from cg.apps.scout.scoutapi import ScoutAPI
from cg.apps.tb import TrailblazerAPI
from cg.apps.vogue import VogueAPI
from cg.store import Store
from pydantic import BaseModel, EmailStr, Field
from typing_extensions import Literal

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
    qos: Literal["low", "normal", "high"] = "low"


class HousekeeperConfig(BaseModel):
    database: str
    root: str


class DemultiplexConfig(BaseModel):
    out_dir: str
    slurm: SlurmConfig


class TrailblazerConfig(BaseModel):
    database: str
    root: str
    service_account: str
    service_account_auth_file: str
    host: str


class CommonAppConfig(BaseModel):
    binary_path: str
    config_path: Optional[str]
    deploy_config: Optional[str]


class FluffyConfig(CommonAppConfig):
    root_dir: str


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
    singularity: str
    reference_config: str
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


class CGConfig(BaseModel):
    database: str
    environment: Literal["production", "stage"] = "stage"
    madeline_exe: str
    bed_path: str
    delivery_path: str
    max_flowcells: Optional[int]
    # Base APIs that always should exist
    status_db_: Store = None
    housekeeper: HousekeeperConfig
    housekeeper_api_: HousekeeperAPI = None

    # App APIs that can be instantiated in CGConfig
    demultiplex: DemultiplexConfig = None
    demultiplex_api_: DemultiplexingAPI = None
    hermes: CommonAppConfig = None
    hermes_api_: HermesApi = None
    backup: BackupConfig = None
    scout: CommonAppConfig = None
    scout_api_: ScoutAPI = None
    trailblazer: TrailblazerConfig = None
    trailblazer_api_: TrailblazerAPI = None
    lims: LimsConfig = None
    lims_api_: LimsAPI = None
    vogue: CommonAppConfig = None
    vogue_api_: VogueAPI = None
    crunchy: CrunchyConfig = None
    crunchy_api_: CrunchyAPI = None
    madeline_api_: MadelineAPI = None
    mutacc_auto: MutaccAutoConfig = None
    mutacc_auto_api_: MutaccAutoAPI = None
    genotype: CommonAppConfig = None
    genotype_api_: GenotypeAPI = None
    chanjo: CommonAppConfig = None
    chanjo_api_: ChanjoAPI = None

    # Meta APIs that will use the apps from CGConfig
    fluffy: FluffyConfig = None
    balsamic: BalsamicConfig = None
    mutant: MutantConfig = None
    mip_rd_dna: MipConfig = Field(None, alias="mip-rd-dna")
    mip_rd_rna: MipConfig = Field(None, alias="mip-rd-rna")

    # These are meta APIs that gets instantiated in the code
    meta_apis: dict = {}

    class Config:
        arbitrary_types_allowed = True
        fields = {
            "status_db_": "status_db",
            "housekeeper_api_": "housekeeper_api",
            "demultiplex_api_": "demultiplex_api",
            "hermes_api_": "hermes_api",
            "scout_api_": "scout_api",
            "trailblazer_api_": "trailblazer_api",
            "lims_api_": "lims_api",
            "vogue_api_": "vogue_api",
            "crunchy_api_": "crunchy_api",
            "madeline_api_": "madeline_api",
            "mutacc_auto_api_": "mutacc_auto_api",
            "genotype_api_": "genotype_api",
            "chanjo_api_": "chanjo_api",
        }

    @property
    def status_db(self) -> Store:
        status_db = self.__dict__.get("status_db_")
        if status_db is None:
            LOG.info("Instantiating status db")
            status_db = Store(self.database)
            self.status_db_ = status_db
        return status_db

    @property
    def housekeeper_api(self) -> HousekeeperAPI:
        housekeeper_api = self.__dict__.get("housekeeper_api_")
        if housekeeper_api is None:
            LOG.info("Instantiating housekeeper api")
            housekeeper_api = HousekeeperAPI(config=self.dict())
            self.housekeeper_api_ = housekeeper_api
        return housekeeper_api

    @property
    def demultiplex_api(self) -> DemultiplexingAPI:
        demultiplex_api = self.__dict__.get("demultiplex_api_")
        if demultiplex_api is None:
            LOG.info("Instantiating demultiplexing api")
            demultiplex_api = DemultiplexingAPI(config=self.dict())
            self.demultiplex_api_ = demultiplex_api
        return demultiplex_api

    @property
    def hermes_api(self) -> HermesApi:
        hermes_api = self.__dict__.get("hermes_api_")
        if hermes_api is None:
            LOG.info("Instantiating hermes api")
            hermes_api = HermesApi(config=self.dict())
            self.hermes_api_ = hermes_api
        return hermes_api

    @property
    def scout_api(self) -> ScoutAPI:
        api = self.__dict__.get("scout_api_")
        if api is None:
            LOG.info("Instantiating scout api")
            api = ScoutAPI(config=self.dict())
            self.scout_api_ = api
        return api

    @property
    def trailblazer_api(self) -> TrailblazerAPI:
        api = self.__dict__.get("trailblazer_api_")
        if api is None:
            LOG.info("Instantiating trailblazer api")
            api = TrailblazerAPI(config=self.dict())
            self.trailblazer_api_ = api
        return api

    @property
    def lims_api(self) -> LimsAPI:
        api = self.__dict__.get("lims_api_")
        if api is None:
            LOG.info("Instantiating lims api")
            api = LimsAPI(config=self.dict())
            self.lims_api_ = api
        return api

    @property
    def vogue_api(self) -> VogueAPI:
        api = self.__dict__.get("vogue_api_")
        if api is None:
            LOG.info("Instantiating vogue api")
            api = VogueAPI(config=self.dict())
            self.vogue_api_ = api
        return api

    @property
    def crunchy_api(self) -> CrunchyAPI:
        api = self.__dict__.get("crunchy_api_")
        if api is None:
            LOG.info("Instantiating crunchy api")
            api = CrunchyAPI(config=self.dict())
            self.crunchy_api_ = api
        return api

    @property
    def madeline_api(self) -> MadelineAPI:
        api = self.__dict__.get("madeline_api_")
        if api is None:
            LOG.info("Instantiating madeline api")
            api = MadelineAPI(config=self.dict())
            self.madeline_api_ = api
        return api

    @property
    def mutacc_auto_api(self) -> MutaccAutoAPI:
        api = self.__dict__.get("mutacc_auto_api_")
        if api is None:
            LOG.info("Instantiating mutacc_auto api")
            api = MutaccAutoAPI(config=self.dict())
            self.mutacc_auto_api_ = api
        return api

    @property
    def genotype_api(self) -> GenotypeAPI:
        api = self.__dict__.get("genotype_api_")
        if api is None:
            LOG.info("Instantiating genotype api")
            api = GenotypeAPI(config=self.dict())
            self.genotype_api_ = api
        return api

    @property
    def chanjo_api(self) -> ChanjoAPI:
        api = self.__dict__.get("chanjo_api_")
        if api is None:
            LOG.info("Instantiating chanjo api")
            api = ChanjoAPI(config=self.dict())
            self.chanjo_api_ = api
        return api


if __name__ == "__main__":
    config = {
        "database": "mysql+pymysql://auser:apwd@localhost:3308/cg-stage",
        "madeline_exe": "path/to/madeline",
        "bed_path": "path/to/bed",
        "delivery_path": "path/to/delivery",
        "housekeeper": {
            "database": "mysql+pymysql://auser:apwd@localhost:3308/housekeeper-stage",
            "root": "path/to/root",
        },
    }
    #
    # This will replace context.ob
    cg_configs = CGConfig(**config)
    print(cg_configs)
    store = cg_configs.status_db
    print(store)
    another_store = cg_configs.status_db
    print(another_store)
