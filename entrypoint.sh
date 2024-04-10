#!/bin/sh
: ${TRACE:=}
: ${APP_USER:=plextraktsync}
: ${APP_GROUP:=plextraktsync}

msg() {
	echo >&2 "* $*"
}

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
		usermod -o -u "$uid" "$APP_USER"
	fi
	if [ -n "$gid" ] && [ "$(id -g $APP_GROUP)" != "$gid" ]; then
		groupmod -o -g "$gid" "$APP_GROUP"
	fi
}

# Run command as app user
# https://github.com/karelzak/util-linux/issues/325
run_user() {
	local uid=$(id -u "$APP_USER")
	local gid=$(id -g "$APP_GROUP")

	setpriv --euid "$uid" --ruid "$uid" --clear-groups --egid "$gid" --rgid "$gid" -- "$@"
}

switch_user() {
	local uid=$(id -u "$APP_USER")
	local gid=$(id -g "$APP_GROUP")

	exec setpriv --euid "$uid" --ruid "$uid" --clear-groups --egid "$gid" --rgid "$gid" -- "$@"
}

fix_permissions() {
	ensure_dir /app/config
	ensure_owner /app/config -R
	ensure_owner "$HOME"
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

# Test docker image health
if [ "${1:-}" = "test" ]; then
	# Check tools linkage
	ldd /usr/bin/setpriv
	ldd /usr/bin/usermod
	ldd /usr/bin/groupmod
	# Continue with info command
	set -- "info"
fi

# fix permissions and switch user if configured
if needs_switch_user; then
	setup_user
	fix_permissions
fi

# Shortcut to pre-install "pipx" and enter as "sh"
if [ "${1:-}" = "pipx" ]; then
	# https://github.com/Taxel/PlexTraktSync/blob/main/CONTRIBUTING.md#install-code-from-pull-request
	msg "Installing git"
	apk add git
	msg "Installing pipx"
	run_user pip install pipx
	if [ ! -x "$PIPX_BIN_DIR/plextraktsync" ]; then
		msg "Installing plextraktsync from pipx"
		run_user pipx install plextraktsync
	fi
	set -- "sh"
fi

# Use "sh" command to passthrough to shell
if [ "${1:-}" != "sh" ]; then
	# Prepend default command
	set -- python -m plextraktsync "$@"
fi

# fix permissions and switch user if configured
if needs_switch_user; then
	switch_user "$@"
fi

exec "$@"
