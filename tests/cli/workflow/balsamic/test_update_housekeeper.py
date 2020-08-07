from pathlib import Path
import json
import logging
import pytest

from cg.cli.workflow.balsamic.base import update_housekeeper
from tests.conftest import fixture_real_housekeeper_api
from cg.exc import BalsamicStartError, BundleAlreadyAddedError
from tests.cli.workflow.balsamic.conftest import balsamic_housekeeper

EXIT_SUCCESS = 0


def mock_config(root_dir, case_id):
    """Create dummy config file at specified path"""

    config_data = {
        "analysis": {
            "case_id": f"{case_id}",
            "analysis_type": "paired",
            "sequencing_type": "targeted",
            "analysis_dir": f"{root_dir}",
            "fastq_path": f"{root_dir}/{case_id}/analysis/fastq/",
            "script": f"{root_dir}/{case_id}/scripts/",
            "log": f"{root_dir}/{case_id}/logs/",
            "result": f"{root_dir}/{case_id}/analysis",
            "benchmark": f"{root_dir}/{case_id}/benchmarks/",
            "dag": f"{root_dir}/{case_id}/{case_id}_BALSAMIC_4.4.0_graph.pdf",
            "BALSAMIC_version": "4",
            "config_creation_date": "2020-07-15 17:35",
        }
    }
    Path.mkdir(Path(root_dir, case_id), parents=True, exist_ok=True)
    config_path = Path(root_dir, case_id, case_id + ".json")
    json.dump(config_data, open(config_path, "w"))


def mock_deliverable(root_dir: str, case_id: str, samples: list):
    """Create deliverable file with dummy data and files to deliver"""

    deliverable_data = {
        "files": [
            {
                "path": f"{root_dir}/{case_id}/multiqc_report.html",
                "path_index": "",
                "step": "multiqc",
                "tags": "qc",
                "id": "T_WGS",
                "format": "html",
            },
            {
                "path": f"{root_dir}/{case_id}/concatenated_{samples[0]}_R_1.fp.fastq.gz",
                "path_index": "",
                "step": "fastp",
                "tags": f"concatenated_{samples[0]}_R,qc",
                "id": f"concatenated_{samples[0]}_R",
                "format": "fastq.gz",
            },
            {
                "path": f"{root_dir}/{case_id}/CNV.somatic.{case_id}.cnvkit.pass.vcf.gz.tbi",
                "path_index": "",
                "step": "vep_somatic",
                "format": "vcf.gz.tbi",
                "tags": f"CNV,{case_id},cnvkit,annotation,somatic,index",
                "id": f"{case_id}",
            },
        ]
    }
    Path.mkdir(Path(root_dir, case_id, "analysis", "delivery_report"), parents=True, exist_ok=True)
    for report_entry in deliverable_data["files"]:
        Path(report_entry["path"]).touch(exist_ok=True)
    hk_report_path = Path(root_dir, case_id, "analysis", "delivery_report", case_id + ".hk")
    json.dump(deliverable_data, open(hk_report_path, "w"))


def mock_analysis_finish(root_dir, case_id):
    """Create analysis_finish file for testing"""
    Path.mkdir(Path(root_dir, case_id, "analysis"), parents=True, exist_ok=True)
    Path(root_dir, case_id, "analysis", "analysis_finish").touch(exist_ok=True)


def test_without_options(cli_runner, balsamic_context):
    """Test command without case_id argument"""
    # GIVEN no case_id
    # WHEN dry running without anything specified
    result = cli_runner.invoke(update_housekeeper, obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN command should mention argument
    assert "Missing argument" in result.output


def test_with_missing_case(cli_runner, balsamic_context, caplog):
    """Test command with invalid case to start with"""
    caplog.set_level(logging.ERROR)
    # GIVEN case_id not in database
    case_id = "soberelephant"
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id)
    # WHEN running
    result = cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)
    # THEN command should NOT successfully call the command it creates
    assert result.exit_code != EXIT_SUCCESS
    # THEN ERROR log should be printed containing invalid case_id
    assert case_id in caplog.text
    assert "not found" in caplog.text


def test_without_samples(cli_runner, balsamic_context, caplog):
    """Test command with case_id and no samples"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "no_sample_case"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "0" in caplog.text


def test_without_config(cli_runner, balsamic_context, caplog):
    """Test command with case_id and no config file"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN dry running with dry specified
    result = cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no config file is found
    assert "No config file found" in caplog.text


def test_case_without_deliverables_file(cli_runner, balsamic_context, caplog):
    """Test command with case_id and config file but no analysis_finish"""
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    Path.mkdir(
        Path(balsamic_context["BalsamicAnalysisAPI"].get_config_path(case_id)).parent, exist_ok=True
    )
    mock_config(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir, case_id=case_id
    )
    # WHEN dry running with dry specified
    result = cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN warning should be printed that no analysis_finish is found
    assert "No deliverables file found" in caplog.text


def test_valid_case(
    cli_runner, balsamic_context, caplog, real_housekeeper_api, balsamic_housekeeper
):
    caplog.set_level(logging.INFO)
    # GIVEN case-id
    case_id = "balsamic_case_wgs_single"
    # WHEN ensuring case config exists where it should be stored
    mock_config(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir, case_id=case_id
    )
    # WHEN ensuring deliverables exists where it should be stored
    mock_deliverable(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir,
        case_id=case_id,
        samples=["sample_case_wgs_single_tumor",],
    )
    # WHEN ensuring analysis_finish file is present
    mock_analysis_finish(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir, case_id=case_id
    )

    # Make sure nothing is currently stored in Housekeeper, and no analyses stored in ClinicalDB
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses

    # WHEN running command
    result = cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)

    # THEN bundle should be successfully added to HK and STATUS
    assert result.exit_code == EXIT_SUCCESS
    assert "Analysis successfully stored in Housekeeper" in caplog.text
    assert "Analysis successfully stored in ClinicalDB" in caplog.text
    assert balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses
    assert balsamic_context["BalsamicAnalysisAPI"].housekeeper_api.bundle(case_id)

    # TEARDOWN change real housekeeper back to balsamic fixture
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = balsamic_housekeeper


def test_valid_case_already_added(
    cli_runner, balsamic_context, caplog, real_housekeeper_api, balsamic_housekeeper
):
    caplog.set_level(logging.ERROR)
    # GIVEN case-id
    case_id = "balsamic_case_tgs_single"
    # SETUP ensuring case config exists where it should be stored
    mock_config(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir, case_id=case_id
    )
    # SETUP ensuring deliverables exists where it should be stored
    mock_deliverable(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir,
        case_id=case_id,
        samples=["sample_case_tgs_single_tumor",],
    )
    # SETUP ensuring analysis_finish file is present
    mock_analysis_finish(
        root_dir=balsamic_context["BalsamicAnalysisAPI"].balsamic_api.root_dir, case_id=case_id
    )
    # SETUP ensure nothing is currently stored in Housekeeper, and no analyses stored in ClinicalDB
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = real_housekeeper_api
    assert not balsamic_context["BalsamicAnalysisAPI"].store.family(case_id).analyses
    # SETUP ensure bundles exist by creating them first
    cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)
    # WHEN running command
    result = cli_runner.invoke(update_housekeeper, [case_id], obj=balsamic_context)
    # THEN command should NOT execute successfully
    assert result.exit_code != EXIT_SUCCESS
    # THEN user should be informed that bundle was already added
    assert "Bundle already added" in caplog.text

    # TEARDOWN change real housekeeper back to balsamic fixture
    balsamic_context["BalsamicAnalysisAPI"].housekeeper_api = balsamic_housekeeper
