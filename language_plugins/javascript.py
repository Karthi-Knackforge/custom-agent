"""JavaScript/TypeScript language plugin."""
import json
from pathlib import Path
from typing import Any, Dict, List

from language_plugins import LanguagePlugin, QualityCommand


class JavaScriptPlugin(LanguagePlugin):
    """Plugin for JavaScript/TypeScript language support."""
    
    @property
    def name(self) -> str:
        return "javascript"
    
    @property
    def extensions(self) -> List[str]:
        return [".js", ".jsx", ".ts", ".tsx"]
    
    def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
        """Summarize JavaScript/TypeScript project structure."""
        structure = {
            "files": [],
            "dependencies": {},
            "scripts": {},
        }
        
        # Check package.json
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json, "r") as f:
                    package_data = json.load(f)
                    structure["dependencies"] = package_data.get("dependencies", {})
                    structure["scripts"] = package_data.get("scripts", {})
            except Exception:
                pass
        
        # Find JS/TS files
        for ext in self.extensions:
            files = list(project_path.rglob(f"*{ext}"))[:30]
            for file in files:
                rel_path = str(file.relative_to(project_path))
                if "node_modules" not in rel_path:
                    structure["files"].append(rel_path)
        
        return structure
    
    def quality_commands(self, project_path: Path) -> List[QualityCommand]:
        """Get JavaScript/TypeScript quality check commands."""
        commands = []
        
        # Check if package.json exists
        package_json = project_path / "package.json"
        if not package_json.exists():
            return commands
        
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
        
        # Type check (if TypeScript)
        tsconfig = project_path / "tsconfig.json"
        if tsconfig.exists() and self.config.get("typecheck"):
            commands.append(QualityCommand(
                name="typecheck",
                command=self.config["typecheck"],
                working_dir=project_path,
                critical=False,
            ))
        
        return commands
