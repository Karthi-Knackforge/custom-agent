"""Context object for managing agent execution state."""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class QualityResult:
    """Result from a quality check (lint, test, typecheck)."""
    
    command: str
    status: str  # "pass", "fail", "skip", "error"
    exit_code: Optional[int] = None
    output: str = ""
    issues: List[Dict[str, Any]] = field(default_factory=list)
    duration_ms: Optional[float] = None


@dataclass
class FileChange:
    """Represents a file change."""
    
    path: str
    content: str
    operation: str = "create_or_update"  # "create_or_update", "delete"
    original_content: Optional[str] = None


@dataclass
class IterationState:
    """State for a single iteration."""
    
    iteration: int
    generated_files: List[FileChange] = field(default_factory=list)
    diff: Optional[str] = None
    quality_results: Dict[str, QualityResult] = field(default_factory=dict)
    critique: Optional[str] = None
    status: str = "pending"  # "pending", "pass", "soft_fail", "hard_fail"


@dataclass
class Context:
    """Execution context shared across agents."""
    
    # Input
    jira_key: str
    task_description: str
    project_name: str
    project_path: Path
    primary_language: str
    allowed_paths: List[str]
    excluded_paths: List[str]
    
    # State
    iteration: int = 1
    max_iterations: int = 3
    iterations: List[IterationState] = field(default_factory=list)
    
    # Outputs
    branch_name: Optional[str] = None
    commit_sha: Optional[str] = None
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    
    # Metadata
    correlation_id: Optional[str] = None
    dry_run: bool = False
    model: str = "claude-3-5-sonnet-20241022"
    
    def current_iteration(self) -> Optional[IterationState]:
        """Get current iteration state."""
        if self.iterations and len(self.iterations) >= self.iteration:
            return self.iterations[self.iteration - 1]
        return None
    
    def add_iteration(self, state: IterationState) -> None:
        """Add iteration state."""
        self.iterations.append(state)
    
    def overall_quality_status(self) -> str:
        """Determine overall quality status from current iteration."""
        current = self.current_iteration()
        if not current or not current.quality_results:
            return "pending"
        
        statuses = [r.status for r in current.quality_results.values()]
        if all(s == "pass" or s == "skip" for s in statuses):
            return "pass"
        elif any(s == "fail" for s in statuses):
            return "hard_fail"
        elif any(s == "error" for s in statuses):
            return "hard_fail"
        return "soft_fail"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary."""
        return {
            "jira_key": self.jira_key,
            "task_description": self.task_description,
            "project_name": self.project_name,
            "project_path": str(self.project_path),
            "primary_language": self.primary_language,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "branch_name": self.branch_name,
            "commit_sha": self.commit_sha,
            "pr_url": self.pr_url,
            "pr_number": self.pr_number,
            "dry_run": self.dry_run,
            "model": self.model,
        }
