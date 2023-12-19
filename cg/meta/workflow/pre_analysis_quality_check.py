from cg.constants import Priority
from cg.constants.constants import PrepCategory
from cg.meta.workflow.analysis import AnalysisAPI
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.meta.workflow.balsamic_qc import BalsamicQCAnalysisAPI
from cg.meta.workflow.balsamic_umi import BalsamicUmiAnalysisAPI
from cg.meta.workflow.microsalt import MicrosaltAnalysisAPI
from cg.meta.workflow.mip_dna import MipDNAAnalysisAPI
from cg.meta.workflow.mip_rna import MipRNAAnalysisAPI
from cg.meta.workflow.raredisease import RarediseaseAnalysisAPI
from cg.meta.workflow.rnafusion import RnafusionAnalysisAPI
from cg.meta.workflow.taxprofiler import TaxprofilerAnalysisAPI
from cg.store.models import Case, Sample


class PreAnalysisQualityCheck:
    def __init__(self, case: Case) -> None:
        """
        Initialize the PreAnalysisQualityCheck class.

        Args:
            case (Case): The case object.

        """
        self.case: Case = case
        self.samples: list[Sample] = case.samples

    def standard_sequencing_qc(self) -> bool:
        """
        Run standard sequencing qc for all samples in a case.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        return all(sample.reads >= sample.expected_reads for sample in self.samples)

    def express_sequencing_qc(self) -> bool:
        """
        Run express sequencing qc for all samples in a case.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        return all(
            sample.reads >= self.get_express_reads_threshold(sample) for sample in self.samples
        )

    def all_samples_have_reads(self) -> bool:
        """
        Check if all samples have reads.

        Returns:
            bool: True if all samples have reads, False otherwise.

        """
        return all(bool(sample.reads) for sample in self.samples)

    def any_sample_has_reads(self) -> bool:
        """
        Check if any sample has reads.

        Returns:
            bool: True if any sample has reads, False otherwise.

        """
        return any(bool(sample.reads) for sample in self.samples)

    @staticmethod
    def get_express_reads_threshold(sample: Sample) -> int:
        """
        Get the express reads threshold for a sample.

        Args:
            sample (Sample): The sample object.

        Returns:
            int: The express reads threshold.

        """
        return round(sample.application_version.application.target_reads / 2)

    def sequencing_qc(self) -> bool:
        """
        Run qc for all samples in case.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        raise NotImplementedError("Must be implemented in subclass.")

    @classmethod
    def run_qc(cls, case: Case) -> bool:
        """
        Run pre analysis qc for all samples in case.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        instance = cls(case)
        return instance.sequencing_qc()


class FastqPreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        """
        Initialize the FastqPreAnalysisQc class.

        Args:
            case (Case): The case object.

        """
        super().__init__(case)

    def all_samples_are_ready_made_libraries(self) -> bool:
        """
        Check if all samples in case are ready made libraries.

        Returns:
            bool: True if all samples are ready made libraries, False otherwise.

        """
        return all(
            sample.prep_category == PrepCategory.ready_made_library for sample in self.samples
        )

    def ready_made_library_qc(self) -> bool:
        """
        Perform qc for ready made libraries.

        Returns:
            bool: True if all ready made libraries pass the qc, False otherwise.

        """
        return self.all_samples_have_reads()

    def sequencing_qc(self) -> bool:
        """
        Perform fastq sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        if self.all_samples_are_ready_made_libraries():
            return self.ready_made_library_qc()
        return self.standard_sequencing_qc()


class BalsamicPreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        """
        Initialize the BalsamicPreAnalysisQc class.

        Args:
            case (Case): The case object.

        """
        super().__init__(case)

    def sequencing_qc(self) -> bool:
        """
        Perform balsamic sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        if self.case.priority == Priority.express:
            return self.express_sequencing_qc()
        return self.standard_sequencing_qc()


class MicrobialPreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        super().__init__(case)

    def sequencing_qc(self) -> bool:
        """
        Perform microbial sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        return self.any_sample_has_reads()


class MIPPreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        super().__init__(case)

    def sequencing_qc(self) -> bool:
        """
        Perform mip sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        if self.case.priority == Priority.express:
            return self.express_sequencing_qc()
        return self.standard_sequencing_qc()


class TaxProfilerPreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        super().__init__(case)

    def sequencing_qc(self) -> bool:
        """
        Perform taxprofiler sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """

        return self.all_samples_have_reads()


class RnafusionPreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        super().__init__(case)

    def sequencing_qc(self) -> bool:
        """
        Perform rnafusion sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        if self.case.priority == Priority.express:
            return self.express_sequencing_qc()
        return self.standard_sequencing_qc()


class RareDiseasePreAnalysisQc(PreAnalysisQualityCheck):
    def __init__(self, case: Case) -> None:
        super().__init__(case)

    def sequencing_qc(self) -> bool:
        """
        Perform rare disease sequencing qc.

        Returns:
            bool: True if all samples pass the qc, False otherwise.

        """
        if self.case.priority == Priority.express:
            return self.express_sequencing_qc()
        return self.standard_sequencing_qc()


def get_pre_analysis_quality_check_for_workflow(
    analysis_api: AnalysisAPI,
) -> PreAnalysisQualityCheck:
    pre_analysis_quality_checks: dict[AnalysisAPI, PreAnalysisQualityCheck] = {
        BalsamicAnalysisAPI: BalsamicPreAnalysisQc,
        BalsamicQCAnalysisAPI: BalsamicPreAnalysisQc,
        BalsamicUmiAnalysisAPI: BalsamicPreAnalysisQc,
        MicrosaltAnalysisAPI: MicrobialPreAnalysisQc,
        MipDNAAnalysisAPI: MIPPreAnalysisQc,
        MipRNAAnalysisAPI: MIPPreAnalysisQc,
        TaxprofilerAnalysisAPI: TaxProfilerPreAnalysisQc,
        RnafusionAnalysisAPI: RnafusionPreAnalysisQc,
        RarediseaseAnalysisAPI: RareDiseasePreAnalysisQc,
    }
    pre_analysis_quality_check: PreAnalysisQualityCheck = pre_analysis_quality_checks.get(
        type(analysis_api)
    )
    if not pre_analysis_quality_check:
        raise NotImplementedError("No pre analysis quality check implemented for this workflow.")
    return pre_analysis_quality_check
