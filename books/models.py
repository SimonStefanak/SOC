from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class Genre(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Series(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "series"

    def __str__(self):
        return self.name


class Book(models.Model):
    class Source(models.TextChoices):
        GOODBOOKS = "goodbooks", "goodbooks-10k"
        OPENLIBRARY = "openlibrary", "Open Library"

    title = models.CharField(max_length=500)
    author = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    original_publication_year = models.IntegerField(null=True, blank=True)
    language_code = models.CharField(max_length=10, blank=True)
    series = models.ForeignKey(Series, null=True, blank=True, on_delete=models.SET_NULL, related_name="books")
    series_position = models.CharField(max_length=50, blank=True)
    isbn = models.CharField(max_length=10, unique=True, null=True, blank=True)
    isbn13 = models.CharField(max_length=13, unique=True, null=True, blank=True)
    goodreads_id = models.PositiveIntegerField(unique=True, null=True, blank=True)
    openlibrary_key = models.CharField(max_length=50, unique=True, null=True, blank=True)
    source = models.CharField(max_length=20, choices=Source.choices, default=Source.GOODBOOKS)
    image_url = models.URLField(max_length=500, blank=True)
    small_image_url = models.URLField(max_length=500, blank=True)
    goodreads_avg_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    goodreads_ratings_count = models.PositiveIntegerField(null=True, blank=True)
    genres = models.ManyToManyField(Genre, through="BookGenre", related_name="books")

    class Meta:
        ordering = ["title"]

    def __str__(self):
        return f"{self.title} by {self.author}"

    @property
    def catalog_stars(self):
        """Number of filled stars (0-5) for the catalog rating."""
        return int(round(float(self.goodreads_avg_rating))) if self.goodreads_avg_rating else 0


class BookGenre(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    tag_count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["book", "genre"], name="unique_book_genre")]
        ordering = ["-tag_count"]

    def __str__(self):
        return f"{self.book} - {self.genre}"


class UserBook(models.Model):
    """One row per (user, book): reading status, dates, rating and review."""

    class Status(models.TextChoices):
        TO_READ = "to_read", "Want"
        READING = "reading", "Reading"
        READ = "read", "Finished"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="user_books")
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="user_books")
    status = models.CharField(max_length=10, choices=Status.choices)
    owned = models.BooleanField(default=False)
    favorite = models.BooleanField(default=False)
    rating = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )  # 1-5 stars
    review_text = models.TextField(null=True, blank=True)
    date_started = models.DateField(null=True, blank=True)
    date_finished = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    added_at = models.DateTimeField(default=timezone.now, editable=False)  # when it first went on a shelf
    liked_at = models.DateTimeField(null=True, blank=True, editable=False)  # when the heart was last turned on

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "book"], name="unique_user_book")]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.user} - {self.book} ({self.get_status_display()})"

    def save(self, *args, **kwargs):
        # liked_at follows the heart: set when it's turned on, cleared when it's turned off
        if self.favorite and not self.liked_at:
            self.liked_at = timezone.now()
        elif not self.favorite:
            self.liked_at = None
        super().save(*args, **kwargs)
