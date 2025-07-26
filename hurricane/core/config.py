"""
Configuration management for Hurricane AI Agent.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class OllamaConfig(BaseModel):
    """Ollama configuration settings."""
    host: str = Field(default="http://localhost:11434", description="Ollama server host")
    model: str = Field(default="codellama", description="Default model to use")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    temperature: float = Field(default=0.7, description="Model temperature")
    max_tokens: int = Field(default=2048, description="Maximum tokens to generate")


class PreferencesConfig(BaseModel):
    """User preferences configuration."""
    code_style: str = Field(default="clean", description="Preferred code style")
    documentation_format: str = Field(default="markdown", description="Documentation format")
    file_organization: str = Field(default="by_type", description="File organization strategy")
    auto_save: bool = Field(default=True, description="Auto-save generated files")
    verbose: bool = Field(default=False, description="Verbose output")


class Config(BaseModel):
    """Main configuration class for Hurricane."""
    ollama: OllamaConfig = Field(default_factory=OllamaConfig)
    preferences: PreferencesConfig = Field(default_factory=PreferencesConfig)
    
    @classmethod
    def load_config(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from file or create default."""
        if config_path is None:
            config_path = cls.get_default_config_path()
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
            return cls(**config_data)
        else:
            # Create default config
            config = cls()
            config.save_config(config_path)
            return config
    
    def save_config(self, config_path: Optional[Path] = None) -> None:
        """Save configuration to file."""
        if config_path is None:
            config_path = self.get_default_config_path()
        
        # Ensure directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False, indent=2)
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get the default configuration file path."""
        home = Path.home()
        return home / ".hurricane" / "config.yaml"
    
    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        for key, value in updates.items():
            if hasattr(self, key):
                if isinstance(getattr(self, key), BaseModel):
                    # Update nested config
                    current_config = getattr(self, key)
                    for sub_key, sub_value in value.items():
                        if hasattr(current_config, sub_key):
                            setattr(current_config, sub_key, sub_value)
                else:
                    setattr(self, key, value)
