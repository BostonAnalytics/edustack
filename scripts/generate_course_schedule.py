"""Generate a simple course schedule from the feeder workbook."""

from __future__ import annotations

import argparse
from datetime import timedelta
from pathlib import Path

import pandas as pd


def build_schedule(workbook_path: Path) -> pd.DataFrame:
    course = pd.read_excel(workbook_path, sheet_name="Course Details")
    sections = pd.read_excel(workbook_path, sheet_name="Sections")

    if sections.empty:
        raise SystemExit("Sections sheet must contain at least one section row.")

    first_section = sections.iloc[0]
    start_date = pd.to_datetime(first_section["Start Date"])

    rows: list[dict[str, object]] = []
    for index, item in course.iterrows():
        module_number = index // 2 + 1
        week_start = start_date + timedelta(weeks=module_number - 1)
        rows.append(
            {
                "Week": module_number,
                "Module": item.get("Module", ""),
                "Lecture": item.get("Lecture", ""),
                "Title": item.get("Title", ""),
                "Date": week_start.date().isoformat(),
                "Mode": item.get("Mode", ""),
                "Source File": item.get("Source File", ""),
            }
        )

    return pd.DataFrame(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a draft schedule CSV from Course-Schedule.xlsx."
    )
    parser.add_argument("workbook", help="Path to Course-Schedule.xlsx.")
    parser.add_argument(
        "output",
        nargs="?",
        default="data/generated_schedule.csv",
        help="CSV output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = Path(args.workbook).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    schedule = build_schedule(workbook_path)
    schedule.to_csv(output_path, index=False)
    print(f"Generated draft schedule: {output_path}")


if __name__ == "__main__":
    main()
