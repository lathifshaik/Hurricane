"""
Reactive and proactive monitoring system for Hurricane AI Agent.
Provides file system monitoring, continuous analysis, and intelligent notifications.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import threading
from queue import Queue

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.text import Text

from ..core.config import Config
from ..core.ollama_client import OllamaClient

console = Console()


@dataclass
class FileEvent:
    """Represents a file system event."""
    event_type: str  # created, modified, deleted, moved
    file_path: str
    timestamp: str
    size: Optional[int] = None
    is_directory: bool = False
    old_path: Optional[str] = None  # For move events


@dataclass
class Notification:
    """Represents a system notification."""
    id: str
    type: str  # info, warning, error, success
    title: str
    message: str
    timestamp: str
    priority: int  # 1-5, 5 being highest
    actions: List[str]  # Suggested actions
    context: Dict[str, Any]
    acknowledged: bool = False


class HurricaneFileHandler(FileSystemEventHandler):
    """Custom file system event handler for Hurricane."""
    
    def __init__(self, event_queue: Queue, ignored_patterns: List[str]):
        super().__init__()
        self.event_queue = event_queue
        self.ignored_patterns = ignored_patterns
    
    def _should_ignore(self, path: str) -> bool:
        """Check if file should be ignored."""
        for pattern in self.ignored_patterns:
            if pattern in path:
                return True
        return False
    
    def on_created(self, event):
        if not self._should_ignore(event.src_path):
            file_event = FileEvent(
                event_type="created",
                file_path=event.src_path,
                timestamp=datetime.now().isoformat(),
                is_directory=event.is_directory
            )
            self.event_queue.put(file_event)
    
    def on_modified(self, event):
        if not event.is_directory and not self._should_ignore(event.src_path):
            try:
                size = Path(event.src_path).stat().st_size
            except:
                size = None
            
            file_event = FileEvent(
                event_type="modified",
                file_path=event.src_path,
                timestamp=datetime.now().isoformat(),
                size=size,
                is_directory=False
            )
            self.event_queue.put(file_event)
    
    def on_deleted(self, event):
        if not self._should_ignore(event.src_path):
            file_event = FileEvent(
                event_type="deleted",
                file_path=event.src_path,
                timestamp=datetime.now().isoformat(),
                is_directory=event.is_directory
            )
            self.event_queue.put(file_event)
    
    def on_moved(self, event):
        if not self._should_ignore(event.src_path) and not self._should_ignore(event.dest_path):
            file_event = FileEvent(
                event_type="moved",
                file_path=event.dest_path,
                old_path=event.src_path,
                timestamp=datetime.now().isoformat(),
                is_directory=event.is_directory
            )
            self.event_queue.put(file_event)


class ReactiveMonitor:
    """Reactive and proactive monitoring system."""
    
    def __init__(self, ollama_client: OllamaClient, config: Config, project_root: Path):
        self.ollama_client = ollama_client
        self.config = config
        self.project_root = Path(project_root)
        
        # Monitoring state
        self.is_monitoring = False
        self.observer = None
        self.event_queue = Queue()
        self.notifications = []
        self.monitoring_thread = None
        
        # Storage
        self.hurricane_dir = self.project_root / ".hurricane"
        self.hurricane_dir.mkdir(exist_ok=True)
        
        self.events_file = self.hurricane_dir / "file_events.json"
        self.notifications_file = self.hurricane_dir / "notifications.json"
        self.monitoring_config_file = self.hurricane_dir / "monitoring_config.json"
        
        # Load existing data
        self.file_events = self._load_file_events()
        self.notifications = self._load_notifications()
        self.monitoring_config = self._load_monitoring_config()
        
        # Monitoring patterns
        self.ignored_patterns = [
            '__pycache__', '.git', '.svn', 'node_modules', '.vscode',
            '.idea', 'venv', 'env', '.env', 'dist', 'build', '.DS_Store',
            '.pytest_cache', '.coverage', 'htmlcov', '.hurricane',
            '.pyc', '.pyo', '.log', '.tmp'
        ]
        
        # Analysis thresholds
        self.analysis_thresholds = {
            'file_size_warning': 1024 * 1024,  # 1MB
            'rapid_changes_threshold': 5,  # 5 changes in 1 minute
            'error_pattern_check': True,
            'dependency_change_alert': True
        }
        
        # Callbacks for different events
        self.event_callbacks = {}
    
    def _load_file_events(self) -> List[FileEvent]:
        """Load file events from storage."""
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                return [FileEvent(**event) for event in data]
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load file events: {e}[/yellow]")
        return []
    
    def _load_notifications(self) -> List[Notification]:
        """Load notifications from storage."""
        if self.notifications_file.exists():
            try:
                with open(self.notifications_file, 'r') as f:
                    data = json.load(f)
                return [Notification(**notif) for notif in data]
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load notifications: {e}[/yellow]")
        return []
    
    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration."""
        if self.monitoring_config_file.exists():
            try:
                with open(self.monitoring_config_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                console.print(f"[yellow]⚠️ Could not load monitoring config: {e}[/yellow]")
        
        return {
            "auto_analysis": True,
            "notification_level": "info",
            "watch_patterns": ["*.py", "*.js", "*.json", "*.md", "*.txt"],
            "analysis_interval": 300,  # 5 minutes
            "max_events": 1000,
            "max_notifications": 100
        }
    
    def _save_file_events(self):
        """Save file events to storage."""
        try:
            # Keep only last 1000 events
            events_to_save = self.file_events[-1000:] if len(self.file_events) > 1000 else self.file_events
            data = [asdict(event) for event in events_to_save]
            with open(self.events_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving file events: {e}[/red]")
    
    def _save_notifications(self):
        """Save notifications to storage."""
        try:
            # Keep only last 100 notifications
            notifs_to_save = self.notifications[-100:] if len(self.notifications) > 100 else self.notifications
            data = [asdict(notif) for notif in notifs_to_save]
            with open(self.notifications_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving notifications: {e}[/red]")
    
    def _save_monitoring_config(self):
        """Save monitoring configuration."""
        try:
            with open(self.monitoring_config_file, 'w') as f:
                json.dump(self.monitoring_config, f, indent=2)
        except Exception as e:
            console.print(f"[red]❌ Error saving monitoring config: {e}[/red]")
    
    def start_monitoring(self):
        """Start file system monitoring."""
        if self.is_monitoring:
            console.print("[yellow]⚠️ Monitoring is already active[/yellow]")
            return
        
        console.print("[blue]👁️ Starting reactive monitoring...[/blue]")
        
        # Set up file system observer
        self.observer = Observer()
        event_handler = HurricaneFileHandler(self.event_queue, self.ignored_patterns)
        
        self.observer.schedule(event_handler, str(self.project_root), recursive=True)
        self.observer.start()
        
        # Start monitoring thread
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        console.print("[green]✅ Reactive monitoring started[/green]")
    
    def stop_monitoring(self):
        """Stop file system monitoring."""
        if not self.is_monitoring:
            console.print("[yellow]⚠️ Monitoring is not active[/yellow]")
            return
        
        console.print("[blue]🛑 Stopping reactive monitoring...[/blue]")
        
        self.is_monitoring = False
        
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.observer = None
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
            self.monitoring_thread = None
        
        console.print("[green]✅ Reactive monitoring stopped[/green]")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        last_analysis = time.time()
        
        while self.is_monitoring:
            try:
                # Process file events
                self._process_file_events()
                
                # Periodic analysis
                if time.time() - last_analysis > self.monitoring_config["analysis_interval"]:
                    asyncio.run(self._perform_periodic_analysis())
                    last_analysis = time.time()
                
                time.sleep(1)  # Check every second
                
            except Exception as e:
                console.print(f"[red]❌ Error in monitoring loop: {e}[/red]")
                time.sleep(5)  # Wait before retrying
    
    def _process_file_events(self):
        """Process queued file events."""
        events_processed = 0
        
        while not self.event_queue.empty() and events_processed < 50:  # Limit batch size
            try:
                event = self.event_queue.get_nowait()
                self.file_events.append(event)
                
                # Analyze event for immediate notifications
                asyncio.run(self._analyze_file_event(event))
                
                events_processed += 1
                
            except Exception as e:
                console.print(f"[red]❌ Error processing file event: {e}[/red]")
                break
        
        if events_processed > 0:
            self._save_file_events()
    
    async def _analyze_file_event(self, event: FileEvent):
        """Analyze a file event for immediate notifications."""
        try:
            file_path = Path(event.file_path)
            
            # Check for large files
            if event.size and event.size > self.analysis_thresholds['file_size_warning']:
                await self._create_notification(
                    "warning",
                    "Large File Created",
                    f"Large file created: {file_path.name} ({event.size / 1024 / 1024:.1f}MB)",
                    ["Review file size", "Consider compression", "Check if intentional"],
                    {"file_path": str(file_path), "size": event.size}
                )
            
            # Check for rapid changes
            if event.event_type == "modified":
                recent_events = [e for e in self.file_events[-10:] 
                               if e.file_path == event.file_path and 
                               (datetime.now() - datetime.fromisoformat(e.timestamp)).seconds < 60]
                
                if len(recent_events) > self.analysis_thresholds['rapid_changes_threshold']:
                    await self._create_notification(
                        "info",
                        "Rapid File Changes",
                        f"File {file_path.name} has been modified {len(recent_events)} times in the last minute",
                        ["Check if auto-save is causing issues", "Review changes"],
                        {"file_path": str(file_path), "change_count": len(recent_events)}
                    )
            
            # Check for important file types
            if file_path.suffix in ['.py', '.js', '.json', '.yaml', '.yml']:
                if event.event_type == "created":
                    await self._create_notification(
                        "info",
                        "New Code File",
                        f"New {file_path.suffix} file created: {file_path.name}",
                        ["Review new file", "Add to version control", "Run analysis"],
                        {"file_path": str(file_path), "file_type": file_path.suffix}
                    )
            
            # Check for dependency files
            if file_path.name in ['requirements.txt', 'package.json', 'pyproject.toml', 'Pipfile']:
                await self._create_notification(
                    "warning",
                    "Dependency File Changed",
                    f"Dependency file modified: {file_path.name}",
                    ["Review changes", "Update dependencies", "Test compatibility"],
                    {"file_path": str(file_path), "file_type": "dependency"}
                )
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing file event: {e}[/red]")
    
    async def _perform_periodic_analysis(self):
        """Perform periodic analysis of the project."""
        if not self.monitoring_config["auto_analysis"]:
            return
        
        try:
            console.print("[dim]🔍 Performing periodic analysis...[/dim]")
            
            # Analyze recent file changes
            recent_events = [e for e in self.file_events 
                           if (datetime.now() - datetime.fromisoformat(e.timestamp)).seconds < 3600]  # Last hour
            
            if len(recent_events) > 50:
                await self._create_notification(
                    "info",
                    "High Activity Detected",
                    f"{len(recent_events)} file changes in the last hour",
                    ["Review recent changes", "Consider committing progress"],
                    {"event_count": len(recent_events)}
                )
            
            # Check for error patterns in recent files
            if self.analysis_thresholds['error_pattern_check']:
                await self._check_for_error_patterns()
            
            # Check project health
            await self._check_project_health()
            
        except Exception as e:
            console.print(f"[red]❌ Error in periodic analysis: {e}[/red]")
    
    async def _check_for_error_patterns(self):
        """Check recently modified files for error patterns."""
        recent_python_files = []
        
        for event in self.file_events[-20:]:  # Check last 20 events
            if event.event_type in ["created", "modified"] and event.file_path.endswith('.py'):
                recent_python_files.append(event.file_path)
        
        for file_path in set(recent_python_files):  # Remove duplicates
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check for common error patterns
                error_patterns = {
                    'syntax_error': r'SyntaxError|IndentationError',
                    'import_error': r'ImportError|ModuleNotFoundError',
                    'name_error': r'NameError',
                    'type_error': r'TypeError',
                    'bare_except': r'except\s*:',
                    'print_debug': r'print\s*\(',
                    'todo_fixme': r'(TODO|FIXME|XXX|HACK)'
                }
                
                import re
                for pattern_name, pattern in error_patterns.items():
                    if re.search(pattern, content, re.IGNORECASE):
                        await self._create_notification(
                            "warning",
                            f"Potential Issue: {pattern_name}",
                            f"Pattern '{pattern_name}' found in {Path(file_path).name}",
                            ["Review code", "Fix issues", "Run tests"],
                            {"file_path": file_path, "pattern": pattern_name}
                        )
                        break  # Only report first pattern found per file
                
            except Exception:
                continue  # Skip files that can't be read
    
    async def _check_project_health(self):
        """Check overall project health."""
        try:
            # Check for common project files
            important_files = ['README.md', 'requirements.txt', '.gitignore', 'setup.py', 'pyproject.toml']
            missing_files = []
            
            for file_name in important_files:
                if not (self.project_root / file_name).exists():
                    missing_files.append(file_name)
            
            if missing_files:
                await self._create_notification(
                    "info",
                    "Missing Project Files",
                    f"Consider adding: {', '.join(missing_files)}",
                    ["Create missing files", "Review project structure"],
                    {"missing_files": missing_files}
                )
            
            # Check Git status if available
            git_dir = self.project_root / '.git'
            if git_dir.exists():
                # Count uncommitted changes
                uncommitted_files = [e for e in self.file_events[-50:] 
                                   if e.event_type in ["created", "modified"] and 
                                   not any(pattern in e.file_path for pattern in self.ignored_patterns)]
                
                if len(uncommitted_files) > 10:
                    await self._create_notification(
                        "info",
                        "Many Uncommitted Changes",
                        f"Consider committing recent changes ({len(uncommitted_files)} files modified)",
                        ["Review changes", "Commit progress", "Create branch"],
                        {"modified_count": len(uncommitted_files)}
                    )
            
        except Exception as e:
            console.print(f"[red]❌ Error checking project health: {e}[/red]")
    
    async def _create_notification(self, type: str, title: str, message: str, 
                                 actions: List[str], context: Dict[str, Any]):
        """Create a new notification."""
        notification = Notification(
            id=f"notif_{int(time.time())}_{len(self.notifications)}",
            type=type,
            title=title,
            message=message,
            timestamp=datetime.now().isoformat(),
            priority={"error": 5, "warning": 3, "info": 2, "success": 1}.get(type, 2),
            actions=actions,
            context=context,
            acknowledged=False
        )
        
        self.notifications.append(notification)
        self._save_notifications()
        
        # Display notification if monitoring is active
        if self.is_monitoring:
            self._display_notification(notification)
    
    def _display_notification(self, notification: Notification):
        """Display a notification to the user."""
        color_map = {
            "error": "red",
            "warning": "yellow",
            "info": "blue",
            "success": "green"
        }
        
        color = color_map.get(notification.type, "white")
        icon_map = {
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "success": "✅"
        }
        
        icon = icon_map.get(notification.type, "📢")
        
        console.print(f"\n[{color}]{icon} {notification.title}[/{color}]")
        console.print(f"[dim]{notification.message}[/dim]")
        
        if notification.actions:
            console.print("[dim]Suggested actions:[/dim]")
            for action in notification.actions[:3]:  # Show max 3 actions
                console.print(f"[dim]  • {action}[/dim]")
    
    def acknowledge_notification(self, notification_id: str):
        """Acknowledge a notification."""
        for notification in self.notifications:
            if notification.id == notification_id:
                notification.acknowledged = True
                self._save_notifications()
                console.print(f"[green]✅ Notification acknowledged: {notification.title}[/green]")
                return True
        return False
    
    def get_unacknowledged_notifications(self) -> List[Notification]:
        """Get all unacknowledged notifications."""
        return [n for n in self.notifications if not n.acknowledged]
    
    def get_recent_events(self, hours: int = 1) -> List[FileEvent]:
        """Get recent file events."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [e for e in self.file_events 
                if datetime.fromisoformat(e.timestamp) > cutoff_time]
    
    def register_event_callback(self, event_type: str, callback: Callable):
        """Register a callback for specific event types."""
        if event_type not in self.event_callbacks:
            self.event_callbacks[event_type] = []
        self.event_callbacks[event_type].append(callback)
    
    def show_monitoring_status(self):
        """Display monitoring system status."""
        console.print(Panel.fit(
            "[bold blue]👁️ Reactive Monitoring Status[/bold blue]",
            border_style="blue"
        ))
        
        # Status table
        status_table = Table(title="📊 Monitoring Statistics")
        status_table.add_column("Metric", style="cyan")
        status_table.add_column("Value", style="green")
        
        status_table.add_row("Monitoring Active", "✅ Yes" if self.is_monitoring else "❌ No")
        status_table.add_row("Total Events", str(len(self.file_events)))
        status_table.add_row("Total Notifications", str(len(self.notifications)))
        status_table.add_row("Unacknowledged", str(len(self.get_unacknowledged_notifications())))
        status_table.add_row("Recent Events (1h)", str(len(self.get_recent_events(1))))
        
        console.print(status_table)
        
        # Recent notifications
        unack_notifications = self.get_unacknowledged_notifications()
        if unack_notifications:
            console.print("\n[bold yellow]🔔 Unacknowledged Notifications:[/bold yellow]")
            for notification in unack_notifications[-5:]:  # Show last 5
                timestamp = datetime.fromisoformat(notification.timestamp).strftime("%H:%M")
                console.print(f"[{notification.type}]• [{timestamp}] {notification.title}[/{notification.type}]")
        
        # Recent events
        recent_events = self.get_recent_events(1)
        if recent_events:
            console.print(f"\n[bold cyan]📁 Recent Activity ({len(recent_events)} events):[/bold cyan]")
            for event in recent_events[-5:]:  # Show last 5
                timestamp = datetime.fromisoformat(event.timestamp).strftime("%H:%M")
                file_name = Path(event.file_path).name
                console.print(f"[dim]• [{timestamp}] {event.event_type}: {file_name}[/dim]")
