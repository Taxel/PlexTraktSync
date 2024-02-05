from __future__ import annotations

import csv
from dataclasses import dataclass
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

    @cached_property
    def media_type(self):
        if self.type == "tvSeries":
            return "show"

        return self.type

    @staticmethod
    def from_csv(row):
        mapping = Ratings.FIELD_MAPPING
        data = {}
        for k, v in row.items():
            if k not in mapping:
                continue
            data[mapping[k]] = v

        return Ratings(**data)


def imdb_import(input: PathLike, dry_run: bool):
    trakt = factory.trakt_api
    print = factory.print

    for r in read_csv(input):
        print(f"Importing [blue]{r.media_type} {r.imdb}[/]: {r.title} ({r.year}), rated at {r.rate_date}")
        m = trakt.search_by_id(r.imdb, "imdb", r.media_type)
        rating = trakt.rating(m)
        print(f"{'Would rate' if dry_run else 'Rating'} {m} with {r.rating} (was {rating})")
        if not dry_run:
            trakt.rate(m, r.rating)
