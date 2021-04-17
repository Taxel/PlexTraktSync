#!/bin/sh
set -eu

dir=$(dirname "$0")

exec python3 "$dir/main.py" "$@"
