"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
rsync -rvL {source_path} {destination_path}
"""

COVID_RSYNC = """
rsync -rvL {source_path} {destination_path}
rsync -rvL {covid_report_path} {covid_destination_path}
touch {log_dir}/rsync_complete.txt
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
