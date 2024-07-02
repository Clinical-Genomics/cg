"""Fixtures for parsed raw LIMS samples for demultiplexing and sample sheet creation."""

from pathlib import Path

import pytest

from cg.apps.demultiplex.sample_sheet.sample_models import IlluminaSampleIndexSetting
from cg.apps.demultiplex.sample_sheet.sample_sheet_creator import SampleSheetCreator
from cg.constants import FileExtensions
from cg.io.json import read_json
from cg.models.run_devices.illumina_run_directory_data import IlluminaRunDirectoryData


@pytest.fixture
def hiseq_x_single_index_bcl_convert_lims_samples(
    hiseq_x_single_index_flow_cell_dir: Path,
) -> list[IlluminaSampleIndexSetting]:
    """Return a list of BCLConvert samples parsed from LIMS for a HiSeqX single index flow cell."""
    path = Path(
        hiseq_x_single_index_flow_cell_dir, f"HJCFFALXX_bcl_convert_raw{FileExtensions.JSON}"
    )
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_hiseq_x_single_index_sample_ids() -> list[str]:
    """Return a list of sample ids for a HiSeqX single index flow cell."""
    return ["SVE2648A1", "ACC2655A1"]


@pytest.fixture
def selected_hiseq_x_single_index_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a HiSeqX single index flow cell."""
    return ["preposterousmink", "gloriouschicken"]


@pytest.fixture
def hiseq_x_dual_index_bcl_convert_lims_samples(
    hiseq_x_dual_index_flow_cell_dir: Path,
) -> list[IlluminaSampleIndexSetting]:
    """Return a list of samples parsed from LIMS for a HiSeqX dual index flow cell."""
    path = Path(hiseq_x_dual_index_flow_cell_dir, f"HL32LCCXY_bcl_convert_raw{FileExtensions.JSON}")
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_hiseq_x_dual_index_sample_ids() -> list[str]:
    """Return a list of sample ids for a HiSeqX dual index flow cell."""
    return ["ACC4519A1", "ACC4519A2"]


@pytest.fixture
def selected_hiseq_x_dual_index_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a HiSeqX dual index flow cell."""
    return ["illustriousmarlin", "infamouspenguin"]


@pytest.fixture
def hiseq_2500_dual_index_bcl_convert_lims_samples(
    hiseq_2500_dual_index_flow_cell_dir: Path,
) -> list[IlluminaSampleIndexSetting]:
    """Return a list of samples parsed from LIMS for a HiSeq2500 dual index flow cell."""
    path = Path(hiseq_2500_dual_index_flow_cell_dir, "HM2LNBCX2_bcl_convert_raw.json")
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_hiseq_2500_dual_index_sample_ids() -> list[str]:
    """Return a list of sample ids for a HiSeq2500 dual index flow cell."""
    return ["ACC4842A47", "ACC4842A48"]


@pytest.fixture
def selected_hiseq_2500_dual_index_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a HiSeq2500 dual index flow cell."""
    return ["mysteriouscat", "magnificentdog"]


@pytest.fixture
def hiseq_2500_custom_index_bcl_convert_lims_samples(
    hiseq_2500_custom_index_flow_cell_dir: Path,
) -> list[IlluminaSampleIndexSetting]:
    """Return a list of samples parsed from LIMS for a HiSeq2500 custom index flow cell."""
    path = Path(hiseq_2500_custom_index_flow_cell_dir, "HGYFNBCX2_bcl_convert_raw.json")
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_hiseq_2500_custom_index_sample_ids() -> list[str]:
    """Return a list of sample ids for a HiSeq2500 custom index flow cell."""
    return ["MIC4464A1", "ACC4551A1"]


@pytest.fixture
def selected_hiseq_2500_custom_index_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a HiSeq2500 custom index flow cell."""
    return ["downcobra", "upmoose"]


@pytest.fixture
def novaseq_6000_pre_1_5_kits_bcl_convert_lims_samples(
    novaseq_6000_pre_1_5_kits_flow_cell_path: Path,
) -> list[IlluminaSampleIndexSetting]:
    """Return a list of samples parsed from LIMS for a NovaSeq6000 pre 1.5 flow cell."""
    path = Path(novaseq_6000_pre_1_5_kits_flow_cell_path, "HLYWYDSXX_bcl_convert_raw.json")
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_novaseq_6000_pre_1_5_kits_sample_ids() -> list[str]:
    """Return a list of sample ids for a NovaSeq6000 pre 1.5 kits flow cell."""
    return ["ACC6217A7", "ACC6217A12"]


@pytest.fixture
def selected_novaseq_6000_pre_1_5_kits_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a NovaSeq6000 pre 1.5 kits flow cell."""
    return ["fastsnail", "slowsloth"]


@pytest.fixture
def novaseq_6000_post_1_5_kits_bcl_convert_lims_samples(
    novaseq_6000_post_1_5_kits_flow_cell_path: Path,
) -> list[IlluminaSampleIndexSetting]:
    """Return a list of samples parsed from LIMS for a NovaSeq6000 post 1.5 flow cell."""
    path = Path(novaseq_6000_post_1_5_kits_flow_cell_path, "HK33MDRX3_bcl_convert_raw.json")
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_novaseq_6000_post_1_5_kits_sample_ids() -> list[str]:
    """Return a list of sample ids for a NovaSeq6000 post 1.5 kits flow cell."""
    return ["ACC12642A7", "ACC12642A4"]


@pytest.fixture
def selected_novaseq_6000_post_1_5_kits_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a NovaSeq6000 post 1.5 kits flow cell."""
    return ["enlightendfox", "thunderousrabbit"]


@pytest.fixture
def novaseq_x_lims_samples(novaseq_x_flow_cell_dir: Path) -> list[IlluminaSampleIndexSetting]:
    """Return a list of samples parsed from LIMS for a NovaSeqX flow cell."""
    path = Path(novaseq_x_flow_cell_dir, "22F52TLT3_raw.json")
    return [IlluminaSampleIndexSetting.model_validate(sample) for sample in read_json(path)]


@pytest.fixture
def selected_novaseq_x_sample_ids() -> list[str]:
    """Return a list of sample ids for a NovaSeqX flow cell."""
    return ["ACC13169A1", "ACC13170A6"]


@pytest.fixture
def selected_novaseq_x_case_ids() -> list[str]:
    """Return a list of case ids associated to selected samples for a NovaSeqX flow cell."""
    return ["swifttiger", "furiouslion"]


@pytest.fixture
def sample_id_sequenced_on_multiple_flow_cells() -> str:
    """Return a sample id that has been sequenced on multiple flow cells."""
    return "ACC13169A1"


@pytest.fixture
def flow_cells_with_the_same_sample(
    novaseq_x_flow_cell_id: str, novaseq_6000_post_1_5_kits_flow_cell_id: str
) -> list[str]:
    """Return a list of flow cell ids that have the same sample sequenced."""
    return [novaseq_x_flow_cell_id, novaseq_6000_post_1_5_kits_flow_cell_id]


@pytest.fixture
def case_id_for_sample_on_multiple_flow_cells() -> str:
    """Return a case id for a sample sequenced on multiple flow cells."""
    return "swifttiger"


@pytest.fixture
def seven_canonical_flow_cells_selected_sample_ids(
    selected_hiseq_x_single_index_sample_ids: list[str],
    selected_hiseq_x_dual_index_sample_ids: list[str],
    selected_hiseq_2500_dual_index_sample_ids: list[str],
    selected_hiseq_2500_custom_index_sample_ids: list[str],
    selected_novaseq_6000_pre_1_5_kits_sample_ids: list[str],
    selected_novaseq_6000_post_1_5_kits_sample_ids: list[str],
    selected_novaseq_x_sample_ids: list[str],
) -> list[list[str]]:
    """Return a list of lists containing the selected sample ids for each canonical flow cell."""
    return [
        selected_hiseq_x_single_index_sample_ids,
        selected_hiseq_x_dual_index_sample_ids,
        selected_hiseq_2500_dual_index_sample_ids,
        selected_hiseq_2500_custom_index_sample_ids,
        selected_novaseq_6000_pre_1_5_kits_sample_ids,
        selected_novaseq_6000_post_1_5_kits_sample_ids,
        selected_novaseq_x_sample_ids,
    ]


@pytest.fixture
def seven_canonical_sequencing_runs_selected_case_ids(
    selected_hiseq_x_single_index_case_ids: list[str],
    selected_hiseq_x_dual_index_case_ids: list[str],
    selected_hiseq_2500_dual_index_case_ids: list[str],
    selected_hiseq_2500_custom_index_case_ids: list[str],
    selected_novaseq_6000_pre_1_5_kits_case_ids: list[str],
    selected_novaseq_6000_post_1_5_kits_case_ids: list[str],
    selected_novaseq_x_case_ids: list[str],
) -> list[list[str]]:
    """Return a list of lists containing the selected case ids for each canonical flow cell."""
    return [
        selected_hiseq_x_single_index_case_ids,
        selected_hiseq_x_dual_index_case_ids,
        selected_hiseq_2500_dual_index_case_ids,
        selected_hiseq_2500_custom_index_case_ids,
        selected_novaseq_6000_pre_1_5_kits_case_ids,
        selected_novaseq_6000_post_1_5_kits_case_ids,
        selected_novaseq_x_case_ids,
    ]


# Sample sheet creators


@pytest.fixture
def bcl_convert_sample_sheet_creator(
    novaseq_x_flow_cell: IlluminaRunDirectoryData,
    novaseq_x_lims_samples: list[IlluminaSampleIndexSetting],
) -> SampleSheetCreator:
    """Returns a sample sheet creator for sample sheet v2."""
    return SampleSheetCreator(
        run_directory_data=novaseq_x_flow_cell,
        samples=novaseq_x_lims_samples,
    )
