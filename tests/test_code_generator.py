"""Tests for code generator agent."""
import pytest
from unittest.mock import Mock, patch

from agents.code_generator import CodeGeneratorAgent
from core.context import Context, FileChange
from core.events import EventDispatcher, EventType
from pathlib import Path


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client."""
    client = Mock()
    client.generate_code.return_value = {
        "files": [
            {
                "path": "src/test.py",
                "content": "def test():\n    pass\n"
            }
        ],
        "notes": "Created test function"
    }
    return client


@pytest.fixture
def event_dispatcher():
    """Create event dispatcher."""
    return EventDispatcher()


@pytest.fixture
def context():
    """Create test context."""
    return Context(
        jira_key="TEST-123",
        task_description="Create a test function",
        project_name="test-project",
        project_path=Path("/tmp/test"),
        primary_language="python",
        allowed_paths=["src/**"],
        excluded_paths=["**/.git/**"],
        max_iterations=3,
    )


@pytest.mark.asyncio
async def test_code_generator_success(mock_anthropic_client, event_dispatcher, context):
    """Test successful code generation."""
    agent = CodeGeneratorAgent(
        name="TestGenerator",
        config={"max_tokens": 4096, "temperature": 0.1, "max_file_size": 204800},
        event_dispatcher=event_dispatcher,
        anthropic_client=mock_anthropic_client,
    )
    
    result = await agent.execute(context)
    
    assert result["success"] is True
    assert len(result["files"]) == 1
    assert result["files"][0].path == "src/test.py"
    
    # Check events were emitted
    events = event_dispatcher.get_history()
    event_types = [e.type for e in events]
    assert EventType.CODE_GENERATION_STARTED in event_types
    assert EventType.CODE_GENERATED in event_types


@pytest.mark.asyncio
async def test_code_generator_path_validation(mock_anthropic_client, event_dispatcher, context):
    """Test path validation rejects invalid paths."""
    # Mock client to return file outside allowed paths
    mock_anthropic_client.generate_code.return_value = {
        "files": [
            {
                "path": "../etc/passwd",  # Path traversal
                "content": "malicious"
            }
        ],
        "notes": "Malicious attempt"
    }
    
    agent = CodeGeneratorAgent(
        name="TestGenerator",
        config={"max_tokens": 4096, "temperature": 0.1, "max_file_size": 204800},
        event_dispatcher=event_dispatcher,
        anthropic_client=mock_anthropic_client,
    )
    
    result = await agent.execute(context)
    
    # Should succeed but filter out invalid files
    assert result["success"] is True
    assert len(result["files"]) == 0  # Invalid file filtered out
