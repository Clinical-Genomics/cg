from pathlib import Path
from cg.models.nf_analysis import NextflowSample, PipelineParameters
from cg.constants.sequencing import SequencingPlatform


class TaxprofilerParameters(PipelineParameters):
    """Model for Taxprofiler parameters."""

    input: Path
    outdir: Path
    databases: Path
    save_preprocessed_reads: bool = True
    perform_shortread_qc: bool = True
    perform_shortread_complexityfilter: bool = True
    save_complexityfiltered_reads: bool = True
    perform_shortread_hostremoval: bool = True
    hostremoval_reference: Path
    save_hostremoval_index: bool = True
    save_hostremoval_mapped: bool = True
    save_hostremoval_unmapped: bool = True
    perform_runmerging: bool = True
    run_kraken2: bool = True
    kraken2_save_reads: bool = True
    kraken2_save_readclassification: bool = True
    run_krona: bool = True
    run_profile_standardisation: bool = True


class TaxprofilerSample(NextflowSample):
    """Taxprofiler sample model is used when building the sample sheet."""

    instrument_platform: SequencingPlatform
