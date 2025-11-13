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
    
    def _parse_adf_to_text(self, adf_content: Optional[Dict[str, Any]]) -> str:
        """Parse Atlassian Document Format to plain text.
        
        Args:
            adf_content: ADF content dictionary
            
        Returns:
            Plain text string
        """
        if not adf_content or not isinstance(adf_content, dict):
            return ""
        
        text_parts = []
        
        def extract_text(node: Dict[str, Any]) -> None:
            """Recursively extract text from ADF nodes."""
            if not isinstance(node, dict):
                return
            
            node_type = node.get("type", "")
            
            # Handle text nodes
            if node_type == "text":
                text_parts.append(node.get("text", ""))
            
            # Handle content array
            content = node.get("content", [])
            if isinstance(content, list):
                for child in content:
                    extract_text(child)
                    # Add newline after paragraphs
                    if child.get("type") == "paragraph":
                        text_parts.append("\n")
        
        extract_text(adf_content)
        return "".join(text_parts).strip()
    
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
        
        # Parse description from ADF format
        description_adf = fields.get("description")
        description = self._parse_adf_to_text(description_adf)
        
        # Safely get nested fields with defaults
        issuetype = fields.get("issuetype") or {}
        status = fields.get("status") or {}
        priority = fields.get("priority") or {}
        assignee = fields.get("assignee") or {}
        reporter = fields.get("reporter") or {}
        
        return {
            "key": data.get("key", ""),
            "id": data.get("id", ""),
            "summary": fields.get("summary", ""),
            "description": description,
            "issue_type": issuetype.get("name", ""),
            "status": status.get("name", ""),
            "priority": priority.get("name", ""),
            "assignee": assignee.get("displayName", "Unassigned"),
            "reporter": reporter.get("displayName", ""),
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
