from unittest.mock import Mock

from cg.services.analysis_starter.configurator.extensions.raredisease import RarediseaseExtension


def test_configure_success():
    # GIVEN a raredisease pipeline extension
    raredisease_extension = RarediseaseExtension(
        gene_panel_file_creator=Mock(), managed_variants_file_creator=Mock()
    )
    # WHEN calling configure
    raredisease_extension.configure(case_id="case_id")

    # THEN the file creators should have been called
    raredisease_extension.gene_panel_file_creator.configure.assert_called_once_with()
    raredisease_extension.managed_variants_file_creator.configure.assert_called_once_with()
