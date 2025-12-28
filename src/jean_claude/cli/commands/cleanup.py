# ABOUTME: CLI command for cleaning up temporary Jean Claude files
# ABOUTME: Removes old verification scripts, reports, and agent work directories

import click
from pathlib import Path
from datetime import datetime, timedelta
import shutil


@click.command()
@click.option(
    "--age",
    type=int,
    default=7,
    help="Remove files older than N days (default: 7)",
)
@click.option(
    "--all",
    "clean_all",
    is_flag=True,
    help="Remove all temporary files regardless of age",
)
@click.option(
    "--agents",
    is_flag=True,
    help="Also clean up old agent work directories",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be deleted without actually deleting",
)
def cleanup(age: int, clean_all: bool, agents: bool, dry_run: bool):
    """Clean up temporary Jean Claude files.

    Removes old verification scripts, status reports, and optionally
    agent work directories to keep your project clean.

    Examples:
        jc cleanup                    # Remove files older than 7 days
        jc cleanup --age 14           # Remove files older than 14 days
        jc cleanup --all              # Remove all temporary files
        jc cleanup --agents           # Also clean agent directories
        jc cleanup --dry-run          # Preview what would be deleted
    """
    project_root = Path.cwd()
    jc_dir = project_root / ".jc"

    if not jc_dir.exists():
        click.echo("❌ No .jc directory found. Run 'jc init' first.")
        return

    # Calculate cutoff time
    if not clean_all:
        cutoff = datetime.now() - timedelta(days=age)
        click.echo(f"🧹 Cleaning files older than {age} days...")
    else:
        cutoff = None
        click.echo("🧹 Cleaning ALL temporary files...")

    # Directories to clean
    temp_dirs = [
        jc_dir / "temp",
        jc_dir / "reports",
        jc_dir / "verification",
    ]

    if agents:
        agents_dir = project_root / "agents"
        if agents_dir.exists():
            temp_dirs.append(agents_dir)

    total_size = 0
    total_files = 0
    files_to_delete = []

    # Collect files to delete
    for temp_dir in temp_dirs:
        if not temp_dir.exists():
            continue

        for item in temp_dir.rglob("*"):
            if not item.is_file():
                continue

            # Check age if not cleaning all
            if cutoff:
                mtime = datetime.fromtimestamp(item.stat().st_mtime)
                if mtime > cutoff:
                    continue

            size = item.stat().st_size
            files_to_delete.append((item, size))
            total_size += size
            total_files += 1

    if not files_to_delete:
        click.echo("✨ No files to clean up!")
        return

    # Display summary
    click.echo(f"\n📊 Found {total_files} files ({_format_size(total_size)}):")
    for temp_dir in temp_dirs:
        if not temp_dir.exists():
            continue
        dir_files = [f for f, _ in files_to_delete if str(f).startswith(str(temp_dir))]
        if dir_files:
            click.echo(f"  • {temp_dir.relative_to(project_root)}: {len(dir_files)} files")

    if dry_run:
        click.echo("\n🔍 Dry run - no files were deleted")
        return

    # Confirm deletion
    if not clean_all:
        if not click.confirm("\nProceed with cleanup?"):
            click.echo("❌ Cleanup cancelled")
            return

    # Delete files
    deleted_count = 0
    for file_path, _ in files_to_delete:
        try:
            file_path.unlink()
            deleted_count += 1
        except Exception as e:
            click.echo(f"⚠️  Failed to delete {file_path}: {e}", err=True)

    # Remove empty directories
    for temp_dir in temp_dirs:
        if temp_dir.exists() and temp_dir != (project_root / "agents"):
            try:
                # Try to remove directory if empty
                if not any(temp_dir.iterdir()):
                    temp_dir.rmdir()
            except Exception:
                pass  # Not empty, that's fine

    click.echo(f"\n✅ Cleaned up {deleted_count} files ({_format_size(total_size)})")


def _format_size(bytes_size: int) -> str:
    """Format bytes as human-readable size."""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"
