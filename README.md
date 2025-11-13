# Multi-Agent Code Generation System

A sophisticated multi-agent system for automated code generation, review, and deployment using Claude (Anthropic), integrated with GitHub Actions, Jira, and Git workflows.

## 🚀 Features

- **Multi-Agent Architecture**: Coordinated execution of specialized agents (generator, reviewer, git handler, jira handler)
- **Language Agnostic**: Plugin-based architecture supporting Python, JavaScript/TypeScript, Go, Java, and more
- **Monorepo Support**: Configure multiple projects with different languages in a single repository
- **Quality Gates**: Automated testing, linting, and type checking before commits
- **Iterative Refinement**: Automatic code regeneration based on review feedback (up to configurable max iterations)
- **GitHub Integration**: Automatic PR creation as drafts with quality summaries
- **Jira Integration**: Fetch issue details and post status updates
- **Dry Run Mode**: Test execution without making Git/Jira changes

## 📋 Prerequisites

- Python 3.11+
- Git repository
- Anthropic API key (Claude access)
- GitHub Personal Access Token (for PR creation)
- Jira credentials (optional, for issue integration)

## 🛠️ Installation

1. **Clone the repository:**
```bash
git clone <repository-url>
cd custom-multiagent
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
export GITHUB_TOKEN="your-github-token"
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_TOKEN="your-jira-api-token"
```

4. **Configure projects** (optional):
Create project-specific configs in `config/projects/`:
```yaml
# config/projects/my-service.yaml
name: my-service
path: services/my-service
primary_language: python
languages: [python]

scopes:
  include:
    - services/my-service/**
  exclude:
    - services/my-service/build/**
```

## 🎯 Usage

### Command Line

**Basic usage with Jira issue:**
```bash
python scripts/run_agent.py --jira-key PROJ-123 --project my-service
```

**With custom task description:**
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --task "Add user authentication endpoint"
```

**Dry run (no Git/Jira operations):**
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --dry-run
```

**Specify project path directly:**
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project-path /path/to/project
```

**Override max iterations:**
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --max-iterations 5
```

### GitHub Actions

Trigger the workflow manually from GitHub:

1. Go to **Actions** → **Multi-Agent Code Generator**
2. Click **Run workflow**
3. Fill in:
   - Jira issue key (e.g., `PROJ-123`)
   - Project name (optional)
   - Task description (optional)
   - Dry run checkbox

The workflow will:
- Fetch Jira issue details
- Generate code iteratively until quality checks pass
- Create a branch and commit changes
- Open a draft PR with the `needs-approval` label
- Post a summary comment to the Jira issue
- Upload execution artifacts

## 🏗️ Architecture

### Agent Flow

```
1. JiraHandler → Fetch issue details
2. CodeGenerator → Generate code (Claude)
3. CodeReviewer → Run quality checks (lint/test/typecheck)
   ↓ If failed and iterations remain
   └→ CodeGenerator (with critique) → Regenerate
4. GitHandler → Branch, commit, push, create PR
5. JiraHandler → Post status comment
```

### Components

- **Orchestrator**: Coordinates agent execution sequentially
- **CodeGeneratorAgent**: Uses Claude to generate/update code based on task spec
- **CodeReviewerAgent**: Runs language-specific quality commands (tests, lint, typecheck)
- **GitHandlerAgent**: Manages Git operations (branch, commit, push, PR)
- **JiraHandlerAgent**: Fetches issues and posts comments
- **Language Plugins**: Provide language-specific summarization and quality commands

### Configuration

Global config: `config/agent.yaml`
- Model settings (model name, temperature, max tokens)
- Iteration limits
- PR settings (draft, labels)
- Language command mappings

Project config: `config/projects/<name>.yaml`
- Project paths and language
- Allowed/excluded file patterns
- Custom quality commands

## 🔧 Configuration

### Global Settings (`config/agent.yaml`)

```yaml
default_model: claude-3-5-sonnet-20241022
max_iterations: 3
max_tokens: 4096
temperature: 0.1

pr:
  draft: true
  reviewers_label: "needs-approval"
  branch_prefix: "feat"

languages:
  python:
    test: "pytest -q"
    lint: "ruff check ."
    typecheck: "mypy ."
  javascript:
    test: "npm test"
    lint: "eslint ."
```

### Project Settings

Create `config/projects/<project-name>.yaml`:

```yaml
name: inventory-service
path: services/inventory
primary_language: python

scopes:
  include:
    - services/inventory/**
  exclude:
    - services/inventory/build/**
    - services/inventory/__pycache__/**

jira:
  issue_prefix: INV
```

## 🧪 Testing

Run tests:
```bash
pytest tests/ -v
```

Run specific test:
```bash
pytest tests/test_code_generator.py -v
```

## 📊 Output & Artifacts

All execution artifacts are stored in `artifacts/`:
- `run_<timestamp>.log`: Structured JSONL logs
- `iteration_<n>/prompt.json`: Prompts sent to Claude
- `iteration_<n>/response.json`: Claude's responses
- `iteration_<n>/diff.patch`: Generated code diffs
- `iteration_<n>/quality_report.json`: Quality check results
- `summary.json`: Final execution summary

## 🔐 Security

- API keys and tokens stored as environment variables or GitHub secrets
- Path validation prevents directory traversal attacks
- File size limits prevent runaway generation
- Restricted patterns block sensitive files (.env, .git, etc.)
- Draft PRs require manual approval before merge

## 🚦 Quality Gates

Code must pass quality checks before proceeding:

**Hard Fail** (blocks or requires regeneration):
- Test failures
- Security issues flagged
- Critical lint errors

**Soft Fail** (proceeds with warnings):
- Style violations
- Non-critical lint issues

**Pass**:
- All checks successful or skipped

## 📝 Extending

### Adding a New Language Plugin

1. Create `language_plugins/<language>.py`:
```python
from language_plugins import LanguagePlugin, QualityCommand

class RustPlugin(LanguagePlugin):
    @property
    def name(self) -> str:
        return "rust"
    
    @property
    def extensions(self) -> list[str]:
        return [".rs"]
    
    def summarize(self, project_path, max_tokens=2000):
        # Implement project structure summarization
        pass
    
    def quality_commands(self, project_path):
        return [
            QualityCommand(name="test", command="cargo test"),
            QualityCommand(name="lint", command="cargo clippy"),
        ]
```

2. Register in `core/orchestrator.py`:
```python
from language_plugins.rust import RustPlugin

def _register_plugins(self):
    # ... existing plugins
    rust_config = self.config_loader.get_language_config("rust") or {}
    self.plugin_registry.register(RustPlugin(rust_config))
```

3. Add language config to `config/agent.yaml`:
```yaml
languages:
  rust:
    test: "cargo test"
    lint: "cargo clippy"
    format: "cargo fmt"
    extensions: [".rs"]
```

## 🐛 Troubleshooting

**Issue: "ANTHROPIC_API_KEY environment variable not set"**
- Solution: Export the API key in your shell or add to GitHub secrets

**Issue: "Could not detect project language"**
- Solution: Ensure language marker files exist (e.g., `pyproject.toml` for Python)

**Issue: "Path not allowed" for generated files**
- Solution: Check `allowed_paths` and `excluded_paths` in project config

**Issue: Quality checks timeout**
- Solution: Increase timeout in `code_reviewer.py` or optimize tests

**Issue: PR creation fails**
- Solution: Verify `GITHUB_TOKEN` has `contents:write` and `pull-requests:write` permissions

## 📚 Additional Documentation

- [Architecture Deep Dive](docs/ARCHITECTURE.md)
- [Plugin Development Guide](docs/PLUGINS.md)

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

[Add your license here]

## 🙏 Acknowledgments

- Anthropic Claude for code generation capabilities
- GitHub Actions for CI/CD automation
- Community contributors
