"""Git handler agent."""
from pathlib import Path
from typing import Any, Dict, Optional

from agents.base import Agent
from core.context import Context
from core.events import EventType
from integrations.git_ops import GitClient, GitHubClient


class GitHandlerAgent(Agent):
    """Agent responsible for Git operations."""
    
    def __init__(
        self,
        name: str,
        config: Dict[str, Any],
        event_dispatcher,
        git_client: GitClient,
        github_client: Optional[GitHubClient] = None,
    ):
        super().__init__(name, config, event_dispatcher)
        self.git_client = git_client
        self.github_client = github_client
    
    async def execute(self, context: Context) -> Dict[str, Any]:
        """Execute Git operations: branch, commit, push, create PR.
        
        Args:
            context: Execution context
            
        Returns:
            Result dictionary with Git operation details
        """
        if context.dry_run:
            self.log_info("Dry run mode: skipping Git operations")
            return {"success": True, "dry_run": True}
        
        try:
            # Create branch
            branch_name = self._create_branch(context)
            context.branch_name = branch_name
            
            # Stage and commit changes
            commit_sha = self._commit_changes(context)
            context.commit_sha = commit_sha
            
            # Push to remote
            self._push_branch(context)
            
            # Create PR if GitHub client is available
            if self.github_client:
                pr_info = self._create_pull_request(context)
                context.pr_url = pr_info.get("url")
                context.pr_number = pr_info.get("number")
            
            return {
                "success": True,
                "branch": branch_name,
                "commit_sha": commit_sha,
                "pr_url": context.pr_url,
                "pr_number": context.pr_number,
            }
            
        except Exception as e:
            self.log_error("Git operation failed", error=e)
            self.emit_event(EventType.GIT_OPERATION_FAILED, {
                "error": str(e),
            })
            return {"success": False, "error": str(e)}
    
    def _create_branch(self, context: Context) -> str:
        """Create a new branch for changes.
        
        Args:
            context: Execution context
            
        Returns:
            Branch name
        """
        # Generate branch name
        branch_prefix = self.config.get("pr", {}).get("branch_prefix", "feat")
        jira_key_slug = context.jira_key.lower().replace("-", "_")
        branch_name = f"{branch_prefix}/{jira_key_slug}"
        
        # Check if branch exists
        if self.git_client.branch_exists(branch_name):
            # Append iteration number
            branch_name = f"{branch_name}_v{context.iteration}"
        
        self.log_info(f"Creating branch: {branch_name}")
        self.git_client.create_branch(branch_name)
        
        self.emit_event(EventType.GIT_BRANCH_CREATED, {
            "branch": branch_name,
        })
        
        return branch_name
    
    def _commit_changes(self, context: Context) -> str:
        """Stage and commit changes.
        
        Args:
            context: Execution context
            
        Returns:
            Commit SHA
        """
        current_iteration = context.current_iteration()
        if not current_iteration:
            raise ValueError("No current iteration")
        
        # Collect file paths
        file_paths = [f.path for f in current_iteration.generated_files]
        
        # Write files to disk
        for file_change in current_iteration.generated_files:
            file_path = context.project_path / file_change.path
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(file_change.content)
        
        # Stage files
        self.log_info(f"Staging {len(file_paths)} files")
        self.git_client.stage_files(file_paths)
        
        # Generate commit message
        commit_message = self._generate_commit_message(context)
        
        # Commit
        self.log_info(f"Committing changes: {commit_message}")
        commit_sha = self.git_client.commit(commit_message)
        
        self.emit_event(EventType.GIT_COMMIT_CREATED, {
            "commit_sha": commit_sha,
            "file_count": len(file_paths),
        })
        
        return commit_sha
    
    def _push_branch(self, context: Context) -> None:
        """Push branch to remote.
        
        Args:
            context: Execution context
        """
        if not context.branch_name:
            raise ValueError("No branch name")
        
        self.log_info(f"Pushing branch: {context.branch_name}")
        self.git_client.push(context.branch_name)
    
    def _create_pull_request(self, context: Context) -> Dict[str, Any]:
        """Create a pull request on GitHub.
        
        Args:
            context: Execution context
            
        Returns:
            Dictionary with PR details
        """
        if not self.github_client:
            return {}
        
        # Extract repo info from git remote
        repo_info = self._get_repo_info()
        
        # Generate PR title and body
        pr_title = f"[{context.jira_key}] {context.task_description[:80]}"
        pr_body = self._generate_pr_body(context)
        
        # Create PR
        self.log_info("Creating pull request")
        
        draft = self.config.get("pr", {}).get("draft", True)
        
        pr_info = self.github_client.create_pull_request(
            owner=repo_info["owner"],
            repo=repo_info["repo"],
            title=pr_title,
            body=pr_body,
            head=context.branch_name,
            base="main",  # TODO: Make configurable
            draft=draft,
        )
        
        # Add label
        label = self.config.get("pr", {}).get("reviewers_label", "needs-approval")
        if label:
            self.github_client.add_label_to_pr(
                owner=repo_info["owner"],
                repo=repo_info["repo"],
                pr_number=pr_info["number"],
                labels=[label],
            )
        
        self.emit_event(EventType.GIT_PR_CREATED, {
            "pr_number": pr_info["number"],
            "pr_url": pr_info["url"],
        })
        
        return pr_info
    
    def _get_repo_info(self) -> Dict[str, str]:
        """Extract repository info from git remote.
        
        Returns:
            Dictionary with owner and repo
        """
        # Get remote URL
        remote_url = self.git_client.repo.remotes.origin.url
        
        # Parse GitHub URL
        # Supports: https://github.com/owner/repo.git or git@github.com:owner/repo.git
        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                # SSH format
                parts = remote_url.split(":")[-1].replace(".git", "").split("/")
            else:
                # HTTPS format
                parts = remote_url.split("github.com/")[-1].replace(".git", "").split("/")
            
            return {
                "owner": parts[0],
                "repo": parts[1] if len(parts) > 1 else parts[0],
            }
        
        raise ValueError(f"Could not parse GitHub repo from URL: {remote_url}")
    
    def _generate_commit_message(self, context: Context) -> str:
        """Generate commit message.
        
        Args:
            context: Execution context
            
        Returns:
            Commit message
        """
        current_iteration = context.current_iteration()
        file_count = len(current_iteration.generated_files) if current_iteration else 0
        
        message = f"{context.jira_key}: {context.task_description[:72]}\n\n"
        message += f"Generated by multi-agent system (iteration {context.iteration})\n"
        message += f"Files changed: {file_count}\n"
        
        return message
    
    def _generate_pr_body(self, context: Context) -> str:
        """Generate pull request body.
        
        Args:
            context: Execution context
            
        Returns:
            PR body markdown
        """
        current_iteration = context.current_iteration()
        
        body_parts = [
            f"## Jira Issue: {context.jira_key}\n",
            f"**Description:** {context.task_description}\n",
            f"\n### Generation Summary",
            f"- Iterations: {context.iteration}/{context.max_iterations}",
            f"- Quality Status: {current_iteration.status if current_iteration else 'unknown'}",
            f"- Files Changed: {len(current_iteration.generated_files) if current_iteration else 0}\n",
        ]
        
        # Add changed files
        if current_iteration and current_iteration.generated_files:
            body_parts.append("\n### Changed Files")
            for file_change in current_iteration.generated_files[:20]:  # Limit to 20
                body_parts.append(f"- `{file_change.path}`")
            
            if len(current_iteration.generated_files) > 20:
                remaining = len(current_iteration.generated_files) - 20
                body_parts.append(f"- ... and {remaining} more files")
        
        # Add quality results
        if current_iteration and current_iteration.quality_results:
            body_parts.append("\n### Quality Checks")
            for name, result in current_iteration.quality_results.items():
                status_emoji = "✅" if result.status == "pass" else "❌"
                body_parts.append(f"- {status_emoji} {name}: {result.status}")
        
        body_parts.append("\n---")
        body_parts.append("*This PR was automatically generated by the multi-agent system.*")
        body_parts.append("*Manual review and approval required before merge.*")
        
        return "\n".join(body_parts)
