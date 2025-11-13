"""Python language plugin."""
import ast
from pathlib import Path
from typing import Any, Dict, List

from language_plugins import LanguagePlugin, QualityCommand


class PythonPlugin(LanguagePlugin):
    """Plugin for Python language support."""
    
    @property
    def name(self) -> str:
        return "python"
    
    @property
    def extensions(self) -> List[str]:
        return [".py"]
    
    def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
        """Summarize Python project structure."""
        structure = {
            "modules": [],
            "classes": [],
            "functions": [],
            "imports": set(),
        }
        
        # Find Python files
        py_files = list(project_path.rglob("*.py"))[:50]  # Limit to 50 files
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                tree = ast.parse(content)
                
                rel_path = str(py_file.relative_to(project_path))
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        structure["classes"].append({
                            "name": node.name,
                            "file": rel_path,
                            "line": node.lineno,
                        })
                    elif isinstance(node, ast.FunctionDef):
                        # Only top-level functions
                        if isinstance(node.parent if hasattr(node, 'parent') else None, ast.Module):
                            structure["functions"].append({
                                "name": node.name,
                                "file": rel_path,
                                "line": node.lineno,
                            })
                    elif isinstance(node, (ast.Import, ast.ImportFrom)):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                structure["imports"].add(alias.name)
                        elif isinstance(node, ast.ImportFrom) and node.module:
                            structure["imports"].add(node.module)
                
                structure["modules"].append(rel_path)
                
            except Exception:
                # Skip files that can't be parsed
                continue
        
        # Convert set to list for JSON serialization
        structure["imports"] = sorted(list(structure["imports"]))[:20]
        
        return structure
    
    def quality_commands(self, project_path: Path) -> List[QualityCommand]:
        """Get Python quality check commands."""
        commands = []
        
        # Test
        if self.config.get("test"):
            commands.append(QualityCommand(
                name="test",
                command=self.config["test"],
                working_dir=project_path,
                critical=True,
            ))
        
        # Lint
        if self.config.get("lint"):
            commands.append(QualityCommand(
                name="lint",
                command=self.config["lint"],
                working_dir=project_path,
                critical=False,
            ))
        
        # Type check
        if self.config.get("typecheck"):
            commands.append(QualityCommand(
                name="typecheck",
                command=self.config["typecheck"],
                working_dir=project_path,
                critical=False,
            ))
        
        return commands
    
    def post_process(self, file_path: Path, content: str) -> str:
        """Post-process Python file with formatting."""
        # Format command is optional
        if self.config.get("format"):
            # Note: Actual formatting would be done by the reviewer agent
            # This is just a hook for future formatting integration
            pass
        return content
