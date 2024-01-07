#!/bin/sh

: "${TRAKT_API_KEY=$(jq -r .CLIENT_ID < .pytrakt.json)}"
: "${TRAKT_AUTHORIZATION=Bearer $(jq -r .OAUTH_TOKEN < .pytrakt.json)}"

curl -sSf \
     --header "Content-Type: application/json" \
     --header "trakt-api-version: 2" \
     --header "trakt-api-key: $TRAKT_API_KEY" \
     --header "Authorization: $TRAKT_AUTHORIZATION" \
	 "$@"
