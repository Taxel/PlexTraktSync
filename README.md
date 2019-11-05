# Plex-Trakt-Sync
This project adds a two-way-sync between trakt.tv and Plex Media Server. It requires a trakt.tv account but no Plex premium and Trakt VIP subscriptions, unlike the Plex app provided by Trakt.

This is currently under construction, so use at own risk, there may be bugs and the documentation and comments are lacking at best.

## Setup
To setup this on your own machine, first clone or download this repo.

`pip3 install -r requirements.txt` should install the required Python packages.

After that, rename the `.env_example` file to `.env`. The data you have to put into this file will be printed out by `python3 get_env_data.py`, so execute this script and follow the instructions.

After that you're done. run `python3 plex.py`. You can take a look at the progress in the `last_update.log` file which will be created. 

Personally, I run this script in a cronjob every two hours. On Mac this worked by adding the line

`0 */2 * * * cd ~/path/to/this/repo/ && ./plex_trakt_sync.sh`

to the cronjobs after typing `crontab -e` in the terminal.