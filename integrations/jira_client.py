"""Jira API client for issue management."""
import os
from typing import Any, Dict, Optional

import requests


class JiraClient:
    """Client for Jira REST API operations."""
    
    def __init__(self, base_url: Optional[str] = None, email: Optional[str] = None, token: Optional[str] = None):
        """Initialize Jira client.
        
        Args:
            base_url: Jira instance base URL (e.g., https://company.atlassian.net)
            email: User email for authentication
            token: API token for authentication
        """
        self.base_url = (base_url or os.getenv("JIRA_BASE_URL", "")).rstrip("/")
        self.email = email or os.getenv("JIRA_EMAIL", "")
        self.token = token or os.getenv("JIRA_TOKEN", "")
        
        if not all([self.base_url, self.email, self.token]):
            raise ValueError("Jira credentials not fully configured")
        
        self.session = requests.Session()
        self.session.auth = (self.email, self.token)
        self.session.headers.update({"Content-Type": "application/json"})
    
    def get_issue(self, issue_key: str) -> Dict[str, Any]:
        """Fetch issue details by key.
        
        Args:
            issue_key: Jira issue key (e.g., "PROJ-123")
            
        Returns:
            Dictionary with issue details
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}"
        
        response = self.session.get(url)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract relevant fields
        fields = data.get("fields", {})
        
        return {
            "key": data.get("key"),
            "id": data.get("id"),
            "summary": fields.get("summary", ""),
            "description": fields.get("description", ""),
            "issue_type": fields.get("issuetype", {}).get("name", ""),
            "status": fields.get("status", {}).get("name", ""),
            "priority": fields.get("priority", {}).get("name", ""),
            "assignee": fields.get("assignee", {}).get("displayName", "Unassigned"),
            "reporter": fields.get("reporter", {}).get("displayName", ""),
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
        }
    
    def add_comment(self, issue_key: str, comment: str) -> Dict[str, Any]:
        """Add a comment to an issue.
        
        Args:
            issue_key: Jira issue key
            comment: Comment text (supports Jira markdown)
            
        Returns:
            Dictionary with comment details
        """
        url = f"{self.base_url}/rest/api/3/issue/{issue_key}/comment"
        
        payload = {
            "body": {
                "type": "doc",
                "version": 1,
                "content": [
                    {
                        "type": "paragraph",
                        "content": [
                            {
                                "type": "text",
                                "text": comment
                            }
                        ]
                    }
                ]
            }
        }
        
        response = self.session.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def search_issues(self, jql: str, max_results: int = 50) -> list[Dict[str, Any]]:
        """Search issues using JQL.
        
        Args:
            jql: JQL query string
            max_results: Maximum number of results
            
        Returns:
            List of issue dictionaries
        """
        url = f"{self.base_url}/rest/api/3/search"
        
        params = {
            "jql": jql,
            "maxResults": max_results,
            "fields": "summary,description,status,issuetype,priority",
        }
        
        response = self.session.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get("issues", [])
