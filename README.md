# Hurricane AI Agent 🌪️

Hurricane is an intelligent AI coding assistant powered by Ollama that helps you with:
- **Code Generation & Assistance**: Write, debug, and refactor code
- **Documentation Generation**: Auto-generate README files, comments, and API docs
- **File Management**: Create, organize, and manage project files intelligently

## Features

- 🤖 **Local AI Processing**: Uses Ollama for privacy-focused AI operations
- 💻 **Multi-language Support**: Works with Python, JavaScript, Go, and more
- 📝 **Smart Documentation**: Generates comprehensive documentation
- 🗂️ **Intelligent File Management**: Organizes and creates project structures
- ⚡ **Fast CLI Interface**: Beautiful command-line interface with rich output
- 🔧 **Extensible Architecture**: Plugin-based system for easy expansion

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd hurricane

# Install dependencies
pip install -r requirements.txt

# Install Hurricane
pip install -e .
```

## Prerequisites

- Python 3.9+
- Ollama installed and running
- A compatible LLM model (e.g., llama2, codellama, mistral)

## Quick Start

```bash
# Start Hurricane (Interactive Mode - Recommended!)
hurricane start

# Or use individual commands:
hurricane init                    # Initialize Hurricane
hurricane code generate "create a Python function to calculate fibonacci"
hurricane docs generate          # Generate documentation
hurricane files scaffold python my-project
```

## 🌪️ Interactive Mode (Super Easy!)

Just run `hurricane start` and Hurricane will:
1. Show you a beautiful welcome screen
2. Help you download the best AI models
3. Let you chat in plain English!

**Example conversations:**
- "Fix the bug in main.py"
- "Create a README for my project"
- "Generate a FastAPI server with authentication"
- "Debug my Python code"
- "Refactor this code to be cleaner"
- "Explain what this function does"
- "Create unit tests for my code"
- "Organize my project files"

**Recommended Models:**
- `qwen2.5-coder:7b` - 🚀 Best for coding (4.2GB)
- `deepseek-coder:6.7b` - 💎 Code specialist (3.8GB)
- `codellama:7b` - 🦙 Meta's coding model (3.8GB)

## Usage

### Coding Assistant
```bash
# Generate code
hurricane code "create a REST API with FastAPI"

# Debug code
hurricane debug --file main.py

# Refactor code
hurricane refactor --file old_code.py --style clean
```

### Documentation
```bash
# Generate README
hurricane docs readme

# Add code comments
hurricane docs comment --file app.py

# Create API documentation
hurricane docs api --format markdown
```

### File Management
```bash
# Create project structure
hurricane files scaffold --type web-app

# Organize files
hurricane files organize --directory ./src

# Create templates
hurricane files template --name custom-template
```

## Configuration

Hurricane uses a configuration file at `~/.hurricane/config.yaml`:

```yaml
ollama:
  host: "http://localhost:11434"
  model: "codellama"
  
preferences:
  code_style: "clean"
  documentation_format: "markdown"
  file_organization: "by_type"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
