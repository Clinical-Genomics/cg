"""Module for Raredisease Analysis API."""

import logging
from typing import Any
from pathlib import Path

from cg.io.txt import concat_txt
from cg.io.config import write_config_nextflow_style
from cg.constants import GenePanelMasterList, Workflow
from cg.constants.constants import FileExtensions
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.constants.gene_panel import GENOME_BUILD_37
from cg.meta.workflow.analysis import add_gene_panel_combo
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.fastq import FastqFileMeta
from cg.models.raredisease.raredisease import (
    RarediseaseSampleSheetEntry,
    RarediseaseSampleSheetHeaders,
)
from cg.models.nf_analysis import WorkflowParameters
from cg.store.models import Case, CaseSample


LOG = logging.getLogger(__name__)


class RarediseaseAnalysisAPI(NfAnalysisAPI):
    """Handles communication between RAREDISEASE processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.RAREDISEASE,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.raredisease.root
        self.nfcore_workflow_path: str = config.raredisease.workflow_path
        self.references: str = config.raredisease.references
        self.profile: str = config.raredisease.profile
        self.conda_env: str = config.raredisease.conda_env
        self.conda_binary: str = config.raredisease.conda_binary
        self.config_platform: str = config.raredisease.config_platform
        self.config_params: str = config.raredisease.config_params
        self.config_resources: str = config.raredisease.config_resources
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.raredisease.tower_workflow
        self.account: str = config.raredisease.slurm.account
        self.compute_env: str = config.raredisease.compute_env
        self.revision: str = config.raredisease.revision

    def write_config_case(
        self,
        case_id: str,
        dry_run: bool,
    ) -> None:
        """Create a parameter (.config) files and a Nextflow sample sheet input for Raredisease analysis."""
        self.create_case_directory(case_id=case_id, dry_run=dry_run)
        sample_sheet_content: list[list[Any]] = self.get_sample_sheet_content(case_id=case_id)
        workflow_parameters: WorkflowParameters = self.get_workflow_parameters(case_id=case_id)
        if dry_run:
            LOG.info("Dry run: nextflow sample sheet and parameter file will not be written")
            return
        self.write_sample_sheet(
            content=sample_sheet_content,
            file_path=self.get_sample_sheet_path(case_id=case_id),
            header=RarediseaseSampleSheetHeaders.headers(),
        )
        self.write_params_file(case_id=case_id, workflow_parameters=workflow_parameters.dict())

    def get_sample_sheet_content_per_sample(
        self, case: Case = "", case_sample: CaseSample = ""
    ) -> list[list[str]]:
        """Get sample sheet content per sample."""
        sample_metadata: list[FastqFileMeta] = self.gather_file_metadata_for_sample(
            case_sample.sample
        )
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
            sex=self.get_sex_code(case_sample.sample.sex),
            phenotype=self.get_phenotype_code(case_sample.status),
            paternal_id=case_sample.get_paternal_sample_id,
            maternal_id=case_sample.get_maternal_sample_id,
            case_id=case.internal_id,
        )
        return sample_sheet_entry.reformat_sample_content

    def get_sample_sheet_content(
        self,
        case_id: str,
    ) -> list[list[Any]]:
        """Return Raredisease nextflow sample sheet content for a case."""
        case: Case = self.status_db.get_case_by_internal_id(internal_id=case_id)
        sample_sheet_content = []
        LOG.info("Getting sample sheet information")
        LOG.info(f"Samples linked to case {case_id}: {len(case.links)}")
        for link in case.links:
            sample_sheet_content.extend(
                self.get_sample_sheet_content_per_sample(case=case, case_sample=link)
            )
        return sample_sheet_content

    def get_workflow_parameters(self, case_id: str) -> WorkflowParameters:
        """Return parameters."""
        LOG.info("Getting parameters information")
        return WorkflowParameters(
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=self.get_case_path(case_id=case_id),
        )

    def get_params_file_path(self, case_id: str, params_file: Path | None = None) -> Path:
        """Return parameters file or a path where the default parameters file for a case id should be located."""
        if params_file:
            return params_file.absolute()
        case_path: Path = self.get_case_path(case_id)
        return Path(case_path, f"{case_id}_params_file{FileExtensions.CONFIG}")
        # This function should be moved to nf-analysis to replace the current one when all nextflow pipelines are using the same config files approach

    def write_params_file(self, case_id: str, workflow_parameters: dict) -> None:
        """Write params-file for analysis."""
        LOG.debug("Writing parameters file")
        config_files_list = [self.config_platform, self.config_params, self.config_resources]
        extra_parameters_str = [
            write_config_nextflow_style(workflow_parameters),
            self.set_cluster_options(case_id=case_id),
        ]
        concat_txt(
            file_paths=config_files_list,
            target_file=self.get_params_file_path(case_id=case_id),
            str_content=extra_parameters_str,
        )

    @staticmethod
    def get_phenotype_code(phenotype: str) -> int:
        """Return Raredisease phenotype code."""
        LOG.debug("Translate phenotype to integer code")
        try:
            code = PlinkPhenotypeStatus[phenotype.upper()]
        except KeyError:
            raise ValueError(f"{phenotype} is not a valid phenotype")
        return code

    @staticmethod
    def get_sex_code(sex: str) -> int:
        """Return Raredisease sex code."""
        LOG.debug("Translate sex to integer code")
        try:
            code = PlinkSex[sex.upper()]
        except KeyError:
            raise ValueError(f"{sex} is not a valid sex")
        return code

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
