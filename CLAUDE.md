# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Agent Zero is a personal, organic agentic framework that grows and learns with you. It's a general-purpose AI assistant that uses the computer as a tool to accomplish tasks, featuring multi-agent cooperation, persistent memory, and complete customizability.

## Core Architecture

### Main Components
- **`agent.py`** - Core agent implementation with context management and execution loop
- **`initialize.py`** - System initialization and environment setup
- **`python/`** - Backend ecosystem containing all logic, tools, and API endpoints
- **`webui/`** - Frontend interface with real-time streaming capabilities
- **`prompts/`** - All system prompts, behavior definitions, and message templates
- **`agents/`** - Different agent roles and configurations
- `conf/model_providers.yaml` - LLM provider configurations
- `requirements.txt` - Python dependencies

### Key Technologies
- **Backend**: Python with Flask, LiteLLM for multi-provider AI integration
- **Frontend**: Vanilla HTML/CSS/JavaScript with real-time streaming via WebSocket
- **Memory**: FAISS vector database with sentence transformers for semantic search
- **Browser Automation**: Playwright for web interactions
- **Docker**: Full containerization with multi-stage builds

## Development Commands

### Running the Application
```bash
# Local development
python initialize.py

# Docker development
docker build -f DockerfileLocal -t agent-zero:local .
docker run -p 50001:80 agent-zero:local
```

### Python Environment
```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```

### Configuration
- Model providers and API keys: `conf/model_providers.yaml`
- Agent behavior: Modify files in `prompts/` directory
- Agent roles: Create new configurations in `agents/` directories

## Development Principles

### Behavioral Equivalence Principle
When implementing "enhanced" versions of existing functionality, maintain identical user experience patterns. Users expect consistent behavior - if they say "exactly like X", prioritize behavioral similarity over technical sophistication.

### Evidence-Based Validation Protocol
- Always verify assumptions against actual system state using empirical evidence (file contents, command outputs)
- Use exact string matching patterns that reflect actual code format (single quotes vs double quotes)
- Test each component individually before end-to-end validation to catch issues early

### User Intent Prioritization
Technical implementation should serve user intent, not technical elegance. When user feedback indicates a different approach is needed, pivot quickly and completely rather than making partial adjustments.

### Incremental Implementation Strategy
- Build complex systems step-by-step, testing each component
- Use comprehensive verification methods to ensure implementation correctness
- Fix issues independently without requiring user intervention when possible

## Development Patterns

### File Organization
- **API Endpoints**: `python/api/api_*.py` - Follow existing patterns with proper error handling
- **Tools**: `python/tools/*.py` - Custom tools that extend agent capabilities
- **Helpers**: `python/helpers/*.py` - Shared utilities and common functionality
- **Extensions**: `python/extensions/*/` - System hooks and callbacks
- **Frontend Components**: `webui/components/*.html` and `webui/components/*.js`

### Adding New Tools
1. Create tool file in `python/tools/` following existing patterns
2. Use the `Tool` base class and implement proper error handling
3. Add tool description and usage instructions in relevant prompts
4. Test with different model providers and agent roles

### Adding New Agent Roles
1. Create directory in `agents/` with descriptive name
2. Add role-specific prompts in `agents/*/prompts/`
3. Add role-specific tools in `agents/*/tools/` if needed
4. Update agent initialization logic if required

### API Endpoint Development
```python
from python.helpers.api import api_call
from python.helpers.errors import RepairableException

@api_call
def api_custom_endpoint():
    try:
        # Implementation logic
        return {"status": "success", "data": result}
    except Exception as e:
        raise RepairableException(f"Error: {str(e)}")
```

### Frontend Development
- Use vanilla JavaScript (no frameworks)
- Follow existing component structure in `webui/components/`
- Maintain real-time streaming functionality
- Use existing notification and modal systems
- Follow established CSS class naming conventions

## Key Architectural Concepts

### Multi-Agent System
- Every agent has a superior agent giving tasks and instructions
- Agents can create subordinate agents for subtask delegation
- Communication flows through hierarchical agent structure
- Agent 0 reports directly to the human user

### Memory System
- Persistent memory storage in `memory/` directory
- Vector embeddings using FAISS for semantic search
- Automatic memory consolidation and AI-powered filtering
- Memory loading with intelligent retrieval based on context

### Tool Usage
- Agents use the computer as a tool through code execution
- Default tools include: search, code execution, memory, communication
- Custom tools can be created and added to agent arsenal
- Tool execution follows security patterns with sandboxing

### Prompt System
- Agent behavior defined by system prompts in `prompts/default/agent.system.md`
- All prompts are modular and customizable
- Message templates follow established patterns
- Prompt merging system for behavior customization

## Security Considerations
- Run Agent Zero in isolated environments (Docker recommended)
- Use the existing secrets management system for credentials
- Be cautious with code execution tools and file system access
- Follow proper input validation and sanitization patterns
- Use Docker security best practices for containerization

## Testing Guidelines
- Test with multiple model providers (OpenAI, Anthropic, local models)
- Test memory persistence and retrieval functionality
- Verify real-time streaming capabilities
- Test tool execution and error handling
- Validate Docker containerization
- Test agent roles and configurations

## Common Development Tasks
- **Modify agent behavior**: Edit prompts in `prompts/` directory
- **Add new capabilities**: Create tools in `python/tools/` and update prompts
- **Change UI**: Modify components in `webui/components/` and related CSS
- **Configure models**: Update `conf/model_providers.yaml`
- **Debug issues**: Check logs in `logs/` directory and use existing debug helpers