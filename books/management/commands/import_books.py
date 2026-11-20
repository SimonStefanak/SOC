"""
Import the goodbooks-10k dataset into the database.

Usage:
    python manage.py import_books           # import (refuses if books already exist)
    python manage.py import_books --clear   # delete all books/series/genres first, then import

Reads from the data/ folder next to manage.py:
    books.csv, tags.csv, book_tags.csv
"""

import csv
import re
from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from books.models import Book, BookGenre, Genre, Series

DATA_DIR = Path(settings.BASE_DIR) / "data"
TOP_GENRES_PER_BOOK = 3

# Whitelist: genre name -> Goodreads tags that count as that genre.
# Decisions: Middle Grade merged into Children, Erotica merged into Romance,
# Mystery / Thriller / Crime kept separate.
GENRES = {
    "Fantasy": ["fantasy", "high-fantasy", "epic-fantasy", "urban-fantasy", "fantasy-fiction", "magic"],
    "Science Fiction": ["sci-fi", "science-fiction", "scifi", "sf"],
    "Romance": ["romance", "contemporary-romance", "adult-romance", "chick-lit", "chicklit", "chic-lit", "erotica"],
    "Paranormal": ["paranormal", "supernatural", "vampires", "vampire", "paranormal-romance", "pnr"],
    "Mystery": ["mystery", "mysteries", "detective", "murder-mystery", "mystery-crime"],
    "Thriller": ["thriller", "thrillers", "suspense", "mystery-thriller", "suspense-thriller"],
    "Crime": ["crime", "crime-fiction", "crime-mystery", "crime-thriller"],
    "Horror": ["horror"],
    "Historical Fiction": ["historical-fiction", "historical"],
    "Classics": ["classics", "classic", "classic-literature", "modern-classics", "classic-fiction"],
    "Literary Fiction": ["literary-fiction", "literature", "literary"],
    "Contemporary": ["contemporary", "contemporary-fiction", "realistic-fiction"],
    "Young Adult": ["young-adult", "ya", "ya-fiction", "young-adult-fiction", "teen", "ya-books", "ya-lit", "teen-fiction"],
    "Children": ["children", "childrens", "children-s", "kids", "children-s-books", "childrens-books",
                 "kids-books", "juvenile", "picture-books", "middle-grade"],
    "Dystopian": ["dystopian", "dystopia"],
    "Adventure": ["adventure", "action-adventure"],
    "Humor": ["humor", "humour", "funny", "comedy"],
    "Non-fiction": ["non-fiction", "nonfiction"],
    "Biography & Memoir": ["biography", "memoir", "memoirs", "biographies", "autobiography",
                           "biography-memoir", "memoir-biography"],
    "History": ["history"],
    "Science": ["science"],
    "Philosophy": ["philosophy"],
    "Psychology": ["psychology"],
    "Religion & Spirituality": ["religion", "spirituality", "spiritual", "christian"],
    "Politics": ["politics"],
    "Self-help": ["self-help"],
    "Poetry": ["poetry"],
    "Short Stories": ["short-stories"],
    "Graphic Novels & Comics": ["graphic-novels", "graphic-novel", "comics", "manga"],
    "War": ["war"],
    "Mythology": ["mythology"],
    "New Adult": ["new-adult"],
}

# "The Hunger Games (The Hunger Games, #1)" -> title / series / position.
# Only parentheses that contain '#' are treated as a series.
TRAILING_PARENS = re.compile(r"^(?P<title>.*?)\s*\((?P<inner>[^()]*#[^()]*)\)\s*$")


# ---------- helpers ----------

def parse_title(raw):
    """Return (title, series_name, series_position)."""
    raw = raw.strip()
    m = TRAILING_PARENS.match(raw)
    if not m:
        return raw, "", ""
    inner = m.group("inner")
    name, _, position = inner.rpartition("#")
    name = name.strip().rstrip(",").strip()
    title = m.group("title").strip() or raw
    return title, name, position.strip()


def isbn10_is_valid(isbn):
    if len(isbn) != 10 or not isbn[:9].isdigit() or not (isbn[9].isdigit() or isbn[9] == "X"):
        return False
    total = sum((10 - i) * (10 if ch == "X" else int(ch)) for i, ch in enumerate(isbn))
    return total % 11 == 0


def isbn10_to_isbn13(isbn10):
    core = "978" + isbn10[:9]
    total = sum(int(d) * (1 if i % 2 == 0 else 3) for i, d in enumerate(core))
    return core + str((10 - total % 10) % 10)


def clean_isbns(raw_isbn):
    """
    Return (isbn10, isbn13) or (None, None).
    The CSV's isbn13 column is ignored: it was saved as a float and rounded.
    ISBN10 lost its leading zeros, so it is padded back to 10 characters.
    """
    raw = (raw_isbn or "").strip().upper()
    if not raw:
        return None, None
    isbn10 = raw.zfill(10)
    if not isbn10_is_valid(isbn10):
        return None, None
    return isbn10, isbn10_to_isbn13(isbn10)


def to_int(value):
    value = (value or "").strip()
    return int(float(value)) if value else None


def clean_cover(url):
    url = (url or "").strip()
    return "" if (not url or "nophoto" in url) else url


def read_csv(name):
    path = DATA_DIR / name
    if not path.exists():
        raise CommandError(f"Missing file: {path}")
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


# ---------- command ----------

class Command(BaseCommand):
    help = "Import goodbooks-10k (books, series, genres) from the data/ folder."

    def add_arguments(self, parser):
        parser.add_argument("--clear", action="store_true",
                            help="Delete existing books, series and genres before importing.")

    @transaction.atomic  # all or nothing: if anything fails, the database is left untouched
    def handle(self, *args, **options):
        if options["clear"]:
            BookGenre.objects.all().delete()
            Book.objects.all().delete()
            Series.objects.all().delete()
            Genre.objects.all().delete()
            self.stdout.write("Cleared existing books, series and genres.")
        elif Book.objects.exists():
            raise CommandError("Books already exist. Use --clear to re-import from scratch.")

        book_rows = read_csv("books.csv")
        self.stdout.write(f"Read {len(book_rows)} rows from books.csv")

        # 1) Series: create each name once
        parsed = {}
        series_names = set()
        for row in book_rows:
            title, series_name, position = parse_title(row["title"])
            parsed[row["goodreads_book_id"]] = (title, series_name, position)
            if series_name:
                series_names.add(series_name)
        Series.objects.bulk_create([Series(name=n) for n in sorted(series_names)])
        series_by_name = {s.name: s for s in Series.objects.all()}

        # 2) Books
        books = []
        missing_isbn = []
        for row in book_rows:
            gr_id = row["goodreads_book_id"]
            title, series_name, position = parsed[gr_id]
            isbn10, isbn13 = clean_isbns(row["isbn"])
            if not isbn10:
                missing_isbn.append(f"{gr_id}\t{title}")
            avg = (row["average_rating"] or "").strip()
            books.append(Book(
                title=title,
                author=row["authors"].split(",")[0].strip(),
                original_publication_year=to_int(row["original_publication_year"]),
                language_code=(row["language_code"] or "").strip(),
                series=series_by_name.get(series_name),
                series_position=position,
                isbn=isbn10,
                isbn13=isbn13,
                goodreads_id=int(gr_id),
                source=Book.Source.GOODBOOKS,
                image_url=clean_cover(row["image_url"]),
                small_image_url=clean_cover(row["small_image_url"]),
                goodreads_avg_rating=Decimal(avg) if avg else None,
                # work_ratings_count = ratings across all editions of the book
                goodreads_ratings_count=to_int(row["work_ratings_count"]),
            ))
        Book.objects.bulk_create(books, batch_size=500)
        book_by_gr_id = dict(Book.objects.values_list("goodreads_id", "id"))
        self.stdout.write(f"Created {len(books)} books, {len(series_names)} series")

        # 3) Genres from the whitelist
        Genre.objects.bulk_create([Genre(name=n, slug=slugify(n)) for n in GENRES])
        genre_by_name = {g.name: g.id for g in Genre.objects.all()}
        genre_for_tag = {tag: g for g, tags in GENRES.items() for tag in tags}

        # tag_id -> genre name (only for whitelisted tags)
        tag_to_genre = {}
        for row in read_csv("tags.csv"):
            genre = genre_for_tag.get(row["tag_name"])
            if genre:
                tag_to_genre[row["tag_id"]] = genre

        # Sum tag counts per (book, genre). Synonyms add up: ya + young-adult -> Young Adult.
        totals = defaultdict(lambda: defaultdict(int))
        for row in read_csv("book_tags.csv"):
            genre = tag_to_genre.get(row["tag_id"])
            count = int(row["count"])
            if genre and count > 0:  # the dataset has a few negative counts; skip them
                totals[row["goodreads_book_id"]][genre] += count

        # Keep each book's top N genres
        links = []
        for gr_id, genre_counts in totals.items():
            book_id = book_by_gr_id.get(int(gr_id))
            if not book_id:
                continue
            top = sorted(genre_counts.items(), key=lambda kv: kv[1], reverse=True)[:TOP_GENRES_PER_BOOK]
            for genre, count in top:
                links.append(BookGenre(book_id=book_id, genre_id=genre_by_name[genre], tag_count=count))
        BookGenre.objects.bulk_create(links, batch_size=1000)
        self.stdout.write(f"Created {len(GENRES)} genres, {len(links)} book-genre links")

        # 4) Report books without an ISBN
        report = DATA_DIR / "missing_isbn.txt"
        report.write_text("goodreads_id\ttitle\n" + "\n".join(missing_isbn), encoding="utf-8")
        self.stdout.write(f"{len(missing_isbn)} books have no valid ISBN (list in {report.name})")

        self.stdout.write(self.style.SUCCESS("Import finished."))
