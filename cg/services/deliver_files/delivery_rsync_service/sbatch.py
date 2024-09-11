"""Sbatch templates for the rsync function"""

RSYNC_COMMAND = """
rsync -rvL {source_path} {destination_path}
"""

RSYNC_CONTENTS_COMMAND = """
rsync -rvL {source_path}/ {destination_path}
"""

COVID_RSYNC = """
rsync -rvL {source_path} {destination_path}
rsync -rvL --chmod=777 {covid_report_path} {covid_destination_path}
"""

COVID_REPORT_RSYNC = """
rsync -rvL --chmod=777 {covid_report_path} {covid_destination_path}
"""

ERROR_RSYNC_FUNCTION = """
echo "Rsync failed"
"""
