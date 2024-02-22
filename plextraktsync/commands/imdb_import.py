from __future__ import annotations

import csv
from dataclasses import dataclass, fields
from functools import cached_property
from typing import TYPE_CHECKING

from plextraktsync.factory import factory

if TYPE_CHECKING:
    from os import PathLike


def read_csv(file: PathLike):
    with open(file, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield Ratings.from_csv(row)


@dataclass
class Ratings:
    imdb: str
    title: str
    year: int
    rating: int
    rate_date: str
    type: str

    FIELD_MAPPING = {
        "Const": "imdb",
        "Your Rating": "rating",
        "Date Rated": "rate_date",
        "Title": "title",
        "Year": "year",
        "Title Type": "type",
        # 'URL': 'url',
        # 'IMDb Rating': 'imdb_rating',
        # 'Runtime (mins)': 'runtime',
        # 'Genres': 'genres',
        # 'Num Votes': 'votes',
        # 'Release Date': 'release_date',
        # 'Directors': 'directors',
    }

    def __post_init__(self):
        # cast "int" fields
        fieldnames = [f.name for f in fields(self) if f.type == "int"]
        for name in fieldnames:
            value = self.__dict__[name]
            if value is not None and not isinstance(value, int):
                self.__dict__[name] = int(value)

    @cached_property
    def media_type(self):
        if self.type == "tvSeries":
            return "show"

        return self.type

    @classmethod
    def from_csv(cls, row):
        mapping = cls.FIELD_MAPPING
        data = {}
        for k, v in row.items():
            if k not in mapping:
                continue
            data[mapping[k]] = v

        return cls(**data)


def imdb_import(input: PathLike, dry_run: bool):
    trakt = factory.trakt_api
    print = factory.print

    for r in read_csv(input):
        print(f"Importing [blue]{r.media_type} {r.imdb}[/]: {r.title} ({r.year}), rated at {r.rate_date}")
        m = trakt.search_by_id(r.imdb, "imdb", r.media_type)
        rating = trakt.rating(m)
        if r.rating == rating:
            print(f"Rating {rating} already exists")
            continue
        print(f"{'Would rate' if dry_run else 'Rating'} {m} with {r.rating} (was {rating})")
        if not dry_run:
            trakt.rate(m, r.rating)
