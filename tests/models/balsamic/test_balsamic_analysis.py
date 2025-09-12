from pathlib import Path

import pytest

from cg.constants.constants import SampleType, Workflow
from cg.meta.workflow.balsamic import BalsamicAnalysisAPI
from cg.models.balsamic.analysis import BalsamicAnalysis
from cg.models.balsamic.config import (
    BalsamicConfigAnalysis,
    BalsamicConfigJSON,
    BalsamicConfigPanel,
    BalsamicConfigQC,
    BalsamicConfigReference,
    BalsamicConfigSample,
    BalsamicVarCaller,
)
from cg.models.balsamic.metrics import BalsamicTargetedQCMetrics, BalsamicWGSQCMetrics
from cg.models.cg_config import CGConfig


@pytest.fixture
def expected_tga_balsamic_analysis() -> BalsamicAnalysis:
    return BalsamicAnalysis(
        balsamic_config=BalsamicConfigJSON(
            analysis=BalsamicConfigAnalysis(
                case_id="mock_case",
                analysis_type="paired",
                analysis_workflow="balsamic",
                sequencing_type="targeted",
                BALSAMIC_version="8.2.5",
                config_creation_date="2021-12-28 13:12",
            ),
            samples=[
                BalsamicConfigSample(
                    type=SampleType.NORMAL,
                    name="ACC0000A0",
                    fastq_info={
                        "H3CVVDRXY_ACC0000A0_S68_L001": {
                            "fwd": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A0_S68_L001_R1_001.fastq.gz"
                            ),
                            "rev": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A0_S68_L001_R2_001.fastq.gz"
                            ),
                        },
                        "H3CVVDRXY_ACC0000A0_S68_L002": {
                            "fwd": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A0_S68_L002_R1_001.fastq.gz"
                            ),
                            "rev": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A0_S68_L002_R2_001.fastq.gz"
                            ),
                        },
                    },
                ),
                BalsamicConfigSample(
                    type=SampleType.TUMOR,
                    name="ACC0000A1",
                    fastq_info={
                        "H3CVVDRXY_ACC0000A1_S68_L001": {
                            "fwd": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A1_S68_L001_R1_001.fastq.gz"
                            ),
                            "rev": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A1_S68_L001_R2_001.fastq.gz"
                            ),
                        },
                        "H3CVVDRXY_ACC0000A1_S68_L002": {
                            "fwd": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A1_S68_L002_R1_001.fastq.gz"
                            ),
                            "rev": Path(
                                "/mock/path/cases/mock_case/analysis/fastq/H3CVVDRXY_ACC0000A1_S68_L002_R2_001.fastq.gz"
                            ),
                        },
                    },
                ),
            ],
            reference=BalsamicConfigReference(
                reference_genome=Path(
                    "/mock/path/balsamic_cache/8.2.5/hg19/genome/human_g1k_v37.fasta"
                ),
                reference_genome_version="hg19",
            ),
            panel=BalsamicConfigPanel(
                capture_kit="gicfdna_3.1_hg19_design.bed",
                capture_kit_version="3.1",
                chrom=[
                    "19",
                    "2",
                    "8",
                    "18",
                    "14",
                    "12",
                    "1",
                    "7",
                    "20",
                    "3",
                    "4",
                    "9",
                    "5",
                    "10",
                    "16",
                    "17",
                ],
                pon_cnn="gmsmyeloid_5.3_hg19_design_CNVkit_PON_reference_v1.cnn",
            ),
            QC=BalsamicConfigQC(
                adapter="AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT",
                min_seq_length="25",
            ),
            vcf={
                "manta": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "cnvkit": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="CNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted"],
                    workflow_solution=["BALSAMIC"],
                ),
                "vardict": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted"],
                    workflow_solution=["BALSAMIC"],
                ),
                "tnscope": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["wgs"],
                    workflow_solution=["Sentieon"],
                ),
                "dnascope": BalsamicVarCaller(
                    mutation="germline",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["Sentieon"],
                ),
                "tnhaplotyper": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["Sentieon"],
                ),
                "manta_germline": BalsamicVarCaller(
                    mutation="germline",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "haplotypecaller": BalsamicVarCaller(
                    mutation="germline",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted"],
                    workflow_solution=["BALSAMIC"],
                ),
                "TNscope_umi": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["single", "paired"],
                    sequencing_type=["targeted"],
                    workflow_solution=["Sentieon_umi"],
                ),
                "delly": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["wgs", "targeted"],
                    workflow_solution=["BALSAMIC"],
                ),
                "ascat": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="CNV",
                    analysis_type=["paired"],
                    sequencing_type=["wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
            },
            bioinfo_tools_version={
                "manta": ["1.6.0"],
                "bcftools": ["1.9", "1.11"],
                "tabix": ["0.2.6"],
                "samtools": ["1.9", "1.12", "1.11"],
                "sentieon": ["202010.02"],
                "delly": ["0.8.7"],
                "sambamba": ["0.6.6"],
                "mosdepth": ["0.2.9"],
                "ascatNgs": ["4.5.0"],
                "gatk": ["3.8"],
                "vardict": ["2019.06.04=pl526_0"],
                "bedtools": ["2.30.0"],
                "bwa": ["0.7.15"],
                "fastqc": ["0.11.9"],
                "picard": ["2.25.0"],
                "multiqc": ["1.11"],
                "fastp": ["0.20.1"],
                "csvkit": ["1.0.4"],
                "ensembl-vep": ["100.2"],
                "vcfanno": ["0.3.2"],
            },
        ),
        sample_metrics={
            "ACC00000A1": BalsamicTargetedQCMetrics(
                fold_80_base_penalty=1.683366,
                mean_insert_size=168.719145,
                median_target_coverage=1094.0,
                percent_duplication=0.6418730000000001,
                compare_predicted_to_given_sex="male",
                mean_target_coverage=1033.586714,
                pct_target_bases_50x=0.998543,
                pct_target_bases_100x=0.9976939999999999,
                pct_target_bases_250x=0.9859179999999999,
                pct_target_bases_500x=0.882644,
                pct_target_bases_1000x=0.56992,
                pct_off_bait=0.375377,
                gc_dropout=0.243943,
            ),
            "ACC00001A2": BalsamicTargetedQCMetrics(
                fold_80_base_penalty=1.686386,
                mean_insert_size=168.515498,
                median_target_coverage=964.0,
                percent_duplication=0.61773,
                compare_predicted_to_given_sex="male",
                mean_target_coverage=903.903117,
                pct_target_bases_50x=0.998473,
                pct_target_bases_100x=0.9972569999999999,
                pct_target_bases_250x=0.978843,
                pct_target_bases_500x=0.83066,
                pct_target_bases_1000x=0.461154,
                pct_off_bait=0.372064,
                gc_dropout=0.444905,
            ),
            "tga-case": BalsamicTargetedQCMetrics(),
        },
    )


@pytest.fixture
def expected_wgs_balsamic_analysis() -> BalsamicAnalysis:
    return BalsamicAnalysis(
        balsamic_config=BalsamicConfigJSON(
            analysis=BalsamicConfigAnalysis(
                case_id="wgs-case",
                analysis_type="paired",
                analysis_workflow="balsamic",
                sequencing_type="wgs",
                BALSAMIC_version="15.0.1",
                config_creation_date="2024-09-25 09:01",
            ),
            samples=[
                BalsamicConfigSample(
                    type=SampleType.TUMOR,
                    name="ACC0000A1",
                    fastq_info={
                        "2_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/2_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/2_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L002_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L002_R2_001.fastq.gz"),
                        },
                        "1_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/1_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/1_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L001_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L001_R2_001.fastq.gz"),
                        },
                        "4_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/4_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/4_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L004_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L004_R2_001.fastq.gz"),
                        },
                        "8_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/8_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/8_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L008_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L008_R2_001.fastq.gz"),
                        },
                        "6_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/6_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/6_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L006_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L006_R2_001.fastq.gz"),
                        },
                        "7_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/7_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/7_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L007_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L007_R2_001.fastq.gz"),
                        },
                        "5_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/5_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/5_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L005_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L005_R2_001.fastq.gz"),
                        },
                        "3_171015_22C3TNLT4_ACC0000A1_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/3_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/3_171015_22C3TNLT4_ACC0000A1_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_2/file_S418_L003_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_2/file_S418_L003_R2_001.fastq.gz"),
                        },
                    },
                ),
                BalsamicConfigSample(
                    type=SampleType.NORMAL,
                    name="ACC0000A2",
                    fastq_info={
                        "7_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/7_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/7_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L007_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L007_R2_001.fastq.gz"),
                        },
                        "4_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/4_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/4_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L004_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L004_R2_001.fastq.gz"),
                        },
                        "1_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/1_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/1_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L001_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L001_R2_001.fastq.gz"),
                        },
                        "8_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/8_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/8_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L008_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L008_R2_001.fastq.gz"),
                        },
                        "2_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/2_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/2_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L002_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L002_R2_001.fastq.gz"),
                        },
                        "1_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/1_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/1_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L001_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L001_R2_001.fastq.gz"),
                        },
                        "2_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/2_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/2_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L002_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L002_R2_001.fastq.gz"),
                        },
                        "5_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/5_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/5_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L005_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L005_R2_001.fastq.gz"),
                        },
                        "8_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/8_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/8_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L008_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L008_R2_001.fastq.gz"),
                        },
                        "6_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/6_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/6_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L006_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L006_R2_001.fastq.gz"),
                        },
                        "3_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/3_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/3_171015_22GJ3YLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_3/file_S9_L003_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_3/file_S9_L003_R2_001.fastq.gz"),
                        },
                        "7_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/7_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/7_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L007_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L007_R2_001.fastq.gz"),
                        },
                        "4_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/4_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/4_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L004_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L004_R2_001.fastq.gz"),
                        },
                        "6_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/6_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/6_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L006_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L006_R2_001.fastq.gz"),
                        },
                        "3_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/3_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/3_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L003_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L003_R2_001.fastq.gz"),
                        },
                        "5_171015_22GHNMLT3_ACC0000A2_XXXXXX_R": {
                            "fwd": Path(
                                "/dummy/fastq/5_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_1.fastq.gz"
                            ),
                            "rev": Path(
                                "/dummy/fastq/5_171015_22GHNMLT3_ACC0000A2_XXXXXX_R_2.fastq.gz"
                            ),
                            "fwd_resolved": Path("/dummy_4/file_S9_L005_R1_001.fastq.gz"),
                            "rev_resolved": Path("/dummy_4/file_S9_L005_R2_001.fastq.gz"),
                        },
                    },
                ),
            ],
            reference=BalsamicConfigReference(
                reference_genome=Path("/dummy_5/15.0.1/hg19/genome/human_g1k_v37.fasta"),
                reference_genome_version="hg19",
            ),
            panel=None,
            QC=BalsamicConfigQC(
                adapter="AATGATACGGCGACCACCGAGATCTACACTCTTTCCCTACACGACGCTCTTCCGATCT",
                min_seq_length="25",
            ),
            vcf={
                "vardict": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted"],
                    workflow_solution=["BALSAMIC"],
                ),
                "tnscope": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["wgs"],
                    workflow_solution=["Sentieon"],
                ),
                "dnascope": BalsamicVarCaller(
                    mutation="germline",
                    mutation_type="SNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["Sentieon"],
                ),
                "tnscope_umi": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SNV",
                    analysis_type=["single", "paired"],
                    sequencing_type=["targeted"],
                    workflow_solution=["Sentieon_umi"],
                ),
                "manta_germline": BalsamicVarCaller(
                    mutation="germline",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "manta": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "dellysv": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "cnvkit": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="CNV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted"],
                    workflow_solution=["BALSAMIC"],
                ),
                "ascat": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="CNV",
                    analysis_type=["paired"],
                    sequencing_type=["wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "dellycnv": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="CNV",
                    analysis_type=["single", "paired"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "tiddit": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["single", "paired"],
                    sequencing_type=["wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "cnvpytor": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="CNV",
                    analysis_type=["single"],
                    sequencing_type=["wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "igh_dux4": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["single", "paired"],
                    sequencing_type=["wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
                "svdb": BalsamicVarCaller(
                    mutation="somatic",
                    mutation_type="SV",
                    analysis_type=["paired", "single"],
                    sequencing_type=["targeted", "wgs"],
                    workflow_solution=["BALSAMIC"],
                ),
            },
            bioinfo_tools_version={
                "purecn": ["2.6.4"],
                "somalier": ["0.2.16"],
                "bcftools": ["1.10.2", "1.15.1", "1.9"],
                "bedtools": ["2.30.0"],
                "ensembl-vep": ["104.3"],
                "vcfanno": ["0.3.3"],
                "genmod": ["3.7.4"],
                "delly": ["1.0.3"],
                "bwa": ["0.7.17"],
                "gatk": ["4.4.0.0"],
                "samtools": ["1.9", "1.15.1"],
                "svdb": ["2.8.1"],
                "tabix": ["1.11", "0.2.6"],
                "tiddit": ["3.3.2"],
                "vardict": ["2019.06.04"],
                "cnvpytor": ["1.3.1"],
                "manta": ["1.6.0"],
                "cadd": ["1.6"],
                "ascatNgs": ["4.5.0"],
                "csvkit": ["1.0.7"],
                "fastp": ["0.23.2"],
                "fastqc": ["0.11.9"],
                "multiqc": ["1.12"],
                "picard": ["2.27.1"],
                "vcf2cytosure": ["0.8.1"],
                "cnvkit": ["0.9.10"],
                "mosdepth": ["0.3.3"],
                "sambamba": ["0.8.2"],
            },
        ),
        sample_metrics={
            "ACC00000A2": BalsamicWGSQCMetrics(
                fold_80_base_penalty=1.224108,
                mean_insert_size=347.069842,
                median_target_coverage=30.0,
                percent_duplication=0.128775,
                compare_predicted_to_given_sex="female",
                pct_15x=0.966635,
                pct_30x=0.5082489999999999,
                pct_60x=0.2788,
                pct_100x=0.11130000000000001,
                pct_pf_reads_improper_pairs=0.14465000000000001,
            ),
            "ACC00000A1": BalsamicWGSQCMetrics(
                fold_80_base_penalty=1.323066,
                mean_insert_size=359.345997,
                median_target_coverage=111.0,
                percent_duplication=0.12004900000000001,
                compare_predicted_to_given_sex="female",
                pct_15x=0.979451,
                pct_30x=0.976069,
                pct_60x=0.941892,
                pct_100x=0.646318,
                pct_pf_reads_improper_pairs=1.4569,
            ),
            "wgs-case": BalsamicWGSQCMetrics(),
        },
    )


def test_parse_analysis_tga(
    cg_context: CGConfig,
    balsamic_tga_config_raw: dict,
    balsamic_tga_metrics_raw: list[dict],
    expected_tga_balsamic_analysis: BalsamicAnalysis,
):
    """Tests BALSAMIC analysis instance creation"""

    # GIVEN a config and metrics dictionaries and a BALSAMIC analysis API
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context, Workflow.BALSAMIC)

    # WHEN instantiating a BALSAMIC analysis object
    balsamic_analysis = balsamic_analysis_api.parse_analysis(
        balsamic_tga_config_raw, balsamic_tga_metrics_raw
    )

    # THEN the Balsamic analysis is as expected
    assert balsamic_analysis.model_dump() == expected_tga_balsamic_analysis.model_dump()


def test_parse_analysis_wgs(
    cg_context: CGConfig,
    balsamic_wgs_config_raw: dict,
    balsamic_wgs_metrics_raw: list[dict],
    expected_wgs_balsamic_analysis: BalsamicAnalysis,
):
    """Tests BALSAMIC analysis instance creation"""

    # GIVEN a config and metrics dictionaries and a BALSAMIC analysis API
    balsamic_analysis_api = BalsamicAnalysisAPI(cg_context, Workflow.BALSAMIC)

    # WHEN instantiating a BALSAMIC analysis object
    balsamic_analysis = balsamic_analysis_api.parse_analysis(
        balsamic_wgs_config_raw, balsamic_wgs_metrics_raw
    )

    # THEN the Balsamic analysis is as expected
    assert balsamic_analysis.model_dump() == expected_wgs_balsamic_analysis.model_dump()
