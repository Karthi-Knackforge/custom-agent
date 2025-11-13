"""Code reviewer agent."""
import subprocess
from pathlib import Path
from typing import Any, Dict, List

from agents.base import Agent
from core.context import Context, QualityResult
from core.events import EventType
from language_plugins import LanguagePlugin, QualityCommand


class CodeReviewerAgent(Agent):
    """Agent responsible for reviewing generated code."""
    
    def __init__(self, name: str, config: Dict[str, Any], event_dispatcher, language_plugin: LanguagePlugin):
        super().__init__(name, config, event_dispatcher)
        self.language_plugin = language_plugin
    
    async def execute(self, context: Context) -> Dict[str, Any]:
        """Review generated code by running quality checks.
        
        Args:
            context: Execution context
            
        Returns:
            Result dictionary with quality check results
        """
        self.emit_event(EventType.REVIEW_STARTED, {
            "iteration": context.iteration,
        })
        
        try:
            current_iteration = context.current_iteration()
            if not current_iteration:
                return {"success": False, "error": "No current iteration"}
            
            # Get quality commands from language plugin
            commands = self.language_plugin.quality_commands(context.project_path)
            
            if not commands:
                self.log_info("No quality commands configured, skipping checks")
                current_iteration.status = "pass"
                self.emit_event(EventType.REVIEW_PASSED, {
                    "iteration": context.iteration,
                    "reason": "No quality checks configured",
                })
                return {"success": True, "status": "pass", "results": {}}
            
            # Run quality checks
            results = {}
            for command in commands:
                self.log_info(f"Running {command.name}: {command.command}")
                result = self._run_quality_command(command)
                results[command.name] = result
                current_iteration.quality_results[command.name] = result
            
            # Determine overall status
            overall_status = self._determine_overall_status(results)
            current_iteration.status = overall_status
            
            # Generate critique if not passing
            critique = None
            if overall_status != "pass":
                critique = self._generate_critique(results)
                current_iteration.critique = critique
            
            # Emit appropriate event
            if overall_status == "pass":
                self.emit_event(EventType.REVIEW_PASSED, {
                    "iteration": context.iteration,
                })
            elif overall_status == "soft_fail":
                self.emit_event(EventType.REVIEW_SOFT_FAIL, {
                    "iteration": context.iteration,
                    "critique": critique,
                })
            else:
                self.emit_event(EventType.REVIEW_HARD_FAIL, {
                    "iteration": context.iteration,
                    "critique": critique,
                })
            
            return {
                "success": True,
                "status": overall_status,
                "results": {k: v.status for k, v in results.items()},
                "critique": critique,
            }
            
        except Exception as e:
            self.log_error("Review failed", error=e)
            self.emit_event(EventType.REVIEW_FAILED, {
                "iteration": context.iteration,
                "error": str(e),
            })
            return {"success": False, "error": str(e)}
    
    def _run_quality_command(self, command: QualityCommand) -> QualityResult:
        """Run a single quality check command.
        
        Args:
            command: Quality command to run
            
        Returns:
            Quality result
        """
        import time
        
        start_time = time.time()
        
        try:
            # Run command
            result = subprocess.run(
                command.command,
                shell=True,
                cwd=command.working_dir or Path.cwd(),
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            # Determine status
            if result.returncode == 0:
                status = "pass"
            elif command.critical:
                status = "fail"
            else:
                status = "fail"  # Still fail, but will be soft_fail overall
            
            # Combine stdout and stderr
            output = result.stdout + result.stderr
            
            return QualityResult(
                command=command.command,
                status=status,
                exit_code=result.returncode,
                output=output[:5000],  # Truncate long output
                duration_ms=duration_ms,
            )
            
        except subprocess.TimeoutExpired:
            return QualityResult(
                command=command.command,
                status="error",
                exit_code=-1,
                output="Command timed out after 5 minutes",
                duration_ms=(time.time() - start_time) * 1000,
            )
        except Exception as e:
            return QualityResult(
                command=command.command,
                status="error",
                exit_code=-1,
                output=f"Error running command: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000,
            )
    
    def _determine_overall_status(self, results: Dict[str, QualityResult]) -> str:
        """Determine overall status from individual results.
        
        Args:
            results: Dictionary of quality results
            
        Returns:
            Overall status: "pass", "soft_fail", or "hard_fail"
        """
        if not results:
            return "pass"
        
        statuses = [r.status for r in results.values()]
        
        # Check for hard failures (critical commands)
        if "fail" in statuses or "error" in statuses:
            # Check if any critical command failed
            for result in results.values():
                if result.status in ["fail", "error"]:
                    # Determine if this is a critical failure
                    # For simplicity, test failures are critical, lint failures are not
                    if "test" in result.command.lower():
                        return "hard_fail"
            return "soft_fail"
        
        return "pass"
    
    def _generate_critique(self, results: Dict[str, QualityResult]) -> str:
        """Generate critique from quality check results.
        
        Args:
            results: Dictionary of quality results
            
        Returns:
            Critique text
        """
        critique_parts = ["Quality check failures:\n"]
        
        for name, result in results.items():
            if result.status in ["fail", "error"]:
                critique_parts.append(f"\n## {name.upper()}")
                critique_parts.append(f"Status: {result.status}")
                critique_parts.append(f"Exit code: {result.exit_code}")
                
                if result.output:
                    critique_parts.append(f"Output:\n```\n{result.output}\n```")
        
        critique_parts.append("\nPlease fix these issues and regenerate the code.")
        
        return "\n".join(critique_parts)
