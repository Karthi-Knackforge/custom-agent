# Quick Setup Guide: Jira → GitHub Integration

This is a simplified guide to get Jira automation triggering your GitHub Actions quickly.

## Prerequisites

- ✅ GitHub repository with the multi-agent system
- ✅ Jira Cloud instance with admin access
- ✅ GitHub Personal Access Token with `repo` and `workflow` scopes

## 5-Minute Setup

### Step 1: Create GitHub PAT (2 minutes)

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)**
3. Name: `Jira Automation`
4. Select scopes:
   - ✅ `repo`
   - ✅ `workflow`
5. Click **Generate token**
6. **Copy the token** (starts with `ghp_`)

### Step 2: Configure GitHub Secrets (1 minute)

Go to your repo: `Settings → Secrets and variables → Actions`

Add these secrets (if not already added):
- `ANTHROPIC_API_KEY` - Your Claude API key
- `JIRA_BASE_URL` - Your Jira URL
- `JIRA_EMAIL` - Your Jira email
- `JIRA_TOKEN` - Your Jira API token
- `GITHUB_PAT` - The PAT you just created

### Step 3: Create Jira Automation (2 minutes)

1. Go to **Jira Settings → System → Automation**
2. Click **Create rule**
3. **Trigger**: Select "Issue created"
4. Click **New component → Action → Send web request**
5. Configure:

**URL:**
```
https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches
```
Example: `https://api.github.com/repos/Karthi-Knackforge/cms-project/dispatches`

**HTTP Method:** `POST`

**Body:**
```json
{
  "event_type": "jira-issue-created",
  "client_payload": {
    "issue_key": "{{issue.key}}",
    "event_type": "{{issue.issueType.name}}",
    "project_key": "{{issue.project.key}}",
    "issue_type": "{{issue.issueType.name}}",
    "summary": "{{issue.summary}}",
    "assignee": "{{issue.assignee.displayName}}"
  }
}
```

**Headers:**
```
Accept: application/vnd.github+json
Authorization: Bearer YOUR_GITHUB_PAT
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Replace `YOUR_GITHUB_PAT` with your actual PAT token.

6. Click **Save**
7. Name it: "Trigger GitHub Agent"
8. Click **Turn it on**

## Test It!

### Option 1: Test from Command Line

```bash
# Set your GitHub PAT
export GITHUB_PAT="ghp_your_token_here"

# Test the webhook
python3 scripts/test_github_webhook.py \
  --owner Karthi-Knackforge \
  --repo cms-project \
  --issue CGCI-2
```

### Option 2: Create a Test Issue in Jira

1. Create a new issue in Jira
2. Go to GitHub: `https://github.com/YOUR_USERNAME/YOUR_REPO/actions`
3. Look for "Jira Triggered Agent Execution" workflow
4. You should see it running!

## Verify It Works

1. Check GitHub Actions tab
2. Look for workflow runs
3. Click on a run to see logs
4. Verify the agent executed successfully

## Troubleshooting

**No workflow triggered?**
- Check GitHub PAT has correct scopes
- Verify webhook URL is correct
- Test with the Python script first

**Workflow fails?**
- Check all GitHub secrets are set
- Verify API keys are valid
- Look at the workflow logs for details

**Jira automation fails?**
- Check Authorization header format
- Verify PAT token is correct
- Look at Jira automation audit log

## What Happens?

```
1. User creates Jira issue (CGCI-2)
2. Jira automation triggers
3. Sends webhook to GitHub API
4. GitHub Actions workflow starts
5. Multi-agent system executes
6. Code is generated and PR is created
7. Updates are posted back to Jira
```

## Next Steps

- ✅ Test with a real issue
- ✅ Adjust automation rules as needed
- ✅ Monitor first few runs
- ✅ Set up notifications

## Full Documentation

For detailed setup, advanced configuration, and troubleshooting:
- See [JIRA_GITHUB_INTEGRATION.md](JIRA_GITHUB_INTEGRATION.md)

## Common Customizations

### Only trigger for specific issue types

Add a condition in Jira automation:
- **Condition**: Issue fields condition
- **Field**: Issue Type
- **Value**: Story, Task (select the ones you want)

### Only trigger when assigned

Add a condition:
- **Condition**: Issue fields condition
- **Field**: Assignee
- **Condition**: is not empty

### Multiple projects

Edit `.github/workflows/jira-triggered.yml` and add your project mappings in the "Determine Project Path" step.

---

**Need Help?** See the full documentation or create an issue in the repository.
