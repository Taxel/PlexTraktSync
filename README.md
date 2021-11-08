# Plex-Trakt-Sync

![Python Versions][python-versions-badge]

This project adds a two-way-sync between trakt.tv and Plex Media Server. It
requires a trakt.tv account but no Plex premium and no Trakt VIP subscriptions,
unlike the Plex app provided by Trakt.

Note: The PyTrakt API keys are not stored securely, so if you do not want to have a file containing those on your harddrive, you can not use this project.

**To contribute, please find issues with the [`help-wanted`](https://github.com/Taxel/PlexTraktSync/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) label, thank you.**

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
- [GitHub download](#github-download)
- [GitHub clone](#github-clone)
- [Docker Compose](#docker-compose)
- [Windows Setup (optional alternative)](#windows-setup-optional-alternative)

### pipx

Installation with [pipx][install-pipx].

```
pipx install PlexTraktSync
```

to install specific version:

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

### GitHub download

- Find the latest release from https://github.com/Taxel/PlexTraktSync/tags
- Download the `.tar` or `.zip`
- Extract to `PlexTraktSync` directory

Proceed to [Install dependencies](#install-dependencies)

### GitHub clone

- Find the latest release from https://github.com/Taxel/PlexTraktSync/tags
- Checkout the release with Git:
  ```
  git clone -b 0.15.0 --depth=1 https://github.com/Taxel/PlexTraktSync
  ```

NOTE: Use released versions, when making bug reports.

Proceed to [Install dependencies](#install-dependencies)

### Install dependencies

This applies to [GitHub download](#github-download) and [GitHub clone](#github-clone).

In the `PlexTraktSync` directory, install the required Python packages:
```
python3 -m pip install -r requirements.txt
```

To run from `PlexTraktSync` directory:
```
python3 -m plextraktsync
```

Or use a wrapper which is able to change directory accordingly:
```
/path/to/PlexTraktSync/plextraktsync.sh
```

*or* alternatively you can use [pipenv]:

```
python3 -m pip install pipenv
pipenv install
pipenv run plextraktsync
```

[pipenv]: https://pipenv.pypa.io/

## Docker Compose

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

## Setup

- You will need to create a Trakt API app if you do not already have one:

  - Visit https://trakt.tv/oauth/applications/new
  - Give it a meaningful name
  - Enter `urn:ietf:wg:oauth:2.0:oob` as the redirect url
  - You can leave Javascript origins and the Permissions checkboxes blank

- Run `python3 -m plextraktsync`.

- At first run you will be asked to setup Trakt and Plex access.

  Follow the instructions, your credentials and API keys will be stored in
  `.env` and `.pytrakt.json` files.

  If you have [2 Factor Authentication enabled on Plex](https://support.plex.tv/articles/two-factor-authentication/#toc-1:~:text=Old%20Third%2DParty%20Apps%20%26%20Tools) you can append the code to your password.

* Cronjobs can be optionally used on Linux or macOS to run the script at set intervals.

  For example, to run this script in a cronjob every two hours:

  ```
  crontab -e
  0 */2 * * * cd ~/path/to/this/repo && python3 -m plextraktsync
  ```

## Windows Setup (optional alternative)

- Download the latest `.zip` release from https://github.com/Taxel/PlexTraktSync/tags
- Run `setup.bat` to install requirements and create optional shortcuts and routines _(requires Windows 7sp1 - 11)_.

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

You can view sync progress in the `last_update.log` file which will be created.

## Commands

### Sync

The `sync` subcommand supports `--sync=shows` and `--sync=movies` options,
so you can sync only specific library types.

```
➔ python3 -m plextraktsync sync --help
Usage: plextraktsync sync [OPTIONS]

  Perform sync between Plex and Trakt

Options:
  --sync [all|movies|shows] Specify what to sync  [default: all]
  --help                    Show this message and exit.
```

### Unmatched

You can use `unmatched` command to scan your library and display unmatched movies.

Support for unmatched shows is not yet implemented.

`python3 -m plextraktsync unmatched`

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

`python3 -m plextraktsync watch`

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

### Systemd setup

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

### Unraid setup

Create a Unraid container of PlexTraktSync:

- Go to the Docker section, under "Docker Containers" and click "Add Container".
  - Click the advanced view to see all of the available parameters.
  - Leave the template blank/unselected.
  - Under Name: enter a name for the docker (e.g., PlexTraktSync).
  - Under Repository: enter `ghcr.io/taxel/plextraktsync:latest` (or whatever tag you want).
  - Under Extra Parameters: enter `-it` for interactive mode.
- Click "Apply".
- The container should start automatically. If not, start it.
- Enter the console for the container.
- Enter `python3 -m plextraktsync` to start the credential process described above.
