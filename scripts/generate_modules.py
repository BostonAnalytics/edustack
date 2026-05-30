"""Generate the standard Quarto course module scaffold.

This script creates module folders using the canonical naming convention used
throughout the book:

    M01/M01_A.qmd
    M01/M01_LN1.qmd
    M01/M01_P1.qmd
    M01/M01_Proj.qmd
    M01/M01_Lab1.qmd
    M01/M01_Participation1.qmd

Existing files are left untouched by default.
"""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_START_MODULE = 1
DEFAULT_END_MODULE = 7

QMD_FILES = {
    "Assignment": "{module}_A.qmd",
    "Lecture Note 1": "{module}_LN1.qmd",
    "Lecture Note 2": "{module}_LN2.qmd",
    "Presentation 1": "{module}_P1.qmd",
    "Presentation 2": "{module}_P2.qmd",
    "Project": "{module}_Proj.qmd",
    "Lab 1": "{module}_Lab1.qmd",
    "Lab 2": "{module}_Lab2.qmd",
    "Participation 1": "{module}_Participation1.qmd",
    "Participation 2": "{module}_Participation2.qmd",
}

SUBFOLDERS = (
    "data",
    "output",
    "{module}_lecture01_figures",
    "{module}_lecture02_figures",
    "{module}_presentation01_files",
    "{module}_presentation02_files",
    "{module}_P1_files",
    "{module}_P2_files",
)


def module_name(number: int) -> str:
    return f"M{number:02d}"


def qmd_stub(title: str) -> str:
    return f'---\ntitle: "{title}"\n---\n\n# {title}\n'


def generate_module(root: Path, number: int, overwrite: bool) -> list[Path]:
    module = module_name(number)
    module_dir = root / module
    module_dir.mkdir(parents=True, exist_ok=True)

    created: list[Path] = []

    for label, pattern in QMD_FILES.items():
        file_path = module_dir / pattern.format(module=module)
        if file_path.exists() and not overwrite:
            continue
        file_path.write_text(qmd_stub(f"{module} {label}"), encoding="utf-8")
        created.append(file_path)

    for pattern in SUBFOLDERS:
        folder_path = module_dir / pattern.format(module=module)
        folder_path.mkdir(parents=True, exist_ok=True)
        created.append(folder_path)

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate canonical M01-style Quarto course modules."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Course project root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=DEFAULT_START_MODULE,
        help="First module number to create. Defaults to 1.",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=DEFAULT_END_MODULE,
        help="Last module number to create. Defaults to 7.",
    )
    parser.add_argument(
        "--include-module-zero",
        action="store_true",
        help="Also create M00 for prerequisite or orientation content.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing scaffold files. Existing folders are preserved.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()

    if not root.exists():
        raise SystemExit(f"Project root does not exist: {root}")
    if not root.is_dir():
        raise SystemExit(f"Project root is not a directory: {root}")
    if args.end < args.start:
        raise SystemExit("--end must be greater than or equal to --start")

    module_numbers = list(range(args.start, args.end + 1))
    if args.include_module_zero and 0 not in module_numbers:
        module_numbers.insert(0, 0)

    created_count = 0
    for number in module_numbers:
        created_count += len(generate_module(root, number, args.overwrite))

    print(f"Generated or verified {len(module_numbers)} module folders in {root}.")
    print(f"Created or updated {created_count} files/folders.")


if __name__ == "__main__":
    main()
