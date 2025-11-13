# Deployment Guide

## Architecture Overview

```
Jira Issue → Webhook → GitHub Actions (custom-agent) → Clone cms-project → Make Changes → Create PR
```

### Repositories

1. **custom-agent** (this repo) - Multi-agent implementation
   - Contains agent code, orchestrator, integrations
   - Hosts GitHub Actions workflow
   - Triggered by Jira webhooks

2. **cms-project** (target repo) - Where code changes are made
   - Cloned by the workflow
   - Agent makes changes here
   - PRs created against this repo

## Step-by-Step Deployment

### 1. Push custom-agent to GitHub

```bash
cd /Users/karthis/Public/Projects/custom-multiagent

# Initialize git if not already done
git init
git add .
git commit -m "Initial commit: Multi-agent system"

# Add remote (replace with your repo URL)
git remote add origin https://github.com/Karthi-Knackforge/custom-agent.git
git branch -M main
git push -u origin main
```

### 2. Configure GitHub Secrets

Go to: https://github.com/Karthi-Knackforge/custom-agent/settings/secrets/actions

Add these secrets:

| Secret Name | Value |
|-------------|-------|
| `ANTHROPIC_API_KEY` | Your Claude API key |
| `JIRA_BASE_URL` | `https://knackforge-team-xpf6pae3.atlassian.net` |
| `JIRA_EMAIL` | `karthi.s@knackforge.com` |
| `JIRA_TOKEN` | Your Jira API token |
| `GITHUB_TOKEN` | Auto-provided (has access to cms-project) |

### 3. Set Up Jira Automation

**Go to:** Jira Project Settings → Automation → Create Rule

**Trigger:** Issue Created (or Updated/Transitioned)

**Condition (Optional):** 
- Issue type = Story/Task/Bug
- Labels contains "Auto-Copilot"

**Action:** Send web request

**Configuration:**
- **URL:** `https://api.github.com/repos/Karthi-Knackforge/custom-agent/dispatches`
- **Method:** `POST`
- **Headers:**
  ```
  Content-Type: application/json
  Accept: application/vnd.github+json
  Authorization: Bearer YOUR_GITHUB_PAT
  X-GitHub-Api-Version: 2022-11-28
  ```
- **Body:**
  ```json
  {
    "event_type": "jira-issue-created",
    "client_payload": {
      "issue_key": "{{issue.key}}",
      "issue_id": "{{issue.id}}",
      "summary": "{{issue.summary}}",
      "description": "{{issue.description}}",
      "issue_type": "{{issue.issueType.name}}",
      "priority": "{{issue.priority.name}}",
      "reporter": "{{issue.reporter.displayName}}",
      "project_key": "{{issue.project.key}}"
    }
  }
  ```

**Note:** Replace `YOUR_GITHUB_PAT` with a Personal Access Token that has `workflow` scope.

### 4. Test the Integration

#### Option A: Manual Test
```bash
curl -X POST \
  https://api.github.com/repos/Karthi-Knackforge/custom-agent/dispatches \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_PAT" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  -d '{
    "event_type": "jira-issue-created",
    "client_payload": {
      "issue_key": "CGCI-2",
      "project_key": "CGCI",
      "summary": "Test issue",
      "description": "Testing webhook"
    }
  }'
```

#### Option B: Create Jira Issue
1. Create a new issue in Jira
2. Add label "Auto-Copilot"
3. Watch for workflow run at: https://github.com/Karthi-Knackforge/custom-agent/actions

### 5. Verify Workflow Execution

1. Go to: https://github.com/Karthi-Knackforge/custom-agent/actions
2. Check the latest workflow run
3. Verify it:
   - ✅ Checks out custom-agent repo
   - ✅ Clones cms-project repo
   - ✅ Installs dependencies
   - ✅ Runs agent
   - ✅ Creates PR in cms-project

## Workflow Details

### What the Workflow Does

1. **Triggered by:** Jira webhook → repository_dispatch event
2. **Checks out:** 
   - `custom-agent` repo (agent code)
   - `cms-project` repo (target for changes)
3. **Installs:** Python dependencies from requirements.txt
4. **Runs:** `run_agent.py` with Jira issue key
5. **Agent executes:**
   - Fetches Jira issue details
   - Generates code using Claude
   - Reviews code
   - Creates branch in cms-project
   - Commits changes
   - Pushes to GitHub
   - Creates PR

### Environment Variables

The workflow sets these for the agent:

| Variable | Purpose |
|----------|---------|
| `ANTHROPIC_API_KEY` | Claude API access |
| `JIRA_BASE_URL` | Jira instance URL |
| `JIRA_EMAIL` | Jira authentication |
| `JIRA_TOKEN` | Jira API token |
| `GITHUB_TOKEN` | GitHub API access |
| `GITHUB_OWNER` | Target repo owner |
| `GITHUB_REPO` | Target repo name |

## Local Testing

Before pushing to GitHub, test locally:

```bash
# Set environment variables
export ANTHROPIC_API_KEY="your-key"
export JIRA_BASE_URL="https://knackforge-team-xpf6pae3.atlassian.net"
export JIRA_EMAIL="karthi.s@knackforge.com"
export JIRA_TOKEN="your-token"
export GITHUB_TOKEN="your-pat"
export GITHUB_OWNER="Karthi-Knackforge"
export GITHUB_REPO="cms-project"

# Run agent
cd /Users/karthis/Public/Projects/custom-multiagent
python run_agent.py \
  --jira-key CGCI-2 \
  --project cms-project \
  --project-path /path/to/local/cms-project

# Or dry run (no Git operations)
python run_agent.py \
  --jira-key CGCI-2 \
  --project cms-project \
  --project-path /path/to/local/cms-project \
  --dry-run
```

## Troubleshooting

### Workflow fails with "requirements.txt not found"
- Ensure requirements.txt exists in custom-agent repo root
- Check workflow references correct path: `custom-agent/requirements.txt`

### Agent can't access cms-project
- Verify GITHUB_TOKEN has access to cms-project (must be private repo collaborator)
- Check workflow checkout uses correct repository name

### PR creation fails
- Verify GitHub token has `workflow` scope
- Check git config in workflow (user.name, user.email)
- Ensure target branch doesn't already exist

### Jira webhook doesn't trigger workflow
- Verify webhook URL points to custom-agent repo (not cms-project)
- Check Accept header: `application/vnd.github+json`
- Test manually with curl first

## Next Steps

1. ✅ Push custom-agent to GitHub
2. ✅ Configure GitHub secrets
3. ✅ Set up Jira automation
4. ✅ Test with real Jira issue
5. Review and merge first PR
6. Iterate and improve agent prompts
