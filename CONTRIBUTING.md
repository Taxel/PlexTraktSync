# Contributing to PlexTraktSync

We love your input! We want to make contributing to this project as easy and transparent as possible, whether it's:

- Reporting a bug
- Discussing the current state of the code
- Submitting a fix
- Proposing new features
- Becoming a maintainer

## We Develop with GitHub

We use GitHub to host code, to track issues and feature requests, as well as accept pull requests.

## Code Changes Happen Through Pull Requests

Pull requests are the best way to propose changes to the codebase.

We use [Git-Flow] to automate our `git` branching workflow.

In short development happens as this:
1. the new changes end up in `develop` branch via pull requests
1. when release is prepared, a pull request from `develop` to `master` is created
1. when that pull request is meged, a release is tagged
1. after release `master` is merged back to `develop`

For bugfixes the flow is more like [GitHub Flow]:
1. pull request is made against `master` branch
1. pull request is merged
1. release is tagged
1. after release `master` is merged back to `develop`

[Git-Flow]: https://nvie.com/posts/a-successful-git-branching-model/
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

## License

By contributing, you agree that your contributions will be licensed under its MIT License.

## References

This document was adapted from [@briandk gist] which itself was adapted from
the open-source contribution guidelines for [Facebook's Draft].

[@briandk gist]: https://gist.github.com/briandk/3d2e8b3ec8daf5a27a62
[Facebook's Draft]: https://github.com/facebook/draft-js/blob/a9316a723f9e918afde44dea68b5f9f39b7d9b00/CONTRIBUTING.md
