# AI Codepilot

A powerful AI-driven coding assistant that helps developers understand, maintain, and modify codebases through intelligent automation and natural language interaction.

## Features

- **Intelligent Code Analysis:** Dynamic codebase understanding and context-aware suggestions
- **Interactive Development:** Real-time communication through WebSocket interface
- **Modular Agent Architecture:** Specialized agents for planning, coding, and review
- **Data Validation:** Robust data handling with Pydantic models
- **Code Review:** Built-in code review capabilities with feedback system
- **Asynchronous Support:** High-performance async operations
- **Modern Web Interface:** Real-time updates with Svelte frontend

## Prerequisites

- Python 3.10+
- Node.js (for frontend development)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/ai-codepilot.git
cd ai-codepilot
```

2. Install backend dependencies:
```bash
pip install -r requirements.txt
```

3. Install frontend dependencies:
```bash
cd frontend
npm install
```

## Usage

### Backend

Start the backend server:

```bash
python -m uvicorn backend.server:app --reload
```

### Frontend

In a new terminal, start the frontend development server:

```bash
cd frontend
npm run dev
```

## Project Structure

```
.
├── backend/
│   ├── agents/           # AI agent implementations
│   ├── server.py         # FastAPI server
│   ├── repo_map.py       # Code repository analyzer
│   └── utils.py          # Utility functions
├── frontend/            # Svelte-based web interface
└── requirements.txt     # Python dependencies
```

## Architecture

The system consists of several specialized agents:

- **Orchestrator Agent:** Coordinates the overall execution flow
- **Planner Agent:** Breaks down tasks into manageable steps
- **Context Builder:** Analyzes and provides relevant code context
- **Coder Agent:** Implements code changes with review capability
- **Review Agent:** Provides code review and feedback
- **Merge Agent:** Handles code merging and conflict resolution

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---
Built with ❤️ using Pydantic, FastAPI, and Svelte