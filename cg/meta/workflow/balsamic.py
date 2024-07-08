"""Module for Balsamic Analysis API."""

import logging
from pathlib import Path

from housekeeper.store.models import File, Version
from pydantic.v1 import EmailStr, ValidationError

from cg.constants import Workflow
from cg.constants.constants import FileFormat, SampleType
from cg.constants.housekeeper_tags import BalsamicAnalysisTag
from cg.constants.observations import ObservationsFileWildcards
from cg.constants.priority import SlurmQos
from cg.constants.sequencing import Variants
from cg.constants.subject import Sex
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
from cg.utils.utils import build_command_from_dict, get_string_from_list_by_pattern

LOG = logging.getLogger(__name__)

MAX_CASES_TO_START_IN_50_MINUTES = 21


class BalsamicAnalysisAPI(AnalysisAPI):
    """Handles communication between BALSAMIC processes
    and the rest of CG infrastructure"""

    __BALSAMIC_APPLICATIONS = {"wgs", "wes", "tgs"}
    __BALSAMIC_BED_APPLICATIONS = {"wes", "tgs"}

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.BALSAMIC,
    ):
        super().__init__(workflow=workflow, config=config)
        self.account: str = config.balsamic.slurm.account
        self.binary_path: str = config.balsamic.binary_path
        self.balsamic_cache: str = config.balsamic.balsamic_cache
        self.conda_binary: str = config.balsamic.conda_binary
        self.conda_env: str = config.balsamic.conda_env
        self.bed_path: str = config.balsamic.bed_path
        self.cadd_path: str = config.balsamic.cadd_path
        self.genome_interval_path: str = config.balsamic.genome_interval_path
        self.gnomad_af5_path: str = config.balsamic.gnomad_af5_path
        self.gens_coverage_female_path: str = config.balsamic.gens_coverage_female_path
        self.gens_coverage_male_path: str = config.balsamic.gens_coverage_male_path
        self.email: EmailStr = config.balsamic.slurm.mail_user
        self.loqusdb_path: str = config.balsamic.loqusdb_path
        self.pon_path: str = config.balsamic.pon_path
        self.qos: SlurmQos = config.balsamic.slurm.qos
        self.root_dir: str = config.balsamic.root
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

    def get_cases_ready_for_analysis(self) -> list[Case]:
        """Returns a list of cases that are ready for analysis."""
        cases_to_analyse: list[Case] = self.get_cases_to_analyse()
        cases_ready_for_analysis: list[Case] = [
            case for case in cases_to_analyse if self.is_case_ready_for_analysis(case)
        ]
        return cases_ready_for_analysis[:MAX_CASES_TO_START_IN_50_MINUTES]

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

        application_type: str = self.get_application_type(
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
            self.status_db.get_bed_version_by_short_name(
                bed_version_short_name=panel_bed.as_posix()
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
                raise BalsamicStartError("Cannot set panel_bed for WGS sample!")
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

    def get_verified_pon(self, panel_bed: str, pon_cnn: str) -> str | None:
        """Returns the validated PON or extracts the latest one available if it is not provided

        Raises BalsamicStartError:
            When there is a missmatch between the PON and the panel bed file names
        """

        if pon_cnn:
            latest_pon = pon_cnn
            if Path(panel_bed).stem not in Path(latest_pon).stem:
                raise BalsamicStartError(
                    f"The specified PON reference file {latest_pon} does not match the panel bed {panel_bed}"
                )
        else:
            latest_pon = self.get_latest_pon_file(panel_bed)
            if latest_pon:
                LOG.info(
                    f"The following PON reference file will be used for the analysis: {latest_pon}"
                )

        return latest_pon

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

    @staticmethod
    def get_verified_sex(sample_data: dict) -> Sex:
        """Takes a dict with samples and attributes, and returns a verified case sex provided by the customer."""
        sex: Sex = next(iter(sample_data.values()))["sex"]
        if all(val["sex"] == sex for val in sample_data.values()) and sex in set(
            value for value in Sex
        ):
            if sex not in [Sex.FEMALE, Sex.MALE]:
                LOG.warning(f"The provided sex is unknown, setting {Sex.FEMALE} as the default")
                sex = Sex.FEMALE

            return sex
        else:
            LOG.error(f"Unable to retrieve a valid sex from samples: {sample_data.keys()}")
            raise BalsamicStartError

    def get_verified_samples(self, case_id: str) -> dict[str, str]:
        """Return a verified tumor and normal sample dictionary."""
        tumor_samples: list[Sample] = self.status_db.get_samples_by_type(
            case_id=case_id, sample_type=SampleType.TUMOR
        )
        normal_samples: list[Sample] = self.status_db.get_samples_by_type(
            case_id=case_id, sample_type=SampleType.NORMAL
        )
        if (
            not tumor_samples
            and not normal_samples
            or len(tumor_samples) > 1
            or len(normal_samples) > 1
        ):
            LOG.error(f"Case {case_id} has an invalid number of samples")
            raise BalsamicStartError

        tumor_sample_id: str = tumor_samples[0].internal_id if tumor_samples else None
        normal_sample_id: str = normal_samples[0].internal_id if normal_samples else None
        if normal_sample_id and not tumor_sample_id:
            LOG.warning(
                f"Only a normal sample was found for case {case_id}. "
                f"Balsamic analysis will treat it as a tumor sample."
            )
            tumor_sample_id, normal_sample_id = normal_sample_id, None
        return {"tumor_sample_name": tumor_sample_id, "normal_sample_name": normal_sample_id}

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

        config_raw_data = self.get_latest_raw_file_data(case_id, BalsamicAnalysisTag.CONFIG)
        metrics_raw_data = self.get_latest_raw_file_data(case_id, BalsamicAnalysisTag.QC_METRICS)

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

    def parse_analysis(self, config_raw: dict, qc_metrics_raw: dict, **kwargs) -> BalsamicAnalysis:
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
            config=config_raw,
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
    def get_latest_file_by_pattern(directory: Path, pattern: str) -> str | None:
        """Returns the latest file (<file_name>-<date>-.vcf.gz) matching a pattern from a specific directory."""
        available_files: iter = sorted(
            Path(directory).glob(f"*{pattern}*.vcf.gz"),
            key=lambda file: file.stem.split("-"),
            reverse=True,
        )
        return str(available_files[0]) if available_files else None

    def get_parsed_observation_file_paths(self, observations: list[str]) -> dict:
        """Returns a verified {option: path} observations dictionary."""
        verified_observations: dict[str, str] = {}
        for wildcard in list(ObservationsFileWildcards):
            file_path: str = get_string_from_list_by_pattern(observations, wildcard)
            verified_observations.update(
                {
                    wildcard: (
                        file_path
                        if file_path
                        else self.get_latest_file_by_pattern(
                            directory=self.loqusdb_path, pattern=wildcard
                        )
                    )
                }
            )

        return verified_observations

    def get_verified_gens_file_paths(self, sex: Sex) -> dict[str, str] | None:
        """Return a list of file path arguments for Gens."""
        return {
            "genome_interval": self.genome_interval_path,
            "gnomad_min_af5": self.gnomad_af5_path,
            "gens_coverage_pon": (
                self.gens_coverage_female_path
                if sex == Sex.FEMALE
                else self.gens_coverage_male_path
            ),
        }

    def get_swegen_verified_path(self, variants: Variants) -> str | None:
        """Return verified SweGen path."""
        swegen_file: str = self.get_latest_file_by_pattern(
            directory=self.swegen_path, pattern=variants
        )
        return swegen_file

    def get_verified_config_case_arguments(
        self,
        case_id: str,
        genome_version: str,
        panel_bed: str,
        pon_cnn: str,
        observations: list[str] = None,
        sex: str | None = None,
    ) -> dict:
        """Takes a dictionary with per-sample parameters,
        validates them, and transforms into command line arguments
        Raises BalsamicStartError:
            When no samples associated with case are marked for BALSAMIC analysis
        """
        sample_data = self.get_sample_params(case_id=case_id, panel_bed=panel_bed)
        if len(sample_data) == 0:
            raise BalsamicStartError(f"{case_id} has no samples tagged for BALSAMIC analysis!")

        verified_panel_bed = self.get_verified_bed(panel_bed=panel_bed, sample_data=sample_data)
        verified_pon = (
            self.get_verified_pon(pon_cnn=pon_cnn, panel_bed=verified_panel_bed)
            if verified_panel_bed
            else None
        )
        verified_sex: Sex = sex or self.get_verified_sex(sample_data=sample_data)

        verified_exome_argument: bool = self.has_case_only_exome_samples(case_id=case_id)

        config_case: dict[str, str] = {
            "case_id": case_id,
            "analysis_workflow": self.workflow,
            "genome_version": genome_version,
            "sex": verified_sex,
            "panel_bed": verified_panel_bed,
            "pon_cnn": verified_pon,
            "swegen_snv": self.get_swegen_verified_path(Variants.SNV),
            "swegen_sv": self.get_swegen_verified_path(Variants.SV),
            "exome": verified_exome_argument,
        }

        config_case.update(self.get_verified_samples(case_id=case_id))
        config_case.update(self.get_parsed_observation_file_paths(observations))
        (
            config_case.update(self.get_verified_gens_file_paths(sex=verified_sex))
            if not verified_panel_bed
            else None
        )

        return config_case

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
                "application_type": self.get_application_type(link_object.sample),
                "target_bed": self.resolve_target_bed(panel_bed=panel_bed, link_object=link_object),
            }
            for link_object in self.status_db.get_case_by_internal_id(internal_id=case_id).links
        }

        self.print_sample_params(case_id=case_id, sample_data=sample_data)
        return sample_data

    def resolve_target_bed(self, panel_bed: str | None, link_object: CaseSample) -> str | None:
        if panel_bed:
            return panel_bed
        if self.get_application_type(link_object.sample) not in self.__BALSAMIC_BED_APPLICATIONS:
            return None
        return self.get_target_bed_from_lims(link_object.case.internal_id)

    def get_workflow_version(self, case_id: str) -> str:
        LOG.debug("Fetch workflow version")
        config_data: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON, file_path=self.get_case_config_path(case_id=case_id)
        )
        return config_data["analysis"]["BALSAMIC_version"]

    def config_case(
        self,
        case_id: str,
        gender: str,
        genome_version: str,
        panel_bed: str,
        pon_cnn: str,
        observations: list[str],
        cache_version: str,
        dry_run: bool = False,
    ) -> None:
        """Create config file for BALSAMIC analysis"""
        arguments = self.get_verified_config_case_arguments(
            case_id=case_id,
            sex=gender,
            genome_version=genome_version,
            panel_bed=panel_bed,
            pon_cnn=pon_cnn,
            observations=observations,
        )
        command = ["config", "case"]
        options = build_command_from_dict(
            {
                "--analysis-dir": self.root_dir,
                "--analysis-workflow": arguments.get("analysis_workflow"),
                "--balsamic-cache": self.balsamic_cache,
                "--cache-version": cache_version,
                "--cadd-annotations": self.cadd_path,
                "--cancer-germline-snv-observations": arguments.get("cancer_germline_snv"),
                "--cancer-germline-sv-observations": arguments.get("cancer_germline_sv"),
                "--cancer-somatic-snv-observations": arguments.get("cancer_somatic_snv"),
                "--cancer-somatic-sv-observations": arguments.get("cancer_somatic_sv"),
                "--case-id": arguments.get("case_id"),
                "--clinical-snv-observations": arguments.get("clinical_snv"),
                "--clinical-sv-observations": arguments.get("clinical_sv"),
                "--fastq-path": self.get_sample_fastq_destination_dir(
                    self.status_db.get_case_by_internal_id(case_id)
                ),
                "--gender": arguments.get("sex"),
                "--genome-interval": arguments.get("genome_interval"),
                "--genome-version": arguments.get("genome_version"),
                "--gens-coverage-pon": arguments.get("gens_coverage_pon"),
                "--gnomad-min-af5": arguments.get("gnomad_min_af5"),
                "--normal-sample-name": arguments.get("normal_sample_name"),
                "--panel-bed": arguments.get("panel_bed"),
                "--exome": arguments.get("exome"),
                "--pon-cnn": arguments.get("pon_cnn"),
                "--swegen-snv": arguments.get("swegen_snv"),
                "--swegen-sv": arguments.get("swegen_sv"),
                "--tumor-sample-name": arguments.get("tumor_sample_name"),
                "--umi-trim-length": arguments.get("umi_trim_length"),
            },
            exclude_true=True,
        )
        parameters = command + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def run_analysis(
        self,
        case_id: str,
        cluster_config: Path | None = None,
        slurm_quality_of_service: str | None = None,
        dry_run: bool = False,
    ) -> None:
        """Execute BALSAMIC run analysis with given options"""

        command = ["run", "analysis"]
        run_analysis = ["--run-analysis"] if not dry_run else []
        benchmark = ["--benchmark"]
        options = build_command_from_dict(
            {
                "--account": self.account,
                "--mail-user": self.email,
                "--qos": slurm_quality_of_service or self.get_slurm_qos_for_case(case_id=case_id),
                "--sample-config": self.get_case_config_path(case_id=case_id),
                "--cluster-config": cluster_config,
            }
        )
        parameters = command + options + run_analysis + benchmark
        self.process.run_command(parameters=parameters, dry_run=dry_run)

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
        analysis_metadata: BalsamicAnalysis = self.get_latest_metadata(case_id)
        return analysis_metadata.config.reference.reference_genome_version

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
        sequencing_type: str = analysis_metadata.config.analysis.sequencing_type
        analysis_type: str = analysis_metadata.config.analysis.analysis_type
        var_callers: dict[str, BalsamicVarCaller] = analysis_metadata.config.vcf
        tool_versions: dict[str, list] = analysis_metadata.config.bioinfo_tools_version
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
        if analysis_metadata.config.panel:
            if pon_cnn := analysis_metadata.config.panel.pon_cnn:
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
