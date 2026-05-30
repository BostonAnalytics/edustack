"""Validate the standard course feeder workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from generate_course_workbook import SHEETS


def validate_workbook(path: Path) -> list[str]:
    errors: list[str] = []

    if not path.exists():
        return [f"Workbook does not exist: {path}"]

    workbook = pd.ExcelFile(path)
    sheet_names = set(workbook.sheet_names)

    for sheet_name, expected_columns in SHEETS.items():
        if sheet_name not in sheet_names:
            errors.append(f"Missing sheet: {sheet_name}")
            continue

        df = pd.read_excel(path, sheet_name=sheet_name, nrows=0)
        actual_columns = [str(col) for col in df.columns]
        missing = [col for col in expected_columns if col not in actual_columns]
        if missing:
            errors.append(f"{sheet_name}: missing columns: {', '.join(missing)}")

    return errors


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate the standard course feeder workbook."
    )
    parser.add_argument(
        "workbook",
        nargs="?",
        default="data/Course-Schedule.xlsx",
        help="Workbook path to validate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    workbook_path = Path(args.workbook).expanduser().resolve()
    errors = validate_workbook(workbook_path)

    if errors:
        print("Workbook validation failed:")
        for error in errors:
            print(f"- {error}")
        raise SystemExit(1)

    print(f"Workbook is valid: {workbook_path}")


if __name__ == "__main__":
    main()
