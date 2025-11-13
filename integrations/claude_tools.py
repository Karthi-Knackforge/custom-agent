"""Tool definitions and handlers for Claude function calling."""
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List


class ClaudeTools:
    """Provides tools that Claude can call during code generation."""
    
    def __init__(self, project_path: Path):
        """Initialize tools with project context.
        
        Args:
            project_path: Path to the project directory
        """
        self.project_path = Path(project_path)
    
    @staticmethod
    def get_tool_definitions() -> List[Dict[str, Any]]:
        """Get tool definitions for Claude API.
        
        Returns:
            List of tool definition dictionaries
        """
        return [
            {
                "name": "read_file",
                "description": "Read the contents of a file from the project. Use this to understand existing code before making changes.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to the file from project root (e.g., 'src/main.py')"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "list_directory",
                "description": "List files and directories in a given path. Use this to explore project structure.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Relative path to directory from project root (use '.' for root)"
                        }
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "search_code",
                "description": "Search for a pattern in the codebase using grep. Useful for finding function definitions, imports, etc.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Search pattern (supports regex)"
                        },
                        "file_pattern": {
                            "type": "string",
                            "description": "File pattern to search in (e.g., '*.py', '*.js')"
                        }
                    },
                    "required": ["pattern"]
                }
            },
            {
                "name": "run_command",
                "description": "Run a shell command in the project directory. Use for linting, testing, or checking project status.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Command to execute (e.g., 'pytest tests/', 'npm test')"
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in seconds (default: 30)"
                        }
                    },
                    "required": ["command"]
                }
            },
            {
                "name": "get_git_status",
                "description": "Get the current git status of the project, including changed files.",
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool and return the result.
        
        Args:
            tool_name: Name of the tool to execute
            tool_input: Input parameters for the tool
            
        Returns:
            Result dictionary with 'success' and 'result' or 'error'
        """
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "list_directory":
                return self._list_directory(tool_input["path"])
            elif tool_name == "search_code":
                return self._search_code(
                    tool_input["pattern"],
                    tool_input.get("file_pattern", "*")
                )
            elif tool_name == "run_command":
                return self._run_command(
                    tool_input["command"],
                    tool_input.get("timeout", 30)
                )
            elif tool_name == "get_git_status":
                return self._get_git_status()
            else:
                return {"success": False, "error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _read_file(self, path: str) -> Dict[str, Any]:
        """Read a file from the project."""
        file_path = self.project_path / path
        
        if not file_path.exists():
            return {"success": False, "error": f"File not found: {path}"}
        
        if not file_path.is_file():
            return {"success": False, "error": f"Not a file: {path}"}
        
        # Security: ensure file is within project
        try:
            file_path.resolve().relative_to(self.project_path.resolve())
        except ValueError:
            return {"success": False, "error": "Access denied: file outside project"}
        
        try:
            content = file_path.read_text(encoding="utf-8")
            return {"success": True, "content": content}
        except Exception as e:
            return {"success": False, "error": f"Failed to read file: {str(e)}"}
    
    def _list_directory(self, path: str) -> Dict[str, Any]:
        """List directory contents."""
        dir_path = self.project_path / path
        
        if not dir_path.exists():
            return {"success": False, "error": f"Directory not found: {path}"}
        
        if not dir_path.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}
        
        try:
            items = []
            for item in sorted(dir_path.iterdir()):
                items.append({
                    "name": item.name,
                    "type": "directory" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"success": True, "items": items}
        except Exception as e:
            return {"success": False, "error": f"Failed to list directory: {str(e)}"}
    
    def _search_code(self, pattern: str, file_pattern: str) -> Dict[str, Any]:
        """Search for pattern in codebase."""
        try:
            cmd = [
                "grep",
                "-rn",
                "--include", file_pattern,
                pattern,
                str(self.project_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            matches = []
            if result.stdout:
                for line in result.stdout.split("\n")[:50]:  # Limit results
                    if line:
                        matches.append(line)
            
            return {
                "success": True,
                "matches": matches,
                "count": len(matches)
            }
        except Exception as e:
            return {"success": False, "error": f"Search failed: {str(e)}"}
    
    def _run_command(self, command: str, timeout: int) -> Dict[str, Any]:
        """Run a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            
            return {
                "success": True,
                "exit_code": result.returncode,
                "stdout": result.stdout[:5000],  # Limit output
                "stderr": result.stderr[:5000]
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Command timed out after {timeout}s"}
        except Exception as e:
            return {"success": False, "error": f"Command failed: {str(e)}"}
    
    def _get_git_status(self) -> Dict[str, Any]:
        """Get git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            changed_files = []
            for line in result.stdout.split("\n"):
                if line:
                    status = line[:2]
                    file_path = line[3:]
                    changed_files.append({
                        "status": status.strip(),
                        "path": file_path
                    })
            
            return {
                "success": True,
                "changed_files": changed_files,
                "has_changes": len(changed_files) > 0
            }
        except Exception as e:
            return {"success": False, "error": f"Git status failed: {str(e)}"}
