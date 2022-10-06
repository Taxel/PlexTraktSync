import csv
from dataclasses import dataclass
from os import PathLike

from plextraktsync.console import print


def read_csv(file: PathLike):
    with open(file, newline='') as fh:
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
        'Const': 'imdb',
        'Your Rating': 'rating',
        'Date Rated': 'rate_date',
        'Title': 'title',
        'Year': 'year',
        'Title Type': 'type',
    }

    @staticmethod
    def from_csv(row):
        mapping = Ratings.FIELD_MAPPING
        data = {}
        for k, v in row.items():
            if k not in mapping:
                continue
            data[mapping[k]] = v

        return Ratings(**data)


def imdb_import(input: PathLike):
    for r in read_csv(input):
        print(f"Importing [blue]{r.type} {r.imdb}[/]: {r.title} ({r.year}), rated {r.rating} at {r.rate_date}")
