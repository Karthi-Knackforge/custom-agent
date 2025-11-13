# Architecture Deep Dive

## System Overview

The multi-agent system follows a sequential orchestration pattern where specialized agents collaborate to generate, review, and deploy code changes automatically.

## Core Design Principles

1. **Separation of Concerns**: Each agent has a single, well-defined responsibility
2. **Event-Driven Communication**: Agents emit events for observability and loose coupling
3. **Language Agnostic**: Plugin architecture supports multiple programming languages
4. **Fail-Safe Defaults**: Dry-run mode, draft PRs, manual approval gates
5. **Iterative Refinement**: Automatic regeneration based on quality feedback

## Component Architecture

### 1. Orchestrator (`core/orchestrator.py`)

**Responsibility**: Coordinates sequential execution of all agents

**Flow**:
```
initialize() → fetch_jira() → [generate → review → regenerate?]* → commit → pr → comment
```

**Key Features**:
- Manages execution context (shared state across agents)
- Implements iteration loop with configurable max attempts
- Handles error recovery and cleanup
- Provides dry-run mode for testing

### 2. Context (`core/context.py`)

**Responsibility**: Shared execution state

**Key Data**:
- Input: Jira key, task description, project metadata
- State: Current iteration, quality results, generated files
- Output: Branch name, commit SHA, PR URL

**Iteration State**:
Each iteration tracks:
- Generated files (path + content)
- Diff patch
- Quality check results (lint, test, typecheck)
- Critique from reviewer (if failed)
- Overall status (pass/soft_fail/hard_fail)

### 3. Event System (`core/events.py`)

**Responsibility**: Publish-subscribe event bus for agent coordination

**Event Types**:
- Lifecycle: `AGENT_STARTED`, `AGENT_COMPLETED`, `AGENT_FAILED`
- Generation: `CODE_GENERATED`, `CODE_GENERATION_FAILED`
- Review: `REVIEW_PASSED`, `REVIEW_HARD_FAIL`, `REVIEW_SOFT_FAIL`
- Git: `GIT_BRANCH_CREATED`, `GIT_PR_CREATED`
- Jira: `JIRA_ISSUE_FETCHED`, `JIRA_COMMENT_POSTED`

**Use Cases**:
- Observability (log all events)
- Metrics collection (token usage, duration)
- Debugging (event history replay)
- Future: Webhooks, external integrations

### 4. Configuration System (`core/config_loader.py`)

**Responsibility**: Load and merge configuration from YAML files

**Hierarchy**:
```
config/agent.yaml (global defaults)
  └─> config/projects/<name>.yaml (project overrides)
```

**Features**:
- Deep merge of configurations
- Language detection (marker file scanning)
- Project discovery and listing

### 5. Language Plugin System (`language_plugins/`)

**Responsibility**: Abstract language-specific operations

**Plugin Interface**:
```python
class LanguagePlugin(Protocol):
    name: str
    extensions: list[str]
    
    def summarize(project_path) -> dict
    def quality_commands(project_path) -> list[QualityCommand]
    def post_process(file_path, content) -> str
    def build_context_fragments(changed_paths) -> list[str]
```

**Built-in Plugins**:
- Python: AST parsing for structure, pytest/ruff/mypy
- JavaScript/TypeScript: package.json parsing, npm test/eslint/tsc

**Extension Points**:
- Add new languages by implementing `LanguagePlugin`
- Register in `Orchestrator._register_plugins()`
- Define quality commands in config

## Agent Details

### CodeGeneratorAgent

**Input**:
- Task description (from Jira or CLI)
- Project context (language, structure summary)
- Constraints (allowed paths, quality requirements)
- Previous critique (if iteration > 1)

**Process**:
1. Build generation context (project summary, constraints)
2. Construct prompt with system + user messages
3. Call Claude API with retry logic
4. Parse JSON response (`files` array)
5. Validate file paths (no traversal, size limits)
6. Create `FileChange` objects

**Output**:
- List of `FileChange` objects (path + content)
- Notes explaining changes

**Prompt Strategy**:
- System: Coding standards, security guidelines, output format
- User: Task + context + constraints + critique (if any)
- Iteration-specific adjustments (tighter constraints on later iterations)

**Validation**:
- Path traversal checks (`..` detection)
- Path whitelist/blacklist enforcement
- File size limits (default 200KB)
- JSON schema validation

### CodeReviewerAgent

**Input**:
- Current iteration state (generated files)
- Language plugin (for quality commands)

**Process**:
1. Get quality commands from language plugin
2. Execute each command (subprocess with timeout)
3. Parse output and determine status
4. Aggregate results into overall status
5. Generate critique if failures exist

**Quality Command Types**:
- **test**: Critical (failure = hard_fail)
- **lint**: Non-critical (failure = soft_fail)
- **typecheck**: Non-critical (failure = soft_fail)
- **format**: Optional post-processing

**Status Determination**:
```
All pass → PASS
Test fail → HARD_FAIL
Lint/typecheck fail → SOFT_FAIL
```

**Critique Generation**:
- Extract failure messages from command output
- Format with context (command, exit code, output)
- Provide actionable suggestions

**Timeout Handling**:
- Default: 5 minutes per command
- Retry once on timeout
- Fail gracefully with partial results

### GitHandlerAgent

**Input**:
- Context with generated files
- Git client (configured with repo)
- GitHub client (for PR operations)

**Process**:
1. Create feature branch (`feat/<jira-key>`)
2. Write files to disk
3. Stage changed files
4. Commit with conventional message
5. Push to remote
6. Create draft PR via GitHub API
7. Add labels (`needs-approval`)

**Branch Naming**:
```
<prefix>/<jira-key-lowercase>
prefix: "feat" (new feature), "fix" (bug fix), "chore" (maintenance)
```

**Commit Message Format**:
```
<JIRA-KEY>: <task summary>

Generated by multi-agent system (iteration N)
Files changed: M
```

**PR Body Template**:
```markdown
## Jira Issue: <KEY>
**Description:** <summary>

### Generation Summary
- Iterations: N/M
- Quality Status: pass/fail
- Files Changed: X

### Changed Files
- path/to/file1.py
- path/to/file2.js
...

### Quality Checks
- ✅ test: pass
- ✅ lint: pass
- ❌ typecheck: fail

---
*This PR was automatically generated by the multi-agent system.*
*Manual review and approval required before merge.*
```

**Draft PR Rationale**:
- Prevents accidental auto-merge
- Requires explicit human review
- Allows CI/CD to run before approval

### JiraHandlerAgent

**Input**:
- Jira client (authenticated)
- Context with execution details

**Actions**:

**1. Fetch Issue** (`action="fetch"`):
- Retrieve issue via REST API
- Extract summary, description, status
- Update context with task description

**2. Post Comment** (`action="comment"`):
- Generate summary comment
- Post via REST API
- Include PR link, iteration count, quality status

**Comment Template**:
```
🤖 Automated Agent Update

Jira Key: <KEY>
Pull Request: <URL> (draft)
Iterations: N/M
Status: Quality checks <status>
Files Changed: X

Changed Files:
• path/to/file1
• path/to/file2
...

Quality Checks:
• ✓ test: pass
• ✗ lint: fail

Next Action: Human review and approval required.
```

**Error Handling**:
- Graceful degradation if Jira unavailable
- Continue execution without blocking
- Log warnings for visibility

## Integration Layer

### AnthropicClient (`integrations/anthropic_client.py`)

**Features**:
- Retry with exponential backoff (rate limits, server errors)
- JSON extraction from markdown code blocks
- Schema validation for model outputs
- Token budgeting (truncate large inputs)

**Retry Strategy**:
```python
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((RateLimitError, InternalServerError))
)
```

**Prompt Construction**:
1. System prompt (base + language-specific)
2. User prompt (task + context + constraints + critique)
3. Output format instructions (strict JSON schema)

**Response Parsing**:
- Extract JSON from markdown (```json blocks)
- Fallback: regex search for JSON object
- Validate required fields (`files`, `path`, `content`)
- Handle malformed responses gracefully

### GitClient (`integrations/git_ops.py`)

**Wrapper around GitPython**:
- Branch operations (create, checkout, exists)
- Staging and commits
- Push with upstream tracking
- Diff generation

**Safety Features**:
- Check working directory cleanliness before operations
- Validate branch names
- Author configuration (use GitHub Actions bot)

### GitHubClient (`integrations/git_ops.py`)

**REST API Operations**:
- Create pull request (POST /repos/{owner}/{repo}/pulls)
- Add labels (POST /repos/{owner}/{repo}/issues/{number}/labels)
- Parse remote URL to extract owner/repo

**Authentication**:
- Bearer token (GITHUB_TOKEN env var)
- Auto-provided in GitHub Actions

### JiraClient (`integrations/jira_client.py`)

**REST API Operations**:
- Get issue (GET /rest/api/3/issue/{key})
- Add comment (POST /rest/api/3/issue/{key}/comment)
- Search issues (GET /rest/api/3/search with JQL)

**Authentication**:
- Basic auth (email + API token)
- Credentials from environment variables

**Comment Format**:
- Atlassian Document Format (ADF)
- Supports text, paragraphs, code blocks

## Execution Flow Details

### Sequential Flow

```
1. Initialize
   └─> Load config
   └─> Detect project language
   └─> Initialize agents

2. Fetch Jira Issue (optional)
   └─> Call Jira API
   └─> Extract summary as task description

3. Iteration Loop (max N times)
   ├─> Generate Code
   │   ├─> Build context (project summary)
   │   ├─> Build constraints (paths, requirements)
   │   ├─> Call Claude with prompt
   │   ├─> Parse JSON response
   │   └─> Validate & create FileChange objects
   │
   ├─> Review Code
   │   ├─> Get quality commands from plugin
   │   ├─> Run commands (test, lint, typecheck)
   │   ├─> Aggregate results
   │   └─> Generate critique if failures
   │
   └─> Decision
       ├─> If PASS → Exit loop
       ├─> If SOFT_FAIL & last iteration → Exit loop
       ├─> If HARD_FAIL & last iteration → Exit loop (with warnings)
       └─> Else → Continue to next iteration

4. Git Operations
   ├─> Create feature branch
   ├─> Write files to disk
   ├─> Stage & commit changes
   ├─> Push to remote
   └─> Create draft PR with label

5. Jira Comment
   └─> Post summary with PR link and status

6. Finalize
   └─> Save artifacts (logs, prompts, diffs)
```

### Iteration Logic

**Max Iterations**: Configurable (default: 3)

**Stop Conditions**:
1. Quality checks pass (all tests, lint, typecheck)
2. Max iterations reached (proceed with best effort)
3. Unrecoverable error (abort)

**Regeneration Trigger**:
- HARD_FAIL: Test failures, security issues
- SOFT_FAIL: Style violations, non-critical warnings

**Critique Feed-Forward**:
- Review agent generates structured critique
- Passed as `previous_critique` in next generation prompt
- Model instructed to address all issues

**Convergence Strategy**:
- Tighter constraints in later iterations
- More explicit failure descriptions
- Fallback to "best effort" on timeout

## Data Flow

### Context Evolution

```
Iteration 1:
  Context {
    iteration: 1
    iterations: []
  }
  ↓ Generate
  Context {
    iteration: 1
    iterations: [
      IterationState {
        iteration: 1
        generated_files: [FileChange, ...]
        status: "pending"
      }
    ]
  }
  ↓ Review
  Context {
    iteration: 1
    iterations: [
      IterationState {
        iteration: 1
        generated_files: [FileChange, ...]
        quality_results: {test: pass, lint: fail}
        critique: "..."
        status: "soft_fail"
      }
    ]
  }

Iteration 2:
  Context {
    iteration: 2
    iterations: [IterationState(1), IterationState(2)]
  }
  ...
```

### Event Flow

```
Orchestrator
  ├─> ITERATION_STARTED
  │
  ├─> CodeGeneratorAgent
  │   ├─> CODE_GENERATION_STARTED
  │   └─> CODE_GENERATED
  │
  ├─> CodeReviewerAgent
  │   ├─> REVIEW_STARTED
  │   └─> REVIEW_PASSED | REVIEW_SOFT_FAIL | REVIEW_HARD_FAIL
  │
  ├─> (Iteration decision)
  │
  ├─> GitHandlerAgent
  │   ├─> GIT_BRANCH_CREATED
  │   ├─> GIT_COMMIT_CREATED
  │   └─> GIT_PR_CREATED
  │
  └─> JiraHandlerAgent
      └─> JIRA_COMMENT_POSTED
```

## Extensibility

### Adding New Agents

1. Inherit from `Agent` base class
2. Implement `execute(context) -> dict` method
3. Emit events for observability
4. Register in orchestrator

Example:
```python
class SecurityScannerAgent(Agent):
    async def execute(self, context):
        self.emit_event(EventType.SECURITY_SCAN_STARTED, {})
        
        # Run security scan
        vulnerabilities = self.scan(context.current_iteration().generated_files)
        
        if vulnerabilities:
            self.emit_event(EventType.SECURITY_ISSUES_FOUND, {
                "count": len(vulnerabilities)
            })
            return {"success": False, "vulnerabilities": vulnerabilities}
        
        self.emit_event(EventType.SECURITY_SCAN_PASSED, {})
        return {"success": True}
```

### Parallel Execution (Future)

Currently sequential. For parallel:
- Use `asyncio.gather()` for independent operations
- Implement dependency graph (DAG)
- Ensure thread-safe context updates

### Webhook Integration (Future)

- Subscribe to events in `EventDispatcher`
- Post events to external systems (Slack, PagerDuty, etc.)
- Example: Post notification on `REVIEW_HARD_FAIL`

## Performance Considerations

### Token Usage

**Optimization Strategies**:
- Summarize large files (signatures only, not full content)
- Truncate long outputs (first 5000 chars)
- Use streaming responses (future)
- Cache project summaries (future)

**Typical Usage**:
- Generation prompt: ~2000-4000 tokens
- Generation response: ~2000-8000 tokens
- Review prompt: ~1000-3000 tokens
- Review response: ~500-2000 tokens

**Per Iteration**: ~10K-20K tokens
**3 Iterations**: ~30K-60K tokens

### Execution Time

**Typical Durations**:
- Jira fetch: 1-2s
- Code generation: 10-30s (depends on model, task complexity)
- Quality checks: 5-60s (depends on test suite size)
- Git operations: 2-5s
- PR creation: 2-3s

**Total (3 iterations)**: ~1-5 minutes

**Optimization**:
- Parallel quality command execution
- Incremental diffs (only changed files)
- Caching of static analysis results

## Security & Safety

### Input Validation

**Path Traversal Prevention**:
```python
if ".." in path or path.startswith("/"):
    reject()
```

**File Size Limits**:
- Default: 200KB per file
- Prevents runaway generation costs

**Pattern Restrictions**:
```yaml
restricted_patterns:
  - "**/.env"
  - "**/.git/**"
  - "**/secrets/**"
```

### Secrets Management

**Environment Variables**:
- `ANTHROPIC_API_KEY`: Claude API access
- `GITHUB_TOKEN`: PR creation
- `JIRA_TOKEN`: Issue access

**GitHub Actions Secrets**:
- Encrypted at rest
- Masked in logs
- Scoped to repository

**Best Practices**:
- Never log secret values
- Use least-privilege tokens
- Rotate regularly

### Approval Gates

**Draft PR + Label**:
- Prevents auto-merge
- Requires manual review
- CI/CD runs before approval

**Quality Gates**:
- Hard fail on test failures
- Soft fail on style issues
- Always generate PR for visibility

## Monitoring & Observability

### Logging

**Structured Logs** (JSONL):
```json
{"timestamp": "...", "agent": "CodeGenerator", "event": "CODE_GENERATED", "iteration": 1}
```

**Log Levels**:
- INFO: Normal operation
- WARNING: Recoverable issues
- ERROR: Failures

### Artifacts

**Per Execution**:
- `run_<timestamp>.log`: Full event log
- `summary.json`: Final result

**Per Iteration**:
- `iteration_N/prompt.json`: Full prompt sent
- `iteration_N/response.json`: Model response
- `iteration_N/diff.patch`: Generated changes
- `iteration_N/quality_report.json`: Test/lint results

**Retention**:
- GitHub Actions: 7 days (configurable)
- Local: Indefinite (until manual cleanup)

### Metrics (Future)

**Key Metrics**:
- Execution success rate
- Average iterations to pass
- Token usage per execution
- Quality check failure breakdown
- Time per agent

**Dashboards**:
- Grafana integration
- Prometheus metrics export
- OpenTelemetry tracing

## Failure Modes & Recovery

### Common Failures

1. **Model Hallucination** (invalid file paths)
   - **Mitigation**: Path validation, whitelist enforcement
   - **Recovery**: Filter invalid files, log warning

2. **Quality Check Timeout**
   - **Mitigation**: 5-minute timeout, retry once
   - **Recovery**: Proceed with partial results

3. **API Rate Limits** (Anthropic, GitHub, Jira)
   - **Mitigation**: Exponential backoff retry
   - **Recovery**: Wait and retry (3 attempts)

4. **Git Conflicts**
   - **Mitigation**: Work on isolated branch
   - **Recovery**: Manual intervention required

5. **Iteration Timeout** (max reached with failures)
   - **Mitigation**: Still create PR for visibility
   - **Recovery**: Human review and fix

### Error Handling Strategy

**Levels**:
- **Recoverable**: Retry with backoff
- **Degraded**: Continue without feature (e.g., skip Jira comment)
- **Fatal**: Abort execution, clean up

**Cleanup**:
- Event log saved to artifacts
- Partial PR created (if possible)
- Error reported to Jira/GitHub issue

## Future Enhancements

### Short Term

- [ ] Embeddings-based context retrieval (for large codebases)
- [ ] Parallel quality check execution
- [ ] Support for more languages (Rust, Ruby, C#)
- [ ] Auto-merge for low-risk changes (with confidence scoring)

### Medium Term

- [ ] Planning agent (task decomposition)
- [ ] Security scanner agent (SAST integration)
- [ ] Dependency update agent
- [ ] Multi-file refactoring support

### Long Term

- [ ] Continuous learning (fine-tuning on repo patterns)
- [ ] A/B testing of prompts and strategies
- [ ] Distributed execution (multiple repos in parallel)
- [ ] Full CI/CD integration (deploy on merge)
