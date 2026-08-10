from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

from edustack_schedule.installer import install_wrappers
from edustack_schedule.workbook import (
    GeneratedWorkbookConfig,
    build_generated_schedule_workbook,
)


def _load_config(path: Path):
    spec = importlib.util.spec_from_file_location("edustack_course_schedule_config", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load config from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def generate(args: argparse.Namespace) -> int:
    course_root = Path(args.course_root).resolve()
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = course_root / config_path
    config_module = _load_config(config_path)

    configured_source_workbook = getattr(
        config_module,
        "source_workbook",
        "data/Course-Schedule.xlsx",
    )
    source_workbook = Path(args.source_workbook or configured_source_workbook)
    if not source_workbook.is_absolute():
        source_workbook = course_root / source_workbook

    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = course_root / data_dir

    output_path = Path(args.output_path) if args.output_path else None
    if output_path and not output_path.is_absolute():
        output_path = course_root / output_path

    workbook_config = GeneratedWorkbookConfig(
        section_configs_by_semester=config_module.section_configs_by_semester,
        source_workbook=source_workbook,
        data_dir=data_dir,
        output_path=output_path,
    )

    output = build_generated_schedule_workbook(
        config=workbook_config,
        semester=args.semester if args.semester is not None else getattr(config_module, "semester", None),
        year=args.year if args.year is not None else getattr(config_module, "year", None),
        sections=args.sections,
    )
    print(output)
    return 0


def install(args: argparse.Namespace) -> int:
    results = install_wrappers(
        args.course_root,
        force=args.force,
        dry_run=args.dry_run,
        include_config=args.include_config,
    )
    for result in results:
        print(f"{result.action}: {result.path}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="edustack-schedule",
        description="Generate BU course schedules and install course compatibility wrappers.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    generate_parser = subcommands.add_parser("generate", help="Build a generated schedule workbook.")
    generate_parser.add_argument("--course-root", default=".", help="Course repository root.")
    generate_parser.add_argument("--config", default="schedules/config.py", help="Python config path.")
    generate_parser.add_argument("--source-workbook")
    generate_parser.add_argument("--data-dir", default="data")
    generate_parser.add_argument("--output-path")
    generate_parser.add_argument("--semester")
    generate_parser.add_argument("--year", type=int)
    generate_parser.add_argument("--sections", nargs="*")
    generate_parser.set_defaults(func=generate)

    install_parser = subcommands.add_parser("install", help="Install course-local wrapper files.")
    install_parser.add_argument("course_root")
    install_parser.add_argument("--force", action="store_true", help="Overwrite existing wrapper files.")
    install_parser.add_argument("--dry-run", action="store_true", help="Print actions without writing files.")
    install_parser.add_argument(
        "--include-config",
        action="store_true",
        help="Also create schedules/config.py if missing.",
    )
    install_parser.set_defaults(func=install)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
