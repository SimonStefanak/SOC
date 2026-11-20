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
