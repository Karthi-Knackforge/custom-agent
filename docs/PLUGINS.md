# Language Plugin Development Guide

## Overview

Language plugins provide language-specific functionality for the multi-agent system, including:
- Project structure summarization
- Quality check command definitions
- File post-processing (formatting)
- Context fragment generation

## Plugin Interface

### Base Class

```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List

from language_plugins import LanguagePlugin, QualityCommand

class MyLanguagePlugin(LanguagePlugin):
    """Plugin for MyLanguage support."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        # Initialize plugin-specific state
    
    @property
    def name(self) -> str:
        """Return language name (lowercase)."""
        return "mylanguage"
    
    @property
    def extensions(self) -> List[str]:
        """Return file extensions for this language."""
        return [".mylang", ".ml"]
    
    def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
        """Summarize project structure.
        
        Args:
            project_path: Path to project root
            max_tokens: Approximate token budget for summary
            
        Returns:
            Dictionary with structure information
        """
        # Implement summarization logic
        pass
    
    def quality_commands(self, project_path: Path) -> List[QualityCommand]:
        """Get quality check commands.
        
        Args:
            project_path: Path to project root
            
        Returns:
            List of QualityCommand objects
        """
        # Define quality checks
        pass
    
    def post_process(self, file_path: Path, content: str) -> str:
        """Post-process generated content (optional).
        
        Args:
            file_path: Path to the file
            content: Generated content
            
        Returns:
            Post-processed content
        """
        # Optional: apply formatting, fix imports, etc.
        return content
    
    def build_context_fragments(self, project_path: Path, changed_paths: List[Path]) -> List[str]:
        """Build context fragments for changed files (optional).
        
        Args:
            project_path: Path to project root
            changed_paths: List of paths being modified
            
        Returns:
            List of context strings
        """
        # Optional: extract relevant context from existing code
        return []
```

## Quality Commands

### QualityCommand Structure

```python
@dataclass
class QualityCommand:
    """Represents a quality check command."""
    
    name: str              # "lint", "test", "typecheck", "format"
    command: str           # Shell command to execute
    working_dir: Optional[Path] = None  # Working directory
    critical: bool = True  # If False, failure is soft-fail
```

### Command Types

1. **test**: Run automated tests
   - Critical: Yes (failure blocks progress)
   - Example: `pytest -q`, `npm test`, `cargo test`

2. **lint**: Static code analysis
   - Critical: No (soft fail)
   - Example: `ruff check .`, `eslint .`, `golangci-lint run`

3. **typecheck**: Type checking
   - Critical: No (soft fail)
   - Example: `mypy .`, `tsc --noEmit`

4. **format**: Code formatting (optional)
   - Critical: No
   - Example: `ruff format .`, `prettier --write .`, `gofmt -w .`

## Summarization Strategies

### Goals

- Provide compact representation of project structure
- Stay within token budget (~2000 tokens)
- Include essential information for code generation

### Approaches

#### 1. Signature Extraction (Recommended)

Extract function/class signatures without implementation:

**Python Example**:
```python
import ast

def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
    structure = {"classes": [], "functions": []}
    
    for py_file in project_path.rglob("*.py"):
        tree = ast.parse(py_file.read_text())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                structure["classes"].append({
                    "name": node.name,
                    "file": str(py_file.relative_to(project_path)),
                    "methods": [m.name for m in node.body if isinstance(m, ast.FunctionDef)]
                })
            elif isinstance(node, ast.FunctionDef):
                structure["functions"].append({
                    "name": node.name,
                    "file": str(py_file.relative_to(project_path)),
                })
    
    return structure
```

**JavaScript Example**:
```python
import json

def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
    structure = {"modules": [], "dependencies": {}}
    
    # Parse package.json
    package_json = project_path / "package.json"
    if package_json.exists():
        data = json.loads(package_json.read_text())
        structure["dependencies"] = data.get("dependencies", {})
        structure["scripts"] = data.get("scripts", {})
    
    # List main files
    for js_file in project_path.rglob("*.js"):
        if "node_modules" not in str(js_file):
            structure["modules"].append(str(js_file.relative_to(project_path)))
    
    return structure
```

#### 2. Dependency Graph

Extract imports/dependencies to understand relationships:

```python
def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
    imports = set()
    
    for file in project_path.rglob("*.py"):
        tree = ast.parse(file.read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module)
    
    return {
        "imports": sorted(list(imports))[:50],  # Limit to top 50
    }
```

#### 3. File Listing

Simple approach for small projects:

```python
def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
    files = []
    
    for ext in self.extensions:
        files.extend(project_path.rglob(f"*{ext}"))
    
    return {
        "files": [str(f.relative_to(project_path)) for f in files[:100]]
    }
```

### Token Budget Management

- Limit number of items returned (e.g., top 50 functions)
- Truncate long lists with ellipsis
- Prioritize recently modified files
- Use compact JSON format

## Example Plugins

### Go Plugin

```python
from language_plugins import LanguagePlugin, QualityCommand
from pathlib import Path
from typing import Any, Dict, List

class GoPlugin(LanguagePlugin):
    @property
    def name(self) -> str:
        return "go"
    
    @property
    def extensions(self) -> List[str]:
        return [".go"]
    
    def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
        structure = {"packages": [], "modules": []}
        
        # Check go.mod
        go_mod = project_path / "go.mod"
        if go_mod.exists():
            content = go_mod.read_text()
            structure["module"] = content.split("\n")[0].replace("module ", "")
        
        # List packages
        for go_file in project_path.rglob("*.go"):
            rel_path = str(go_file.relative_to(project_path))
            if "/vendor/" not in rel_path:
                structure["packages"].append(rel_path)
        
        return structure
    
    def quality_commands(self, project_path: Path) -> List[QualityCommand]:
        commands = []
        
        # Test
        commands.append(QualityCommand(
            name="test",
            command="go test ./...",
            working_dir=project_path,
            critical=True,
        ))
        
        # Lint
        commands.append(QualityCommand(
            name="lint",
            command="golangci-lint run",
            working_dir=project_path,
            critical=False,
        ))
        
        # Format check
        commands.append(QualityCommand(
            name="format",
            command="gofmt -l . | grep -v '^$' && exit 1 || exit 0",
            working_dir=project_path,
            critical=False,
        ))
        
        return commands
```

### Rust Plugin

```python
class RustPlugin(LanguagePlugin):
    @property
    def name(self) -> str:
        return "rust"
    
    @property
    def extensions(self) -> List[str]:
        return [".rs"]
    
    def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
        structure = {"crates": [], "dependencies": {}}
        
        # Parse Cargo.toml
        cargo_toml = project_path / "Cargo.toml"
        if cargo_toml.exists():
            import tomli  # or tomllib in Python 3.11+
            data = tomli.loads(cargo_toml.read_text())
            structure["package"] = data.get("package", {}).get("name")
            structure["dependencies"] = data.get("dependencies", {})
        
        # List source files
        for rs_file in project_path.rglob("*.rs"):
            if "/target/" not in str(rs_file):
                structure["crates"].append(str(rs_file.relative_to(project_path)))
        
        return structure
    
    def quality_commands(self, project_path: Path) -> List[QualityCommand]:
        return [
            QualityCommand(
                name="test",
                command="cargo test",
                working_dir=project_path,
                critical=True,
            ),
            QualityCommand(
                name="lint",
                command="cargo clippy -- -D warnings",
                working_dir=project_path,
                critical=False,
            ),
            QualityCommand(
                name="format",
                command="cargo fmt --check",
                working_dir=project_path,
                critical=False,
            ),
        ]
```

## Registration

### Add to Orchestrator

Edit `core/orchestrator.py`:

```python
from language_plugins.go import GoPlugin
from language_plugins.rust import RustPlugin

def _register_plugins(self) -> None:
    """Register language plugins."""
    # Existing plugins
    python_config = self.config_loader.get_language_config("python") or {}
    self.plugin_registry.register(PythonPlugin(python_config))
    
    # New plugins
    go_config = self.config_loader.get_language_config("go") or {}
    self.plugin_registry.register(GoPlugin(go_config))
    
    rust_config = self.config_loader.get_language_config("rust") or {}
    self.plugin_registry.register(RustPlugin(rust_config))
```

### Add to Configuration

Edit `config/agent.yaml`:

```yaml
languages:
  go:
    test: "go test ./..."
    lint: "golangci-lint run"
    format: "gofmt -w ."
    extensions: [".go"]
  
  rust:
    test: "cargo test"
    lint: "cargo clippy"
    format: "cargo fmt"
    extensions: [".rs"]
```

## Testing Plugins

### Unit Test Template

```python
import pytest
from pathlib import Path
from language_plugins.go import GoPlugin

@pytest.fixture
def go_project(tmp_path):
    """Create a minimal Go project."""
    project = tmp_path / "go-project"
    project.mkdir()
    
    # Create go.mod
    (project / "go.mod").write_text("module example.com/myapp\n\ngo 1.21")
    
    # Create main.go
    (project / "main.go").write_text("""
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
""")
    
    return project

def test_go_plugin_summarize(go_project):
    """Test Go plugin summarization."""
    plugin = GoPlugin(config={})
    
    summary = plugin.summarize(go_project)
    
    assert "module" in summary
    assert summary["module"] == "example.com/myapp"
    assert len(summary["packages"]) == 1
    assert "main.go" in summary["packages"][0]

def test_go_plugin_quality_commands(go_project):
    """Test Go plugin quality commands."""
    plugin = GoPlugin(config={
        "test": "go test ./...",
        "lint": "golangci-lint run",
    })
    
    commands = plugin.quality_commands(go_project)
    
    assert len(commands) >= 2
    assert any(cmd.name == "test" for cmd in commands)
    assert any(cmd.name == "lint" for cmd in commands)
    
    # Test command should be critical
    test_cmd = next(cmd for cmd in commands if cmd.name == "test")
    assert test_cmd.critical is True
```

## Best Practices

### 1. Error Handling

```python
def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
    try:
        # Parse project structure
        return self._parse_structure(project_path)
    except Exception as e:
        # Graceful degradation
        return {
            "error": str(e),
            "fallback": True,
            "files": [str(f) for f in project_path.rglob(f"*{self.extensions[0]}")][:20]
        }
```

### 2. Performance

- Limit file scanning (use glob patterns efficiently)
- Cache results if called multiple times
- Use lazy evaluation for large projects

```python
def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
    # Limit to first 100 files
    files = list(project_path.rglob("*.go"))[:100]
    
    # Process in batches
    for file in files:
        # ... process
        pass
```

### 3. Configuration

Use config for customization:

```python
def quality_commands(self, project_path: Path) -> List[QualityCommand]:
    commands = []
    
    # Use config or fallback to default
    test_cmd = self.config.get("test", "default test command")
    commands.append(QualityCommand(
        name="test",
        command=test_cmd,
        working_dir=project_path,
        critical=True,
    ))
    
    return commands
```

### 4. Language Detection

Help with auto-detection by checking marker files:

```python
@staticmethod
def detect(project_path: Path) -> bool:
    """Check if this plugin applies to the project."""
    return (project_path / "go.mod").exists()
```

Update `ConfigLoader.detect_project_language()`:

```python
def detect_project_language(self, project_path: Path) -> Optional[str]:
    if (project_path / "go.mod").exists():
        return "go"
    # ... other checks
```

## Common Pitfalls

1. **Token Overflow**: Don't return entire file contents
   - **Solution**: Extract signatures/metadata only

2. **Slow Summarization**: Scanning thousands of files
   - **Solution**: Limit file count, use caching

3. **Missing Dependencies**: Quality commands require tools
   - **Solution**: Document required tools, provide installation instructions

4. **Hard-Coded Paths**: Assuming specific directory structure
   - **Solution**: Use relative paths, detect project layout

5. **Non-Deterministic Output**: Random ordering, timestamps
   - **Solution**: Sort results, normalize output

## Additional Resources

- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [Tree-sitter (multi-language parsing)](https://tree-sitter.github.io/tree-sitter/)
- [Language Server Protocol](https://microsoft.github.io/language-server-protocol/)

## Support

For questions or issues:
1. Check existing plugin implementations in `language_plugins/`
2. Review unit tests in `tests/test_plugins_*.py`
3. Open an issue with your plugin design
