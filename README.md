# Plex-Trakt-Sync
This project adds a two-way-sync between trakt.tv and Plex Media Server. It requires a trakt.tv account but no Plex premium and Trakt VIP subscriptions, unlike the Plex app provided by Trakt.

This is currently under construction, so use at own risk, there may be bugs and the documentation and comments are lacking at best.

## Features

 - All media in PMS are added to Trakt collection

 - Ratings are synced (if ratings differ, Trakt takes precedence)

 - Watched status is synced (only if watched or not, not the dates)

 - Liked lists in Trakt are downloaded and all movies in PMS belonging to that list are added

 - None of the above requires a Plex Pass or Trakt VIP membership, downside: Needs to be executed manually or via cronjob, can not use live data via webhooks.

## Setup
To setup this on your own machine, first clone or download this repo.

`pip3 install -r requirements.txt` should install the required Python packages.

After that, rename the `.env_example` file to `.env`. The data you have to put into this file will be printed out by `python3 get_env_data.py`, so execute this script and follow the instructions.

After that you're done. run `python3 plex.py`. You can take a look at the progress in the `last_update.log` file which will be created. 

Personally, I run this script in a cronjob every two hours. On Mac this worked by adding the line

`0 */2 * * * cd ~/path/to/this/repo/ && ./plex_trakt_sync.sh`

to the cronjobs after typing `crontab -e` in the terminal.

## Notes

 - The first execution of the script will (depending on your PMS library size) take a long time. After that, movie details and Trakt lists are cached, so it should run a lot quicker the second time. This does mean, however, that Trakt lists are not updated dynamically (which is fine for lists like "2018 Academy Award Nominees" but might not be ideal for lists that are updated often). Here are the execution times on my Plex server: First run - 1228 seconds, second run - 111 seconds

 - The PyTrakt API keys are not stored securely, so if you do not want to have a file containing those on your harddrive, you can not use this project.