# Plex-Trakt-Sync

![Python Versions][python-versions-badge]

This project adds a two-way-sync between trakt.tv and Plex Media Server. It
requires a trakt.tv account but no Plex premium and no Trakt VIP subscriptions,
unlike the Plex app provided by Trakt.

![image](https://raw.githubusercontent.com/twolaw/PlexTraktSync/img/plextraktsync_banner.png)

Originally created by [@Taxel][@taxel], but now maintained by [contributors].

[@taxel]: https://github.com/Taxel
[contributors]: https://github.com/Taxel/PlexTraktSync/graphs/contributors

Note: The PyTrakt API keys are not stored securely, so if you do not want to
have a file containing those on your harddrive, you can not use this project.

**Looking for a way to contribute? Please find issues with the [help-wanted]
label or to improve documentation [docs-needed], thank you.**

[help-wanted]: https://github.com/Taxel/PlexTraktSync/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22
[docs-needed]: https://github.com/Taxel/PlexTraktSync/issues?q=label%3A%22docs+needed%22+sort%3Aupdated-desc

- [Plex-Trakt-Sync](#plex-trakt-sync)
  - [Features](#features)
  - [Pre-requisites](#pre-requisites)
  - [Installation](#installation)
    - [pipx](#pipx)
    - [Docker Compose](#docker-compose)
    - [Install code from Pull request](#install-code-from-pull-request), development
    - [Windows Setup (optional alternative)](#windows-setup-optional-alternative), unsupported
    - [Unraid setup](#unraid-setup), unsupported
    - [GitHub](#github), unsupported
  - [Setup](#setup)
  - [Sync settings](#sync-settings)
    - [Logging](#logging)
  - [Commands](#commands)
    - [Sync](#sync)
    - [Unmatched](#unmatched)
    - [Info command](#info-command)
    - [Watch](#watch)
      - [Systemd setup](#systemd-setup)
  - [Good practices](#good-practices)
  - [Troubleshooting](#troubleshooting)

[python-versions-badge]: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9%20%7C%203.10%20%7C%203.11-blue

## Features

- Media in Plex are added to Trakt collection
- Ratings are synced (if ratings differ, Trakt takes precedence)
- Watched status are synced (dates are not reported from Trakt to Plex)
- Liked lists in Trakt are downloaded and all movies in Plex belonging to that
  list are added
- Watchlists are synced
- You can edit the config file to choose what to sync
- None of the above requires a Plex Pass or Trakt VIP membership.
  Downside: Needs to be executed manually or via cronjob,
  can not use live data via webhooks.

## Pre-requisites

The script is known to work with Python 3.7-3.10 versions.

## Installation

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
plextraktsync self-update
```

which just calls `pipx` with:

```
pipx upgrade PlexTraktSync
```

to run:

```
plextraktsync
```

NOTE: `pipx` install will use OS specific paths for Config, Logs, Cache, see
[appdirs] documentation for details or check output of [info command](#info-command).

[appdirs]: https://pypi.org/project/appdirs
[install-pipx]: https://github.com/pypa/pipx#install-pipx

### Docker Compose

You can setup docker compose file like this:

```yaml
version: '2'
services:
  plextraktsync:
    image: ghcr.io/taxel/plextraktsync
    container_name: plextraktsync
    restart: on-failure:2
    volumes:
      - ./config:/app/config
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Europe/Tallinn
```

#### Run the Docker Container

To run sync:

```
docker-compose run --rm plextraktsync
```

The container will stop after the sync is completed. Read Setup section to run
it automatically at set intervals.

### Install code from Pull request

This is to install development version to test if pull request would fix some problem.

See contributing guide how to [install code from pull request].

[install code from pull request]: CONTRIBUTING.md#install-code-from-pull-request

### Windows Setup (optional alternative)

NOTE: _This installation method is not supported. It's documented solely by user contribution._

- Download the latest `.zip` release from https://github.com/Taxel/PlexTraktSync/tags
- Run `setup.bat` to install requirements and create optional shortcuts and
  routines _(requires Windows 7sp1 - 11)_.

### Unraid setup

NOTE: _This installation method is not supported. It's documented solely by user contribution._

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
- Go to the (newly created) Apps tab and search "plextraktsync", and click on
  the App, and click "Install" (https://forums.unraid.net/topic/38582-plug-in-community-applications/)
- Take all the default settings (the -it switch as outlined elsewhere in the
  README is already present), and click "Apply".
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

NOTE: _This installation method is not supported._ You will not get support if you use this installation method.

Installing from GitHub is considered developer mode, and it's documented in
[CONTRIBUTING.md](CONTRIBUTING.md#checking-out-code).

## Setup

- You will need to create a Trakt API app if you do not already have one:

  - Visit https://trakt.tv/oauth/applications/new
  - Give it a meaningful name
  - Enter `urn:ietf:wg:oauth:2.0:oob` as the redirect url
  - You can leave Javascript origins and the Permissions checkboxes blank

- Run `plextraktsync`, the script will ask for missing credentials

  > **Note**
  > To setup the credentials in the Docker Container, refer to the [Run the Docker Container](#run-the-docker-container) section

- At first run you will be asked to setup Trakt and Plex access.

  Follow the instructions, your credentials and API keys will be stored in
  `.env` and `.pytrakt.json` files.

  If you have [2 Factor Authentication enabled on Plex][two-factor-authentication] you can append the code to your password.

[two-factor-authentication]: https://support.plex.tv/articles/two-factor-authentication/#toc-1:~:text=Old%20Third%2DParty%20Apps%20%26%20Tools

- Cronjobs can be optionally used on Linux or macOS to run the script at set intervals.

  For example, to run this script in a cronjob every two hours:

  ```
  $ crontab -e
  0 */2 * * * $HOME/.local/bin/plextraktsync
  ```

  - Note the command in the example above may not immediately work. Use the `which plextraktsync` command to locate your system's plextraktsync executable file and update it accordingly.

- Instead of cron, a docker scheduler like [Ofelia][ofelia] can also be used to
  run the script at set intervals.

[ofelia]: https://github.com/mcuadros/ofelia/

A docker-compose example with a 6h interval:

```yaml
version: '2'
services:
  scheduler:
    image: mcuadros/ofelia:latest
    container_name: scheduler
    depends_on:
      - plextraktsync
    command: daemon --docker
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    labels:
      ofelia.job-run.plextraktsync.schedule: "@every 6h"
      ofelia.job-run.plextraktsync.container: "plextraktsync"
  plextraktsync:
    image: ghcr.io/taxel/plextraktsync:latest
    container_name: plextraktsync
    volumes:
      - ./config:/app/config
```

## Sync settings

To disable parts of the functionality of this software, look no further than
`config.yml`. Here, in the sync section, you can disable the following things
by setting them from `true` to `false` in a text editor:

At first run, the script will create `config.yml` based on
`config.default.yml`. If you want to customize settings before first run (eg.
you don't want full sync) you can copy and edit `config.yml` before launching
the script.

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

You can view sync progress in the `plextraktsync.log` file which will be
created.

### Logging

The logging level by default is `INFO`. This can be changed to DEBUG by editing
the "debug" variable in `config.yml` to `true`.

By default the logs will append, if you wish to maintain the log of only your
last run then edit the "append" variable in `config.yml` to `false`.

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

You can use `unmatched` command to scan your library and display unmatched
movies.

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
and scrobble plays. It does NOT run a sync between Plex and Trakt.

> What is scrobbling?
>
> _Scrobbling simply means automatically tracking what you’re watching. Instead
> of checking in from your phone of the website, this command runs in the
> background and automatically scrobbles back to Trakt while you enjoy watching
> your media_ - [Plex Scrobbler@blog.trakt.tv][plex-scrobbler]

[plex-scrobbler]: https://blog.trakt.tv/plex-scrobbler-52db9b016ead

To restrict scrobbling to your user **only** (recommended), set the following
in your `config.yml`:

```yaml
watch:
  username_filter: true
```

To run `watch` command:

`plextraktsync watch`

or

```
docker-compose run --rm plextraktsync watch
```

or add `command: watch` to docker compose file, and `docker-compose up -d
plextraktsync` to start the container detached:

```yaml
version: '2'
services:
  plextraktsync:
    image: ghcr.io/taxel/plextraktsync
    volumes:
      - ./config:/app/config
    command: watch
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

Note, depending on your install method you may need to set your ExecStart
command as follows:

```ini
ExecStart=/path/to/plextraktsync/plextraktsync.sh watch
```

Following that you will need to enable the service:

```
sudo systemctl daemon-reload
sudo systemctl start PlexTraktSync.service
sudo systemctl enable PlexTraktSync.service
```

## Good practices

- Using default `Plex Movie` and `Plex TV Series` [metadata agents] improves
  script compatibility (for matching or for watchlist).
  It is recommended to [migrate to the new Plex TV Series agent][migrating-agent-scanner].
- Organize your shows folders and naming according to [Plex standard][naming-tv-show-files]
  and [theMovieDatabase][tmdb] (tmdb) order. If Plex doesn't properly identify your media,
  you can use the [Fix Match][fix-match] and the [Match Hinting][plexmatch].
  Also check the Episode Ordering preference (under Advanced) to correspond with your files.
- Use tmdb as source for TV Shows if possible,
  because it's the Trakt [primary data source][tv-show-metadata]
  ([switched from tvdb in Jan-2021][tmdb-transition]).

[fix-match]: https://support.plex.tv/articles/201018497-fix-match-match/
[metadata agents]: https://support.plex.tv/articles/200241558-agents/
[migrating-agent-scanner]: https://support.plex.tv/articles/migrating-a-tv-library-to-use-the-new-plex-tv-series-agent-scanner/
[naming-tv-show-files]: https://support.plex.tv/articles/naming-and-organizing-your-tv-show-files/
[plexmatch]: https://support.plex.tv/articles/plexmatch/
[tmdb-transition]: https://blog.trakt.tv/tmdb-transition-ef3d19a5cf24
[tmdb]: https://themoviedb.org/
[tv-show-metadata]: https://blog.trakt.tv/tv-show-metadata-e6e64ed4e6ef

## Troubleshooting

### I have duplicate watched episodes sent to Trakt at every sync

Check your Plex episodes ordering compared to Trakt ordering.
If episodes are in a different order, it should not be a problem because they
are identified with ids.
But if a season or an episode is missing on Trakt (and tmdb) it can't be synced.
You can fix it by [adding the missing episodes] or edit metadata (eg. missing
tvdb or imdb ids) on [tmdb] or [report a metadata issue on Trakt][how-to-report-metadata-issues] ([answers][reports]. It's free for anyone
to sign up and edit info at tmdb. Trakt will [update from tmdb][trakt-tvshow-update] data.

[adding the missing episodes]: https://support.trakt.tv/support/solutions/articles/70000264977
[tmdb]: https://themoviedb.org/
[trakt-tvshow-update]: https://support.trakt.tv/support/solutions/articles/70000260936-how-does-movie-tv-show-information-metadata-get-updated-how-can-i-refresh-or-sync-trakt-to-tmdb-
[how-to-report-metadata-issues]: https://support.trakt.tv/support/solutions/articles/70000627644-how-to-report-metadata-issues
[reports]: https://trakt.tv/settings/reports

### I have many matching errors in logs

Make sure you use [good practices](#good-practices) about Plex agent and files
organization as stated above.
Check if episodes are not missing on Trakt as explained in previous answer, and
check if [external ids][house-of-the-dragon] are populated on tmdb.

[house-of-the-dragon]: https://www.themoviedb.org/tv/94997-house-of-the-dragon/season/1/episode/1/edit?active_nav_item=external_ids

### I have season 0 matching errors

Season 0 folder must only contains episodes being officially in season 0.
Trailers, deleted scenes, featurettes, interviews,... must be stored in a
separate [Extra folder][extra-folder] according to Plex rules.
Keep in mind that seasons 0 are not really official so datasources (tmdb, imdb
and tvdb) sometimes don't correspond.
Use tmdb as Plex source as much as you can.

[extra-folder]: https://support.plex.tv/articles/local-files-for-tv-show-trailers-and-extras/

### How to sync multiple users ?

The easiest way is to use containers with custom config folder for each user:
[Multi-User docker-compose][discussions/997].

[discussions/997]: https://github.com/Taxel/PlexTraktSync/discussions/997

### Can this run on Synology, HomeAssistant, Portainer,... ?

Yes using docker, check [Discussions][discussions] page.

### I have another question

Check [Discussions][discussions], maybe someone already asked and found the answer.

[discussions]: https://github.com/Taxel/PlexTraktSync/discussions
