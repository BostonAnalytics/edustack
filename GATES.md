# Gates: Package Course Tools

OWNS: packages/**, pyproject.toml, uv.lock, 13_class_schedule_automation.qmd

Scope: Convert scheduling, calendar, classroom organization and automation folders to installable Python packages and verify them.

- [x] G1: edustack-schedule CLI help works
  CHECK: uv run edustack-schedule --help
  EXPECT: positional arguments:\n  {generate,install}
  EVIDENCE: |
    usage: edustack-schedule [-h] {generate,install} ...
    
    Generate BU course schedules and install course compatibility wrappers.
    
    positional arguments:
      {generate,install}
        generate          Build a generated schedule workbook.
        install           Install course-local wrapper files.

- [x] G2: edustack-classroom CLI help works
  CHECK: uv run edustack-classroom --help
  EXPECT: Commands:\n  announcements
  EVIDENCE: |
    Usage: edustack-classroom [OPTIONS] COMMAND [ARGS]...
    
      GitHub and Classroom organization automation tools for EduStack.
    
    Options:
      --help  Show this message and exit.
    
    Commands:
      announcements    Generate weekly announcements in Word (.docx) format.
      create-labs      Batch create lab repositories in a GitHub Organization.
      reinvite         Revoke & re-invite pending repository collaborators.
      setup-classroom  Create starter repos and Classroom assignments.

- [x] G3: AD688 course schedule table builds without saved calendar sheets log statement
  CHECK: uv run python -c "from schedules.course_calendar import build_course_schedule_table; build_course_schedule_table()"
  CWD: D:\Repositories\AD688-Web-Analytics
  EXPECT: Lecture
  EVIDENCE: |
       Lecture  ... On-Campus (A1)
    0     L0.1  ...     2026-09-01
    1     L0.2  ...     2026-09-01
    ...
