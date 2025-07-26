"""
File management module for Hurricane AI Agent.
"""

import os
import shutil
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from rich.console import Console
from rich.tree import Tree
import aiofiles

from ..core.config import Config

console = Console()


class FileManager:
    """File management and organization module."""
    
    def __init__(self, config: Config):
        self.config = config
        self.templates_dir = Path(__file__).parent.parent / "templates"
        self.templates_dir.mkdir(exist_ok=True)
    
    async def save_file(self, file_path: Path, content: str) -> bool:
        """Save content to a file."""
        try:
            # Ensure directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)
            
            console.print(f"[green]✅ File saved: {file_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error saving file {file_path}: {e}[/red]")
            return False
    
    async def read_file(self, file_path: Path) -> str:
        """Read content from a file."""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            return content
            
        except Exception as e:
            console.print(f"[red]❌ Error reading file {file_path}: {e}[/red]")
            return ""
    
    async def create_project_structure(
        self, 
        project_type: str,
        project_name: str,
        base_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        """Create a project structure based on type."""
        if base_path is None:
            base_path = Path.cwd()
        
        project_path = base_path / project_name
        
        # Project templates
        templates = {
            "python": self._create_python_project,
            "web-app": self._create_web_app_project,
            "api": self._create_api_project,
            "cli": self._create_cli_project,
            "library": self._create_library_project,
            "data-science": self._create_data_science_project,
        }
        
        creator = templates.get(project_type, self._create_basic_project)
        
        try:
            result = await creator(project_path, project_name)
            console.print(f"[green]✅ Created {project_type} project: {project_name}[/green]")
            return result
            
        except Exception as e:
            console.print(f"[red]❌ Error creating project: {e}[/red]")
            return {"error": str(e)}
    
    async def _create_python_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create a Python project structure."""
        structure = {
            "directories": [
                project_path / project_name,
                project_path / "tests",
                project_path / "docs",
                project_path / "scripts",
            ],
            "files": {
                "README.md": f"# {project_name}\n\nA Python project created by Hurricane AI Agent.",
                "requirements.txt": "# Add your dependencies here\n",
                "setup.py": f'''from setuptools import setup, find_packages

setup(
    name="{project_name}",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add dependencies here
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python project",
    python_requires=">=3.8",
)''',
                f"{project_name}/__init__.py": f'"""\\n{project_name} - A Python project.\\n"""\\n\\n__version__ = "0.1.0"',
                f"{project_name}/main.py": '''"""\\nMain module for the application.\\n"""\\n\\ndef main():\\n    """Main function."""\\n    print("Hello from Hurricane!")\\n\\n\\nif __name__ == "__main__":\\n    main()''',
                "tests/__init__.py": "",
                "tests/test_main.py": f'''"""\\nTests for {project_name}.\\n"""\\n\\nimport pytest\\nfrom {project_name}.main import main\\n\\n\\ndef test_main():\\n    """Test main function."""\\n    # Add your tests here\\n    pass''',
                ".gitignore": '''__pycache__/\\n*.py[cod]\\n*$py.class\\n*.so\\n.Python\\nbuild/\\ndevelop-eggs/\\ndist/\\ndownloads/\\neggs/\\n.eggs/\\nlib/\\nlib64/\\nparts/\\nsdist/\\nvar/\\nwheels/\\n*.egg-info/\\n.installed.cfg\\n*.egg\\nPIPFILE.LOCK\\n.env\\n.venv\\nenv/\\nvenv/\\nENV/\\nenv.bak/\\nvenv.bak/''',
            }
        }
        
        return await self._create_structure(structure)
    
    async def _create_web_app_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create a web application project structure."""
        structure = {
            "directories": [
                project_path / "src",
                project_path / "public",
                project_path / "tests",
                project_path / "docs",
            ],
            "files": {
                "README.md": f"# {project_name}\n\nA web application created by Hurricane AI Agent.",
                "package.json": f'''{{\n  "name": "{project_name}",\n  "version": "1.0.0",\n  "description": "A web application",\n  "main": "src/index.js",\n  "scripts": {{\n    "start": "node src/index.js",\n    "dev": "nodemon src/index.js",\n    "test": "jest"\n  }},\n  "dependencies": {{\n    "express": "^4.18.0"\n  }},\n  "devDependencies": {{\n    "nodemon": "^2.0.0",\n    "jest": "^29.0.0"\n  }}\n}}''',
                "src/index.js": '''const express = require('express');\\nconst app = express();\\nconst PORT = process.env.PORT || 3000;\\n\\napp.use(express.static('public'));\\n\\napp.get('/', (req, res) => {\\n  res.send('Hello from Hurricane Web App!');\\n});\\n\\napp.listen(PORT, () => {\\n  console.log(`Server running on port ${PORT}`);\\n});''',
                "public/index.html": f'''<!DOCTYPE html>\\n<html lang="en">\\n<head>\\n  <meta charset="UTF-8">\\n  <meta name="viewport" content="width=device-width, initial-scale=1.0">\\n  <title>{project_name}</title>\\n</head>\\n<body>\\n  <h1>Welcome to {project_name}</h1>\\n  <p>Created by Hurricane AI Agent</p>\\n</body>\\n</html>''',
                ".gitignore": "node_modules/\\n.env\\n.DS_Store\\ndist/\\nbuild/",
            }
        }
        
        return await self._create_structure(structure)
    
    async def _create_api_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create an API project structure."""
        structure = {
            "directories": [
                project_path / "app",
                project_path / "app" / "routes",
                project_path / "app" / "models",
                project_path / "app" / "utils",
                project_path / "tests",
                project_path / "docs",
            ],
            "files": {
                "README.md": f"# {project_name} API\n\nA REST API created by Hurricane AI Agent.",
                "requirements.txt": "fastapi>=0.104.0\\nuvicorn>=0.24.0\\npydantic>=2.5.0\\npython-multipart>=0.0.6",
                "main.py": '''from fastapi import FastAPI\\nfrom app.routes import api_router\\n\\napp = FastAPI(title="Hurricane API", version="1.0.0")\\n\\napp.include_router(api_router, prefix="/api/v1")\\n\\n@app.get("/")\\nasync def root():\\n    return {"message": "Welcome to Hurricane API"}\\n\\nif __name__ == "__main__":\\n    import uvicorn\\n    uvicorn.run(app, host="0.0.0.0", port=8000)''',
                "app/__init__.py": "",
                "app/routes/__init__.py": '''from fastapi import APIRouter\\n\\napi_router = APIRouter()\\n\\n@api_router.get("/health")\\nasync def health_check():\\n    return {"status": "healthy"}''',
                "app/models/__init__.py": '''from pydantic import BaseModel\\n\\nclass HealthResponse(BaseModel):\\n    status: str''',
                "app/utils/__init__.py": '''"""Utility functions for the API."""\\n\\ndef format_response(data, message="Success"):\\n    return {"data": data, "message": message}''',
                ".gitignore": "__pycache__/\\n*.pyc\\n.env\\n.venv/\\nvenv/",
            }
        }
        
        return await self._create_structure(structure)
    
    async def _create_cli_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create a CLI project structure."""
        structure = {
            "directories": [
                project_path / project_name,
                project_path / "tests",
                project_path / "docs",
            ],
            "files": {
                "README.md": f"# {project_name}\n\nA CLI application created by Hurricane AI Agent.",
                "requirements.txt": "click>=8.1.0\\nrich>=13.0.0\\ntyper>=0.9.0",
                "setup.py": f'''from setuptools import setup, find_packages\\n\\nsetup(\\n    name="{project_name}",\\n    version="0.1.0",\\n    packages=find_packages(),\\n    install_requires=["click", "rich"],\\n    entry_points={{\\n        "console_scripts": [\\n            "{project_name}={project_name}.cli:main",\\n        ],\\n    }},\\n)''',
                f"{project_name}/__init__.py": f'__version__ = "0.1.0"',
                f"{project_name}/cli.py": '''import click\\nfrom rich.console import Console\\n\\nconsole = Console()\\n\\n@click.group()\\n@click.version_option()\\ndef main():\\n    """Hurricane CLI Application."""\\n    pass\\n\\n@main.command()\\n@click.option("--name", default="World", help="Name to greet")\\ndef hello(name):\\n    """Say hello."""\\n    console.print(f"Hello, {name}!", style="bold green")\\n\\nif __name__ == "__main__":\\n    main()''',
                ".gitignore": "__pycache__/\\n*.pyc\\n.env\\nbuild/\\ndist/\\n*.egg-info/",
            }
        }
        
        return await self._create_structure(structure)
    
    async def _create_library_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create a library project structure."""
        return await self._create_python_project(project_path, project_name)
    
    async def _create_data_science_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create a data science project structure."""
        structure = {
            "directories": [
                project_path / "data" / "raw",
                project_path / "data" / "processed",
                project_path / "notebooks",
                project_path / "src",
                project_path / "models",
                project_path / "reports",
                project_path / "tests",
            ],
            "files": {
                "README.md": f"# {project_name}\n\nA data science project created by Hurricane AI Agent.",
                "requirements.txt": "pandas>=2.0.0\\nnumpy>=1.24.0\\nscikit-learn>=1.3.0\\njupyter>=1.0.0\\nmatplotlib>=3.7.0\\nseaborn>=0.12.0",
                "notebooks/01_exploration.ipynb": '''{"cells": [], "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}}, "nbformat": 4, "nbformat_minor": 4}''',
                "src/__init__.py": "",
                "src/data_processing.py": '''"""Data processing utilities."""\\n\\nimport pandas as pd\\n\\ndef load_data(filepath):\\n    """Load data from file."""\\n    return pd.read_csv(filepath)\\n\\ndef clean_data(df):\\n    """Clean the dataset."""\\n    return df.dropna()''',
                ".gitignore": "__pycache__/\\n*.pyc\\n.env\\n.ipynb_checkpoints/\\ndata/raw/*\\n!data/raw/.gitkeep\\nmodels/*\\n!models/.gitkeep",
                "data/raw/.gitkeep": "",
                "models/.gitkeep": "",
            }
        }
        
        return await self._create_structure(structure)
    
    async def _create_basic_project(self, project_path: Path, project_name: str) -> Dict[str, Any]:
        """Create a basic project structure."""
        structure = {
            "directories": [project_path],
            "files": {
                "README.md": f"# {project_name}\n\nA project created by Hurricane AI Agent.",
                ".gitignore": ".DS_Store\\n*.log\\n.env",
            }
        }
        
        return await self._create_structure(structure)
    
    async def _create_structure(self, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Create the actual file structure."""
        created_files = []
        created_dirs = []
        
        # Create directories
        for directory in structure.get("directories", []):
            directory.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(directory))
        
        # Create files
        for file_path, content in structure.get("files", {}).items():
            full_path = structure["directories"][0] / file_path if structure.get("directories") else Path(file_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            await self.save_file(full_path, content)
            created_files.append(str(full_path))
        
        return {
            "created_directories": created_dirs,
            "created_files": created_files,
            "project_path": str(structure["directories"][0]) if structure.get("directories") else None,
        }
    
    async def organize_files(self, directory: Path, strategy: str = "by_type") -> Dict[str, Any]:
        """Organize files in a directory based on strategy."""
        if not directory.exists() or not directory.is_dir():
            return {"error": f"Directory {directory} does not exist or is not a directory"}
        
        strategies = {
            "by_type": self._organize_by_type,
            "by_date": self._organize_by_date,
            "by_size": self._organize_by_size,
            "by_project": self._organize_by_project,
        }
        
        organizer = strategies.get(strategy, self._organize_by_type)
        return await organizer(directory)
    
    async def _organize_by_type(self, directory: Path) -> Dict[str, Any]:
        """Organize files by file type."""
        type_mapping = {
            "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"],
            "documents": [".pdf", ".doc", ".docx", ".txt", ".md", ".rtf"],
            "code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".go", ".rs"],
            "data": [".csv", ".json", ".xml", ".xlsx", ".sql"],
            "archives": [".zip", ".tar", ".gz", ".rar", ".7z"],
            "videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
            "audio": [".mp3", ".wav", ".flac", ".aac", ".ogg"],
        }
        
        moved_files = {}
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_ext = file_path.suffix.lower()
                
                # Find appropriate category
                category = "misc"
                for cat, extensions in type_mapping.items():
                    if file_ext in extensions:
                        category = cat
                        break
                
                # Create category directory
                category_dir = directory / category
                category_dir.mkdir(exist_ok=True)
                
                # Move file
                new_path = category_dir / file_path.name
                if not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    moved_files[str(file_path)] = str(new_path)
        
        return {"moved_files": moved_files, "strategy": "by_type"}
    
    async def _organize_by_date(self, directory: Path) -> Dict[str, Any]:
        """Organize files by modification date."""
        moved_files = {}
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                # Get modification date
                mod_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                date_folder = mod_time.strftime("%Y-%m")
                
                # Create date directory
                date_dir = directory / date_folder
                date_dir.mkdir(exist_ok=True)
                
                # Move file
                new_path = date_dir / file_path.name
                if not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    moved_files[str(file_path)] = str(new_path)
        
        return {"moved_files": moved_files, "strategy": "by_date"}
    
    async def _organize_by_size(self, directory: Path) -> Dict[str, Any]:
        """Organize files by size."""
        moved_files = {}
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                file_size = file_path.stat().st_size
                
                # Determine size category
                if file_size < 1024 * 1024:  # < 1MB
                    size_category = "small"
                elif file_size < 100 * 1024 * 1024:  # < 100MB
                    size_category = "medium"
                else:
                    size_category = "large"
                
                # Create size directory
                size_dir = directory / size_category
                size_dir.mkdir(exist_ok=True)
                
                # Move file
                new_path = size_dir / file_path.name
                if not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    moved_files[str(file_path)] = str(new_path)
        
        return {"moved_files": moved_files, "strategy": "by_size"}
    
    async def _organize_by_project(self, directory: Path) -> Dict[str, Any]:
        """Organize files by project (based on filename patterns)."""
        moved_files = {}
        
        for file_path in directory.iterdir():
            if file_path.is_file():
                # Extract project name from filename (simple heuristic)
                name_parts = file_path.stem.split('_')
                project_name = name_parts[0] if name_parts else "misc"
                
                # Create project directory
                project_dir = directory / project_name
                project_dir.mkdir(exist_ok=True)
                
                # Move file
                new_path = project_dir / file_path.name
                if not new_path.exists():
                    shutil.move(str(file_path), str(new_path))
                    moved_files[str(file_path)] = str(new_path)
        
        return {"moved_files": moved_files, "strategy": "by_project"}
    
    def display_tree(self, directory: Path, max_depth: int = 3) -> None:
        """Display directory tree structure."""
        tree = Tree(f"📁 {directory.name}")
        self._build_tree(tree, directory, max_depth, 0)
        console.print(tree)
    
    def _build_tree(self, tree, directory: Path, max_depth: int, current_depth: int) -> None:
        """Recursively build tree structure."""
        if current_depth >= max_depth:
            return
        
        try:
            items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                if item.name.startswith('.'):
                    continue
                
                if item.is_dir():
                    branch = tree.add(f"📁 {item.name}")
                    self._build_tree(branch, item, max_depth, current_depth + 1)
                else:
                    tree.add(f"📄 {item.name}")
                    
        except PermissionError:
            tree.add("❌ Permission denied")
