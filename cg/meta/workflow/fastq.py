import logging
from pathlib import Path
from typing import List

from cgmodels.cg.constants import Pipeline

from cg.constants.delivery import PIPELINE_ANALYSIS_TAG_MAP
from cg.constants.priority import PRIORITY_TO_SLURM_QOS
from cg.meta.deliver import DeliverAPI
from cg.meta.rsync import RsyncAPI
from cg.meta.workflow.analysis import AnalysisAPI
from cg.models.cg_config import CGConfig
from cg.store import models

LOG = logging.getLogger(__name__)


class FastqAnalysisAPI(AnalysisAPI):
    """Minimalist API to integrate automatic fastq delivery in existing architecture"""

    def __init__(self, config: CGConfig, pipeline: Pipeline = Pipeline.FASTQ):
        super().__init__(pipeline, config)
        self.deliver_api: DeliverAPI = DeliverAPI(
            store=self.status_db,
            hk_api=self.housekeeper_api,
            case_tags=PIPELINE_ANALYSIS_TAG_MAP["fastq"]["case_tags"],
            sample_tags=PIPELINE_ANALYSIS_TAG_MAP["fastq"]["sample_tags"],
            delivery_type="fastq",
            project_base_path=Path(config.delivery_path),
        )
        self.rsync_api: RsyncAPI = RsyncAPI(config=config)

    def upload_bundle_housekeeper(self, case_id: str) -> None:
        """No housekeeper bundles should be created for fastq cases"""
        pass

    def upload_bundle_statusdb(self, case_id: str) -> None:
        """Creates an analysis in statusdb and sets uploaded dates"""
        super().upload_bundle_statusdb(case_id=case_id)
        analysis: models.Analysis = self.status_db.family(internal_id=case_id).analyses[0]
        analysis.upload_started_at = analysis.started_at
        analysis.uploaded_at = analysis.completed_at
        self.status_db.commit()

    def get_cases_to_store(self) -> List[models.Family]:
        """Retrieve a list of cases where the rsync finished successfully,
        and an analysis should be created in statusdb"""
        finished_cases: List[models.Family] = [
            case_object
            for case_object in self.get_running_cases()
            if self.trailblazer_api.is_latest_analysis_completed(case_id=case_object.internal_id)
        ]

        return finished_cases

    def get_deliverables_file_path(self, case_id: str) -> Path:
        """
        Location in working directory where deliverables file will be stored upon completion of analysis.
        Deliverables file is used to communicate paths and tag definitions for files in a finished analysis
        """
        ticket_id: int = self.status_db.get_ticket_from_case(case_id=case_id)
        customer_id: str = self.status_db.get_customer_id_from_ticket(ticket_id=ticket_id)
        return Path(self.deliver_api.project_base_path, customer_id, "inbox", str(ticket_id))

    def run_transfer(self, case: models.Family, case_id: str, dry_run: bool) -> int:
        """Run the transfer of fastq files for a case"""
        self.deliver_api.deliver_files(case)
        job_id: int = self.rsync_api.slurm_rsync_single_case(
            case_id=case_id, dry_run=dry_run, sample_files_present=True
        )
        self.rsync_api.write_trailblazer_config(
            {"jobs": [str(job_id)]}, config_path=self.rsync_api.trailblazer_config_path
        )
        self.trailblazer_api.add_pending_analysis(
            case_id=case_id,
            analysis_type=self.get_application_type(self.status_db.family(case_id).links[0].sample),
            config_path=str(self.rsync_api.trailblazer_config_path),
            out_dir=str(self.rsync_api.log_dir),
            slurm_quality_of_service=PRIORITY_TO_SLURM_QOS[case.priority],
            data_analysis=Pipeline.FASTQ,
        )
        self.set_statusdb_action(case_id=case_id, action="running")
        return job_id
