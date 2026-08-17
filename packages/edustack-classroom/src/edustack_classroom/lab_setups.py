import os
from github import Github, Auth
from dotenv import load_dotenv

def create_lab_repositories(
    org_name: str,
    repo_prefix: str = "Lab",
    start_num: int = 1,
    end_num: int = 12,
    private: bool = True,
    is_template: bool = True,
    token: str | None = None,
):
    """Create template repositories for labs in a GitHub Organization."""
    load_dotenv()
    
    github_token = token or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN") or os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise ValueError("GitHub token not found. Set GITHUB_PERSONAL_ACCESS_TOKEN in env or pass it.")

    auth = Auth.Token(github_token)
    g = Github(auth=auth)

    try:
        org = g.get_organization(org_name)
    except Exception as e:
        raise RuntimeError(f"Could not retrieve GitHub Organization '{org_name}': {e}")

    # Generate repository names (e.g., 'Lab 01' to 'Lab 12')
    repo_names = [f"{repo_prefix} {str(i).zfill(2)}" for i in range(start_num, end_num + 1)]

    for repo_name in repo_names:
        print(f"Creating repository '{repo_name}' in org '{org_name}'...")
        try:
            repo = org.create_repo(
                name=repo_name,
                description=f"Template repository for {repo_name}",
                private=private,
                has_issues=True,
                has_wiki=False,
                has_downloads=False
            )
            
            # Note: PyGithub doesn't have a direct parameter `is_template` in org.create_repo for some versions,
            # so we update it via a patch/edit call if needed.
            if is_template:
                repo.edit(is_template=True)
                
            print(f"Successfully created '{repo_name}' (private={private}, template={is_template})")
        except Exception as e:
            print(f"Error creating repository '{repo_name}': {e}")
