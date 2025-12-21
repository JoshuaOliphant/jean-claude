# Install Worktree

This command sets up an isolated worktree environment for parallel ADW workflow execution.

## Parameters
- Worktree path: {0}

## Read
- .env.sample (from parent repo)

## Steps

1. **Navigate to worktree directory**
   ```bash
   cd {0}
   ```

2. **Copy environment files**
   - Copy `.env` from parent repo if it exists
   - If not, create from `.env.sample`

3. **Install Python dependencies**
   ```bash
   uv sync --all-extras
   ```

4. **Verify installation**
   ```bash
   uv run python --version
   ```

## Error Handling
- If parent .env file doesn't exist, create minimal version from .env.sample
- Ensure all paths are absolute to avoid confusion

## Report
- List all files created/modified
- Confirm dependencies installed
- Note any missing parent .env files that need user attention
