# Jira-GitHub Integration Summary

## What Was Implemented

A complete Jira automation → GitHub Actions integration that allows Jira issues to automatically trigger your multi-agent system.

## Files Created

### 1. GitHub Actions Workflow
**File**: `.github/workflows/jira-triggered.yml`

- Responds to `repository_dispatch` events
- Supports 3 event types:
  - `jira-issue-created`
  - `jira-issue-updated`
  - `jira-issue-transition`
- Automatically extracts Jira issue details
- Runs the multi-agent system
- Uploads artifacts and logs
- Provides success/failure notifications

### 2. Documentation

**File**: `docs/JIRA_GITHUB_INTEGRATION.md`
- Comprehensive setup guide
- Step-by-step Jira automation configuration
- GitHub PAT creation instructions
- Webhook configuration examples
- Troubleshooting guide
- Security best practices
- Advanced configuration options

**File**: `docs/JIRA_SETUP_QUICKSTART.md`
- Quick 5-minute setup guide
- Simplified instructions
- Common use cases
- Quick troubleshooting

### 3. Testing Script

**File**: `scripts/test_github_webhook.py`
- Command-line tool to test webhooks
- Sends test `repository_dispatch` events
- Validates configuration
- Provides detailed error messages
- Supports all event types

## How It Works

```
┌─────────────┐
│ Jira Issue  │
│ Created/    │
│ Updated     │
└──────┬──────┘
       │
       │ Jira Automation Rule
       │ Triggers
       ↓
┌─────────────────┐
│ HTTP Request    │
│ to GitHub API   │
│ (repository_    │
│  dispatch)      │
└──────┬──────────┘
       │
       │ GitHub receives
       │ dispatch event
       ↓
┌─────────────────┐
│ GitHub Actions  │
│ Workflow        │
│ Triggers        │
└──────┬──────────┘
       │
       │ Workflow runs
       │ run_agent.py
       ↓
┌─────────────────┐
│ Multi-Agent     │
│ System          │
│ Executes        │
└──────┬──────────┘
       │
       │ Generates code
       │ Creates PR
       ↓
┌─────────────────┐
│ Updates Jira    │
│ with PR link    │
│ and status      │
└─────────────────┘
```

## Setup Requirements

### GitHub Side

1. **Secrets Required**:
   - `ANTHROPIC_API_KEY` - Claude API key
   - `JIRA_BASE_URL` - Jira instance URL
   - `JIRA_EMAIL` - Jira account email
   - `JIRA_TOKEN` - Jira API token
   - `GITHUB_PAT` - Personal Access Token for workflow triggering

2. **Workflow File**: `.github/workflows/jira-triggered.yml` (already created)

3. **GitHub PAT Scopes**:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `workflow` (Update GitHub Action workflows)

### Jira Side

1. **Automation Rule** with:
   - **Trigger**: Issue created/updated/transitioned
   - **Condition** (optional): Filter by issue type, project, etc.
   - **Action**: Send web request to GitHub API

2. **Webhook Configuration**:
   - URL: `https://api.github.com/repos/{owner}/{repo}/dispatches`
   - Method: `POST`
   - Headers: Authorization with GitHub PAT
   - Body: JSON with issue details

## Event Types

### 1. jira-issue-created
Triggered when new issues are created.

**Use Case**: Automatically start work on new stories/tasks

**Payload**:
```json
{
  "event_type": "jira-issue-created",
  "client_payload": {
    "issue_key": "CGCI-2",
    "project_key": "CGCI",
    "issue_type": "Story",
    "summary": "Add authentication",
    "assignee": "John Doe"
  }
}
```

### 2. jira-issue-updated
Triggered when issue fields are updated.

**Use Case**: Regenerate code when requirements change

### 3. jira-issue-transition
Triggered when issue status changes.

**Use Case**: Start work when moved to "In Progress"

## Testing

### Test with Python Script

```bash
# Set environment variables
export GITHUB_PAT="ghp_your_token"
export GITHUB_OWNER="Karthi-Knackforge"
export GITHUB_REPO="cms-project"

# Run test
python3 scripts/test_github_webhook.py \
  --issue CGCI-2 \
  --event jira-issue-created
```

### Test with curl

```bash
curl -X POST \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: Bearer ${GITHUB_PAT}" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  https://api.github.com/repos/OWNER/REPO/dispatches \
  -d '{
    "event_type": "jira-issue-created",
    "client_payload": {
      "issue_key": "CGCI-2",
      "project_key": "CGCI"
    }
  }'
```

### Test in Jira

1. Create automation rule
2. Use "Test component" button
3. Check GitHub Actions tab for workflow run

## Verification Steps

1. ✅ Create test Jira issue
2. ✅ Check Jira automation audit log
3. ✅ Verify webhook sent (HTTP 204 response)
4. ✅ Check GitHub Actions tab
5. ✅ Verify workflow triggered
6. ✅ Check workflow logs for errors
7. ✅ Verify PR created (if not dry-run)

## Monitoring

### GitHub Actions Logs

Navigate to: `https://github.com/{owner}/{repo}/actions`

Look for:
- Workflow name: "Jira Triggered Agent Execution"
- Triggered by: `repository_dispatch`
- Check logs for each step

### Jira Automation Audit Log

Navigate to: Jira Settings → System → Automation → [Your Rule] → Audit log

Check for:
- Execution history
- Success/failure status
- Error messages

## Troubleshooting

### Issue: Workflow not triggered

**Possible Causes**:
- GitHub PAT missing or invalid
- PAT lacks required scopes
- Webhook URL incorrect
- Authorization header malformed

**Solution**:
1. Verify PAT has `repo` and `workflow` scopes
2. Check webhook URL format
3. Test with Python script first

### Issue: Workflow triggered but fails

**Possible Causes**:
- Missing GitHub secrets
- Invalid API keys
- Project path not found

**Solution**:
1. Check all secrets are configured
2. Verify API keys are valid
3. Check workflow logs for specific error

### Issue: Jira automation fails

**Possible Causes**:
- GitHub PAT expired
- Incorrect JSON syntax
- Network issues

**Solution**:
1. Check Jira automation audit log
2. Verify JSON payload syntax
3. Test with "Test component" button

## Security Considerations

1. **Never commit tokens**: Always use GitHub Secrets
2. **Rotate credentials**: Update tokens regularly
3. **Minimal scopes**: Only grant necessary PAT scopes
4. **Audit logs**: Review automation logs periodically
5. **Environment isolation**: Use separate tokens for prod/dev

## Advanced Configuration

### Multiple Projects

Map different Jira projects to different repository paths:

```yaml
case "$PROJECT_KEY" in
  "CGCI")
    echo "project_path=." >> $GITHUB_OUTPUT
    ;;
  "PROJ2")
    echo "project_path=services/api" >> $GITHUB_OUTPUT
    ;;
esac
```

### Conditional Execution

Only run for specific issue types:

```yaml
if: |
  github.event.client_payload.issue_type == 'Story' ||
  github.event.client_payload.issue_type == 'Task'
```

### Notifications

Add Slack/email notifications on success/failure.

## Performance

- **Webhook Response Time**: < 1 second
- **GitHub Actions Start**: 5-30 seconds
- **Agent Execution**: Varies (5-10 minutes typical)
- **Total Time**: Issue created → PR ready: 5-15 minutes

## Cost Implications

- **GitHub Actions**: Free for public repos, included minutes for private
- **Anthropic API**: Per request (reduced 85% with caching)
- **Jira Automation**: Included with Jira Cloud

## Next Steps

1. ✅ Complete initial setup
2. ✅ Test with sample issues
3. ✅ Monitor first few runs
4. ✅ Adjust automation rules as needed
5. ✅ Set up notifications
6. ✅ Document team workflow

## Success Metrics

Track these to measure effectiveness:

- ✅ Issues automatically processed
- ✅ PRs created per day
- ✅ Time from issue → PR
- ✅ Manual intervention rate
- ✅ Success/failure ratio

## Resources

- 📖 [Quick Setup Guide](JIRA_SETUP_QUICKSTART.md)
- 📖 [Full Integration Guide](JIRA_GITHUB_INTEGRATION.md)
- 🔧 [Test Script](../scripts/test_github_webhook.py)
- 🎬 [Workflow File](../.github/workflows/jira-triggered.yml)

## Support

For issues or questions:
1. Check documentation
2. Review workflow logs
3. Check Jira automation audit log
4. Create issue in repository

---

**Status**: ✅ Complete and Ready for Use  
**Last Updated**: November 13, 2025
