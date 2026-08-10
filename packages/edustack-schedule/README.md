# edustack-schedule

Reusable BU semester schedule and assignment-calendar generation extracted from
AD688 and AD698.

This package is intentionally narrower than the EduStack book. Course repos keep
their own `schedules/config.py`, source workbook, and deliverable rules; this
package owns the shared term resolution, BU calendar scraping/caching, lecture
date planning, generated workbook tables, and compatibility-wrapper installer.

Course configs can declare the course-specific workbook name:

```python
semester = "Fall"
year = 2026
source_workbook = "data/AD698-Schedule.xlsx"
```

## Local usage

```powershell
uv run --project packages/edustack-schedule edustack-schedule --help
uv run --project packages/edustack-schedule edustack-schedule install D:\Repositories\AD698-generative-ai-for-BA --dry-run
```

## Later PyPI install

```powershell
pip install edustack-schedule
```
