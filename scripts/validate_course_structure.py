"""Validate the standard Quarto course module scaffold."""

from __future__ import annotations

import argparse
from pathlib import Path


QMD_PATTERNS = (
    "{module}_A.qmd",
    "{module}_LN1.qmd",
    "{module}_LN2.qmd",
    "{module}_P1.qmd",
    "{module}_P2.qmd",
    "{module}_Proj.qmd",
    "{module}_Lab1.qmd",
    "{module}_Lab2.qmd",
    "{module}_Participation1.qmd",
    "{module}_Participation2.qmd",
)

FOLDER_PATTERNS = (
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


def missing_items(root: Path, module_number: int) -> list[Path]:
    module = module_name(module_number)
    module_dir = root / module
    missing: list[Path] = []

    if not module_dir.is_dir():
        return [module_dir]

    for pattern in QMD_PATTERNS:
        path = module_dir / pattern.format(module=module)
        if not path.is_file():
            missing.append(path)

    for pattern in FOLDER_PATTERNS:
        path = module_dir / pattern.format(module=module)
        if not path.is_dir():
            missing.append(path)

    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate canonical M01-style Quarto course modules."
    )
    parser.add_argument(
        "root",
        nargs="?",
        default=".",
        help="Course project root. Defaults to the current directory.",
    )
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=7)
    parser.add_argument(
        "--include-module-zero",
        action="store_true",
        help="Also validate M00.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    module_numbers = list(range(args.start, args.end + 1))
    if args.include_module_zero and 0 not in module_numbers:
        module_numbers.insert(0, 0)

    all_missing: list[Path] = []
    for number in module_numbers:
        all_missing.extend(missing_items(root, number))

    if all_missing:
        print("Missing course structure items:")
        for path in all_missing:
            print(f"- {path.relative_to(root)}")
        raise SystemExit(1)

    print(f"Course structure is valid for {len(module_numbers)} module folders.")


if __name__ == "__main__":
    main()
