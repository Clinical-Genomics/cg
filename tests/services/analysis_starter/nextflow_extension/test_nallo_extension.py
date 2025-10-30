from cg.services.analysis_starter.configurator.extensions.nallo import NalloExtension
from tests.services.analysis_starter.file_creators.test_gene_panel_file_creator import (
    gene_panel_creator,
)


def test_configure():
    # GIVEN a Nallo extension
    nallo_extension = NalloExtension()

    # WHEN configuring a case
    nallo_extension.configure()

    # THEN a gene panel file should have been created
    gene_panel_creator.create.assert_called_once_with(case_id="case_id", file_path=".tsv")
