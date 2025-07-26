"""
App Generator for Hurricane AI Agent.
Creates complete applications (web apps, games, etc.) in new directories with full context awareness.
"""

import asyncio
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.syntax import Syntax

from ..core.config import Config
from ..core.ollama_client import OllamaClient
from .project_planner import ProjectPlanner
from .web_search import WebSearchAssistant

console = Console()


@dataclass
class AppTemplate:
    """Template for different types of applications."""
    name: str
    description: str
    tech_stack: List[str]
    directory_structure: Dict[str, Any]
    required_files: List[str]
    dependencies: Dict[str, List[str]]  # package manager -> packages
    setup_commands: List[str]
    dev_commands: List[str]


class AppGenerator:
    """Generates complete applications in new directories with full context awareness."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, base_path: Path = None):
        self.ollama_client = ollama_client
        self.config = config
        self.base_path = base_path or Path.cwd()
        self.web_search = WebSearchAssistant(ollama_client, config)
        
        # App templates
        self.templates = {
            "react_landing": AppTemplate(
                name="React Landing Page",
                description="Modern React landing page with Tailwind CSS",
                tech_stack=["React", "Vite", "Tailwind CSS", "JavaScript"],
                directory_structure={
                    "src": {
                        "components": {},
                        "pages": {},
                        "styles": {},
                        "assets": {"images": {}}
                    },
                    "public": {}
                },
                required_files=[
                    "package.json", "vite.config.js", "tailwind.config.js", 
                    "src/App.jsx", "src/main.jsx", "src/index.css",
                    "src/components/Header.jsx", "src/components/Hero.jsx",
                    "src/components/Features.jsx", "src/components/Footer.jsx",
                    "index.html", "README.md"
                ],
                dependencies={
                    "npm": ["react", "react-dom", "vite", "@vitejs/plugin-react", "tailwindcss", "autoprefixer", "postcss"]
                },
                setup_commands=["npm install", "npx tailwindcss init -p"],
                dev_commands=["npm run dev"]
            ),
            "nextjs_app": AppTemplate(
                name="Next.js Web App",
                description="Full-stack Next.js application with modern features",
                tech_stack=["Next.js", "React", "TypeScript", "Tailwind CSS"],
                directory_structure={
                    "src": {
                        "app": {
                            "api": {},
                            "components": {},
                            "lib": {}
                        }
                    },
                    "public": {}
                },
                required_files=[
                    "package.json", "next.config.js", "tailwind.config.ts", "tsconfig.json",
                    "src/app/layout.tsx", "src/app/page.tsx", "src/app/globals.css",
                    "src/app/components/Header.tsx", "src/app/components/Footer.tsx",
                    "README.md"
                ],
                dependencies={
                    "npm": ["next", "react", "react-dom", "@types/node", "@types/react", "@types/react-dom", "typescript", "tailwindcss", "autoprefixer", "postcss"]
                },
                setup_commands=["npm install"],
                dev_commands=["npm run dev"]
            ),
            "python_game": AppTemplate(
                name="Python Game",
                description="2D game using Pygame with modern architecture",
                tech_stack=["Python", "Pygame", "Object-Oriented Design"],
                directory_structure={
                    "src": {
                        "game": {},
                        "entities": {},
                        "scenes": {},
                        "utils": {}
                    },
                    "assets": {
                        "images": {},
                        "sounds": {},
                        "fonts": {}
                    },
                    "tests": {}
                },
                required_files=[
                    "requirements.txt", "main.py", "src/game/game.py", "src/game/settings.py",
                    "src/entities/player.py", "src/entities/enemy.py",
                    "src/scenes/menu.py", "src/scenes/gameplay.py",
                    "src/utils/helpers.py", "README.md"
                ],
                dependencies={
                    "pip": ["pygame", "numpy", "pytest"]
                },
                setup_commands=["pip install -r requirements.txt"],
                dev_commands=["python main.py"]
            ),
            "express_api": AppTemplate(
                name="Express.js API",
                description="RESTful API with Express.js, MongoDB, and authentication",
                tech_stack=["Node.js", "Express.js", "MongoDB", "JWT"],
                directory_structure={
                    "src": {
                        "controllers": {},
                        "models": {},
                        "routes": {},
                        "middleware": {},
                        "utils": {}
                    },
                    "tests": {}
                },
                required_files=[
                    "package.json", "server.js", "src/app.js", "src/config/database.js",
                    "src/controllers/authController.js", "src/controllers/userController.js",
                    "src/models/User.js", "src/routes/auth.js", "src/routes/users.js",
                    "src/middleware/auth.js", ".env.example", "README.md"
                ],
                dependencies={
                    "npm": ["express", "mongoose", "bcryptjs", "jsonwebtoken", "cors", "dotenv", "helmet", "express-rate-limit"]
                },
                setup_commands=["npm install"],
                dev_commands=["npm run dev"]
            ),
            "flutter_app": AppTemplate(
                name="Flutter Mobile App",
                description="Cross-platform mobile app with Flutter",
                tech_stack=["Flutter", "Dart", "Material Design"],
                directory_structure={
                    "lib": {
                        "screens": {},
                        "widgets": {},
                        "models": {},
                        "services": {},
                        "utils": {}
                    },
                    "assets": {
                        "images": {},
                        "fonts": {}
                    },
                    "test": {}
                },
                required_files=[
                    "pubspec.yaml", "lib/main.dart", "lib/screens/home_screen.dart",
                    "lib/widgets/custom_button.dart", "lib/models/user.dart",
                    "lib/services/api_service.dart", "README.md"
                ],
                dependencies={
                    "flutter": ["http", "provider", "shared_preferences"]
                },
                setup_commands=["flutter pub get"],
                dev_commands=["flutter run"]
            )
        }
    
    async def detect_app_type(self, user_request: str) -> Optional[str]:
        """Detect what type of app the user wants to create."""
        user_request_lower = user_request.lower()
        
        # Direct matches
        if any(word in user_request_lower for word in ['landing page', 'landing', 'marketing site']):
            return "react_landing"
        elif any(word in user_request_lower for word in ['nextjs', 'next.js', 'full stack', 'web app']):
            return "nextjs_app"
        elif any(word in user_request_lower for word in ['game', 'pygame', 'python game']):
            return "python_game"
        elif any(word in user_request_lower for word in ['api', 'backend', 'express', 'rest api']):
            return "express_api"
        elif any(word in user_request_lower for word in ['mobile app', 'flutter', 'android', 'ios']):
            return "flutter_app"
        
        # Use AI to determine app type
        prompt = f"""Based on this user request, determine what type of application they want to create:

Request: "{user_request}"

Available app types:
1. react_landing - React landing page with Tailwind CSS
2. nextjs_app - Full-stack Next.js web application
3. python_game - 2D Python game with Pygame
4. express_api - RESTful API with Express.js and MongoDB
5. flutter_app - Cross-platform mobile app with Flutter

Respond with only the app type key (e.g., "react_landing") or "unknown" if unclear."""
        
        response = await self.ollama_client.generate_response(
            prompt,
            system_prompt="You are an expert at determining application types from user requests. Be precise and only return the app type key."
        )
        
        app_type = response.strip().lower()
        return app_type if app_type in self.templates else None
    
    async def create_app(self, user_request: str, app_name: str = None, app_type: str = None) -> Optional[Path]:
        """Create a complete application based on user request."""
        console.print(f"[bold blue]🚀 Creating your application based on: '{user_request}'[/bold blue]")
        
        # Detect app type if not provided
        if not app_type:
            app_type = await self.detect_app_type(user_request)
            if not app_type:
                console.print("[red]❌ Could not determine app type from request[/red]")
                return None
        
        template = self.templates.get(app_type)
        if not template:
            console.print(f"[red]❌ Unknown app type: {app_type}[/red]")
            return None
        
        # Generate app name if not provided
        if not app_name:
            app_name = await self._generate_app_name(user_request, template)
        
        # Create app directory
        app_path = self.base_path / app_name
        if app_path.exists():
            if not Confirm.ask(f"Directory '{app_name}' already exists. Continue?"):
                return None
            shutil.rmtree(app_path)
        
        console.print(f"[green]📁 Creating app directory: {app_path}[/green]")
        app_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize project planner for the new app
        project_planner = ProjectPlanner(self.ollama_client, self.config, app_path)
        
        # Generate project plan
        await self._generate_project_plan(project_planner, user_request, template, app_name)
        
        # Create directory structure
        await self._create_directory_structure(app_path, template.directory_structure)
        
        # Generate all required files with context awareness
        await self._generate_app_files(app_path, template, user_request, project_planner)
        
        # Create dependency files
        await self._create_dependency_files(app_path, template)
        
        # Show completion summary
        await self._show_completion_summary(app_path, template, app_name)
        
        return app_path
    
    async def _generate_app_name(self, user_request: str, template: AppTemplate) -> str:
        """Generate a suitable app name based on the request."""
        prompt = f"""Generate a suitable directory/project name for this app request:

Request: "{user_request}"
App Type: {template.name}

Requirements:
- Use lowercase letters, numbers, and hyphens only
- Be descriptive but concise (2-4 words max)
- Reflect the purpose of the app

Examples: "my-landing-page", "todo-api", "space-shooter-game"

Return only the name, nothing else."""
        
        response = await self.ollama_client.generate_response(
            prompt,
            system_prompt="Generate concise, descriptive project names using lowercase and hyphens."
        )
        
        # Clean up the response
        name = response.strip().lower()
        name = ''.join(c if c.isalnum() or c in '-_' else '-' for c in name)
        name = '-'.join(word for word in name.split('-') if word)
        
        return name[:50]  # Limit length
    
    async def _generate_project_plan(self, project_planner: ProjectPlanner, user_request: str, template: AppTemplate, app_name: str):
        """Generate a project plan for the new app."""
        plan_content = f"""# {app_name.replace('-', ' ').title()} - Project Plan

## Project Overview
**Request:** {user_request}
**Type:** {template.name}
**Tech Stack:** {', '.join(template.tech_stack)}

## Project Goals
- Create a fully functional {template.description.lower()}
- Implement modern best practices and clean architecture
- Ensure responsive design and user-friendly interface
- Include proper documentation and setup instructions

## Technical Requirements
- **Framework/Language:** {template.tech_stack[0]}
- **Dependencies:** {', '.join(template.dependencies.get(list(template.dependencies.keys())[0], [])[:5])}
- **Architecture:** Component-based, modular design

## Development Tasks
- [ ] Set up project structure and dependencies
- [ ] Implement core functionality
- [ ] Create user interface components
- [ ] Add styling and responsive design
- [ ] Implement data handling/state management
- [ ] Add error handling and validation
- [ ] Write documentation and README
- [ ] Test functionality and fix bugs

## File Structure
{self._format_file_structure(template.required_files)}

## Setup Commands
```bash
{chr(10).join(template.setup_commands)}
```

## Development Commands
```bash
{chr(10).join(template.dev_commands)}
```

## Next Steps
1. Review generated code and customize as needed
2. Run setup commands to install dependencies
3. Start development server and test functionality
4. Iterate and enhance based on requirements
"""
        
        # Save the plan
        plan_path = project_planner.project_root / "plan.md"
        plan_path.write_text(plan_content, encoding='utf-8')
        
        # Initialize project context
        await project_planner.initialize_project_context(app_name, user_request)
    
    def _format_file_structure(self, files: List[str]) -> str:
        """Format file structure for display."""
        structure = []
        for file in sorted(files):
            indent = "  " * (file.count('/'))
            name = file.split('/')[-1]
            structure.append(f"{indent}- {name}")
        return '\n'.join(structure)
    
    async def _create_directory_structure(self, app_path: Path, structure: Dict[str, Any], current_path: Path = None):
        """Create the directory structure for the app."""
        if current_path is None:
            current_path = app_path
        
        for name, content in structure.items():
            dir_path = current_path / name
            dir_path.mkdir(exist_ok=True)
            
            if isinstance(content, dict):
                await self._create_directory_structure(app_path, content, dir_path)
    
    async def _generate_app_files(self, app_path: Path, template: AppTemplate, user_request: str, project_planner: ProjectPlanner):
        """Generate all required files for the app with full context awareness."""
        console.print("[blue]📝 Generating application files with AI assistance...[/blue]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Generating files...", total=len(template.required_files))
            
            # Generate files in logical order
            ordered_files = self._order_files_by_dependency(template.required_files)
            
            for file_path in ordered_files:
                progress.update(task, description=f"Creating {file_path}")
                
                # Generate file content with full context
                content = await self._generate_file_content(
                    app_path, file_path, template, user_request, project_planner
                )
                
                if content:
                    full_path = app_path / file_path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    full_path.write_text(content, encoding='utf-8')
                    
                    # Track file creation in project planner
                    project_planner.track_file_edit(
                        str(full_path),
                        [f"Generated {file_path} for {template.name}"],
                        "complete"
                    )
                
                progress.advance(task)
    
    def _order_files_by_dependency(self, files: List[str]) -> List[str]:
        """Order files by dependency (config files first, then core files, then components)."""
        config_files = [f for f in files if any(f.endswith(ext) for ext in ['.json', '.js', '.ts', '.yaml', '.yml', '.config.js', '.md'])]
        core_files = [f for f in files if 'main' in f or 'app' in f or 'index' in f or 'server' in f]
        component_files = [f for f in files if 'component' in f.lower() or f.startswith('src/')]
        other_files = [f for f in files if f not in config_files + core_files + component_files]
        
        return config_files + core_files + component_files + other_files
    
    async def _generate_file_content(self, app_path: Path, file_path: str, template: AppTemplate, user_request: str, project_planner: ProjectPlanner) -> str:
        """Generate content for a specific file with full context awareness."""
        try:
            # Get project context
            context = project_planner.get_context_for_file(str(app_path / file_path))
            
            # Research best practices if needed
            research_info = ""
            if any(keyword in file_path.lower() for keyword in ['component', 'page', 'api', 'model']):
                research_query = f"{template.tech_stack[0]} {file_path.split('/')[-1]} best practices"
                async with self.web_search as search_assistant:
                    research_info = await search_assistant.search_and_summarize(research_query, template.tech_stack[0])
            
            # Generate file-specific content
            prompt = f"""Generate the complete content for this file in a {template.name}:

File: {file_path}
User Request: "{user_request}"
Tech Stack: {', '.join(template.tech_stack)}
Project Goal: {context['project_goal']}

File Purpose: {self._get_file_purpose(file_path, template)}

Requirements:
- Follow {template.tech_stack[0]} best practices
- Include proper imports and dependencies
- Add comprehensive comments and documentation
- Ensure code is production-ready and well-structured
- Make it responsive and user-friendly (for UI files)
- Include error handling where appropriate

{f"Research Findings: {research_info[:500]}" if research_info else ""}

Generate ONLY the file content, no explanations or markdown formatting."""
            
            content = await self.ollama_client.generate_response(
                prompt,
                system_prompt=f"You are an expert {template.tech_stack[0]} developer. Generate complete, production-ready code files."
            )
            
            # Clean up content (remove any markdown formatting)
            if "```" in content:
                import re
                code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', content, re.DOTALL)
                if code_blocks:
                    content = code_blocks[0]
            
            return content.strip()
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Error generating {file_path}: {e}[/yellow]")
            return f"// TODO: Implement {file_path}\n// Error during generation: {e}"
    
    def _get_file_purpose(self, file_path: str, template: AppTemplate) -> str:
        """Get the purpose/description of a file based on its path and template."""
        file_name = file_path.split('/')[-1].lower()
        
        purposes = {
            'package.json': 'Node.js project configuration and dependencies',
            'requirements.txt': 'Python project dependencies',
            'pubspec.yaml': 'Flutter project configuration and dependencies',
            'main.py': 'Python application entry point',
            'main.jsx': 'React application entry point',
            'main.dart': 'Flutter application entry point',
            'app.jsx': 'Main React application component',
            'app.js': 'Express.js application setup and middleware',
            'server.js': 'Node.js server entry point',
            'index.html': 'HTML entry point for web application',
            'readme.md': 'Project documentation and setup instructions',
            'header': 'Navigation header component',
            'footer': 'Page footer component',
            'hero': 'Hero section component for landing page',
            'features': 'Features showcase component',
            'controller': 'API request handler and business logic',
            'model': 'Data model and database schema',
            'route': 'API endpoint definitions',
            'middleware': 'Request processing middleware',
            'config': 'Application configuration settings'
        }
        
        for key, purpose in purposes.items():
            if key in file_name:
                return purpose
        
        return f"Component file for {template.name}"
    
    async def _create_dependency_files(self, app_path: Path, template: AppTemplate):
        """Create dependency management files."""
        for package_manager, packages in template.dependencies.items():
            if package_manager == "npm":
                await self._create_package_json(app_path, template, packages)
            elif package_manager == "pip":
                await self._create_requirements_txt(app_path, packages)
            elif package_manager == "flutter":
                await self._create_pubspec_yaml(app_path, template, packages)
    
    async def _create_package_json(self, app_path: Path, template: AppTemplate, packages: List[str]):
        """Create package.json for Node.js projects."""
        app_name = app_path.name
        package_json = {
            "name": app_name,
            "version": "1.0.0",
            "description": template.description,
            "main": "index.js",
            "scripts": {
                "dev": "vite" if "vite" in packages else "next dev" if "next" in packages else "nodemon server.js",
                "build": "vite build" if "vite" in packages else "next build" if "next" in packages else "echo 'No build script'",
                "start": "vite preview" if "vite" in packages else "next start" if "next" in packages else "node server.js",
                "lint": "eslint . --ext js,jsx,ts,tsx"
            },
            "dependencies": {pkg: "latest" for pkg in packages if not pkg.startswith("@types")},
            "devDependencies": {pkg: "latest" for pkg in packages if pkg.startswith("@types") or pkg in ["eslint", "prettier"]}
        }
        
        (app_path / "package.json").write_text(
            __import__('json').dumps(package_json, indent=2),
            encoding='utf-8'
        )
    
    async def _create_requirements_txt(self, app_path: Path, packages: List[str]):
        """Create requirements.txt for Python projects."""
        content = '\n'.join(f"{pkg}>=1.0.0" for pkg in packages)
        (app_path / "requirements.txt").write_text(content, encoding='utf-8')
    
    async def _create_pubspec_yaml(self, app_path: Path, template: AppTemplate, packages: List[str]):
        """Create pubspec.yaml for Flutter projects."""
        app_name = app_path.name.replace('-', '_')
        content = f"""name: {app_name}
description: {template.description}
version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  cupertino_icons: ^1.0.2
{chr(10).join(f'  {pkg}: ^1.0.0' for pkg in packages)}

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^2.0.0

flutter:
  uses-material-design: true
"""
        (app_path / "pubspec.yaml").write_text(content, encoding='utf-8')
    
    async def _show_completion_summary(self, app_path: Path, template: AppTemplate, app_name: str):
        """Show completion summary and next steps."""
        console.print(Panel(
            f"[bold green]🎉 Application '{app_name}' created successfully![/bold green]\n\n"
            f"[bold]Type:[/bold] {template.name}\n"
            f"[bold]Location:[/bold] {app_path}\n"
            f"[bold]Tech Stack:[/bold] {', '.join(template.tech_stack)}\n"
            f"[bold]Files Created:[/bold] {len(template.required_files)}\n\n"
            f"[bold cyan]Next Steps:[/bold cyan]\n"
            f"1. cd {app_name}\n"
            f"2. {template.setup_commands[0] if template.setup_commands else 'Review the files'}\n"
            f"3. {template.dev_commands[0] if template.dev_commands else 'Start development'}\n\n"
            f"[dim]All files have been generated with AI assistance and include\n"
            f"modern best practices, proper documentation, and error handling.[/dim]",
            title="🚀 App Generation Complete",
            border_style="green"
        ))
        
        # Show file tree
        console.print(f"\n[bold blue]📁 Generated File Structure:[/bold blue]")
        self._show_file_tree(app_path)
    
    def _show_file_tree(self, path: Path, prefix: str = "", max_depth: int = 3, current_depth: int = 0):
        """Show a tree view of the generated files."""
        if current_depth > max_depth:
            return
        
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))
        for i, item in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            console.print(f"{prefix}{current_prefix}{item.name}")
            
            if item.is_dir() and current_depth < max_depth:
                next_prefix = prefix + ("    " if is_last else "│   ")
                self._show_file_tree(item, next_prefix, max_depth, current_depth + 1)
    
    def list_available_templates(self):
        """List all available app templates."""
        console.print("[bold blue]🎯 Available App Templates:[/bold blue]\n")
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Template", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Tech Stack", style="green")
        
        for key, template in self.templates.items():
            table.add_row(
                key,
                template.description,
                ", ".join(template.tech_stack[:3])
            )
        
        console.print(table)
        console.print("\n[dim]Use: 'Create a [type] app' or specify the template directly[/dim]")
