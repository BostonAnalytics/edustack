# Designing a Course With Quarto

This repository contains a Quarto book for professors, instructional designers,
and academic technologists who want to build maintainable course materials with
Quarto, GitHub, GitHub Classroom, and Blackboard Ultra.

The book is designed as a practical course-building workflow rather than a
general Quarto reference. It explains the tools, then shows how to turn a course
outline into a repeatable structure of lecture notes, presentations, labs,
assignments, projects, participation activities, schedules, and Blackboard-ready
HTML.

## Key Workflows

- Follow the professor quickstart path.
- Install and verify the authoring toolchain.
- Set up Git and GitHub for course version control.
- Build a Quarto course microsite.
- Use a feeder workbook to organize course structure.
- Generate canonical `M01_*` module folders and files.
- Prepare materials for GitHub Classroom and Blackboard Ultra.
- Use AI-assisted scripts to reduce repetitive course production work.
- Complete a capstone mini-course modeled after AD688.

## Module Naming Convention

Course modules use a two-digit folder and file prefix:

```text
M01/
  M01_A.qmd
  M01_LN1.qmd
  M01_LN2.qmd
  M01_P1.qmd
  M01_P2.qmd
  M01_Proj.qmd
  M01_Lab1.qmd
  M01_Lab2.qmd
  M01_Participation1.qmd
  M01_Participation2.qmd
```

Use `scripts/generate_modules.py` to create this structure and
`scripts/validate_course_structure.py` to confirm it remains consistent.

## Render the Book

```bash
quarto render
```

The rendered book is written to `_book/`.
