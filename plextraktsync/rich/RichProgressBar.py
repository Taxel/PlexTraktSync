from functools import cached_property


class RichProgressBar:
    def __init__(self, iterable, total, options=None, desc=""):
        self.iter = iterable
        self.options = options or {}
        self.desc = desc
        self.total = total

    def __iter__(self):
        p = self.progress
        task_id = p.add_task(self.desc, total=self.total)

        i = 0
        for it in self.iter:
            yield it
            i += 1
            p.update(task_id, completed=i)

    def __enter__(self):
        self.progress.__enter__()
        return self

    def __exit__(self, *exc):
        self.progress.__exit__(*exc)

    @cached_property
    def progress(self):
        from tqdm.rich import FractionColumn, RateColumn

        from rich.progress import (BarColumn, Progress, TimeElapsedColumn,
                                   TimeRemainingColumn)

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
            "]"
        )
        progress = Progress(*args, **self.options)

        return progress
