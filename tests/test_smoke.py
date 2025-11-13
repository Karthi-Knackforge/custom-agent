"""Basic smoke tests to verify system structure."""
import pytest
from pathlib import Path


def test_directory_structure():
    """Verify all required directories exist."""
    base = Path(__file__).parent.parent
    
    required_dirs = [
        "agents",
        "core",
        "integrations",
        "language_plugins",
        "config",
        "scripts",
        "prompts",
        "docs",
        "tests",
    ]
    
    for dir_name in required_dirs:
        assert (base / dir_name).exists(), f"Missing directory: {dir_name}"


def test_config_files_exist():
    """Verify configuration files exist."""
    base = Path(__file__).parent.parent
    
    assert (base / "config" / "agent.yaml").exists()
    assert (base / "requirements.txt").exists()
    assert (base / "README.md").exists()


def test_can_import_modules():
    """Verify core modules can be imported."""
    from core import events, context, config_loader
    from agents import base
    from language_plugins import LanguagePlugin
    
    assert events is not None
    assert context is not None
    assert config_loader is not None
    assert base is not None
    assert LanguagePlugin is not None


def test_event_system():
    """Test basic event system functionality."""
    from core.events import EventDispatcher, Event, EventType
    
    dispatcher = EventDispatcher()
    events_received = []
    
    def handler(event):
        events_received.append(event)
    
    dispatcher.subscribe(EventType.CODE_GENERATED, handler)
    
    test_event = Event(
        type=EventType.CODE_GENERATED,
        payload={"test": "data"}
    )
    
    dispatcher.dispatch(test_event)
    
    assert len(events_received) == 1
    assert events_received[0].type == EventType.CODE_GENERATED


def test_config_loader():
    """Test configuration loader."""
    from core.config_loader import ConfigLoader
    from pathlib import Path
    
    base = Path(__file__).parent.parent
    config_path = base / "config" / "agent.yaml"
    
    loader = ConfigLoader(config_path)
    
    assert loader.get("default_model") is not None
    assert loader.get("max_iterations") == 3
    assert "python" in loader.config.get("languages", {})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
