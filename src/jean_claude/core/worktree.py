# ABOUTME: Git worktree operations for isolated workflow execution
# ABOUTME: Creates and manages worktrees in trees/{workflow_id}/ for parallel work

"""Git worktree operations for isolated execution."""

import subprocess
from pathlib import Path
from typing import Optional


class WorktreeManager:
    """Manages git worktrees for isolated workflow execution."""

    def __init__(self, project_root: Path) -> None:
        """Initialize the worktree manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root
        self.trees_dir = project_root / "trees"

    def create(
        self,
        workflow_id: str,
        branch_name: Optional[str] = None,
    ) -> Path:
        """Create a new worktree for a workflow.

        Args:
            workflow_id: Unique ID for the workflow
            branch_name: Optional branch name (creates new branch if provided)

        Returns:
            Path to the created worktree
        """
        worktree_path = self.trees_dir / workflow_id
        self.trees_dir.mkdir(parents=True, exist_ok=True)

        cmd = ["git", "worktree", "add"]
        if branch_name:
            cmd.extend(["-b", branch_name])
        cmd.append(str(worktree_path))

        subprocess.run(cmd, cwd=self.project_root, check=True, capture_output=True)
        return worktree_path

    def remove(self, workflow_id: str, force: bool = False) -> None:
        """Remove a worktree.

        Args:
            workflow_id: ID of the workflow whose worktree to remove
            force: Force removal even if there are changes
        """
        worktree_path = self.trees_dir / workflow_id

        cmd = ["git", "worktree", "remove"]
        if force:
            cmd.append("--force")
        cmd.append(str(worktree_path))

        subprocess.run(cmd, cwd=self.project_root, check=True, capture_output=True)

    def list_worktrees(self) -> list[Path]:
        """List all active worktrees.

        Returns:
            List of worktree paths
        """
        if not self.trees_dir.exists():
            return []
        return [p for p in self.trees_dir.iterdir() if p.is_dir()]

    def exists(self, workflow_id: str) -> bool:
        """Check if a worktree exists.

        Args:
            workflow_id: ID to check

        Returns:
            True if worktree exists
        """
        return (self.trees_dir / workflow_id).exists()
