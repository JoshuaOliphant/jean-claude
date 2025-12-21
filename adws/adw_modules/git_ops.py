"""ABOUTME: Git operations module providing centralized git command wrappers for ADW workflows.
ABOUTME: Handles branch management, commits, pushes, and PR operations with error handling."""

import subprocess
import json
import logging
from typing import Optional, Tuple


def get_current_branch(cwd: Optional[str] = None) -> str:
    """Get current git branch name.

    Args:
        cwd: Working directory (default: current directory)

    Returns:
        Branch name as string
    """
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout.strip()


def get_repo_url(cwd: Optional[str] = None) -> str:
    """Get the remote repository URL.

    Args:
        cwd: Working directory (default: current directory)

    Returns:
        Repository URL as string

    Raises:
        RuntimeError: If unable to get repo URL
    """
    result = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )

    if result.returncode != 0:
        raise RuntimeError(f"Failed to get repo URL: {result.stderr}")

    return result.stdout.strip()


def extract_repo_path(repo_url: str) -> str:
    """Extract owner/repo from a git URL.

    Args:
        repo_url: Git repository URL

    Returns:
        Repository path in format "owner/repo"

    Example:
        >>> extract_repo_path("git@github.com:owner/repo.git")
        "owner/repo"
    """
    # Handle SSH format: git@github.com:owner/repo.git
    if repo_url.startswith("git@"):
        path = repo_url.split(":")[-1]
    # Handle HTTPS format: https://github.com/owner/repo.git
    else:
        path = "/".join(repo_url.split("/")[-2:])

    # Remove .git suffix if present
    return path.replace(".git", "")


def push_branch(
    branch_name: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Push current branch to remote.

    Args:
        branch_name: Name of branch to push
        cwd: Working directory (default: current directory)

    Returns:
        Tuple of (success, error_message)
    """
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def check_pr_exists(branch_name: str, cwd: Optional[str] = None) -> Optional[str]:
    """Check if PR exists for branch.

    Args:
        branch_name: Branch name to check
        cwd: Working directory (default: current directory)

    Returns:
        PR URL if exists, None otherwise
    """
    try:
        repo_url = get_repo_url(cwd)
        repo_path = extract_repo_path(repo_url)
    except Exception:
        return None

    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo_path,
            "--head",
            branch_name,
            "--json",
            "url",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode == 0:
        prs = json.loads(result.stdout)
        if prs:
            return prs[0]["url"]
    return None


def create_branch(
    branch_name: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Create and checkout a new branch.

    Args:
        branch_name: Name of branch to create
        cwd: Working directory (default: current directory)

    Returns:
        Tuple of (success, error_message)
    """
    # Create branch
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        # Check if error is because branch already exists
        if "already exists" in result.stderr:
            # Try to checkout existing branch
            result = subprocess.run(
                ["git", "checkout", branch_name],
                capture_output=True,
                text=True,
                cwd=cwd,
            )
            if result.returncode != 0:
                return False, result.stderr
            return True, None
        return False, result.stderr
    return True, None


def commit_changes(
    message: str, cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Stage all changes and commit.

    Args:
        message: Commit message
        cwd: Working directory (default: current directory)

    Returns:
        Tuple of (success, error_message)
    """
    # Check if there are changes to commit
    result = subprocess.run(
        ["git", "status", "--porcelain"], capture_output=True, text=True, cwd=cwd
    )
    if not result.stdout.strip():
        return True, None  # No changes to commit

    # Stage all changes
    result = subprocess.run(
        ["git", "add", "-A"], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, result.stderr

    # Commit
    result = subprocess.run(
        ["git", "commit", "-m", message], capture_output=True, text=True, cwd=cwd
    )
    if result.returncode != 0:
        return False, result.stderr
    return True, None


def get_pr_number(branch_name: str, cwd: Optional[str] = None) -> Optional[str]:
    """Get PR number for a branch.

    Args:
        branch_name: Branch name to check
        cwd: Working directory (default: current directory)

    Returns:
        PR number as string if exists, None otherwise
    """
    try:
        repo_url = get_repo_url(cwd)
        repo_path = extract_repo_path(repo_url)
    except Exception:
        return None

    result = subprocess.run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            repo_path,
            "--head",
            branch_name,
            "--json",
            "number",
            "--limit",
            "1",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode == 0:
        prs = json.loads(result.stdout)
        if prs:
            return str(prs[0]["number"])
    return None


def approve_pr(pr_number: str, logger: logging.Logger, cwd: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """Approve a PR.

    Args:
        pr_number: PR number to approve
        logger: Logger instance for output
        cwd: Working directory (default: current directory)

    Returns:
        Tuple of (success, error_message)
    """
    try:
        repo_url = get_repo_url(cwd)
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        return False, f"Failed to get repo info: {e}"

    result = subprocess.run(
        [
            "gh",
            "pr",
            "review",
            pr_number,
            "--repo",
            repo_path,
            "--approve",
            "--body",
            "ADW Ship workflow approved this PR after validating all state fields.",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return False, result.stderr

    logger.info(f"Approved PR #{pr_number}")
    return True, None


def merge_pr(
    pr_number: str, logger: logging.Logger, merge_method: str = "squash", cwd: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Merge a PR.

    Args:
        pr_number: PR number to merge
        logger: Logger instance for output
        merge_method: One of 'merge', 'squash', 'rebase' (default: 'squash')
        cwd: Working directory (default: current directory)

    Returns:
        Tuple of (success, error_message)
    """
    try:
        repo_url = get_repo_url(cwd)
        repo_path = extract_repo_path(repo_url)
    except Exception as e:
        return False, f"Failed to get repo info: {e}"

    # First check if PR is mergeable
    result = subprocess.run(
        [
            "gh",
            "pr",
            "view",
            pr_number,
            "--repo",
            repo_path,
            "--json",
            "mergeable,mergeStateStatus",
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        return False, f"Failed to check PR status: {result.stderr}"

    pr_status = json.loads(result.stdout)
    if pr_status.get("mergeable") != "MERGEABLE":
        return (
            False,
            f"PR is not mergeable. Status: {pr_status.get('mergeStateStatus', 'unknown')}",
        )

    # Merge the PR
    merge_cmd = [
        "gh",
        "pr",
        "merge",
        pr_number,
        "--repo",
        repo_path,
        f"--{merge_method}",
    ]

    # Add auto-merge body
    merge_cmd.extend(
        ["--body", "Merged by ADW Ship workflow after successful validation."]
    )

    result = subprocess.run(merge_cmd, capture_output=True, text=True, cwd=cwd)
    if result.returncode != 0:
        return False, result.stderr

    logger.info(f"Merged PR #{pr_number} using {merge_method} method")
    return True, None


def get_git_status(cwd: Optional[str] = None) -> str:
    """Get git status output.

    Args:
        cwd: Working directory (default: current directory)

    Returns:
        Git status output as string
    """
    result = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    return result.stdout


def has_uncommitted_changes(cwd: Optional[str] = None) -> bool:
    """Check if there are uncommitted changes.

    Args:
        cwd: Working directory (default: current directory)

    Returns:
        True if there are uncommitted changes, False otherwise
    """
    status = get_git_status(cwd)
    return bool(status.strip())
