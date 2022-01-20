#!/bin/sh
set -eu

file=$(readlink -f "$0")
dir=$(dirname "$file")
cd "$dir"

exec python3 -m plextraktsync "$@"
