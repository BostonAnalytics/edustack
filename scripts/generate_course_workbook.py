"""Create the standard course feeder workbook."""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SHEETS: dict[str, list[str]] = {
    "Course Details": [
        "Module",
        "Lecture",
        "Title",
        "Description",
        "Mode",
        "Source File",
    ],
    "Sections": [
        "Section",
        "Modality",
        "Location",
        "Instructor",
        "Email",
        "Start Date",
        "Meeting Days",
        "Meeting Time",
    ],
    "Grade": [
        "Category",
        "Count",
        "Points Each",
        "Total Points",
        "Weight",
    ],
    "Deliverables": [
        "Module",
        "Deliverable",
        "Type",
        "Source File",
        "Due Offset Days",
        "Points",
    ],
}


EXAMPLE_ROWS: dict[str, list[list[object]]] = {
    "Course Details": [
        [
            "Module 1",
            "L1.1",
            "Course Foundations",
            "Introduce the course workflow, tools, and first applied example.",
            "Online; On-Campus",
            "M01/M01_LN1.qmd",
        ],
        [
            "Module 1",
            "L1.2",
            "Applied Workflow",
            "Extend the first example into a lab, assignment, and project step.",
            "Online; On-Campus",
            "M01/M01_LN2.qmd",
        ],
    ],
    "Sections": [
        [
            "A1",
            "On-Campus",
            "Room TBD",
            "Instructor Name",
            "instructor@example.edu",
            "2026-01-20",
            "Tuesday",
            "6:00 PM-8:45 PM",
        ],
        [
            "O1",
            "Online",
            "Blackboard Ultra",
            "Instructor Name",
            "instructor@example.edu",
            "2026-01-20",
            "Tuesday",
            "Asynchronous",
        ],
    ],
    "Grade": [
        ["Labs", 2, 10, 20, "20%"],
        ["Assignments", 1, 30, 30, "30%"],
        ["Project", 1, 40, 40, "40%"],
        ["Participation", 2, 5, 10, "10%"],
    ],
    "Deliverables": [
        ["Module 1", "Lab 1", "Lab", "M01/M01_Lab1.qmd", 5, 10],
        ["Module 1", "Assignment", "Assignment", "M01/M01_A.qmd", 7, 30],
        ["Module 1", "Project Step", "Project", "M01/M01_Proj.qmd", 10, 40],
        [
            "Module 1",
            "Participation 1",
            "Participation",
            "M01/M01_Participation1.qmd",
            3,
            5,
        ],
    ],
}


def create_workbook(output_path: Path, overwrite: bool) -> None:
    if output_path.exists() and not overwrite:
        raise SystemExit(f"Workbook already exists: {output_path}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for sheet_name, columns in SHEETS.items():
            df = pd.DataFrame(EXAMPLE_ROWS.get(sheet_name, []), columns=columns)
            df.to_excel(writer, sheet_name=sheet_name, index=False)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the standard course feeder workbook."
    )
    parser.add_argument(
        "output",
        nargs="?",
        default="data/Course-Schedule.xlsx",
        help="Workbook path to create.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    create_workbook(output_path, args.overwrite)
    print(f"Created course feeder workbook: {output_path}")


if __name__ == "__main__":
    main()
