from django import template

register = template.Library()


@register.filter
def short_number(value):
    """4942365 -> '4.9M', 147210 -> '147k', 950 -> '950'."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return ""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M".replace(".0M", "M")
    if n >= 1_000:
        return f"{n // 1_000}k"
    return str(n)


@register.filter
def pub_year(value):
    """1902 -> '1902', -750 -> '750 BC'."""
    try:
        year = int(value)
    except (TypeError, ValueError):
        return ""
    return f"{-year} BC" if year < 0 else str(year)


@register.filter
def star_range(count):
    """[(1, on), ..., (5, on)] where 'on' is True for stars up to `count`."""
    try:
        count = int(count or 0)
    except (TypeError, ValueError):
        count = 0
    return [(i, i <= count) for i in range(1, 6)]


@register.simple_tag
def static_v(path):
    """Like {% static %}, plus ?v=<last modified time>, so the browser loads a
    fresh copy whenever the file changes instead of reusing an old cached one."""
    import os
    from django.contrib.staticfiles import finders
    from django.templatetags.static import static

    url = static(path)
    found = finders.find(path)
    if not found:
        return url
    return f"{url}?v={int(os.path.getmtime(found))}"


TITLE_LIMIT = 40
SUBTITLE_SEPARATORS = (": ", " - ", " – ", " — ")


@register.filter
def short_title(title, limit=TITLE_LIMIT):
    """Card-friendly title.
    1. Drop a subtitle: "Sex at Dawn: The Prehistoric Origins..." -> "Sex at Dawn".
    2. Still too long? Cut at the last whole word before `limit` and add "...".
    The full title stays on the book page and in the card's hover text."""
    title = (title or "").strip()
    limit = int(limit)
    for sep in SUBTITLE_SEPARATORS:
        head = title.split(sep, 1)[0].strip()
        if head != title and len(head) >= 3:
            title = head
            break
    if len(title) > limit:
        cut = title[:limit]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        title = cut.rstrip(" ,;:.-–—(") + "…"
    return title
