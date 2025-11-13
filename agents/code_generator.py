"""Code generator agent."""
import json
from pathlib import Path
from typing import Any, Dict

from agents.base import Agent, AgentResult
from core.context import Context, FileChange, IterationState
from core.events import EventType
from integrations.anthropic_client import AnthropicClient


class CodeGeneratorAgent(Agent):
    """Agent responsible for generating code using Claude."""
    
    def __init__(self, name: str, config: Dict[str, Any], event_dispatcher, anthropic_client: AnthropicClient):
        super().__init__(name, config, event_dispatcher)
        self.anthropic_client = anthropic_client
    
    async def execute(self, context: Context) -> Dict[str, Any]:
        """Generate code based on task description and context.
        
        Args:
            context: Execution context
            
        Returns:
            Result dictionary with generated files
        """
        self.emit_event(EventType.CODE_GENERATION_STARTED, {
            "iteration": context.iteration,
            "jira_key": context.jira_key,
        })
        
        try:
            # Build context for generation
            generation_context = self._build_generation_context(context)
            
            # Get previous critique if not first iteration
            previous_critique = None
            if context.iteration > 1 and context.iterations:
                prev_iteration = context.iterations[-1]
                previous_critique = prev_iteration.critique
            
            # Build constraints
            constraints = self._build_constraints(context)
            
            # Generate code
            self.log_info(f"Generating code (iteration {context.iteration}/{context.max_iterations})")
            
            result = self.anthropic_client.generate_code(
                task_description=context.task_description,
                context=generation_context,
                constraints=constraints,
                iteration=context.iteration,
                previous_critique=previous_critique,
                max_tokens=self.config.get("max_tokens", 4096),
                temperature=self.config.get("temperature", 0.1),
            )
            
            # Validate and process generated files
            files = self._process_generated_files(result.get("files", []), context)
            
            # Create iteration state
            iteration_state = IterationState(
                iteration=context.iteration,
                generated_files=files,
                status="pending",
            )
            
            context.add_iteration(iteration_state)
            
            self.emit_event(EventType.CODE_GENERATED, {
                "iteration": context.iteration,
                "file_count": len(files),
                "notes": result.get("notes", ""),
            })
            
            return {
                "success": True,
                "files": files,
                "notes": result.get("notes", ""),
            }
            
        except Exception as e:
            self.log_error(f"Code generation failed", error=e)
            self.emit_event(EventType.CODE_GENERATION_FAILED, {
                "iteration": context.iteration,
                "error": str(e),
            })
            
            return {
                "success": False,
                "error": str(e),
            }
    
    def _build_generation_context(self, context: Context) -> Dict[str, Any]:
        """Build context dictionary for code generation.
        
        Args:
            context: Execution context
            
        Returns:
            Context dictionary for the model
        """
        gen_context = {
            "language": context.primary_language,
            "project_name": context.project_name,
            "jira_key": context.jira_key,
        }
        
        # Add project structure if available (would be populated by language plugin)
        # For now, this is a placeholder
        gen_context["project_structure"] = {
            "language": context.primary_language,
            "path": str(context.project_path),
        }
        
        return gen_context
    
    def _build_constraints(self, context: Context) -> list[str]:
        """Build list of constraints for code generation.
        
        Args:
            context: Execution context
            
        Returns:
            List of constraint strings
        """
        constraints = [
            f"Only modify files within: {', '.join(context.allowed_paths)}",
            f"Do not modify: {', '.join(context.excluded_paths)}",
            "All code must be production-ready with proper error handling",
            "Include tests for new functionality",
            f"Target language: {context.primary_language}",
        ]
        
        # Add iteration-specific constraints
        if context.iteration > 1:
            constraints.append("Address all issues from previous review")
        
        return constraints
    
    def _process_generated_files(self, files: list[Dict[str, Any]], context: Context) -> list[FileChange]:
        """Process and validate generated files.
        
        Args:
            files: List of file dictionaries from model
            context: Execution context
            
        Returns:
            List of validated FileChange objects
        """
        processed = []
        
        for file_data in files:
            path = file_data.get("path", "")
            content = file_data.get("content", "")
            
            # Validate path
            if not self._is_path_allowed(path, context):
                self.log_error(f"Path not allowed: {path}")
                continue
            
            # Check file size
            if len(content) > self.config.get("max_file_size", 204800):
                self.log_error(f"File too large: {path}")
                continue
            
            # Create file change
            file_change = FileChange(
                path=path,
                content=content,
                operation="create_or_update",
            )
            
            processed.append(file_change)
        
        return processed
    
    def _is_path_allowed(self, path: str, context: Context) -> bool:
        """Check if a file path is allowed.
        
        Args:
            path: File path to check
            context: Execution context
            
        Returns:
            True if path is allowed
        """
        # Check for path traversal
        if ".." in path or path.startswith("/"):
            return False
        
        # Check against excluded patterns
        for excluded in context.excluded_paths:
            if excluded in path:
                return False
        
        # Check against allowed patterns (if any specified)
        if context.allowed_paths and context.allowed_paths != ["**"]:
            # Simple prefix matching for now
            allowed = any(path.startswith(p.rstrip("*")) for p in context.allowed_paths)
            if not allowed:
                return False
        
        return True
