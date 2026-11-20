import re
from datetime import date, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.core.paginator import Paginator
from django.db.models import Count, F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateformat import format as format_date
from django.views.decorators.http import require_POST

from .forms import ReviewForm, ShelfForm
from .models import Book, Genre, UserBook


def home(request):
    context = {}
    if request.user.is_authenticated:
        mine = UserBook.objects.filter(user=request.user).select_related("book")
        year = timezone.localdate().year

        # the book you started most recently (and haven't finished)
        context["current"] = (
            mine.filter(status=UserBook.Status.READING)
            .order_by("-date_started", "-updated_at")
            .first()
        )
        context["read_this_year"] = (
            mine.filter(status=UserBook.Status.READ, date_finished__year=year)
            .order_by("-date_finished", "-updated_at")
        )
        # genres of the books you've finished, most-finished first
        context["top_genres"] = (
            Genre.objects.filter(
                bookgenre__book__user_books__user=request.user,
                bookgenre__book__user_books__status=UserBook.Status.READ,
            )
            .annotate(read_count=Count("bookgenre__book", distinct=True))
            .order_by("-read_count", "name")[:8]
        )
    return render(request, "books/home/index.html", context)


@login_required
@require_POST
def finish_book(request, book_id):
    """'Mark as finished' on the homepage: shelf -> Finished, finish date -> today."""
    entry = get_object_or_404(UserBook, user=request.user, book_id=book_id)
    entry.status = UserBook.Status.READ
    entry.date_finished = entry.date_finished or timezone.localdate()
    entry.save()
    messages.success(request, f"Finished “{entry.book.title}”. Nice one!")
    return redirect("home")


@login_required
@require_POST
def quick_update(request, book_id):
    """Background save from the homepage card: changes only the fields that are
    sent (rating, favorite, review_text) and leaves shelf and dates alone."""
    entry = get_object_or_404(UserBook, user=request.user, book_id=book_id)
    fields = []

    if "rating" in request.POST:
        value = request.POST["rating"].strip()
        if value == "":
            entry.rating = None
        elif value.isdigit() and 1 <= int(value) <= 5:
            entry.rating = int(value)
        else:
            return JsonResponse({"ok": False, "errors": ["The rating must be 1 to 5 stars."]}, status=400)
        fields.append("rating")

    if "favorite" in request.POST:
        entry.favorite = request.POST["favorite"] == "true"
        fields.append("favorite")

    if "review_text" in request.POST:
        entry.review_text = request.POST["review_text"].strip()
        fields.append("review_text")

    if fields:
        entry.save(update_fields=fields + ["updated_at"])
    return JsonResponse({"ok": True})


def search(request):
    """Search all books by title, author or ISBN. Every word must match
    (in the title or the author), most-rated books first."""
    query = request.GET.get("q", "").strip()[:200]
    page = None
    if query:
        books = Book.objects.all()
        digits = query.replace("-", "").replace(" ", "")
        if re.fullmatch(r"\d{9}[\dXx]|\d{13}", digits):  # looks like an ISBN-10 or ISBN-13
            books = books.filter(Q(isbn__iexact=digits) | Q(isbn13=digits))
        else:
            for word in query.split():
                books = books.filter(Q(title__icontains=word) | Q(author__icontains=word))
        books = books.order_by("-goodreads_ratings_count", "title")
        page = Paginator(books, 24).get_page(request.GET.get("page"))
    return render(request, "books/search/index.html", {"query": query, "page": page})


# The two shelf pages share one template; this is what differs between them.
SHELVES = {
    "to_read": {
        "status": UserBook.Status.TO_READ,
        "title": "To read",
        "date_field": "added_at",        # a DateTimeField
        "date_label": "Date added",
        "card_label": "Added",
        "sorts": [
            ("-added", "Date added, newest", [F("added_at").desc()]),
            ("added", "Date added, oldest", [F("added_at").asc()]),
            ("title", "Title, A–Z", ["book__title"]),
            ("author", "Author, A–Z", ["book__author", "book__title"]),
        ],
        "empty": "Nothing on your to-read shelf yet. Find a book and set it to “To read”.",
    },
    "finished": {
        "status": UserBook.Status.READ,
        "title": "Finished",
        "date_field": "date_finished",   # a DateField, may be empty
        "date_label": "Date finished",
        "card_label": "Finished",
        "sorts": [
            ("-finished", "Date finished, newest", [F("date_finished").desc(nulls_last=True), "-updated_at"]),
            ("finished", "Date finished, oldest", [F("date_finished").asc(nulls_last=True), "updated_at"]),
            ("-rating", "Your rating, highest", [F("rating").desc(nulls_last=True), "book__title"]),
            ("title", "Title, A–Z", ["book__title"]),
            ("author", "Author, A–Z", ["book__author", "book__title"]),
        ],
        "empty": "No finished books yet. Mark a book as finished and it will land here.",
    },
}
DATE_RANGES = [("7", "Last 7 days"), ("30", "Last 30 days"), ("365", "Last year")]


def _shelf_page(request, key):
    shelf = SHELVES[key]
    on_shelf = UserBook.objects.filter(user=request.user, status=shelf["status"])
    entries = on_shelf.select_related("book")

    # Date filter: only the values offered in the dropdown are accepted
    days = request.GET.get("added", "")
    if days in dict(DATE_RANGES):
        field = shelf["date_field"]
        since = timedelta(days=int(days))
        if field == "added_at":
            entries = entries.filter(added_at__gte=timezone.now() - since)
        else:
            entries = entries.filter(**{f"{field}__gte": timezone.localdate() - since})
    else:
        days = ""

    # Genre filter: only genres that occur on this shelf are offered
    genres = Genre.objects.filter(bookgenre__book__user_books__in=on_shelf).distinct().order_by("name")
    genre = request.GET.get("genre", "")
    if genre and genres.filter(slug=genre).exists():
        entries = entries.filter(book__bookgenre__genre__slug=genre)
    else:
        genre = ""

    sorts = {value: ordering for value, _, ordering in shelf["sorts"]}
    sort = request.GET.get("sort", "")
    if sort not in sorts:
        sort = shelf["sorts"][0][0]
    entries = entries.order_by(*sorts[sort])

    return render(request, "books/shelf/index.html", {
        "shelf": shelf,
        "shelf_key": key,
        "entries": entries,
        "total": on_shelf.count(),
        "filtered": bool(days or genre),
        "date_ranges": DATE_RANGES,
        "genres": genres,
        "selected": {"added": days, "genre": genre, "sort": sort},
    })


@login_required
def to_be_read(request):
    return _shelf_page(request, "to_read")


@login_required
def finished(request):
    return _shelf_page(request, "finished")


def _save_entry(form):
    """Save the reader's UserBook row and return its status ("" = not on a shelf).

    - Shelf set to "Add to shelf" and nothing else filled in: the row is removed.
    - No shelf picked but something filled in (rating, review, dates, heart):
      a sensible shelf is chosen so the data isn't lost.
    """
    entry = form.save(commit=False)
    has_data = any([entry.rating, entry.favorite, entry.date_started, entry.date_finished, entry.review_text])

    if not entry.status:
        if not has_data:
            if entry.pk:
                entry.delete()
            return ""
        if entry.rating or entry.review_text or entry.date_finished:
            entry.status = UserBook.Status.READ
        elif entry.date_started:
            entry.status = UserBook.Status.READING
        else:
            entry.status = UserBook.Status.TO_READ

    entry.save()
    return entry.status


SERIES_NUMBER = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*$")
SERIES_LEADING = re.compile(r"^\s*(\d+(?:\.\d+)?)")


def _series_order(book):
    """Single numbered books first (#1, #2, #2.5 ...), then box sets and
    part-volumes ("1-5", "5, Part 1"), then anything without a number."""
    pos = book.series_position or ""
    single = SERIES_NUMBER.match(pos)
    if single:
        return (0, float(single.group(1)), book.title)
    leading = SERIES_LEADING.match(pos)
    if leading:
        return (1, float(leading.group(1)), book.title)
    return (2, 0.0, book.title)


def book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    entry = None
    if request.user.is_authenticated:
        entry = UserBook.objects.filter(user=request.user, book=book).first()

    if request.method == "POST":
        if not request.user.is_authenticated:
            if is_ajax:
                return JsonResponse({"ok": False, "errors": ["Log in to save this book."]}, status=403)
            return redirect_to_login(request.get_full_path())

        # Card controls save in the background (ShelfForm, review text untouched);
        # the "Save review" button posts everything (ReviewForm).
        form_class = ShelfForm if is_ajax else ReviewForm
        form = form_class(request.POST, instance=entry or UserBook(user=request.user, book=book))

        if form.is_valid():
            status = _save_entry(form)
            if is_ajax:
                return JsonResponse({"ok": True, "status": status})
            messages.success(request, "Review saved.")
            return redirect("book", book_id=book.pk)

        errors = [e for field_errors in form.errors.values() for e in field_errors]
        if is_ajax:
            return JsonResponse({"ok": False, "errors": errors}, status=400)
        for e in errors:
            messages.error(request, e)

    # Which part of the dates field to show (see script.js)
    if entry and entry.date_finished:
        dates_step = "done"
    elif entry and entry.date_started:
        dates_step = "finish"
    else:
        dates_step = "start"

    reviews = (
        book.user_books.exclude(review_text__isnull=True)
        .exclude(review_text="")
        .select_related("user")
        .order_by("-updated_at")
    )
    if request.user.is_authenticated:
        reviews = reviews.exclude(user=request.user)  # your own review is in the form

    series_books = []
    if book.series_id:
        series_books = sorted(book.series.books.exclude(pk=book.pk), key=_series_order)

    return render(request, "books/book/index.html", {
        "book": book,
        "series_books": series_books,
        "genres": book.genres.order_by("-bookgenre__tag_count")[:3],
        "entry": entry,
        "status_choices": UserBook.Status.choices,
        "dates_step": dates_step,
        "reviews": reviews,
    })


# ---------- Calendar ----------

CAL_VIEWS = [("month", "Month"), ("week", "Week"), ("day", "Day")]
CAL_COLOURS = ["blue", "green", "purple", "cyan"]  # one per book (by id); gold = reading


def _cal_range(view, anchor):
    """First and last day shown, the dates the arrows jump to, and the title."""
    if view == "month":
        first = anchor.replace(day=1)
        last = (first + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        start = first - timedelta(days=first.weekday())          # back to Monday
        end = last + timedelta(days=6 - last.weekday())           # on to Sunday
        prev, nxt = (first - timedelta(days=1)).replace(day=1), last + timedelta(days=1)
        title = format_date(first, "F Y")
    elif view == "week":
        start = anchor - timedelta(days=anchor.weekday())
        end = start + timedelta(days=6)
        prev, nxt = start - timedelta(days=7), start + timedelta(days=7)
        if start.month == end.month:
            title = f"{start.day} – {format_date(end, 'j F Y')}"
        else:
            title = f"{format_date(start, 'j M')} – {format_date(end, 'j M Y')}"
    else:
        start = end = anchor
        prev, nxt = anchor - timedelta(days=1), anchor + timedelta(days=1)
        title = format_date(anchor, "l j F Y")
    return start, end, prev, nxt, title


def _reading_spans(user, start, end, today):
    """Each dated shelf entry as a (first day, last day) span that touches the range.
    A book you're still reading runs up to today."""
    spans = []
    entries = (
        UserBook.objects.filter(user=user)
        .filter(Q(date_started__isnull=False) | Q(date_finished__isnull=False))
        .select_related("book")
    )
    for entry in entries:
        reading = entry.status == UserBook.Status.READING
        first = entry.date_started or entry.date_finished
        if entry.date_finished:
            last = entry.date_finished
        elif reading:
            last = max(today, first)
        else:
            last = first
        first, last = min(first, last), max(first, last)
        if last < start or first > end:
            continue
        spans.append({
            "entry": entry,
            "first": first,
            "last": last,
            "reading": reading,
            "colour": "reading" if reading else CAL_COLOURS[entry.book_id % len(CAL_COLOURS)],
        })
    # earlier first, then longer first, so long bars claim the top rows
    spans.sort(key=lambda sp: (sp["first"], -(sp["last"] - sp["first"]).days, sp["entry"].pk))
    return spans


def _lay_out_row(days, spans):
    """Place the bars for one row of days (a week, or a single day).
    Each bar gets a grid column, span and row; overlapping bars stack."""
    row_first, row_last = days[0]["date"], days[-1]["date"]
    lane_ends = []   # last column taken in each stacked row
    bars = []
    for sp in spans:
        if sp["last"] < row_first or sp["first"] > row_last:
            continue
        a, b = max(sp["first"], row_first), min(sp["last"], row_last)
        col = (a - row_first).days + 1
        span = (b - a).days + 1
        lane = next((i for i, taken in enumerate(lane_ends) if taken < col), None)
        if lane is None:
            lane = len(lane_ends)
            lane_ends.append(0)
        lane_ends[lane] = col + span - 1
        bars.append({**sp, "col": col, "span": span, "row": lane + 2,
                     "open_start": sp["first"] < row_first, "open_end": sp["last"] > row_last})
    return bars


@login_required
def calendar(request):
    today = timezone.localdate()
    view = request.GET.get("view", "")
    if view not in dict(CAL_VIEWS):
        view = "month"
    try:
        anchor = date.fromisoformat(request.GET.get("date", ""))
        if not 1900 <= anchor.year <= 2200:
            raise ValueError
    except ValueError:
        anchor = today

    start, end, prev, nxt, title = _cal_range(view, anchor)
    spans = _reading_spans(request.user, start, end, today)

    days = []
    d = start
    while d <= end:
        days.append({
            "date": d,
            "label": format_date(d, "j M") if d.day == 1 else d.day,
            "out": view == "month" and d.month != anchor.month,
            "today": d == today,
        })
        d += timedelta(days=1)

    per_row = 1 if view == "day" else 7
    rows = []
    for i in range(0, len(days), per_row):
        row_days = days[i:i + per_row]
        rows.append({"days": row_days, "bars": _lay_out_row(row_days, spans)})

    if view == "day":
        weekdays = [format_date(start, "D")]
    else:
        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    return render(request, "books/calendar/index.html", {
        "view": view,
        "views": CAL_VIEWS,
        "title": title,
        "anchor": anchor,
        "prev": prev,
        "next": nxt,
        "today": today,
        "weekdays": weekdays,
        "rows": rows,
        "has_books": bool(spans),
    })
