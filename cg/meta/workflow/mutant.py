import json
import logging
from pathlib import Path
from typing import List

from cg.constants import Pipeline
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.fastq import MicrosaltFastqHandler
from cg.models.workflow.mutant import MutantSampleConfig
from cg.store import models
from cg.utils import Process

LOG = logging.getLogger(__name__)


class MutantAnalysisAPI(AnalysisAPI):
    def __init__(
        self,
        config: dict = None,
        pipeline: Pipeline = Pipeline.SARS_COV_2,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir = config["mutant"]["root"]

    @property
    def process(self) -> Process:
        if not self._process:
            self._process = Process(
                binary=self.config["mutant"]["binary_path"],
                environment=self.config["mutant"]["conda_env"],
            )
        return self._process

    @property
    def fastq_handler(self):
        return MicrosaltFastqHandler

    def get_case_path(self, case_id: str) -> Path:
        return Path(self.root_dir, case_id)

    def get_case_output_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "results")

    def get_case_fastq_dir(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "fastq")

    def get_sample_fastq_destination_dir(self, case_obj: models.Family, sample_obj: models.Sample):
        return Path(self.get_case_path(case_id=case_obj.internal_id), "fastq")

    def get_case_config_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "case_config.json")

    def get_deliverables_file_path(self, case_id: str) -> Path:
        return Path(self.get_case_path(case_id=case_id), "deliverables.yaml")

    def link_fastq_files(self, case_id: str, dry_run: bool = False) -> None:
        case_obj = self.status_db.family(case_id)
        samples: List[models.Sample] = [link.sample for link in case_obj.links]
        for sample_obj in samples:
            self.link_fastq_files_for_sample(
                case_obj=case_obj, sample_obj=sample_obj, concatenate=True
            )

    def get_sample_parameters(self, sample_obj: models.Sample) -> MutantSampleConfig:
        return MutantSampleConfig(
            cg_sample_id=sample_obj.internal_id,
            case_id=sample_obj.links[0].family.internal_id,
            customer_sample_id=sample_obj.name,
            customer_id=sample_obj.customer.internal_id,
            cg_qc_pass=sample_obj.reads > 0,
            cg_project_id=sample_obj.links[0].family.name,
            customer_project_id=sample_obj.ticket_number,
            application_tag=sample_obj.application_version.application.tag,
            method_libprep=self.lims_api.get_sample_attribute(
                lims_id=sample_obj.internal_id, key="pre_processing_method"
            ),
            method_sequencing="novaseq",
            date_arrival=str(sample_obj.received_at),
            date_libprep=str(sample_obj.prepared_at),
            date_sequencing=str(sample_obj.sequenced_at),
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
        )

    def create_case_config(self, case_id: str, dry_run: bool) -> None:
        case_obj = self.status_db.family(case_id)
        samples: List[models.Sample] = [link.sample for link in case_obj.links]
        case_config_list = [
            self.get_sample_parameters(sample_obj=sample_obj).dict() for sample_obj in samples
        ]
        config_path = self.get_case_config_path(case_id=case_id)
        if dry_run:
            LOG.info("Dry-run, would have created config at path %s, with content:", config_path)
            LOG.info(case_config_list)
        json.dump(case_config_list, open(config_path, "w"))
        LOG.info("Saved config to %s", config_path)

    def run_analysis(self, case_id: str, dry_run: bool) -> None:
        self.process.run_command(
            [
                "analyse",
                "--config_case",
                self.get_case_config_path(case_id=case_id).as_posix(),
                "--outdir",
                self.get_case_output_path(case_id=case_id).as_posix(),
                self.get_case_fastq_dir(case_id=case_id),
            ],
            dry_run=dry_run,
        )
