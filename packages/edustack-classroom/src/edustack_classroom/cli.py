import click
from edustack_classroom.announcements import generate_announcements
from edustack_classroom.lab_setups import create_lab_repositories
from edustack_classroom.gh_reinvite import revoke_and_reinvite_collaborators
from edustack_classroom.gh_repocreate import create_classroom_repositories_and_assignments

@click.group()
def main():
    """GitHub and Classroom organization automation tools for EduStack."""
    pass

@main.command("announcements")
@click.option("--excel-file", default="data/Course-Schedule.xlsx", help="Path to the Excel course schedule workbook.")
@click.option("--output-dir", default="Announcements", help="Output folder where docx files will be written.")
@click.option("--semester", help="Course semester (e.g. Fall, Spring, Summer). Resolved automatically if not provided.")
@click.option("--year", type=int, help="Course year (e.g. 2026). Resolved automatically if not provided.")
def cmd_announcements(excel_file, output_dir, semester, year):
    """Generate weekly announcements in Word (.docx) format."""
    try:
        generate_announcements(
            excel_file=excel_file,
            output_dir=output_dir,
            semester=semester,
            year=year
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@main.command("create-labs")
@click.option("--org", required=True, help="GitHub organization name.")
@click.option("--repo-prefix", default="Lab", help="Prefix for repository names.")
@click.option("--start-num", type=int, default=1, help="Starting number for repositories.")
@click.option("--end-num", type=int, default=12, help="Ending number for repositories.")
@click.option("--public", is_flag=True, default=False, help="Make repositories public (default: private).")
@click.option("--no-template", is_flag=True, default=False, help="Do not flag repositories as templates.")
@click.option("--token", help="GitHub token (defaults to GITHUB_PERSONAL_ACCESS_TOKEN or GITHUB_TOKEN environment variable).")
def cmd_create_labs(org, repo_prefix, start_num, end_num, public, no_template, token):
    """Batch create lab repositories in a GitHub Organization."""
    try:
        create_lab_repositories(
            org_name=org,
            repo_prefix=repo_prefix,
            start_num=start_num,
            end_num=end_num,
            private=not public,
            is_template=not no_template,
            token=token
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@main.command("reinvite")
@click.option("--org", required=True, help="GitHub Organization (e.g. ad688-SP26).")
@click.option("--prefix", required=True, help="Repo name prefix to match (e.g. a02-sp26-).")
@click.option("--permission", default="write", help="Collaborator permission (default: write).")
@click.option("--limit", type=int, default=1000, help="Max repos to inspect.")
@click.option("--out-csv", default="reinvites.csv", help="Log output CSV file.")
@click.option("--dry-run", is_flag=True, default=False, help="Print actions but do not execute them.")
def cmd_reinvite(org, prefix, permission, limit, out_csv, dry_run):
    """Revoke & re-invite pending repository collaborators."""
    try:
        revoke_and_reinvite_collaborators(
            org=org,
            prefix=prefix,
            permission=permission,
            limit=limit,
            out_csv=out_csv,
            dry_run=dry_run
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

@main.command("setup-classroom")
@click.option("--classroom-org", required=True, help="GitHub Org where student repos live.")
@click.option("--template-org", required=True, help="GitHub Org where template repos live.")
@click.option("--classroom-name", required=True, help="GitHub Classroom name.")
@click.option("--group-set", help="Classroom Group Set name (required if there are group assignments).")
@click.option("--config-file", help="Path to JSON configuration file for labs.")
@click.option("--dry-run", is_flag=True, default=False, help="Print commands without executing them.")
def cmd_setup_classroom(classroom_org, template_org, classroom_name, group_set, config_file, dry_run):
    """Create starter repos and Classroom assignments."""
    try:
        create_classroom_repositories_and_assignments(
            classroom_org=classroom_org,
            template_org=template_org,
            classroom_name=classroom_name,
            group_set=group_set,
            config_file=config_file,
            dry_run=dry_run
        )
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        raise click.Abort()

if __name__ == "__main__":
    main()
