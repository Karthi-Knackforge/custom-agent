"""Language plugin interface and registry."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class QualityCommand:
    """Represents a quality check command."""
    
    name: str  # "lint", "test", "typecheck", "format"
    command: str
    working_dir: Optional[Path] = None
    critical: bool = True  # If False, failure is soft-fail


class LanguagePlugin(ABC):
    """Base class for language-specific plugins."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Language name."""
        pass
    
    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """File extensions for this language."""
        pass
    
    @abstractmethod
    def summarize(self, project_path: Path, max_tokens: int = 2000) -> Dict[str, Any]:
        """Summarize project structure for context.
        
        Args:
            project_path: Path to the project
            max_tokens: Maximum tokens to generate (approximate)
            
        Returns:
            Dictionary with structure summary
        """
        pass
    
    @abstractmethod
    def quality_commands(self, project_path: Path) -> List[QualityCommand]:
        """Get quality check commands for this language.
        
        Args:
            project_path: Path to the project
            
        Returns:
            List of quality commands to run
        """
        pass
    
    def post_process(self, file_path: Path, content: str) -> str:
        """Post-process generated file content.
        
        Args:
            file_path: Path to the file
            content: Generated content
            
        Returns:
            Post-processed content
        """
        # Default: no post-processing
        return content
    
    def build_context_fragments(self, project_path: Path, changed_paths: List[Path]) -> List[str]:
        """Build context fragments for changed files.
        
        Args:
            project_path: Path to the project
            changed_paths: List of paths being changed
            
        Returns:
            List of context strings
        """
        fragments = []
        for path in changed_paths:
            if path.exists():
                try:
                    content = path.read_text()
                    fragments.append(f"File: {path.relative_to(project_path)}\n```\n{content[:500]}...\n```")
                except Exception:
                    pass
        return fragments


class PluginRegistry:
    """Registry for language plugins."""
    
    def __init__(self):
        self._plugins: Dict[str, LanguagePlugin] = {}
    
    def register(self, plugin: LanguagePlugin) -> None:
        """Register a language plugin.
        
        Args:
            plugin: Plugin instance to register
        """
        self._plugins[plugin.name] = plugin
    
    def get(self, language: str) -> Optional[LanguagePlugin]:
        """Get plugin for a language.
        
        Args:
            language: Language name
            
        Returns:
            Plugin instance or None
        """
        return self._plugins.get(language)
    
    def list_languages(self) -> List[str]:
        """List all registered languages.
        
        Returns:
            List of language names
        """
        return list(self._plugins.keys())
