"""Hold encryption sbatch templates in variables."""

FLOW_CELL_ENCRYPT_ERROR = """
if [[ -e {spring_path} ]]
then
    rm -rf {flow_cell_encrypt_dir}
fi
"""

FLOW_CELL_ENCRYPT_COMMANDS = """
{symmetric_passphrase_cmd}
{asymmetrically_encrypt_passphrase_cmd}
{tar_encrypt_flow_cell_dir_cmd} | {parallel_gzip_cmd} | {tee_cmd} | {flow_cell_symmetric_encryption_cmd}
{flow_cell_symmetric_decryption_cmd} | {md5sum_cmd}
{diff_cmd}
{mv_passphrase_file_cmd}
{remove_pending_file}
"""
