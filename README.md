# Plex-Trakt-Sync

![Python Versions][python-versions-badge]

This project adds a two-way-sync between trakt.tv and Plex Media Server. It
requires a trakt.tv account but no Plex premium and no Trakt VIP subscriptions,
unlike the Plex app provided by Trakt.

Note: The PyTrakt API keys are not stored securely, so if you do not want to have a file containing those on your harddrive, you can not use this project.

**To contribute, please find issues with the [`help-wanted`](https://github.com/Taxel/PlexTraktSync/issues?q=is%3Aissue+is%3Aopen+label%3A%22help+wanted%22) label, thank you.**

[python-versions-badge]: https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue

## Features

 - Media in Plex are added to Trakt collection
 - Ratings are synced (if ratings differ, Trakt takes precedence)
 - Watched status are synced (dates are not reported from Trakt to Plex)
 - Liked lists in Trakt are downloaded and all movies in Plex belonging to that
   list are added
 - You can edit the [config file](https://github.com/Taxel/PlexTraktSync/blob/HEAD/plex_trakt_sync/config.default.json) to choose what to sync
 - None of the above requires a Plex Pass or Trakt VIP membership.
   Downside: Needs to be executed manually or via cronjob,
   can not use live data via webhooks.

## Pre-requisites

The script is known to work with Python 3.7-3.9 versions.

## Installation

To install this project on Linux, macOS or Windows WSL:   

- Verify the latest release at https://github.com/Taxel/PlexTraktSync/releases

- Download the `.tar` or `.zip`   
  *or* checkout the release with Git (For example, the command to clone with Git):
  ```
  git clone -b 0.7.19 --depth=1 https://github.com/Taxel/PlexTraktSync
  ```

- In the extracted directory, install the required Python packages:
  ```
  python3 -m pip install -r requirements.txt
  ```

  *or* alternatively you can use [pipenv]:
  ```
  python3 -m pip install pipenv
  pipenv install
  pipenv run plex-trakt-sync
  ```

  [pipenv]: https://pipenv.pypa.io/

## Docker Compose

You can setup docker compose file like this:

```yaml
services:
  plex-trakt-sync:
    image: ghcr.io/taxel/plextraktsync
    volumes:
      - ./config:/app/config
```

To run sync:

```
docker-compose run --rm plex-trakt-sync
```

To run `watch` command:

```
docker-compose run --rm plex-trakt-sync watch
```

## Setup
  - You will need to create a Trakt API app if you do not already have one:
    - Visit https://trakt.tv/oauth/applications/new
    - Give it a meaningful name
    - Enter `urn:ietf:wg:oauth:2.0:oob` as the redirect url
    - You can leave Javascript origins and the Permissions checkboxes blank

  - Run `python3 -m plex_trakt_sync`.

  - At first run you will be asked to setup Trakt and Plex access.   
  Follow the instructions, your credentials and API keys will be stored in
  `.env` and `.pytrakt.json` files.   
  If you have [2 Factor Authentication enabled on Plex](https://support.plex.tv/articles/two-factor-authentication/#toc-1:~:text=Old%20Third%2DParty%20Apps%20%26%20Tools) you can append the code to your password.


- Cronjobs can be optionally used on Linux or macOS to run the script at set intervals.   
  For example, to run this script in a cronjob every two hours:  
  ```
  crontab -e
  0 */2 * * * cd ~/path/to/this/repo && python3 -m plex_trakt_sync
  ```

## Windows Setup (optional alternative)

- Download the latest `.zip` release from https://github.com/Taxel/PlexTraktSync/releases
- Run `setup.bat` to install requirements and create optional shortcuts and routines *(requires Windows 7sp1 - 11)*.

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

The `sync` subcommand supports `--sync=tv` and `--sync=movies` options,
so you can sync only specific library types.

```
➔ python3 -m plex_trakt_sync sync --help
Usage: plex_trakt_sync sync [OPTIONS]

  Perform sync between Plex and Trakt

Options:
  --sync [all|movies|tv]  Specify what to sync  [default: all]
  --help                  Show this message and exit.
```

### Unmatched 
You can use `unmatched` command to scan your library and display unmatched movies.   
Support for unmatched shows is not yet implemented.   

`python3 -m plex_trakt_sync unmatched`   

### Watch
You can use the `watch` command to listen to events from Plex Media Server
and scrobble plays.   

`python3 -m plex_trakt_sync watch`   

> What is scrobbling?
>
> _Scrobbling simply means automatically tracking what you’re watching. Instead
> of checking in from your phone of the website, this command runs in the
> background and automatically scrobbles back to Trakt while you enjoy watching
> your media_ - [Plex Scrobbler@blog.trakt.tv][plex-scrobbler]

[plex-scrobbler]: https://blog.trakt.tv/plex-scrobbler-52db9b016ead

Create a systemd unit so that it scrobbles automatically in the background:

```ini
[Unit]
Description=PlexTraktSync watch daemon
After=network-online.target

[Service]
ExecStart=/path/to/PlexTraktSync/plex_trakt_sync.sh watch

Restart=on-failure
RestartSec=10
User=user
Group=user

[Install]
WantedBy=multi-user.target
```

NOTE: The `watch` command will scrobble all Plex Watches to Trakt as filtering
by user is not implemented [#324].

[#324]: https://github.com/Taxel/PlexTraktSync/issues/324
