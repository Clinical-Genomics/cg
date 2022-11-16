"""Fixtures for the upload scout api tests"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List

import pytest
from cg.constants import Pipeline, DataDelivery
from cg.constants.constants import FileFormat
from cg.constants.sequencing import SequencingMethod
from cg.io.controller import ReadFile
from cg.meta.upload.scout.balsamic_config_builder import BalsamicConfigBuilder
from cg.meta.upload.scout.mip_config_builder import MipConfigBuilder
from cg.meta.upload.scout.uploadscoutapi import UploadScoutAPI
from cg.models.scout.scout_load_config import MipLoadConfig
from cg.store import Store, models
from housekeeper.store import models as hk_models

# Mocks
from tests.mocks.hk_mock import MockHousekeeperAPI
from tests.mocks.limsmock import MockLimsAPI
from tests.mocks.madeline import MockMadelineAPI
from tests.mocks.scout import MockScoutAPI
from tests.store_helpers import StoreHelpers
from tests.mocks.mip_analysis_mock import MockMipAnalysis

LOG = logging.getLogger(__name__)


@pytest.fixture(name="rna_case_id")
def fixture_rna_case_id() -> str:
    """Return a rna case id"""
    return "affirmativecat"


@pytest.fixture(name="dna_case_id")
def fixture_dna_case_id(case_id) -> str:
    """Return a dna case id"""
    return case_id


@pytest.fixture(name="rna_sample_son_id")
def fixture_rna_sample_son_id() -> str:
    """Return a rna sample id"""
    return "rna_son"


@pytest.fixture(name="rna_sample_daughter_id")
def fixture_rna_sample_daughter_id() -> str:
    """Return a rna sample id"""
    return "rna_daughter"


@pytest.fixture(name="rna_sample_mother_id")
def fixture_rna_sample_mother_id() -> str:
    """Return a rna sample id"""
    return "rna_mother"


@pytest.fixture(name="rna_sample_father_id")
def fixture_rna_sample_father_id() -> str:
    """Return a rna sample id"""
    return "rna_father"


@pytest.fixture(name="dna_sample_son_id")
def fixture_dna_sample_son_id() -> str:
    """Return a rna sample id"""
    return "dna_son"


@pytest.fixture(name="dna_sample_daughter_id")
def fixture_dna_sample_daughter_id() -> str:
    """Return a rna sample id"""
    return "dna_daughter"


@pytest.fixture(name="dna_sample_mother_id")
def fixture_dna_sample_mother_id() -> str:
    """Return a rna sample id"""
    return "dna_mother"


@pytest.fixture(name="dna_sample_father_id")
def fixture_dna_sample_father_id() -> str:
    """Return a rna sample id"""
    return "dna_father"


@pytest.fixture(name="another_sample_id")
def fixture_another_sample_id() -> str:
    """Return another sample id."""
    return "another_sample_id"


@pytest.fixture(name="another_rna_sample_id")
def fixture_another_rna_sample_id() -> str:
    """Return another RNA sample id."""
    return "another_rna_sample_id"


@pytest.fixture(name="rna_store")
def fixture_rna_store(
    base_store: Store,
    helpers: StoreHelpers,
    rna_case_id: str,
    dna_case_id: str,
) -> Store:
    """Populate store with an rna case that is connected to a dna case via sample.subject_id"""

    store: Store = base_store

    # an existing RNA case with related sample
    rna_case = helpers.ensure_case(
        store=store,
        name="rna_case",
        customer=helpers.ensure_customer(store=store),
        data_analysis=Pipeline.MIP_RNA,
        data_delivery=DataDelivery.SCOUT,
    )
    rna_case.internal_id = rna_case_id

    rna_sample_son = helpers.add_sample(
        store=store,
        name="rna_son",
        subject_id="son",
        application_type=SequencingMethod.WTS,
    )
    rna_sample_daughter = helpers.add_sample(
        store=store,
        name="rna_daughter",
        subject_id="daughter",
        application_type=SequencingMethod.WTS,
    )
    rna_sample_mother = helpers.add_sample(
        store=store,
        name="rna_mother",
        subject_id="mother",
        application_type=SequencingMethod.WTS,
    )
    rna_sample_father = helpers.add_sample(
        store=store,
        name="rna_father",
        subject_id="father",
        application_type=SequencingMethod.WTS,
    )
    helpers.add_relationship(
        store=store,
        sample=rna_sample_son,
        case=rna_case,
        mother=rna_sample_mother,
        father=rna_sample_father,
        status="affected",
    )
    helpers.add_relationship(
        store=store,
        sample=rna_sample_daughter,
        case=rna_case,
        mother=rna_sample_mother,
        father=rna_sample_father,
        status="unaffected",
    )
    helpers.add_relationship(
        store=store, sample=rna_sample_mother, case=rna_case, status="unaffected"
    )
    helpers.add_relationship(
        store=store, sample=rna_sample_father, case=rna_case, status="affected"
    )

    for link in rna_case.links:
        link.sample.internal_id = link.sample.name

    # an existing DNA case with related sample
    dna_case = helpers.ensure_case(
        store=store,
        name="dna_case",
        customer=helpers.ensure_customer(store=store),
        data_analysis=Pipeline.MIP_DNA,
        data_delivery=DataDelivery.SCOUT,
    )
    dna_case.internal_id = dna_case_id

    dna_sample_son = helpers.add_sample(
        store=store,
        name="dna_son",
        subject_id="son",
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
    )
    dna_sample_daughter = helpers.add_sample(
        store=store,
        name="dna_daughter",
        subject_id="daughter",
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
    )
    dna_sample_mother = helpers.add_sample(
        store=store,
        name="dna_mother",
        subject_id="mother",
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
    )
    dna_sample_father = helpers.add_sample(
        store=store,
        name="dna_father",
        subject_id="father",
        application_tag=SequencingMethod.WGS,
        application_type=SequencingMethod.WGS,
    )
    helpers.add_relationship(
        store=store,
        sample=dna_sample_son,
        case=dna_case,
        mother=dna_sample_mother,
        father=dna_sample_father,
        status="affected",
    )
    helpers.add_relationship(
        store=store,
        sample=dna_sample_daughter,
        case=dna_case,
        mother=dna_sample_mother,
        father=dna_sample_father,
        status="unaffected",
    )
    helpers.add_relationship(
        store=store, sample=dna_sample_mother, case=dna_case, status="unaffected"
    )
    helpers.add_relationship(
        store=store, sample=dna_sample_father, case=dna_case, status="affected"
    )

    for link in dna_case.links:
        link.sample.internal_id = link.sample.name

    store.commit()
    return store


@pytest.fixture(name="lims_family")
def fixture_lims_family(fixtures_dir) -> dict:
    """Returns a lims-like case of samples"""
    return ReadFile.get_content_from_file(
        file_format=FileFormat.JSON, file_path=Path(fixtures_dir, "report", "lims_family.json")
    )


@pytest.fixture(name="lims_samples")
def fixture_lims_samples(lims_family: dict) -> List[dict]:
    """Returns the samples of a lims case"""
    return lims_family["samples"]


@pytest.fixture(scope="function", name="mip_dna_analysis_hk_bundle_data")
def fixture_mip_dna_analysis_hk_bundle_data(
    case_id: str, timestamp: datetime, mip_dna_analysis_dir: Path, sample_id: str
) -> dict:
    """Get some bundle data for housekeeper"""
    data = {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(mip_dna_analysis_dir / "snv.vcf"),
                "archive": False,
                "tags": ["vcf-snv-clinical"],
            },
            {
                "path": str(mip_dna_analysis_dir / "sv.vcf"),
                "archive": False,
                "tags": ["vcf-sv-clinical"],
            },
            {
                "path": str(mip_dna_analysis_dir / "snv_research.vcf"),
                "archive": False,
                "tags": ["vcf-snv-research"],
            },
            {
                "path": str(mip_dna_analysis_dir / "sv_research.vcf"),
                "archive": False,
                "tags": ["vcf-sv-research"],
            },
            {
                "path": str(mip_dna_analysis_dir / "str.vcf"),
                "archive": False,
                "tags": ["vcf-str"],
            },
            {
                "path": str(mip_dna_analysis_dir / "smn.vcf"),
                "archive": False,
                "tags": ["smn-calling"],
            },
            {
                "path": str(mip_dna_analysis_dir / "adm1.cram"),
                "archive": False,
                "tags": ["cram", sample_id],
            },
            {
                "path": str(mip_dna_analysis_dir / "report.pdf"),
                "archive": False,
                "tags": ["delivery-report"],
            },
            {
                "path": str(mip_dna_analysis_dir / "adm1.mt.bam"),
                "archive": False,
                "tags": ["bam-mt", sample_id],
            },
            {
                "path": str(mip_dna_analysis_dir / "vcf2cytosure.txt"),
                "archive": False,
                "tags": ["vcf2cytosure", sample_id],
            },
            {
                "path": str(mip_dna_analysis_dir / "multiqc.html"),
                "archive": False,
                "tags": ["multiqc-html", sample_id],
            },
        ],
    }
    return data


@pytest.fixture(scope="function", name="mip_rna_analysis_hk_bundle_data")
def fixture_mip_rna_analysis_hk_bundle_data(
    rna_case_id: str,
    timestamp: datetime,
    mip_dna_analysis_dir: Path,
    rna_sample_son_id: str,
    rna_sample_daughter_id: str,
    rna_sample_mother_id: str,
    rna_sample_father_id: str,
) -> dict:
    """Get some bundle data for housekeeper"""

    files: [dict] = [
        {
            "path": str(mip_dna_analysis_dir / f"{rna_case_id}_report.selected.pdf"),
            "archive": False,
            "tags": ["fusion", "pdf", "clinical", rna_case_id],
        },
        {
            "path": str(mip_dna_analysis_dir / f"{rna_case_id}_report.pdf"),
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
                    "path": str(
                        mip_dna_analysis_dir / f"{sample_id}_lanes_1_star_sorted_sj.bigWig"
                    ),
                    "archive": False,
                    "tags": ["coverage", "bigwig", "scout", sample_id],
                },
                {
                    "path": str(
                        mip_dna_analysis_dir / f"{sample_id}_lanes_1234_star_sorted_sj.bed.gz.tbi"
                    ),
                    "archive": False,
                    "tags": ["bed", "scout", "junction", sample_id],
                },
            ]
        )

    data = {
        "name": rna_case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": files,
    }
    return data


@pytest.fixture(scope="function", name="balsamic_analysis_hk_bundle_data")
def fixture_balsamic_analysis_hk_bundle_data(
    case_id: str, timestamp: datetime, balsamic_wgs_analysis_dir: Path, sample_id: str
) -> dict:
    """Get some bundle data for housekeeper"""
    return {
        "name": case_id,
        "created": timestamp,
        "expires": timestamp,
        "files": [
            {
                "path": str(balsamic_wgs_analysis_dir / "snv.vcf"),
                "archive": False,
                "tags": ["vcf-snv-clinical"],
            },
            {
                "path": str(balsamic_wgs_analysis_dir / "sv.vcf"),
                "archive": False,
                "tags": ["vcf-sv-clinical"],
            },
            {
                "path": str(balsamic_wgs_analysis_dir / "umi.sv.vcf"),
                "archive": False,
                "tags": ["vcf-umi-snv-clinical"],
            },
            {
                "path": str(balsamic_wgs_analysis_dir / "adm1.cram"),
                "archive": False,
                "tags": ["cram", sample_id],
            },
            {
                "path": str(balsamic_wgs_analysis_dir / "ascat.output.pdf"),
                "archive": False,
                "tags": ["ascatngs", "visualization", sample_id],
            },
            {
                "path": str(balsamic_wgs_analysis_dir / "coverage_qc_report.pdf"),
                "archive": False,
                "tags": ["delivery-report"],
            },
        ],
    }


@pytest.fixture(name="balsamic_analysis_hk_version")
def fixture_balsamic_analysis_hk_version(
    housekeeper_api: MockHousekeeperAPI, balsamic_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    return helpers.ensure_hk_version(housekeeper_api, balsamic_analysis_hk_bundle_data)


@pytest.fixture(name="mip_dna_analysis_hk_version")
def fixture_mip_dna_analysis_hk_version(
    housekeeper_api: MockHousekeeperAPI, mip_dna_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    return helpers.ensure_hk_version(housekeeper_api, mip_dna_analysis_hk_bundle_data)


@pytest.fixture(name="mip_dna_analysis_hk_api")
def fixture_mip_dna_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, mip_dna_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a housekeeper api populated with some mip dna analysis files"""
    helpers.ensure_hk_version(housekeeper_api, mip_dna_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture(name="mip_rna_analysis_hk_api")
def fixture_mip_rna_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, mip_rna_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a housekeeper api populated with some mip rna analysis files"""
    helpers.ensure_hk_version(housekeeper_api, mip_rna_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture(name="balsamic_analysis_hk_api")
def fixture_balsamic_analysis_hk_api(
    housekeeper_api: MockHousekeeperAPI, balsamic_analysis_hk_bundle_data: dict, helpers
) -> MockHousekeeperAPI:
    """Return a housekeeper api populated with some mip analysis files"""
    helpers.ensure_hk_version(housekeeper_api, balsamic_analysis_hk_bundle_data)
    return housekeeper_api


@pytest.fixture(name="mip_file_handler")
def fixture_mip_file_handler(mip_dna_analysis_hk_version: hk_models.Version) -> MipConfigBuilder:
    return MipConfigBuilder(hk_version_obj=mip_dna_analysis_hk_version)


@pytest.fixture(name="mip_dna_analysis_obj")
def fixture_mip_dna_analysis_obj(
    analysis_store_trio: Store, case_id: str, timestamp: datetime, helpers: StoreHelpers
) -> models.Analysis:
    helpers.add_synopsis_to_case(store=analysis_store_trio, case_id=case_id)
    case_obj: models.Family = analysis_store_trio.family(case_id)
    analysis_obj: models.Analysis = helpers.add_analysis(
        store=analysis_store_trio,
        case=case_obj,
        started_at=timestamp,
        pipeline=Pipeline.MIP_DNA,
        completed_at=timestamp,
    )
    for link in case_obj.links:
        helpers.add_phenotype_groups_to_sample(
            store=analysis_store_trio, sample_id=link.sample.internal_id
        )
        helpers.add_phenotype_terms_to_sample(
            store=analysis_store_trio, sample_id=link.sample.internal_id
        )
        helpers.add_subject_id_to_sample(
            store=analysis_store_trio, sample_id=link.sample.internal_id
        )
    return analysis_obj


@pytest.fixture(name="balsamic_analysis_obj")
def fixture_balsamic_analysis_obj(analysis_obj: models.Analysis) -> models.Analysis:
    analysis_obj.pipeline = Pipeline.BALSAMIC
    for link_object in analysis_obj.family.links:
        link_object.sample.application_version.application.prep_category = "wes"
        link_object.family.data_analysis = Pipeline.BALSAMIC
    return analysis_obj


@pytest.fixture(name="balsamic_umi_analysis_obj")
def fixture_balsamic_umi_analysis_obj(analysis_obj: models.Analysis) -> models.Analysis:
    analysis_obj.pipeline = Pipeline.BALSAMIC_UMI
    for link_object in analysis_obj.family.links:
        link_object.sample.application_version.application.prep_category = "wes"
        link_object.family.data_analysis = Pipeline.BALSAMIC_UMI

    return analysis_obj


@pytest.fixture(name="mip_config_builder")
def fixture_mip_config_builder(
    mip_dna_analysis_hk_version: hk_models.Version,
    mip_dna_analysis_obj: models.Analysis,
    lims_api: MockLimsAPI,
    mip_analysis_api: MockMipAnalysis,
    madeline_api: MockMadelineAPI,
) -> MipConfigBuilder:
    return MipConfigBuilder(
        hk_version_obj=mip_dna_analysis_hk_version,
        analysis_obj=mip_dna_analysis_obj,
        lims_api=lims_api,
        mip_analysis_api=mip_analysis_api,
        madeline_api=madeline_api,
    )


@pytest.fixture(name="balsamic_config_builder")
def fixture_balsamic_config_builder(
    balsamic_analysis_hk_version: hk_models.Version,
    balsamic_analysis_obj: models.Analysis,
    lims_api: MockLimsAPI,
) -> BalsamicConfigBuilder:
    return BalsamicConfigBuilder(
        hk_version_obj=balsamic_analysis_hk_version,
        analysis_obj=balsamic_analysis_obj,
        lims_api=lims_api,
    )


@pytest.fixture(name="mip_load_config")
def fixture_mip_load_config(
    mip_dna_analysis_dir: Path, case_id: str, customer_id: str
) -> MipLoadConfig:
    """Return a valid mip load_config"""
    return MipLoadConfig(
        owner=customer_id,
        family=case_id,
        vcf_snv=str(mip_dna_analysis_dir / "snv.vcf"),
        track="rare",
    )


@pytest.fixture(name="lims_api")
def fixture_lims_api(lims_samples: List[dict]) -> MockLimsAPI:
    return MockLimsAPI(samples=lims_samples)


@pytest.fixture(name="mip_analysis_api")
def fixture_mip_analysis_api() -> MockMipAnalysis:
    return MockMipAnalysis()


@pytest.fixture(name="upload_scout_api")
def fixture_upload_scout_api(
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: List[dict],
    housekeeper_api: MockHousekeeperAPI,
    store: Store,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api"""
    analysis_mock = MockMipAnalysis()
    lims_api = MockLimsAPI(samples=lims_samples)

    return UploadScoutAPI(
        hk_api=housekeeper_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )


@pytest.fixture(name="upload_mip_analysis_scout_api")
def fixture_upload_mip_analysis_scout_api(
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: List[dict],
    mip_dna_analysis_hk_api: MockHousekeeperAPI,
    store: Store,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api"""
    analysis_mock = MockMipAnalysis()
    lims_api = MockLimsAPI(samples=lims_samples)

    _api = UploadScoutAPI(
        hk_api=mip_dna_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )

    yield _api


@pytest.fixture(name="upload_balsamic_analysis_scout_api")
def fixture_upload_balsamic_analysis_scout_api(
    scout_api: MockScoutAPI,
    madeline_api: MockMadelineAPI,
    lims_samples: List[dict],
    balsamic_analysis_hk_api: MockHousekeeperAPI,
    store: Store,
) -> UploadScoutAPI:
    """Fixture for upload_scout_api"""
    analysis_mock = MockMipAnalysis()
    lims_api = MockLimsAPI(samples=lims_samples)

    _api = UploadScoutAPI(
        hk_api=balsamic_analysis_hk_api,
        scout_api=scout_api,
        madeline_api=madeline_api,
        analysis_api=analysis_mock,
        lims_api=lims_api,
        status_db=store,
    )

    yield _api
