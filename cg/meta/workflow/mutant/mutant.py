import logging
import shutil
from pathlib import Path
from cg.constants import SequencingFileTag, Workflow
from cg.constants.constants import FileFormat, MutantQC
from cg.constants.tb import AnalysisStatus
from cg.exc import CgError
from cg.io.controller import WriteFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MutantFastqHandler
from cg.services.sequencing_qc_service.sequencing_qc_service import SequencingQCService
from cg.meta.workflow.mutant.quality_controller.models import MutantQualityResult
from cg.meta.workflow.mutant.quality_controller.quality_controller import MutantQualityController
from cg.models.cg_config import CGConfig
from cg.models.workflow.mutant import MutantSampleConfig
from cg.store.models import Application, Case, Sample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class MutantAnalysisAPI(AnalysisAPI):
    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.MUTANT,
    ):
        super().__init__(workflow=workflow, config=config)
        self.root_dir = config.mutant.root
        self.quality_checker = MutantQualityController(
            status_db=config.status_db, lims=config.lims_api
        )

    @property
    def conda_binary(self) -> str:
        return self.config.mutant.conda_binary

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=self.config.mutant.binary_path,
                conda_binary=f"{self.conda_binary}" if self.conda_binary else None,
                environment=self.config.mutant.conda_env,
            )
        return self._process

    @property
    def fastq_handler(self):
        return MutantFastqHandler

    def get_case_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id)

    def get_case_output_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "results")

    def get_case_results_file_path(self, case: Case) -> Path:
        case_output_path: Path = self.get_case_output_path(case.internal_id)
        return Path(case_output_path, f"sars-cov-2_{case.latest_ticket}_results.csv")

    def get_case_fastq_dir(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "fastq")

    def get_case_qc_report_path(self, case_id: str) -> Path:
        case_path: Path = self.get_case_path(case_id=case_id)
        return Path(case_path, MutantQC.QUALITY_REPORT_FILE_NAME)

    def get_job_ids_path(self, case_id: str) -> Path:
        return Path(self.get_case_output_path(case_id=case_id), "trailblazer_config.yaml")

    def _is_nanopore(self, application: Application) -> bool:
        return application.tag[3:6] == "ONT"

    def get_sample_fastq_destination_dir(self, case: Case, sample: Sample) -> Path:
        """Return the path to the FASTQ destination directory."""
        application: str = sample.application_version.application
        if self._is_nanopore(application=application):
            return Path(self.get_case_path(case_id=case.internal_id), FileFormat.FASTQ, sample.name)
        return Path(self.get_case_path(case_id=case.internal_id), FileFormat.FASTQ)

    def get_case_config_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "case_config.json")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        return Path(self.get_case_output_path(case_id=case_id), f"{case_id}_deliverables.yaml")

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        case_obj = self.status_db.get_case_by_internal_id(internal_id=case_id)
        samples: list[Sample] = [link.sample for link in case_obj.links]
        for sample_obj in samples:
            application = sample_obj.application_version.application
            if self._is_nanopore(application):
                self.link_nanopore_fastq_for_sample(
                    case=case_obj, sample=sample_obj, concatenate=True
                )
                continue
            if not SequencingQCService.sample_pass_sequencing_qc(sample_obj):
                LOG.info(f"Sample {sample_obj.internal_id} read count below threshold, skipping!")
                continue
            self.link_fastq_files_for_sample(case=case_obj, sample=sample_obj, concatenate=True)

    def get_sample_parameters(self, sample_obj: Sample, sequencing_qc: bool) -> MutantSampleConfig:
        return MutantSampleConfig(
            CG_ID_sample=sample_obj.internal_id,
            case_ID=sample_obj.links[0].case.internal_id,
            Customer_ID_sample=sample_obj.name,
            customer_id=sample_obj.customer.internal_id,
            sequencing_qc_pass=sequencing_qc,
            CG_ID_project=sample_obj.links[0].case.name,
            Customer_ID_project=sample_obj.original_ticket,
            application_tag=sample_obj.application_version.application.tag,
            method_libprep=str(self.lims_api.get_prep_method(lims_id=sample_obj.internal_id)),
            method_sequencing=str(
                self.lims_api.get_sequencing_method(lims_id=sample_obj.internal_id)
            ),
            date_arrival=str(sample_obj.received_at),
            date_libprep=str(sample_obj.prepared_at),
            date_sequencing=str(sample_obj.last_sequenced_at),
            selection_criteria=self.lims_api.get_sample_attribute(
                lims_id=sample_obj.internal_id, key="selection_criteria"
            ),
            priority=self.lims_api.get_sample_attribute(
                lims_id=sample_obj.internal_id, key="priority"
            ),
            region_code=self.lims_api.get_sample_attribute(
                lims_id=sample_obj.internal_id, key="region_code"
            ),
            lab_code=self.lims_api.get_sample_attribute(
                lims_id=sample_obj.internal_id, key="lab_code"
            ),
            primer=self.lims_api.get_sample_attribute(lims_id=sample_obj.internal_id, key="primer"),
        )

    def create_case_config(self, case_id: str, dry_run: bool) -> None:
        case_obj = self.status_db.get_case_by_internal_id(internal_id=case_id)
        samples: list[Sample] = [link.sample for link in case_obj.links]
        case_config_list: list[dict] = []
        for sample in samples:
            sample_passed_sequencing_qc: bool = SequencingQCService.sample_pass_sequencing_qc(
                sample=sample
            )
            case_config_list.append(
                self.get_sample_parameters(
                    sample_obj=sample, sequencing_qc=sample_passed_sequencing_qc
                ).model_dump()
            )
        config_path: Path = self.get_case_config_path(case_id=case_id)
        if dry_run:
            LOG.info(
                f"Dry-run, would have created config at path {config_path.as_posix()}, with content:"
            )
            LOG.info(case_config_list)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        WriteFile.write_file_from_content(
            content=case_config_list, file_format=FileFormat.JSON, file_path=config_path
        )
        LOG.info(f"Saved config to {config_path.as_posix()}")

    def get_lims_naming_metadata(self, sample: Sample) -> str | None:
        region_code = self.lims_api.get_sample_attribute(
            lims_id=sample.internal_id, key="region_code"
        ).split(" ")[0]
        lab_code = self.lims_api.get_sample_attribute(
            lims_id=sample.internal_id, key="lab_code"
        ).split(" ")[0]

        return f"{region_code}_{lab_code}_{sample.name}"

    def run_analysis(self, case_id: str, dry_run: bool, config_artic: str = None) -> None:
        if self.get_case_output_path(case_id=case_id).exists():
            LOG.info("Found old output files, directory will be cleaned!")
            shutil.rmtree(self.get_case_output_path(case_id=case_id), ignore_errors=True)

        if config_artic:
            self.process.run_command(
                [
                    "analyse",
                    "sarscov2",
                    "--config_case",
                    self.get_case_config_path(case_id=case_id).as_posix(),
                    "--config_artic",
                    config_artic,
                    "--outdir",
                    self.get_case_output_path(case_id=case_id).as_posix(),
                    self.get_case_fastq_dir(case_id=case_id).as_posix(),
                ],
                dry_run=dry_run,
            )
        else:
            self.process.run_command(
                [
                    "analyse",
                    "sarscov2",
                    "--config_case",
                    self.get_case_config_path(case_id=case_id).as_posix(),
                    "--outdir",
                    self.get_case_output_path(case_id=case_id).as_posix(),
                    self.get_case_fastq_dir(case_id=case_id).as_posix(),
                ],
                dry_run=dry_run,
            )

    def get_cases_to_store(self) -> list[Case]:
        """Return cases for which the analysis is complete on Traiblazer and a QC report has been generated."""
        cases_to_store: list[Case] = [
            case
            for case in self.status_db.get_running_cases_in_workflow(self.workflow)
            if self.trailblazer_api.is_latest_analysis_completed(case.internal_id)
            and self.get_case_qc_report_path(case_id=case.internal_id).exists()
        ]
        return cases_to_store

    def get_cases_to_perform_qc_on(self) -> list[Case]:
        """Return cases with a completed analysis that are not yet stored."""
        cases_to_perform_qc_on: list[Case] = [
            case
            for case in self.status_db.get_running_cases_in_workflow(self.workflow)
            if self.trailblazer_api.is_latest_analysis_completed(case.internal_id)
            and not self.get_case_qc_report_path(case_id=case.internal_id).exists()
        ]
        return cases_to_perform_qc_on

    def get_metadata_for_nanopore_sample(self, sample: Sample) -> list[dict]:
        return [
            self.fastq_handler.parse_nanopore_file_data(file_obj.full_path)
            for file_obj in self.housekeeper_api.files(
                bundle=sample.internal_id, tags={SequencingFileTag.FASTQ}
            )
        ]

    def link_nanopore_fastq_for_sample(
        self, case: Case, sample: Sample, concatenate: bool = False
    ) -> None:
        """
        Link FASTQ files for a nanopore sample to working directory.
        If workflow input requires concatenated fastq, files can also be concatenated
        """
        read_paths = []
        files: list[dict] = self.get_metadata_for_nanopore_sample(sample=sample)
        sorted_files = sorted(files, key=lambda k: k["path"])
        fastq_dir = self.get_sample_fastq_destination_dir(case=case, sample=sample)
        fastq_dir.mkdir(parents=True, exist_ok=True)

        for counter, fastq_data in enumerate(sorted_files):
            fastq_path = Path(fastq_data["path"])
            fastq_name = self.fastq_handler.create_nanopore_fastq_name(
                flowcell=fastq_data["flowcell"],
                sample=sample.internal_id,
                filenr=str(counter),
                meta=self.get_lims_naming_metadata(sample),
            )
            destination_path: Path = fastq_dir / fastq_name
            read_paths.append(destination_path)

            if not destination_path.exists():
                LOG.info(f"Linking: {fastq_path} -> {destination_path}")
                destination_path.symlink_to(fastq_path)
            else:
                LOG.warning(f"Destination path already exists: {destination_path}")

        if not concatenate:
            return

        concatenated_fastq_name = self.fastq_handler.create_nanopore_fastq_name(
            flowcell=fastq_data["flowcell"],
            sample=sample.internal_id,
            filenr=str(1),
            meta=self.get_lims_naming_metadata(sample),
        )
        concatenated_path = (
            f"{fastq_dir}/{self.fastq_handler.get_concatenated_name(concatenated_fastq_name)}"
        )
        LOG.info(f"Concatenation in progress for sample {sample.internal_id}.")
        self.fastq_handler.concatenate(read_paths, concatenated_path)
        self.fastq_handler.remove_files(read_paths)

    def run_qc_on_case(self, case: Case, dry_run: bool) -> None:
        """Run qc check on case, report qc summary on Trailblazer and set analysis status to fail if it fails QC."""
        try:
            qc_result: MutantQualityResult = self.get_qc_result(case=case)
        except Exception as exception:
            error_message: str = f"Could not perform QC on case {case.internal_id}: {exception}"
            LOG.error(error_message)
            if not dry_run:
                self.trailblazer_api.add_comment(
                    case_id=case.internal_id, comment="ERROR: Could not perform QC on case"
                )
                self.trailblazer_api.set_analysis_status(
                    case_id=case.internal_id, status=AnalysisStatus.ERROR
                )
            raise CgError(error_message)

        if not dry_run:
            self.report_qc_on_trailblazer(case=case, qc_result=qc_result)
            if not qc_result.passes_qc:
                self.trailblazer_api.set_analysis_status(
                    case_id=case.internal_id, status=AnalysisStatus.FAILED
                )

    def get_qc_result(self, case: Case) -> MutantQualityResult:
        case_results_file_path: Path = self.get_case_results_file_path(case=case)
        case_qc_report_path: Path = self.get_case_qc_report_path(case_id=case.internal_id)
        qc_result: MutantQualityResult = self.quality_checker.get_quality_control_result(
            case=case,
            case_results_file_path=case_results_file_path,
            case_qc_report_path=case_qc_report_path,
        )
        return qc_result

    def report_qc_on_trailblazer(self, case: Case, qc_result: MutantQualityResult) -> None:
        report_file_path: Path = self.get_case_qc_report_path(case_id=case.internal_id)

        comment = qc_result.summary + (
            f" QC report: {report_file_path}" if not qc_result.passes_qc else ""
        )
        self.trailblazer_api.add_comment(case_id=case.internal_id, comment=comment)

    def run_qc(self, case_id: str, dry_run: bool) -> None:
        LOG.info(f"Running QC on case {case_id}.")

        case: Case = self.status_db.get_case_by_internal_id(case_id)

        self.run_qc_on_case(case=case, dry_run=dry_run)
