import json
import subprocess
from pathlib import Path
from typing import Dict, Any

def create_classroom_repositories_and_assignments(
    classroom_org: str,
    template_org: str,
    classroom_name: str,
    group_set: str | None = None,
    config_file: str | Path | None = None,
    labs_config: Dict[str, Any] | None = None,
    dry_run: bool = False,
):
    """Create GitHub starter repositories from templates and set up Classroom assignments.

    Config format can be JSON/dict specifying deadlines, templates, and assignment types.
    """
    if config_file:
        with open(config_file, "r", encoding="utf-8") as f:
            labs_config = json.load(f)

    if not labs_config:
        # Provide a default configuration structure
        labs_config = {
            "labs": {
                "lab01": "lab01",
                "lab02": "lab02",
            },
            "deadlines": {
                "lab01": "2026-02-01T23:59:00Z",
                "lab02": "2026-02-08T23:59:00Z",
            },
            "assignment_types": {
                "lab01": "individual",
                "lab02": "individual",
            }
        }

    labs = labs_config.get("labs", {})
    deadlines = labs_config.get("deadlines", {})
    assignment_types = labs_config.get("assignment_types", {})

    for lab, template in labs.items():
        starter_repo = f"{lab}-starter"
        deadline = deadlines.get(lab)
        assign_type = assignment_types.get(lab, "individual")

        print(f"\n=== Processing {lab} ===")
        print(f"Template repository: {template_org}/{template}")
        print(f"Target repository:   {classroom_org}/{starter_repo}")
        print(f"Deadline:            {deadline}")
        print(f"Assignment Type:     {assign_type}")

        # 1. Create the repository
        repo_cmd = [
            "gh", "repo", "create", f"{classroom_org}/{starter_repo}",
            "--template", f"{template_org}/{template}",
            "--private",
            "--confirm"
        ]

        if dry_run:
            print(f"[Dry-run] Would execute: {' '.join(repo_cmd)}")
        else:
            try:
                print(f"Creating repository from template...")
                p = subprocess.run(repo_cmd, capture_output=True, text=True, check=True)
                print(p.stdout.strip())
            except subprocess.CalledProcessError as e:
                print(f"Error creating repository: {e.stderr.strip()}")
                continue

        # 2. Create Classroom assignment
        class_cmd = [
            "gh", "classroom", "assignment", "create",
            "--classroom", classroom_name,
            "--title", lab,
            "--starter-code-repo", f"{classroom_org}/{starter_repo}",
            "--acceptance-repo-visibility", "private",
            "--students-repo-prefix", f"{lab}-",
            "--confirm"
        ]

        if deadline:
            class_cmd.extend(["--deadline", deadline])

        if assign_type == "group":
            if not group_set:
                raise ValueError("group_set must be specified for group assignments.")
            class_cmd.extend(["--group-assignment", "--group-set", group_set])

        if dry_run:
            print(f"[Dry-run] Would execute: {' '.join(class_cmd)}")
        else:
            try:
                print(f"Creating Classroom assignment...")
                p = subprocess.run(class_cmd, capture_output=True, text=True, check=True)
                print(p.stdout.strip())
            except subprocess.CalledProcessError as e:
                print(f"Error creating Classroom assignment: {e.stderr.strip()}")

        print(f"=== Done: {lab} ===")
