"""Hold encryption sbatch templates in variables."""

FLOW_CELL_ENCRYPT_ERROR = """
if [[ -e {pending_file_path} ]]
then
    rm -f {pending_file_path}
fi
"""

FLOW_CELL_ENCRYPT_COMMANDS = """
{symmetric_passphrase}

{asymmetrically_encrypt_passphrase}

{make_tmp_encrypt_dir}

{copy_flow_cell_dir_to_tmp}

{tar_encrypt_tmp_dir} | {parallel_gzip} | {tee} | {flow_cell_symmetric_encryption}

{flow_cell_symmetric_decryption} | {md5sum}

{diff}

{mv_passphrase_file}

{remove_pending_file}

{flag_as_complete}

{remove_tmp_encrypt_dir}
"""
