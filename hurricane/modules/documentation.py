"""
Documentation generation module for Hurricane AI Agent.
"""

import re
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


class DocumentationGenerator:
    """Documentation generation and management module."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config):
        self.ollama_client = ollama_client
        self.config = config
    
    async def generate_documentation(
        self, 
        code_or_project: str,
        doc_type: str = "readme",
        format_type: str = "markdown"
    ) -> str:
        """Generate documentation based on type and format."""
        doc_generators = {
            "readme": self._generate_readme,
            "api": self._generate_api_docs,
            "comments": self._generate_code_comments,
            "docstring": self._generate_docstrings,
            "changelog": self._generate_changelog,
            "contributing": self._generate_contributing_guide,
            "license": self._generate_license,
        }
        
        generator = doc_generators.get(doc_type, self._generate_readme)
        return await generator(code_or_project, format_type)
    
    async def _generate_readme(self, project_info: str, format_type: str) -> str:
        """Generate README documentation."""
        system_prompt = f"""You are Hurricane, a technical documentation expert.
Generate a comprehensive README.{format_type} file that is professional, clear, and engaging.
Include all necessary sections for a complete project documentation."""
        
        prompt = f"""Generate a comprehensive README in {format_type} format for this project:

{project_info}

Include these sections:
1. Project title and description
2. Features and capabilities
3. Installation instructions
4. Usage examples
5. API documentation (if applicable)
6. Configuration options
7. Contributing guidelines
8. License information
9. Contact/support information

Make it professional, clear, and user-friendly."""
        
        readme = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._format_documentation(readme, format_type)
    
    async def _generate_api_docs(self, code: str, format_type: str) -> str:
        """Generate API documentation."""
        system_prompt = f"""You are Hurricane, an API documentation specialist.
Generate comprehensive API documentation in {format_type} format.
Include endpoints, parameters, responses, and examples."""
        
        prompt = f"""Generate API documentation in {format_type} format for this code:

{code}

Include:
1. Overview of the API
2. Authentication (if applicable)
3. Endpoints with HTTP methods
4. Request/response parameters
5. Example requests and responses
6. Error codes and handling
7. Rate limiting (if applicable)
8. SDK/client library information"""
        
        api_docs = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._format_documentation(api_docs, format_type)
    
    async def _generate_code_comments(self, code: str, format_type: str) -> str:
        """Generate inline code comments."""
        system_prompt = """You are Hurricane, a code documentation expert.
Add clear, concise, and helpful comments to the code.
Focus on explaining the 'why' not just the 'what'."""
        
        prompt = f"""Add comprehensive comments to this code:

{code}

Guidelines:
1. Add docstrings for functions and classes
2. Comment complex logic and algorithms
3. Explain business logic and decisions
4. Add TODO/FIXME comments where appropriate
5. Keep comments concise but informative
6. Follow language-specific comment conventions

Return the code with added comments."""
        
        commented_code = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return commented_code
    
    async def _generate_docstrings(self, code: str, format_type: str) -> str:
        """Generate docstrings for functions and classes."""
        system_prompt = """You are Hurricane, a docstring generation expert.
Generate comprehensive docstrings following standard conventions.
Include parameters, return values, exceptions, and examples."""
        
        prompt = f"""Add comprehensive docstrings to this code:

{code}

Follow these guidelines:
1. Use standard docstring format (Google, NumPy, or Sphinx style)
2. Document all parameters with types
3. Document return values
4. Document raised exceptions
5. Include usage examples where helpful
6. Keep docstrings clear and concise

Return the code with added docstrings."""
        
        documented_code = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return documented_code
    
    async def _generate_changelog(self, project_info: str, format_type: str) -> str:
        """Generate changelog documentation."""
        system_prompt = f"""You are Hurricane, a changelog documentation expert.
Generate a well-structured changelog in {format_type} format following semantic versioning."""
        
        prompt = f"""Generate a CHANGELOG.{format_type} for this project:

{project_info}

Follow these guidelines:
1. Use semantic versioning (MAJOR.MINOR.PATCH)
2. Group changes by type: Added, Changed, Deprecated, Removed, Fixed, Security
3. Include dates for each version
4. Write clear, concise descriptions
5. Link to relevant issues/PRs if applicable
6. Start with most recent version

Create a template with example entries."""
        
        changelog = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._format_documentation(changelog, format_type)
    
    async def _generate_contributing_guide(self, project_info: str, format_type: str) -> str:
        """Generate contributing guidelines."""
        system_prompt = f"""You are Hurricane, a project contribution expert.
Generate comprehensive contributing guidelines in {format_type} format."""
        
        prompt = f"""Generate CONTRIBUTING.{format_type} guidelines for this project:

{project_info}

Include:
1. How to get started contributing
2. Development setup instructions
3. Code style and standards
4. Testing requirements
5. Pull request process
6. Issue reporting guidelines
7. Code of conduct reference
8. Recognition for contributors

Make it welcoming and clear for new contributors."""
        
        contributing = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return self._format_documentation(contributing, format_type)
    
    async def _generate_license(self, project_info: str, format_type: str) -> str:
        """Generate license documentation."""
        system_prompt = """You are Hurricane, a legal documentation assistant.
Generate appropriate license information and explanations."""
        
        prompt = f"""Generate license documentation for this project:

{project_info}

Include:
1. Recommended license type (MIT, Apache 2.0, GPL, etc.) with reasoning
2. License text template
3. How to apply the license
4. Copyright notice template
5. Third-party license considerations
6. License compatibility information

Provide practical guidance for developers."""
        
        license_info = await self.ollama_client.generate_response(
            prompt, 
            system_prompt=system_prompt
        )
        
        return license_info
    
    def _format_documentation(self, content: str, format_type: str) -> str:
        """Format documentation according to specified format."""
        if format_type.lower() == "markdown":
            return self._format_markdown(content)
        elif format_type.lower() == "rst":
            return self._format_rst(content)
        elif format_type.lower() == "html":
            return self._format_html(content)
        else:
            return content
    
    def _format_markdown(self, content: str) -> str:
        """Format content as Markdown."""
        # Ensure proper markdown formatting
        content = re.sub(r'\n\n\n+', '\n\n', content)  # Remove excessive newlines
        content = re.sub(r'^#([^#\s])', r'# \1', content, flags=re.MULTILINE)  # Fix heading spacing
        return content.strip()
    
    def _format_rst(self, content: str) -> str:
        """Format content as reStructuredText."""
        # Convert markdown-style headers to RST
        content = re.sub(r'^# (.+)$', r'\1\n' + '=' * 50, content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'\1\n' + '-' * 30, content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'\1\n' + '^' * 20, content, flags=re.MULTILINE)
        return content.strip()
    
    def _format_html(self, content: str) -> str:
        """Format content as HTML."""
        # Basic markdown to HTML conversion
        content = re.sub(r'^# (.+)$', r'<h1>\1</h1>', content, flags=re.MULTILINE)
        content = re.sub(r'^## (.+)$', r'<h2>\1</h2>', content, flags=re.MULTILINE)
        content = re.sub(r'^### (.+)$', r'<h3>\1</h3>', content, flags=re.MULTILINE)
        content = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', content)
        content = re.sub(r'\*(.+?)\*', r'<em>\1</em>', content)
        content = re.sub(r'`(.+?)`', r'<code>\1</code>', content)
        return f"<html><body>{content}</body></html>"
    
    async def generate_project_docs(self, project_path: Path) -> Dict[str, str]:
        """Generate comprehensive documentation for an entire project."""
        docs = {}
        
        console.print("[blue]📚 Generating comprehensive project documentation...[/blue]")
        
        # Analyze project structure
        project_info = await self._analyze_project_structure(project_path)
        
        # Generate different types of documentation
        doc_types = ["readme", "api", "contributing", "changelog"]
        
        for doc_type in doc_types:
            try:
                console.print(f"[blue]  Generating {doc_type} documentation...[/blue]")
                docs[doc_type] = await self.generate_documentation(
                    project_info, 
                    doc_type, 
                    self.config.preferences.documentation_format
                )
            except Exception as e:
                console.print(f"[red]  Error generating {doc_type}: {e}[/red]")
                docs[doc_type] = f"Error generating {doc_type} documentation: {e}"
        
        return docs
    
    async def _analyze_project_structure(self, project_path: Path) -> str:
        """Analyze project structure to understand the codebase."""
        analysis = f"Project: {project_path.name}\n"
        analysis += f"Path: {project_path}\n"
        analysis += f"Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # Get file structure
        analysis += "File Structure:\n"
        for item in project_path.rglob("*"):
            if item.is_file() and not any(part.startswith('.') for part in item.parts):
                relative_path = item.relative_to(project_path)
                analysis += f"  {relative_path}\n"
        
        # Look for key files
        key_files = ["README.md", "setup.py", "requirements.txt", "package.json", "Cargo.toml"]
        analysis += "\nKey Files Found:\n"
        for key_file in key_files:
            if (project_path / key_file).exists():
                analysis += f"  ✓ {key_file}\n"
        
        return analysis
