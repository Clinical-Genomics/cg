"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
rsync -rvL {source_path} {destination_path}
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
