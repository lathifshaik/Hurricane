"""
Code Assistant module for Hurricane AI Agent.
"""

import ast
import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from rich.console import Console
from rich.syntax import Syntax

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


class CodeAssistant:
    """Code generation and assistance module."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config):
        self.ollama_client = ollama_client
        self.config = config
    
    async def generate_code(
        self, 
        description: str, 
        language: str = "python",
        context: Optional[str] = None
    ) -> str:
        """Generate code based on description."""
        system_prompt = self._get_code_generation_prompt(language)
        
        prompt = f"""Generate {language} code for: {description}

Requirements:
- Follow {self.config.preferences.code_style} coding style
- Include proper error handling
- Add docstrings and comments
- Make it production-ready
- Only return the code, no explanations"""
        
        if context:
            prompt += f"\n\nContext/Existing code:\n{context}"
        
        code = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        # Clean up the generated code
        cleaned_code = self._clean_generated_code(code, language)
        
        if self.config.preferences.verbose:
            console.print(Panel(
                Syntax(cleaned_code, language, theme="monokai"),
                title=f"Generated {language.title()} Code",
                border_style="green"
            ))
        
        return cleaned_code
    
    async def debug_code(self, code: str, error: Optional[str] = None) -> str:
        """Debug code and provide fixes."""
        system_prompt = """You are Hurricane, an expert code debugger.
Analyze the code, identify issues, and provide clear fixes.
Return both the explanation and the corrected code."""
        
        prompt = f"Debug this code and fix any issues:\n\n```\n{code}\n```"
        if error:
            prompt += f"\n\nError message: {error}"
        
        prompt += "\n\nProvide:\n1. Explanation of issues found\n2. Corrected code\n3. Prevention tips"
        
        debug_result = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return debug_result
    
    async def refactor_code(self, code: str, style: str = "clean") -> str:
        """Refactor code according to specified style."""
        system_prompt = f"""You are Hurricane, an expert code refactorer.
Refactor the code to follow {style} coding practices.
Improve readability, maintainability, and performance."""
        
        style_guidelines = self._get_style_guidelines(style)
        
        prompt = f"""Refactor this code following {style} style guidelines:

{style_guidelines}

Code to refactor:
```
{code}
```

Return only the refactored code with improvements."""
        
        refactored_code = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._clean_generated_code(refactored_code)
    
    async def explain_code(self, code: str) -> str:
        """Explain what the code does."""
        system_prompt = """You are Hurricane, a code explanation expert.
Provide clear, comprehensive explanations of code functionality."""
        
        prompt = f"""Explain this code in detail:

```
{code}
```

Include:
1. Overall purpose
2. Key components and their roles
3. Data flow
4. Important algorithms or patterns used
5. Potential improvements"""
        
        explanation = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return explanation
    
    async def optimize_code(self, code: str, optimization_type: str = "performance") -> str:
        """Optimize code for performance, memory, or readability."""
        system_prompt = f"""You are Hurricane, a code optimization expert.
Optimize the code for {optimization_type} while maintaining functionality."""
        
        optimization_guidelines = self._get_optimization_guidelines(optimization_type)
        
        prompt = f"""Optimize this code for {optimization_type}:

Guidelines:
{optimization_guidelines}

Code to optimize:
```
{code}
```

Return the optimized code with comments explaining the improvements."""
        
        optimized_code = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._clean_generated_code(optimized_code)
    
    def _get_code_generation_prompt(self, language: str) -> str:
        """Get system prompt for code generation."""
        return f"""You are Hurricane, an expert {language} developer with years of experience.
Generate clean, well-documented, and production-ready code.
Follow best practices for {language} development.
Include appropriate error handling and type hints where applicable.
Write code that is maintainable, readable, and efficient."""
    
    def _get_style_guidelines(self, style: str) -> str:
        """Get style guidelines for refactoring."""
        guidelines = {
            "clean": """
- Use descriptive variable and function names
- Keep functions small and focused (single responsibility)
- Remove code duplication
- Add proper error handling
- Include docstrings and comments
- Follow PEP 8 (for Python) or language-specific conventions
            """,
            "minimal": """
- Remove unnecessary code and comments
- Use concise variable names
- Combine operations where possible
- Remove redundant imports and variables
- Keep only essential functionality
            """,
            "enterprise": """
- Add comprehensive error handling
- Include detailed logging
- Use design patterns where appropriate
- Add input validation
- Include type hints and documentation
- Follow enterprise coding standards
            """
        }
        return guidelines.get(style, guidelines["clean"])
    
    def _get_optimization_guidelines(self, optimization_type: str) -> str:
        """Get optimization guidelines."""
        guidelines = {
            "performance": """
- Use efficient algorithms and data structures
- Minimize loops and nested operations
- Cache frequently used values
- Use list comprehensions over loops (Python)
- Avoid unnecessary object creation
- Use appropriate built-in functions
            """,
            "memory": """
- Use generators instead of lists where possible
- Delete unused variables
- Use slots for classes (Python)
- Avoid storing large objects in memory
- Use memory-efficient data structures
            """,
            "readability": """
- Use clear variable and function names
- Add comments for complex logic
- Break down complex functions
- Use consistent formatting
- Remove dead code
            """
        }
        return guidelines.get(optimization_type, guidelines["performance"])
    
    def _clean_generated_code(self, code: str, language: str = "python") -> str:
        """Clean up generated code by removing markdown formatting."""
        # Remove markdown code blocks
        code = re.sub(r'```\w*\n?', '', code)
        code = re.sub(r'```', '', code)
        
        # Remove leading/trailing whitespace
        code = code.strip()
        
        # For Python, validate syntax
        if language.lower() == "python":
            try:
                ast.parse(code)
            except SyntaxError as e:
                console.print(f"[yellow]Warning: Generated code has syntax errors: {e}[/yellow]")
        
        return code
    
    async def generate_tests(self, code: str, test_framework: str = "pytest") -> str:
        """Generate unit tests for the given code."""
        system_prompt = f"""You are Hurricane, an expert in writing comprehensive unit tests.
Generate thorough {test_framework} tests for the provided code.
Include edge cases, error conditions, and positive/negative test cases."""
        
        prompt = f"""Generate {test_framework} unit tests for this code:

```
{code}
```

Include:
1. Test setup and teardown if needed
2. Positive test cases
3. Negative test cases and error conditions
4. Edge cases
5. Mock external dependencies if present
6. Clear test names and documentation"""
        
        tests = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._clean_generated_code(tests)
    
    async def review_code(self, code: str) -> str:
        """Perform a code review and provide feedback."""
        system_prompt = """You are Hurricane, a senior code reviewer.
Provide constructive feedback on code quality, best practices, and potential improvements."""
        
        prompt = f"""Review this code and provide feedback:

```
{code}
```

Evaluate:
1. Code quality and readability
2. Best practices adherence
3. Potential bugs or issues
4. Performance considerations
5. Security concerns
6. Suggestions for improvement"""
        
        review = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return review
