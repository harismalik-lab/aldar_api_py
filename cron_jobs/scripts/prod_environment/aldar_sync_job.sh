#!/usr/bin/env bash
echo $1
export APPLICATION_SETTINGS=/home/apicron/script/adr_scripts/cron_jobs/configs/prod_settings.py
source /home/apicron/script/adr_scripts/envname/bin/activate
python /home/apicron/script/adr_scripts/cron_jobs/aldar_csv_data_sync.py -sftp_file_dir $1
deactivate
