"""Populate YAML front matter in generated Quarto files from a CSV outline."""

from __future__ import annotations

import argparse
import csv
import os
from datetime import date
from pathlib import Path


def optional_ai_summary(title: str, description: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return description

    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        response = client.responses.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
            input=(
                "Write a concise one-sentence course page description.\n"
                f"Title: {title}\n"
                f"Description: {description}"
            ),
        )
        return response.output_text.strip()
    except Exception:
        return description


def yaml_block(title: str, subtitle: str, description: str) -> str:
    summary = optional_ai_summary(title, description)
    return "\n".join(
        [
            "---",
            f'title: "{title}"',
            f'subtitle: "{subtitle}"',
            "number-sections: true",
            f'date-modified: "{date.today().isoformat()}"',
            f'description: "{summary}"',
            "---",
            "",
        ]
    )


def update_file(path: Path, front_matter: str, overwrite_body: bool) -> None:
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    body = ""

    if existing.startswith("---") and not overwrite_body:
        parts = existing.split("---", 2)
        if len(parts) == 3:
            body = parts[2].lstrip()
    elif not overwrite_body:
        body = existing

    if not body:
        body = "# Notes\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(front_matter + body, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Populate Quarto YAML metadata from a CSV outline."
    )
    parser.add_argument("outline", help="CSV with Source File, Title, Description.")
    parser.add_argument(
        "--root",
        default=".",
        help="Course project root. Defaults to the current directory.",
    )
    parser.add_argument(
        "--overwrite-body",
        action="store_true",
        help="Replace page body with a generic placeholder.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()
    outline_path = Path(args.outline).expanduser().resolve()

    with outline_path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            source_file = row.get("Source File", "").strip()
            if not source_file:
                continue

            title = row.get("Title", "").strip() or "Course Page"
            subtitle = row.get("Lecture", "").strip()
            description = row.get("Description", "").strip()
            target = root / source_file
            update_file(
                target,
                yaml_block(title, subtitle, description),
                overwrite_body=args.overwrite_body,
            )
            print(f"Updated metadata: {target}")


if __name__ == "__main__":
    main()
