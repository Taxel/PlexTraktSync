from functools import cached_property


class RichProgressBar:
    def __init__(self, iterable, total=None, options=None, desc=""):
        self.options = options or {}
        self.desc = desc
        if total is None:
            total = len(iterable)
        self.total = total
        self.i = 0

        if hasattr(iterable, "__next__"):
            self.iterable_next = iterable.__next__
        else:
            self.iterable_next = iter(iterable).__next__

    def __iter__(self):
        return self

    def __next__(self):
        res = self.iterable_next()
        self.update()
        return res

    def __enter__(self):
        self.progress.__enter__()
        return self

    def __exit__(self, *exc):
        self.progress.__exit__(*exc)

    def update(self):
        self.i += 1
        self.progress.update(self.task_id, completed=self.i)

    @cached_property
    def task_id(self):
        return self.progress.add_task(self.desc, total=self.total)

    @cached_property
    def progress(self):
        from rich.progress import (BarColumn, Progress, TimeElapsedColumn,
                                   TimeRemainingColumn)
        from tqdm.rich import FractionColumn, RateColumn

        args = (
            "[progress.description]{task.description}"
            "[progress.percentage]{task.percentage:>4.0f}%",
            BarColumn(bar_width=None),
            FractionColumn(
                unit_scale=False,
                unit_divisor=1000,
            ),
            "[",
            TimeElapsedColumn(),
            "<",
            TimeRemainingColumn(),
            ",",
            RateColumn(
                unit="it",
                unit_scale=False,
                unit_divisor=1000,
            ),
            "]",
        )
        progress = Progress(*args, **self.options)

        return progress
