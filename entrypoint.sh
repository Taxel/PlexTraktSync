#!/bin/sh
: ${TRACE:=}
: ${APP_USER:=plextraktsync}
: ${APP_GROUP:=plextraktsync}

ensure_dir() {
	install -o "$APP_USER" -g "$APP_GROUP" -d "$@"
}

ensure_owner() {
	chown "$APP_USER:$APP_GROUP" "$@"
}

# change uid/gid of app user if requested
setup_user() {
	local uid=${PUID:-}
	local gid=${PGID:-}

	if [ -n "$uid" ] && [ "$(id -u $APP_USER)" != "$uid" ]; then
		usermod -u "$uid" "$APP_USER"
	fi
	if [ -n "$gid" ] && [ "$(id -g $APP_GROUP)" != "$gid" ]; then
		groupmod -g "$gid" "$APP_GROUP"
	fi
}

# Run command as app user
# https://github.com/karelzak/util-linux/issues/325
switch_user() {
	local uid=$(id -u "$APP_USER")
	local gid=$(id -g "$APP_GROUP")

	exec setpriv --euid "$uid" --ruid "$uid" --clear-groups --egid "$gid" --rgid "$gid" -- "$@"
}

fix_permissions() {
	ensure_dir /app/config
	ensure_owner /app/config -R
}

needs_switch_user() {
	local uid=${PUID:-0}
	local gid=${PGID:-0}

	# configured to run as non-root
	if [ "$uid" -eq 0 ] && [ "$gid" -eq 0 ]; then
		return 1
	fi

	# must be root to be able to switch user
	[ "$(id -u)" -eq 0 ]
}

set -eu
test -n "$TRACE" && set -x

# prepend default command
set -- python -m plextraktsync "$@"

# fix permissions and switch user if configured
if needs_switch_user; then
	setup_user
	fix_permissions
	switch_user "$@"
fi

exec "$@"
