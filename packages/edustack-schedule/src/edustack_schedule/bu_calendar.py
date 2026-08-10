from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BU_SEMESTER_CALENDAR_URL = "https://www.bu.edu/reg/calendars/semester/"


def _normalize_date_raw(date_raw: str) -> str:
    date_raw = re.sub(r"\s+", " ", date_raw).strip()

    if "–" in date_raw:
        start, end = [part.strip() for part in date_raw.split("–", 1)]
        start = re.sub(r",\s*\d{4}$", "", start).strip()
        end = re.sub(r",\s*\d{4}$", "", end).strip()

        start_month = start.split()[0]
        if re.match(r"^\d{1,2}$", end):
            end = f"{start_month} {end}"

        return f"{start} – {end}"

    return re.sub(r",\s*\d{4}$", "", date_raw).strip()


def scrape_bu_calendar(url: str = BU_SEMESTER_CALENDAR_URL) -> pd.DataFrame:
    """Scrape BU's semester calendar into term/date/event rows."""

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    rows: list[dict[str, str]] = []

    for container in soup.select("div.bu_collapsible_container"):
        heading = container.find("h3")
        if not heading:
            continue

        term = heading.get_text(" ", strip=True)
        if term == "Past Semester Dates:":
            continue

        section = container.find("div", class_="bu_collapsible_section")
        if not section:
            continue

        for tr in section.select("table tr"):
            cells = tr.find_all(["th", "td"], recursive=False)
            if len(cells) != 2:
                continue

            rows.append(
                {
                    "term": term,
                    "date_raw": _normalize_date_raw(cells[0].get_text(" ", strip=True)),
                    "event": cells[1].get_text(" ", strip=True),
                }
            )

    return pd.DataFrame(rows)


def calendar_csv(season: str, year: int, data_dir: str | Path = "data") -> Path:
    return Path(data_dir) / f"{season.lower()}_calendar_{year}.csv"


def load_calendar(
    season: str,
    year: int,
    *,
    data_dir: str | Path = "data",
    refresh: bool = False,
) -> pd.DataFrame:
    """Load a cached BU calendar, scraping and caching if needed."""

    csv_path = calendar_csv(season, year, data_dir=data_dir)

    if csv_path.exists() and not refresh:
        return pd.read_csv(csv_path)

    df = scrape_bu_calendar()
    df = df[df["term"].str.contains(f"{season} {year}", case=False, na=False)]

    if df.empty:
        raise RuntimeError(f"No BU calendar rows found for {season} {year}.")

    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path, index=False)
    return df


def parse_range(date_raw: str, year: int) -> tuple[datetime, datetime]:
    """Parse a BU calendar range such as `March 7 – March 15`."""

    start, end = re.split(r"\s*[–-]\s*", str(date_raw), maxsplit=1)
    if re.match(r"^\d{1,2}$", end.strip()):
        end = f"{start.strip().split()[0]} {end.strip()}"
    return (
        datetime.strptime(f"{start.strip()} {year}", "%B %d %Y"),
        datetime.strptime(f"{end.strip()} {year}", "%B %d %Y"),
    )


def parse_single_date(date_raw: str, year: int) -> datetime:
    return datetime.strptime(f"{str(date_raw).strip()} {year}", "%B %d %Y")
