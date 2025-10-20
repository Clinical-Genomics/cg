import pytest

from cg.models.cg_config import BalsamicConfig


@pytest.fixture
def expected_tgs_normal_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_normal"
    )


@pytest.fixture
def expected_tgs_paired_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "  # TODO are there 2 versions of this?
        f"--normal-sample-name sample_normal "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--soft-filter-normal "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


@pytest.fixture
def expected_tgs_tumour_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


@pytest.fixture
def expected_wes_normal_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--exome "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_normal"
    )


@pytest.fixture
def expected_wes_paired_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--exome "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--normal-sample-name sample_normal "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--soft-filter-normal "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


@pytest.fixture
def expected_wes_tumour_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--exome "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-version hg19 "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--panel-bed {cg_balsamic_config.bed_path}/bed_version.bed "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_1"
    )


@pytest.fixture
def expected_wgs_paired_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--artefact-sv-observations {cg_balsamic_config.loqusdb_artefact_sv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-interval {cg_balsamic_config.genome_interval_path} "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {cg_balsamic_config.gens_coverage_female_path} "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--normal-sample-name sample_normal "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_tumour"
    )


@pytest.fixture
def expected_wgs_tumour_only_command(cg_balsamic_config: BalsamicConfig) -> str:
    return (
        f"{cg_balsamic_config.conda_binary} "
        f"run --name {cg_balsamic_config.conda_env} "
        f"{cg_balsamic_config.binary_path} config case "
        f"--analysis-dir {cg_balsamic_config.root} "
        f"--analysis-workflow balsamic "
        f"--artefact-snv-observations {cg_balsamic_config.loqusdb_artefact_snv} "
        f"--artefact-sv-observations {cg_balsamic_config.loqusdb_artefact_sv} "
        f"--balsamic-cache {cg_balsamic_config.balsamic_cache} "
        f"--cadd-annotations {cg_balsamic_config.cadd_path} "
        f"--cancer-germline-snv-observations {cg_balsamic_config.loqusdb_cancer_germline_snv} "
        f"--cancer-somatic-snv-observations {cg_balsamic_config.loqusdb_cancer_somatic_snv} "
        f"--cancer-somatic-sv-observations {cg_balsamic_config.loqusdb_cancer_somatic_sv} "
        f"--case-id case_1 "
        f"--clinical-snv-observations {cg_balsamic_config.loqusdb_clinical_snv} "
        f"--clinical-sv-observations {cg_balsamic_config.loqusdb_clinical_sv} "
        f"--fastq-path {cg_balsamic_config.root}/case_1/fastq "
        f"--gender female "
        f"--genome-interval {cg_balsamic_config.genome_interval_path} "
        f"--genome-version hg19 "
        f"--gens-coverage-pon {cg_balsamic_config.gens_coverage_female_path} "
        f"--gnomad-min-af5 {cg_balsamic_config.gnomad_af5_path} "
        f"--sentieon-install-dir {cg_balsamic_config.sentieon_licence_path} "
        f"--sentieon-license {cg_balsamic_config.sentieon_licence_server} "
        f"--swegen-snv {cg_balsamic_config.swegen_snv} "
        f"--swegen-sv {cg_balsamic_config.swegen_sv} "
        f"--tumor-sample-name sample_1"
    )
