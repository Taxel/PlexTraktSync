#!/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:~/bin:/usr/bin:/bin:/usr/sbin:/sbin
set -eu

file=$(readlink -f "$0")
dir=$(dirname "$file")
date=$(date --rfc-3339=ns | tr ' ' '_')

if python3 "$dir/main.py" "$@"; then
	mv last_update.log "update-$date.log"
else
	mv last_update.log "error-$date.log"
fi
