"""
Hurricane AI Agent - An intelligent coding assistant powered by Ollama.

Hurricane helps developers with:
- Code generation and assistance
- Documentation generation
- File management and organization
"""

__version__ = "0.1.0"
__author__ = "Hurricane AI Team"
__email__ = "hurricane@example.com"

from .core.agent import HurricaneAgent
from .core.config import Config

__all__ = ["HurricaneAgent", "Config"]
