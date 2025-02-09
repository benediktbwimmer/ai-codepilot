# AI Codepilot

A powerful AI‐driven coding assistant that helps developers understand, maintain, and modify codebases through intelligent automation, natural language processing, and real‐time interaction. AI Codepilot integrates multiple specialized agents to analyze your code, generate updates, and review changes—ensuring modifications are accurate and maintainable.

## Features

- **Intelligent Code Analysis:** Automatically generate a repository stub to capture the structure and context of your codebase.
- **Modular Agent Architecture:** Leverage specialized agents including:
  - Orchestrator Agent: Coordinates the overall process.
  - Planner Agent: Decomposes user requests into manageable tasks.
  - Coder Agent: Implements code updates based on the plan.
  - Merge Agent: Applies updates and resolves code conflicts.
  - Review Agent: Provides automated code reviews and constructive feedback.
- **Interactive Development:** Real-time communication via WebSocket with a modern Svelte frontend.
- **Token Usage Tracking:** Monitor API token consumption per agent.
- **Asynchronous & Scalable:** Built using FastAPI and asyncio for high-performance operations.
- **Extensible & Robust:** Powered by Pydantic for strong data validation and easy extensibility.

## Prerequisites

- Python 3.10+
- Node.js (for frontend development)
- API Keys:
  - OpenAI API key
  - Gemini API key (optional)

## Installation

1. Clone the Repository:

```bash
git clone https://github.com/yourusername/ai-codepilot.git
cd ai-codepilot
```

2. Configure Environment Variables:

Create a .env file in the root directory (or copy from .env.example) and add your API keys:

```bash
cp .env.example .env
# Edit .env with your API keys
```

3. Install Backend Dependencies:

```bash
pip install -r requirements.txt
```

4. Install Frontend Dependencies:

```bash
cd frontend
npm install
```

## Usage

### Running the Backend

Start the FastAPI server using Uvicorn:

```bash
python -m uvicorn backend.server:app
```

### Running the Frontend

In a separate terminal, start the Svelte development server:

```bash
cd frontend
npm run dev
```

Your application should now be accessible (typically at http://localhost:5173 or a similar URL).

### Running Tests

To run the backend tests:

```bash
pytest
```

## Project Structure

```
.
├── backend/
│   ├── agents/           # AI agent implementations (Coder, Merge, Planner, Review, Orchestrator)
│   ├── models/           # Pydantic models for data validation
│   ├── repo_map.py       # Code repository analyzer and stub generator
│   ├── server.py         # FastAPI server and WebSocket endpoint
│   └── utils.py          # Utility functions and search index integration
├── frontend/             # Svelte-based web interface with Tailwind CSS
│   ├── src/
│   │   ├── lib/          # Svelte components (Header, UserInput, DiffViewer, etc.)
│   │   ├── App.svelte    # Main Svelte application
│   │   └── main.js       # Application entry point
│   ├── public/           # Static assets
│   └── package.json      # Frontend dependencies and scripts
├── requirements.txt      # Python dependencies
└── README.md             # Project documentation
```

## Architecture Overview

AI Codepilot employs a multi-agent system to process user requests and update codebases:

- **Orchestrator Agent:** Combines repository context with the user request to kick off the workflow.
- **Planner Agent:** Creates a detailed plan by breaking down tasks.
- **Coder Agent:** Generates and groups code updates by file.
- **Merge Agent:** Integrates the code updates while resolving potential conflicts.
- **Review Agent:** Evaluates proposed changes and provides feedback for iterative improvements.
- **WebSocket Communicator:** Enables real-time interaction between the frontend and backend.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request with your improvements. For major changes, open an issue first to discuss your ideas.

## License

This project is licensed under the MIT License. See the LICENSE file for details.

Built with ❤️ using FastAPI, Pydantic, Svelte, and state-of-the-art AI models.