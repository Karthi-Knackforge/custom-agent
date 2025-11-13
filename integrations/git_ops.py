"""Git operations wrapper using GitPython."""
import subprocess
from pathlib import Path
from typing import Optional

from git import Repo
from git.exc import GitCommandError


class GitClient:
    """Wrapper for Git operations."""
    
    def __init__(self, repo_path: Path):
        """Initialize Git client.
        
        Args:
            repo_path: Path to the git repository
        """
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
    
    def get_current_branch(self) -> str:
        """Get current branch name.
        
        Returns:
            Current branch name
        """
        return self.repo.active_branch.name
    
    def create_branch(self, branch_name: str, base_branch: Optional[str] = None) -> str:
        """Create and checkout a new branch.
        
        Args:
            branch_name: Name of the new branch
            base_branch: Base branch to create from (defaults to current)
            
        Returns:
            Created branch name
        """
        if base_branch:
            self.repo.git.checkout(base_branch)
        
        self.repo.git.checkout("-b", branch_name)
        return branch_name
    
    def stage_files(self, file_paths: list[str]) -> None:
        """Stage files for commit.
        
        Args:
            file_paths: List of file paths to stage
        """
        self.repo.index.add(file_paths)
    
    def commit(self, message: str, author_name: Optional[str] = None, author_email: Optional[str] = None) -> str:
        """Create a commit.
        
        Args:
            message: Commit message
            author_name: Optional author name
            author_email: Optional author email
            
        Returns:
            Commit SHA
        """
        if author_name and author_email:
            self.repo.index.commit(
                message,
                author=f"{author_name} <{author_email}>"
            )
        else:
            self.repo.index.commit(message)
        
        return self.repo.head.commit.hexsha
    
    def push(self, branch_name: str, remote: str = "origin", set_upstream: bool = True) -> None:
        """Push branch to remote.
        
        Args:
            branch_name: Branch name to push
            remote: Remote name (default: origin)
            set_upstream: Whether to set upstream tracking
        """
        if set_upstream:
            self.repo.git.push("--set-upstream", remote, branch_name)
        else:
            self.repo.git.push(remote, branch_name)
    
    def get_diff(self, staged: bool = True) -> str:
        """Get diff of changes.
        
        Args:
            staged: If True, get staged changes; if False, get unstaged
            
        Returns:
            Diff as string
        """
        if staged:
            return self.repo.git.diff("--cached")
        else:
            return self.repo.git.diff()
    
    def get_file_diff(self, file_path: str) -> str:
        """Get diff for a specific file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Diff as string
        """
        return self.repo.git.diff(file_path)
    
    def is_clean(self) -> bool:
        """Check if working directory is clean.
        
        Returns:
            True if no uncommitted changes
        """
        return not self.repo.is_dirty()
    
    def get_changed_files(self) -> list[str]:
        """Get list of changed files.
        
        Returns:
            List of changed file paths
        """
        return [item.a_path for item in self.repo.index.diff(None)]
    
    def branch_exists(self, branch_name: str) -> bool:
        """Check if a branch exists.
        
        Args:
            branch_name: Branch name to check
            
        Returns:
            True if branch exists
        """
        return branch_name in [b.name for b in self.repo.branches]


class GitHubClient:
    """Client for GitHub API operations (PR creation, etc.)."""
    
    def __init__(self, token: Optional[str] = None):
        """Initialize GitHub client.
        
        Args:
            token: GitHub personal access token
        """
        import os
        self.token = token or os.getenv("GITHUB_TOKEN", "")
        
        if not self.token:
            raise ValueError("GitHub token not configured")
        
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
    
    def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head: str,
        base: str,
        draft: bool = True,
    ) -> dict:
        """Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head: Head branch
            base: Base branch
            draft: Whether to create as draft
            
        Returns:
            Dictionary with PR details
        """
        import requests
        
        url = f"https://api.github.com/repos/{owner}/{repo}/pulls"
        
        payload = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": draft,
        }
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        
        data = response.json()
        
        return {
            "number": data.get("number"),
            "url": data.get("html_url"),
            "state": data.get("state"),
        }
    
    def add_label_to_pr(self, owner: str, repo: str, pr_number: int, labels: list[str]) -> None:
        """Add labels to a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            labels: List of label names
        """
        import requests
        
        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pr_number}/labels"
        
        payload = {"labels": labels}
        
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
