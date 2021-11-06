#!/bin/sh
set -eu

dir=$(dirname "$0")
cd "$dir"

exec python3 -m plextraktsync "$@"
