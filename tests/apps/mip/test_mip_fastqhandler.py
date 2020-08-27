"""Test FastqHandler"""

from cg.apps import tb
from cg.apps.mip.fastq import FastqHandler
from cg.store import Store


def test_link_file_count(
    cg_config,
    link_family,
    simple_files_data,
    store: Store,
    tb_api: tb.TrailblazerAPI,
    helpers,
):
    """Test method to test that the right number of files are created by linking"""

    # GIVEN some fastq-files belonging to family and sample
    link_files = simple_files_data
    # GIVEN a store populated with a sample
    sample = helpers.add_sample(store)

    # WHEN calling the method to link
    FastqHandler(cg_config, store, tb_api).link(
        case=link_family, sample=sample.internal_id, files=link_files
    )

    # THEN assert that the linking function was called
    assert tb_api.link_was_called()
