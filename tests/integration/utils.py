import shutil
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, cast

from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer

from cg.apps.environ import environ_email
from cg.constants.constants import Workflow
from cg.constants.housekeeper_tags import SequencingFileTag
from cg.constants.tb import AnalysisType
from cg.store.models import Case, IlluminaFlowCell, IlluminaSequencingRun, Sample
from cg.store.store import Store
from tests.store_helpers import StoreHelpers


class IntegrationTestPaths(NamedTuple):
    cg_config_file: Path
    test_root_dir: Path


def create_formatted_config(status_db_uri: str, housekeeper_db_uri: str, test_root_dir: str):
    template_path = "tests/integration/config/cg-test.yaml"
    with open(template_path) as f:
        config_content = f.read()

    config_content = config_content.format(
        test_root_dir=test_root_dir,
        status_db_uri=status_db_uri,
        housekeeper_db_uri=housekeeper_db_uri,
    )

    config_path = Path(test_root_dir, "cg-config.yaml")
    with open(config_path, "w") as f:
        f.write(config_content)
    return config_path


def create_integration_test_sample(
    status_db: Store,
    housekeeper_db: HousekeeperStore,
    test_run_paths: IntegrationTestPaths,
    application_type: AnalysisType,
    flow_cell_id: str,
    is_tumour: bool = False,
) -> Sample:
    helpers = StoreHelpers()
    sample: Sample = helpers.add_sample(
        store=status_db,
        is_tumour=is_tumour,
        last_sequenced_at=datetime.now(),
        application_type=application_type,
    )
    flow_cell: IlluminaFlowCell = helpers.add_illumina_flow_cell(
        store=status_db, flow_cell_id=flow_cell_id
    )
    sequencing_run: IlluminaSequencingRun = helpers.add_illumina_sequencing_run(
        store=status_db,
        flow_cell=flow_cell,
    )
    helpers.add_illumina_sample_sequencing_metrics_object(
        store=status_db, sample_id=sample.internal_id, sequencing_run=sequencing_run, lane=1
    )

    create_fastq_file_and_add_to_housekeeper(
        housekeeper_db=housekeeper_db, test_root_dir=test_run_paths.test_root_dir, sample=sample
    )

    return sample


def create_fastq_file_and_add_to_housekeeper(
    housekeeper_db: HousekeeperStore, sample: Sample, test_root_dir: Path
) -> None:
    fastq_base_path: Path = Path(test_root_dir, "fastq_files")
    fastq_base_path.mkdir(parents=True, exist_ok=True)

    fastq_file_path1: Path = Path(fastq_base_path, f"{sample.internal_id}.fastq.gz")
    copy_integration_test_file(
        from_path=Path("tests/integration/config/file.fastq.gz"), to_path=fastq_file_path1
    )
    fastq_file_path2: Path = Path(fastq_base_path, f"{sample.internal_id}2.fastq.gz")
    copy_integration_test_file(
        from_path=Path("tests/integration/config/file.fastq.gz"), to_path=fastq_file_path2
    )

    bundle_data = {
        "name": sample.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {
                "path": fastq_file_path1.as_posix(),
                "archive": False,
                "tags": [sample.id, SequencingFileTag.FASTQ],
            },
            {
                "path": fastq_file_path2.as_posix(),
                "archive": False,
                "tags": [sample.id, SequencingFileTag.FASTQ],
            },
        ],
    }

    bundle, version = cast(tuple[Bundle, Version], housekeeper_db.add_bundle(bundle_data))
    housekeeper_db.session.add(bundle)
    housekeeper_db.session.add(version)
    housekeeper_db.session.commit()


def create_empty_file(file_path: Path):
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.touch()


def copy_integration_test_file(from_path: Path, to_path: Path):
    to_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(from_path, to_path)
    return True


def expect_to_add_pending_analysis_to_trailblazer(
    trailblazer_server: HTTPServer,
    case: Case,
    ticket_id: int,
    case_path: Path,
    config_path: Path,
    analysis_type: AnalysisType,
    workflow: Workflow,
):
    trailblazer_server.expect_request(
        "/trailblazer/add-pending-analysis",
        data=b'{"case_id": "%(case_id)s", "email": "%(email)s", "type": "%(type)s", '
        b'"config_path": "%(config_path)s",'
        b' "order_id": 1, "out_dir": "%(case_path)s/analysis", '
        b'"priority": "normal", "workflow": "%(workflow)s", "ticket": "%(ticket_id)s", '
        b'"workflow_manager": "slurm", "tower_workflow_id": null, "is_hidden": true}'
        % {
            b"email": environ_email().encode(),
            b"type": str(analysis_type).encode(),
            b"case_id": case.internal_id.encode(),
            b"ticket_id": str(ticket_id).encode(),
            b"case_path": str(case_path).encode(),
            b"config_path": str(config_path).encode(),
            b"workflow": str(workflow).upper().encode(),
        },
        method="POST",
    ).respond_with_json(
        {
            "id": "1",
            "logged_at": "",
            "started_at": "",
            "completed_at": "",
            "out_dir": "out/dir",
            "config_path": "config/path",
        }
    )


def expect_lims_sample_request(lims_server: HTTPServer, sample: Sample, bed_name: str):
    lims_server.expect_request(f"/lims/api/v2/samples/{sample.internal_id}").respond_with_data(
        f"""<smp:sample xmlns:udf="http://genologics.com/ri/userdefined" xmlns:ri="http://genologics.com/ri" xmlns:file="http://genologics.com/ri/file" xmlns:smp="http://genologics.com/ri/sample" uri="http://127.0.0.1:8000/api/v2/samples/ACC0001A1" limsid="ACC0001A1">
<name>2016-00001</name>
<date-received>2017-05-20</date-received>
<project limsid="ACC0001" uri="http://127.0.0.1:8000/api/v2/projects/ACC0001"/>
<submitter uri="http://127.0.0.1:8000/api/v2/researchers/3">
<first-name>API</first-name>
<last-name>Access</last-name>
</submitter>
<artifact limsid="ACC0001A1PA1" uri="http://127.0.0.1:8000/api/v2/artifacts/ACC0001A1PA1?state=55264"/>
<udf:field type="Boolean" name="Sample Delivered">true</udf:field>
<udf:field type="String" name="Concentration (nM)">NA</udf:field>
<udf:field type="String" name="customer">cust000</udf:field>
<udf:field type="String" name="familyID">F0000001</udf:field>
<udf:field type="String" name="Gender">M</udf:field>
<udf:field type="String" name="priority">standard</udf:field>
<udf:field type="String" name="Process only if QC OK">NA</udf:field>
<udf:field type="Numeric" name="Reads missing (M)">0</udf:field>
<udf:field type="String" name="Reference Genome Microbial">NA</udf:field>
<udf:field type="String" name="Sample Buffer">NA</udf:field>
<udf:field type="String" name="Sequencing Analysis">EXXCUSR000</udf:field>
<udf:field type="String" name="Status">unaffected</udf:field>
<udf:field type="String" name="Strain">NA</udf:field>
<udf:field type="String" name="Source">NA</udf:field>
<udf:field type="String" name="Volume (uL)">NA</udf:field>
<udf:field type="String" name="Gene List">OMIM-AUTO</udf:field>
<udf:field type="String" name="Index type">NA</udf:field>
<udf:field type="String" name="Data Analysis">scout</udf:field>
<udf:field type="String" name="Index number">NA</udf:field>
<udf:field type="String" name="Application Tag Version">1</udf:field>
<udf:field type="String" name="Bait Set">{bed_name}</udf:field>
<udf:field type="String" name="Capture Library version">Agilent Sureselect V5</udf:field>
</smp:sample>""",
        content_type="application/xml",
    )
