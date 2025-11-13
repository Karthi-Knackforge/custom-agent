# Project Structure Overview

## Complete File Tree

```
custom-multiagent/
├── .github/
│   └── workflows/
│       └── agent.yml                 # GitHub Actions workflow
├── .gitignore                        # Git ignore patterns
├── README.md                         # Main documentation
├── requirements.txt                  # Python dependencies
│
├── agents/                           # Agent implementations
│   ├── __init__.py
│   ├── base.py                       # Base agent class
│   ├── code_generator.py            # Code generation agent
│   ├── code_reviewer.py             # Code review agent
│   ├── git_handler.py               # Git operations agent
│   └── jira_handler.py              # Jira integration agent
│
├── core/                             # Core system modules
│   ├── __init__.py
│   ├── config_loader.py             # Configuration management
│   ├── context.py                   # Execution context
│   ├── events.py                    # Event system
│   └── orchestrator.py              # Main orchestration logic
│
├── integrations/                     # External service clients
│   ├── __init__.py
│   ├── anthropic_client.py          # Claude API wrapper
│   ├── git_ops.py                   # Git/GitHub operations
│   └── jira_client.py               # Jira API client
│
├── language_plugins/                 # Language-specific plugins
│   ├── __init__.py                  # Plugin interface
│   ├── python.py                    # Python language support
│   └── javascript.py                # JavaScript/TypeScript support
│
├── config/                           # Configuration files
│   ├── agent.yaml                   # Global configuration
│   └── projects/                    # Project-specific configs
│       └── example.yaml             # Example project config
│
├── prompts/                          # Prompt templates
│   └── system_base.txt              # Base system prompt
│
├── scripts/                          # Executable scripts
│   └── run_agent.py                 # Main CLI entry point
│
├── tests/                            # Test suite
│   ├── test_smoke.py                # Basic structure tests
│   ├── test_code_generator.py       # Generator tests
│   └── test_orchestrator.py         # Orchestrator tests
│
├── docs/                             # Documentation
│   ├── ARCHITECTURE.md              # Architecture deep dive
│   ├── PLUGINS.md                   # Plugin development guide
│   └── QUICKSTART.md                # Quick start guide
│
└── artifacts/                        # Runtime artifacts (gitignored)
    └── .gitkeep
```

## Key Components

### Agents (4 specialized agents)
1. **CodeGeneratorAgent**: Generates code using Claude
2. **CodeReviewerAgent**: Runs quality checks (tests, lint, typecheck)
3. **GitHandlerAgent**: Git operations (branch, commit, push, PR)
4. **JiraHandlerAgent**: Jira integration (fetch, comment)

### Core System
- **Orchestrator**: Coordinates agent execution sequentially
- **Context**: Shared state across agents
- **Events**: Pub-sub event system for observability
- **ConfigLoader**: Configuration management

### Integration Layer
- **AnthropicClient**: Claude API with retry logic
- **GitClient**: Git operations wrapper
- **GitHubClient**: GitHub API for PRs
- **JiraClient**: Jira REST API

### Language Plugins
- **PluginRegistry**: Plugin management
- **PythonPlugin**: Python project support
- **JavaScriptPlugin**: JS/TS project support

## Entry Points

### CLI
```bash
python scripts/run_agent.py --jira-key PROJ-123 --project my-service
```

### GitHub Actions
- Manual trigger via workflow dispatch
- Automatic on specific events (configurable)

### Programmatic
```python
from core.config_loader import ConfigLoader
from core.orchestrator import Orchestrator

config = ConfigLoader()
orchestrator = Orchestrator(config)
await orchestrator.execute(
    jira_key="PROJ-123",
    project_name="my-service",
    project_path=Path("/path/to/project")
)
```

## Configuration Files

### Global Config (`config/agent.yaml`)
- Model settings
- Iteration limits
- PR configuration
- Language command mappings

### Project Config (`config/projects/<name>.yaml`)
- Project path
- Language
- File scope (include/exclude)
- Custom quality commands

## Test Organization

- **test_smoke.py**: Basic structure validation
- **test_code_generator.py**: Generator unit tests
- **test_orchestrator.py**: Integration tests
- More tests can be added per component

## Documentation Structure

- **README.md**: Overview, installation, usage
- **docs/ARCHITECTURE.md**: Detailed system design
- **docs/PLUGINS.md**: Plugin development guide
- **docs/QUICKSTART.md**: Getting started in 5 minutes
- **docs/PROJECT_STRUCTURE.md**: This file

## Artifact Storage

Runtime artifacts stored in `artifacts/`:
- Execution logs (JSONL)
- Per-iteration prompts and responses
- Generated diffs
- Quality check reports
- Final summary

## Extensibility Points

1. **New Agents**: Inherit from `Agent` base class
2. **New Languages**: Implement `LanguagePlugin` interface
3. **New Events**: Add to `EventType` enum
4. **Custom Quality Checks**: Override in project config
5. **Prompt Templates**: Customize in `prompts/`

## Dependencies

### Core
- `anthropic`: Claude API client
- `GitPython`: Git operations
- `requests`: HTTP client
- `pyyaml`: YAML parsing

### Development
- `pytest`: Testing framework
- `ruff`: Python linting
- `mypy`: Type checking

### Optional
- `structlog`: Structured logging (future)
- `tenacity`: Retry logic
- `httpx`: Async HTTP (future)

## Environment Variables

Required:
- `ANTHROPIC_API_KEY`: Claude API access

Optional:
- `GITHUB_TOKEN`: PR creation
- `JIRA_BASE_URL`: Jira instance
- `JIRA_EMAIL`: Jira user
- `JIRA_TOKEN`: Jira API token

## Future Additions

Planned components:
- `agents/security_scanner.py`: SAST integration
- `agents/planner.py`: Task decomposition
- `language_plugins/go.py`: Go support
- `language_plugins/rust.py`: Rust support
- `integrations/vector_store.py`: Embeddings for large repos
- `core/metrics.py`: Observability metrics

## Getting Started

1. Install dependencies: `pip install -r requirements.txt`
2. Set environment variables
3. Run tests: `pytest tests/`
4. Try dry run: `python scripts/run_agent.py --dry-run ...`
5. Configure your project in `config/projects/`
6. Run on real project

## Support Resources

- README.md: Main documentation
- QUICKSTART.md: 5-minute setup
- ARCHITECTURE.md: Design details
- PLUGINS.md: Extend with new languages
- Test files: Usage examples
