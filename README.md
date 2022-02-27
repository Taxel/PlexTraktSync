# Plex-Trakt-Sync

![Python Versions][python-versions-badge]

This project adds a two-way-sync between trakt.tv and Plex Media Server. It
requires a trakt.tv account but no Plex premium and no Trakt VIP subscriptions,
unlike the Plex app provided by Trakt.

Originally created by [@Taxel], but now maintained by [contributors].

[@Taxel]: https://github.com/Taxel
[contributors]: https://github.com/Taxel/PlexTraktSync/graphs/contributors

Note: The PyTrakt API keys are not stored securely, so if you do not want to have a file containing those on your harddrive, you can not use this project.

**Looking for a way to contribute? Please find issues with the [help-wanted] label
or to improve documentation [docs-needed], thank you.**

[help-wanted]: https://github.com/Taxel/PlexTraktSync/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22
[docs-needed]: https://github.com/Taxel/PlexTraktSync/issues?q=label%3A%22docs+needed%22+sort%3Aupdated-desc

- [Plex-Trakt-Sync](#plex-trakt-sync)
  - [Features](#features)
  - [Pre-requisites](#pre-requisites)
  - [Installation](#installation)
    - [pipx](#pipx)
    - [Docker Compose](#docker-compose)
    - [Windows Setup (optional alternative)](#windows-setup-optional-alternative)
    - [Unraid setup](#unraid-setup)
    - [GitHub](#github)
  - [Setup](#setup)
  - [Sync settings](#sync-settings)
    - [Logging](#logging)
  - [Commands](#commands)
    - [Sync](#sync)
    - [Unmatched](#unmatched)
    - [Info command](#info-command)
    - [Watch](#watch)
      - [Systemd setup](#systemd-setup)

[python-versions-badge]: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10-blue

## Features

- Media in Plex are added to Trakt collection
- Ratings are synced (if ratings differ, Trakt takes precedence)
- Watched status are synced (dates are not reported from Trakt to Plex)
- Liked lists in Trakt are downloaded and all movies in Plex belonging to that
  list are added
- You can edit the [config file](https://github.com/Taxel/PlexTraktSync/blob/HEAD/plextraktsync/config.default.json) to choose what to sync
- None of the above requires a Plex Pass or Trakt VIP membership.
  Downside: Needs to be executed manually or via cronjob,
  can not use live data via webhooks.

## Pre-requisites

The script is known to work with Python 3.7-3.10 versions.

## Installation

- [pipx](#pipx) - _This is the recommended installation method_
- [Docker Compose](#docker-compose)
- [Windows Setup (optional alternative)](#windows-setup-optional-alternative)
- [GitHub](#github)

### pipx

Installation with [pipx][install-pipx].

```
pipx install PlexTraktSync
```

or, to install specific version:

```
pipx install PlexTraktSync==0.15.2 --force
```

and to upgrade:

```
pipx upgrade PlexTraktSync
```

to run:

```
plextraktsync
```

NOTE: `pipx` install will use OS specific paths for Config, Logs, Cache, see [appdirs] documentation for details
or check output of [info command](#info-command).

[appdirs]: https://pypi.org/project/appdirs
[install-pipx]: https://github.com/pypa/pipx#install-pipx

### Docker Compose

You can setup docker compose file like this:

```yaml
services:
  plextraktsync:
    image: ghcr.io/taxel/plextraktsync
    volumes:
      - ./config:/app/config
```

To run sync:

```
docker-compose run --rm plextraktsync
```

To run `watch` command:

```
docker-compose run --rm plextraktsync watch
```
or add `command: watch` to docker compose file, and `docker-compose up -d plextraktsync` to start the container detached:

```yaml
services:
  plextraktsync:
    image: ghcr.io/taxel/plextraktsync
    volumes:
      - ./config:/app/config
    command: watch
```

### Windows Setup (optional alternative)

- Download the latest `.zip` release from https://github.com/Taxel/PlexTraktSync/tags
- Run `setup.bat` to install requirements and create optional shortcuts and routines _(requires Windows 7sp1 - 11)_.

### Unraid setup

Option 1 for container creation:
Create a manual Unraid container of PlexTraktSync:

- Go to the Docker section, under "Docker Containers" and click "Add Container".
  - Click the advanced view to see all of the available parameters.
  - Leave the template blank/unselected.
  - Under Name: enter a name for the docker (e.g., PlexTraktSync).
  - Under Repository: enter `ghcr.io/taxel/plextraktsync:latest` (or whatever tag you want).
  - Under Extra Parameters: enter `-it` for interactive mode.
- Click "Apply".
- The container should start automatically. If not, start it.
- Enter the console for the container.
- Enter `plextraktsync` to start the credential process described above.

Option 2 for container creation: 
Utilize the "Community Apps" Unraid Plugin. 
- Go to the Plugins tab, paste the Community Apps URL in the URL area, and click "Install". 
Once installed (or if already installed):
- Go to the (newly created) Apps tab and search "plextraktsync", and click on the App, and click "Install" (https://forums.unraid.net/topic/38582-plug-in-community-applications/)
- Take all the default settings (the -it switch as outlined elsewhere in the README is already present), and click "Apply". 
- The container then installs, and will start. 


Schedule (cron) the container to start at given intervals to process the sync
- Go to the Plugins tab, past the User Scripts URL in the URL area, and click "Install" (https://forums.unraid.net/topic/48286-plugin-ca-user-scripts/)
Once installed (or if already installed):
- Go to the Plugins tab, click on "User Scripts", and click the "Add New Script" button
- Name your script accordingly
- Click the "gear" icon next to the script name, and click "Edit Script"
- Below the "#!/bin/bash" line add: `docker start PlexTraktSync`
- Click "Save Changes"
- Set the schedule accordingly using the dropdown menu next to the "Run in Background" button


### GitHub

Installing from GitHub is considered developer mode and it's documented in
[CONTRIBUTING.md](CONTRIBUTING.md#checking-out-code).

## Setup

- You will need to create a Trakt API app if you do not already have one:

  - Visit https://trakt.tv/oauth/applications/new
  - Give it a meaningful name
  - Enter `urn:ietf:wg:oauth:2.0:oob` as the redirect url
  - You can leave Javascript origins and the Permissions checkboxes blank

- Run `plextraktsync`, the script will ask for missing credentials

- At first run you will be asked to setup Trakt and Plex access.

  Follow the instructions, your credentials and API keys will be stored in
  `.env` and `.pytrakt.json` files.

  If you have [2 Factor Authentication enabled on Plex](https://support.plex.tv/articles/two-factor-authentication/#toc-1:~:text=Old%20Third%2DParty%20Apps%20%26%20Tools) you can append the code to your password.

* Cronjobs can be optionally used on Linux or macOS to run the script at set intervals.

  For example, to run this script in a cronjob every two hours:

  ```
  $ crontab -e
  0 */2 * * * plextraktsync
  ```

## Sync settings

To disable parts of the functionality of this software, look no further than
`config.json`. Here, in the sync section, you can disable the following things
by setting them from `true` to `false` in a text editor:

At first run, the script will create `config.json` based on `config.default.json`.
If you want to customize settings before first run (eg. you don't want full
sync) you can copy and edit `config.json` before launching the script.

- Downloading liked lists from Trakt and adding them to Plex
- Downloading your watchlist from Trakt and adding it to Plex
- Syncing the watched status between Plex and Trakt
- Syncing the collected status between Plex and Trakt

The first execution of the script will (depending on your PMS library size)
take a long time. After that, movie details and Trakt lists are cached, so
it should run a lot quicker the second time. This does mean, however, that
Trakt lists are not updated dynamically (which is fine for lists like "2018
Academy Award Nominees" but might not be ideal for lists that are updated
often). Here are the execution times on my Plex server: First run - 1228
seconds, second run - 111 seconds

You can view sync progress in the `plextraktsync.log` file which will be created.

### Logging

The logging level by default is `INFO`. This can be changed to DEBUG by editing the "debug" variable in `config.json` to `true`.

By default the logs will append, if you wish to maintain the log of only your last run then edit the "append" variable in `config.json` to `false`.

## Commands

### Sync

The `sync` subcommand supports `--sync=shows` and `--sync=movies` options,
so you can sync only specific library types.

```
➔ plextraktsync sync --help
Usage: plextraktsync sync [OPTIONS]

  Perform sync between Plex and Trakt

Options:
  --sync [all|movies|shows] Specify what to sync  [default: all]
  --help                    Show this message and exit.
```

### Unmatched

You can use `unmatched` command to scan your library and display unmatched movies.

Support for unmatched shows is not yet implemented.

`plextraktsync unmatched`

### Info command

The info command can be used to print package versions,
account information,
locations of Cache, Config and Logs directories

```
$ plextraktsync info
PlexTraktSync Version: 0.16.0
Python Version: 3.10.0 (default, Oct  6 2021, 01:11:32) [Clang 13.0.0 (clang-1300.0.29.3)]
Plex API Version: 4.7.2
Trakt API Version: 3.2.1
Cache Dir: /Users/glen/Library/Caches/PlexTraktSync
Config Dir: /Users/glen/Library/Application Support/PlexTraktSync
Log Dir: /Users/glen/Library/Logs/PlexTraktSync
Plex username: nobody
Trakt username: nobody
Plex Server version: 1.24.3.5033-757abe6b4, updated at: 2021-02-21 17:00:00
Server has 2 libraries: ['Movies', 'TV Shows']
```

### Watch

You can use the `watch` command to listen to events from Plex Media Server
and scrobble plays.

`plextraktsync watch`

> What is scrobbling?
>
> _Scrobbling simply means automatically tracking what you’re watching. Instead
> of checking in from your phone of the website, this command runs in the
> background and automatically scrobbles back to Trakt while you enjoy watching
> your media_ - [Plex Scrobbler@blog.trakt.tv][plex-scrobbler]

[plex-scrobbler]: https://blog.trakt.tv/plex-scrobbler-52db9b016ead

To restrict scrobbling to your user **only** (recommended), set the following in your `config.json`:

```json
{
    "watch": {
        "username_filter": true
    }
}
```

#### Systemd setup

Create a systemd unit so that it scrobbles automatically in the background:

```ini
[Unit]
Description=PlexTraktSync watch daemon
After=network-online.target

[Service]
ExecStart=plextraktsync watch
Restart=on-failure
RestartSec=10
User=user
Group=user

[Install]
WantedBy=multi-user.target
```
Note, depending on your install method you may need to set your ExecStart command as follows:

```
ExecStart=/path/to/plextraktsync/plextraktsync.sh watch
```

Following that you will need to enable the service:

```
sudo systemctl daemon-reload
sudo systemctl start PlexTrackSync.service
sudo systemctl enable PlexTrackSync.service
```
