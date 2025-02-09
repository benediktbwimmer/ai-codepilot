# AI Codepilot

AI Codepilot is a powerful, AI‐driven coding assistant designed to help developers understand, maintain, and modify codebases through intelligent automation, natural language processing, and real‐time interaction. By leveraging a modular multi-agent architecture, AI Codepilot can analyze your repository, plan incremental code updates, merge changes, and even perform automated code reviews—all while you interact with the system through a modern, responsive Svelte frontend.

## Table of Contents
- Features
- Architecture Overview
- Prerequisites
- Installation
- Configuration
- Usage
- Project Structure
- Testing
- Contributing
- License

## Features

### Intelligent Code Analysis:
Automatically generates a repository "stub" that summarizes the structure and key elements of your codebase by parsing Python, HTML, JavaScript, CSS, and Svelte files.

### Modular Multi-Agent Architecture:
Leverages specialized agents for different tasks:

- **Orchestrator Agent:** Coordinates the overall process using a set of integrated tools.
- **Planner Agent:** Decomposes user requests into actionable tasks.
- **Coder Agent:** Generates precise code updates (insertions or replacements) based on the plan.
- **Merge Agent:** Applies and integrates code updates while preserving code structure.
- **Review Agent:** Provides automated code reviews and constructive feedback to ensure changes meet quality and style standards.

### Real-Time Interactive Workflow:
Communicates with a Svelte frontend via WebSockets to display logs, diffs, token usage, and to prompt for user confirmations or additional feedback.

### Token Usage Tracking:
Monitors API token consumption for each agent, providing detailed usage summaries within the UI.

### Robust & Extensible:
Built on FastAPI and asyncio, with strong data validation using Pydantic, and designed for scalability and easy extensibility.

## Architecture Overview

AI Codepilot employs a collection of AI-powered agents that work together to process and implement your coding requests:

### Repository Mapping:
The RepoMap module scans your codebase, parses source files (using AST, BeautifulSoup, etc.), and creates a Python-style stub that summarizes available functions, classes, HTML structures, and asset information.

### Planning & Code Generation:
The Planner Agent produces a detailed plan based on the repository context and user request. The Coder Agent then generates code updates (in JSON) for the specified tasks, which are later merged by the Merge Agent.

### Code Review & Iteration:
If enabled, the Review Agent evaluates the proposed changes and provides feedback. The system supports iterative updates—if a review fails, the agents adjust the changes until the update meets quality standards or the maximum number of iterations is reached.

### Interactive Communication:
The backend communicates with the Svelte frontend using WebSockets, enabling real-time logging, diff visualization, and interactive confirmations for code updates.

## Prerequisites

- Python 3.10+
- Node.js (for frontend development)
- API Keys:
  - OPENAI_API_KEY (required)
  - GEMINI_API_KEY (required for Gemini-based features, optional)

## Installation

1. Clone the Repository:

```bash
git clone https://github.com/yourusername/ai-codepilot.git
cd ai-codepilot
```

2. Configure Environment Variables:

Create a .env file in the project root (or copy from a provided .env.example) and add your API keys:

```dotenv
OPENAI_API_KEY=your_openai_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here # Optional
```

3. Install Backend Dependencies:

It is recommended to use a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

4. Install Frontend Dependencies:

Navigate to the frontend directory and install the Node.js dependencies:

```bash
cd frontend
npm install
```

## Configuration

The project uses environment variables to control its behavior:

- OPENAI_API_KEY – Your OpenAI API key.
- GEMINI_API_KEY – Your Gemini API key. Optional.

Make sure these are correctly set in your .env file before running the application.

## Usage

### Running the Backend

Start the FastAPI server with Uvicorn:

```bash
python -m uvicorn backend.server:app
```

### Running the Frontend

In a separate terminal, start the Svelte development server:

```bash
cd frontend
npm run dev
```

The application should now be accessible in your browser (typically at http://localhost:5173 or the URL provided by Vite).

### Interactive Workflow

1. **Submit a Request:**
   Use the frontend to enter your coding request and configure options (e.g., enable review, set max iterations).

2. **Real-Time Feedback:**
   As the orchestration proceeds, you'll see real-time logs, diffs of proposed code changes, and token usage statistics. The system may prompt you for confirmations or additional feedback before applying updates.

3. **Review and Accept Changes:**
   For each code update, you can choose to accept, discard, or provide feedback to further refine the changes.

## Project Structure

```
.
├── backend/                # Python backend
│   ├── agents/           # AI agent implementations (Coder, Merge, Planner, Review, Orchestrator)
│   ├── models/           # Pydantic models for data validation
│   ├── repo_map.py       # Codebase analyzer and stub generator
│   ├── server.py         # FastAPI server with WebSocket endpoints
│   └── utils.py          # Utility functions (file reading, text chunking, search index)
├── frontend/               # Svelte-based web interface
│   ├── public/           # Static assets (HTML, images, etc.)
│   ├── src/              # Svelte source code (components, styles, stores)
│   │   ├── lib/          # Reusable components (Header, UserInput, DiffViewer, etc.)
│   │   ├── App.svelte    # Main Svelte application
│   │   └── main.js       # Application entry point
│   ├── package.json      # Frontend dependencies and scripts
│   └── vite.config.js    # Vite configuration for Svelte and Tailwind CSS
├── tests/                  # (Optional) Additional test files and test configuration
├── requirements.txt        # Python dependencies
├── .env                    # Environment configuration file (not checked into version control)
└── README.md               # Project documentation
```

## Testing

Backend tests are written using pytest and pytest-asyncio. To run the tests:

```bash
pytest
```

Ensure your virtual environment is activated and that you have installed the testing dependencies listed in requirements.txt.

## Contributing

Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please follow these steps:

1. Fork the repository.
2. Create a new branch for your feature or bugfix.
3. Commit your changes and push your branch.
4. Open a pull request describing your changes.

For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License.

Built with ❤️ using FastAPI, Pydantic, Svelte, and state-of-the-art AI models.

Happy coding!