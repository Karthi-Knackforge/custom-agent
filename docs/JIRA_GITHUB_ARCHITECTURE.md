# Jira-GitHub Integration Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                          JIRA CLOUD                                  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ 1. Issue Created/Updated
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Jira Automation Rule                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────┐       │
│  │   Trigger      │→ │   Condition    │→ │   Action       │       │
│  │ Issue Created  │  │ Issue Type =   │  │ Send Webhook   │       │
│  │                │  │ Story/Task     │  │                │       │
│  └────────────────┘  └────────────────┘  └────────────────┘       │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ 2. POST https://api.github.com/repos/{owner}/{repo}/dispatches
                                 │    Headers: Authorization: Bearer {PAT}
                                 │    Body: { "event_type": "jira-issue-created", "client_payload": {...} }
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB API                                   │
│                    (repository_dispatch)                             │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ 3. Triggers GitHub Actions Workflow
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      GitHub Actions Runner                           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │ Workflow: jira-triggered.yml                                  │  │
│  │                                                               │  │
│  │  Step 1: Checkout code                                       │  │
│  │  Step 2: Setup Python                                        │  │
│  │  Step 3: Install dependencies                                │  │
│  │  Step 4: Extract Jira details                                │  │
│  │         ├─ issue_key: CGCI-2                                 │  │
│  │         ├─ project_key: CGCI                                 │  │
│  │         └─ issue_type: Story                                 │  │
│  │  Step 5: Run multi-agent system                              │  │
│  │         └─ python run_agent.py --jira-key CGCI-2 ...        │  │
│  └──────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ 4. Multi-Agent Execution Starts
                                 ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Multi-Agent System                              │
│                                                                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐   │
│  │ JiraHandler    │    │ CodeGenerator  │    │ CodeReviewer   │   │
│  │                │    │                │    │                │   │
│  │ 1. Fetch       │───>│ 2. Generate    │───>│ 3. Review      │   │
│  │    Issue       │    │    Code with   │    │    Quality     │   │
│  │    Details     │    │    Claude +    │    │    Checks      │   │
│  │                │    │    Tools       │    │                │   │
│  └────────────────┘    └────────────────┘    └────────────────┘   │
│                              │                        │             │
│                              │  If fails ↶            │             │
│                              │   (max 3 iterations)   │             │
│                              │                        ↓             │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────┐   │
│  │ JiraHandler    │    │ GitHandler     │    │ GitHandler     │   │
│  │                │    │                │    │                │   │
│  │ 5. Post        │<───│ 4. Create PR   │<───│ 4. Commit      │   │
│  │    Comment     │    │                │    │    Changes     │   │
│  │                │    │                │    │                │   │
│  └────────────────┘    └────────────────┘    └────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                 │
                                 │ 5. Results
                                 ↓
┌──────────────────────────────────┐  ┌──────────────────────────────┐
│         GitHub PR                │  │      Jira Comment            │
│                                  │  │                              │
│  Draft Pull Request              │  │  🤖 Automated Agent Update   │
│  Branch: feature/CGCI-2          │  │                              │
│  Status: Ready for Review        │  │  Jira Key: CGCI-2           │
│  Files Changed: 5                │  │  PR: github.com/...         │
│                                  │  │  Status: Draft              │
└──────────────────────────────────┘  └──────────────────────────────┘
```

## Component Details

### 1. Jira Automation Rule

**Trigger Options**:
- Issue created
- Issue updated
- Issue transitioned
- Field value changed

**Condition Examples**:
- Issue type equals "Story"
- Project equals "CGCI"
- Assignee is not empty
- Priority is "High"

**Action**:
- Send HTTP POST to GitHub API
- Includes issue details in JSON payload

### 2. GitHub repository_dispatch

**Event Types Supported**:
- `jira-issue-created`
- `jira-issue-updated`
- `jira-issue-transition`

**Authentication**:
- GitHub Personal Access Token (PAT)
- Scopes: `repo`, `workflow`

**Payload Structure**:
```json
{
  "event_type": "jira-issue-created",
  "client_payload": {
    "issue_key": "CGCI-2",
    "project_key": "CGCI",
    "issue_type": "Story",
    "summary": "Add authentication",
    "assignee": "John Doe",
    "status": "To Do",
    "priority": "High"
  }
}
```

### 3. GitHub Actions Workflow

**Trigger**: `repository_dispatch`

**Environment Variables Required**:
- `ANTHROPIC_API_KEY` - Claude API
- `JIRA_BASE_URL` - Jira instance
- `JIRA_EMAIL` - Jira auth
- `JIRA_TOKEN` - Jira auth
- `GITHUB_TOKEN` - PR creation

**Workflow Steps**:
1. Checkout repository
2. Setup Python environment
3. Install dependencies
4. Extract Jira issue details
5. Determine project path
6. Run multi-agent system
7. Upload artifacts
8. Notify on success/failure

### 4. Multi-Agent System

**Agents**:
1. **JiraHandler** - Fetches issue details
2. **CodeGenerator** - Generates code using Claude
3. **CodeReviewer** - Reviews quality
4. **GitHandler** - Commits and creates PR

**Claude SDK Features**:
- 🛠️ Tool Use - Explores codebase
- 💾 Prompt Caching - Reduces costs
- 🧠 Extended Thinking - Better quality

**Iteration Loop**:
- Max 3 iterations
- Regenerate if review fails
- Stop if quality passes

### 5. Outputs

**GitHub Pull Request**:
- Created as draft
- Branch: `feature/{issue-key}`
- Includes quality summary
- Ready for human review

**Jira Comment**:
- Posted automatically
- Includes PR link
- Shows iteration count
- Lists changed files
- Quality check results

## Data Flow

```
Jira Issue Data
    ↓
[Jira Automation]
    ↓
HTTP POST with JSON
    ↓
[GitHub API]
    ↓
repository_dispatch Event
    ↓
[GitHub Actions]
    ↓
Environment Variables
    ↓
[Multi-Agent System]
    ↓
    ├─> [Fetch Jira] → Issue Details
    ├─> [Generate Code] → Files + Changes
    ├─> [Review Quality] → Pass/Fail
    ├─> [Git Operations] → Branch + Commit
    └─> [Create PR] → Draft PR
    ↓
Results Back to Jira
```

## Security Flow

```
GitHub PAT (User Creates)
    ↓
Stored in Jira Automation (Secure)
    ↓
Included in Webhook (Authorization Header)
    ↓
GitHub API Validates Token
    ↓
Grants Access to Trigger Workflow
    ↓
Workflow Runs with Repository Secrets
    ↓
Secrets Never Exposed in Logs
```

## Timing Breakdown

```
Event                          Time
─────────────────────────────────────────
Jira Issue Created            T+0s
Jira Automation Triggers      T+1s
Webhook Sent to GitHub        T+2s
GitHub Receives Request       T+2s
Workflow Queued               T+2s
Runner Assigned               T+5-30s
Dependencies Installed        T+30-60s
Agent Execution Starts        T+60s
Code Generation (Claude)      T+90-300s
Quality Review                T+300-360s
Git Operations                T+360-400s
PR Created                    T+400-420s
Jira Comment Posted           T+420-430s
─────────────────────────────────────────
Total Time: 7-10 minutes
```

## Error Handling Flow

```
┌─────────────────┐
│ Workflow Starts │
└────────┬────────┘
         │
         ↓
   ┌────────────┐
   │ Try Execute│
   └─────┬──────┘
         │
    ┌────┴────┐
    │ Success?│
    └────┬────┘
         │
    Yes  │  No
    ↓    │    ↓
┌────────┴────────────┐
│Upload Logs          │
│Notify Success/Fail  │
│Post Jira Comment    │
└─────────────────────┘
```

## Scalability Considerations

- **Concurrent Executions**: GitHub Actions supports parallel runs
- **Rate Limits**: GitHub API has rate limits (check usage)
- **Cost**: Anthropic API costs reduced 85% with caching
- **GitHub Actions Minutes**: Track usage for private repos

## Monitoring Points

1. **Jira Automation Audit Log** - Webhook success/failure
2. **GitHub Actions Logs** - Workflow execution details
3. **Artifacts** - Generated code and logs
4. **Jira Comments** - Execution results
5. **Pull Requests** - Final outputs

---

For implementation details, see:
- [Quick Setup](JIRA_SETUP_QUICKSTART.md)
- [Full Guide](JIRA_GITHUB_INTEGRATION.md)
- [Summary](JIRA_GITHUB_INTEGRATION_SUMMARY.md)
