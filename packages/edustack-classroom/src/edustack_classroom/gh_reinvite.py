import csv
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List

def run_cmd(cmd: List[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"Command failed:\n  {' '.join(cmd)}\n{p.stderr.strip()}")
    return p.stdout

def try_run_cmd(cmd: List[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        return ""
    return p.stdout

def revoke_and_reinvite_collaborators(
    org: str,
    prefix: str,
    permission: str = "write",
    limit: int = 1000,
    out_csv: str | Path = "reinvites.csv",
    dry_run: bool = False,
):
    """Revoke & re-invite pending repository invitations for repositories matching a prefix."""
    # Normalize "write" to GH API accepted value "push"
    perm = "push" if permission == "write" else permission

    # Ensure gh exists and auth works
    if not try_run_cmd(["gh", "--version"]):
        raise RuntimeError("GitHub CLI ('gh') not found. Please install the GitHub CLI first.")

    auth_status = try_run_cmd(["gh", "auth", "status"])
    if not auth_status:
        raise RuntimeError("Not authenticated in GitHub CLI. Run 'gh auth login' to authenticate.")

    print(f"Listing repositories in organization '{org}' matching prefix '{prefix}'...")
    repos_json = run_cmd(["gh", "repo", "list", org, "--limit", str(limit), "--json", "name"])
    repos = [r["name"] for r in json.loads(repos_json)]
    matched = [name for name in repos if name.startswith(prefix)]

    print(f"Found {len(matched)} matching repositories out of {len(repos)} total.")
    ts = lambda: datetime.now(timezone.utc).isoformat()

    out_csv = Path(out_csv)
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["timestamp", "org", "repo", "user", "invite_id", "revoke", "reinvite", "note"])

        for repo in matched:
            full = f"{org}/{repo}"
            invites_out = try_run_cmd(["gh", "api", f"repos/{full}/invitations"])
            if not invites_out.strip() or invites_out.strip() == "[]":
                continue

            invites = json.loads(invites_out)
            for inv in invites:
                invite_id = inv.get("id")
                user = (inv.get("invitee") or {}).get("login")
                if not invite_id or not user:
                    continue

                revoke_ok = reinvite_ok = "SKIP"
                note = ""

                if dry_run:
                    note = "dry-run"
                    print(f"[Dry-run] Would revoke invite {invite_id} and re-invite {user} to {full} with permission '{permission}'")
                else:
                    print(f"Processing invite {invite_id} for user {user} in repository {full}...")
                    # Revoke
                    revoke_ok = "OK"
                    p = subprocess.run(["gh", "api", f"repos/{full}/invitations/{invite_id}", "-X", "DELETE", "--silent"],
                                       capture_output=True, text=True)
                    if p.returncode != 0:
                        revoke_ok = "FAIL"
                        note += f"revoke_error={p.stderr.strip()} "

                    # Re-invite
                    reinvite_ok = "OK"
                    p2 = subprocess.run(
                        ["gh", "api", f"repos/{full}/collaborators/{user}", "-X", "PUT", "-f", f"permission={perm}", "--silent"],
                        capture_output=True, text=True
                    )
                    if p2.returncode != 0:
                        reinvite_ok = "FAIL"
                        note += f"reinvite_error={p2.stderr.strip()} "

                w.writerow([ts(), org, repo, user, invite_id, revoke_ok, reinvite_ok, note.strip()])

    print(f"Done. Wrote invitation log to: {out_csv}")
