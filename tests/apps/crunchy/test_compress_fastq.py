"""Test methods for compressing FASTQ"""
import json
import logging

from cg.apps.crunchy import CrunchyAPI


def test_get_spring_metadata(spring_metadata_file, crunchy_config_dict):
    """Test the method that fetches the SPRING metadata from a file"""
    # GIVEN a SPRING path and the path to a populated SPRING metadata file
    assert spring_metadata_file.is_file()
    assert spring_metadata_file.exists()
    # GIVEN a crunchy API
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN fetching the content of the file
    parsed_content = crunchy_api.get_spring_metadata(spring_metadata_file)

    # THEN assert information about the three files is there
    assert len(parsed_content) == 3
    # THEN assert a list with the files is returned
    assert isinstance(parsed_content, list)


def test_get_spring_archive_files(spring_metadata):
    """Test the method that sorts the SPRING metadata into a dictionary"""
    # GIVEN a SPRING metadata content in its raw format
    assert isinstance(spring_metadata, list)

    # WHEN fetching the content of the file
    parsed_content = CrunchyAPI.get_spring_archive_files(spring_metadata)

    # THEN assert information about the three files is there
    assert len(parsed_content) == 3
    # THEN assert a dictionary with the files is returned
    assert isinstance(parsed_content, dict)


def test_get_spring_metadata_malformed_info(
    spring_metadata_file, spring_metadata, crunchy_config_dict
):
    """Test the method that fetches the SPRING metadata from a file when file is malformed"""
    # GIVEN a SPRING metadata file with missing information
    spring_metadata[0].pop("path")
    with open(spring_metadata_file, "w") as outfile:
        outfile.write(json.dumps(spring_metadata))

    # GIVEN a crunchy API
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN fetching the content of the file
    parsed_content = crunchy_api.get_spring_metadata(spring_metadata_file)

    # THEN assert that None is returned to indicate failure
    assert parsed_content is None


def test_get_spring_metadata_wrong_number_files(
    spring_metadata_file, spring_metadata, crunchy_config_dict
):
    """Test the method that fetches the SPRING metadata from a file when a file is missing"""
    # GIVEN a SPRING metadata file with missing file
    spring_metadata = spring_metadata[1:]
    with open(spring_metadata_file, "w") as outfile:
        outfile.write(json.dumps(spring_metadata))

    # GIVEN a crunchy API
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN fetching the content of the file
    parsed_content = crunchy_api.get_spring_metadata(spring_metadata_file)

    # THEN assert that None is returned to indicate failure
    assert parsed_content is None


def test_fastq_to_spring_sbatch(crunchy_config_dict, compression_object, sbatch_process, caplog):
    """Test fastq_to_spring method"""
    caplog.set_level(logging.DEBUG)
    # GIVEN a crunchy-api, and FASTQ paths

    crunchy_api = CrunchyAPI(crunchy_config_dict)
    crunchy_api.process = sbatch_process
    spring_path = compression_object.spring_path
    log_path = crunchy_api.get_log_dir(spring_path)
    run_name = compression_object.run_name
    sbatch_path = crunchy_api.get_sbatch_path(log_path, "fastq", run_name)

    # GIVEN that the sbatch file does not exist
    assert not sbatch_path.is_file()

    # WHEN calling fastq_to_spring on FASTQ files
    crunchy_api.fastq_to_spring(compression_obj=compression_object)

    # THEN assert that the sbatch file was created
    assert sbatch_path.is_file()


def test_spring_to_fastq(compression_object, spring_metadata_file, crunchy_config_dict, mocker):
    """Test SPRING to FASTQ method

    Test to decompress SPRING to FASTQ. This test will make sure that the correct sbatch content
    was submitted to the Process api
    """
    # GIVEN a crunchy-api given an existing SPRING metadata file
    assert spring_metadata_file.exists()
    mocker_submit_sbatch = mocker.patch.object(CrunchyAPI, "_submit_sbatch")
    crunchy_api = CrunchyAPI(crunchy_config_dict)

    # WHEN calling bam_to_cram method on bam-path
    crunchy_api.spring_to_fastq(compression_obj=compression_object)

    # THEN _submit_sbatch method is called
    mocker_submit_sbatch.assert_called()
