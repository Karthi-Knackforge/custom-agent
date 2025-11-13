"""Configuration loader for agent system."""
import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigLoader:
    """Loads and manages configuration from YAML files."""
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize config loader.
        
        Args:
            config_path: Path to the main config file (defaults to config/agent.yaml)
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "agent.yaml"
        
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self.project_configs: Dict[str, Dict[str, Any]] = {}
        
        self._load_main_config()
        self._load_project_configs()
    
    def _load_main_config(self) -> None:
        """Load main configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")
        
        with open(self.config_path, "r") as f:
            self.config = yaml.safe_load(f) or {}
    
    def _load_project_configs(self) -> None:
        """Load all project-specific configurations."""
        projects_dir = self.config_path.parent / "projects"
        
        if not projects_dir.exists():
            return
        
        for config_file in projects_dir.glob("*.yaml"):
            project_name = config_file.stem
            with open(config_file, "r") as f:
                self.project_configs[project_name] = yaml.safe_load(f) or {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.
        
        Args:
            key: Configuration key (e.g., "pr.draft")
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def get_project_config(self, project_name: str) -> Dict[str, Any]:
        """Get project-specific configuration merged with global config.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Merged configuration dictionary
        """
        project_config = self.project_configs.get(project_name, {})
        
        # Deep merge with global config (project config takes precedence)
        merged = self._deep_merge(self.config.copy(), project_config)
        return merged
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def get_language_config(self, language: str) -> Optional[Dict[str, Any]]:
        """Get language-specific configuration.
        
        Args:
            language: Language name (e.g., "python", "javascript")
            
        Returns:
            Language configuration or None
        """
        languages = self.config.get("languages", {})
        return languages.get(language)
    
    def detect_project_language(self, project_path: Path) -> Optional[str]:
        """Detect primary language of a project.
        
        Args:
            project_path: Path to the project
            
        Returns:
            Detected language or None
        """
        # Check for language-specific marker files
        markers = {
            "python": ["pyproject.toml", "setup.py", "requirements.txt"],
            "javascript": ["package.json"],
            "typescript": ["tsconfig.json"],
            "go": ["go.mod"],
            "java": ["pom.xml", "build.gradle"],
        }
        
        for language, files in markers.items():
            for marker in files:
                if (project_path / marker).exists():
                    return language
        
        return None
    
    def list_projects(self) -> list[str]:
        """List all configured projects.
        
        Returns:
            List of project names
        """
        return list(self.project_configs.keys())
