import shutil
from datetime import datetime
from pathlib import Path
from typing import NamedTuple, cast

from housekeeper.store.models import Bundle, Version
from housekeeper.store.store import Store as HousekeeperStore
from pytest_httpserver import HTTPServer

from cg.apps.environ import environ_email
from cg.constants.constants import Workflow
from cg.constants.housekeeper_tags import AlignmentFileTag, SequencingFileTag
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


def create_integration_test_sample_fastq_files(
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

    _create_fastq_files_and_add_to_housekeeper(
        housekeeper_db=housekeeper_db, test_root_dir=test_run_paths.test_root_dir, sample=sample
    )

    return sample


def create_integration_test_sample_bam_files(
    status_db: Store, housekeeper_db: HousekeeperStore, test_run_paths: IntegrationTestPaths
) -> Sample:
    helpers = StoreHelpers()
    sample: Sample = helpers.add_sample(
        application_type=AnalysisType.WGS, store=status_db, last_sequenced_at=datetime.now()
    )
    _create_bam_files_and_add_to_housekeeper(
        housekeeper_db=housekeeper_db,
        sample=sample,
        test_root_dir=test_run_paths.test_root_dir,
    )

    return sample


def _create_fastq_files_and_add_to_housekeeper(
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

    _create_bundle_for_sample(
        housekeeper_db=housekeeper_db,
        sample=sample,
        file1_path=fastq_file_path1,
        file2_path=fastq_file_path2,
        file_extension=SequencingFileTag.FASTQ,
    )


def _create_bam_files_and_add_to_housekeeper(
    housekeeper_db: HousekeeperStore, sample: Sample, test_root_dir: Path
) -> None:
    file1_path = Path(test_root_dir, "file1.bam")
    file2_path = Path(test_root_dir, "file2.bam")

    create_empty_file(file1_path)
    create_empty_file(file2_path)

    _create_bundle_for_sample(
        housekeeper_db, sample, file1_path, file2_path, file_extension=AlignmentFileTag.BAM
    )


def _create_bundle_for_sample(
    housekeeper_db: HousekeeperStore,
    sample: Sample,
    file1_path: Path,
    file2_path: Path,
    file_extension: str,
):
    bundle_data = {
        "name": sample.internal_id,
        "created": datetime.now(),
        "expires": datetime.now(),
        "files": [
            {
                "path": file1_path.as_posix(),
                "archive": False,
                "tags": [sample.id, file_extension],
            },
            {
                "path": file2_path.as_posix(),
                "archive": False,
                "tags": [sample.id, file_extension],
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


def expect_to_get_latest_analysis_with_empty_response_from_trailblazer(
    trailblazer_server: HTTPServer, case_id: str
):
    trailblazer_server.expect_request(
        "/trailblazer/get-latest-analysis", data='{"case_id": "' + case_id + '"}'
    ).respond_with_json(None)


def expect_to_add_pending_analysis_to_trailblazer(
    trailblazer_server: HTTPServer,
    case: Case,
    ticket_id: int,
    out_dir: Path,
    config_path: Path | None,
    analysis_type: AnalysisType,
    workflow: Workflow,
    tower_workflow_id: str | None = None,
    workflow_manager: str = "slurm",
):
    trailblazer_server.expect_request(
        "/trailblazer/add-pending-analysis",
        data=b'{"case_id": "%(case_id)s", "email": "%(email)s", "type": "%(type)s", '
        b'"config_path": %(config_path)s,'
        b' "order_id": 1, "out_dir": "%(out_dir)s", '
        b'"priority": "normal", "workflow": "%(workflow)s", "ticket": "%(ticket_id)s", '
        b'"workflow_manager": "%(workflow_manager)s", "tower_workflow_id": %(tower_workflow_id)s, "is_hidden": true}'
        % {
            b"email": environ_email().encode(),
            b"type": str(analysis_type).encode(),
            b"case_id": case.internal_id.encode(),
            b"ticket_id": str(ticket_id).encode(),
            b"tower_workflow_id": _quoted_string_or_null(tower_workflow_id),
            b"out_dir": str(out_dir).encode(),
            b"config_path": _quoted_string_or_null(config_path),
            b"workflow": str(workflow).upper().encode(),
            b"workflow_manager": str(workflow_manager).encode(),
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


def _quoted_string_or_null(value: str | Path | None) -> bytes:
    return (f'"{value}"' if value else "null").encode()


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
