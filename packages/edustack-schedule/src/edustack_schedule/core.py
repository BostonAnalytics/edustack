from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable

import pandas as pd


def generate_schedule(
    start_date: datetime,
    class_days: Iterable[int],
    breaks: Iterable[tuple[datetime, datetime]],
    lecture_count: int,
    holiday_substitutions: dict[datetime, datetime] | None = None,
    output_path: str | Path | None = None,
    return_dates: bool = False,
) -> pd.DataFrame | tuple[pd.DataFrame, list[datetime]]:
    """Generate lecture dates while skipping breaks and honoring substitutions.

    `class_days` uses Python weekday indexes: Monday=0 through Sunday=6.
    """

    holiday_substitutions = holiday_substitutions or {}
    class_day_set = set(class_days)
    break_windows = list(breaks)
    lectures: list[datetime] = []
    current = start_date

    while len(lectures) < lecture_count:
        if current in holiday_substitutions:
            lectures.append(holiday_substitutions[current])
        elif current.weekday() in class_day_set:
            if not any(start <= current <= end for start, end in break_windows):
                lectures.append(current)

        current += timedelta(days=1)

    df = pd.DataFrame(
        {
            "#": [f"L{i + 1}" for i in range(len(lectures))],
            "Date": [date.strftime("%d-%b (%a)") for date in lectures],
        }
    )

    if output_path:
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)
        df.to_excel(output, index=False)

    if return_dates:
        return df, lectures
    return df


def generate_online_schedule(
    *,
    start_date: str,
    lecture_count: int = 6,
    class_days: list[int] | None = None,
) -> tuple[pd.DataFrame, list[datetime]]:
    """Generate a simple weekly online schedule from an explicit start date."""

    if class_days is None:
        class_days = [1]

    start = datetime.strptime(start_date, "%Y-%m-%d")
    schedule_df, lecture_dates = generate_schedule(
        start_date=start,
        class_days=class_days,
        breaks=[],
        lecture_count=lecture_count,
        return_dates=True,
    )
    return schedule_df, lecture_dates


def generate_online_dates(start_date: str | datetime, n_weeks: int = 7) -> list[pd.Timestamp]:
    """Return one online anchor date per week."""

    start = pd.to_datetime(start_date)
    return [start + timedelta(weeks=i) for i in range(n_weeks)]
