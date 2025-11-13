"""Orchestrator for coordinating multi-agent execution."""
import asyncio
from pathlib import Path
from typing import Any, Dict, Optional

from agents.code_generator import CodeGeneratorAgent
from agents.code_reviewer import CodeReviewerAgent
from agents.git_handler import GitHandlerAgent
from agents.jira_handler import JiraHandlerAgent
from core.config_loader import ConfigLoader
from core.context import Context
from core.events import EventDispatcher, EventType
from integrations.anthropic_client import AnthropicClient
from integrations.git_ops import GitClient, GitHubClient
from integrations.jira_client import JiraClient
from language_plugins import PluginRegistry
from language_plugins.python import PythonPlugin
from language_plugins.javascript import JavaScriptPlugin


class Orchestrator:
    """Coordinates execution of multiple agents in sequence."""
    
    def __init__(self, config_loader: ConfigLoader, dry_run: bool = False):
        """Initialize orchestrator.
        
        Args:
            config_loader: Configuration loader
            dry_run: If True, skip Git and Jira operations
        """
        self.config_loader = config_loader
        self.config = config_loader.config
        self.dry_run = dry_run
        
        # Event system
        self.event_dispatcher = EventDispatcher()
        
        # Initialize plugin registry
        self.plugin_registry = PluginRegistry()
        self._register_plugins()
        
        # Initialize clients
        self.anthropic_client = self._init_anthropic_client()
        self.jira_client = self._init_jira_client()
        
        # Agents will be initialized per execution
        self.agents: Dict[str, Any] = {}
    
    def _register_plugins(self) -> None:
        """Register language plugins."""
        # Python
        python_config = self.config_loader.get_language_config("python") or {}
        self.plugin_registry.register(PythonPlugin(python_config))
        
        # JavaScript/TypeScript
        js_config = self.config_loader.get_language_config("javascript") or {}
        self.plugin_registry.register(JavaScriptPlugin(js_config))
    
    def _init_anthropic_client(self) -> AnthropicClient:
        """Initialize Anthropic client."""
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY", "")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        
        model = self.config.get("default_model", "claude-3-5-sonnet-20241022")
        return AnthropicClient(api_key=api_key, model=model)
    
    def _init_jira_client(self) -> Optional[JiraClient]:
        """Initialize Jira client."""
        try:
            return JiraClient()
        except ValueError as e:
            print(f"Warning: Jira client not initialized: {e}")
            return None
    
    def _init_agents(self, context: Context) -> None:
        """Initialize agents for execution.
        
        Args:
            context: Execution context
        """
        # Get language plugin
        language_plugin = self.plugin_registry.get(context.primary_language)
        if not language_plugin:
            raise ValueError(f"No plugin found for language: {context.primary_language}")
        
        # Set project path for Anthropic client tools
        self.anthropic_client.set_project_path(context.project_path)
        
        # Initialize Git clients
        git_client = GitClient(context.project_path)
        
        github_client = None
        if not self.dry_run:
            try:
                github_client = GitHubClient()
            except ValueError:
                print("Warning: GitHub client not initialized (missing token)")
        
        # Create agents
        self.agents = {
            "jira": JiraHandlerAgent(
                name="JiraHandler",
                config=self.config,
                event_dispatcher=self.event_dispatcher,
                jira_client=self.jira_client,
            ) if self.jira_client else None,
            "generator": CodeGeneratorAgent(
                name="CodeGenerator",
                config=self.config,
                event_dispatcher=self.event_dispatcher,
                anthropic_client=self.anthropic_client,
            ),
            "reviewer": CodeReviewerAgent(
                name="CodeReviewer",
                config=self.config,
                event_dispatcher=self.event_dispatcher,
                language_plugin=language_plugin,
            ),
            "git": GitHandlerAgent(
                name="GitHandler",
                config=self.config,
                event_dispatcher=self.event_dispatcher,
                git_client=git_client,
                github_client=github_client,
            ),
        }
    
    async def execute(
        self,
        jira_key: str,
        project_name: str,
        project_path: Path,
        task_description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Execute orchestrated agent workflow.
        
        Args:
            jira_key: Jira issue key
            project_name: Project name
            project_path: Path to project
            task_description: Optional task description (fetched from Jira if not provided)
            
        Returns:
            Execution result dictionary
        """
        # Detect project language
        primary_language = self.config_loader.detect_project_language(project_path)
        if not primary_language:
            return {
                "success": False,
                "error": "Could not detect project language",
            }
        
        # Create context
        context = Context(
            jira_key=jira_key,
            task_description=task_description or "",
            project_name=project_name,
            project_path=project_path,
            primary_language=primary_language,
            allowed_paths=["**"],  # Allow all paths by default
            excluded_paths=[
                "**/.git/**",
                "**/node_modules/**",
                "**/__pycache__/**",
                "**/venv/**",
                "**/build/**",
                "**/dist/**",
            ],
            max_iterations=self.config.get("max_iterations", 3),
            dry_run=self.dry_run,
            model=self.config.get("default_model", "claude-3-5-sonnet-20241022"),
        )
        
        # Initialize agents
        self._init_agents(context)
        
        print(f"\n🤖 Starting multi-agent execution for {jira_key}")
        print(f"Project: {project_name} ({primary_language})")
        print(f"Max iterations: {context.max_iterations}")
        print(f"Dry run: {self.dry_run}\n")
        
        try:
            # Step 1: Fetch Jira issue
            if self.agents["jira"] and not task_description:
                print("📋 Fetching Jira issue...")
                result = await self.agents["jira"].execute(context, action="fetch")
                if not result["success"]:
                    return {"success": False, "error": f"Failed to fetch Jira issue: {result.get('error')}"}
                print(f"✓ Issue fetched: {context.task_description}\n")
            
            # Step 2: Iteration loop (generate -> review -> regenerate if needed)
            for iteration in range(1, context.max_iterations + 1):
                context.iteration = iteration
                print(f"🔄 Iteration {iteration}/{context.max_iterations}")
                
                # Generate code
                print("  ⚙️  Generating code...")
                gen_result = await self.agents["generator"].execute(context)
                if not gen_result["success"]:
                    return {"success": False, "error": f"Code generation failed: {gen_result.get('error')}"}
                print(f"  ✓ Generated {len(gen_result['files'])} files\n")
                
                # Review code
                print("  🔍 Reviewing code...")
                review_result = await self.agents["reviewer"].execute(context)
                if not review_result["success"]:
                    return {"success": False, "error": f"Code review failed: {review_result.get('error')}"}
                
                status = review_result["status"]
                print(f"  ✓ Review status: {status}\n")
                
                # Check if we should continue iterating
                if status == "pass":
                    print("✅ Quality checks passed!\n")
                    break
                elif status == "soft_fail" and iteration == context.max_iterations:
                    print("⚠️  Soft failures present, but max iterations reached. Proceeding...\n")
                    break
                elif status == "hard_fail" and iteration == context.max_iterations:
                    print("❌ Hard failures present and max iterations reached.\n")
                    # Still proceed to create PR for visibility
                    break
                else:
                    print(f"⚠️  Issues found, will retry (iteration {iteration + 1})\n")
                    # Continue to next iteration
            
            # Step 3: Git operations (branch, commit, push, PR)
            print("📦 Executing Git operations...")
            git_result = await self.agents["git"].execute(context)
            if not git_result["success"]:
                return {"success": False, "error": f"Git operations failed: {git_result.get('error')}"}
            
            if not self.dry_run:
                print(f"  ✓ Branch: {context.branch_name}")
                print(f"  ✓ Commit: {context.commit_sha[:8]}")
                if context.pr_url:
                    print(f"  ✓ Pull Request: {context.pr_url}\n")
            else:
                print("  ✓ Skipped (dry run)\n")
            
            # Step 4: Post Jira comment
            if self.agents["jira"] and not self.dry_run:
                print("💬 Posting Jira comment...")
                jira_result = await self.agents["jira"].execute(context, action="comment")
                if jira_result["success"]:
                    print("  ✓ Comment posted\n")
                else:
                    print(f"  ⚠️  Failed to post comment: {jira_result.get('error')}\n")
            
            # Success!
            print("✅ Multi-agent execution completed successfully!\n")
            
            return {
                "success": True,
                "context": context.to_dict(),
                "iterations": context.iteration,
                "final_status": context.current_iteration().status if context.current_iteration() else "unknown",
                "pr_url": context.pr_url,
                "branch": context.branch_name,
                "commit_sha": context.commit_sha,
            }
            
        except Exception as e:
            print(f"\n❌ Orchestration failed: {e}\n")
            return {
                "success": False,
                "error": str(e),
                "context": context.to_dict(),
            }
