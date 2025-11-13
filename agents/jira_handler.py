"""Jira handler agent."""
from typing import Any, Dict, Optional

from agents.base import Agent
from core.context import Context
from core.events import EventType
from integrations.jira_client import JiraClient


class JiraHandlerAgent(Agent):
    """Agent responsible for Jira operations."""
    
    def __init__(self, name: str, config: Dict[str, Any], event_dispatcher, jira_client: JiraClient):
        super().__init__(name, config, event_dispatcher)
        self.jira_client = jira_client
    
    async def execute(self, context: Context, action: str = "fetch") -> Dict[str, Any]:
        """Execute Jira operation.
        
        Args:
            context: Execution context
            action: Action to perform ("fetch" or "comment")
            
        Returns:
            Result dictionary
        """
        if action == "fetch":
            return await self._fetch_issue(context)
        elif action == "comment":
            return await self._post_comment(context)
        else:
            return {"success": False, "error": f"Unknown action: {action}"}
    
    async def _fetch_issue(self, context: Context) -> Dict[str, Any]:
        """Fetch Jira issue details.
        
        Args:
            context: Execution context
            
        Returns:
            Result with issue details
        """
        try:
            self.log_info(f"Fetching Jira issue: {context.jira_key}")
            
            issue = self.jira_client.get_issue(context.jira_key)
            
            # Update context with issue details
            if not context.task_description:
                context.task_description = issue.get("summary", "")
            
            self.emit_event(EventType.JIRA_ISSUE_FETCHED, {
                "jira_key": context.jira_key,
                "summary": issue.get("summary"),
                "status": issue.get("status"),
            })
            
            return {
                "success": True,
                "issue": issue,
            }
            
        except Exception as e:
            self.log_error("Failed to fetch Jira issue", error=e)
            self.emit_event(EventType.JIRA_OPERATION_FAILED, {
                "action": "fetch",
                "jira_key": context.jira_key,
                "error": str(e),
            })
            return {"success": False, "error": str(e)}
    
    async def _post_comment(self, context: Context) -> Dict[str, Any]:
        """Post comment to Jira issue.
        
        Args:
            context: Execution context
            
        Returns:
            Result dictionary
        """
        if context.dry_run:
            self.log_info("Dry run mode: skipping Jira comment")
            return {"success": True, "dry_run": True}
        
        try:
            # Generate comment text
            comment = self._generate_comment(context)
            
            self.log_info(f"Posting comment to Jira issue: {context.jira_key}")
            
            result = self.jira_client.add_comment(context.jira_key, comment)
            
            self.emit_event(EventType.JIRA_COMMENT_POSTED, {
                "jira_key": context.jira_key,
                "comment_id": result.get("id"),
            })
            
            return {
                "success": True,
                "comment_id": result.get("id"),
            }
            
        except Exception as e:
            self.log_error("Failed to post Jira comment", error=e)
            self.emit_event(EventType.JIRA_OPERATION_FAILED, {
                "action": "comment",
                "jira_key": context.jira_key,
                "error": str(e),
            })
            return {"success": False, "error": str(e)}
    
    def _generate_comment(self, context: Context) -> str:
        """Generate Jira comment text.
        
        Args:
            context: Execution context
            
        Returns:
            Comment markdown
        """
        current_iteration = context.current_iteration()
        
        lines = [
            "🤖 *Automated Agent Update*\n",
            f"*Jira Key:* {context.jira_key}",
        ]
        
        if context.pr_url:
            lines.append(f"*Pull Request:* {context.pr_url} (draft)")
        
        lines.append(f"*Iterations:* {context.iteration}/{context.max_iterations}")
        
        if current_iteration:
            lines.append(f"*Status:* Quality checks {current_iteration.status}")
            lines.append(f"*Files Changed:* {len(current_iteration.generated_files)}")
        
        # Add changed files summary
        if current_iteration and current_iteration.generated_files:
            lines.append("\n*Changed Files:*")
            for file_change in current_iteration.generated_files[:10]:
                lines.append(f"• {file_change.path}")
            
            if len(current_iteration.generated_files) > 10:
                remaining = len(current_iteration.generated_files) - 10
                lines.append(f"• ... and {remaining} more files")
        
        # Add quality results
        if current_iteration and current_iteration.quality_results:
            lines.append("\n*Quality Checks:*")
            for name, result in current_iteration.quality_results.items():
                status_icon = "✓" if result.status == "pass" else "✗"
                lines.append(f"• {status_icon} {name}: {result.status}")
        
        lines.append("\n*Next Action:* Human review and approval required.")
        
        return "\n".join(lines)
