"""Tests for orchestrator."""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from core.orchestrator import Orchestrator
from core.config_loader import ConfigLoader


@pytest.fixture
def mock_config_loader(tmp_path):
    """Create mock config loader."""
    # Create minimal config file
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    config_file = config_dir / "agent.yaml"
    config_file.write_text("""
default_model: claude-3-5-sonnet-20241022
max_iterations: 2
max_tokens: 4096
temperature: 0.1

languages:
  python:
    test: "echo 'test pass'"
    lint: "echo 'lint pass'"

pr:
  draft: true
  reviewers_label: "needs-approval"
""")
    
    loader = ConfigLoader(config_file)
    return loader


@pytest.mark.asyncio
@patch('core.orchestrator.AnthropicClient')
@patch('core.orchestrator.JiraClient')
@patch('core.orchestrator.GitClient')
@patch('core.orchestrator.GitHubClient')
async def test_orchestrator_dry_run(
    mock_github,
    mock_git,
    mock_jira,
    mock_anthropic,
    mock_config_loader,
    tmp_path,
):
    """Test orchestrator in dry-run mode."""
    # Setup mocks
    mock_anthropic_instance = Mock()
    mock_anthropic.return_value = mock_anthropic_instance
    mock_anthropic_instance.generate_code.return_value = {
        "files": [
            {"path": "test.py", "content": "# test"}
        ],
        "notes": "Created test file"
    }
    
    # Create test project
    project_path = tmp_path / "test-project"
    project_path.mkdir()
    (project_path / "requirements.txt").touch()  # Marker for Python
    
    # Initialize git repo
    import subprocess
    subprocess.run(["git", "init"], cwd=project_path, check=True)
    subprocess.run(["git", "config", "user.name", "test"], cwd=project_path, check=True)
    subprocess.run(["git", "config", "user.email", "test@test.com"], cwd=project_path, check=True)
    
    # Create orchestrator
    orchestrator = Orchestrator(
        config_loader=mock_config_loader,
        dry_run=True,
    )
    
    # Mock environment variable
    with patch.dict('os.environ', {'ANTHROPIC_API_KEY': 'test-key'}):
        result = await orchestrator.execute(
            jira_key="TEST-123",
            project_name="test-project",
            project_path=project_path,
            task_description="Create a test file",
        )
    
    assert result["success"] is True
    assert result["iterations"] <= 2
