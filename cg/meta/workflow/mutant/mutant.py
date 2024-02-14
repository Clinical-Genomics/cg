import csv
import logging
import shutil
from pathlib import Path
from typing import Any, Optional

from cg.constants import Pipeline
from cg.constants.constants import FileFormat, MutantQC
from cg.constants.tb import AnalysisStatus
from cg.io.controller import WriteFile
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MutantFastqHandler
from cg.models.cg_config import CGConfig
from cg.models.workflow.mutant import MutantSampleConfig
from cg.store.models import Application, Case, Sample
from cg.utils import Process

LOG = logging.getLogger(__name__)


class MutantAnalysisAPI(AnalysisAPI):
    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.SARS_COV_2,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir = config.mutant.root

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

    @property
    def use_read_count_threshold(self) -> bool:
        return False

    def get_case_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id)

    def get_case_output_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "results")

    def get_case_results_file_path(self, case: Case) -> Path:
        case_output_path: Path = self.get_case_output_path(case.internal_id)
        return case_output_path / Path(f"/sars-cov-2_{case.latest_ticket}_results.csv")

    def get_case_fastq_dir(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "fastq")

    def get_trailblazer_config_path(self, case_id: str) -> Path:
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
                    case_obj=case_obj, sample_obj=sample_obj, concatenate=True
                )
                continue
            if not sample_obj.sequencing_qc:
                LOG.info("Sample %s read count below threshold, skipping!", sample_obj.internal_id)
                continue
            else:
                self.link_fastq_files_for_sample(
                    case_obj=case_obj, sample_obj=sample_obj, concatenate=True
                )

    def get_sample_parameters(self, sample_obj: Sample) -> MutantSampleConfig:
        return MutantSampleConfig(
            CG_ID_sample=sample_obj.internal_id,
            case_ID=sample_obj.links[0].family.internal_id,
            Customer_ID_sample=sample_obj.name,
            customer_id=sample_obj.customer.internal_id,
            sequencing_qc_pass=sample_obj.sequencing_qc,
            CG_ID_project=sample_obj.links[0].family.name,
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
        case_config_list = [
            self.get_sample_parameters(sample_obj).model_dump() for sample_obj in samples
        ]
        config_path = self.get_case_config_path(case_id=case_id)
        if dry_run:
            LOG.info("Dry-run, would have created config at path %s, with content:", config_path)
            LOG.info(case_config_list)
        config_path.parent.mkdir(parents=True, exist_ok=True)
        WriteFile.write_file_from_content(
            content=case_config_list, file_format=FileFormat.JSON, file_path=config_path
        )
        LOG.info("Saved config to %s", config_path)

    def get_additional_naming_metadata(self, sample_obj: Sample) -> Optional[str]:
        sample_name = sample_obj.name
        region_code = self.lims_api.get_sample_attribute(
            lims_id=sample_obj.internal_id, key="region_code"
        ).split(" ")[0]
        lab_code = self.lims_api.get_sample_attribute(
            lims_id=sample_obj.internal_id, key="lab_code"
        ).split(" ")[0]

        return f"{region_code}_{lab_code}_{sample_name}"

    def get_cases_to_store(self) -> list[Case]:
        """Return running cases where analysis has a deliverables file,
        and is ready to be stored in Housekeeper."""

        return [
            case
            for case in self.status_db.get_running_cases_in_pipeline(pipeline=self.pipeline)
            if Path(self.get_deliverables_file_path(case_id=case.internal_id)).exists()
        ]

    def get_metadata_for_nanopore_sample(self, sample_obj: Sample) -> list[dict]:
        return [
            self.fastq_handler.parse_nanopore_file_data(file_obj.full_path)
            for file_obj in self.housekeeper_api.files(
                bundle=sample_obj.internal_id, tags=["fastq"]
            )
        ]

    def link_nanopore_fastq_for_sample(
        self, case_obj: Case, sample_obj: Sample, concatenate: bool = False
    ) -> None:
        """
        Link FASTQ files for a nanopore sample to working directory.
        If pipeline input requires concatenated fastq, files can also be concatenated
        """
        read_paths = []
        files: list[dict] = self.get_metadata_for_nanopore_sample(sample_obj=sample_obj)
        sorted_files = sorted(files, key=lambda k: k["path"])
        fastq_dir = self.get_sample_fastq_destination_dir(case=case_obj, sample=sample_obj)
        fastq_dir.mkdir(parents=True, exist_ok=True)

        for counter, fastq_data in enumerate(sorted_files):
            fastq_path = Path(fastq_data["path"])
            fastq_name = self.fastq_handler.create_nanopore_fastq_name(
                flowcell=fastq_data["flowcell"],
                sample=sample_obj.internal_id,
                filenr=str(counter),
                meta=self.get_additional_naming_metadata(sample_obj),
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
            sample=sample_obj.internal_id,
            filenr=str(1),
            meta=self.get_additional_naming_metadata(sample_obj),
        )
        concatenated_path = (
            f"{fastq_dir}/{self.fastq_handler.get_concatenated_name(concatenated_fastq_name)}"
        )
        LOG.info("Concatenation in progress for sample %s.", sample_obj.internal_id)
        self.fastq_handler.concatenate(read_paths, concatenated_path)
        self.fastq_handler.remove_files(read_paths)

    def qc_check_fails(self, case: Case) -> bool:
        """TODO: Checks result file and counts False"""

        # fetch the negctrl
        # process_results_file

        # check_negative_control
        #     check_read_counts
        #     #In the future run kraken

        # check_all_samples

        failed_samples, number_of_samples = self.process_results_file(
            self.get_case_results_file_path(case)  # , negative_control
        )

        return (
            True
            if failed_samples / number_of_samples
            > MutantQC.FRACTION_OF_SAMPLES_WITH_FAILED_QC_TRESHOLD
            else False
        )

    def parse_results_file(results_file: Path, negative_control: str) -> tuple[int, int]:
        with open(results_file, "r") as file:
            results: dict[str, Any] = csv.DictReader(file)

        #Parse the values without "" to get the 'clean' string
        # a = {
        #     "Sample": "23CS102364",
        #     "Selection": "Allmän övervakning",
        #     "Region Code": "01",
        #     "Ticket": "841080",
        #     "%N_bases": "0.23",
        #     "%10X_coverage": "99.64",
        #     "QC_pass": "TRUE",
        #     "Lineage": "JD.1.1",
        #     "Pangolin_data_version": "PUSHER-v1.23.1",
        #     "VOC": "No",
        #     "Mutations": "S373P;S375F;N440K;G446S;A475V;S477N;T478K;E484A;F490S;Q498R;N501Y;Y505H;D614G;H655Y;N679K;P681H;N764K;D796Y;Q954H;N969K",
        # }
        # if 0provsek gets true

        # Later do QC check of ration
        number_of_samples: int = 0
        failed_samples: int = 0
        for sample in results:
            if sample["QC_pass"] == "FAIL":
                # TODO: turn "FAIL" into constant
                failed_samples += 1
            number_of_samples += 1
        return (failed_samples, number_of_samples)

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

    def run_qc_and_fail_cases(self, dry_run: bool) -> None:
        """TODO: Fails cases that fail QC."""

        for case in self.get_cases_to_store():
            if self.qc_check_fails(case):
                if not dry_run:
                    self.fail_case(case)

    def fail_case(self, case: Case) -> None:
        """TODO:Fails case on TB and set to none on StatusDB"""
        self.trailblazer_api.set_analysis_status(
            case_id=case.internal_id, status=AnalysisStatus.FAILED
        )
        self.set_statusdb_action(case_id=case.internal_id, action="hold")
