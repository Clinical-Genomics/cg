from pathlib import Path

from cg.constants.scout import ScoutExportFileName
from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from cg.services.analysis_starter.configurator.file_creators.gene_panel import GenePanelFileCreator
from tests.typed_mock import TypedMock, create_typed_mock


def test_configure():
    gene_panel_file_creator: TypedMock[GenePanelFileCreator] = create_typed_mock(
        GenePanelFileCreator
    )

    # GIVEN a Nallo extension
    nallo_extension = NalloExtension(gene_panel_file_creator=gene_panel_file_creator.as_type)
    case_run_directory = Path("case", "run", "directory")

    # WHEN configuring a case
    nallo_extension.configure(case_id="nallo_case", case_run_directory=case_run_directory)

    # THEN a gene panel file should have been created
    gene_panel_file_creator.as_mock.create.assert_called_once_with(
        case_id="nallo_case",
        file_path=case_run_directory / ScoutExportFileName.PANELS_TSV,
        header_filtering=True,
    )
