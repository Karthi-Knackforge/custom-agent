#!/usr/bin/env python3
"""Test GitHub repository_dispatch webhook for Jira integration."""
import argparse
import os
import sys
from typing import Dict, Any

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def send_github_dispatch(
    owner: str,
    repo: str,
    event_type: str,
    issue_key: str,
    github_token: str,
    **extra_payload: Any
) -> bool:
    """Send a repository_dispatch event to GitHub.
    
    Args:
        owner: GitHub repository owner
        repo: GitHub repository name
        event_type: Event type (jira-issue-created, jira-issue-updated, etc.)
        issue_key: Jira issue key (e.g., CGCI-2)
        github_token: GitHub Personal Access Token
        **extra_payload: Additional payload data
        
    Returns:
        True if successful, False otherwise
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/dispatches"
    
    payload = {
        "event_type": event_type,
        "client_payload": {
            "issue_key": issue_key,
            "event_type": extra_payload.get("type", "Story"),
            "project_key": extra_payload.get("project_key", issue_key.split("-")[0]),
            "issue_type": extra_payload.get("issue_type", "Story"),
            "summary": extra_payload.get("summary", f"Test issue {issue_key}"),
            "assignee": extra_payload.get("assignee", "Test User"),
            "status": extra_payload.get("status", "To Do"),
            "priority": extra_payload.get("priority", "Medium"),
            "created": extra_payload.get("created", "2025-11-13T00:00:00.000Z"),
            "updated": extra_payload.get("updated", "2025-11-13T00:00:00.000Z")
        }
    }
    
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {github_token}",
        "X-GitHub-Api-Version": "2022-11-28",
        "Content-Type": "application/json"
    }
    
    print(f"📤 Sending webhook to GitHub...")
    print(f"   URL: {url}")
    print(f"   Event: {event_type}")
    print(f"   Issue: {issue_key}")
    print()
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 204:
            print("✅ Webhook sent successfully!")
            print()
            print("📋 Next steps:")
            print(f"   1. Go to https://github.com/{owner}/{repo}/actions")
            print("   2. Look for 'Jira Triggered Agent Execution' workflow")
            print("   3. You should see a new run starting")
            print()
            return True
        else:
            print(f"❌ Failed to send webhook: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            print()
            print("🔍 Troubleshooting:")
            print("   - Verify GITHUB_PAT has 'repo' and 'workflow' scopes")
            print("   - Check owner/repo names are correct")
            print("   - Ensure repository has Actions enabled")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error sending request: {e}")
        return False


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test GitHub repository_dispatch webhook for Jira integration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test with CGCI-2 issue
  python scripts/test_github_webhook.py --owner Karthi-Knackforge --repo cms-project --issue CGCI-2
  
  # Test with custom event type
  python scripts/test_github_webhook.py --owner myuser --repo myrepo --issue PROJ-123 --event jira-issue-updated
  
  # Test with additional details
  python scripts/test_github_webhook.py --owner myuser --repo myrepo --issue PROJ-123 \\
      --summary "Add authentication" --assignee "John Doe" --priority "High"

Environment Variables:
  GITHUB_PAT          GitHub Personal Access Token (required)
  GITHUB_OWNER        Default GitHub repository owner
  GITHUB_REPO         Default GitHub repository name
        """
    )
    
    parser.add_argument(
        "--owner",
        default=os.getenv("GITHUB_OWNER", ""),
        help="GitHub repository owner (or set GITHUB_OWNER env var)"
    )
    
    parser.add_argument(
        "--repo",
        default=os.getenv("GITHUB_REPO", ""),
        help="GitHub repository name (or set GITHUB_REPO env var)"
    )
    
    parser.add_argument(
        "--issue",
        required=True,
        help="Jira issue key (e.g., CGCI-2)"
    )
    
    parser.add_argument(
        "--event",
        default="jira-issue-created",
        choices=["jira-issue-created", "jira-issue-updated", "jira-issue-transition"],
        help="Event type (default: jira-issue-created)"
    )
    
    parser.add_argument(
        "--summary",
        help="Issue summary/title"
    )
    
    parser.add_argument(
        "--assignee",
        help="Issue assignee name"
    )
    
    parser.add_argument(
        "--priority",
        choices=["Highest", "High", "Medium", "Low", "Lowest"],
        help="Issue priority"
    )
    
    parser.add_argument(
        "--issue-type",
        choices=["Story", "Task", "Bug", "Epic"],
        help="Issue type"
    )
    
    args = parser.parse_args()
    
    # Get GitHub PAT from environment
    github_token = os.getenv("GITHUB_PAT", "")
    
    if not github_token:
        print("❌ Error: GITHUB_PAT environment variable not set")
        print()
        print("To create a GitHub Personal Access Token:")
        print("  1. Go to https://github.com/settings/tokens")
        print("  2. Click 'Generate new token (classic)'")
        print("  3. Select scopes: 'repo' and 'workflow'")
        print("  4. Generate and copy the token")
        print("  5. Set environment variable: export GITHUB_PAT='your_token'")
        sys.exit(1)
    
    if not args.owner:
        print("❌ Error: GitHub owner not specified")
        print("   Use --owner or set GITHUB_OWNER environment variable")
        sys.exit(1)
    
    if not args.repo:
        print("❌ Error: GitHub repo not specified")
        print("   Use --repo or set GITHUB_REPO environment variable")
        sys.exit(1)
    
    # Build extra payload
    extra_payload: Dict[str, Any] = {}
    
    if args.summary:
        extra_payload["summary"] = args.summary
    if args.assignee:
        extra_payload["assignee"] = args.assignee
    if args.priority:
        extra_payload["priority"] = args.priority
    if args.issue_type:
        extra_payload["issue_type"] = args.issue_type
        extra_payload["type"] = args.issue_type
    
    # Send webhook
    success = send_github_dispatch(
        owner=args.owner,
        repo=args.repo,
        event_type=args.event,
        issue_key=args.issue,
        github_token=github_token,
        **extra_payload
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
