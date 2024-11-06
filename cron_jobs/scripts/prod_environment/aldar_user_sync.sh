#!/usr/bin/env bash
export APPLICATION_SETTINGS=/home/apicron/script/adr_scripts/cron_jobs/configs/prod_settings.py
source /home/apicron/script/adr_scripts/envname/bin/activate
python /home/apicron/script/adr_scripts/cron_jobs/aldar_user_sync.py
deactivate
