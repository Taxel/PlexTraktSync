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

[MIT License]: http://choosealicense.com/licenses/mit/

## Report bugs using GitHub's [issues]

We use GitHub issues to track public bugs. Report a bug by [opening a new issue]; it's that easy!

[issues]: https://github.com/Taxel/PlexTraktSync/issues
[opening a new issue]: https://github.com/Taxel/PlexTraktSync/issues/new

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
