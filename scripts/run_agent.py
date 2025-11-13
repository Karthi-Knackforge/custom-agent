"""CLI script for running the multi-agent system."""
import argparse
import asyncio
import sys
from pathlib import Path

Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.config_loader import config_loader
from core.orchestrator import Orchestrator


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Multi-agent code generation system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with Jira issue (fetches description from Jira)
  python scripts/run_agent.py --jira-key PROJ-123 --project my-service
  
  # Run with custom task description
  python scripts/run_agent.py --jira-key PROJ-123 --project my-service \\
      --task "Add user authentication"
  
  # Dry run (no Git/Jira operations)
  python scripts/run_agent.py --jira-key PROJ-123 --project my-service --dry-run
  
  # Specify project path
  python scripts/run_agent.py --jira-key PROJ-123 --project-path /path/to/project
        """
    )
    
    parser.add_argument(
        "--jira-key",
        required=True,
        help="Jira issue key (e.g., PROJ-123)",
    )
    
    parser.add_argument(
        "--project",
        help="Project name (from config/projects/)",
    )
    
    parser.add_argument(
        "--project-path",
        type=Path,
        help="Path to project (overrides project config)",
    )
    
    parser.add_argument(
        "--task",
        help="Task description (if not provided, fetched from Jira)",
    )
    
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to config file (default: config/agent.yaml)",
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode (skip Git and Jira operations)",
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        help="Maximum iterations (overrides config)",
    )
    
    return parser.parse_args()


def resolve_project_path(args, config_loader: ConfigLoader) -> tuple[str, Path]:
    """Resolve project name and path.
    
    Args:
        args: Parsed arguments
        config_loader: Config loader
        
    Returns:
        Tuple of (project_name, project_path)
    """
    # If project path is provided directly, use it
    if args.project_path:
        project_path = args.project_path.resolve()
        project_name = args.project or project_path.name
        return project_name, project_path
    
    # If project name is provided, look up config
    if args.project:
        project_config = config_loader.get_project_config(args.project)
        
        if "path" in project_config:
            project_path = Path(project_config["path"]).resolve()
            return args.project, project_path
        else:
            # Assume project is in current directory
            project_path = Path.cwd() / args.project
            if not project_path.exists():
                print(f"Error: Project path not found: {project_path}")
                sys.exit(1)
            return args.project, project_path
    
    # Default: use current directory
    project_path = Path.cwd()
    project_name = project_path.name
    return project_name, project_path


async def main():
    """Main entry point."""
    args = parse_args()
    
    # Load configuration
    config_path = args.config or Path(__file__).parent.parent / "config" / "agent.yaml"
    
    try:
        config_loader = ConfigLoader(config_path)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    # Override max iterations if specified
    if args.max_iterations:
        config_loader.config["max_iterations"] = args.max_iterations
    
    # Resolve project
    project_name, project_path = resolve_project_path(args, config_loader)
    
    if not project_path.exists():
        print(f"Error: Project path does not exist: {project_path}")
        sys.exit(1)
    
    print(f"Project: {project_name}")
    print(f"Path: {project_path}")
    print(f"Jira Key: {args.jira_key}")
    
    if args.dry_run:
        print("Mode: DRY RUN (Git and Jira operations will be skipped)")
    
    print()
    
    # Create orchestrator
    orchestrator = Orchestrator(
        config_loader=config_loader,
        dry_run=args.dry_run,
    )
    
    # Execute
    result = await orchestrator.execute(
        jira_key=args.jira_key,
        project_name=project_name,
        project_path=project_path,
        task_description=args.task,
    )
    
    # Print result
    if result["success"]:
        print("=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Status: SUCCESS")
        print(f"Iterations: {result.get('iterations', 'N/A')}")
        print(f"Final Status: {result.get('final_status', 'N/A')}")
        
        if result.get("branch"):
            print(f"Branch: {result['branch']}")
        
        if result.get("commit_sha"):
            print(f"Commit: {result['commit_sha'][:8]}")
        
        if result.get("pr_url"):
            print(f"Pull Request: {result['pr_url']}")
        
        print("=" * 60)
        sys.exit(0)
    else:
        print("=" * 60)
        print("EXECUTION FAILED")
        print("=" * 60)
        print(f"Error: {result.get('error', 'Unknown error')}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
