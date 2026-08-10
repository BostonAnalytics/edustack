from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from edustack_schedule.bu_calendar import load_calendar
from edustack_schedule.core import generate_online_schedule
from edustack_schedule.semester_rules import (
    SUPPORTED_SEMESTERS,
    generate_term_schedule,
    normalize_semester,
)

WEEKDAY_LABELS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
WEEKDAY_INDEX = {label.lower(): i for i, label in enumerate(WEEKDAY_LABELS)}
WEEKDAY_INDEX.update(
    {
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }
)

DEFAULT_ONLINE_WEEK_COUNT = 6
ONLINE_LECTURES_PER_WEEK = 2
DEFAULT_ONCAMPUS_LECTURE_COUNT = 12


@dataclass(frozen=True)
class SectionSchedule:
    section: str
    modality: str
    lecture_count: int
    week_count: int | None
    class_days: list[int]
    start_date: str
    lecture_dates: list[datetime]


def normalize_modality(modality: str) -> str:
    key = modality.strip().lower().replace("-", "")
    if key in {"online", "o1", "o2"}:
        return "online"
    if key in {"oncampus", "campus", "a1", "a2"}:
        return "oncampus"
    raise ValueError("Modality must be 'online' or 'oncampus'.")


def get_lecture_catalog(course_df: pd.DataFrame) -> pd.DataFrame:
    lecture_col = course_df["Lecture"].astype(str).str.strip().str.upper()
    valid_rows = lecture_col.str.match(r"^L\d+\.\d+$", na=False)
    no_module_zero = ~lecture_col.str.match(r"^L0\.\d+$", na=False)
    return course_df.loc[valid_rows & no_module_zero].reset_index(drop=True)


def parse_class_day(day: int | str) -> int:
    if isinstance(day, int):
        if day not in range(7):
            raise ValueError("Integer class days must be between 0=Mon and 6=Sun.")
        return day

    key = day.strip().lower()
    if key not in WEEKDAY_INDEX:
        allowed = ", ".join(WEEKDAY_LABELS)
        raise ValueError(f"Unsupported class day '{day}'. Use one of: {allowed}")
    return WEEKDAY_INDEX[key]


def normalize_class_days(
    raw_class_days: Iterable[int | str] | None,
    *,
    start_date: str,
) -> list[int]:
    if raw_class_days is None:
        return [datetime.strptime(start_date, "%Y-%m-%d").weekday()]

    class_days = [parse_class_day(day) for day in raw_class_days]
    if not class_days:
        raise ValueError("class_days must contain at least one day.")
    return class_days


def section_modality(section: str, configured_modality: str | None) -> str:
    if configured_modality:
        return normalize_modality(configured_modality)
    if section.upper().startswith("O"):
        return "online"
    if section.upper().startswith("A"):
        return "oncampus"
    raise ValueError(
        f"Section '{section}' needs a modality because it does not start with O or A."
    )


def lecture_count_for(modality: str, config: dict[str, Any]) -> int:
    if modality == "online":
        online_weeks = int(config.get("weeks", DEFAULT_ONLINE_WEEK_COUNT))
        lectures_per_week = int(config.get("lectures_per_week", ONLINE_LECTURES_PER_WEEK))
        return online_weeks * lectures_per_week
    return int(config.get("lecture_count", DEFAULT_ONCAMPUS_LECTURE_COUNT))


def validate_start_date_matches_class_days(
    *,
    semester: str,
    section: str,
    start_date: str,
    class_days: list[int],
) -> None:
    start = datetime.strptime(start_date, "%Y-%m-%d")
    if start.weekday() in class_days:
        return

    class_day_labels = "/".join(WEEKDAY_LABELS[day] for day in class_days)
    start_label = start.strftime("%Y-%m-%d (%a)")
    raise ValueError(
        f"Start date for {semester} / {section} is {start_label}, "
        f"but configured class days are {class_day_labels}. "
        "Use the first actual class meeting date or update class_days."
    )


def build_section_schedules(
    *,
    semester: str,
    year: int,
    section_configs_by_semester: dict[str, list[dict[str, Any]]],
    sections: Iterable[str] | None = None,
    modalities: Iterable[str] | None = None,
    class_days_override: dict[str, list[int | str]] | None = None,
    data_dir: str | Path = "data",
) -> dict[str, SectionSchedule]:
    """Build lecture dates for active course sections.

    The section config is intentionally plain data so each course can keep
    section starts, modalities, and lecture counts in its own repo.
    """

    season = normalize_semester(semester)
    configured_sections = section_configs_by_semester.get(season, [])
    overrides = class_days_override or {}
    section_filter = {s.strip().upper() for s in sections} if sections else None
    modality_filter = (
        {normalize_modality(modality) for modality in modalities}
        if modalities is not None
        else None
    )
    schedules: dict[str, SectionSchedule] = {}

    for config in configured_sections:
        if config.get("active", True) is False:
            continue

        section = str(config["section"]).strip().upper()
        modality = section_modality(section, config.get("modality"))
        if section_filter is not None and section not in section_filter:
            continue
        if modality_filter is not None and modality not in modality_filter:
            continue

        start_date = str(config.get("start_date", "")).strip()
        if not start_date:
            raise ValueError(
                f"Missing start date for {season} / {section}. "
                "Provide it in section_configs_by_semester."
            )
        start_year = datetime.strptime(start_date, "%Y-%m-%d").year
        if start_year != year:
            raise ValueError(
                f"Start date for {season} {year} / {section} is {start_date}. "
                f"Configure a {year} start date in section_configs_by_semester."
            )

        class_days = normalize_class_days(
            overrides.get(section, config.get("class_days")),
            start_date=start_date,
        )
        lecture_count = lecture_count_for(modality, config)
        week_count = (
            int(config.get("weeks", DEFAULT_ONLINE_WEEK_COUNT))
            if modality == "online"
            else config.get("weeks")
        )

        validate_start_date_matches_class_days(
            semester=season,
            section=section,
            start_date=start_date,
            class_days=class_days,
        )

        if modality == "oncampus":
            calendar_df = load_calendar(season, year, data_dir=data_dir)
            _, lecture_dates = generate_term_schedule(
                calendar_df,
                semester=season,
                return_dates=True,
                class_days=class_days,
                lecture_count=lecture_count,
                start_date=start_date,
            )
        else:
            lectures_per_week = int(config.get("lectures_per_week", ONLINE_LECTURES_PER_WEEK))
            _, weekly_dates = generate_online_schedule(
                start_date=start_date,
                lecture_count=week_count or DEFAULT_ONLINE_WEEK_COUNT,
                class_days=class_days,
            )
            lecture_dates = [
                date
                for date in weekly_dates
                for _ in range(lectures_per_week)
            ]

        schedules[section] = SectionSchedule(
            section=section,
            modality=modality,
            lecture_count=lecture_count,
            week_count=week_count,
            class_days=class_days,
            start_date=start_date,
            lecture_dates=lecture_dates,
        )

    if not schedules:
        allowed = ", ".join(SUPPORTED_SEMESTERS)
        raise ValueError(f"No active sections configured for {season}. Known terms: {allowed}.")

    return schedules
