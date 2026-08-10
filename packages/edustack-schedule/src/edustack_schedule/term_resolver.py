from __future__ import annotations

from datetime import date


def resolve_term(today: date | None = None) -> tuple[str, int]:
    """Resolve the BU semester/year from the render date.

    The resolver is intentionally forward-looking for course prep:
    Spring opens on December 15 for the next calendar year; before that,
    December still resolves to Fall of the current year.
    """

    if today is None:
        today = date.today()

    year = today.year
    month = today.month

    if month == 12 and today.day >= 15:
        return "Spring", year + 1
    if month in (1, 2, 3):
        return "Spring", year
    if month in (4, 5, 6):
        return "Summer", year
    if month in (7, 8, 9, 10, 11, 12):
        return "Fall", year

    raise ValueError(f"Could not resolve an academic term for {today.isoformat()}.")
