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
git clone  https://github.com/lathifshaik/Hurricane.git
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
hurricane init                    # Initialize```
    🌪️  ██╗  ██╗██╗   ██╗██████╗ ██████╗ ██╗ ██████╗ █████╗ ███╗   ██╗███████╗
        ██║  ██║██║   ██║██╔══██╗██╔══██╗██║██╔════╝██╔══██╗████╗  ██║██╔════╝
        ███████║██║   ██║██████╔╝██████╔╝██║██║     ███████║██╔██╗ ██║█████╗  
        ██╔══██║██║   ██║██╔══██╗██╔══██╗██║██║     ██╔══██║██║╚██╗██║██╔══╝  
        ██║  ██║╚██████╔╝██║  ██║██║  ██║██║╚██████╗██║  ██║██║ ╚████║███████╗
        ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚══════╝
                            Your Advanced Agentic AI Coding Assistant
```

# 🌪️ Hurricane AI Agent - Agentic Edition

**Hurricane** is the world's first fully autonomous agentic AI coding assistant powered by Ollama. Unlike traditional AI assistants that simply respond to commands, Hurricane operates as an intelligent agent that can autonomously plan, execute, monitor, and coordinate complex development tasks while continuously learning from your interactions.

## 🚀 **Agentic Capabilities**

### 🧠 **Autonomous Intelligence**
- **Goal-Oriented Behavior**: Set high-level goals and watch Hurricane autonomously break them down into actionable tasks
- **Proactive Suggestions**: Hurricane suggests next steps without being asked
- **Persistent Memory**: Remembers conversations, learns your coding patterns, and maintains context across sessions
- **Decision Making**: Makes intelligent autonomous decisions based on project context and learned preferences

### 🤖 **Multi-Agent Collaboration**
- **Specialized Agents**: 7 specialized agents (Coordinator, Coder, Tester, Documenter, Reviewer, Deployer, Monitor)
- **Workflow Orchestration**: Coordinates complex multi-step development workflows
- **Task Distribution**: Intelligently distributes tasks among specialized agents
- **Performance Tracking**: Monitors agent performance and optimizes task allocation

### 👁️ **Reactive Monitoring**
- **File System Watching**: Continuously monitors your project for changes
- **Intelligent Notifications**: Proactive alerts about issues, opportunities, and required actions
- **Code Quality Monitoring**: Automatic detection of potential problems and suggestions for improvements
- **Project Health Tracking**: Monitors overall project health and suggests maintenance tasks

### 🔧 **Tool Integration**
- **Git Operations**: Automated version control (commit, push, branch, merge)
- **Testing Frameworks**: Integrated testing with pytest, unittest, coverage analysis
- **Code Quality**: Automatic formatting (Black), linting (flake8), type checking (mypy)
- **Package Management**: Smart dependency management (pip, npm, poetry, pipenv)
- **Real-time Execution**: Execute and test code changes in real-time
- **Docker Integration**: Container management and deployment automation

## 📦 **Installation**

### Prerequisites
1. **Install Ollama**:
   ```bash
   # macOS
   brew install ollama
   
   # Linux
   curl -fsSL https://ollama.ai/install.sh | sh
   
   # Windows - Download from https://ollama.ai/download
   ```

2. **Start Ollama service**:
   ```bash
   ollama serve
   ```

3. **Pull recommended AI models**:
   ```bash
   # Best for coding (recommended)
   ollama pull qwen2.5-coder:7b
   
   # Alternative options
   ollama pull deepseek-coder:6.7b
   ollama pull codellama:7b
   ollama pull codegemma:7b
   ```

### Install Hurricane
```bash
# Clone the repository
git clone https://github.com/yourusername/hurricane.git
cd hurricane

# Install dependencies
pip install -r requirements.txt

# Install Hurricane in development mode
pip install -e .
```

## 🎯 **Quick Start Guide**

### 1. Initialize Hurricane
```bash
hurricane init
```
This will check your system, verify Ollama installation, and set up the initial configuration.

### 2. Enable Agentic Mode (New!)
```bash
hurricane agentic enable
```
Activates Hurricane's autonomous behavior, reactive monitoring, and multi-agent coordination.

### 3. Set Autonomous Goals
```bash
hurricane goal set "Build a complete web application with authentication, database, and tests"
```
Hurricane will autonomously break this down into tasks and start working toward the goal.

### 4. Interactive Mode
```bash
hurricane chat
```
Start an interactive session where Hurricane remembers context and learns from your preferences.

## 🔥 **Core Features**

### **Traditional Coding Assistant**
```bash
# Generate code
hurricane code generate "Create a FastAPI web server with JWT authentication"

# Debug issues
hurricane code debug --file app.py --error "AttributeError: 'NoneType' object has no attribute 'id'"

# Refactor code
hurricane code refactor --file messy_code.py --style clean

# Explain code
hurricane code explain --file complex_algorithm.py
```

### **Documentation Generation**
```bash
# Generate comprehensive README
hurricane docs generate --type readme

# Create API documentation
hurricane docs api --format openapi

# Add code comments
hurricane docs comment --file src/
```

### **Project Management**
```bash
# Scaffold new projects
hurricane files scaffold python-web my-api
hurricane files scaffold react-app my-frontend
hurricane files scaffold microservice user-service

# Organize existing projects
hurricane files organize --strategy by_type
```

## 🤖 **Agentic Mode Commands**

### **Autonomous Operations**
```bash
# Enable/disable agentic mode
hurricane agentic enable
hurricane agentic disable

# Set and manage goals
hurricane goal set "Implement user authentication system"
hurricane goal list
hurricane goal status <goal-id>

# Execute autonomous tasks
hurricane task execute-next
hurricane task list

# View comprehensive dashboard
hurricane dashboard
```

### **Multi-Agent Workflows**
```bash
# Create custom workflows
hurricane workflow create "Full Development Cycle" \
  --steps "code,test,document,review,deploy"

# Execute workflows
hurricane workflow run <workflow-id>

# Monitor agent status
hurricane agents status
```

### **Memory and Learning**
```bash
# View conversation history
hurricane memory history

# Check learned patterns
hurricane memory patterns

# View user preferences
hurricane memory preferences
```

### **Tool Integration**
```bash
# Git operations
hurricane git status
hurricane git commit "Implement new feature"
hurricane git push

# Testing
hurricane test run
hurricane test coverage

# Code quality
hurricane format
hurricane lint
hurricane typecheck

# Package management
hurricane install requests
hurricane update-requirements
```

## ⚙️ **Configuration**

Hurricane uses `~/.hurricane/config.yaml` for configuration:

```yaml
# Ollama Configuration
ollama:
  host: "http://localhost:11434"
  model: "qwen2.5-coder:7b"
  timeout: 60
  max_tokens: 4096

# User Preferences
preferences:
  code_style: "clean"
  documentation_format: "markdown"
  auto_save: true
  max_context_length: 8000
  agentic_mode: true

# Agentic Behavior
agentic:
  auto_monitoring: true
  proactive_suggestions: true
  autonomous_execution: false  # Requires approval for autonomous actions
  goal_persistence: true
  learning_enabled: true

# Tool Integration
tools:
  git_auto_commit: false
  auto_format_on_save: true
  run_tests_on_change: true
  notification_level: "info"
```

## 📊 **Agentic Dashboard**

The Hurricane dashboard provides real-time insights into:

- **Active Goals**: Current autonomous objectives and progress
- **Agent Status**: Performance of specialized agents
- **Memory System**: Conversation history and learned patterns
- **Tool Integration**: Available tools and their status
- **Monitoring**: File changes, notifications, and project health
- **Task Queue**: Pending and executing autonomous tasks

## 🎨 **Example Workflows**

### **Complete Web Application Development**
```bash
# Set high-level goal
hurricane goal set "Build a complete todo app with React frontend, FastAPI backend, PostgreSQL database, authentication, tests, and deployment"

# Hurricane will autonomously:
# 1. Plan the architecture
# 2. Create project structure
# 3. Generate backend API code
# 4. Create frontend components
# 5. Set up database models
# 6. Implement authentication
# 7. Write comprehensive tests
# 8. Generate documentation
# 9. Set up deployment pipeline
# 10. Monitor and optimize
```

### **Code Review and Quality Improvement**
```bash
# Hurricane continuously monitors your code and:
# - Suggests improvements
# - Detects potential bugs
# - Recommends refactoring
# - Ensures code quality standards
# - Maintains documentation
```

### **Learning Your Coding Style**
```bash
# Hurricane learns from your interactions:
# - Preferred coding patterns
# - Documentation style
# - Testing approaches
# - Workflow preferences
# - Tool usage patterns
```

## 🔍 **Advanced Features**

### **Context-Aware Processing**
- Hurricane maintains deep understanding of your project structure
- Remembers previous conversations and decisions
- Adapts suggestions based on your coding patterns
- Provides personalized recommendations

### **Intelligent Notifications**
- Proactive alerts about potential issues
- Suggestions for code improvements
- Reminders for pending tasks
- Project health monitoring

### **Autonomous Task Execution**
- Breaks down complex goals into manageable tasks
- Executes tasks autonomously (with your approval)
- Coordinates between different specialized agents
- Tracks progress and adjusts plans dynamically

## 🛠️ **Development & Contributing**

### **Project Structure**
```
hurricane/
├── hurricane/
│   ├── core/                 # Core agent and configuration
│   │   ├── agent.py         # Main Hurricane agent with agentic capabilities
│   │   ├── config.py        # Configuration management
│   │   └── ollama_client.py # Ollama integration
│   ├── modules/             # Specialized modules
│   │   ├── autonomous_planner.py    # Goal-oriented planning
│   │   ├── enhanced_memory.py       # Memory and learning system
│   │   ├── tool_integration.py      # External tool integration
│   │   ├── reactive_monitor.py      # File system monitoring
│   │   ├── multi_agent_system.py    # Multi-agent coordination
│   │   ├── code_assistant.py        # Code generation and debugging
│   │   ├── codebase_analyzer.py     # Code quality analysis
│   │   └── [other modules...]
│   └── cli.py               # Command-line interface
├── tests/                   # Test suite
├── docs/                    # Documentation
└── examples/                # Usage examples
```

### **Contributing**
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Submit a pull request

### **Development Setup**
```bash
# Clone and setup development environment
git clone https://github.com/yourusername/hurricane.git
cd hurricane

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
pytest

# Run Hurricane in development mode
python -m hurricane.cli init
```

## 🚨 **Troubleshooting**

### **Common Issues**

**Ollama Connection Issues**:
```bash
# Check if Ollama is running
ollama list

# Restart Ollama service
ollama serve

# Check Hurricane status
hurricane status
```

**Model Not Found**:
```bash
# Pull the required model
ollama pull qwen2.5-coder:7b

# Verify model is available
ollama list
```

**Agentic Mode Issues**:
```bash
# Check agentic status
hurricane dashboard

# Restart agentic mode
hurricane agentic disable
hurricane agentic enable
```

## 📄 **License**

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **Ollama Team** for the excellent local LLM infrastructure
- **Open Source Community** for the amazing tools and libraries
- **Contributors** who help make Hurricane better

---

**Hurricane AI Agent** - Where autonomous intelligence meets practical development. 🌪️✨
