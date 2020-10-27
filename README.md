# Plex-Trakt-Sync

[![Docker Pulls](https://img.shields.io/docker/pulls/vbutacu/plex-trakt-sync.svg?maxAge=60&style=flat-square)](https://hub.docker.com/repository/docker/vbutacu/plex-trakt-sync)
[![Docker image size](https://img.shields.io/docker/image-size/vbutacu/plex-trakt-sync?style=flat-square)](https://hub.docker.com/repository/docker/vbutacu/plex-trakt-sync)
![CodeQL](https://img.shields.io/github/workflow/status/VladButacu/PlexTraktSync/CodeQL/master)

This project adds a two-way-sync between trakt.tv and Plex Media Server. It
requires a trakt.tv account but no Plex premium and no Trakt VIP subscriptions,
unlike the Plex app provided by Trakt.

I am not actively maintaining this, so use at own risk, there may be bugs and
the documentation and comments are lacking at best.

## Features

 - Media in Plex are added to Trakt collection
 - Ratings are synced (if ratings differ, Trakt takes precedence)
 - Watched status are synced (dates are not reported from Trakt to Plex)
 - Liked lists in Trakt are downloaded and all movies in Plex belonging to that
   list are added
 - You can edit the [config file](https://github.com/VladButacu/PlexTraktSync/blob/master/app/data/app_config.json.example) to choose what to sync
 - None of the above requires a Plex Pass or Trakt VIP membership.
   Downside: Needs to be executed manually or via cronjob,
   can not use live data via webhooks.

## Setup

To setup this on your own machine, first clone or download this repo.

<br/>

### Install required packages
```
pip3 install -r requirements.txt
```
<br/>

### Create app config file
Rename [app_config.json.example](https://github.com/VladButacu/PlexTraktSync/blob/master/app/data/app_config.json.example) to **app_config.json** in `app/data/` folder

<br/>

### Create Trakt app api
To connect to Trakt you need to create a new API app: Visit
`https://trakt.tv/oauth/applications/new`, give it a meaningful name and enter
`urn:ietf:wg:oauth:2.0:oob` as the redirect url. You can leave Javascript
origins and the checkboxes blank.
<img src="https://github.com/VladButacu/PlexTraktSync/blob/master/docs/trakt_api_creation.png">

<br/>

### Generate Plex and Trakt config files
You can run `python3 get_configs.py` to generate the config files with the required credentials for Plex and Trakt. Follow the prompt guide to do so.

If you need to only generate the config for either Plex or Trakt run the script like so:
- Plex: `python3 get_configs.py plex`
- Trakt: `python3 get_configs.py trakt`

<br/>

## Running the script

### Local
Make sure you are in the `app/` folder and run it with:
`python3 main.py`

<br/>

### Docker
`docker run --rm -v /absolute-path-to-this-repo/app/data:/app/data vbutacu/plex-trakt-sync`

</br>

For both *Local* and *Docker* methods you can take a look at the progress in the `last_update.log` file which will be created in the `app/data` folder

</br>

## Sync settings
To disable parts of the functionality of this software, look no further than
`app_config.json`. Here, in the sync section, you can disable the following things
by setting them from `true` to `false` in a text editor:

 - Downloading liked lists from Trakt and adding them to Plex
 - Downloading your watchlist from Trakt and adding it to Plex
 - Syncing the watched status between Plex and Trakt
 - Syncing the collected status between Plex and Trakt

## Notes

 - The first execution of the script will (depending on your PMS library size)
   take a long time. After that, movie details and Trakt lists are cached, so
   it should run a lot quicker the second time. This does mean, however, that
   Trakt lists are not updated dynamically (which is fine for lists like "2018
   Academy Award Nominees" but might not be ideal for lists that are updated
   often). Here are the execution times on my Plex server: First run - 1228
   seconds, second run - 111 seconds

 - The PyTrakt API keys are not stored securely, so if you do not want to have
   a file containing those on your harddrive, you can not use this project.