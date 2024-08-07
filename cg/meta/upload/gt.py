import logging
from pathlib import Path

from housekeeper.store.models import File, Version

from cg.apps.gt import GenotypeAPI
from cg.apps.housekeeper.hk import HousekeeperAPI
from cg.constants.constants import PrepCategory, Workflow
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.store.models import Analysis, Case, Sample

LOG = logging.getLogger(__name__)


class UploadGenotypesAPI(object):
    def __init__(
        self,
        hk_api: HousekeeperAPI,
        gt_api: GenotypeAPI,
    ):
        LOG.info("Initializing UploadGenotypesAPI")
        self.hk = hk_api
        self.gt = gt_api

    def get_gt_data(self, analysis: Analysis) -> dict:
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
        hk_bcf = AnalysisAPI.get_bcf_file(hk_version_obj=hk_version)
        gt_data: dict = {"bcf": hk_bcf.full_path}
        if analysis.workflow in [Workflow.BALSAMIC, Workflow.BALSAMIC_UMI]:
            analysis_api = BalsamicAnalysisAPI
        elif analysis.workflow == Workflow.MIP_DNA:
            analysis_api = MipDNAAnalysisAPI
        elif analysis.workflow == Workflow.RAREDISEASE:
            analysis_api = RarediseaseAnalysisAPI
        else:
            raise ValueError(f"Workflow {analysis.workflow} does not support Genotype upload")
        gt_data["samples_sex"] = analysis_api.get_samples_sex(
            case_obj=analysis.case, hk_version=hk_version
        )
        return gt_data

    def upload(self, gt_data: dict, replace: bool = False):
        """Upload data about genotypes for a family of samples."""
        self.gt.upload(str(gt_data["bcf"]), gt_data["samples_sex"], force=replace)

    @staticmethod
    def is_suitable_for_genotype_upload(case_obj: Case) -> bool:
        """Check if a cancer case is contains WGS and normal sample."""

        samples: list[Sample] = case_obj.samples
        return any(
            (not sample.is_tumour and PrepCategory.WHOLE_GENOME_SEQUENCING == sample.prep_category)
            for sample in samples
        )
