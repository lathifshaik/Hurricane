"""
Git integration module for Hurricane AI Agent.
"""

import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.syntax import Syntax

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


class GitAssistant:
    """AI-powered Git integration and version control assistant."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root).resolve()
        self.git_dir = self.project_root / ".git"
    
    def is_git_repo(self) -> bool:
        """Check if current directory is a Git repository."""
        return self.git_dir.exists() and self.git_dir.is_dir()
    
    async def init_repo(self) -> bool:
        """Initialize a new Git repository."""
        try:
            result = await self._run_git_command(["init"])
            if result.returncode == 0:
                console.print("[green]✅ Git repository initialized![/green]")
                return True
            else:
                console.print(f"[red]❌ Failed to initialize Git repo: {result.stderr}[/red]")
                return False
        except Exception as e:
            console.print(f"[red]❌ Error initializing Git repo: {e}[/red]")
            return False
    
    async def get_status(self) -> Dict[str, Any]:
        """Get Git repository status."""
        if not self.is_git_repo():
            return {"error": "Not a Git repository"}
        
        try:
            # Get status
            status_result = await self._run_git_command(["status", "--porcelain"])
            
            # Get current branch
            branch_result = await self._run_git_command(["branch", "--show-current"])
            current_branch = branch_result.stdout.strip() if branch_result.returncode == 0 else "unknown"
            
            # Parse status
            modified_files = []
            staged_files = []
            untracked_files = []
            
            for line in status_result.stdout.split('\n'):
                if not line.strip():
                    continue
                
                status_code = line[:2]
                filename = line[3:]
                
                if status_code[0] in ['M', 'A', 'D', 'R', 'C']:
                    staged_files.append({"file": filename, "status": status_code[0]})
                
                if status_code[1] in ['M', 'D']:
                    modified_files.append({"file": filename, "status": status_code[1]})
                
                if status_code == "??":
                    untracked_files.append(filename)
            
            return {
                "current_branch": current_branch,
                "modified_files": modified_files,
                "staged_files": staged_files,
                "untracked_files": untracked_files,
                "is_clean": len(modified_files) == 0 and len(staged_files) == 0 and len(untracked_files) == 0
            }
            
        except Exception as e:
            return {"error": str(e)}
    
    async def show_status(self) -> None:
        """Display Git status in a beautiful format."""
        status = await self.get_status()
        
        if "error" in status:
            console.print(f"[red]❌ {status['error']}[/red]")
            return
        
        # Create status table
        table = Table(title=f"🌿 Git Status - Branch: {status['current_branch']}")
        table.add_column("Category", style="cyan")
        table.add_column("Files", style="white")
        table.add_column("Count", style="green")
        
        if status["staged_files"]:
            staged_list = [f"📄 {f['file']} ({f['status']})" for f in status["staged_files"]]
            table.add_row("Staged", "\n".join(staged_list), str(len(status["staged_files"])))
        
        if status["modified_files"]:
            modified_list = [f"📝 {f['file']} ({f['status']})" for f in status["modified_files"]]
            table.add_row("Modified", "\n".join(modified_list), str(len(status["modified_files"])))
        
        if status["untracked_files"]:
            untracked_list = [f"❓ {f}" for f in status["untracked_files"]]
            table.add_row("Untracked", "\n".join(untracked_list), str(len(status["untracked_files"])))
        
        if status["is_clean"]:
            table.add_row("Status", "✅ Working tree clean", "0")
        
        console.print(table)
    
    async def add_files(self, files: List[str] = None) -> bool:
        """Add files to staging area."""
        if not self.is_git_repo():
            console.print("[red]❌ Not a Git repository[/red]")
            return False
        
        try:
            if files is None:
                # Add all files
                result = await self._run_git_command(["add", "."])
                console.print("[green]✅ All files added to staging area[/green]")
            else:
                # Add specific files
                result = await self._run_git_command(["add"] + files)
                console.print(f"[green]✅ Added {len(files)} files to staging area[/green]")
            
            return result.returncode == 0
            
        except Exception as e:
            console.print(f"[red]❌ Error adding files: {e}[/red]")
            return False
    
    async def generate_smart_commit_message(self, changes: Optional[Dict] = None) -> str:
        """Generate an AI-powered commit message based on changes."""
        console.print("[blue]🤖 Generating smart commit message...[/blue]")
        
        try:
            # Get diff if changes not provided
            if changes is None:
                diff_result = await self._run_git_command(["diff", "--cached"])
                diff_content = diff_result.stdout
            else:
                diff_content = str(changes)
            
            if not diff_content.strip():
                return "Update files"
            
            # Generate commit message using AI
            system_prompt = """You are a Git commit message expert. Generate concise, conventional commit messages.
Follow these rules:
1. Use conventional commit format: type(scope): description
2. Types: feat, fix, docs, style, refactor, test, chore
3. Keep under 50 characters for the subject line
4. Be specific about what changed
5. Use imperative mood (Add, Fix, Update, etc.)"""
            
            prompt = f"""Generate a commit message for these changes:

{diff_content[:2000]}  # Limit diff size

Return only the commit message, nothing else."""
            
            commit_message = await self.ollama_client.generate_response(
                prompt, 
                system_prompt=system_prompt
            )
            
            # Clean up the response
            commit_message = commit_message.strip().replace('"', '').replace("'", "")
            
            # Fallback if AI response is too long or invalid
            if len(commit_message) > 72 or not commit_message:
                commit_message = "Update project files"
            
            return commit_message
            
        except Exception as e:
            console.print(f"[yellow]⚠️ Could not generate smart commit message: {e}[/yellow]")
            return "Update files"
    
    async def commit_changes(self, message: str = None, auto_message: bool = False) -> bool:
        """Commit staged changes with optional AI-generated message."""
        if not self.is_git_repo():
            console.print("[red]❌ Not a Git repository[/red]")
            return False
        
        try:
            # Check if there are staged changes
            status = await self.get_status()
            if not status.get("staged_files"):
                console.print("[yellow]⚠️ No staged changes to commit[/yellow]")
                return False
            
            # Generate or get commit message
            if auto_message or message is None:
                message = await self.generate_smart_commit_message()
                console.print(f"[cyan]📝 Generated commit message: {message}[/cyan]")
                
                if not auto_message:
                    if not Confirm.ask("Use this commit message?"):
                        message = Prompt.ask("Enter your commit message")
            
            # Commit changes
            result = await self._run_git_command(["commit", "-m", message])
            
            if result.returncode == 0:
                console.print(f"[green]✅ Successfully committed changes: {message}[/green]")
                return True
            else:
                console.print(f"[red]❌ Failed to commit: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error committing changes: {e}[/red]")
            return False
    
    async def get_commit_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent commit history."""
        if not self.is_git_repo():
            return []
        
        try:
            result = await self._run_git_command([
                "log", 
                f"--max-count={limit}",
                "--pretty=format:%H|%an|%ad|%s",
                "--date=relative"
            ])
            
            commits = []
            for line in result.stdout.split('\n'):
                if line.strip():
                    parts = line.split('|', 3)
                    if len(parts) == 4:
                        commits.append({
                            "hash": parts[0][:8],
                            "author": parts[1],
                            "date": parts[2],
                            "message": parts[3]
                        })
            
            return commits
            
        except Exception as e:
            console.print(f"[red]❌ Error getting commit history: {e}[/red]")
            return []
    
    async def show_commit_history(self, limit: int = 10) -> None:
        """Display commit history in a beautiful format."""
        commits = await self.get_commit_history(limit)
        
        if not commits:
            console.print("[yellow]No commit history found[/yellow]")
            return
        
        table = Table(title="📚 Recent Commits")
        table.add_column("Hash", style="yellow", width=8)
        table.add_column("Author", style="cyan", width=15)
        table.add_column("Date", style="green", width=15)
        table.add_column("Message", style="white")
        
        for commit in commits:
            table.add_row(
                commit["hash"],
                commit["author"],
                commit["date"],
                commit["message"]
            )
        
        console.print(table)
    
    async def create_branch(self, branch_name: str) -> bool:
        """Create and switch to a new branch."""
        if not self.is_git_repo():
            console.print("[red]❌ Not a Git repository[/red]")
            return False
        
        try:
            result = await self._run_git_command(["checkout", "-b", branch_name])
            
            if result.returncode == 0:
                console.print(f"[green]✅ Created and switched to branch '{branch_name}'[/green]")
                return True
            else:
                console.print(f"[red]❌ Failed to create branch: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error creating branch: {e}[/red]")
            return False
    
    async def switch_branch(self, branch_name: str) -> bool:
        """Switch to an existing branch."""
        if not self.is_git_repo():
            console.print("[red]❌ Not a Git repository[/red]")
            return False
        
        try:
            result = await self._run_git_command(["checkout", branch_name])
            
            if result.returncode == 0:
                console.print(f"[green]✅ Switched to branch '{branch_name}'[/green]")
                return True
            else:
                console.print(f"[red]❌ Failed to switch branch: {result.stderr}[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Error switching branch: {e}[/red]")
            return False
    
    async def list_branches(self) -> List[str]:
        """List all branches."""
        if not self.is_git_repo():
            return []
        
        try:
            result = await self._run_git_command(["branch", "-a"])
            branches = []
            
            for line in result.stdout.split('\n'):
                line = line.strip()
                if line and not line.startswith('remotes/origin/HEAD'):
                    # Remove * and whitespace
                    branch = line.replace('*', '').strip()
                    if branch.startswith('remotes/origin/'):
                        branch = branch.replace('remotes/origin/', 'origin/')
                    branches.append(branch)
            
            return branches
            
        except Exception as e:
            console.print(f"[red]❌ Error listing branches: {e}[/red]")
            return []
    
    async def show_branches(self) -> None:
        """Display all branches."""
        branches = await self.list_branches()
        
        if not branches:
            console.print("[yellow]No branches found[/yellow]")
            return
        
        # Get current branch
        status = await self.get_status()
        current_branch = status.get("current_branch", "")
        
        console.print("\n[bold green]🌿 Git Branches:[/bold green]")
        for branch in branches:
            if branch == current_branch:
                console.print(f"  * [bold green]{branch}[/bold green] (current)")
            elif branch.startswith('origin/'):
                console.print(f"    [dim cyan]{branch}[/dim cyan] (remote)")
            else:
                console.print(f"    [cyan]{branch}[/cyan]")
    
    async def smart_commit_workflow(self) -> bool:
        """Complete AI-assisted commit workflow."""
        console.print("[bold blue]🤖 Starting smart commit workflow...[/bold blue]")
        
        # Check status
        status = await self.get_status()
        if "error" in status:
            console.print(f"[red]❌ {status['error']}[/red]")
            return False
        
        if status["is_clean"]:
            console.print("[green]✅ Working tree is clean, nothing to commit[/green]")
            return True
        
        # Show current status
        await self.show_status()
        
        # Ask what to add
        if status["modified_files"] or status["untracked_files"]:
            if Confirm.ask("Add all changes to staging area?"):
                await self.add_files()
            else:
                console.print("[yellow]Please manually stage files with 'git add' first[/yellow]")
                return False
        
        # Generate and commit with smart message
        return await self.commit_changes(auto_message=False)
    
    async def _run_git_command(self, args: List[str]) -> subprocess.CompletedProcess:
        """Run a Git command and return the result."""
        cmd = ["git"] + args
        
        result = subprocess.run(
            cmd,
            cwd=self.project_root,
            capture_output=True,
            text=True
        )
        
        return result
