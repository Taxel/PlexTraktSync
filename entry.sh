#!/bin/sh

# copy /var/config.json to /var/config/config.json if it does not exist
if [ ! -f /var/config/config.json ]; then
    echo "config.json does not exist. copying it."
    cp /var/config.json /var/config/config.json
fi

if [[ ! -z "${RUN_ONCE}" ]]; then
    echo "RUN_ONCE specified. Running script without cronjob."
    python3 /var/src/main.py
    exit 0
fi


if [[ -z "${CRON_SCHEDULE}" ]]; then
  echo "Running the script every 2 hours (CRON_SCHEDULE='0 */2 * * *'). Set environment var 'CRON_SCHEDULE' to a valid cron expression to configure this"
  echo "If you want to run the script only once, specify the environment var 'RUN_ONCE=1'"
  SCHEDULE="0 */2 * * *"
else
  SCHEDULE="${CRON_SCHEDULE}"
fi
# install cronjob
(crontab -l ; echo "$SCHEDULE python3 /var/src/main.py") | sort - | uniq - | crontab -
# run crond so the container does not terminate
crond -l 2 -f