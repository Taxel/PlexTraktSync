# Plex-Trakt-Sync

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
 - You can edit the [config file](https://github.com/Taxel/PlexTraktSync/blob/master/config.json) to choose what to sync
 - None of the above requires a Plex Pass or Trakt VIP membership.
   Downside: Needs to be executed manually or via cronjob,
   can not use live data via webhooks.

## Setup

To setup this on your own machine, first clone or download this repo.

This should install the required Python packages:
```
pip3 install -r requirements.txt
```

Alternatively you can use [pipenv]:
```
pip3 install pipenv
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

If you have [2 Factor Authentication enabled on Plex][2fa], you can append the code to your password.

[2fa]: https://support.plex.tv/articles/two-factor-authentication/#toc-1:~:text=Old%20Third%2DParty%20Apps%20%26%20Tools

You can take a look at the progress in the `last_update.log` file which will
be created. 

Personally, I run this script in a cronjob every two hours. On Mac this worked
by adding the line:

```
0 */2 * * * cd ~/path/to/this/repo/ && ./plex_trakt_sync.sh
```

to the cronjobs after typing `crontab -e` in the terminal.

## Sync settings

To disable parts of the functionality of this software, look no further than
`config.json`. Here, in the sync section, you can disable the following things
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
