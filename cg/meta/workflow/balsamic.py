"""Module for Balsamic Analysis API"""

import logging
from pathlib import Path
from typing import List, Optional, Union, Dict

from pydantic import ValidationError
from cg.constants import Pipeline
from cg.constants.indexes import ListIndexes
from cg.constants.observations import ObservationsFileWildcards
from cg.constants.sequencing import Variants
from cg.constants.subject import Gender
from cg.constants.constants import FileFormat, SampleType
from cg.constants.housekeeper_tags import BalsamicAnalysisTag
from cg.exc import BalsamicStartError, CgError
from cg.io.controller import ReadFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import BalsamicFastqHandler
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.metrics import (
    BalsamicTargetedQCMetrics,
    BalsamicWGSQCMetrics,
    BalsamicMetricsBase,
)
from cg.models.cg_config import CGConfig
from cg.store.models import ApplicationVersion, Family, FamilySample, Sample
from cg.utils import Process
from cg.utils.utils import get_string_from_list_by_pattern

LOG = logging.getLogger(__name__)


class BalsamicAnalysisAPI(AnalysisAPI):
    """Handles communication between BALSAMIC processes
    and the rest of CG infrastructure"""

    __BALSAMIC_APPLICATIONS = {"wgs", "wes", "tgs"}
    __BALSAMIC_BED_APPLICATIONS = {"wes", "tgs"}

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.BALSAMIC,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir = config.balsamic.root
        self.account = config.balsamic.slurm.account
        self.balsamic_cache = config.balsamic.balsamic_cache
        self.email = config.balsamic.slurm.mail_user
        self.qos = config.balsamic.slurm.qos
        self.bed_path = config.balsamic.bed_path
        self.pon_path = config.balsamic.pon_path
        self.loqusdb_path = config.balsamic.loqusdb_path
        self.swegen_path = config.balsamic.swegen_path

    @property
    def root(self) -> str:
        return self.root_dir

    @property
    def threshold_reads(self):
        return True

    @property
    def fastq_handler(self):
        return BalsamicFastqHandler

    @property
    def process(self):
        if not self._process:
            self._process = Process(self.config.balsamic.binary_path)
        return self._process

    @property
    def PON_file_suffix(self) -> str:
        """Panel of normals reference file suffix (<panel-bed>_<PON>_<version>.cnn)"""

        return "CNVkit_PON_reference_v*.cnn"

    def get_case_path(self, case_id: str) -> Path:
        """Returns a path where the Balsamic case for the case_id should be located"""
        return Path(self.root_dir, case_id)

    def get_cases_to_analyze(self) -> List[Family]:
        cases_query: List[Family] = self.status_db.cases_to_analyze(
            pipeline=self.pipeline, threshold=self.threshold_reads
        )
        cases_to_analyze = []
        for case_obj in cases_query:
            if case_obj.action == "analyze" or not case_obj.latest_analyzed:
                cases_to_analyze.append(case_obj)
            elif (
                self.trailblazer_api.get_latest_analysis_status(case_id=case_obj.internal_id)
                == "failed"
            ):
                cases_to_analyze.append(case_obj)
        return cases_to_analyze

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

    def get_trailblazer_config_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id, "analysis", "slurm_jobids.yaml")

    def get_bundle_deliverables_type(self, case_id: str) -> str:
        """Return the analysis type for a case

        Analysis types are any of ["tumor_wgs", "tumor_normal_wgs", "tumor_panel", "tumor_normal_panel"]
        """
        LOG.debug("Fetch analysis type for %s", case_id)
        number_of_samples: int = len(self.status_db.family(case_id).links)

        application_type: str = self.get_application_type(
            self.status_db.family(case_id).links[0].sample
        )
        sample_type = "tumor"
        if number_of_samples == 2:
            sample_type = "tumor_normal"
        if application_type != "wgs":
            application_type = "panel"
        analysis_type = "_".join([sample_type, application_type])
        LOG.info("Found analysis type %s", analysis_type)
        return analysis_type

    def get_sample_fastq_destination_dir(self, case_obj: Family, sample_obj: Sample = None) -> Path:
        return self.get_case_path(case_obj.internal_id) / "fastq"

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        case_obj = self.status_db.family(case_id)
        for link in case_obj.links:
            self.link_fastq_files_for_sample(
                case_obj=case_obj, sample_obj=link.sample, concatenate=True
            )

    def get_concatenated_fastq_path(self, link_object: FamilySample) -> Path:
        """Returns path to the concatenated FASTQ file of a sample"""
        file_collection: List[dict] = self.gather_file_metadata_for_sample(link_object.sample)
        fastq_data = file_collection[0]
        linked_fastq_name = self.fastq_handler.create_fastq_name(
            lane=fastq_data["lane"],
            flowcell=fastq_data["flowcell"],
            sample=link_object.sample.internal_id,
            read=fastq_data["read"],
            undetermined=fastq_data["undetermined"],
        )
        concatenated_fastq_name: str = self.fastq_handler.get_concatenated_name(linked_fastq_name)
        return Path(
            self.root_dir,
            link_object.family.internal_id,
            "fastq",
            concatenated_fastq_name,
        )

    @staticmethod
    def get_gender(sample_obj: Sample) -> str:
        """Returns the gender associated to a specific sample"""

        return sample_obj.sex

    @staticmethod
    def get_sample_type(sample_obj: Sample) -> SampleType:
        """Return the tissue type of the sample."""
        if sample_obj.is_tumour:
            return SampleType.TUMOR
        return SampleType.NORMAL

    def get_derived_bed(self, panel_bed: str) -> Optional[Path]:
        """Returns the verified capture kit path or extracts the derived panel bed"""

        if panel_bed:
            if Path(panel_bed).is_file():
                panel_bed = Path(panel_bed)
            else:
                derived_panel_bed = Path(
                    self.bed_path,
                    self.status_db.bed_version(panel_bed).filename,
                )
                if not derived_panel_bed.is_file():
                    raise BalsamicStartError(
                        f"{panel_bed} or {derived_panel_bed} are not valid paths to a BED file. "
                        f"Please provide absolute path to desired BED file or a valid bed shortname!"
                    )
                panel_bed = derived_panel_bed

        return panel_bed

    def get_verified_bed(self, panel_bed: str, sample_data: dict) -> Optional[str]:
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

        panel_bed = self.get_derived_bed(panel_bed)
        application_types = {v["application_type"].lower() for k, v in sample_data.items()}
        target_beds = {v["target_bed"] for k, v in sample_data.items()}

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

    def get_verified_pon(self, panel_bed: str, pon_cnn: str) -> Optional[str]:
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

    def get_latest_pon_file(self, panel_bed: str) -> Optional[str]:
        """Returns the latest PON cnn file associated to a specific capture bed"""

        if not panel_bed:
            raise BalsamicStartError("BALSAMIC PON workflow requires a panel bed to be specified")

        pon_list = Path(self.pon_path).glob(f"*{Path(panel_bed).stem}_{self.PON_file_suffix}")
        sorted_pon_files = sorted(
            pon_list,
            key=lambda file: int(file.stem.split("_v")[ListIndexes.LAST.value]),
            reverse=True,
        )

        return sorted_pon_files[0].as_posix() if sorted_pon_files else None

    @staticmethod
    def get_verified_gender(sample_data: dict) -> Union[Gender.FEMALE, Gender.MALE]:
        """Takes a dict with samples and attributes, and returns a verified case gender provided by the customer"""

        gender = next(iter(sample_data.values()))["gender"]

        if all(val["gender"] == gender for val in sample_data.values()) and gender in set(
            value for value in Gender
        ):
            if gender not in [Gender.FEMALE, Gender.MALE]:
                LOG.warning(
                    f"The provided gender is unknown, setting {Gender.FEMALE.value} as the default"
                )
                gender = Gender.FEMALE.value

            return gender
        else:
            LOG.error(f"Unable to retrieve a valid gender from samples: {sample_data.keys()}")
            raise BalsamicStartError

    def get_verified_samples(
        self, case_id: str, sample_data: dict, force_normal: bool
    ) -> Dict[str, str]:
        """Return a verified tumor and normal sample dictionary."""

        tumor_samples: List[Sample] = self.status_db.get_samples_by_type(
            case_id=case_id, sample_type=SampleType.TUMOR
        )
        normal_samples: List[Sample] = self.status_db.get_samples_by_type(
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
        tumor_sample_path: str = (
            sample_data.get(tumor_sample_id).get("concatenated_path") if tumor_sample_id else None
        )
        normal_sample_path: str = (
            sample_data.get(normal_sample_id).get("concatenated_path") if normal_sample_id else None
        )
        if normal_sample_id and not tumor_sample_id:
            if force_normal:
                LOG.warning(
                    f"Only a normal sample was found for case {case_id}. "
                    f"Balsamic analysis will treat it as a tumor sample."
                )
                tumor_sample_id, tumor_sample_path = normal_sample_id, normal_sample_path
                normal_sample_id, normal_sample_path = None, None
            else:
                LOG.error(
                    f"Case {case_id} only has a normal sample. Use the --force-normal flag to treat it as a tumor."
                )
                raise BalsamicStartError

        return {
            "tumor_sample_name": tumor_sample_id,
            "tumor": tumor_sample_path,
            "normal_sample_name": normal_sample_id,
            "normal": normal_sample_path,
        }

    def get_latest_raw_file_data(self, case_id: str, tags: list) -> Union[dict, list]:
        """Retrieves the data of the latest file associated to a specific case ID and a list of tags"""

        version = self.housekeeper_api.last_version(bundle=case_id)
        raw_file = self.housekeeper_api.get_files(
            bundle=case_id, version=version.id, tags=tags
        ).first()

        if not raw_file:
            raise FileNotFoundError(
                f"No file associated to {tags} was found in housekeeper for {case_id}"
            )
        return ReadFile.get_content_from_file(
            file_format=FileFormat.YAML, file_path=Path(raw_file.full_path)
        )

    def get_latest_metadata(self, case_id: str) -> BalsamicAnalysis:
        """Get the latest metadata of a specific BALSAMIC case"""

        config_raw_data = self.get_latest_raw_file_data(case_id, [BalsamicAnalysisTag.CONFIG])
        metrics_raw_data = self.get_latest_raw_file_data(case_id, [BalsamicAnalysisTag.QC_METRICS])

        if config_raw_data and metrics_raw_data:
            try:
                balsamic_analysis = self.parse_analysis(
                    config_raw=config_raw_data, qc_metrics_raw=metrics_raw_data
                )
                return balsamic_analysis
            except ValidationError as error:
                LOG.error(
                    "get_latest_metadata failed for '%s', missing attribute: %s",
                    case_id,
                    error,
                )
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
    ) -> Union[BalsamicTargetedQCMetrics, BalsamicWGSQCMetrics]:
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
    def get_latest_file_by_pattern(directory: Path, pattern: str) -> Optional[str]:
        """Returns the latest file (<file_name>-<date>-.vcf.gz) matching a pattern from a specific directory."""
        available_files: iter = sorted(
            Path(directory).glob(f"*{pattern}*.vcf.gz"),
            key=lambda file: file.stem.split("-"),
            reverse=True,
        )
        return str(available_files[0]) if available_files else None

    def get_parsed_observation_file_paths(self, observations: List[str]) -> dict:
        """Returns a verified {option: path} observations dictionary."""
        verified_observations: Dict[str, str] = {}
        for wildcard in list(ObservationsFileWildcards):
            file_path: str = get_string_from_list_by_pattern(observations, wildcard)
            verified_observations.update(
                {
                    wildcard: file_path
                    if file_path
                    else self.get_latest_file_by_pattern(
                        directory=self.loqusdb_path, pattern=wildcard
                    )
                }
            )

        return verified_observations

    def get_swegen_verified_path(self, variants: Variants) -> Optional[str]:
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
        force_normal: bool = False,
        observations: List[str] = None,
        gender: Optional[str] = None,
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

        config_case: Dict[str, str] = {
            "case_id": case_id,
            "analysis_workflow": self.pipeline,
            "genome_version": genome_version,
            "gender": gender or self.get_verified_gender(sample_data=sample_data),
            "panel_bed": verified_panel_bed,
            "pon_cnn": verified_pon,
            "swegen_snv": self.get_swegen_verified_path(Variants.SNV),
            "swegen_sv": self.get_swegen_verified_path(Variants.SV),
        }
        config_case.update(
            self.get_verified_samples(
                case_id=case_id, sample_data=sample_data, force_normal=force_normal
            )
        )
        config_case.update(self.get_parsed_observation_file_paths(observations))

        return config_case

    def build_sample_id_map_string(self, case_id: str) -> str:
        """Creates sample info string for balsamic with format lims_id:tumor/normal:customer_sample_id"""

        tumor_sample_lims_id = self.get_tumor_sample_name(case_id=case_id)
        tumor_string = f"{tumor_sample_lims_id}:tumor:{self.status_db.sample(internal_id=tumor_sample_lims_id).name}"
        normal_sample_lims_id = self.get_normal_sample_name(case_id=case_id)
        if normal_sample_lims_id:
            normal_string = f"{normal_sample_lims_id}:normal:{self.status_db.sample(internal_id=normal_sample_lims_id).name}"
            return ",".join([tumor_string, normal_string])
        return tumor_string

    def build_case_id_map_string(self, case_id: str) -> Optional[str]:
        """Creates case info string for balsamic with format panel_shortname:case_name:application_tag"""

        case_obj: Family = self.status_db.family(case_id)
        sample_obj: Sample = case_obj.links[0].sample
        if sample_obj.from_sample:
            sample_obj: Sample = self.status_db.sample(sample_obj.from_sample)
        capture_kit = self.lims_api.capture_kit(sample_obj.internal_id)
        if capture_kit:
            panel_shortname = self.status_db.bed_version(capture_kit).shortname
        elif self.get_application_type(case_obj.links[0].sample) == "wgs":
            panel_shortname = "Whole_Genome"
        else:
            return
        application_tag = (
            self.status_db.query(ApplicationVersion)
            .filter(ApplicationVersion.id == case_obj.links[0].sample.application_version_id)
            .first()
            .application.tag
        )
        return f"{panel_shortname}:{case_obj.name}:{application_tag}"

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

    def get_sample_params(self, case_id: str, panel_bed: Optional[str]) -> dict:
        """Returns a dictionary of attributes for each sample in given family,
        where SAMPLE ID is used as key"""

        sample_data = {
            link_object.sample.internal_id: {
                "gender": self.get_gender(link_object.sample),
                "tissue_type": self.get_sample_type(link_object.sample).value,
                "concatenated_path": self.get_concatenated_fastq_path(link_object).as_posix(),
                "application_type": self.get_application_type(link_object.sample),
                "target_bed": self.resolve_target_bed(panel_bed=panel_bed, link_object=link_object),
            }
            for link_object in self.status_db.family(case_id).links
        }

        self.print_sample_params(case_id=case_id, sample_data=sample_data)
        return sample_data

    def get_case_application_type(self, case_id: str) -> str:
        application_types = {
            self.get_application_type(link_object.sample)
            for link_object in self.status_db.family(case_id).links
        }

        if application_types:
            return application_types.pop().lower()

    def resolve_target_bed(
        self, panel_bed: Optional[str], link_object: FamilySample
    ) -> Optional[str]:
        if panel_bed:
            return panel_bed
        if self.get_application_type(link_object.sample) not in self.__BALSAMIC_BED_APPLICATIONS:
            return None
        return self.get_target_bed_from_lims(link_object.family.internal_id)

    def get_pipeline_version(self, case_id: str) -> str:
        LOG.debug("Fetch pipeline version")
        config_data: dict = ReadFile.get_content_from_file(
            file_format=FileFormat.JSON, file_path=self.get_case_config_path(case_id=case_id)
        )
        return config_data["analysis"]["BALSAMIC_version"]

    def family_has_correct_number_tumor_normal_samples(self, case_id: str) -> bool:
        """Evaluates if a case has exactly one tumor and up to one normal sample in ClinicalDB.
        This check is only applied to filter jobs which start automatically"""
        query = (
            self.status_db.query(Sample)
            .join(Family.links, FamilySample.sample)
            .filter(Family.internal_id == case_id)
            .filter(Family.data_analysis == self.pipeline)
        )
        return all(
            [
                len(query.filter(Sample.is_tumour == False).all()) <= 1,
                len(query.filter(Sample.is_tumour == True).all()) == 1,
            ]
        )

    def get_valid_cases_to_analyze(self) -> list:
        """Retrieve a list of balsamic cases without analysis,
        where samples have enough reads to be analyzed"""

        return [
            case_object.internal_id
            for case_object in self.get_cases_to_analyze()
            if self.family_has_correct_number_tumor_normal_samples(case_object.internal_id)
        ]

    @staticmethod
    def __build_command_str(options: dict) -> List[str]:
        formatted_options = []
        for key, val in options.items():
            if val:
                formatted_options.append(str(key))
                formatted_options.append(str(val))
        return formatted_options

    def config_case(
        self,
        case_id: str,
        gender: str,
        genome_version: str,
        panel_bed: str,
        pon_cnn: str,
        observations: List[str],
        force_normal: bool,
        dry_run: bool = False,
    ) -> None:
        """Create config file for BALSAMIC analysis"""
        arguments = self.get_verified_config_case_arguments(
            case_id=case_id,
            gender=gender,
            genome_version=genome_version,
            panel_bed=panel_bed,
            pon_cnn=pon_cnn,
            observations=observations,
            force_normal=force_normal,
        )
        command = ["config", "case"]
        options = self.__build_command_str(
            {
                "--analysis-dir": self.root_dir,
                "--balsamic-cache": self.balsamic_cache,
                "--case-id": arguments.get("case_id"),
                "--gender": arguments.get("gender"),
                "--analysis-workflow": arguments.get("analysis_workflow"),
                "--genome-version": arguments.get("genome_version"),
                "--normal": arguments.get(SampleType.NORMAL.value),
                "--tumor": arguments.get(SampleType.TUMOR.value),
                "--panel-bed": arguments.get("panel_bed"),
                "--pon-cnn": arguments.get("pon_cnn"),
                "--umi-trim-length": arguments.get("umi_trim_length"),
                "--tumor-sample-name": arguments.get("tumor_sample_name"),
                "--normal-sample-name": arguments.get("normal_sample_name"),
                "--swegen-snv": arguments.get("swegen_snv"),
                "--swegen-sv": arguments.get("swegen_sv"),
                "--clinical-snv-observations": arguments.get("clinical_snv"),
                "--clinical-sv-observations": arguments.get("clinical_sv"),
                "--cancer-all-snv-observations": arguments.get("cancer_all_snv"),
                "--cancer-somatic-snv-observations": arguments.get("cancer_somatic_snv"),
                "--cancer-somatic-sv-observations": arguments.get("cancer_somatic_sv"),
            }
        )
        parameters = command + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def run_analysis(
        self,
        case_id: str,
        run_analysis: bool = True,
        slurm_quality_of_service: Optional[str] = None,
        dry_run: bool = False,
    ) -> None:
        """Execute BALSAMIC run analysis with given options"""

        command = ["run", "analysis"]
        run_analysis = ["--run-analysis"] if run_analysis else []
        benchmark = ["--benchmark"]
        options = self.__build_command_str(
            {
                "--account": self.account,
                "--mail-user": self.email,
                "--qos": slurm_quality_of_service or self.get_slurm_qos_for_case(case_id=case_id),
                "--sample-config": self.get_case_config_path(case_id=case_id),
            }
        )
        parameters = command + options + run_analysis + benchmark
        self.process.run_command(parameters=parameters, dry_run=dry_run)

    def report_deliver(self, case_id: str, dry_run: bool = False) -> None:
        """Execute BALSAMIC report deliver with given options"""

        command = ["report", "deliver"]
        options = self.__build_command_str(
            {
                "--sample-config": self.get_case_config_path(case_id=case_id),
            }
        )
        parameters = command + options
        self.process.run_command(parameters=parameters, dry_run=dry_run)
