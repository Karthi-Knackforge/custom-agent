"""Anthropic API client wrapper with retry logic."""
import json
import time
from typing import Any, Dict, List, Optional

import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class AnthropicClient:
    """Wrapper for Anthropic API with code generation and review capabilities."""
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key
            model: Model to use for generation
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.InternalServerError))
    )
    def generate_code(
        self,
        task_description: str,
        context: Dict[str, Any],
        constraints: Optional[List[str]] = None,
        iteration: int = 1,
        previous_critique: Optional[str] = None,
        max_tokens: int = 4096,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        """Generate code using Claude.
        
        Args:
            task_description: Description of the task
            context: Project context (structure, existing code, etc.)
            constraints: List of constraints (allowed paths, quality requirements, etc.)
            iteration: Current iteration number
            previous_critique: Critique from previous iteration (if any)
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Dictionary with 'files' list and optional 'notes'
        """
        # Build prompt
        system_prompt = self._build_system_prompt(context.get("language", "python"))
        user_prompt = self._build_generation_prompt(
            task_description=task_description,
            context=context,
            constraints=constraints or [],
            iteration=iteration,
            previous_critique=previous_critique,
        )
        
        # Call API
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        # Extract and parse response
        content = response.content[0].text
        result = self._parse_code_generation_response(content)
        
        return result
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.InternalServerError))
    )
    def review_code(
        self,
        diff: str,
        quality_results: Dict[str, Any],
        guidelines: Optional[List[str]] = None,
        max_tokens: int = 2048,
    ) -> Dict[str, Any]:
        """Review code changes using Claude.
        
        Args:
            diff: Unified diff of changes
            quality_results: Results from automated quality checks
            guidelines: Additional review guidelines
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with 'critique', 'severity', and 'suggestions'
        """
        system_prompt = "You are an expert code reviewer. Analyze code changes and provide constructive feedback."
        
        user_prompt = self._build_review_prompt(
            diff=diff,
            quality_results=quality_results,
            guidelines=guidelines or [],
        )
        
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=0.1,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )
        
        content = response.content[0].text
        result = self._parse_review_response(content)
        
        return result
    
    def _build_system_prompt(self, language: str) -> str:
        """Build system prompt for code generation."""
        base = """You are an expert software engineer. Generate clean, maintainable, and well-tested code.

Guidelines:
- Write production-quality code with proper error handling
- Include appropriate tests
- Follow language-specific best practices and style guides
- Add clear documentation and comments where needed
- Consider security and performance implications
- Output MUST be valid JSON with the exact structure specified"""
        
        language_specific = {
            "python": "\n- Use type hints\n- Follow PEP 8 style guide\n- Prefer f-strings for formatting",
            "javascript": "\n- Use modern ES6+ syntax\n- Follow ESLint recommendations\n- Handle promises properly",
            "typescript": "\n- Use strict TypeScript types\n- Avoid 'any' types\n- Follow ESLint recommendations",
        }
        
        return base + language_specific.get(language, "")
    
    def _build_generation_prompt(
        self,
        task_description: str,
        context: Dict[str, Any],
        constraints: List[str],
        iteration: int,
        previous_critique: Optional[str],
    ) -> str:
        """Build user prompt for code generation."""
        prompt_parts = [
            f"# Task\n{task_description}\n",
            f"\n# Iteration {iteration}",
        ]
        
        if previous_critique:
            prompt_parts.append(f"\n# Previous Review Feedback\n{previous_critique}\n")
        
        if context.get("project_structure"):
            prompt_parts.append(f"\n# Project Structure\n```json\n{json.dumps(context['project_structure'], indent=2)}\n```\n")
        
        if constraints:
            prompt_parts.append(f"\n# Constraints\n" + "\n".join(f"- {c}" for c in constraints) + "\n")
        
        prompt_parts.append("""
# Output Format
You MUST respond with ONLY a JSON object (no markdown, no explanations outside JSON) with this exact structure:
{
  "files": [
    {
      "path": "relative/path/to/file.ext",
      "content": "complete file content here"
    }
  ],
  "notes": "Brief explanation of changes"
}

Ensure paths are relative to the project root and within allowed directories.""")
        
        return "\n".join(prompt_parts)
    
    def _build_review_prompt(
        self,
        diff: str,
        quality_results: Dict[str, Any],
        guidelines: List[str],
    ) -> str:
        """Build user prompt for code review."""
        prompt_parts = [
            "# Code Changes\n```diff\n" + diff[:5000] + "\n```\n",
            f"\n# Automated Quality Check Results\n```json\n{json.dumps(quality_results, indent=2)}\n```\n",
        ]
        
        if guidelines:
            prompt_parts.append("\n# Additional Guidelines\n" + "\n".join(f"- {g}" for g in guidelines) + "\n")
        
        prompt_parts.append("""
# Output Format
Respond with a JSON object:
{
  "critique": "Detailed review comments",
  "severity": "pass|soft_fail|hard_fail",
  "suggestions": ["specific suggestion 1", "specific suggestion 2"]
}

Use 'hard_fail' only for critical issues (tests failing, security risks, breaking changes).
Use 'soft_fail' for style or minor issues.
Use 'pass' if changes are acceptable.""")
        
        return "\n".join(prompt_parts)
    
    def _parse_code_generation_response(self, content: str) -> Dict[str, Any]:
        """Parse code generation response and validate structure."""
        # Try to extract JSON from markdown code blocks if present
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback: try to find JSON object
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(content[start:end])
            else:
                raise ValueError("Could not parse JSON response from model")
        
        # Validate structure
        if "files" not in result:
            raise ValueError("Response missing 'files' field")
        
        if not isinstance(result["files"], list):
            raise ValueError("'files' field must be a list")
        
        for file in result["files"]:
            if "path" not in file or "content" not in file:
                raise ValueError("Each file must have 'path' and 'content' fields")
        
        return result
    
    def _parse_review_response(self, content: str) -> Dict[str, Any]:
        """Parse code review response."""
        # Similar extraction logic
        if "```json" in content:
            start = content.find("```json") + 7
            end = content.find("```", start)
            content = content[start:end].strip()
        elif "```" in content:
            start = content.find("```") + 3
            end = content.find("```", start)
            content = content[start:end].strip()
        
        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start != -1 and end > start:
                result = json.loads(content[start:end])
            else:
                # Fallback to plain text critique
                result = {
                    "critique": content,
                    "severity": "soft_fail",
                    "suggestions": [],
                }
        
        return result
