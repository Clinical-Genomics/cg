"""Module for Raredisease Analysis API."""

import logging
from typing import Any

from cg.constants import Pipeline
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.raredisease.raredisease import RarediseaseSampleSheetEntry, RarediseaseParameters
from cg.store.models import Case, Sample, CaseSample

LOG = logging.getLogger(__name__)


class RarediseaseAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RAREDISEASE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        pipeline: Pipeline = Pipeline.RAREDISEASE,
    ):
        super().__init__(config=config, pipeline=pipeline)
        self.root_dir: str = config.rnafusion.root
        self.nfcore_pipeline_path: str = config.rnafusion.pipeline_path
        self.references: str = config.rnafusion.references
        self.profile: str = config.rnafusion.profile
        self.conda_env: str = config.rnafusion.conda_env
        self.conda_binary: str = config.rnafusion.conda_binary
        self.tower_binary_path: str = config.rnafusion.tower_binary_path
        self.tower_pipeline: str = config.rnafusion.tower_pipeline
        self.account: str = config.rnafusion.slurm.account
        self.compute_env: str = config.rnafusion.compute_env
        self.revision: str = config.rnafusion.revision

    def config_case(
        self,
        case_id: str,
        dry_run: bool,
    ) -> None:
        """Create config files (parameters and sample sheet) for Raredisease analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
            # sample_data: dict[str, str | int] = self.get_sample_data(link_obj=link_obj)
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(case_id=case_id)
        # pipeline_parameters: RarediseaseParameters = self.get_pipeline_parameters(case_id=case_id)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=RarediseaseSampleSheetEntry.headers(),
        )
        self.write_params_file(case_id=case_id, pipeline_parameters=pipeline_parameters.dict())

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, case: Case = "", case_sample: CaseSample = ""
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_metadata: list[str] = self.gather_file_metadata_for_sample(sample)
        # lane: str = "get lane info from somewhere"
        fastq_forward_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        print(fastq_forward_read_paths)
        print(case_sample.sample.internal_id)
        print(sample.sex)
        print(case_sample.status)
        print(sample.father)
        print(sample.father)
        print(case.internal_id)

        # get_phenotype

        sample_sheet_entry = RarediseaseSampleSheetEntry(
            name=case_sample.sample.internal_id,
            lane="1",
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            sex=self.get_sex_code(sample.sex),
            phenotype=self.get_phenotype_code(case_sample.status),
            paternal_id=self.get_parental_code(sample.father_links.internal_id),
            maternal_id=self.get_parental_code(sample.mother_links.internal_id),
            case_id=case.internal_id,
        )
        return sample_sheet_entry.reformat_sample_content()

    # @staticmethod
    # def get_sample_data(link_obj: CaseSample) -> dict[str, str | int]:
    #     """Return sample specific data."""
    #     return {
    #         "sample_id": link_obj.sample.internal_id,
    #         "sample_display_name": link_obj.sample.name,
    #         "analysis_type": link_obj.sample.application_version.application.analysis_type,
    #         "sex": link_obj.sample.sex,
    #         "phenotype": link_obj.status,
    #         "expected_coverage": link_obj.sample.application_version.application.min_sequencing_depth,
    #     }


    def get_sample_sheet_content(
        self,
        case_id: str,
    ) -> list[list[Any]]:
        """Write sample sheet for Raredisease analysis in case folder."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content = []
        LOG.debug("Getting sample sheet information")
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
                # links: list[CaseSample] = self.store.get_case_samples_by_case_id(case_internal_id=case_id)

        for link in case.links:
            sample_sheet_content.extend(
                self.get_sample_sheet_content_per_sample(sample=link.sample, case=case, case_sample=link)
            )
        return sample_sheet_content

    def get_pipeline_parameters(self, case_id: str) -> RarediseaseParameters:
        """Return Raredisease parameters."""
        LOG.debug("Getting parameters information")
        return RarediseaseParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            sample_sheet_path=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
            priority=self.account,
        )

    def get_phenotype_code(self, phenotype: str) -> int:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to int")
        if phenotype == "unaffected":
            return 1
        elif phenotype == "affected":
            return 2
        else:
            return 0

    def get_sex_code(self, sex: str) -> int:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to int")
        if sex == "male":
            return 1
        elif sex == "female":
            return 2
        else:
            return 0

    def get_parental_code(self, parent: str) -> int:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to int")
        if parent:
            return parent
        else:
            return ""


