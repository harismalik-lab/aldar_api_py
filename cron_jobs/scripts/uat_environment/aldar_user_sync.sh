#!/usr/bin/env bash
export APPLICATION_SETTINGS=/home/entutebizapi/theentertainer-python/adr_scripts/cron_jobs/configs/uat_settings.py
source /home/entutebizapi/theentertainer-python/adr_scripts/envname/bin/activate
python /home/entutebizapi/theentertainer-python/adr_scripts/cron_jobs/aldar_user_sync.py
deactivate
