from __future__ import annotations

from datetime import date, datetime

import pandas as pd
import pytest

from edustack_schedule.bu_calendar import parse_range
from edustack_schedule.planner import build_section_schedules
from edustack_schedule.semester_rules import generate_term_schedule
from edustack_schedule.term_resolver import resolve_term
from edustack_schedule.workbook import (
    GeneratedWorkbookConfig,
    build_generated_schedule_workbook,
)


def test_resolve_term_uses_mid_december_spring_boundary():
    assert resolve_term(date(2026, 12, 14)) == ("Fall", 2026)
    assert resolve_term(date(2026, 12, 15)) == ("Spring", 2027)
    assert resolve_term(date(2026, 8, 10)) == ("Fall", 2026)


def test_parse_range_infers_repeated_month():
    assert parse_range("November 25 – 30", 2026) == (
        datetime(2026, 11, 25),
        datetime(2026, 11, 30),
    )


def test_fall_schedule_uses_monday_substitute_for_suspended_class():
    calendar_df = pd.DataFrame(
        [
            {"term": "Fall 2026", "date_raw": "September 2", "event": "Classes Begin"},
            {"term": "Fall 2026", "date_raw": "October 12", "event": "Classes Suspended"},
            {
                "term": "Fall 2026",
                "date_raw": "October 13",
                "event": "Substitute a Monday schedule of classes",
            },
            {"term": "Fall 2026", "date_raw": "November 25 – 29", "event": "Thanksgiving Recess"},
        ]
    )

    _, lecture_dates = generate_term_schedule(
        calendar_df,
        semester="Fall",
        return_dates=True,
        class_days=[0],
        lecture_count=7,
        start_date="2026-09-14",
    )

    assert datetime(2026, 10, 12) not in lecture_dates
    assert datetime(2026, 10, 13) in lecture_dates


def test_section_planner_reads_cached_calendar_and_validates_start_year(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pd.DataFrame(
        [
            {"term": "Fall 2026", "date_raw": "September 2", "event": "Classes Begin"},
            {"term": "Fall 2026", "date_raw": "December 10", "event": "Last Day of Classes"},
        ]
    ).to_csv(data_dir / "fall_calendar_2026.csv", index=False)

    schedules = build_section_schedules(
        semester="Fall",
        year=2026,
        section_configs_by_semester={
            "Fall": [
                {
                    "section": "A1",
                    "modality": "oncampus",
                    "start_date": "2026-09-14",
                    "class_days": ["Mon"],
                    "lecture_count": 2,
                },
                {
                    "section": "O1",
                    "modality": "online",
                    "start_date": "2026-09-17",
                    "class_days": ["Thu"],
                    "weeks": 2,
                    "lectures_per_week": 2,
                },
            ]
        },
        data_dir=data_dir,
    )

    assert [d.strftime("%Y-%m-%d") for d in schedules["A1"].lecture_dates] == [
        "2026-09-14",
        "2026-09-21",
    ]
    assert len(schedules["O1"].lecture_dates) == 4
    assert schedules["O1"].lecture_dates[0] == schedules["O1"].lecture_dates[1]


def test_section_planner_rejects_stale_config_year(tmp_path):
    with pytest.raises(ValueError, match="Configure a 2027 start date"):
        build_section_schedules(
            semester="Spring",
            year=2027,
            section_configs_by_semester={
                "Spring": [
                    {
                        "section": "A1",
                        "modality": "oncampus",
                        "start_date": "2026-01-26",
                        "class_days": ["Mon"],
                    }
                ]
            },
            data_dir=tmp_path,
        )


def test_build_generated_schedule_workbook_writes_summary_and_schedule(tmp_path):
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    pd.DataFrame(
        [
            {"term": "Fall 2026", "date_raw": "September 2", "event": "Classes Begin"},
            {"term": "Fall 2026", "date_raw": "December 10", "event": "Last Day of Classes"},
        ]
    ).to_csv(data_dir / "fall_calendar_2026.csv", index=False)

    source = data_dir / "Course-Schedule.xlsx"
    pd.DataFrame(
        [
            {"Lecture": "L0.1", "Title": "Orientation", "Description": "Start here"},
            {"Lecture": "L1.1", "Title": "Intro", "Description": "First class"},
            {"Lecture": "L1.2", "Title": "Practice", "Description": "Second class"},
        ]
    ).to_excel(source, sheet_name="Course Details", index=False)

    output = build_generated_schedule_workbook(
        config=GeneratedWorkbookConfig(
            section_configs_by_semester={
                "Fall": [
                    {
                        "section": "A1",
                        "modality": "oncampus",
                        "start_date": "2026-09-14",
                        "class_days": ["Mon"],
                        "lecture_count": 2,
                    }
                ]
            },
            source_workbook=source,
            data_dir=data_dir,
        ),
        semester="Fall",
        year=2026,
    )

    summary = pd.read_excel(output, sheet_name="Summary")
    schedule = pd.read_excel(output, sheet_name="Schedule")
    module0 = pd.read_excel(output, sheet_name="Module0 Catalog")

    assert summary.loc[0, "Section"] == "A1"
    assert list(schedule["A1"]) == ["14-Sep", "21-Sep"]
    assert module0.loc[0, "Lecture"] == "L0.1"
