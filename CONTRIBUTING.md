# Contributing to PlexTraktSync

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with GitHub

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## We Use [GitHub Flow], So All Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase (we use [GitHub Flow]). We actively welcome your pull requests:

1. Fork the repo and create your branch from the default branch (`main`).
2. If you've added code that should be tested, add tests.
3. If you've changed APIs, update the documentation.
4. Ensure the test suite passes.
5. Make sure your code lints.
6. Issue that pull request!

[GitHub Flow]: https://guides.github.com/introduction/flow/index.html

## Any contributions you make will be under the MIT Software License

In short, when you submit code changes, your submissions will be understood
under the same [MIT License] that covers the project.

Feel free to contact the maintainers if that's a concern.

[MIT License]: https://choosealicense.com/licenses/mit/

## Report bugs using GitHub's [issues]

We use GitHub issues to track public bugs. Report a bug by [opening a new issue]; it's that easy!

[issues]: https://github.com/Taxel/PlexTraktSync/issues
[opening a new issue]: https://github.com/Taxel/PlexTraktSync/issues/new

## Checking out code

If you checkout a specific version, this can be done in one of different ways:
- [GitHub download](#github-download)
- [Git clone](#git-clone)
- [Install code from Pull request](#install-code-from-pull-request)
- [Build Docker image](#building-docker-image)

Note: Development should be done against the `main` branch and not a specific tag.

### GitHub download

- Find the latest release from https://github.com/Taxel/PlexTraktSync/tags
- Download the `.tar` or `.zip`
- Extract to `PlexTraktSync` directory

Proceed to [Install dependencies](#install-dependencies)

### Git clone

- Find the latest release from https://github.com/Taxel/PlexTraktSync/tags
- Checkout the release with Git:
  ```
  git clone -b 0.15.0 --depth=1 https://github.com/Taxel/PlexTraktSync
  ```

To switch to a different version, find the latest tag and checkout:

```
git fetch --tags
git checkout <tag>
```

Proceed to [Install dependencies](#install-dependencies)

### Install dependencies

This applies to [GitHub download](#github-download) and [Git clone](#git-clone).

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

### Install code from Pull request

This requires prior installation with `pipx`.
Replace `838` with a pull request you intend to install.

```
plextraktsync self-update --pr 838
```

It will create new binary `plextraktsync@838` for that pull request. You need to run this binary instead of `plextraktsync`.

To pull new changes for the same pull request:

```
plextraktsync@838 self-update
```

If you need to do the same in docker container, you should:

͏ ͏ ͏ 1. first prepare the container with:

```
$ docker-compose run --rm --entrypoint sh plextraktsync
/app # pip install pipx
/app # pipx install plextraktsync
/app # apk add git
/app # plextraktsync self-update --pr 969
/app # plextraktsync@969 info
```
͏͏͏͏ ͏ ͏ 2. then run the script with:
```
/app # plextraktsync@969 sync
```

Alternatively you can [build image](#building-docker-image) yourself.

To remove the versions:

```
$ pipx list
venvs are in /Users/glen/.local/pipx/venvs
apps are exposed on your $PATH at /Users/glen/.local/bin
   package plextraktsync 0.20.9, installed using Python 3.10.5
    - plextraktsync
   package PlexTraktSync 0.20.0.dev0 (PlexTraktSync@838), installed using Python 3.10.5
    - plextraktsync@838
   package PlexTraktSync 0.20.0.dev0 (PlexTraktSync@984), installed using Python 3.10.5
    - plextraktsync@984

$ pipx uninstall plextraktsync@838
uninstalled PlexTraktSync@838! ✨ 🌟 ✨
$ pipx uninstall plextraktsync@984
uninstalled PlexTraktSync@984! ✨ 🌟 ✨
$
```

## Building docker image

You can build docker image from default branch:

```sh
docker build https://github.com/Taxel/PlexTraktSync.git#HEAD -t plextraktsync
```

To build for a pull request:

```sh
docker build https://github.com/Taxel/PlexTraktSync.git#refs/pull/1281/head -t plextraktsync/1281
```

## Git: setup pre-commit

For convenience this project uses [pre-commit] hooks:

```
brew install pre-commit
pre-commit install
```

It's usually a good idea to run the hooks against all of the files when adding
new hooks (usually pre-commit will only run on the changed files during git
hooks):

```
pre-commit run --all-files
```

You can update your hooks to the latest version automatically by running
`pre-commit autoupdate`. By default, this will bring the hooks to the latest
tag on the default branch.

[pre-commit]: https://pre-commit.com/

## Testing

We use [pytest] for testing.

First, ensure you have dependencies installed:
```
pip3 install -r tests/requirements.txt
```

To run all tests:

```
python3 -m pytest
```

To run specific test:

```
python3 -m pytest tests/test_version.py
```

[pytest]: https://pytest.org/

## Trakt API

You can use such shell script helper to make requests to [trakt api].
The `.pytrakt.json` file can be found from PlexTraktSync Config dir (`plextraktsync info`).

[trakt api]: https://trakt.docs.apiary.io/

```sh
#!/bin/sh
: ${TRAKT_API_KEY=$(jq -r .CLIENT_ID < .pytrakt.json)}
: ${TRAKT_AUTHORIZATION=Bearer $(jq -r .OAUTH_TOKEN < .pytrakt.json)}

curl -sSf \
     --header "Content-Type: application/json" \
     --header "trakt-api-version: 2" \
     --header "trakt-api-key: $TRAKT_API_KEY" \
     --header "Authorization: $TRAKT_AUTHORIZATION" \
	 "$@"
```

```
$ ./trakt-api.sh "https://api.trakt.tv/users/me" | jq -C | less
```

## Sharing Plex Media Server Database

Sometimes it is useful to share your copy of your Plex Media Server database
and send it to developers.

The database contains only metadata of your library, not actual media files.

The database contains everything about your setup, including local accounts, so
send your database only to people you trust. Plex removes password hashes from
the download, so passwords are not exposed, not even in hashed form.

To download and send the database:
1. Visit [`Plex Web`] -> `Manage Server` -> `Settings` -> `Troubleshooting` -> `Download database`.
   This is typically `https://app.plex.tv/desktop/#!/settings/server/<your_server_id>/manage/help`
1. To find developer email, take any commit made by them, add `.patch` to the url.
1. Upload the downloaded database `Plex Media Server Databases_*.zip` to https://wetransfer.com/
1. Provide it to PlexTraktSync developer privately via their e-mail

[`Plex Web`]: https://app.plex.tv/desktop

## Plex Media XML

Sometimes it's useful to share a fragment, or a complete XML of the item in
your library.

The XML can be viewed from Plex Media Servers that you own:

  - Overflow menu → Get Info → View XML in bottom-left corner of the modal

![][xml-menu]

You can read more from [Investigate Media Information and Formats] Plex support documentation.

[xml-menu]: https://user-images.githubusercontent.com/19761269/114267878-f0d1ae00-9a1b-11eb-8f3b-90110316ed11.png
[Investigate Media Information and Formats]: https://support.plex.tv/articles/201998867-investigate-media-information-and-formats/

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## References

This document was adapted from [@briandk gist] which itself was adapted from
the open-source contribution guidelines for [Facebook's Draft].

[@briandk gist]: https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62
[Facebook's Draft]: https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md
