#!/bin/sh
PATH=/usr/local/bin:/usr/local/sbin:~/bin:/usr/bin:/bin:/usr/sbin:/sbin
set -eu

dir=$(dirname "$0")

exec python3 "$dir/main.py" "$@"
