"""
Project indexing and navigation module for Hurricane AI Agent.
"""

import os
import ast
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
import hashlib
from functools import lru_cache
from rich.console import Console
from rich.tree import Tree
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

# Set up logging
logger = logging.getLogger(__name__)
console = Console()


class ProjectIndexer:
    """Smart project indexing and navigation system."""
    
    def __init__(self, project_root: Path):
        self.project_root = Path(project_root).resolve()
        self.index_file = self.project_root / ".hurricane" / "project_index.json"
        self.index_data = {}
        self.file_cache = {}
        
        # Performance optimization
        self._cache_expiry = timedelta(minutes=30)  # Cache expires after 30 minutes
        self._last_index_time = None
        self._analysis_cache = {}  # Cache for file analysis results
        
        # Supported file types for analysis
        self.code_extensions = {
            '.py': 'python',
            '.js': 'javascript', 
            '.jsx': 'javascript',
            '.ts': 'typescript',
            '.tsx': 'typescript',
            '.go': 'go',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin'
        }
        
        self.doc_extensions = {
            '.md': 'markdown',
            '.txt': 'text',
            '.rst': 'restructuredtext',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.toml': 'toml',
            '.xml': 'xml',
            '.html': 'html',
            '.css': 'css'
        }
        
        # Files to ignore
        self.ignore_patterns = {
            '__pycache__', '.git', '.svn', 'node_modules', '.vscode', 
            '.idea', 'venv', 'env', '.env', 'dist', 'build', '.DS_Store',
            '*.pyc', '*.pyo', '*.pyd', '.pytest_cache', '.coverage'
        }
    
    async def initialize_project(self) -> Dict[str, Any]:
        """Initialize project indexing."""
        console.print("[bold blue]🔍 Initializing project indexing...[/bold blue]")
        
        # Create .hurricane directory
        hurricane_dir = self.project_root / ".hurricane"
        hurricane_dir.mkdir(exist_ok=True)
        
        # Load existing index or create new
        if self.index_file.exists():
            await self._load_index()
            console.print("[green]📚 Loaded existing project index[/green]")
        else:
            console.print("[blue]📊 Creating new project index...[/blue]")
        
        # Scan and index the project
        await self._scan_project()
        await self._save_index()
        
        return {
            "project_root": str(self.project_root),
            "total_files": len(self.index_data.get('files', {})),
            "code_files": len([f for f in self.index_data.get('files', {}).values() if f.get('type') == 'code']),
            "doc_files": len([f for f in self.index_data.get('files', {}).values() if f.get('type') == 'documentation']),
            "last_indexed": self.index_data.get('last_indexed', 'Never')
        }
    
    async def _load_index(self):
        """Load existing project index."""
        try:
            with open(self.index_file, 'r') as f:
                self.index_data = json.load(f)
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not load index: {e}[/yellow]")
            self.index_data = {}
    
    async def _save_index(self):
        """Save project index to file."""
        try:
            self.index_data['last_indexed'] = datetime.now().isoformat()
            with open(self.index_file, 'w') as f:
                json.dump(self.index_data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Could not save index: {e}[/red]")
    
    async def _scan_project(self):
        """Scan and index all project files."""
        files_data = {}
        project_structure = {}
        
        for root, dirs, files in os.walk(self.project_root):
            # Skip ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            root_path = Path(root)
            relative_root = root_path.relative_to(self.project_root)
            
            for file in files:
                if self._should_ignore(file):
                    continue
                
                file_path = root_path / file
                relative_path = file_path.relative_to(self.project_root)
                
                # Analyze file
                file_info = await self._analyze_file(file_path)
                files_data[str(relative_path)] = file_info
        
        self.index_data['files'] = files_data
        self.index_data['project_structure'] = await self._build_structure_tree()
        
        console.print(f"[green]✅ Indexed {len(files_data)} files[/green]")
    
    def _should_ignore(self, name: str) -> bool:
        """Check if file/directory should be ignored."""
        return any(pattern in name or name.startswith('.') for pattern in self.ignore_patterns)
    
    async def _analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file and extract metadata."""
        try:
            stat = file_path.stat()
            file_info = {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "extension": file_path.suffix.lower(),
                "type": "unknown",
                "language": None,
                "functions": [],
                "classes": [],
                "imports": [],
                "summary": "",
                "hash": ""
            }
            
            # Determine file type and language
            ext = file_path.suffix.lower()
            if ext in self.code_extensions:
                file_info["type"] = "code"
                file_info["language"] = self.code_extensions[ext]
                
                # Analyze code structure for Python files
                if ext == '.py':
                    await self._analyze_python_file(file_path, file_info)
                    
            elif ext in self.doc_extensions:
                file_info["type"] = "documentation"
                file_info["language"] = self.doc_extensions[ext]
                
                # Read documentation content
                if stat.st_size < 1024 * 1024:  # Only read files < 1MB
                    try:
                        content = file_path.read_text(encoding='utf-8')
                        file_info["summary"] = content[:200] + "..." if len(content) > 200 else content
                        file_info["hash"] = hashlib.md5(content.encode()).hexdigest()
                    except:
                        pass
            
            return file_info
            
        except Exception as e:
            return {"error": str(e), "type": "error"}
    
    async def _analyze_python_file(self, file_path: Path, file_info: Dict[str, Any]):
        """Analyze Python file structure."""
        try:
            content = file_path.read_text(encoding='utf-8')
            file_info["hash"] = hashlib.md5(content.encode()).hexdigest()
            
            # Parse AST
            tree = ast.parse(content)
            
            # Extract functions, classes, and imports
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    func_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node) or ""
                    }
                    file_info["functions"].append(func_info)
                
                elif isinstance(node, ast.ClassDef):
                    class_info = {
                        "name": node.name,
                        "line": node.lineno,
                        "methods": [],
                        "docstring": ast.get_docstring(node) or ""
                    }
                    
                    # Get class methods
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef):
                            class_info["methods"].append({
                                "name": item.name,
                                "line": item.lineno
                            })
                    
                    file_info["classes"].append(class_info)
                
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        file_info["imports"].append(alias.name)
                
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        for alias in node.names:
                            file_info["imports"].append(f"{node.module}.{alias.name}")
            
            # Create summary
            summary_parts = []
            if file_info["functions"]:
                summary_parts.append(f"{len(file_info['functions'])} functions")
            if file_info["classes"]:
                summary_parts.append(f"{len(file_info['classes'])} classes")
            if file_info["imports"]:
                summary_parts.append(f"{len(file_info['imports'])} imports")
            
            file_info["summary"] = ", ".join(summary_parts) if summary_parts else "Python file"
            
        except Exception as e:
            file_info["error"] = str(e)
    
    async def _build_structure_tree(self) -> Dict[str, Any]:
        """Build project structure tree."""
        structure = {}
        
        for file_path in self.index_data.get('files', {}):
            parts = Path(file_path).parts
            current = structure
            
            for part in parts[:-1]:  # directories
                if part not in current:
                    current[part] = {"type": "directory", "children": {}}
                current = current[part]["children"]
            
            # file
            filename = parts[-1]
            file_info = self.index_data['files'][file_path]
            current[filename] = {
                "type": "file",
                "info": file_info
            }
        
        return structure
    
    def show_project_tree(self, max_depth: int = 3) -> None:
        """Display project structure as a tree."""
        tree = Tree(f"📁 {self.project_root.name}")
        self._build_rich_tree(tree, self.index_data.get('project_structure', {}), 0, max_depth)
        console.print(tree)
    
    def _build_rich_tree(self, tree, structure: Dict, depth: int, max_depth: int):
        """Build rich tree display."""
        if depth >= max_depth:
            return
        
        for name, item in structure.items():
            if item["type"] == "directory":
                branch = tree.add(f"📁 {name}")
                self._build_rich_tree(branch, item.get("children", {}), depth + 1, max_depth)
            else:
                file_info = item.get("info", {})
                icon = "🐍" if file_info.get("language") == "python" else "📄"
                summary = file_info.get("summary", "")
                if summary and len(summary) > 50:
                    summary = summary[:47] + "..."
                display_name = f"{icon} {name}"
                if summary:
                    display_name += f" - {summary}"
                tree.add(display_name)
    
    def search_files(self, query: str, file_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search for files by name or content."""
        results = []
        query_lower = query.lower()
        
        for file_path, file_info in self.index_data.get('files', {}).items():
            if file_type and file_info.get('type') != file_type:
                continue
            
            # Search in filename
            if query_lower in Path(file_path).name.lower():
                results.append({
                    "path": file_path,
                    "match_type": "filename",
                    "info": file_info
                })
                continue
            
            # Search in functions/classes for code files
            if file_info.get('type') == 'code':
                for func in file_info.get('functions', []):
                    if query_lower in func['name'].lower():
                        results.append({
                            "path": file_path,
                            "match_type": "function",
                            "match_name": func['name'],
                            "line": func['line'],
                            "info": file_info
                        })
                
                for cls in file_info.get('classes', []):
                    if query_lower in cls['name'].lower():
                        results.append({
                            "path": file_path,
                            "match_type": "class",
                            "match_name": cls['name'],
                            "line": cls['line'],
                            "info": file_info
                        })
        
        return results
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific file."""
        return self.index_data.get('files', {}).get(file_path)
    
    def list_files_by_type(self, file_type: str) -> List[str]:
        """List all files of a specific type."""
        return [
            path for path, info in self.index_data.get('files', {}).items()
            if info.get('type') == file_type
        ]
    
    def get_project_summary(self) -> Dict[str, Any]:
        """Get project summary statistics."""
        files = self.index_data.get('files', {})
        
        summary = {
            "total_files": len(files),
            "by_type": {},
            "by_language": {},
            "total_functions": 0,
            "total_classes": 0,
            "largest_files": [],
            "recently_modified": []
        }
        
        for path, info in files.items():
            # Count by type
            file_type = info.get('type', 'unknown')
            summary["by_type"][file_type] = summary["by_type"].get(file_type, 0) + 1
            
            # Count by language
            language = info.get('language')
            if language:
                summary["by_language"][language] = summary["by_language"].get(language, 0) + 1
            
            # Count functions and classes
            summary["total_functions"] += len(info.get('functions', []))
            summary["total_classes"] += len(info.get('classes', []))
        
        return summary
    
    async def safe_delete_file(self, file_path: str) -> bool:
        """Safely delete a file with user confirmation."""
        full_path = self.project_root / file_path
        
        if not full_path.exists():
            console.print(f"[red]❌ File {file_path} does not exist[/red]")
            return False
        
        # Get file info
        file_info = self.get_file_info(file_path)
        
        # Show file details
        console.print(f"\n[bold yellow]⚠️ About to delete:[/bold yellow]")
        console.print(f"[cyan]File:[/cyan] {file_path}")
        console.print(f"[cyan]Size:[/cyan] {file_info.get('size', 0)} bytes")
        console.print(f"[cyan]Type:[/cyan] {file_info.get('type', 'unknown')}")
        console.print(f"[cyan]Last modified:[/cyan] {file_info.get('modified', 'unknown')}")
        
        if file_info.get('type') == 'code':
            functions = len(file_info.get('functions', []))
            classes = len(file_info.get('classes', []))
            if functions or classes:
                console.print(f"[cyan]Contains:[/cyan] {functions} functions, {classes} classes")
        
        # Ask for confirmation
        if not Confirm.ask(f"\n[bold red]Are you sure you want to delete {file_path}?[/bold red]"):
            console.print("[green]✅ File deletion cancelled[/green]")
            return False
        
        # Double confirmation for important files
        if file_info.get('type') == 'code' and (
            len(file_info.get('functions', [])) > 5 or 
            len(file_info.get('classes', [])) > 2 or
            file_info.get('size', 0) > 10000
        ):
            console.print("[bold red]⚠️ This appears to be an important code file![/bold red]")
            if not Confirm.ask("[bold red]Are you ABSOLUTELY sure?[/bold red]"):
                console.print("[green]✅ File deletion cancelled[/green]")
                return False
        
        try:
            full_path.unlink()
            
            # Remove from index
            if file_path in self.index_data.get('files', {}):
                del self.index_data['files'][file_path]
                await self._save_index()
            
            console.print(f"[green]✅ Successfully deleted {file_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to delete {file_path}: {e}[/red]")
            return False
    
    async def create_file_with_template(self, file_path: str, template_type: str = "auto") -> bool:
        """Create a new file with appropriate template."""
        full_path = self.project_root / file_path
        
        if full_path.exists():
            if not Confirm.ask(f"[yellow]File {file_path} already exists. Overwrite?[/yellow]"):
                return False
        
        # Ensure directory exists
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine template based on extension
        ext = full_path.suffix.lower()
        content = self._get_file_template(file_path, ext, template_type)
        
        try:
            full_path.write_text(content, encoding='utf-8')
            
            # Add to index
            file_info = await self._analyze_file(full_path)
            self.index_data.setdefault('files', {})[file_path] = file_info
            await self._save_index()
            
            console.print(f"[green]✅ Created {file_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Failed to create {file_path}: {e}[/red]")
            return False
    
    def _get_file_template(self, file_path: str, extension: str, template_type: str) -> str:
        """Get appropriate file template based on extension."""
        filename = Path(file_path).stem
        
        templates = {
            '.py': f'''"""
{filename.replace('_', ' ').title()} module.
"""


def main():
    """Main function."""
    pass


if __name__ == "__main__":
    main()
''',
            '.js': f'''/**
 * {filename.replace('_', ' ').title()} module
 */

function main() {{
    console.log("Hello from {filename}!");
}}

if (require.main === module) {{
    main();
}}

module.exports = {{ main }};
''',
            '.md': f'''# {filename.replace('_', ' ').title()}

## Description

Add your description here.

## Usage

```bash
# Add usage examples here
```

## Features

- Feature 1
- Feature 2
- Feature 3
''',
            '.html': f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename.replace('_', ' ').title()}</title>
</head>
<body>
    <h1>{filename.replace('_', ' ').title()}</h1>
    <p>Welcome to your new page!</p>
</body>
</html>
''',
            '.css': f'''/* {filename.replace('_', ' ').title()} Styles */

body {{
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
    background-color: #f5f5f5;
}}

.container {{
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}}
'''
        }
        
        return templates.get(extension, f"# {filename}\n\n# Created by Hurricane AI Agent\n")
    
    def navigate_to_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Navigate to a specific file and return its context."""
        file_info = self.get_file_info(file_path)
        
        if not file_info:
            return None
        
        full_path = self.project_root / file_path
        
        context = {
            "path": file_path,
            "full_path": str(full_path),
            "exists": full_path.exists(),
            "info": file_info,
            "parent_directory": str(full_path.parent),
            "related_files": self._find_related_files(file_path)
        }
        
        return context
    
    def _find_related_files(self, file_path: str) -> List[str]:
        """Find files related to the given file."""
        related = []
        file_info = self.get_file_info(file_path)
        
        if not file_info:
            return related
        
        # Find files in same directory
        parent_dir = str(Path(file_path).parent)
        
        for path, info in self.index_data.get('files', {}).items():
            if path == file_path:
                continue
                
            # Same directory
            if str(Path(path).parent) == parent_dir:
                related.append(path)
            
            # Same language
            elif info.get('language') == file_info.get('language'):
                related.append(path)
        
        return related[:10]  # Limit to 10 related files
