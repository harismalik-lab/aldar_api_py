#!/usr/bin/env bash
echo $1
export APPLICATION_SETTINGS=/home/entutebizapi/theentertainer-python/adr_scripts/cron_jobs/configs/uat_settings.py
source /home/entutebizapi/theentertainer-python/adr_scripts/envname/bin/activate
python /home/entutebizapi/theentertainer-python/adr_scripts/cron_jobs/aldar_csv_data_sync.py -sftp_file_dir $1
deactivate
