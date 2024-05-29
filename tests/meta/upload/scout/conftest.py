"""Fixtures for the upload Scout API tests."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Generator

import pytest
from housekeeper.store.models import Version

from cg.constants import DataDelivery, Workflow
from cg.constants.constants import FileFormat, PrepCategory
from cg.constants.housekeeper_tags import HK_DELIVERY_REPORT_TAG
from cg.constants.pedigree import Pedigree
from cg.constants.scout import UploadTrack
from cg.constants.sequencing import SequencingMethod
from cg.constants.subject import PhenotypeStatus
from cg.io.controller import ReadFile
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.models.cg_config import CGConfig
from cg.models.scout.scout_load_config import MipLoadConfig
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store

# Mocks
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.mip_analysis_mock import MockMipAnalysis
from tests.mocks.scout import MockScoutAPI
from tests.store_helpers import StoreHelpers

LOG = logging.getLogger(__name__)


@pytest.fixture
def rna_case_id() -> str:
    """Return a rna case id."""
    return "affirmativecat"


@pytest.fixture
def dna_case_id(case_id: str) -> str:
    """Return a DNA case id."""
    return case_id


@pytest.fixture
def rna_sample_son_id() -> str:
    """Return a son RNA sample id."""
    return "rna_son"


@pytest.fixture
def rna_sample_daughter_id() -> str:
    """Return a daughter RNA sample id."""
    return "rna_daughter"


@pytest.fixture
def rna_sample_mother_id() -> str:
    """Return a mother RNA sample id."""
    return "rna_mother"


@pytest.fixture
def rna_sample_father_id() -> str:
    """Return a father RNA sample id."""
    return "rna_father"


@pytest.fixture
def dna_sample_son_id() -> str:
    """Return a son DNA sample id."""
    return "dna_son"


@pytest.fixture
def dna_sample_daughter_id() -> str:
    """Return a daughter DNA sample id."""
    return "dna_daughter"


@pytest.fixture
def dna_sample_mother_id() -> str:
    """Return a mother DNA sample id."""
    return "dna_mother"


@pytest.fixture
def dna_sample_father_id() -> str:
    """Return a father DNA sample id."""
    return "dna_father"


@pytest.fixture
def another_rna_sample_id() -> str:
    """Return another RNA sample id."""
    return "another_rna_sample_id"


@pytest.fixture
def rna_store(
    base_store: Store,
    helpers: StoreHelpers,
    rna_case_id: str,
    dna_case_id: str,
    rna_sample_son_id: str,
    rna_sample_daughter_id: str,
    rna_sample_father_id: str,
    rna_sample_mother_id: str,
    dna_sample_son_id: str,
    dna_sample_daughter_id: str,
    dna_sample_father_id: str,
    dna_sample_mother_id: str,
) -> Store:
    """Populate store with an RNA case that is connected to a DNA case via subject ID."""

    store: Store = base_store

    # an existing RNA case with related sample
    rna_case = helpers.ensure_case(
        store=store,
        case_name="rna_case",
        customer=helpers.ensure_customer(store=store),
        data_analysis=Workflow.MIP_RNA,
        data_delivery=DataDelivery.SCOUT,
    )
    rna_case.internal_id = rna_case_id

    rna_sample_son = helpers.add_sample(
        store=store,
        application_type=SequencingMethod.WTS,
        name=rna_sample_son_id,
        subject_id="son",
    )
    rna_sample_daughter = helpers.add_sample(
        store=store,
        application_type=SequencingMethod.WTS,
        name=rna_sample_daughter_id,
        subject_id="daughter",
    )
    rna_sample_mother = helpers.add_sample(
        store=store,
        application_type=SequencingMethod.WTS,
        name=rna_sample_mother_id,
        subject_id=Pedigree.MOTHER,
    )
    rna_sample_father = helpers.add_sample(
        store=store,
        application_type=SequencingMethod.WTS,
        name=rna_sample_father_id,
        subject_id=Pedigree.FATHER,
    )
    helpers.add_relationship(
        store=store,
        sample=rna_sample_son,
        case=rna_case,
        mother=rna_sample_mother,
        father=rna_sample_father,
        status=PhenotypeStatus.AFFECTED,
    )
    helpers.add_relationship(
        store=store,
        sample=rna_sample_daughter,
        case=rna_case,
        mother=rna_sample_mother,
        father=rna_sample_father,
        status=PhenotypeStatus.UNAFFECTED,
    )
    helpers.add_relationship(
        store=store, sample=rna_sample_mother, case=rna_case, status=PhenotypeStatus.UNAFFECTED
    )
    helpers.add_relationship(
        store=store, sample=rna_sample_father, case=rna_case, status=PhenotypeStatus.AFFECTED
    )

    for link in rna_case.links:
        link.sample.internal_id = link.sample.name

    # an existing DNA case with related sample
    dna_case = helpers.ensure_case(
        store=store,
        case_name="dna_case",
        customer=helpers.ensure_customer(store=store),
        data_analysis=Workflow.MIP_DNA,
        data_delivery=DataDelivery.SCOUT,
    )
    dna_case.internal_id = dna_case_id

    dna_sample_son = helpers.add_sample(
        store=store,
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
        name=dna_sample_son_id,
        subject_id="son",
    )
    dna_sample_daughter = helpers.add_sample(
        store=store,
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
        name=dna_sample_daughter_id,
        subject_id="daughter",
    )
    dna_sample_mother = helpers.add_sample(
        store=store,
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
        name=dna_sample_mother_id,
        subject_id=Pedigree.MOTHER,
    )
    dna_sample_father = helpers.add_sample(
        store=store,
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
        name=dna_sample_father_id,
        subject_id=Pedigree.FATHER,
    )
    helpers.add_relationship(
        store=store,
        sample=dna_sample_son,
        case=dna_case,
        mother=dna_sample_mother,
        father=dna_sample_father,
        status=PhenotypeStatus.AFFECTED,
    )
    helpers.add_relationship(
        store=store,
        sample=dna_sample_daughter,
        case=dna_case,
        mother=dna_sample_mother,
        father=dna_sample_father,
        status=PhenotypeStatus.UNAFFECTED,
    )
    helpers.add_relationship(
        store=store, sample=dna_sample_mother, case=dna_case, status=PhenotypeStatus.UNAFFECTED
    )
    helpers.add_relationship(
        store=store, sample=dna_sample_father, case=dna_case, status=PhenotypeStatus.AFFECTED
    )

    for link in dna_case.links:
        link.sample.internal_id = link.sample.name

    helpers.add_analysis(store=store, case=dna_case, uploaded_at=datetime.now())

    store.session.commit()
    return store


@pytest.fixture(name="lims_family")
def lims_family(fixtures_dir) -> dict:
    """Returns a LIMS-like case of samples."""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(fixtures_dir, "report", "lims_family.json")
    )


@pytest.fixture(name="lims_samples")
def lims_samples(lims_family: dict) -> list[dict]:
    """Returns the samples of a LIMS case."""
    return lims_family["samples"]


@pytest.fixture(scope="function")
def mip_dna_analysis_hk_bundle_data(
    case_id: str,
    timestamp: datetime,
    mip_dna_analysis_dir: Path,
    sample_id: str,
    snv_vcf_file: str,
    sv_vcf_file: str,
    snv_research_vcf_file: str,
    sv_research_vcf_file: str,
    delivery_report_html: Path,
) -> dict:
    """Return MIP DNA bundle data for Housekeeper."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": Path(mip_dna_analysis_dir, snv_vcf_file).as_posix(),
                "archive": False,
                "tags": ["vcf-snv-clinical"],
            },
            {
                "path": Path(mip_dna_analysis_dir, sv_vcf_file).as_posix(),
                "archive": False,
                "tags": ["vcf-sv-clinical"],
            },
            {
                "path": Path(mip_dna_analysis_dir, snv_research_vcf_file).as_posix(),
                "archive": False,
                "tags": ["vcf-snv-research"],
            },
            {
                "path": Path(mip_dna_analysis_dir, sv_research_vcf_file).as_posix(),
                "archive": False,
                "tags": ["vcf-sv-research"],
            },
            {
                "path": Path(mip_dna_analysis_dir, "str.vcf").as_posix(),
                "archive": False,
                "tags": ["vcf-str"],
            },
            {
                "path": Path(mip_dna_analysis_dir, "smn.vcf").as_posix(),
                "archive": False,
                "tags": ["smn-calling"],
            },
            {
                "path": Path(mip_dna_analysis_dir, "adm1.cram").as_posix(),
                "archive": False,
                "tags": ["cram", sample_id],
            },
            {
                "path": Path(mip_dna_analysis_dir, "report.pdf").as_posix(),
                "archive": False,
                "tags": ["delivery-report"],
            },
            {
                "path": Path(mip_dna_analysis_dir, "adm1.mt.bam").as_posix(),
                "archive": False,
                "tags": ["bam-mt", sample_id],
            },
            {
                "path": Path(mip_dna_analysis_dir, "vcf2cytosure.txt").as_posix(),
                "archive": False,
                "tags": ["vcf2cytosure", sample_id],
            },
            {
                "path": Path(mip_dna_analysis_dir, "multiqc.html").as_posix(),
                "archive": False,
                "tags": ["multiqc-html", sample_id],
            },
        ],
    }


@pytest.fixture(scope="function")
def mip_rna_analysis_hk_bundle_data(
    rna_case_id: str,
    timestamp: datetime,
    mip_dna_analysis_dir: Path,
    rna_sample_son_id: str,
    rna_sample_daughter_id: str,
    rna_sample_mother_id: str,
    rna_sample_father_id: str,
) -> dict:
    """Return MIP RNA bundle data for Housekeeper."""

    files: list[dict] = [
        {
            "path": Path(mip_dna_analysis_dir, f"{rna_case_id}.cram").as_posix(),
            "archive": False,
            "tags": ["cram", rna_case_id],
        },
        {
            "path": Path(mip_dna_analysis_dir, f"{rna_case_id}_report.selected.pdf").as_posix(),
            "archive": False,
            "tags": ["fusion", "pdf", "clinical", rna_case_id],
        },
        {
            "path": Path(mip_dna_analysis_dir, f"{rna_case_id}_report.pdf").as_posix(),
            "archive": False,
            "tags": ["fusion", "pdf", "research", rna_case_id],
        },
    ]
    for sample_id in [
        rna_sample_son_id,
        rna_sample_daughter_id,
        rna_sample_mother_id,
        rna_sample_father_id,
    ]:
        files.extend(
            [
                {
                    "path": Path(
                        mip_dna_analysis_dir, f"{sample_id}_lanes_1_star_sorted_sj.bigWig"
                    ).as_posix(),
                    "archive": False,
                    "tags": ["coverage", "bigwig", "scout", sample_id],
                },
                {
                    "path": Path(
                        mip_dna_analysis_dir, f"{sample_id}_lanes_1234_star_sorted_sj.bed.gz.tbi"
                    ).as_posix(),
                    "archive": False,
                    "tags": ["bed", "scout", "junction", sample_id],
                },
            ]
        )

    return {
        "name": rna_case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": files,
    }


@pytest.fixture(scope="function")
def balsamic_analysis_hk_bundle_data(
    case_id: str,
    timestamp: datetime,
    balsamic_wgs_analysis_dir: Path,
    sample_id: str,
    snv_vcf_file: str,
    sv_vcf_file: str,
) -> dict:
    """Return Balsamic bundle data for Housekeeper,"""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": Path(balsamic_wgs_analysis_dir, snv_vcf_file).as_posix(),
                "archive": False,
                "tags": ["vcf-snv-clinical"],
            },
            {
                "path": Path(balsamic_wgs_analysis_dir, sv_vcf_file).as_posix(),
                "archive": False,
                "tags": ["vcf-sv-clinical"],
            },
            {
                "path": Path(balsamic_wgs_analysis_dir, "umi.sv.vcf").as_posix(),
                "archive": False,
                "tags": ["vcf-umi-snv-clinical"],
            },
            {
                "path": Path(balsamic_wgs_analysis_dir, "adm1.cram").as_posix(),
                "archive": False,
                "tags": ["cram", sample_id],
            },
            {
                "path": Path(balsamic_wgs_analysis_dir, "ascat.output.pdf").as_posix(),
                "archive": False,
                "tags": ["ascatngs", "visualization", sample_id],
            },
            {
                "path": Path(balsamic_wgs_analysis_dir, "coverage_qc_report.pdf").as_posix(),
                "archive": False,
                "tags": ["delivery-report"],
            },
        ],
    }


@pytest.fixture(scope="function")
def rnafusion_analysis_hk_bundle_data(
    case_id: str, timestamp: datetime, rnafusion_analysis_dir: Path, delivery_report_html: Path
) -> dict:
    """Get some bundle data for housekeeper."""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(rnafusion_analysis_dir / "multiqc.html"),
                "archive": False,
                "tags": ["multiqc-html", "rna"],
            },
            {
                "path": Path(rnafusion_analysis_dir, "rnafusion_report.html").as_posix(),
                "archive": False,
                "tags": ["fusionreport", "research"],
            },
            {
                "path": delivery_report_html.as_posix(),
                "archive": False,
                "tags": [HK_DELIVERY_REPORT_TAG],
            },
        ],
    }


@pytest.fixture
def balsamic_analysis_hk_version(
    housekeeper_api: MockHousekeeperAPI, balsamic_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return Housekeeper version for a Balsamic bundle."""
    return helpers.ensure_hk_version(housekeeper_api, balsamic_analysis_hk_bundle_data)


@pytest.fixture
def mip_dna_analysis_hk_version(
    housekeeper_api: MockHousekeeperAPI, mip_dna_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return Housekeeper version for a MIP DNA bundle."""
    return helpers.ensure_hk_version(housekeeper_api, mip_dna_analysis_hk_bundle_data)


@pytest.fixture
def mip_dna_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, mip_dna_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a Housekeeper API populated with MIP DNA analysis files."""
    helpers.ensure_hk_version(housekeeper_api, mip_dna_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture
def mip_rna_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, mip_rna_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a Housekeeper API populated with MIP RNA analysis files."""
    helpers.ensure_hk_version(housekeeper_api, mip_rna_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture
def balsamic_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, balsamic_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a Housekeeper API populated with Balsamic analysis files."""
    helpers.ensure_hk_version(housekeeper_api, balsamic_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture
def rnafusion_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, rnafusion_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a housekeeper api populated with some rnafusion analysis files"""
    helpers.ensure_hk_version(housekeeper_api, rnafusion_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture
def mip_dna_analysis(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers: StoreHelpers
) -> Analysis:
    """Return a MIP DNA analysis object."""
    helpers.add_synopsis_to_case(store=analysis_store_trio, case_id=case_id)
    case: Case = analysis_store_trio.get_case_by_internal_id(internal_id=case_id)
    analysis: Analysis = helpers.add_analysis(
        store=analysis_store_trio,
        case=case,
        started_at=timestamp,
        completed_at=timestamp,
        workflow=Workflow.MIP_DNA,
    )
    for link in case.links:
        helpers.add_phenotype_groups_to_sample(
            store=analysis_store_trio, sample_id=link.sample.internal_id
        )
        helpers.add_phenotype_terms_to_sample(
            store=analysis_store_trio, sample_id=link.sample.internal_id
        )
        helpers.add_subject_id_to_sample(
            store=analysis_store_trio, sample_id=link.sample.internal_id
        )
    return analysis


@pytest.fixture
def balsamic_analysis_obj(analysis_obj: Analysis) -> Analysis:
    """Return a Balsamic analysis object."""
    analysis_obj.workflow = Workflow.BALSAMIC
    for link_object in analysis_obj.case.links:
        link_object.sample.application_version.application.prep_category = (
            PrepCategory.WHOLE_EXOME_SEQUENCING
        )
        link_object.case.data_analysis = Workflow.BALSAMIC
    return analysis_obj


@pytest.fixture
def balsamic_umi_analysis_obj(analysis_obj: Analysis) -> Analysis:
    """Return a Balsamic UMI analysis object."""
    analysis_obj.workflow = Workflow.BALSAMIC_UMI
    for link_object in analysis_obj.case.links:
        link_object.sample.application_version.application.prep_category = (
            PrepCategory.WHOLE_EXOME_SEQUENCING
        )
        link_object.case.data_analysis = Workflow.BALSAMIC_UMI

    return analysis_obj


@pytest.fixture
def rnafusion_analysis_obj(analysis_obj: Analysis) -> Analysis:
    """Return a RNAfusion analysis object."""
    analysis_obj.workflow = Workflow.RNAFUSION
    for link_object in analysis_obj.case.links:
        link_object.sample.application_version.application.prep_category = (
            PrepCategory.WHOLE_TRANSCRIPTOME_SEQUENCING
        )
        link_object.case.data_analysis = Workflow.RNAFUSION
        link_object.case.panels = None
    return analysis_obj


@pytest.fixture
def mip_config_builder(
    mip_dna_analysis_hk_version: Version,
    mip_dna_analysis: Analysis,
    lims_api: MockLimsAPI,
    mip_analysis_api: MockMipAnalysis,
    madeline_api: MockMadelineAPI,
) -> MipConfigBuilder:
    """Return a MIP config builder."""
    return MipConfigBuilder(
        hk_version_obj=mip_dna_analysis_hk_version,
        analysis_obj=mip_dna_analysis,
        lims_api=lims_api,
        mip_analysis_api=mip_analysis_api,
        madeline_api=madeline_api,
    )


@pytest.fixture
def balsamic_config_builder(
    balsamic_analysis_hk_version: Version,
    balsamic_analysis_obj: Analysis,
    lims_api: MockLimsAPI,
) -> BalsamicConfigBuilder:
    """Return a Balsamic config builder."""
    return BalsamicConfigBuilder(
        hk_version_obj=balsamic_analysis_hk_version,
        analysis_obj=balsamic_analysis_obj,
        lims_api=lims_api,
    )


@pytest.fixture
def mip_load_config(
    mip_dna_analysis_dir: Path,
    case_id: str,
    customer_id: str,
    snv_vcf_file: str,
    delivery_report_html: Path,
) -> MipLoadConfig:
    """Return a valid MIP load_config."""
    return MipLoadConfig(
        owner=customer_id,
        family=case_id,
        vcf_snv=Path(mip_dna_analysis_dir, snv_vcf_file).as_posix(),
        track=UploadTrack.RARE_DISEASE.value,
        delivery_report=delivery_report_html.as_posix(),
    )


@pytest.fixture
def lims_api(lims_samples: list[dict]) -> MockLimsAPI:
    """Return a LIMS API."""
    return MockLimsAPI(samples=lims_samples)


@pytest.fixture
def mip_analysis_api(cg_context: CGConfig) -> MockMipAnalysis:
    """Return a MIP analysis API."""
    return MockMipAnalysis(config=cg_context, workflow=Workflow.MIP_DNA)


@pytest.fixture
def upload_scout_api(
    cg_context: CGConfig,
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: list[dict],
    housekeeper_api: MockHousekeeperAPI,
    store: Store,
) -> UploadScoutAPI:
    """Return upload Scout API."""
    analysis_mock = MockMipAnalysis(config=cg_context, workflow=Workflow.MIP_DNA)
    lims_api = MockLimsAPI(samples=lims_samples)

    return UploadScoutAPI(
        hk_api=housekeeper_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )


@pytest.fixture
def upload_mip_analysis_scout_api(
    cg_context: CGConfig,
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: list[dict],
    mip_dna_analysis_hk_api: MockHousekeeperAPI,
    store: Store,
) -> Generator[UploadScoutAPI, None, None]:
    """Return MIP upload Scout API."""
    analysis_mock = MockMipAnalysis(config=cg_context, workflow=Workflow.MIP_DNA)
    lims_api = MockLimsAPI(samples=lims_samples)

    yield UploadScoutAPI(
        hk_api=mip_dna_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )


@pytest.fixture
def upload_balsamic_analysis_scout_api(
    cg_context: CGConfig,
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: list[dict],
    balsamic_analysis_hk_api: MockHousekeeperAPI,
    store: Store,
) -> Generator[UploadScoutAPI, None, None]:
    """Return Balsamic upload Scout API."""
    analysis_mock = MockMipAnalysis(config=cg_context, workflow=Workflow.MIP_DNA)
    lims_api = MockLimsAPI(samples=lims_samples)

    yield UploadScoutAPI(
        hk_api=balsamic_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )


@pytest.fixture
def rna_dna_sample_case_map(
    rna_sample_son_id: str,
    rna_store: Store,
    upload_scout_api: UploadScoutAPI,
) -> dict[str, list[str]]:
    """Return a valid RNA-DNA case map."""
    rna_sample: Sample = rna_store.get_sample_by_internal_id(internal_id=rna_sample_son_id)

    # WHEN adding the RNA sample rna_dna_case_map
    rna_dna_sample_case_map: dict[str, dict[str, list[str]]] = {}
    upload_scout_api._map_dna_samples_related_to_rna_sample(
        rna_sample=rna_sample, rna_dna_sample_case_map=rna_dna_sample_case_map
    )

    return rna_dna_sample_case_map


@pytest.fixture
def upload_rnafusion_analysis_scout_api(
    cg_context: CGConfig,
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: list[dict],
    rnafusion_analysis_hk_api: MockHousekeeperAPI,
    store: Store,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api."""
    analysis_mock = MockMipAnalysis(config=cg_context, workflow=Workflow.MIP_DNA)
    lims_api = MockLimsAPI(samples=lims_samples)

    _api = UploadScoutAPI(
        hk_api=rnafusion_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )

    return _api
