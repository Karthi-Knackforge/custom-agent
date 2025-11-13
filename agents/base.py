"""Base agent interface."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from core.context import Context
from core.events import Event, EventDispatcher, EventType


class Agent(ABC):
    """Base class for all agents."""
    
    def __init__(self, name: str, config: Dict[str, Any], event_dispatcher: EventDispatcher):
        self.name = name
        self.config = config
        self.event_dispatcher = event_dispatcher
    
    @abstractmethod
    async def execute(self, context: Context) -> Dict[str, Any]:
        """Execute the agent's main task.
        
        Args:
            context: Current execution context
            
        Returns:
            Result dictionary with agent-specific outputs
        """
        pass
    
    def emit_event(self, event_type: EventType, payload: Dict[str, Any]) -> None:
        """Emit an event through the dispatcher.
        
        Args:
            event_type: Type of event to emit
            payload: Event payload data
        """
        event = Event(
            type=event_type,
            payload=payload,
            agent_name=self.name
        )
        self.event_dispatcher.dispatch(event)
    
    def log_info(self, message: str, **kwargs) -> None:
        """Log informational message."""
        print(f"[{self.name}] {message}", kwargs if kwargs else "")
    
    def log_error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """Log error message."""
        print(f"[{self.name}] ERROR: {message}", error, kwargs if kwargs else "")


class AgentResult:
    """Standardized result from agent execution."""
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data or {}
        self.error = error
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }
