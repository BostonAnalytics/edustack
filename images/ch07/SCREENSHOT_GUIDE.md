# Chapter 7 Screenshot Guide

Drop your screenshots into this folder with the exact filenames listed below.
Quarto will automatically pick them up when you replace the placeholder callouts.

---

## Required Screenshots (19 total)

| # | Filename | What to Capture |
|---|----------|----------------|
| 1 | `bb-ultra-course-home.png` | Blackboard Ultra course home screen — course banner, left sidebar, content area |
| 2 | `bb-content-collection-browser.png` | Content collection folder hierarchy, upload button, file listing, path breadcrumbs |
| 3 | `kim-crosta-approval-example.png` | Example approval email or meeting summary (redact personal info) |
| 4 | `bb-module-list-overview.png` | All modules collapsed in course content panel — shows naming convention |
| 5 | `bb-module-expanded-wrapup.png` | Single module expanded — Wrap-Up item highlighted at top |
| 6 | `bb-highlight-page-rendered.png` | Highlight page rendered in Blackboard content viewer |
| 7 | `bb-lecture-folder-expanded.png` | Lecture folder showing Lecture Notes, Presentation, Tutorial items |
| 8 | `bb-deliverables-folder-expanded.png` | Deliverables folder with all 6 items and due dates visible |
| 9 | `bb-assignment-creation-screen.png` | Assignment creation screen — due date, submission window, rubric, HTML link |
| 10 | `bb-lab-submission-view.png` | Lab item student view — text box, file attachment, submit button |
| 11 | `bb-participation-discussion-board.png` | Discussion board with participation prompt and reply threads (blur names) |
| 12 | `bb-project-step-submission-window.png` | Project step with Opens/Due dates and point value visible |
| 13 | `quarto-project-folder-structure.png` | VS Code explorer showing full module folder tree |
| 14 | `quarto-render-terminal-output.png` | Terminal showing `quarto render` completing with "Output created: _site/" |
| 15 | `site-zip-file-explorer.png` | File Explorer showing `_site/` folder and `_site.zip` with file sizes |
| 16 | `bb-content-collection-nav.png` | Course Management → Content Collection navigation path |
| 17 | `bb-upload-site-zip-dialog.png` | Upload Files dialog with `_site.zip` selected + confirmation screen |
| 18 | `bb-add-content-menu.png` | "Add Content" menu with Content Collection Item option highlighted |
| 19 | `bb-content-collection-file-picker.png` | File picker navigating to `_site/module-01/wrap-up.html` |
| 20 | `bb-content-collection-before-after-update.png` | Content collection Date Modified before vs. after re-upload |

---

## Replacing a Placeholder

Once you have a screenshot, replace the callout block in `07_blackboard_ultra.qmd`:

**Before** (placeholder):
```
::: {.callout-note appearance="minimal"}
**Screenshot needed**: ...

\`\`\`
Replace with: images/ch07/bb-ultra-course-home.png
\`\`\`
:::
```

**After** (with your image):
```
![Blackboard Ultra course home screen.](../images/ch07/bb-ultra-course-home.png){fig-alt="Blackboard Ultra course home screen showing navigation sidebar and content area." width="90%"}
```

---

## Recommended Screenshot Settings

- **Resolution**: 1920×1080 or higher (scale to 90% width in the document)
- **Format**: PNG preferred; JPEG acceptable for photos
- **Annotations**: Use red arrows or boxes to highlight UI elements being described
- **Privacy**: Blur or redact student names, email addresses, and BU IDs before saving
- **Tool**: Snagit, Windows Snipping Tool, or macOS Screenshot app

---

## Temporary References (until your screenshots are ready)

Some placeholders link to Syracuse University's Blackboard documentation for visual context.
These are noted inline in the chapter. Remove those notes once your screenshots are in place.
