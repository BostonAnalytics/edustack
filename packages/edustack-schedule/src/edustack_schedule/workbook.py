from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable

import pandas as pd

from edustack_schedule.bu_calendar import load_calendar
from edustack_schedule.planner import (
    SectionSchedule,
    WEEKDAY_LABELS,
    build_section_schedules,
    get_lecture_catalog,
)
from edustack_schedule.semester_rules import normalize_semester
from edustack_schedule.term_resolver import resolve_term

DeliverablesHook = Callable[[pd.DataFrame, list[pd.Timestamp], SectionSchedule], pd.DataFrame]


GENERATED_SHEET_NAMES = {
    "summary": "Summary",
    "module0_catalog": "Module0 Catalog",
    "schedule": "Schedule",
    "online_deliverables": "Online Deliverables",
    "oncampus_deliverables": "OnCampus Deliverables",
}


@dataclass(frozen=True)
class GeneratedWorkbookConfig:
    section_configs_by_semester: dict[str, list[dict]]
    source_workbook: str | Path
    data_dir: str | Path = "data"
    output_path: str | Path | None = None
    sheet_names: dict[str, str] = field(default_factory=lambda: dict(GENERATED_SHEET_NAMES))
    course_details_sheet: str = "Course Details"


def resolve_schedule_term(
    semester: str | None = None,
    year: int | None = None,
) -> tuple[str, int]:
    if semester is None or year is None:
        return resolve_term()
    return normalize_semester(semester), int(year)


def generated_schedule_path(
    semester: str | None = None,
    year: int | None = None,
    *,
    data_dir: str | Path = "data",
) -> Path:
    season, term_year = resolve_schedule_term(semester, year)
    return Path(data_dir) / f"{season.lower()}{str(term_year)[-2:]}_generated_schedule.xlsx"


def format_date(value, fmt: str) -> str:
    return "-" if pd.isna(value) else value.strftime(fmt)


def class_days_label(class_days: list[int]) -> str:
    return "/".join(WEEKDAY_LABELS[day] for day in class_days)


def parse_calendar_date(date_raw: str, year: int, *, range_end: bool = False) -> pd.Timestamp:
    raw = str(date_raw).strip()
    if "–" in raw:
        parts = [part.strip() for part in raw.split("–")]
        raw = parts[-1] if range_end else parts[0]
    return pd.to_datetime(f"{raw} {year}")


def term_dates(semester: str, year: int, *, data_dir: str | Path = "data") -> tuple[pd.Timestamp, pd.Timestamp]:
    calendar = load_calendar(semester, year, data_dir=data_dir)
    begin_rows = calendar[
        calendar["event"].str.contains("Classes Begin", case=False, na=False)
    ]
    end_rows = calendar[
        calendar["event"].str.contains("Last Day of Classes", case=False, na=False)
    ]

    if begin_rows.empty or end_rows.empty:
        raise ValueError(f"Could not find term start/end dates for {semester} {year}.")

    start = parse_calendar_date(begin_rows.iloc[0]["date_raw"], year)
    end = parse_calendar_date(end_rows.iloc[0]["date_raw"], year, range_end=True)
    return start, end


def load_course_catalog(
    source_workbook: str | Path,
    *,
    course_details_sheet: str = "Course Details",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    course_table = pd.read_excel(source_workbook, sheet_name=course_details_sheet)

    module0_catalog = (
        course_table.loc[
            course_table["Lecture"]
            .astype(str)
            .str.strip()
            .str.upper()
            .str.match(r"^L0\.\d+$", na=False),
            ["Lecture", "Title", "Description"],
        ]
        .reset_index(drop=True)
    )

    course_table = course_table.drop(
        columns=["Modules", "Module Name"],
        errors="ignore",
    )
    return get_lecture_catalog(course_table), module0_catalog


def build_schedule_tables(
    *,
    semester: str,
    year: int,
    config: GeneratedWorkbookConfig,
    sections: Iterable[str] | None = None,
    online_deliverables: DeliverablesHook | None = None,
    oncampus_deliverables: DeliverablesHook | None = None,
) -> dict[str, pd.DataFrame]:
    section_plan = build_section_schedules(
        semester=semester,
        year=year,
        sections=sections,
        section_configs_by_semester=config.section_configs_by_semester,
        data_dir=config.data_dir,
    )

    course_table, module0_catalog = load_course_catalog(
        config.source_workbook,
        course_details_sheet=config.course_details_sheet,
    )
    term_start, term_end = term_dates(semester, year, data_dir=config.data_dir)
    max_lectures = max(plan.lecture_count for plan in section_plan.values())
    course_table = course_table.head(max_lectures).reset_index(drop=True)
    schedule = course_table[["Lecture", "Title"]].copy()

    ordered_sections = [
        section
        for section, plan in section_plan.items()
        if plan.modality == "oncampus"
    ] + [
        section
        for section, plan in section_plan.items()
        if plan.modality != "oncampus"
    ]

    for section in ordered_sections:
        dates = section_plan[section].lecture_dates
        schedule[section] = dates + [pd.NaT] * (max_lectures - len(dates))
        schedule[section] = schedule[section].map(lambda date: format_date(date, "%d-%b"))

    summary = pd.DataFrame(
        [
            {
                "Section": section,
                "Modality": plan.modality,
                "Term Start": term_start.strftime("%d-%b (%a)"),
                "Term End": term_end.strftime("%d-%b (%a)"),
                "Class Days": class_days_label(plan.class_days),
                "Weeks": "" if plan.week_count is None else str(plan.week_count),
                "Lectures": plan.lecture_count,
                "Start Date": pd.to_datetime(plan.start_date).strftime("%d-%b (%a)"),
            }
            for section, plan in section_plan.items()
        ]
    )

    online_frames: list[pd.DataFrame] = []
    oncampus_frames: list[pd.DataFrame] = []
    for section, plan in section_plan.items():
        base = pd.DataFrame(
            {"Date": [date.strftime("%d-%b (%a)") for date in plan.lecture_dates]}
        )

        if plan.modality == "oncampus" and oncampus_deliverables:
            deliverables = oncampus_deliverables(base, plan.lecture_dates, plan)
            deliverables.insert(0, "Section", section)
            oncampus_frames.append(deliverables)
        elif plan.modality == "online" and online_deliverables:
            deliverables = online_deliverables(base, plan.lecture_dates, plan)
            deliverables.insert(0, "Section", section)
            online_frames.append(deliverables)

    return {
        "summary": summary,
        "module0_catalog": module0_catalog,
        "schedule": schedule,
        "online_deliverables": (
            pd.concat(online_frames, ignore_index=True)
            if online_frames
            else pd.DataFrame()
        ),
        "oncampus_deliverables": (
            pd.concat(oncampus_frames, ignore_index=True)
            if oncampus_frames
            else pd.DataFrame()
        ),
    }


def build_generated_schedule_workbook(
    *,
    config: GeneratedWorkbookConfig,
    semester: str | None = None,
    year: int | None = None,
    sections: Iterable[str] | None = None,
    online_deliverables: DeliverablesHook | None = None,
    oncampus_deliverables: DeliverablesHook | None = None,
) -> Path:
    season, term_year = resolve_schedule_term(semester, year)
    output = (
        Path(config.output_path)
        if config.output_path
        else generated_schedule_path(season, term_year, data_dir=config.data_dir)
    )
    output.parent.mkdir(parents=True, exist_ok=True)

    tables = build_schedule_tables(
        semester=season,
        year=term_year,
        config=config,
        sections=sections,
        online_deliverables=online_deliverables,
        oncampus_deliverables=oncampus_deliverables,
    )

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for key, sheet_name in config.sheet_names.items():
            tables[key].to_excel(writer, sheet_name=sheet_name, index=False)

    return output


def load_generated_schedule(
    sheet: str,
    *,
    semester: str | None = None,
    year: int | None = None,
    workbook_path: str | Path | None = None,
    data_dir: str | Path = "data",
    sheet_names: dict[str, str] | None = None,
) -> pd.DataFrame:
    names = sheet_names or GENERATED_SHEET_NAMES
    sheet_name = names.get(sheet, sheet)
    workbook = Path(workbook_path) if workbook_path else generated_schedule_path(
        semester,
        year,
        data_dir=data_dir,
    )

    if not workbook.exists():
        raise FileNotFoundError(
            f"{workbook} does not exist. Run `edustack-schedule generate` "
            "after updating your course schedule config."
        )

    df = pd.read_excel(workbook, sheet_name=sheet_name).fillna("")
    if "Weeks" in df.columns:
        df["Weeks"] = df["Weeks"].map(
            lambda value: str(int(value))
            if isinstance(value, float) and value.is_integer()
            else str(value)
        )
    return df
