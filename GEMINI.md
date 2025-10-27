# Agent Zero Framework Context

This document provides a comprehensive overview of the Agent Zero project, intended as instructional context for future interactions.

## 1. Project Overview

**Agent Zero** is a robust, open-source, and highly customizable **agentic framework** written primarily in **Python**. It is designed to be a dynamic, general-purpose personal assistant that grows and learns with the user.

### Core Concepts:
*   **Multi-Agent Architecture:** Agents can create subordinate agents to break down and solve complex subtasks, maintaining a clean and focused context.
*   **Prompt-Driven Behavior:** The agent's entire behavior is defined by system prompts, making it extremely flexible and customizable.
*   **Computer as a Tool:** The agent is designed to use the operating system and terminal to execute code and create its own tools as needed.
*   **Persistent Memory:** Utilizes RAG (Retrieval-Augmented Generation) with FAISS and Sentence Transformers for persistent memory and knowledge base lookups.

## 2. Key Technologies & Architecture

| Component | Technology/Location | Description |
| :--- | :--- | :--- |
| **Core Language** | Python (confirmed by `requirements.txt`) | The primary language for the agent logic. |
| **Web UI** | Flask (`run_ui.py`), `webui/` | Provides a modern, interactive, and real-time streamed user interface. |
| **LLM Abstraction** | LiteLLM (`litellm` in `requirements.txt`) | Used for unified access to a wide range of LLM providers (OpenAI, Google/Gemini, Anthropic, Ollama, Groq, etc.), configured in `conf/model_providers.yaml`. |
| **Agent Logic** | `agent.py` | Contains the core `Agent` class, managing the asynchronous communication loop, history, and tool execution. |
| **Configuration** | `conf/model_providers.yaml` | Defines all supported LLM providers and their LiteLLM configurations. |
| **Customization** | `prompts/` directory | All agent behavior, messages, and utility functions are defined here via Markdown files. |
| **Tooling** | `python/tools/`, `instruments/` | Modular tools and custom functions that the agent can call. |
| **Communication** | MCP (Multi-agent Communication Protocol) | Custom protocol for agent-to-agent and server-to-server communication. |
| **Containerization** | Docker (`DockerfileLocal`) | The primary and recommended deployment method for isolation and consistency. |

## 3. Building and Running

The recommended way to run Agent Zero is via Docker.

### Quick Start (Docker)

The framework is fully dockerized and can be run with the following commands:

```bash
# 1. Pull the latest image
docker pull agent0ai/agent-zero

# 2. Run the container, mapping a host port and a volume for persistence
# Replace $PORT with your desired port (e.g., 50001)
# Replace /path/to/your/data with a local directory for persistent storage
docker run -p $PORT:80 -v /path/to/your/data:/a0 agent0ai/agent-zero
```

### Local Development

For local development, the project can be run directly using Python:

1.  Install dependencies: `pip install -r requirements.txt`
2.  Run the Web UI: `python run_ui.py` (This will start the Flask server).

## 4. Customization and Development

The framework is designed for maximum extensibility:

*   **Prompts:** Modify files in the `prompts/` directory to change the agent's personality, instructions, and communication style.
*   **Tools:** New tools can be added to `python/tools/` or within agent-specific directories under `agents/`.
*   **Models:** Model selection for Chat, Utility, and Embedding roles is configured via the Web UI settings, leveraging the providers defined in `conf/model_providers.yaml`.