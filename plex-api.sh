#!/bin/sh

# Get PLEX_SERVER value from .env
get_plex_server() {
	awk -F= '$1 == "PLEX_SERVER" {print $2}' .env
}

load_servers() {
	python -c 'import yaml; import json; fp=open("servers.yml"); print(json.dumps(yaml.safe_load(fp)["servers"]))'
}

get_server() {
	local name="$1"

	load_servers | jq ".$name"
}

get_plex_token() {
	local name server

	name=${PLEX_SERVER:-$(get_plex_server)}
	server=$(get_server "$name")

	echo "$server" | jq -r ".token"
}

: "${PLEX_TOKEN=$(get_plex_token)}"

curl -sSf \
	 --header "X-Plex-Token: $PLEX_TOKEN" \
	 "$@"
