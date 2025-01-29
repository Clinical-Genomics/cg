"""Module for Nallo Analysis API."""

import logging

from cg.constants import Workflow
from cg.constants.nf_analysis import NALLO_METRIC_CONDITIONS
from cg.constants.subject import PlinkPhenotypeStatus, PlinkSex
from cg.meta.workflow.nf_analysis import NfAnalysisAPI
from cg.models.cg_config import CGConfig
from cg.models.nallo.nallo import NalloSampleSheetHeaders, NalloSampleSheetEntry, NalloParameters
from cg.store.models import CaseSample
from pathlib import Path

LOG = logging.getLogger(__name__)


class NalloAnalysisAPI(NfAnalysisAPI):
    """Handles communication between Nallo processes
    and the rest of CG infrastructure."""

    def __init__(
        self,
        config: CGConfig,
        workflow: Workflow = Workflow.NALLO,
    ):
        super().__init__(config=config, workflow=workflow)
        self.root_dir: str = config.nallo.root
        self.workflow_bin_path: str = config.nallo.workflow_bin_path
        self.profile: str = config.nallo.profile
        self.conda_env: str = config.nallo.conda_env
        self.conda_binary: str = config.nallo.conda_binary
        self.platform: str = config.nallo.platform
        self.params: str = config.nallo.params
        self.workflow_config_path: str = config.nallo.config
        self.resources: str = config.nallo.resources
        self.tower_binary_path: str = config.tower_binary_path
        self.tower_workflow: str = config.nallo.tower_workflow
        self.account: str = config.nallo.slurm.account
        self.email: str = config.nallo.slurm.mail_user
        self.compute_env_base: str = config.nallo.compute_env
        self.revision: str = config.nallo.revision
        self.nextflow_binary_path: str = config.nallo.binary_path

    @property
    def sample_sheet_headers(self) -> list[str]:
        """Headers for sample sheet."""
        return NalloSampleSheetHeaders.list()

    def get_sample_sheet_content_per_sample(self, case_sample: CaseSample) -> list[list[str]]:
        """Collect and format information required to build a sample sheet for a single sample."""
        read_file_paths = self.get_bam_read_file_paths(sample=case_sample.sample)
        sample_sheet_entries = []

        for bam_path in read_file_paths:
            sample_sheet_entry = NalloSampleSheetEntry(
                project=case_sample.case.internal_id,
                sample=case_sample.sample.internal_id,
                read_file=Path(bam_path),
                family_id=case_sample.case.internal_id,
                paternal_id=case_sample.get_paternal_sample_id or "0",
                maternal_id=case_sample.get_maternal_sample_id or "0",
                sex=self.get_sex_code(case_sample.sample.sex),
                phenotype=self.get_phenotype_code(case_sample.status),
            )
            sample_sheet_entries.extend(sample_sheet_entry.reformat_sample_content)
        return sample_sheet_entries

    @staticmethod
    def get_phenotype_code(phenotype: str) -> int:
        """Return Nallo phenotype code."""
        LOG.debug("Translate phenotype to integer code")
        try:
            code = PlinkPhenotypeStatus[phenotype.upper()]
        except KeyError:
            raise ValueError(f"{phenotype} is not a valid phenotype")
        return code

    @staticmethod
    def get_sex_code(sex: str) -> int:
        """Return Nallo sex code."""
        LOG.debug("Translate sex to integer code")
        try:
            code = PlinkSex[sex.upper()]
        except KeyError:
            raise ValueError(f"{sex} is not a valid sex")
        return code

    def get_built_workflow_parameters(self, case_id: str) -> NalloParameters:
        """Return parameters."""
        outdir = self.get_case_path(case_id=case_id)

        return NalloParameters(
            input=self.get_sample_sheet_path(case_id=case_id),
            outdir=outdir,
        )

    def get_workflow_metrics(self, metric_id: str) -> dict:
        return NALLO_METRIC_CONDITIONS
