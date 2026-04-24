"""Integration tests for Scout load config generation.

These tests generate an actual scout_load.yaml from a real database and real Housekeeper
bundles, then read the file back and verify that all fields — especially those derived
from Enum types — are serialized as plain scalar values rather than Python object
representations.
"""

from datetime import datetime
from pathlib import Path
from typing import cast

import pytest
import yaml
from click.testing import CliRunner, Result
from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer

from cg.cli.base import base
from cg.constants.constants import Workflow
from cg.constants.housekeeper_tags import AlignmentFileTag
from cg.store.models import Analysis, Case, Sample
from cg.store.store import Store
from tests.integration.utils import IntegrationTestPaths, create_empty_file
from tests.store_helpers import StoreHelpers

_LIMS_BASE = "http://localhost:8888/lims"


def _expect_lims_sample_and_project(httpserver: HTTPServer, sample: Sample) -> None:
    """Register httpserver handlers for the LIMS sample and its project.

    The genologics library lazily fetches linked resources (the project) using the absolute
    URI embedded in the sample XML. We therefore:
    1. Return a sample XML where the project URI points back to the test httpserver.
    2. Register a minimal project handler so the lazy load succeeds.
    """
    project_uri = f"{_LIMS_BASE}/api/v2/projects/ACC0001"

    sample_xml = f"""<smp:sample
        xmlns:udf="http://genologics.com/ri/userdefined"
        xmlns:ri="http://genologics.com/ri"
        xmlns:file="http://genologics.com/ri/file"
        xmlns:smp="http://genologics.com/ri/sample"
        uri="{_LIMS_BASE}/api/v2/samples/{sample.internal_id}"
        limsid="{sample.internal_id}">
      <name>sample-name</name>
      <date-received>2017-05-20</date-received>
      <project limsid="ACC0001" uri="{project_uri}"/>
      <udf:field type="String" name="customer">cust000</udf:field>
      <udf:field type="String" name="familyID">F0000001</udf:field>
      <udf:field type="String" name="Gender">M</udf:field>
      <udf:field type="String" name="priority">standard</udf:field>
      <udf:field type="String" name="Source">blood</udf:field>
      <udf:field type="String" name="Status">unaffected</udf:field>
      <udf:field type="String" name="Gene List">OMIM-AUTO</udf:field>
      <udf:field type="String" name="Data Analysis">scout</udf:field>
      <udf:field type="String" name="Sequencing Analysis">EXXCUSR000</udf:field>
      <udf:field type="String" name="Application Tag Version">1</udf:field>
      <udf:field type="String" name="Bait Set">NA</udf:field>
    </smp:sample>"""

    project_xml = f"""<prj:project
        xmlns:prj="http://genologics.com/ri/project"
        limsid="ACC0001"
        uri="{project_uri}">
      <name>Test Project</name>
      <open-date>2017-05-20</open-date>
    </prj:project>"""

    httpserver.expect_request(f"/lims/api/v2/samples/{sample.internal_id}").respond_with_data(
        sample_xml, content_type="application/xml"
    )

    httpserver.expect_request("/lims/api/v2/projects/ACC0001").respond_with_data(
        project_xml, content_type="application/xml"
    )


@pytest.fixture(autouse=True)
def current_workflow() -> Workflow:
    return Workflow.NALLO


@pytest.fixture
def nallo_case(helpers: StoreHelpers, status_db: Store) -> Case:
    return helpers.add_case(store=status_db, data_analysis=Workflow.NALLO)


@pytest.fixture
def nallo_sample(helpers: StoreHelpers, status_db: Store) -> Sample:
    return helpers.add_sample(
        application_type="wgs",
        store=status_db,
        last_sequenced_at=datetime.now(),
    )


@pytest.fixture
def nallo_hk_bundle(
    nallo_case: Case,
    nallo_sample: Sample,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
) -> Version:
    """Create a Housekeeper bundle for a Nallo case with the minimum required analysis files."""
    root = test_run_paths.test_root_dir
    sample_id = nallo_sample.internal_id

    vcf_snv = Path(root, "vcf_snv_clinical.vcf")
    vcf_snv_research = Path(root, "vcf_snv_research.vcf")
    vcf_sv = Path(root, "vcf_sv_clinical.vcf")
    vcf_sv_research = Path(root, "vcf_sv_research.vcf")
    delivery_report = Path(root, "delivery_report.html")
    bam_file = Path(root, f"{sample_id}.bam")

    for path in [vcf_snv, vcf_snv_research, vcf_sv, vcf_sv_research, delivery_report, bam_file]:
        create_empty_file(path)

    bundle_data = {
        "name": nallo_case.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {"path": vcf_snv.as_posix(), "tags": ["vcf-snv-clinical"], "archive": False},
            {"path": vcf_snv_research.as_posix(), "tags": ["vcf-snv-research"], "archive": False},
            {"path": vcf_sv.as_posix(), "tags": ["vcf-sv-clinical"], "archive": False},
            {"path": vcf_sv_research.as_posix(), "tags": ["vcf-sv-research"], "archive": False},
            {"path": delivery_report.as_posix(), "tags": ["delivery-report"], "archive": False},
            {
                "path": bam_file.as_posix(),
                "tags": [AlignmentFileTag.BAM, "haplotags", sample_id],
                "archive": False,
            },
        ],
    }

    bundle, version = cast(tuple[Bundle, Version], housekeeper_db.add_bundle(bundle_data))
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.add(version)
    housekeeper_db.session.commit()
    return version


@pytest.fixture
def nallo_completed_analysis(
    helpers: StoreHelpers,
    nallo_case: Case,
    nallo_hk_bundle: Version,
    nallo_sample: Sample,
    status_db: Store,
) -> Analysis:
    helpers.relate_samples(base_store=status_db, case=nallo_case, samples=[nallo_sample])
    return helpers.add_analysis(
        store=status_db,
        case=nallo_case,
        workflow=Workflow.NALLO,
        completed_at=datetime.now(),
    )


@pytest.mark.xdist_group(name="integration")
@pytest.mark.integration
def test_create_nallo_scout_load_config_serializes_correctly(
    httpserver: HTTPServer,
    nallo_case: Case,
    nallo_completed_analysis: Analysis,
    nallo_sample: Sample,
    test_run_paths: IntegrationTestPaths,
):
    """Test that the generated scout_load.yaml contains correctly serialized scalar values.

    Enums and StrEnum values must appear as their plain string/numeric equivalents so that
    Scout can load the file without errors.
    """
    cli_runner = CliRunner()

    # GIVEN the case output directory exists (normally created by the workflow run)
    case_dir = Path(test_run_paths.test_root_dir, "nallo_root_path", nallo_case.internal_id)
    case_dir.mkdir(parents=True, exist_ok=True)

    # GIVEN the LIMS server handles the sample and project metadata requests
    _expect_lims_sample_and_project(httpserver=httpserver, sample=nallo_sample)

    # WHEN generating the scout load config via the CLI
    result: Result = cli_runner.invoke(
        base,
        [
            "--config",
            test_run_paths.cg_config_file.as_posix(),
            "upload",
            "create-scout-load-config",
            nallo_case.internal_id,
        ],
        catch_exceptions=False,
    )

    # THEN the command exits successfully
    assert result.exit_code == 0, result.output

    # THEN the scout_load.yaml file exists at the expected path
    scout_load_config_path = Path(case_dir, "scout_load.yaml")
    assert scout_load_config_path.exists()

    # THEN the YAML can be loaded without errors
    with open(scout_load_config_path) as fh:
        config = yaml.safe_load(fh)

    # THEN top-level enum-derived fields are plain strings, not Python object representations
    assert config["track"] == "rare", f"track was {config['track']!r}, expected 'rare'"
    assert (
        config["human_genome_build"] == "38"
    ), f"human_genome_build was {config['human_genome_build']!r}, expected '38'"

    # THEN case identity fields are plain strings
    assert config["family"] == nallo_case.internal_id
    assert config["owner"] == nallo_case.customer.internal_id

    # THEN the sample block contains the expected sample with correctly serialized enum fields
    assert len(config["samples"]) == 1
    sample_config = config["samples"][0]

    assert sample_config["sample_id"] == nallo_sample.internal_id
    assert isinstance(sample_config["analysis_type"], str), (
        f"analysis_type was {sample_config['analysis_type']!r} "
        f"(type {type(sample_config['analysis_type']).__name__}), expected a plain str"
    )
    assert isinstance(sample_config["sex"], str), (
        f"sex was {sample_config['sex']!r} (type {type(sample_config['sex']).__name__}), "
        "expected a plain str"
    )
    assert isinstance(sample_config["phenotype"], str), (
        f"phenotype was {sample_config['phenotype']!r} "
        f"(type {type(sample_config['phenotype']).__name__}), expected a plain str"
    )
    # father/mother derive from RelationshipStatus.HAS_NO_PARENT ("0") — must be a plain string
    assert sample_config["father"] == "0", f"father was {sample_config['father']!r}, expected '0'"
    assert sample_config["mother"] == "0", f"mother was {sample_config['mother']!r}, expected '0'"

    # THEN the VCF paths are plain strings (not wrapped objects)
    assert isinstance(config["vcf_snv"], str)
    assert isinstance(config["vcf_snv_research"], str)
    assert isinstance(config["vcf_sv"], str)
    assert isinstance(config["vcf_sv_research"], str)
