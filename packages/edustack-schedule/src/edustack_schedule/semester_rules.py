from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd

from edustack_schedule.bu_calendar import parse_range, parse_single_date
from edustack_schedule.core import generate_schedule

SUPPORTED_SEMESTERS = ("Spring", "Summer", "Fall")


def normalize_semester(semester: str) -> str:
    key = semester.strip().title()
    if key not in SUPPORTED_SEMESTERS:
        allowed = ", ".join(SUPPORTED_SEMESTERS)
        raise ValueError(f"Unsupported semester '{semester}'. Choose one of: {allowed}")
    return key


def first_meeting_on_or_after(start: datetime, class_days: list[int]) -> datetime:
    current = start
    while current.weekday() not in class_days:
        current += timedelta(days=1)
    return current


def classes_begin(calendar_df: pd.DataFrame, year: int) -> datetime:
    start_row = calendar_df[
        calendar_df["event"].str.contains("Classes Begin", case=False, na=False)
    ]
    if start_row.empty:
        raise ValueError("Could not find 'Classes Begin' in the BU calendar data.")
    return datetime.strptime(start_row.iloc[0]["date_raw"], "%B %d").replace(year=year)


def spring_breaks(calendar_df: pd.DataFrame, year: int) -> list[tuple[datetime, datetime]]:
    return [
        parse_range(row["date_raw"], year)
        for _, row in calendar_df[
            calendar_df["event"].str.contains("Spring Recess", case=False, na=False)
        ].iterrows()
    ]


def fall_breaks_and_substitutions(
    calendar_df: pd.DataFrame,
    year: int,
) -> tuple[list[tuple[datetime, datetime]], dict[datetime, datetime]]:
    breaks: list[tuple[datetime, datetime]] = []
    suspended_dates: list[datetime] = []

    for _, row in calendar_df.iterrows():
        event = row["event"]
        date_raw = row["date_raw"]

        if "Thanksgiving Recess" in event or "Study Period" in event:
            breaks.append(parse_range(date_raw, year))
        elif "Classes Suspended" in event:
            suspended_date = parse_single_date(date_raw, year)
            suspended_dates.append(suspended_date)
            breaks.append((suspended_date, suspended_date))

    substitutions: dict[datetime, datetime] = {}
    substitute_rows = calendar_df[
        calendar_df["event"].str.contains(
            "Substitute a Monday schedule", case=False, na=False
        )
    ]

    for _, row in substitute_rows.iterrows():
        substitute_date = parse_single_date(row["date_raw"], year)
        prior_mondays = [
            date
            for date in suspended_dates
            if date.weekday() == 0 and date < substitute_date
        ]
        if prior_mondays:
            substitutions[max(prior_mondays)] = substitute_date

    return breaks, substitutions


def generate_term_schedule(
    calendar_df: pd.DataFrame,
    *,
    semester: str,
    output_path=None,
    return_dates: bool = False,
    class_days: list[int] | None = None,
    lecture_count: int = 14,
    start_date: str | None = None,
):
    """Generate a Spring/Summer/Fall schedule from BU calendar rows."""

    if class_days is None:
        raise ValueError("class_days must be provided")

    season = normalize_semester(semester)
    year = int(calendar_df.iloc[0]["term"].split()[-1])
    first_meeting = (
        datetime.strptime(start_date, "%Y-%m-%d")
        if start_date
        else first_meeting_on_or_after(classes_begin(calendar_df, year), class_days)
    )

    breaks: list[tuple[datetime, datetime]] = []
    substitutions: dict[datetime, datetime] = {}
    if season == "Spring":
        breaks = spring_breaks(calendar_df, year)
    elif season == "Fall":
        breaks, substitutions = fall_breaks_and_substitutions(calendar_df, year)

    return generate_schedule(
        start_date=first_meeting,
        class_days=class_days,
        breaks=breaks,
        holiday_substitutions=substitutions,
        lecture_count=lecture_count,
        output_path=output_path,
        return_dates=return_dates,
    )
