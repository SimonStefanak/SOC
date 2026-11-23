from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("book/<int:book_id>/", views.book, name="book"),
    path("book/<int:book_id>/finish/", views.finish_book, name="finish_book"),
    path("book/<int:book_id>/quick/", views.quick_update, name="quick_update"),
    path("search/", views.search, name="search"),
    path("to-be-read/", views.to_be_read, name="to_be_read"),
    path("finished/", views.finished, name="finished"),
    path("liked/", views.liked, name="liked"),
    path("calendar/", views.calendar, name="calendar"),
]
