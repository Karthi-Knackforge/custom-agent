# Jira Automation to GitHub Integration Guide

This guide shows you how to set up Jira automation to trigger your multi-agent system via GitHub Actions.

## Overview

```
Jira Issue Created/Updated
    ↓
Jira Automation Rule
    ↓
HTTP Request to GitHub API
    ↓
GitHub repository_dispatch Event
    ↓
GitHub Actions Workflow Triggered
    ↓
Multi-Agent System Executes
```

## Step 1: Set Up GitHub Secrets

In your GitHub repository, go to **Settings → Secrets and variables → Actions** and add:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Your Claude API key |
| `JIRA_BASE_URL` | `https://yoursite.atlassian.net` | Your Jira instance URL |
| `JIRA_EMAIL` | `your@email.com` | Jira account email |
| `JIRA_TOKEN` | `ATATT3x...` | Jira API token |
| `GITHUB_TOKEN` | Automatically provided | Used for PR creation |
| `GITHUB_PAT` | `ghp_...` | Personal Access Token for triggering workflows |

### Creating GitHub Personal Access Token (PAT)

1. Go to **GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)**
2. Click **Generate new token (classic)**
3. Give it a name: "Jira Automation Trigger"
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)
5. Click **Generate token**
6. Copy the token (starts with `ghp_`) and save it as `GITHUB_PAT` secret

## Step 2: Configure Jira Automation

### 2.1 Create Automation Rule in Jira

1. Go to **Jira Settings → System → Automation**
2. Click **Create rule**
3. Choose a trigger:
   - **Issue created** - Trigger when new issues are created
   - **Issue transitioned** - Trigger when issue status changes
   - **Field value changed** - Trigger on specific field changes

### 2.2 Add Conditions (Optional)

Add conditions to filter when the automation runs:

**Example: Only for specific issue types**
- Add condition: **Issue fields condition**
- Field: `Issue Type`
- Condition: `equals`
- Value: `Story`, `Task`, or `Bug`

**Example: Only for specific projects**
- Add condition: **Issue fields condition**
- Field: `Project`
- Condition: `equals`
- Value: `CGCI` (your project key)

**Example: Only when assigned**
- Add condition: **Issue fields condition**
- Field: `Assignee`
- Condition: `is not empty`

### 2.3 Add GitHub Webhook Action

1. Click **Add component → Action → Send web request**
2. Configure the webhook:

**Webhook URL:**
```
https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches
```

Replace:
- `YOUR_USERNAME` with your GitHub username (e.g., `Karthi-Knackforge`)
- `YOUR_REPO` with your repository name (e.g., `cms-project`)

**HTTP Method:** `POST`

**Webhook body (Custom data):**
```json
{
  "event_type": "jira-issue-created",
  "client_payload": {
    "issue_key": "{{issue.key}}",
    "event_type": "{{issue.issueType.name}}",
    "project_key": "{{issue.project.key}}",
    "issue_type": "{{issue.issueType.name}}",
    "summary": "{{issue.summary}}",
    "assignee": "{{issue.assignee.displayName}}",
    "status": "{{issue.status.name}}",
    "priority": "{{issue.priority.name}}",
    "created": "{{issue.created}}",
    "updated": "{{issue.updated}}"
  }
}
```

**Headers:**
```
Accept: application/vnd.github+json
Authorization: Bearer YOUR_GITHUB_PAT_TOKEN
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Replace `YOUR_GITHUB_PAT_TOKEN` with your GitHub PAT (the one you created in Step 1).

**Important:** For the Authorization header, you can either:
- Option A: Use a Jira secret/vault to store the token securely
- Option B: Paste the token directly (less secure but simpler)

### 2.4 Test and Save

1. Click **Test component** to verify the webhook works
2. Give your rule a name: "Trigger GitHub Agent for New Issues"
3. Click **Turn it on**

## Step 3: Event Types

You can create different rules for different events:

### Event Type: `jira-issue-created`
Triggered when a new issue is created.

```json
{
  "event_type": "jira-issue-created",
  "client_payload": { ... }
}
```

### Event Type: `jira-issue-updated`
Triggered when an issue is updated.

```json
{
  "event_type": "jira-issue-updated",
  "client_payload": { ... }
}
```

### Event Type: `jira-issue-transition`
Triggered when an issue status changes.

```json
{
  "event_type": "jira-issue-transition",
  "client_payload": {
    ...
    "from_status": "{{issue.status.previousStatus}}",
    "to_status": "{{issue.status.name}}"
  }
}
```

## Step 4: Test the Integration

### Manual Test from Command Line

```bash
# Test triggering the workflow manually
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer YOUR_GITHUB_PAT" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/dispatches \
  -d '{
    "event_type": "jira-issue-created",
    "client_payload": {
      "issue_key": "CGCI-2",
      "event_type": "Story",
      "project_key": "CGCI",
      "issue_type": "Story",
      "summary": "Test issue",
      "assignee": "Test User"
    }
  }'
```

### Test with Python Script

Save this as `test_github_webhook.py`:

```python
#!/usr/bin/env python3
"""Test GitHub repository_dispatch webhook."""
import os
import requests
import sys

GITHUB_TOKEN = os.getenv("GITHUB_PAT", "")
GITHUB_OWNER = "YOUR_USERNAME"  # Replace
GITHUB_REPO = "YOUR_REPO"       # Replace

if not GITHUB_TOKEN:
    print("Error: GITHUB_PAT environment variable not set")
    sys.exit(1)

url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/dispatches"

payload = {
    "event_type": "jira-issue-created",
    "client_payload": {
        "issue_key": "CGCI-2",
        "event_type": "Story",
        "project_key": "CGCI",
        "issue_type": "Story",
        "summary": "Test issue from script",
        "assignee": "Test User"
    }
}

headers = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "X-GitHub-Api-Version": "2022-11-28",
    "Content-Type": "application/json"
}

print(f"Sending webhook to {url}...")
response = requests.post(url, json=payload, headers=headers)

if response.status_code == 204:
    print("✅ Webhook sent successfully!")
    print("Check GitHub Actions tab to see the workflow run.")
else:
    print(f"❌ Failed to send webhook: {response.status_code}")
    print(response.text)
```

Run it:
```bash
export GITHUB_PAT="your_github_pat"
python3 test_github_webhook.py
```

### Verify in GitHub

1. Go to your repository on GitHub
2. Click **Actions** tab
3. Look for "Jira Triggered Agent Execution" workflow
4. You should see a new run triggered by the webhook

## Step 5: Monitor and Debug

### Check GitHub Actions Logs

1. Go to **Actions** tab in your repository
2. Click on the workflow run
3. Expand each step to see logs

### Common Issues

**Issue: Workflow not triggered**
- ✅ Check that `GITHUB_PAT` has correct scopes (`repo`, `workflow`)
- ✅ Verify webhook URL is correct
- ✅ Check Authorization header format

**Issue: Workflow triggered but fails**
- ✅ Check GitHub secrets are set correctly
- ✅ Verify Jira credentials in secrets
- ✅ Check Anthropic API key is valid

**Issue: Jira automation test fails**
- ✅ Verify GitHub PAT token is valid
- ✅ Check webhook URL syntax
- ✅ Ensure JSON payload is valid

### Debug Jira Automation

1. Go to **Jira Settings → System → Automation**
2. Click on your rule
3. Click **Audit log** tab
4. View execution history and errors

## Step 6: Advanced Configuration

### Multiple Projects

Edit the workflow file to map different Jira projects:

```yaml
- name: Determine Project Path
  id: project
  run: |
    PROJECT_KEY="${{ steps.jira.outputs.project_key }}"
    
    case "$PROJECT_KEY" in
      "CGCI")
        echo "project_name=cms-project" >> $GITHUB_OUTPUT
        echo "project_path=." >> $GITHUB_OUTPUT
        ;;
      "PROJ2")
        echo "project_name=other-project" >> $GITHUB_OUTPUT
        echo "project_path=services/other" >> $GITHUB_OUTPUT
        ;;
      *)
        echo "project_name=default" >> $GITHUB_OUTPUT
        echo "project_path=." >> $GITHUB_OUTPUT
        ;;
    esac
```

### Conditional Execution

Add conditions to the workflow:

```yaml
jobs:
  run-multi-agent:
    runs-on: ubuntu-latest
    # Only run for specific issue types
    if: |
      github.event.client_payload.issue_type == 'Story' ||
      github.event.client_payload.issue_type == 'Task'
```

### Notifications

Add Slack notifications:

```yaml
- name: Notify Slack on Success
  if: success()
  uses: slackapi/slack-github-action@v1
  with:
    webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
    payload: |
      {
        "text": "✅ Agent completed: ${{ steps.jira.outputs.issue_key }}",
        "blocks": [
          {
            "type": "section",
            "text": {
              "type": "mrkdwn",
              "text": "*Issue*: ${{ steps.jira.outputs.issue_key }}\n*Status*: Success"
            }
          }
        ]
      }
```

## Security Best Practices

1. **Never commit tokens** - Always use GitHub Secrets
2. **Use specific PAT scopes** - Only grant necessary permissions
3. **Rotate tokens regularly** - Update PAT and Jira tokens periodically
4. **Use Jira secrets** - Store GitHub PAT in Jira vault if available
5. **Audit automation** - Review Jira automation logs regularly

## Troubleshooting Checklist

- [ ] GitHub PAT created with `repo` and `workflow` scopes
- [ ] GitHub PAT added as secret in repository
- [ ] All required secrets configured in GitHub
- [ ] Jira automation rule created and enabled
- [ ] Webhook URL correct (owner/repo names)
- [ ] Authorization header includes `Bearer` prefix
- [ ] JSON payload is valid (test with curl)
- [ ] Workflow file exists in `.github/workflows/`
- [ ] Repository has Actions enabled

## Example Jira Automation Rules

### Rule 1: New Story Created
- **Trigger**: Issue created
- **Condition**: Issue type equals "Story"
- **Action**: Send webhook with event_type "jira-issue-created"

### Rule 2: Issue Moved to "In Progress"
- **Trigger**: Issue transitioned
- **Condition**: Status equals "In Progress"
- **Action**: Send webhook with event_type "jira-issue-transition"

### Rule 3: High Priority Bug Assigned
- **Trigger**: Issue updated
- **Condition**: 
  - Issue type equals "Bug"
  - Priority equals "High"
  - Assignee is not empty
- **Action**: Send webhook with event_type "jira-issue-updated"

## Next Steps

1. ✅ Test the integration with a sample issue
2. ✅ Monitor the first few runs to ensure success
3. ✅ Adjust automation rules based on your workflow
4. ✅ Set up notifications for failures
5. ✅ Document your team's workflow

## Resources

- [GitHub Actions Events](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#repository_dispatch)
- [Jira Automation](https://support.atlassian.com/cloud-automation/)
- [GitHub API - Create Dispatch Event](https://docs.github.com/en/rest/repos/repos#create-a-repository-dispatch-event)
