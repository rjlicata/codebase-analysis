import git


def download_repo(repo_url: str) -> None:
    """
    Downloads the repository from GitLab.
    """
    # Clone the repository
    if not repo_url.endswith(".git"):
        repo_url += ".git"
    repo_name = repo_url.split("/")[-1].split(".git")[0]
    # check if the repo already exists
    try:
        git.Repo(f"/workspace/tmp/{repo_name}")
    except git.exc.InvalidGitRepositoryError:
        git.Repo.clone_from(repo_url, f"/workspace/tmp/{repo_name}")
    return f"/workspace/tmp/{repo_name}"


if __name__ == "__main__":
    download_repo("https://github.com/rjlicata/json-output-inspector")
