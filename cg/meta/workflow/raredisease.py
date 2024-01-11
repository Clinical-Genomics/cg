"""Module for Raredisease Analysis API."""

import logging
from typing import Any
from pathlib import Path

from cg.constants import GenePanelMasterList, Pipeline
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.meta.workflow.analysis import add_gene_panel_combo
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.raredisease.raredisease import RarediseaseSampleSheetEntry
from cg.models.nf_analysis import PipelineParameters
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
        self.root_dir: str = config.raredisease.root
        self.nfcore_pipeline_path: str = config.raredisease.pipeline_path
        self.references: str = config.raredisease.references
        self.profile: str = config.raredisease.profile
        self.conda_env: str = config.raredisease.conda_env
        self.conda_binary: str = config.raredisease.conda_binary
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_pipeline: str = config.raredisease.tower_pipeline
        self.account: str = config.raredisease.slurm.account
        self.compute_env: str = config.raredisease.compute_env
        self.revision: str = config.raredisease.revision

    def config_case(
        self,
        case_id: str,
        dry_run: bool,
    ) -> None:
        """Create config files (parameters and sample sheet) for Raredisease analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(case_id=case_id)
        if dry_run:
            LOG.info("Dry run: Config files will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=RarediseaseSampleSheetEntry.headers(),
        )
        pipeline_parameters: PipelineParameters = self.get_pipeline_parameters(case_id=case_id)
        self.write_params_file(case_id=case_id, pipeline_parameters=pipeline_parameters.dict())

    def get_sample_sheet_content_per_sample(
        self, sample: Sample, case: Case = "", case_sample: CaseSample = ""
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_metadata: list[str] = self.gather_file_metadata_for_sample(sample)
        fastq_forward_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, forward_read=True
        )
        fastq_reverse_read_paths: list[str] = self.extract_read_files(
            metadata=sample_metadata, reverse_read=True
        )
        sample_sheet_entry = RarediseaseSampleSheetEntry(
            name=case_sample.sample.internal_id,
            fastq_forward_read_paths=fastq_forward_read_paths,
            fastq_reverse_read_paths=fastq_reverse_read_paths,
            sex=self.get_sex_code(sample.sex),
            phenotype=self.get_phenotype_code(case_sample.status),
            paternal_id=self.get_parental_id(case_sample.father),
            maternal_id=self.get_parental_id(case_sample.mother),
            case_id=case.internal_id,
        )
        return sample_sheet_entry.reformat_sample_content()

    def get_sample_sheet_content(
        self,
        case_id: str,
    ) -> list[list[Any]]:
        """Write sample sheet for Raredisease analysis in case folder."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content = []
        LOG.debug("Getting sample sheet information")
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        for link in case.links:
            sample_sheet_content.extend(
                self.get_sample_sheet_content_per_sample(
                    sample=link.sample, case=case, case_sample=link
                )
            )
        return sample_sheet_content

    def get_pipeline_parameters(self, case_id: str) -> PipelineParameters:
        """Return parameters."""
        LOG.info("Getting parameters information")
        return PipelineParameters(
            cluster_options=f"--qos={self.get_slurm_qos_for_case(case_id=case_id)}",
            priority=self.account,
            sample_sheet_path=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
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

    def get_parental_id(self, parent: CaseSample) -> str:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to int")
        if parent:
            return parent.internal_id
        else:
            return ""

    @property
    def root(self) -> str:
        return self.config.raredisease.root

    def write_managed_variants(self, case_id: str, content: list[str]) -> None:
        self._write_managed_variants(out_dir=Path(self.root, case_id), content=content)

    def write_panel(self, case_id: str, content: list[str]) -> None:
        """Write the gene panel to case dir."""
        self._write_panel(out_dir=Path(self.root, case_id), content=content)

    @staticmethod
    def get_aggregated_panels(customer_id: str, default_panels: set[str]) -> list[str]:
        """Check if customer should use the gene panel master list
        and if all default panels are included in the gene panel master list.
        If not, add gene panel combo and OMIM-AUTO.
        Return an aggregated gene panel."""
        master_list: list[str] = GenePanelMasterList.get_panel_names()
        if customer_id in GenePanelMasterList.collaborators() and default_panels.issubset(
            master_list
        ):
            return master_list
        all_panels: set[str] = add_gene_panel_combo(default_panels=default_panels)
        all_panels |= {GenePanelMasterList.OMIM_AUTO, GenePanelMasterList.PANELAPP_GREEN}
        return list(all_panels)

    def get_gene_panel(self, case_id: str) -> list[str]:
        """Create and return the aggregated gene panel file."""
        return self._get_gene_panel(case_id=case_id, genome_build=GENOME_BUILD_37)

    def get_managed_variants(self) -> list[str]:
        """Create and return the managed variants."""
        return self._get_managed_variants(genome_build=GENOME_BUILD_37)
