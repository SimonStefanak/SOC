from django.contrib import admin

from .models import Book, BookGenre, Genre, Series, UserBook


class BookGenreInline(admin.TabularInline):
    model = BookGenre
    extra = 0


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "original_publication_year", "goodreads_avg_rating")
    search_fields = ("title", "author", "isbn", "isbn13")
    list_filter = ("source", "genres")
    inlines = [BookGenreInline]


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Series)
class SeriesAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(UserBook)
class UserBookAdmin(admin.ModelAdmin):
    list_display = ("user", "book", "status", "rating", "favorite", "updated_at")
    list_filter = ("status", "favorite")
    search_fields = ("book__title", "user__username")
    autocomplete_fields = ("book",)
