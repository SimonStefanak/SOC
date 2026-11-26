from django.urls import path
from django.views.generic import RedirectView

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("book/<int:book_id>/", views.book, name="book"),
    path("book/<int:book_id>/finish/", views.finish_book, name="finish_book"),
    path("book/<int:book_id>/quick/", views.quick_update, name="quick_update"),
    path("search/", views.search, name="search"),
    path("accounts/register/", views.register, name="register"),
    path("want/", views.to_be_read, name="to_be_read"),
    # old address of the Want page, kept so existing links and bookmarks still work
    path("to-be-read/", RedirectView.as_view(pattern_name="to_be_read", query_string=True, permanent=True)),
    path("finished/", views.finished, name="finished"),
    path("liked/", views.liked, name="liked"),
    path("calendar/", views.calendar, name="calendar"),
]
