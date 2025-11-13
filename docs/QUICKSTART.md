# Quick Start Guide

Get the multi-agent system running in 5 minutes!

## Prerequisites

- Python 3.11+
- Git
- Anthropic API key

## Step 1: Installation

```bash
# Clone the repository
git clone <repo-url>
cd custom-multiagent

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configuration

Set up your environment variables:

```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional (for GitHub Actions)
export GITHUB_TOKEN="ghp_..."
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_TOKEN="your-jira-token"
```

Or create a `.env` file:

```bash
ANTHROPIC_API_KEY=sk-ant-...
GITHUB_TOKEN=ghp_...
JIRA_BASE_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_TOKEN=your-jira-token
```

## Step 3: First Run (Dry Run)

Test the system without making any changes:

```bash
python scripts/run_agent.py \
  --jira-key TEST-123 \
  --task "Create a simple hello world function" \
  --project-path . \
  --dry-run
```

**What happens:**
- ✅ Generates code using Claude
- ✅ Runs quality checks (if configured)
- ❌ Skips Git operations (dry run)
- ❌ Skips Jira comments (dry run)

## Step 4: Real Run

Make actual changes (on a test project first!):

```bash
# Initialize a test project
mkdir test-project
cd test-project
git init
echo "# Test Project" > README.md
git add README.md
git commit -m "Initial commit"

# Create a Python marker file
touch requirements.txt

# Run the agent
cd ..
python scripts/run_agent.py \
  --jira-key TEST-123 \
  --task "Add a calculator module with add and subtract functions" \
  --project-path ./test-project
```

**What happens:**
1. Detects Python project
2. Generates code (e.g., `calculator.py`)
3. Creates feature branch (`feat/test_123`)
4. Commits changes
5. Pushes to remote
6. Creates draft PR (if GitHub token configured)

## Step 5: Review Output

Check the generated artifacts:

```bash
ls -la artifacts/
```

You'll find:
- Execution logs
- Generated prompts and responses
- Code diffs
- Quality check results

## Step 6: Configure for Your Project

Create a project config:

```bash
# config/projects/my-service.yaml
cat > config/projects/my-service.yaml << EOF
name: my-service
path: services/my-service
primary_language: python

scopes:
  include:
    - services/my-service/**
  exclude:
    - services/my-service/build/**

quality:
  test: "pytest tests/"
  lint: "ruff check ."
EOF
```

Run with project name:

```bash
python scripts/run_agent.py \
  --jira-key PROJ-456 \
  --project my-service
```

## Step 7: GitHub Actions Setup

Add secrets to your GitHub repository:

1. Go to **Settings** → **Secrets and variables** → **Actions**
2. Add these secrets:
   - `ANTHROPIC_API_KEY`
   - `JIRA_BASE_URL`
   - `JIRA_EMAIL`
   - `JIRA_TOKEN`

The workflow is already configured in `.github/workflows/agent.yml`.

Trigger manually:
1. Go to **Actions** → **Multi-Agent Code Generator**
2. Click **Run workflow**
3. Enter Jira key and other parameters

## Common Commands

**Run with max 5 iterations:**
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --max-iterations 5
```

**Custom config file:**
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --config /path/to/custom-config.yaml
```

**Help:**
```bash
python scripts/run_agent.py --help
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Could not detect project language"

Add a language marker file:
- Python: `requirements.txt` or `pyproject.toml`
- JavaScript: `package.json`
- Go: `go.mod`
- Java: `pom.xml` or `build.gradle`

### "Tests failed"

The agent will iterate and try to fix issues. If max iterations reached, it still creates a PR for manual review.

### "PR creation failed"

Check that:
1. `GITHUB_TOKEN` is set
2. Token has `contents:write` and `pull-requests:write` permissions
3. Remote repository is on GitHub

## Next Steps

- [Read the full README](../README.md)
- [Understand the architecture](ARCHITECTURE.md)
- [Create custom language plugins](PLUGINS.md)
- Configure quality checks for your project
- Customize PR templates and commit messages

## Getting Help

- Check logs in `artifacts/`
- Review test cases in `tests/`
- Open an issue with error details
- Share artifacts for debugging

## Example Output

Successful execution:

```
🤖 Starting multi-agent execution for PROJ-123
Project: my-service (python)
Max iterations: 3
Dry run: False

📋 Fetching Jira issue...
✓ Issue fetched: Add user authentication

🔄 Iteration 1/3
  ⚙️  Generating code...
  ✓ Generated 3 files

  🔍 Reviewing code...
  ✓ Review status: pass

✅ Quality checks passed!

📦 Executing Git operations...
  ✓ Branch: feat/proj_123
  ✓ Commit: a1b2c3d4
  ✓ Pull Request: https://github.com/org/repo/pull/42

💬 Posting Jira comment...
  ✓ Comment posted

✅ Multi-agent execution completed successfully!

============================================================
EXECUTION SUMMARY
============================================================
Status: SUCCESS
Iterations: 1
Final Status: pass
Branch: feat/proj_123
Commit: a1b2c3d4
Pull Request: https://github.com/org/repo/pull/42
============================================================
```

Happy coding! 🚀
