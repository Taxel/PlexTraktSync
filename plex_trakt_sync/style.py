from functools import partial

import click

title = partial(click.style, fg="yellow")
prompt = partial(click.style, fg="yellow")
success = partial(click.style, fg="green")
error = partial(click.style, fg="red")
comment = partial(click.style, fg="bright_cyan")
disabled = partial(click.style, fg="blue")
highlight = partial(click.style, fg="bright_white")
