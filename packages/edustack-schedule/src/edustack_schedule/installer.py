from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

WRAPPERS: dict[str, str] = {
    "bu_calendar/__init__.py": '"""Compatibility wrappers for EduStack BU calendar helpers."""\n',
    "bu_calendar/bu_calendar_cache.py": """from edustack_schedule.bu_calendar import calendar_csv, load_calendar
""",
    "bu_calendar/bu_calendar_scrape.py": """from edustack_schedule.bu_calendar import BU_SEMESTER_CALENDAR_URL as BU_URL
from edustack_schedule.bu_calendar import scrape_bu_calendar
""",
    "bu_calendar/bu_calendar_utils.py": """from edustack_schedule.bu_calendar import parse_range
""",
    "schedules/__init__.py": '"""Course-local schedule config plus EduStack schedule wrappers."""\n',
    "schedules/engine.py": """from edustack_schedule.core import generate_schedule
""",
    "schedules/term_resolver.py": """from edustack_schedule.term_resolver import resolve_term
""",
    "schedules/online_schedule.py": """from edustack_schedule.core import generate_online_schedule as generate
""",
    "schedules/build_schedule.py": """from __future__ import annotations

from datetime import timedelta

import pandas as pd

from edustack_schedule.bu_calendar import load_calendar
from edustack_schedule.core import generate_online_dates
from edustack_schedule.semester_rules import generate_term_schedule
from edustack_schedule.term_resolver import resolve_term


def build(
    return_dates=False,
    class_days=None,
    season=None,
    year=None,
    lecture_count=14,
    start_date=None,
    write_output=True,
):
    if class_days is None:
        raise ValueError("class_days must be provided")

    if season is None or year is None:
        season, year = resolve_term()

    calendar_df = load_calendar(season, year)
    output_path = f"data/{season.lower()}_schedule_{year}.xlsx" if write_output else None

    return generate_term_schedule(
        calendar_df,
        semester=season,
        output_path=output_path,
        return_dates=return_dates,
        class_days=class_days,
        lecture_count=lecture_count,
        start_date=start_date,
    )
""",
    "schedules/fall.py": """from edustack_schedule.semester_rules import generate_term_schedule


def generate(calendar_df, **kwargs):
    return generate_term_schedule(calendar_df, semester="Fall", **kwargs)
""",
    "schedules/spring.py": """from edustack_schedule.semester_rules import generate_term_schedule


def generate(calendar_df, **kwargs):
    return generate_term_schedule(calendar_df, semester="Spring", **kwargs)
""",
    "schedules/summer.py": """from edustack_schedule.semester_rules import generate_term_schedule


def generate(calendar_df, **kwargs):
    return generate_term_schedule(calendar_df, semester="Summer", **kwargs)
""",
    "schedules/generated_schedule.py": """from __future__ import annotations

from pathlib import Path

from edustack_schedule.workbook import (
    GeneratedWorkbookConfig,
    build_generated_schedule_workbook as _build_generated_schedule_workbook,
    generated_schedule_path,
    load_generated_schedule,
)
from schedules import config as schedule_config


def _default_source_workbook() -> Path:
    configured = getattr(schedule_config, "source_workbook", None)
    if configured:
        return Path(configured)

    for candidate in (
        Path("data/Course-Schedule.xlsx"),
        Path("data/AD698-Schedule.xlsx"),
    ):
        if candidate.exists():
            return candidate

    return Path("data/Course-Schedule.xlsx")


COURSE_SOURCE_WORKBOOK = _default_source_workbook()


def _deliverables_hooks():
    try:
        from schedules.deliverables.oncampus_deliverables import apply_oncampus_deliverables
        from schedules.presentation import format_deliverables_view
    except ImportError:
        oncampus_hook = None
    else:
        def oncampus_hook(base, lecture_dates, plan):
            return format_deliverables_view(
                apply_oncampus_deliverables(
                    base,
                    lecture_dates,
                    class_day_index=plan.class_days[0],
                )
            )

    try:
        from schedules.deliverables.online_deliverables import apply_online_deliverables
        from schedules.presentation import format_deliverables_view
    except ImportError:
        online_hook = None
    else:
        def online_hook(base, lecture_dates, plan):
            return format_deliverables_view(
                apply_online_deliverables(base, lecture_dates)
            )

    return online_hook, oncampus_hook


def build_generated_schedule_workbook(
    *,
    semester=getattr(schedule_config, "semester", None),
    year=getattr(schedule_config, "year", None),
    sections=None,
    source_workbook=COURSE_SOURCE_WORKBOOK,
    output_path=None,
):
    config = GeneratedWorkbookConfig(
        section_configs_by_semester=schedule_config.section_configs_by_semester,
        source_workbook=source_workbook,
        output_path=output_path,
    )
    online_hook, oncampus_hook = _deliverables_hooks()
    return _build_generated_schedule_workbook(
        config=config,
        semester=semester,
        year=year,
        sections=sections,
        online_deliverables=online_hook,
        oncampus_deliverables=oncampus_hook,
    )


if __name__ == "__main__":
    print(build_generated_schedule_workbook())
""",
}


CONFIG_TEMPLATE = """# Course-specific schedule configuration for EduStack.
# Set semester/year to None to resolve from the render date.

semester = None
year = None
source_workbook = "data/Course-Schedule.xlsx"

section_configs_by_semester = {
    "Spring": [],
    "Summer": [],
    "Fall": [],
}
"""


@dataclass(frozen=True)
class InstalledFile:
    path: Path
    action: str


def install_wrappers(
    course_root: str | Path,
    *,
    force: bool = False,
    dry_run: bool = False,
    include_config: bool = False,
) -> list[InstalledFile]:
    """Install course-local compatibility wrappers.

    Existing files are skipped unless `force=True`, so this is safe to preview
    before migrating an active course repository.
    """

    root = Path(course_root).resolve()
    files = dict(WRAPPERS)
    if include_config:
        files["schedules/config.py"] = CONFIG_TEMPLATE

    installed: list[InstalledFile] = []
    for relative_path, content in files.items():
        target = root / relative_path
        if target.exists() and not force:
            installed.append(InstalledFile(target, "skipped"))
            continue

        installed.append(InstalledFile(target, "would-write" if dry_run else "written"))
        if dry_run:
            continue

        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")

    return installed
