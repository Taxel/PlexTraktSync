# Hawke.one Plex-Trakt-Sync

This project adds a two-way-sync between trakt.tv and hawke.one. 
It requires a trakt.tv account, but no Plex premium or Trakt VIP subscriptions.

I am not actively maintaining this, so use at own risk, there may be bugs and
the documentation and comments are lacking at best.

## Features

 - Media in Plex are added to Trakt collection
 - Ratings are synced (if ratings differ, Trakt takes precedence)
 - Watched status are synced (dates are not reported from Trakt to Plex)
 - Liked lists in Trakt are downloaded and all movies in Plex belonging to that
   list are added
 - You can edit the data/config.json file (it's just plain text) to choose what to sync
 - None of the above requires a Plex Pass or Trakt VIP membership.

## Setup

To setup this project on your own machine, clone or download this repo, and then:

* Windows - Run setup.bat and follow the prompts.

* Linux / MacOS - Use the files in the data folder to complete the following steps:

If you don't have it already, install Python - http://www.python.com

This should install the required Python packages:
```
pip3 install -r requirements.txt
```

Alternatively you can use [pipenv]:
```
pip install pipenv
pipenv run python main.py
```

[pipenv]: https://pipenv.pypa.io/


To connect to Trakt you need to create a new API app: Visit
`https://trakt.tv/oauth/applications/new`, give it a meaningful name and enter
`urn:ietf:wg:oauth:2.0:oob`as the redirect url. You can leave Javascript
origins and the checkboxes blank.

Then, run `python3 main.py`.

At first run, you will be asked to setup Trakt and Plex access.
Follow the instructions, your credentials and API keys will be stored in
`.env` and `.pytrakt.json` files.
You can take a look at the progress in the `last_update.log` file which will
be created. 

An example cronjob line that would run this script every 12 hours:

```
0 */12 * * * cd ~/path/to/this/repo/ && ./plex_trakt_sync.sh
```

This can be added to the cronjobs after typing `crontab -e` in the terminal.

## Sync settings

To disable parts of the functionality of this software, look no further than
`config.json`. Here, in the sync section, you can disable the following things
by setting them from `true` to `false` in a text editor:

 - Downloading liked lists from Trakt and adding them to Plex
 - Downloading your watchlist from Trakt and adding it to Plex
 - Syncing the watched status between Plex and Trakt
 - Syncing the collected status between Plex and Trakt

## Notes

 - The first execution of the script will take a long time. 
   After that, movie details and Trakt lists are cached, so it should run 
   quicker. Large sections (such as TV Shows) will still take a significant time.

 - The PyTrakt API keys are not stored securely, so if you do not want to have
   a file containing those on your harddrive, you can not use this project.
