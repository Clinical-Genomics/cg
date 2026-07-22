"""Module for Balsamic Analysis API."""

import logging
from pathlib import Path

from housekeeper.store.models import File, Version
from pydantic import EmailStr
from pydantic.v1 import ValidationError

from cg.constants import Workflow
from cg.constants.constants import BedVersionGenomeVersion, FileFormat, GenomeVersion, SampleType
from cg.constants.housekeeper_tags import BalsamicAnalysisTag
from cg.constants.priority import SlurmQos
from cg.constants.scout import BALSAMIC_CASE_TAGS
from cg.exc import BalsamicStartError, CgError
from cg.io.controller import ReadFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.config import BalsamicVarCaller
from cg.models.balsamic.metrics import (
    BalsamicMetricsBase,
    BalsamicTargetedQCMetrics,
    BalsamicWGSQCMetrics,
)
from cg.models.cg_config import CGConfig
from cg.store.models import Case, CaseSample, Sample
from cg.utils import Process
from cg.utils.utils import build_command_from_dict

LOG = logging.getLogger(__name__)


class BalsamicAnalysisAPI(AnalysisAPI):
    """Handles communication between BALSAMIC processes and the rest of CG infrastructure."""

    __BALSAMIC_APPLICATIONS = {"wgs", "wes", "tgs"}
    __BALSAMIC_BED_APPLICATIONS = {"wes", "tgs"}

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.BALSAMIC,
    ):
        super().__init__(workflow=workflow, config=config)
        self.account: str = config.balsamic.slurm.account
        self.balsamic_cache: str = str(config.balsamic.balsamic_cache)
        self.bed_path: str = str(config.balsamic.bed_path)
        self.binary_path: str = str(config.balsamic.binary_path)
        self.cadd_path: str = str(config.balsamic.cadd_path)
        self.conda_binary: str = str(config.balsamic.conda_binary)
        self.conda_env: str = config.balsamic.conda_env
        self.email: EmailStr = config.balsamic.slurm.mail_user
        self.genome_interval_path: str = str(config.balsamic.genome_interval_path)
        self.gens_coverage_female_path: str = str(config.balsamic.gens_coverage_female_path)
        self.gens_coverage_male_path: str = str(config.balsamic.gens_coverage_male_path)
        self.gnomad_af5_path: str = str(config.balsamic.gnomad_af5_path)
        self.head_job_partition: str = config.balsamic.head_job_partition
        self.loqusdb_path: str = str(config.balsamic.loqusdb_path)
        self.pon_path: str = str(config.balsamic.pon_path)
        self.qos: SlurmQos = config.balsamic.slurm.qos
        self.root_dir: str = str(config.balsamic.root)
        self.sentieon_licence_path: str = str(config.balsamic.sentieon_licence_path)
        self.sentieon_licence_server: str = config.balsamic.sentieon_licence_server
        self.swegen_path: str = config.balsamic.swegen_path

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def fastq_handler(self):
        return BalsamicFastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(
                binary=self.binary_path, conda_binary=self.conda_binary, environment=self.conda_env
            )
        return self._process

    @property
    def PON_file_suffix(self) -> str:
        """Panel of normals reference file suffix (<panel-bed>_<PON>_<version>.cnn)"""

        return "CNVkit_PON_reference_v*.cnn"

    def get_case_path(self, case_id: str) -> Path:
        """Returns a path where the Balsamic case for the case_id should be located"""
        return Path(self.root_dir, case_id)

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """Returns a path where the Balsamic deliverables file for the case_id should be located.

        (Optional) Checks if deliverables file exists
        """
        return Path(
            self.root_dir,
            case_id,
            "analysis",
            "delivery_report",
            case_id + ".hk",
        )

    def get_case_config_path(self, case_id: str) -> Path:
        """Generates a path where the Balsamic config for the case_id should be located.

        (Optional) Checks if config file exists.
        """
        return Path(self.root_dir, case_id, case_id + ".json")

    def get_job_ids_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "analysis", "slurm_jobids.yaml")

    def get_bundle_deliverables_type(self, case_id: str) -> str:
        """Return the analysis type for a case

        Analysis types are any of ["tumor_wgs", "tumor_normal_wgs", "tumor_panel", "tumor_normal_panel"]
        """
        LOG.debug(f"Fetch analysis type for {case_id}")
        number_of_samples: int = len(
            self.status_db.get_case_by_internal_id(internal_id=case_id).links
        )

        application_type: str = self.get_analysis_type(
            self.status_db.get_case_by_internal_id(internal_id=case_id).links[0].sample
        )
        sample_type = "tumor"
        if number_of_samples == 2:
            sample_type = "tumor_normal"
        if application_type != "wgs":
            application_type = "panel"
        analysis_type = "_".join([sample_type, application_type])
        LOG.debug(f"Found analysis type {analysis_type}")
        return analysis_type

    def get_sample_fastq_destination_dir(self, case: Case, sample: Sample = None) -> Path:
        """Return the path to the FASTQ destination directory."""
        return Path(self.get_case_path(case.internal_id), FileFormat.FASTQ)

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        """Link fastq files from Housekeeper to Balsamic case working directory."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        for link in case.links:
            self.link_fastq_files_for_sample(case=case, sample=link.sample)

    @staticmethod
    def get_sample_type(sample_obj: Sample) -> SampleType:
        """Return the tissue type of the sample."""
        if sample_obj.is_tumour:
            return SampleType.TUMOR
        return SampleType.NORMAL

    def get_derived_bed(self, panel_bed: str) -> Path | None:
        """Returns the verified capture kit path or the derived panel BED path."""
        if not panel_bed:
            return None
        panel_bed: Path = Path(panel_bed)
        if panel_bed.is_file():
            return panel_bed
        derived_panel_bed: Path = Path(
            self.bed_path,
            self.status_db.get_bed_version_by_short_name_and_genome_version_strict(
                short_name=panel_bed.as_posix(), genome_version=BedVersionGenomeVersion.HG19
            ).filename,
        )
        if not derived_panel_bed.is_file():
            raise BalsamicStartError(
                f"{panel_bed} or {derived_panel_bed} are not valid paths to a BED file. "
                f"Please provide absolute path to desired BED file or a valid bed shortname!"
            )
        return derived_panel_bed

    def get_verified_bed(self, panel_bed: str, sample_data: dict) -> str | None:
        """Takes a dict with samples and attributes.
        Retrieves unique attributes for application type and target_bed.
        Verifies that those attributes are the same across multiple samples,
        where applicable.
        Verifies that the attributes are valid BALSAMIC attributes
        If application type requires bed, returns path to bed.

        Raises BalsamicStartError:
        - When application type invalid for balsamic
        - When multiple samples have different parameters
        - When bed file required for analysis, but is not set or cannot be retrieved.
        """

        panel_bed: Path | None = self.get_derived_bed(panel_bed)
        application_types = {v["application_type"].lower() for k, v in sample_data.items()}
        target_beds: set = {v["target_bed"] for k, v in sample_data.items()}

        if not application_types.issubset(self.__BALSAMIC_APPLICATIONS):
            raise BalsamicStartError("Case application not compatible with BALSAMIC")
        if len(application_types) != 1:
            raise BalsamicStartError("Multiple application types found in LIMS")
        if not application_types.issubset(self.__BALSAMIC_BED_APPLICATIONS):
            if panel_bed:
                raise BalsamicStartError("Cannot set panel_bed for WHOLE_GENOME_SEQUENCING sample!")
            return None
        if panel_bed:
            return panel_bed.as_posix()
        if len(target_beds) == 1:
            target_bed = target_beds.pop()
            if not target_bed:
                raise BalsamicStartError(
                    f"Application type {application_types.pop()} requires a bed file to be analyzed!"
                )
            return Path(self.bed_path, target_bed).as_posix()

    def get_latest_pon_file(self, panel_bed: str) -> str | None:
        """Returns the latest PON cnn file associated to a specific capture bed"""

        if not panel_bed:
            raise BalsamicStartError("BALSAMIC PON workflow requires a panel bed to be specified")

        pon_list = Path(self.pon_path).glob(f"*{Path(panel_bed).stem}_{self.PON_file_suffix}")
        sorted_pon_files = sorted(
            pon_list,
            key=lambda file: int(file.stem.split("_v")[-1]),
            reverse=True,
        )

        return sorted_pon_files[0].as_posix() if sorted_pon_files else None

    def get_latest_raw_file_data(self, case_id: str, tags: list) -> dict | list:
        """Retrieves the data of the latest file associated to a specific case ID and a list of tags."""

        version: Version = self.housekeeper_api.last_version(bundle=case_id)
        raw_file: File = self.housekeeper_api.get_latest_file(
            bundle=case_id, version=version.id, tags=tags
        )

        if not raw_file:
            raise FileNotFoundError(
                f"No file associated to {tags} was found in housekeeper for {case_id}"
            )
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=Path(raw_file.full_path)
        )

    def get_latest_metadata(self, case_id: str) -> BalsamicAnalysis:
        """Return the latest metadata of a specific BALSAMIC case."""

        config_raw_data: dict = self.get_latest_raw_file_data(
            case_id=case_id, tags=BalsamicAnalysisTag.CONFIG
        )
        metrics_raw_data: list[dict] = self.get_latest_raw_file_data(
            case_id=case_id, tags=BalsamicAnalysisTag.QC_METRICS
        )

        if config_raw_data and metrics_raw_data:
            try:
                balsamic_analysis = self.parse_analysis(
                    config_raw=config_raw_data, qc_metrics_raw=metrics_raw_data
                )
                return balsamic_analysis
            except ValidationError as error:
                LOG.error(f"get_latest_metadata failed for '{case_id}', missing attribute: {error}")
                raise error
        else:
            LOG.error(f"Unable to retrieve the latest metadata for {case_id}")
            raise CgError

    def parse_analysis(
        self, config_raw: dict, qc_metrics_raw: list[dict], **kwargs
    ) -> BalsamicAnalysis:
        """Returns a formatted BalsamicAnalysis object"""

        sequencing_type = config_raw["analysis"]["sequencing_type"]
        qc_metrics = dict()

        for value in qc_metrics_raw:
            sample_metric = BalsamicMetricsBase(**value)
            try:
                qc_metrics[sample_metric.id].update(
                    {sample_metric.name.lower(): sample_metric.value}
                )
            except KeyError:
                qc_metrics[sample_metric.id] = {sample_metric.name.lower(): sample_metric.value}

        return BalsamicAnalysis(
            balsamic_config=config_raw,
            sample_metrics=self.cast_metrics_type(sequencing_type, qc_metrics),
        )

    @staticmethod
    def cast_metrics_type(
        sequencing_type: str, metrics: dict
    ) -> BalsamicTargetedQCMetrics | BalsamicWGSQCMetrics:
        """Cast metrics model type according to the sequencing type"""

        if metrics:
            for k, v in metrics.items():
                metrics[k] = (
                    BalsamicWGSQCMetrics(**v)
                    if sequencing_type == "wgs"
                    else BalsamicTargetedQCMetrics(**v)
                )

        return metrics

    @staticmethod
    def print_sample_params(case_id: str, sample_data: dict) -> None:
        """Outputs a table of samples to be displayed in log"""

        LOG.info(f"Case {case_id} has following BALSAMIC samples:")
        LOG.info(
            "{:<20} {:<20} {:<20} {:<20}".format(
                "SAMPLE ID", "TISSUE TYPE", "APPLICATION", "BED VERSION"
            )
        )
        for key in sample_data:
            LOG.info(
                "{:<20} {:<20} {:<20} {:<20}".format(
                    key,
                    str(sample_data[key]["tissue_type"]),
                    str(sample_data[key]["application_type"]),
                    str(sample_data[key]["target_bed"]),
                )
            )
        LOG.info("")

    def get_sample_params(self, case_id: str, panel_bed: str | None) -> dict:
        """Returns a dictionary of attributes for each sample in given family,
        where SAMPLE ID is used as key"""

        sample_data = {
            link_object.sample.internal_id: {
                "sex": link_object.sample.sex,
                "tissue_type": self.get_sample_type(link_object.sample).value,
                "application_type": self.get_analysis_type(link_object.sample),
                "target_bed": self.resolve_target_bed(panel_bed=panel_bed, link_object=link_object),
            }
            for link_object in self.status_db.get_case_by_internal_id(internal_id=case_id).links
        }

        self.print_sample_params(case_id=case_id, sample_data=sample_data)
        return sample_data

    def resolve_target_bed(self, panel_bed: str | None, link_object: CaseSample) -> str | None:
        if panel_bed:
            return panel_bed
        if self.get_analysis_type(link_object.sample) not in self.__BALSAMIC_BED_APPLICATIONS:
            return None
        return self.get_target_bed_from_lims(link_object.case.internal_id)

    def get_workflow_version(self, case_id: str) -> str:
        LOG.debug("Fetch workflow version")
        config_data: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON, file_path=self.get_case_config_path(case_id=case_id)
        )
        return config_data["analysis"]["BALSAMIC_version"]

    def report_deliver(self, case_id: str, dry_run: bool = False) -> None:
        """Execute BALSAMIC report deliver with given options"""

        command = ["report", "deliver"]
        options = build_command_from_dict(
            {
                "--sample-config": self.get_case_config_path(case_id=case_id),
            }
        )
        parameters = command + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def get_genome_build(self, case_id: str) -> str:
        """Returns the reference genome build version of a Balsamic analysis."""
        return GenomeVersion.HG19

    @staticmethod
    def get_variant_caller_version(var_caller_name: str, var_caller_versions: dict) -> str | None:
        """Return the version of a specific Balsamic bioinformatic tool."""
        for tool_name, versions in var_caller_versions.items():
            if tool_name in var_caller_name:
                return versions[0]
        return None

    def get_variant_callers(self, case_id: str) -> list[str]:
        """
        Return list of Balsamic variant-calling filters and their versions (if available) from the
        config.json file.
        """
        analysis_metadata: BalsamicAnalysis = self.get_latest_metadata(case_id)
        sequencing_type: str = analysis_metadata.balsamic_config.analysis.sequencing_type
        analysis_type: str = analysis_metadata.balsamic_config.analysis.analysis_type
        var_callers: dict[str, BalsamicVarCaller] = analysis_metadata.balsamic_config.vcf
        tool_versions: dict[str, list] = analysis_metadata.balsamic_config.bioinfo_tools_version
        analysis_var_callers = []
        for var_caller_name, var_caller_attributes in var_callers.items():
            if (
                sequencing_type in var_caller_attributes.sequencing_type
                and analysis_type in var_caller_attributes.analysis_type
            ):
                version: str = self.get_variant_caller_version(
                    var_caller_name=var_caller_name, var_caller_versions=tool_versions
                )
                analysis_var_callers.append(
                    f"{var_caller_name} (v{version})" if version else var_caller_name
                )
        return analysis_var_callers

    def get_pons(self, case_id: str) -> list[str]:
        """Return list of panel of normals used for analysis."""
        pons: list[str] = []
        analysis_metadata: BalsamicAnalysis = self.get_latest_metadata(case_id)
        if analysis_metadata.balsamic_config.panel:
            if pon_cnn := analysis_metadata.balsamic_config.panel.pon_cnn:
                pons.append(pon_cnn)
        return pons

    def get_data_analysis_type(self, case_id: str) -> str | None:
        """Return data analysis type carried out."""
        return self.get_bundle_deliverables_type(case_id)

    def is_analysis_normal_only(self, case_id: str) -> bool:
        """Return whether the analysis is normal only."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        if case.non_tumour_samples and not case.tumour_samples:
            return True
        return False

    def get_scout_upload_case_tags(self) -> dict:
        """Return Balsamic Scout upload case tags."""
        return BALSAMIC_CASE_TAGS
