# Setup Instructions

## ✅ Scaffolding Complete!

Your multi-agent system has been fully scaffolded and is ready for use.

## 📂 What Was Created

### Core Components (All Implemented)
- ✅ **4 Specialized Agents**: CodeGenerator, CodeReviewer, GitHandler, JiraHandler
- ✅ **Orchestrator**: Sequential coordination with iteration loop
- ✅ **Event System**: Pub-sub for observability
- ✅ **Context Manager**: Shared state across agents
- ✅ **Configuration Loader**: YAML-based config with project overrides

### Integration Layer (All Implemented)
- ✅ **Anthropic Client**: Claude API with retry logic and JSON validation
- ✅ **Git Client**: GitPython wrapper for Git operations
- ✅ **GitHub Client**: REST API for PR creation
- ✅ **Jira Client**: REST API for issue management

### Language Support (Extensible)
- ✅ **Python Plugin**: AST parsing, pytest/ruff/mypy
- ✅ **JavaScript Plugin**: package.json parsing, npm test/eslint
- ✅ **Plugin Interface**: Easy to add more languages

### Automation & CI/CD
- ✅ **CLI Script**: Full-featured command-line interface
- ✅ **GitHub Actions Workflow**: Manual trigger with parameters
- ✅ **Dry Run Mode**: Test without making changes

### Documentation (Comprehensive)
- ✅ **README.md**: Overview, features, usage
- ✅ **ARCHITECTURE.md**: Deep dive into design
- ✅ **PLUGINS.md**: Plugin development guide
- ✅ **QUICKSTART.md**: 5-minute setup guide
- ✅ **PROJECT_STRUCTURE.md**: File organization

### Testing
- ✅ **Unit Tests**: CodeGenerator tests
- ✅ **Integration Tests**: Orchestrator tests
- ✅ **Smoke Tests**: Structure validation

## 🚀 Next Steps

### 1. Install Dependencies

```bash
cd /Users/karthis/Public/Projects/custom-multiagent

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
# Required
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Optional (for full functionality)
export GITHUB_TOKEN="your-github-token"
export JIRA_BASE_URL="https://your-domain.atlassian.net"
export JIRA_EMAIL="your-email@example.com"
export JIRA_TOKEN="your-jira-api-token"
```

### 3. Run Tests (Verify Setup)

```bash
# Run all tests
pytest tests/ -v

# Run specific test
pytest tests/test_smoke.py -v
```

### 4. Try a Dry Run

```bash
python scripts/run_agent.py \
  --jira-key TEST-123 \
  --task "Create a simple calculator function" \
  --project-path . \
  --dry-run
```

### 5. Configure Your Project

Create a project config in `config/projects/`:

```yaml
# config/projects/your-project.yaml
name: your-project
path: path/to/your/project
primary_language: python

scopes:
  include:
    - path/to/your/project/**
  exclude:
    - path/to/your/project/build/**
```

### 6. Run on Real Project

```bash
python scripts/run_agent.py \
  --jira-key YOUR-123 \
  --project your-project
```

## 📖 Key Documentation

Start with these docs in order:

1. **QUICKSTART.md** - Get running in 5 minutes
2. **README.md** - Full feature overview
3. **ARCHITECTURE.md** - Understand the design
4. **PLUGINS.md** - Add new language support

## 🔧 Configuration

### Global Settings
Edit `config/agent.yaml` to customize:
- Model selection and parameters
- Iteration limits
- PR settings (draft, labels)
- Language command mappings

### Project Settings
Create `config/projects/<name>.yaml` for each project:
- Project path and language
- File scope (include/exclude patterns)
- Custom quality commands
- Jira prefix mapping

## 🧪 Testing

The system includes comprehensive tests:

```bash
# All tests
pytest tests/ -v

# Specific test files
pytest tests/test_code_generator.py -v
pytest tests/test_orchestrator.py -v
pytest tests/test_smoke.py -v

# With coverage
pytest tests/ --cov=. --cov-report=html
```

## 🤖 GitHub Actions

The workflow is ready to use:

1. Add secrets to your GitHub repository:
   - `ANTHROPIC_API_KEY`
   - `GITHUB_TOKEN` (optional, auto-provided in Actions)
   - `JIRA_BASE_URL`
   - `JIRA_EMAIL`
   - `JIRA_TOKEN`

2. Go to **Actions** → **Multi-Agent Code Generator**

3. Click **Run workflow** and fill in parameters

## 🎯 Usage Examples

### Basic Usage
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service
```

### With Custom Task
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --task "Add user authentication with JWT tokens" \
  --project-path ./services/auth
```

### Dry Run (Testing)
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --dry-run
```

### Max Iterations Override
```bash
python scripts/run_agent.py \
  --jira-key PROJ-123 \
  --project my-service \
  --max-iterations 5
```

## 🔍 Monitoring & Debugging

### Check Artifacts

After each run, check `artifacts/` directory:

```bash
ls -la artifacts/
```

You'll find:
- `run_<timestamp>.log` - Full execution log
- `iteration_N/prompt.json` - Prompts sent to Claude
- `iteration_N/response.json` - Claude responses
- `iteration_N/diff.patch` - Generated diffs
- `iteration_N/quality_report.json` - Test results
- `summary.json` - Final summary

### View Logs

```bash
# Latest run log
cat artifacts/run_*.log | tail -100

# Specific iteration prompt
cat artifacts/iteration_1/prompt.json | jq .
```

## 🛡️ Security Notes

- **Never commit API keys** - Use environment variables
- **Review all PRs** - Draft PRs require manual approval
- **Path validation** - System blocks traversal attacks
- **File size limits** - Default 200KB per file
- **Restricted patterns** - Blocks .env, .git, secrets/

## 🐛 Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

### "Could not detect project language"
Add a language marker file:
- Python: `requirements.txt` or `pyproject.toml`
- JS/TS: `package.json`

### "Tests failed"
Agent will iterate and fix. Max iterations reached = PR created anyway.

### Import errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

## 📦 File Counts

Your project now contains:

- **Core Files**: 14 Python modules
- **Agent Implementations**: 4 agents + base
- **Integration Clients**: 3 clients
- **Language Plugins**: 2 plugins + interface
- **Configuration**: 2 YAML files
- **Documentation**: 5 markdown files
- **Tests**: 3 test files
- **Scripts**: 1 CLI script
- **Workflow**: 1 GitHub Actions workflow

**Total: ~40 files, ~3500 lines of code**

## 🎓 Learning Path

1. **Start here**: `docs/QUICKSTART.md`
2. **Run dry-run**: Test without changes
3. **Read**: `docs/ARCHITECTURE.md` to understand flow
4. **Customize**: Edit configs for your project
5. **Extend**: Add new language plugin (see `docs/PLUGINS.md`)
6. **Deploy**: Set up GitHub Actions

## 🤝 Contributing

To extend the system:

1. **Add language support**: Implement `LanguagePlugin`
2. **Add agents**: Inherit from `Agent` base class
3. **Customize prompts**: Edit `prompts/system_base.txt`
4. **Add quality checks**: Define in project config

## 📞 Support

- **Documentation**: Check `docs/` folder
- **Examples**: Look at test files
- **Issues**: Check error logs in `artifacts/`
- **Debug**: Enable verbose logging

## ✨ Features Highlights

✅ Multi-language support (Python, JS/TS, extensible)  
✅ Monorepo ready (configure multiple projects)  
✅ Iterative refinement (auto-fix based on review)  
✅ Quality gates (tests, lint, typecheck)  
✅ Draft PRs (manual approval required)  
✅ Jira integration (fetch & comment)  
✅ Dry run mode (test safely)  
✅ Comprehensive logging & artifacts  
✅ GitHub Actions ready  
✅ Extensible architecture  

## 🎉 You're Ready!

The system is fully scaffolded and ready to use. Follow the steps above to:

1. Install dependencies
2. Set environment variables
3. Run your first agent execution

**Happy coding! 🚀**

---

For detailed information, see:
- 📘 [README.md](../README.md)
- 🏗️ [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- 🔌 [PLUGINS.md](docs/PLUGINS.md)
- ⚡ [QUICKSTART.md](docs/QUICKSTART.md)
