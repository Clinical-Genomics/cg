import logging
from pathlib import Path

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import PrepCategory, Workflow
from cg.constants.subject import Sex
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI

from cg.store.models import Analysis, Case, Sample

from housekeeper.store.models import File, Version

LOG = logging.getLogger(__name__)


class UploadGenotypesAPI(object):
    """Genotype upload API"""

    def __init__(
        self,
        hk_api: HousekeeperAPI,
        gt_api: GenotypeAPI,
    ):
        LOG.info("Initializing UploadGenotypesAPI")
        self.hk = hk_api
        self.gt = gt_api

    def get_gt_data(self, analysis: Analysis) -> dict[dict[str, dict[str, str]]]:
        """Fetch data about an analysis to load genotypes.

        Returns: dict on form
        {
            "bcf": path_to_bcf,
            "samples_sex": [
                "sample_id: {
                    "pedigree": "male",
                    "analysis": "male"
                    }
            ]
        }
        """

        case_id = analysis.case.internal_id
        LOG.info(f"Fetching upload genotype data for {case_id}")
        hk_version = self.hk.last_version(case_id)
        if analysis.workflow in [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI]:
            analysis_api = BalsamicAnalysisAPI
        elif analysis.workflow == Workflow.MIP_DNA:
            analysis_api = MipDNAAnalysisAPI
        elif analysis.workflow == Workflow.RAREDISEASE:
            analysis_api = RarediseaseAnalysisAPI
        else:
            raise ValueError(f"Workflow {analysis.workflow} does not support Genotype upload")
        hk_bcf = self.get_bcf_file(hk_version_obj=hk_version)
        gt_data: dict = {"bcf": hk_bcf.full_path}
        gt_data["samples_sex"] = self.get_samples_sex(
            case=analysis.case, hk_version=hk_version, analysis_api=analysis_api
        )
        return gt_data

    def upload(self, gt_data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(gt_data["bcf"]), gt_data["samples_sex"], force=replace)

    @staticmethod
    def is_suitable_for_genotype_upload(case: Case) -> bool:
        """Check if a cancer case is contains WGS and normal sample."""

        samples: list[Sample] = case.samples
        return any(
            (not sample.is_tumour and PrepCategory.WHOLE_GENOME_SEQUENCING == sample.prep_category)
            for sample in samples
        )

    def get_genotype_files(self, version_id: int) -> list:
        return HousekeeperAPI.files(self, version=version_id, tags={"genotype"}).all()

    def is_variant_file(self, genotype_file: File):
        return genotype_file.full_path.endswith("vcf.gz") or genotype_file.full_path.endswith("bcf")

    def get_bcf_file(
        self,
        hk_version_obj: Version,
    ) -> File:
        """Return a BCF file object. Raises error if nothing is found in the bundle"""
        genotype_files: list = self.get_genotype_files(version_id=hk_version_obj.id)
        for genotype_file in genotype_files:
            if self.is_variant_file(genotype_file=genotype_file):
                LOG.debug(f"Found BCF file {genotype_file.full_path}")
                return genotype_file
        raise FileNotFoundError(f"No VCF or BCF file found for bundle {hk_version_obj.bundle_id}")

    def get_samples_sex(self, case: Case, hk_version: Version, analysis_api: AnalysisAPI) -> dict:
        if analysis_api == Workflow.BALSAMIC or analysis_api == Workflow.BALSAMIC_UMI:
            return self.get_samples_sex_balsamic(case)
        elif analysis_api == Workflow.MIP_DNA:
            return self.get_samples_sex_mip_dna(case, hk_version, analysis_api)
        elif analysis_api == Workflow.RAREDISEASE:
            return self.get_samples_sex_raredisease(case, hk_version, analysis_api)

    def get_samples_sex_balsamic(
        self, case: Case
    ) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (UNKNOWN for BALSAMIC)."""
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            if case_sample.sample.is_tumour:
                continue
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": Sex.UNKNOWN,
            }
        return samples_sex

    def get_samples_sex_mip_dna(
        self, case: Case, hk_version: Version, analysis_api: MipDNAAnalysisAPI
    ) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (stored Housekeeper QC metrics file)."""
        qc_metrics_file: Path = analysis_api.get_qcmetrics_file(hk_version)
        analysis_sexes: dict = analysis_api.get_analysis_sex(qc_metrics_file)
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": analysis_sexes[sample_id],
            }
        return samples_sex

    def get_samples_sex_raredisease(
        self, case: Case, hk_version: Version, analysis_api: RarediseaseAnalysisAPI
    ) -> dict[str, dict[str, str]]:
        """Return sex information from StatusDB and from analysis prediction (stored Housekeeper QC metrics file)."""
        qc_metrics_file: Path = analysis_api.get_qcmetrics_file(hk_version)
        samples_sex: dict[str, dict[str, str]] = {}
        for case_sample in case.links:
            sample_id: str = case_sample.sample.internal_id
            samples_sex[sample_id] = {
                "pedigree": case_sample.sample.sex,
                "analysis": analysis_api.get_analysis_sex(
                    qc_metrics_file, sample_id=sample_id
                ),
            }
        return samples_sex
