"""ABOUTME: Core workflow operations for ADW including issue classification, planning, and implementation.
ABOUTME: Provides high-level workflow orchestration functions used by ADW scripts."""

import logging
import os
import json
from typing import Tuple, Optional
from .data_types import GitHubIssue, AgentTemplateRequest, AgentPromptResponse
from .agent import execute_template
from .git_ops import get_repo_url, extract_repo_path
from .state import ADWState
from .utils import parse_json


# Agent name constants
AGENT_PLANNER = "sdlc_planner"
AGENT_IMPLEMENTOR = "sdlc_implementor"
AGENT_CLASSIFIER = "issue_classifier"
AGENT_BRANCH_GENERATOR = "branch_generator"
AGENT_PR_CREATOR = "pr_creator"


def fetch_issue_unified(
    issue_identifier: str, logger: logging.Logger
) -> Tuple[Optional[GitHubIssue], Optional[str]]:
    """Fetch issue from GitHub or Beads based on identifier format.

    Args:
        issue_identifier: GitHub issue number or Beads issue ID
        logger: Logger instance

    Returns:
        Tuple of (issue, error_message)
    """
    from .beads_integration import is_beads_issue, fetch_beads_issue

    # Check if it's a beads issue
    if is_beads_issue(issue_identifier):
        logger.info(f"Fetching beads issue: {issue_identifier}")
        return fetch_beads_issue(issue_identifier)
    else:
        # GitHub issue - would need GitHub API integration
        logger.error("GitHub issue fetching not yet implemented")
        return None, "GitHub issue fetching not implemented"


def classify_issue(
    issue: GitHubIssue, adw_id: str, logger: logging.Logger
) -> Tuple[Optional[str], Optional[str]]:
    """Classify GitHub issue and return appropriate slash command.

    Args:
        issue: The issue to classify
        adw_id: ADW ID for tracking
        logger: Logger instance

    Returns:
        Tuple of (command, error_message) where command is /chore, /bug, or /feature
    """
    # Use the classify_issue slash command template with minimal payload
    minimal_issue_json = json.dumps({
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
    })

    request = AgentTemplateRequest(
        agent_name=AGENT_CLASSIFIER,
        slash_command="/classify_issue",
        args=[minimal_issue_json],
        adw_id=adw_id,
    )

    logger.debug(f"Classifying issue: {issue.title}")

    response = execute_template(request)

    if not response.success:
        return None, response.output

    # Extract the classification from the response
    output = response.output.strip()

    # Look for the classification pattern in the output
    import re
    classification_match = re.search(r"(/chore|/bug|/feature|0)", output)

    if classification_match:
        issue_command = classification_match.group(1)
    else:
        issue_command = output

    if issue_command == "0":
        return None, f"No command selected: {response.output}"

    if issue_command not in ["/chore", "/bug", "/feature"]:
        return None, f"Invalid command selected: {response.output}"

    return issue_command, None


def build_plan(
    issue: GitHubIssue,
    command: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Build implementation plan for the issue using the specified command.

    Args:
        issue: The issue to plan for
        command: Slash command to use (/chore, /bug, or /feature)
        adw_id: ADW ID for tracking
        logger: Logger instance
        working_dir: Working directory for execution

    Returns:
        AgentPromptResponse with plan creation result
    """
    # Use minimal payload
    minimal_issue_json = json.dumps({
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
    })

    issue_plan_template_request = AgentTemplateRequest(
        agent_name=AGENT_PLANNER,
        slash_command=command,
        args=[str(issue.number), adw_id, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(f"Creating plan for issue {issue.number}")

    issue_plan_response = execute_template(issue_plan_template_request)

    return issue_plan_response


def implement_plan(
    plan_file: str,
    adw_id: str,
    logger: logging.Logger,
    agent_name: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> AgentPromptResponse:
    """Implement the plan using the /implement command.

    Args:
        plan_file: Path to the plan file
        adw_id: ADW ID for tracking
        logger: Logger instance
        agent_name: Agent name to use (default: AGENT_IMPLEMENTOR)
        working_dir: Working directory for execution

    Returns:
        AgentPromptResponse with implementation result
    """
    implementor_name = agent_name or AGENT_IMPLEMENTOR

    implement_template_request = AgentTemplateRequest(
        agent_name=implementor_name,
        slash_command="/implement",
        args=[plan_file],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug(f"Implementing plan: {plan_file}")

    implement_response = execute_template(implement_template_request)

    return implement_response


def generate_branch_name(
    issue: GitHubIssue,
    issue_class: str,
    adw_id: str,
    logger: logging.Logger,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate a git branch name for the issue.

    Args:
        issue: The issue to generate branch name for
        issue_class: Issue class (/chore, /bug, /feature)
        adw_id: ADW ID for tracking
        logger: Logger instance

    Returns:
        Tuple of (branch_name, error_message)
    """
    # Remove the leading slash from issue_class for the branch name
    issue_type = issue_class.replace("/", "")

    # Use minimal payload
    minimal_issue_json = json.dumps({
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
    })

    request = AgentTemplateRequest(
        agent_name=AGENT_BRANCH_GENERATOR,
        slash_command="/generate_branch_name",
        args=[issue_type, adw_id, minimal_issue_json],
        adw_id=adw_id,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    branch_name = response.output.strip()
    logger.info(f"Generated branch name: {branch_name}")
    return branch_name, None


def create_pull_request(
    branch_name: str,
    issue: Optional[GitHubIssue],
    state: ADWState,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a pull request for the implemented changes.

    Args:
        branch_name: Branch name for the PR
        issue: The issue (if available)
        state: ADW state
        logger: Logger instance
        working_dir: Working directory

    Returns:
        Tuple of (pr_url, error_message)
    """
    # Get plan file from state (may be None for test runs)
    plan_file = state.get("plan_file") or "No plan file (test run)"
    adw_id = state.get("adw_id")

    # If we don't have issue data, try to construct minimal data
    if not issue:
        issue_data = state.get("issue", {})
        issue_json = json.dumps(issue_data) if issue_data else "{}"
    elif isinstance(issue, dict):
        issue_json = json.dumps(issue, default=str)
    else:
        # Use minimal payload
        issue_json = json.dumps({
            "number": issue.number,
            "title": issue.title,
            "body": issue.body,
        })

    request = AgentTemplateRequest(
        agent_name=AGENT_PR_CREATOR,
        slash_command="/pull_request",
        args=[branch_name, issue_json, plan_file, adw_id],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    pr_url = response.output.strip()
    logger.info(f"Created pull request: {pr_url}")
    return pr_url, None


def create_commit(
    agent_name: str,
    issue: GitHubIssue,
    issue_class: str,
    adw_id: str,
    logger: logging.Logger,
    working_dir: str,
) -> Tuple[Optional[str], Optional[str]]:
    """Create a git commit with a properly formatted message.

    Args:
        agent_name: Agent name for tracking
        issue: The issue
        issue_class: Issue class (/chore, /bug, /feature)
        adw_id: ADW ID for tracking
        logger: Logger instance
        working_dir: Working directory

    Returns:
        Tuple of (commit_message, error_message)
    """
    # Remove the leading slash from issue_class
    issue_type = issue_class.replace("/", "")

    # Create unique committer agent name by suffixing '_committer'
    unique_agent_name = f"{agent_name}_committer"

    # Use minimal payload
    minimal_issue_json = json.dumps({
        "number": issue.number,
        "title": issue.title,
        "body": issue.body,
    })

    request = AgentTemplateRequest(
        agent_name=unique_agent_name,
        slash_command="/commit",
        args=[agent_name, issue_type, minimal_issue_json],
        adw_id=adw_id,
        working_dir=working_dir,
    )

    response = execute_template(request)

    if not response.success:
        return None, response.output

    commit_message = response.output.strip()
    logger.info(f"Created commit message: {commit_message}")
    return commit_message, None


def create_and_implement_patch(
    adw_id: str,
    review_change_request: str,
    logger: logging.Logger,
    agent_name_planner: str,
    agent_name_implementor: str,
    spec_path: Optional[str] = None,
    issue_screenshots: Optional[str] = None,
    working_dir: Optional[str] = None,
) -> Tuple[Optional[str], AgentPromptResponse]:
    """Create a patch plan and implement it.

    Args:
        adw_id: ADW ID for tracking
        review_change_request: The review change request
        logger: Logger instance
        agent_name_planner: Planner agent name
        agent_name_implementor: Implementor agent name
        spec_path: Optional path to spec file
        issue_screenshots: Optional screenshots
        working_dir: Working directory

    Returns:
        Tuple of (patch_file_path, implement_response)
    """
    # Create patch plan using /patch command
    args = [adw_id, review_change_request]

    # Add optional arguments in the correct order
    if spec_path:
        args.append(spec_path)
    else:
        args.append("")  # Empty string for optional spec_path

    args.append(agent_name_planner)

    if issue_screenshots:
        args.append(issue_screenshots)

    request = AgentTemplateRequest(
        agent_name=agent_name_planner,
        slash_command="/patch",
        args=args,
        adw_id=adw_id,
        working_dir=working_dir,
    )

    logger.debug("Creating patch plan")

    response = execute_template(request)

    if not response.success:
        logger.error(f"Error creating patch plan: {response.output}")
        return None, AgentPromptResponse(
            output=f"Failed to create patch plan: {response.output}", success=False
        )

    # Extract the patch plan file path from the response
    patch_file_path = response.output.strip()

    # Validate that it looks like a file path
    if "specs/patch/" not in patch_file_path or not patch_file_path.endswith(".md"):
        logger.error(f"Invalid patch plan path returned: {patch_file_path}")
        return None, AgentPromptResponse(
            output=f"Invalid patch plan path: {patch_file_path}", success=False
        )

    logger.info(f"Created patch plan: {patch_file_path}")

    # Now implement the patch plan using the provided implementor agent name
    implement_response = implement_plan(
        patch_file_path, adw_id, logger, agent_name_implementor, working_dir=working_dir
    )

    return patch_file_path, implement_response


def find_spec_file(state: ADWState, logger: logging.Logger) -> Optional[str]:
    """Find the spec file from state or by examining git diff.

    For isolated workflows, automatically uses worktree_path from state.

    Args:
        state: ADW state
        logger: Logger instance

    Returns:
        Path to spec file if found, None otherwise
    """
    import subprocess
    import glob

    # Get worktree path if in isolated workflow
    worktree_path = state.get("worktree_path")

    # Check if spec file is already in state (from plan phase)
    spec_file = state.get("plan_file")
    if spec_file:
        # If worktree_path exists and spec_file is relative, make it absolute
        if worktree_path and not os.path.isabs(spec_file):
            spec_file = os.path.join(worktree_path, spec_file)

        if os.path.exists(spec_file):
            logger.info(f"Using spec file from state: {spec_file}")
            return spec_file

    # Otherwise, try to find it from git diff
    logger.info("Looking for spec file in git diff")
    result = subprocess.run(
        ["git", "diff", "origin/main", "--name-only"],
        capture_output=True,
        text=True,
        cwd=worktree_path,
    )

    if result.returncode == 0:
        files = result.stdout.strip().split("\n")
        spec_files = [f for f in files if f.startswith("specs/") and f.endswith(".md")]

        if spec_files:
            spec_file = spec_files[0]
            if worktree_path:
                spec_file = os.path.join(worktree_path, spec_file)
            logger.info(f"Found spec file: {spec_file}")
            return spec_file

    # If still not found, try to derive from branch name
    branch_name = state.get("branch_name")
    if branch_name:
        import re
        match = re.search(r"issue-(\d+)", branch_name)
        if match:
            issue_num = match.group(1)
            adw_id = state.get("adw_id")

            # Look for spec files matching the pattern
            search_dir = worktree_path if worktree_path else os.getcwd()
            pattern = os.path.join(
                search_dir, f"specs/issue-{issue_num}-adw-{adw_id}*.md"
            )
            spec_files = glob.glob(pattern)

            if spec_files:
                spec_file = spec_files[0]
                logger.info(f"Found spec file by pattern: {spec_file}")
                return spec_file

    logger.warning("No spec file found")
    return None
