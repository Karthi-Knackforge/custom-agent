# Scripts Directory

Utility scripts for testing and managing the multi-agent system.

## test_github_webhook.py

Test GitHub repository_dispatch webhooks for Jira integration.

### Usage

```bash
# Basic test
python3 scripts/test_github_webhook.py \
  --owner Karthi-Knackforge \
  --repo cms-project \
  --issue CGCI-2

# With custom details
python3 scripts/test_github_webhook.py \
  --owner YOUR_USERNAME \
  --repo YOUR_REPO \
  --issue PROJ-123 \
  --event jira-issue-updated \
  --summary "Add authentication" \
  --assignee "John Doe" \
  --priority "High"
```

### Environment Variables

```bash
export GITHUB_PAT="ghp_your_token_here"
export GITHUB_OWNER="default-owner"  # Optional
export GITHUB_REPO="default-repo"    # Optional
```

### Options

- `--owner` - GitHub repository owner
- `--repo` - GitHub repository name
- `--issue` - Jira issue key (required)
- `--event` - Event type (default: jira-issue-created)
- `--summary` - Issue summary
- `--assignee` - Assignee name
- `--priority` - Issue priority
- `--issue-type` - Issue type (Story, Task, Bug, Epic)

### Output

```
📤 Sending webhook to GitHub...
   URL: https://api.github.com/repos/owner/repo/dispatches
   Event: jira-issue-created
   Issue: CGCI-2

✅ Webhook sent successfully!

📋 Next steps:
   1. Go to https://github.com/owner/repo/actions
   2. Look for 'Jira Triggered Agent Execution' workflow
   3. You should see a new run starting
```

### Troubleshooting

**Error: GITHUB_PAT not set**
```bash
export GITHUB_PAT="your_token"
```

**Error: HTTP 404**
- Check owner/repo names are correct
- Verify repository exists and you have access

**Error: HTTP 401/403**
- Verify GITHUB_PAT is valid
- Check PAT has `repo` and `workflow` scopes

## Future Scripts

Additional utility scripts to be added:

- `setup_secrets.py` - Helper to configure GitHub secrets
- `test_jira_connection.py` - Verify Jira credentials
- `cleanup_branches.py` - Clean up feature branches
- `generate_report.py` - Generate execution reports

---

See [../docs/JIRA_GITHUB_INTEGRATION.md](../docs/JIRA_GITHUB_INTEGRATION.md) for full integration guide.
