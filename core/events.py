"""Event system for inter-agent communication."""
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class EventType(str, Enum):
    """Event types for agent coordination."""
    
    # Lifecycle
    AGENT_STARTED = "agent_started"
    AGENT_COMPLETED = "agent_completed"
    AGENT_FAILED = "agent_failed"
    
    # Code Generation
    CODE_GENERATION_STARTED = "code_generation_started"
    CODE_GENERATED = "code_generated"
    CODE_GENERATION_FAILED = "code_generation_failed"
    
    # Code Review
    REVIEW_STARTED = "review_started"
    REVIEW_PASSED = "review_passed"
    REVIEW_SOFT_FAIL = "review_soft_fail"
    REVIEW_HARD_FAIL = "review_hard_fail"
    REVIEW_FAILED = "review_failed"
    
    # Git Operations
    GIT_BRANCH_CREATED = "git_branch_created"
    GIT_COMMIT_CREATED = "git_commit_created"
    GIT_PR_CREATED = "git_pr_created"
    GIT_OPERATION_FAILED = "git_operation_failed"
    
    # Jira Operations
    JIRA_ISSUE_FETCHED = "jira_issue_fetched"
    JIRA_COMMENT_POSTED = "jira_comment_posted"
    JIRA_OPERATION_FAILED = "jira_operation_failed"
    
    # Iteration
    ITERATION_STARTED = "iteration_started"
    ITERATION_COMPLETED = "iteration_completed"
    MAX_ITERATIONS_REACHED = "max_iterations_reached"


@dataclass
class Event:
    """Represents an event in the agent system."""
    
    type: EventType
    payload: Dict[str, Any]
    correlation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    agent_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for logging."""
        return {
            "type": self.type.value,
            "payload": self.payload,
            "correlation_id": self.correlation_id,
            "timestamp": self.timestamp,
            "agent_name": self.agent_name,
        }


class EventDispatcher:
    """Simple event dispatcher for agent coordination."""
    
    def __init__(self):
        self._handlers: Dict[EventType, List[Callable[[Event], None]]] = {}
        self._event_history: List[Event] = []
    
    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]) -> None:
        """Subscribe a handler to an event type."""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
    
    def dispatch(self, event: Event) -> None:
        """Dispatch an event to all subscribed handlers."""
        self._event_history.append(event)
        
        if event.type in self._handlers:
            for handler in self._handlers[event.type]:
                try:
                    handler(event)
                except Exception as e:
                    # Log but don't fail the entire dispatch
                    print(f"Handler error for {event.type}: {e}")
    
    def get_history(self, event_type: Optional[EventType] = None) -> List[Event]:
        """Get event history, optionally filtered by type."""
        if event_type:
            return [e for e in self._event_history if e.type == event_type]
        return self._event_history
    
    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
